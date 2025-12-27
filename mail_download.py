import poplib
import email
from email.policy import default
from datetime import datetime
import os
import ssl

# =====================================================
# CONFIG
# =====================================================
POP3_SERVER = "mail.ongc.co.in"
POP3_PORT = 995

BASE_PATH = "/home/hgupta/Learning/Practice/practice"
CREDS_FILE = f"{BASE_PATH}/verse_creds.txt"

SENDER_EMAIL = "vashudhara_vcr@ongc.co.in"
SUBJECT_KEY = "MORN_DPR"

SAVE_DIR = f"{BASE_PATH}/attachments"
os.makedirs(SAVE_DIR, exist_ok=True)

today = datetime.now().date()

# =====================================================
# READ CREDENTIALS
# =====================================================
with open(CREDS_FILE) as f:
    USERNAME = f.readline().strip()
    PASSWORD = f.readline().strip()

# =====================================================
# CONNECT TO POP3
# =====================================================
context = ssl.create_default_context()
pop = poplib.POP3_SSL(POP3_SERVER, POP3_PORT, context=context)
pop.user(USERNAME)
pop.pass_(PASSWORD)

print("✅ POP3 login successful")

# =====================================================
# FETCH MAIL LIST
# =====================================================
num_messages = len(pop.list()[1])
print(f"📨 Total messages: {num_messages}")

# =====================================================
# PROCESS MAILS (LATEST FIRST)
# =====================================================
for i in range(num_messages, 0, -1):
    response, lines, octets = pop.retr(i)
    raw_email = b"\n".join(lines)

    msg = email.message_from_bytes(raw_email, policy=default)

    subject = msg.get("Subject", "")
    sender = msg.get("From", "")
    date_hdr = msg.get("Date", "")

    # Subject + sender check
    if SUBJECT_KEY not in subject:
        continue
    if SENDER_EMAIL.lower() not in sender.lower():
        continue

    # Date check (today)
    try:
        msg_date = email.utils.parsedate_to_datetime(date_hdr).date()
    except Exception:
        continue

    if msg_date != today:
        continue

    print(f"✅ Found mail: {subject}")

    # =================================================
    # EXTRACT ATTACHMENTS
    # =================================================
    for part in msg.walk():
        if part.get_content_disposition() == "attachment":
            filename = part.get_filename()
            if not filename:
                continue

            ext = os.path.splitext(filename)[1]
            new_name = f"{SUBJECT_KEY}_{today.strftime('%Y%m%d')}{ext}"
            save_path = os.path.join(SAVE_DIR, new_name)

            with open(save_path, "wb") as f:
                f.write(part.get_payload(decode=True))

            print(f"⬇️ Attachment saved: {save_path}")

    break
else:
    print("❌ No matching mail found today")

# =====================================================
# CLEANUP
# =====================================================
pop.quit()
