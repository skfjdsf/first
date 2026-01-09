#!/bin/bash
set -e

echo "[*] Running email session..."
python3 -u send_emails.py

echo "[*] progress.txt pushed to GitHub, safe to delete Codespace."
