#!/usr/bin/env python3
import os
import sys
import time
import socket
import random
import subprocess
import threading
from queue import Queue
from email.mime.text import MIMEText
import dkim
import requests

pause_event = threading.Event()
pause_event.set()
completed_checkpoints = set()
consecutive_failures = 0
MAX_CONSECUTIVE_FAILS = 10

# ================= CONFIG =================
FROM_EMAIL = "fbeauty@rec-bestgoods.com"
SUBJECT = "why do you jerkoff alone? you can with me!"
DKIM_SELECTOR = "default"
DKIM_DOMAIN = "rec-bestgoods.com"
DKIM_KEY_FILE = "default.private"
EMAIL_LIST_FILE = "list.txt"
HTML_BODY_FILE = "body.html"
PROGRESS_FILE = "progress.txt"
NOTIFY_EMAIL = "mikassahax@outlook.com"
STATUS_FILE = "status.log"
CHECKPOINTS = [1200, 1500, 2200, 2600, 5200, 5500, 6200, 8500, 11000, 14000]

lock = threading.Lock()
success_count = 0


# ================= EMERGENCY SAVE PROGRESS =================
def emergency_save_progress():
    retry_delay = 2
    attempt = 0
    
    while True:
        attempt += 1
        try:
            subprocess.run(["git", "add", PROGRESS_FILE], check=True)
            status = subprocess.run(["git", "diff", "--cached", "--quiet"])
            if status.returncode == 0:
                write_status("EMERGENCY_PUSH_SKIPPED | No progress change")
                return
            
            subprocess.run(["git", "commit", "-m", f"Emergency progress save: {read_progress()}"], check=True)
            subprocess.run(["git", "push"], check=True)
            write_status("EMERGENCY_PUSH_SUCCESS | progress.txt saved to repo")
            return
            
        except Exception as e:
            write_status(f"EMERGENCY_PUSH_RETRY | Attempt {attempt} failed: {e}")
            time.sleep(retry_delay)

# ================= DELETE CODESPACE =================
def delete_own_codespace():
    codespace_name = os.environ.get("CODESPACE_NAME")
    gh_token = os.environ.get("MY_GITHUB_TOKEN")
    if not codespace_name or not gh_token:
        write_status("DELETE_FAIL | Missing env vars")
        return
    headers = {
        "Authorization": f"token {gh_token}",
        "Accept": "application/vnd.github+json"
    }
    r = requests.delete(
        f"https://api.github.com/user/codespaces/{codespace_name}",
        headers=headers
    )
    if r.status_code == 204:
        write_status(f"CODESPACE_DELETED | {codespace_name}")
    else:
        write_status(f"CODESPACE_DELETE_FAIL | {r.text}")


# ================= STATUS =================
def write_status(text):
    msg = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {text}"
    print(f"[STATUS] {msg}", flush=True)
    with open(STATUS_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


# ================= PROGRESS =================
def read_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return int(f.read().strip())
        except:
            return 0
    return 0


def save_progress(line):
    """
    Save current line number.
    If we reached (or passed) the last line of list.txt → reset to 0
    """
    try:
        with open(EMAIL_LIST_FILE, encoding="utf-8") as f:
            total_lines = sum(1 for line in f if "@" in line.strip())
    except Exception as e:
        write_status(f"ERROR_COUNTING_LINES | {e}")
        total_lines = 999999  # fallback

    if line >= total_lines:
        line = 0
        write_status(f"PROGRESS_RESET | Reached end of list ({total_lines} emails) → reset to 0")

    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        f.write(str(line))


# ================= PTR =================
def fetch_ptr():
    try:
        ip = requests.get("https://api.ipify.org", timeout=8).text.strip()
        ptr = socket.gethostbyaddr(ip)[0]
        return ip, ptr
    except Exception:
        return "0.0.0.0", "rec-bestgoods.com"


ip, ptr = fetch_ptr()


# ================= SMTP SEND FUNCTION =================
def swaks_send(to_email, signed_email):
    cmd = [
        "swaks",
        "--to", to_email,
        "--from", FROM_EMAIL,
        "--server", "outlook-com.olc.protection.outlook.com",
        "--helo", ptr,
        "--header", "X-Message-Flag: Flag for follow up",
        "--header", "Importance: high",
        "--header", "X-Priority: 1",
        "--timeout", "30",
        "--data", "-"
    ]
    p = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = p.communicate(input=signed_email.encode("utf-8"))
    output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
    return output, p.returncode


# ================= SMTP TEST =================
def smtp_test(private_key, label="INITIAL"):
    write_status(f"SMTP_TEST_START | {label}")
    msg = MIMEText(open(HTML_BODY_FILE, encoding="utf-8").read(), "html", "utf-8")
    msg["From"] = FROM_EMAIL
    msg["To"] = NOTIFY_EMAIL
    msg["Subject"] = SUBJECT

    signature = dkim.sign(
        msg.as_string().encode("utf-8"),
        DKIM_SELECTOR.encode("utf-8"),
        DKIM_DOMAIN.encode("utf-8"),
        private_key,
        include_headers=[b"from", b"to", b"subject"],
        canonicalize=(b"relaxed", b"relaxed")
    )
    signed_email = signature.decode("utf-8") + msg.as_string()

    out, rc = swaks_send(NOTIFY_EMAIL, signed_email)
    write_status("SMTP_TEST_OUTPUT | " + out[:400])

    fail_conditions = [
        rc != 0,
        "550" in out,
        "554" in out,
        "Spamhaus" in out,
        "blocked" in out.lower()
    ]

    if any(fail_conditions):
        write_status(f"SMTP_TEST_FAIL | {label}")
        emergency_save_progress()
        delete_own_codespace()
        sys.exit(1)

    if any(x in out for x in ["250 2.0.0", "250 2.6.0", "Queued mail for delivery"]):
        write_status(f"SMTP_TEST_OK | {label}")
        return True

    write_status(f"SMTP_TEST_UNKNOWN | {label}")
    return False


# ================= SEND EMAIL =================
def send_email(to_email, private_key, line_number):
    global success_count

    time.sleep(random.uniform(0.08, 0.12))  # ~8.7–11.8 emails/sec

    msg = MIMEText(open(HTML_BODY_FILE, encoding="utf-8").read(), "html", "utf-8")
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = SUBJECT

    signature = dkim.sign(
        msg.as_string().encode("utf-8"),
        DKIM_SELECTOR.encode("utf-8"),
        DKIM_DOMAIN.encode("utf-8"),
        private_key,
        include_headers=[b"from", b"to", b"subject"],
        canonicalize=(b"relaxed", b"relaxed")
    )

    signed_email = signature.decode("utf-8") + msg.as_string()

    out, rc = swaks_send(to_email, signed_email)

    success_keywords = ["250 2.0.0", "250 2.6.0", "Queued mail for delivery"]
    if any(kw in out for kw in success_keywords):
        with lock:
            success_count += 1
            current = success_count
        write_status(f"SMTP_OK | SENT:{to_email} | LINE:{line_number}")
        return True

    fail_keywords = ["550", "554", "Spamhaus", "blocked"]
    if rc != 0 or any(kw in out.lower() for kw in fail_keywords):
        write_status(f"SMTP_FAIL | {to_email}")
        return False

    write_status(f"SMTP_UNKNOWN_RESULT | {to_email}")
    return False


# ================= WORKER =================
def worker():
    global consecutive_failures
    while True:
        pause_event.wait()
        item = queue.get()
        if item is None:
            break
        line, email = item

        ok = send_email(email, private_key, line)
        save_progress(line)

        if ok:
            consecutive_failures = 0
            with lock:
                current = success_count
                if current in CHECKPOINTS and current not in completed_checkpoints:
                    completed_checkpoints.add(current)
                    write_status(f"CHECKPOINT_REACHED | {current}")
                    pause_event.clear()

                    if not smtp_test(private_key, f"CHECKPOINT_{current}"):
                        write_status("CHECKPOINT_SMTP_TEST_FAILED → STOPPING")
                        sys.exit(1)

                    write_status(f"CHECKPOINT_OK | {current} | CONTINUE")
                    pause_event.set()
        else:
            with lock:
                consecutive_failures += 1
                current_streak = consecutive_failures

            write_status(f"CRITICAL_FAIL_STOPPING | {email} | "
                         f"consecutive failures: {current_streak}/{MAX_CONSECUTIVE_FAILS}")

            if current_streak >= MAX_CONSECUTIVE_FAILS:
                write_status(f"TOO_MANY_CONSECUTIVE_FAILURES | {current_streak} in a row → STOPPING")
                emergency_save_progress()
                delete_own_codespace()
                sys.exit(1)

        queue.task_done()


# ================= MAIN =================
if __name__ == "__main__":
    try:
        private_key = open(DKIM_KEY_FILE, "rb").read()
    except FileNotFoundError:
        write_status(f"KEY_NOT_FOUND | {DKIM_KEY_FILE}")
        sys.exit(1)

    # First SMTP check
    if not smtp_test(private_key, "START"):
        sys.exit(1)

    emails = [x.strip() for x in open(EMAIL_LIST_FILE, encoding="utf-8") if "@" in x]
    start_line = read_progress()
    emails = emails[start_line:]

    queue = Queue()

    # Start workers
    threads = []
    for _ in range(10):
        t = threading.Thread(target=worker, daemon=True)
        t.start()
        threads.append(t)

    # Feed queue
    for i, email in enumerate(emails, start_line + 1):
        queue.put((i, email))
        if i % 10 == 0:
            save_progress(i)

    queue.join()

    write_status("DONE | ALL EMAILS SENT")
    print("🎉 All emails sent successfully!")
