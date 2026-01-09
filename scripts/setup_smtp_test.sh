#!/bin/bash
set -e

echo "[*] Installing dependencies..."
sudo apt update
sudo apt install -y swaks dnsutils vim

# Install Python packages for the session
pip3 install --no-cache-dir dkimpy requests

echo "[*] Running SMTP test..."
python3 test.py || {
    echo "❌ SMTP test failed. Exiting Codespace."
    exit 1
}

echo "[*] SMTP test passed. Starting email sending session..."
python3 -u send_emails.py
