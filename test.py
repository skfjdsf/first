#!/usr/bin/env python3
import subprocess
import socket
import requests
import sys
import dkim
from email.mime.text import MIMEText

FROM_EMAIL = "qsxzaqy@rec-bestgoods.com"
TO_EMAIL = "mikassahax@outlook.com"
SMTP_SERVER = "outlook-com.olc.protection.outlook.com"

DKIM_SELECTOR = "default"
DKIM_DOMAIN = "rec-bestgoods.com"
DKIM_KEY_FILE = "default.private"

HTML_BODY = "<h1>Test</h1><p>This is a test email.</p>"

# === PTR / HELO NAME ===
def fetch_ptr_or_default(default="rec-bestgoods.com"):
    try:
        ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return default

helo_name = fetch_ptr_or_default()

# === LOAD DKIM KEY ===
try:
    with open(DKIM_KEY_FILE, "rb") as f:
        private_key = f.read()
except FileNotFoundError:
    print("❌ DKIM key not found")
    sys.exit(1)

# === BUILD MESSAGE ===
msg = MIMEText(HTML_BODY, "html", "utf-8")
msg["From"] = FROM_EMAIL
msg["To"] = TO_EMAIL
msg["Subject"] = "SMTP Port 25 Test"

signature = dkim.sign(
    message=msg.as_string().encode(),
    selector=DKIM_SELECTOR.encode(),
    domain=DKIM_DOMAIN.encode(),
    privkey=private_key,
    include_headers=[b"from", b"to", b"subject"],
    canonicalize=(b"relaxed", b"relaxed"),
)

signed_email = signature.decode() + msg.as_string()

# === CHECK SPAMHAUS ===
def spamhaus_check(ip):
    rev = ".".join(ip.split(".")[::-1])
    r = subprocess.run(
        ["dig", "+short", f"{rev}.zen.spamhaus.org"],
        capture_output=True,
        text=True
    )
    return bool(r.stdout.strip())

ip = fetch_ptr_or_default()
print(f"[*] Current IP: {ip}")

if spamhaus_check(ip):
    print("RESULT=BLOCKED (Spamhaus)")
    sys.exit(1)

# === SEND VIA SWAKS ===
cmd = [
    "swaks",
    "--to", TO_EMAIL,
    "--from", FROM_EMAIL,
    "--server", SMTP_SERVER,
    "--helo", helo_name,
    "--data", "-"
]

process = subprocess.Popen(
    cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

stdout, stderr = process.communicate(input=signed_email.encode())

print("====== SMTP STDOUT ======")
print(stdout.decode())
print("====== SMTP STDERR ======")
print(stderr.decode())

if b"250" in stdout:
    print("RESULT=SUCCESS")
    sys.exit(0)
else:
    print("RESULT=BLOCKED (SMTP)")
    sys.exit(1)
