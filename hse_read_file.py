#!/usr/bin/env python3

import json
from collections import defaultdict
from datetime import datetime
import shutil
from pathlib import Path
import os

# ==================================================
# BASE PATHS
# ==================================================
# Script location:
# /home/ubuntu/intranet_script/hse_index/hse_index.py
BASE_DIR = Path(__file__).resolve().parent

# Source folder inside hse_index
SOURCE_DIR = BASE_DIR / "source"

# Logs folder (already exists earlier)
LOG_DIR = BASE_DIR / "logs"

# Upload destination
UPLOAD_DST = Path("/mnt/upload")

# ==================================================
# ENSURE REQUIRED DIRECTORIES EXIST
# ==================================================
BASE_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ==================================================
# FILE PATHS
# ==================================================
JSON_SRC = "/mnt/hse_dashboard_data/hse_index_json.json"
JSON_DST = SOURCE_DIR / "hse_index_json.json"

current_date = datetime.now().strftime("%d-%m-%Y")
LOG_FILE = LOG_DIR / f"hse_index_{current_date}.log"

site_index = None
site_sum = defaultdict(float)
site_count = defaultdict(int)

# -------------------------------------------------
# MAIN PROCESSING
# -------------------------------------------------
try:
    # Copy JSON from Samba
    shutil.copy2(JSON_SRC, JSON_DST)
    print(f"{current_date} - File copied from the server")

    # Load JSON
    with open(JSON_DST, "r") as f:
        data = json.load(f)

    # Plant → Site mapping
    plant_to_site = {
        '11': 'MH_Asset',
        '12': 'NH_Asset',
        '13': 'BS_Asset',
        '10D1': 'DRILLING',
        '10P1': 'URAN',
    }
    months = sorted({
        datetime.fromisoformat(item["Date"].replace("Z", "+00:00")).replace(day=1)
        for item in data
        if "Date" in item and item["Date"]
    })

    if not months:
        raise ValueError("No valid dates found")

    start = months[0]
    end = months[-1]

    result = f"{start.strftime('%B %Y')} to {end.strftime('%B %Y')}"
    print(f"{current_date} - Data logging period recorded")

    # Aggregate values
    for v in data:
        total = v.get("Total")
        if total in ("", None):
            continue

        plant = v.get("Plant Code", "")
        site = plant_to_site.get(plant) or plant_to_site.get(plant[:2])

        if site:
            site_sum[site] += total
            site_count[site] += 1

    # Site-wise averages
    site_index = {
        site: round(site_sum[site] / site_count[site], 1)
        for site in site_sum
    }

    # -------------------------------------------------
    # OVERALL WEIGHTED AVERAGE (CORRECT METHOD)
    # -------------------------------------------------
    overall_weighted_average = round(
        sum(site_sum.values()) / sum(site_count.values()),
        1
    )

    site_index["WEIGHTED_AVERAGE"] = overall_weighted_average
    site_index['TIME_PERIOD'] = result

    # Write today’s log
    with LOG_FILE.open("w") as f:
        json.dump(site_index, f, indent=4)
    print(f'{current_date} - Data recorded in final file {LOG_FILE}')
except Exception as e:
    print(f"[{current_date}] ERROR: {e}")

# -------------------------------------------------
# FALLBACK UPLOAD LOGIC
# -------------------------------------------------
def get_latest_log():
    logs = sorted(BASE_DIR.glob("hse_index_*.log"), reverse=True)
    return logs[0] if logs else None

upload_file = LOG_FILE if LOG_FILE.exists() else get_latest_log()

if upload_file:
    shutil.copy2(upload_file, UPLOAD_DST)
    print(f"{current_date} - Uploaded: {upload_file.name}")
else:
    print("No log file available to upload")
