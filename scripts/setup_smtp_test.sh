#!/bin/bash
set -e

# Get the directory where this script is located, then go up one level
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "[*] Installing dependencies..."
sudo apt update
sudo apt install -y swaks dnsutils vim

# Install Python packages for the session
pip3 install --no-cache-dir dkimpy requests

echo "[*] Running SMTP test..."
python3 "$PROJECT_ROOT/test.py" || {
    echo "❌ SMTP test failed. Exiting Codespace."
    exit 1
}

echo "[*] SMTP test passed. Starting email sending session..."
python3 -u "$PROJECT_ROOT/send_emails.py"
