#!/usr/bin/env python3

import imaplib
import email
import os
import sys
import re
import json
from email.header import decode_header
from email.utils import parseaddr
from datetime import datetime, timedelta

from openpyxl import load_workbook
import xlrd

# -------------------------
# CONFIGURATION
# -------------------------
CRED_FILE = "practice/cred.log"
IMAP_PORT = 143
INBOX_FOLDER = "INBOX"

EXPECTED_FROM = "vashudhara_vcr@ongc.co.in"
SUBJECT_PREFIX = "MORN DPR"

DOWNLOAD_DIR = "practice/DPR"
ALLOWED_EXT = (".xls", ".xlsx")

VERIFICATION_LOG = "mail_attachment_verification.log"
PROD_JSON_FILE = "practice/prod_fig.json"
PROD_JSON_PREFIX = "practice/prod_fig_"

MIN_OIL = 221000
MIN_GAS = 36

# -------------------------
# LOAD CREDENTIALS
# -------------------------
with open(CRED_FILE) as f:
    creds = [line.strip() for line in f if line.strip()]

USERNAME, PASSWORD, IMAP_SERVER = creds[:3]

# -------------------------
# HELPERS
# -------------------------
def log(msg):
    print(f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | {msg}")

def decode_value(value):
    if not value:
        return ""
    out = ""
    for text, enc in decode_header(value):
        if isinstance(text, bytes):
            out += text.decode(enc or "utf-8", errors="ignore")
        else:
            out += text
    return out

def parse_date_from_subject(subject):
    text = subject.upper().replace(SUBJECT_PREFIX, "")
    text = re.sub(r"[^\w]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    parts = text.split()

    for i in range(len(parts) - 2):
        candidate = f"{parts[i]} {parts[i+1]} {parts[i+2]}"
        for fmt in ("%d %m %Y", "%d %m %y", "%d %b %Y", "%d %B %Y",
                    "%d %b %y", "%d %B %y"):
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                pass
    return None

def write_verification_log(date_str):
    log(f"Writing verification log: {VERIFICATION_LOG}")
    with open(VERIFICATION_LOG, "w") as f:
        f.write(f"{date_str} | Mail attachment available for date {date_str}\n")

def coerce_float(val, cell):
    if isinstance(val, (int, float)):
        log(f"Cell {cell} read as numeric: {val}")
        return float(val)

    if isinstance(val, str):
        try:
            num = float(val.strip())
            log(f"Cell {cell} converted from str → float: '{val}' → {num}")
            return num
        except ValueError:
            log(f"Cell {cell} INVALID string '{val}', defaulting to 0.0")
            return 0.0

    log(f"Cell {cell} empty/unknown ({val}), defaulting to 0.0")
    return 0.0

def extract_excel_values(path):
    log(f"Reading Excel file: {path}")

    if path.lower().endswith(".xlsx"):
        wb = load_workbook(path, data_only=True)
        sh = wb["Sheet1"]

        oil = coerce_float(sh["B38"].value, "B38")
        f39 = coerce_float(sh["F39"].value, "F39")
        h34 = coerce_float(sh["H34"].value, "H34")
        h35 = coerce_float(sh["H35"].value, "H35")
    else:
        wb = xlrd.open_workbook(path)
        sh = wb.sheet_by_name("Sheet1")

        oil = coerce_float(sh.cell_value(37, 1), "B38")
        f39 = coerce_float(sh.cell_value(38, 5), "F39")
        h34 = coerce_float(sh.cell_value(33, 7), "H34")
        h35 = coerce_float(sh.cell_value(34, 7), "H35")

    gas = f39 - (h34 + h35)
    log(f"Gas calculation: {f39} - ({h34} + {h35}) = {gas}")

    return oil, gas

def update_json_if_valid(oil, gas):
    oil_i = int(round(oil))
    gas_f = round(gas, 2)

    if oil_i < MIN_OIL:
        log(f"Oil {oil_i} < {MIN_OIL} → JSON NOT updated")
        return

    if gas_f < MIN_GAS:
        log(f"Gas {gas_f} < {MIN_GAS} → JSON NOT updated")
        return

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")

    data = {
        "date": yesterday,
        "oil_produce": oil_i,
        "Gas_produce": gas_f
    }

    # Main JSON
    log(f"Writing production JSON: {PROD_JSON_FILE}")
    with open(PROD_JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Daily archival JSON
    dated_file = f"{PROD_JSON_PREFIX}{yesterday}.json"
    log(f"Writing daily JSON archive: {dated_file}")
    with open(dated_file, "w") as f:
        json.dump(data, f, indent=2)

    log(f"JSON updated successfully → oil={oil_i}, gas={gas_f}, date={yesterday}")

# -------------------------
# MAIN
# -------------------------
try:
    today = datetime.now().date()
    log(f"Today date: {today.strftime('%d-%m-%Y')}")

    log("Connecting to IMAP server (NO SSL)...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.login(USERNAME, PASSWORD)

    log("Selecting INBOX...")
    imap.select(INBOX_FOLDER)

    status, msg_ids = imap.search(None, "ALL")
    msg_ids = msg_ids[0].split()

    for msg_id in reversed(msg_ids):
        _, data = imap.fetch(msg_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        from_email = parseaddr(decode_value(msg.get("From")))[1]
        subject = decode_value(msg.get("Subject"))

        log(f"Checking mail: {subject}")

        if from_email.lower() != EXPECTED_FROM.lower():
            log("Sender mismatch — skipped")
            continue

        if not subject.upper().startswith(SUBJECT_PREFIX):
            log("Subject prefix mismatch — skipped")
            continue

        if parse_date_from_subject(subject) != today:
            log("Subject date mismatch — skipped")
            continue

        log("Valid DPR mail identified")

        attachment_path = None

        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                fname = decode_value(part.get_filename())
                if not fname.lower().endswith(ALLOWED_EXT):
                    continue

                path = os.path.join(DOWNLOAD_DIR, fname)

                if os.path.exists(path):
                    log(f"File already exists: {fname}")
                    attachment_path = path
                else:
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    log(f"File downloaded: {fname}")
                    attachment_path = path

        if attachment_path:
            write_verification_log(today.strftime("%d-%m-%Y"))
            oil, gas = extract_excel_values(attachment_path)
            update_json_if_valid(oil, gas)

        break

    imap.logout()
    log("IMAP session closed")

except Exception as e:
    log(f"ERROR: {e}")
    sys.exit(1)