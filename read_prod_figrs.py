#!/usr/bin/env python3

import imaplib
import email
import os
import sys
import re
import json
import shutil
from email.header import decode_header
from email.utils import parseaddr
from datetime import datetime, timedelta

from openpyxl import load_workbook
import xlrd

# -------------------------
# CONFIGURATION
# -------------------------
# CRED_FILE = "/home/ubuntu/learn/projects/data_from_reports/production_figure/.cred"
# IMAP_PORT = 143
# INBOX_FOLDER = "INBOX"

# EXPECTED_FROM = "vashudhara_vcr@ongc.co.in"

# DOWNLOAD_DIR = "/home/ubuntu/learn/projects/data_from_reports/DPR"
# ALLOWED_EXT = (".xls", ".xlsx")

# VERIFICATION_LOG = "/home/ubuntu/learn/projects/data_from_reports/mail_attachment_verification.log"
# PROD_JSON_FILE = "/home/ubuntu/learn/projects/data_from_reports/production_figure/prod_fig.json"
# PROD_JSON_PREFIX = "/home/ubuntu/learn/projects/data_from_reports/production_figure/daily/prod_fig_"
#!/usr/bin/env python3

import os
import json
from dotenv import load_dotenv

# --------------------------------------------------
# BASE DIR (directory of this script)
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# LOAD .env (CRON SAFE)
# --------------------------------------------------
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# --------------------------------------------------
# ENSURE REQUIRED DIRECTORIES EXIST
# --------------------------------------------------
REQUIRED_DIRS = [
    os.path.join(BASE_DIR, "production_figure"),
    os.path.join(BASE_DIR, "production_figure", "daily"),
    os.path.join(BASE_DIR, "DPR_from_mail"),
    os.path.join(BASE_DIR, "logs"),
]

for d in REQUIRED_DIRS:
    os.makedirs(d, exist_ok=True)

# --------------------------------------------------
# CONFIG FROM .env
# --------------------------------------------------
IMAP_SERVER = os.getenv("IMAP_SERVER")
USERNAME    = os.getenv("USERNAME")
PASSWORD    = os.getenv("PASSWORD")

IMAP_PORT = 143
INBOX_FOLDER = "INBOX"

EXPECTED_FROM = "vashudhara_vcr@ongc.co.in"

# --------------------------------------------------
# PATH CONFIG (DERIVED FROM BASE_DIR)
# --------------------------------------------------
DOWNLOAD_DIR = os.path.join(
    BASE_DIR, "DPR_from_mail"
)

VERIFICATION_LOG = os.path.join(
    BASE_DIR, "logs", "mail_attachment_verification.log"
)

PROD_JSON_FILE = os.path.join(
    BASE_DIR, "production_figure", "prod_fig.json"
)

PROD_JSON_PREFIX = os.path.join(
    BASE_DIR, "production_figure", "daily", "prod_fig_"
)

ALLOWED_EXT = (".xls", ".xlsx")

UPLOAD_DIR = "/mnt/upload"

MIN_OIL = 221000
MIN_GAS = 36

# -------------------------
# LOAD CREDENTIALS
# -------------------------
with open(CRED_FILE) as f:
    creds = [line.strip() for line in f if line.strip()]

USERNAME, PASSWORD, IMAP_SERVER = creds[:3]

# -------------------------
# LOGGING
# -------------------------
def log(msg):
    print(f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')} | {msg}")

# -------------------------
# HELPERS
# -------------------------
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

# ---------- SUBJECT / FILENAME HANDLING ----------

def normalize_subject(subject):
    return re.sub(r"[ _\-.]", "", subject.upper())

def subject_is_valid(subject):
    s = normalize_subject(subject)
    valid = (
        s.startswith("MRDPR") or
        s.startswith("MORNDPR") or
        s.startswith("MORNINGDPR")
    )
    log(f"DEBUG: Subject '{subject}' normalized='{s}' valid={valid}")
    return valid

def parse_date_from_text(text):
    log(f"DEBUG: Trying to parse date from text: {text}")

    cleaned = re.sub(r"(?i)morn(?:ing)?|mr|dpr", " ", text)
    cleaned = re.sub(r"[^\w]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    log(f"DEBUG: Cleaned text for date parsing: '{cleaned}'")

    parts = cleaned.split()

    for i in range(len(parts) - 2):
        candidate = f"{parts[i]} {parts[i+1]} {parts[i+2]}"
        for fmt in (
            "%d %m %Y", "%d %m %y",
            "%d %b %Y", "%d %B %Y",
            "%d %b %y", "%d %B %y",
        ):
            try:
                parsed = datetime.strptime(candidate, fmt).date()
                log(f"DEBUG: Parsed date '{parsed}' using '{candidate}' format '{fmt}'")
                return parsed
            except ValueError:
                pass

    log("DEBUG: No date parsed from text")
    return None

# ---------- FILE & DATA HANDLING ----------

def write_verification_log(date_str):
    log(f"Writing verification log: {VERIFICATION_LOG}")
    with open(VERIFICATION_LOG, "w") as f:
        f.write(f"{date_str} | Mail attachment available for date {date_str}\n")

def coerce_float(val, cell):
    if isinstance(val, (int, float)):
        log(f"DEBUG: Cell {cell} numeric → {val}")
        return float(val)
    if isinstance(val, str):
        try:
            num = float(val.strip())
            log(f"DEBUG: Cell {cell} str '{val}' → {num}")
            return num
        except ValueError:
            log(f"DEBUG: Cell {cell} invalid '{val}', defaulting 0")
            return 0.0
    log(f"DEBUG: Cell {cell} empty/unknown, defaulting 0")
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
    log(f"DEBUG: Gas calc = {f39} - ({h34} + {h35}) = {gas}")

    return oil, gas

def update_json_if_valid(oil, gas):
    oil_i = int(round(oil))
    gas_f = round(gas, 2)

    log(f"DEBUG: Oil={oil_i}, Gas={gas_f}")

    if oil_i < MIN_OIL:
        log("Oil below threshold → JSON NOT updated")
        return False

    if gas_f < MIN_GAS:
        log("Gas below threshold → JSON NOT updated")
        return False

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

    data = {
        "date": yesterday,
        "oil_produce": oil_i,
        "Gas_produce": f"{gas_f:.2f}"
    }

    log(f"DEBUG: Writing JSON → {data}")

    with open(PROD_JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)

    dated_file = f"{PROD_JSON_PREFIX}{yesterday}.json"
    with open(dated_file, "w") as f:
        json.dump(data, f, indent=2)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    shutil.copy2(PROD_JSON_FILE, os.path.join(UPLOAD_DIR, "prod_fig.json"))

    log("JSON updated and copied to upload directory")
    return True

# -------------------------
# MAIN
# -------------------------
try:
    today = datetime.now().date()
    log(f"Today date: {today}")

    log("Connecting to IMAP...")
    imap = imaplib.IMAP4(IMAP_SERVER, IMAP_PORT)
    imap.login(USERNAME, PASSWORD)
    imap.select(INBOX_FOLDER)

    _, msg_ids = imap.search(None, "ALL")
    msg_ids = msg_ids[0].split()

    log(f"DEBUG: Total mails found: {len(msg_ids)}")

    for msg_id in reversed(msg_ids):
        _, data = imap.fetch(msg_id, "(RFC822)")
        msg = email.message_from_bytes(data[0][1])

        from_email = parseaddr(decode_value(msg.get("From")))[1]
        subject = decode_value(msg.get("Subject"))

        log(f"DEBUG: Processing mail ID {msg_id}")
        log(f"DEBUG: From={from_email}")
        log(f"DEBUG: Subject={subject}")

        if from_email.lower() != EXPECTED_FROM.lower():
            log("DEBUG: Sender mismatch, skipping")
            continue

        mail_date = None
        if subject_is_valid(subject):
            mail_date = parse_date_from_text(subject)

        attachment_path = None
        attachment_date = None

        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                fname = decode_value(part.get_filename())
                log(f"DEBUG: Found attachment: {fname}")

                if not fname.lower().endswith(ALLOWED_EXT):
                    log("DEBUG: Attachment extension not allowed")
                    continue

                attachment_date = parse_date_from_text(fname)

                path = os.path.join(DOWNLOAD_DIR, fname)
                if not os.path.exists(path):
                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    log(f"DEBUG: Attachment saved to {path}")
                else:
                    log("DEBUG: Attachment already exists")

                attachment_path = path

        log(f"DEBUG: mail_date={mail_date}, attachment_date={attachment_date}")

        run_allowed = False

        if attachment_date == today:
            log("DEBUG: Attachment date matches today → RUN allowed")
            run_allowed = True
        elif attachment_date is None and mail_date == today:
            log("DEBUG: Subject date matches today → RUN allowed")
            run_allowed = True

        if not run_allowed or not attachment_path:
            log("DEBUG: No valid date match or no attachment → skipping")
            continue

        write_verification_log(today.strftime("%d-%m-%Y"))
        oil, gas = extract_excel_values(attachment_path)
        update_json_if_valid(oil, gas)
        break

    imap.logout()
    log("IMAP session closed")

except Exception as e:
    log(f"ERROR: {e}")
    sys.exit(1)