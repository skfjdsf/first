#!/usr/bin/env python3

# """make sure to instal pip install --user dkimpy""" pip3 install requests
# mkdir email && cd email && pip install --user dkimpy && scp rdpuser@132.226.65.42:/home/rdpuser/replit/* /home/runner/workspace/email/ && vi ~/.bashrc
# 
import socket
import subprocess
import dkim
from email.mime.text import MIMEText
import os
import time
import threading
from queue import Queue
import sys
import requests
import random
# === CHECKPOINTS - Test at these email counts THIS SESSION ===
CHECKPOINTS = [1200, 1500, 2200, 2600, 5200, 5500, 6200, 8500, 11000, 14000, 18000]
subjects = {
    "Re: 💕 Do you want to meet ?",
    "Re: Are you free for s*xting tonight 💋?",
    "87 girls in your area ready to f*ck now!",
    "(1) Private message for you",
    "Attractive women nearby want a date.",
    "Local singles seeking casual encounters.",
    "Wanna hook up this afternoon?",
    "so you're into dirty texting?",  
    "(1) Unread message for you",
    "Stop doing it solo when we can do together!",
    "Re: Your profile turns me on.",
    "Who needs romance, let's hook up.",
    "That special someone awaits your message.",
    "Re: My bed is lonely tonight.",
    "Imagining you while I touch myself ",
    "Foreign women want your attention."
}

from_email = 'Maica@rusmika.space'
dkim_selector = 'default'
dkim_domain = 'rusmika.space'
dkim_key_file = 'default.private'
email_list_file = 'list.txt'
html_body_file = 'body.html'
progress_file = 'progress.txt'
notify_email = 'mikassahax@outlook.com'



# === READ HTML BODY FROM FILE ===
try:
    with open(html_body_file, 'r', encoding='utf-8') as f:
        html_body = f.read()
    print(f"✓ Loaded HTML body from {html_body_file}")
except FileNotFoundError:
    print(f"❌ Error: {html_body_file} not found!")
    sys.exit(1)

# Global counters
success_count = 0
lock = threading.Lock()
should_stop = False

# === FUNCTION TO READ PROGRESS (line number in list.txt) ===
def read_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            try:
                return int(f.read().strip())
            except:
                return 0
    return 0

# === FUNCTION TO SAVE PROGRESS (line number in list.txt) ===
def save_progress(line_number):
    with open(progress_file, 'w') as f:
        f.write(str(line_number))



## function for ptr
def fetch_ptr_or_default(default="lovconnect.online"):
    # 1. Get public IP from ifconfig.co
    ip = requests.get("https://ifconfig.co/ip").text.strip()

    # 2. Try to resolve PTR
    try:
        ptr = socket.gethostbyaddr(ip)[0]
    except Exception:
        ptr = default  # fallback if no PTR found

    return ip, ptr

ip, ptr = fetch_ptr_or_default()

# === FUNCTION TO SEND EMAIL ===
def send_email(to_email, subject, body, private_key):
    global success_count


    
    msg = MIMEText(body, 'html', 'utf-8')
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    
    signature = dkim.sign(
        message=msg.as_string().encode(),
        selector=dkim_selector.encode(),
        domain=dkim_domain.encode(),
        privkey=private_key,
        include_headers=[b'from', b'to', b'subject'],
        canonicalize=(b'relaxed', b'relaxed')
    )
    
    signed_email = signature.decode() + msg.as_string()
    recipient_domain = to_email.split('@')[1]
    
    process = subprocess.Popen(
        [
            'swaks',
            '--to', to_email,
            '--from', from_email,
            '--server', 'outlook-com.olc.protection.outlook.com',
            # Header 1: Follow up flag
            '--header', 'X-Message-Flag: Flag for follow up',
            # Header 2: High Importance
            '--header', 'Importance: high',
            # Header 3: Priority Level
            '--header', 'X-Priority: 1',
            '--helo', ptr,
            # Data Input (Stdin)
            '--data', '-'
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    stdout, stderr = process.communicate(input=signed_email.encode())
    success = "250" in stdout.decode()
    
    if success:
        with lock:
            success_count += 1
    
    return success

# === FUNCTION TO TEST SMTP (uses same email format) ===
def test_smtp(private_key):
    """Test if emails are being accepted using actual email format"""


    try:
        print("\n" + "="*50)
        print("🔍 TESTING SMTP CONNECTION...")
        print("="*50)
        
        # Create test email with DKIM signature (same as real emails)
        msg = MIMEText(html_body, 'html', 'utf-8')
        msg['From'] = from_email
        msg['To'] = notify_email
        msg['Subject'] = "This is a test email"
        
        signature = dkim.sign(
            message=msg.as_string().encode(),
            selector=dkim_selector.encode(),
            domain=dkim_domain.encode(),
            privkey=private_key,
            include_headers=[b'from', b'to', b'subject'],
            canonicalize=(b'relaxed', b'relaxed')
        )
        
        signed_email = signature.decode() + msg.as_string()
        
        # Send test email using swaks
        process = subprocess.Popen(
            [
                'swaks',
                '--to', notify_email,
                '--from', from_email,
                '--server', 'outlook-com.olc.protection.outlook.com',
                # Header 1: Follow up flag
                '--header', 'X-Message-Flag: Flag for follow up',
                # Header 2: High Importance
                '--header', 'Importance: high',
                # Header 3: Priority Level
                '--header', 'X-Priority: 1',
                '--helo', ptr,
                # Data Input (Stdin)
                '--data', '-'
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate(input=signed_email.encode())
        output = stdout.decode()
        
        print(output)
        
        if "Queued mail for delivery" in output:
            print("✅ TEST PASSED - Continuing...\n")
            return True
        else:
            print("❌ TEST FAILED - Exiting script!\n")

            time.sleep(7)
            os.system("kill 1")
            return False
            
    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        print("Exiting script!\n")
        return False

# === READ DKIM KEY ===
try:
    with open(dkim_key_file, 'rb') as f:
        private_key = f.read()
    print(f"✓ Loaded DKIM key from {dkim_key_file}")
except FileNotFoundError:
    print(f"❌ Error: {dkim_key_file} not found!")
    sys.exit(1)

# === INITIAL TEST ===
print("\n" + "="*50)
print("🚀 INITIAL SMTP TEST")
print("="*50)
if not test_smtp(private_key):
    print("❌ Initial SMTP test failed. Not sending emails.")
    sys.exit(1)

send = 'true'

# Worker function
def worker(queue, private_key):
    global should_stop
    while True:
        item = queue.get()
        if item is None or should_stop:
            queue.task_done()
            break
        
        list_position, to_email, total_in_list = item
        subject = random.choice(list(subjects))
        result = send_email(to_email, subject, html_body, private_key)
        
        with lock:
            status = "✓" if result else "✗"
            print(f"[Line {list_position}/{total_in_list}] {to_email} - {status}")
        
        queue.task_done()

# === READ EMAILS ===
try:
    with open(email_list_file, 'r') as f:
        all_emails = [line.strip() for line in f if line.strip() and '@' in line]
    print(f"✓ Loaded {len(all_emails)} emails from {email_list_file}")
except FileNotFoundError:
    print(f"❌ Error: {email_list_file} not found!")
    sys.exit(1)

# Read where we left off in list.txt
start_line = read_progress()
print(f"📍 Resuming from line {start_line} in list.txt")

# Get all remaining emails
emails_to_send = all_emails[start_line:]
total_emails_in_list = len(all_emails)

if len(emails_to_send) == 0:
    print("✅ All emails in list.txt have been sent!")
    sys.exit(0)

print(f"📧 Will send {len(emails_to_send)} remaining emails")
print(f"📊 Total in list.txt: {total_emails_in_list}")

# === SEND EMAILS ===
if send == 'true':
    print("\n🚀 Starting to send emails at 10 per second...\n")
    
    queue = Queue()
    num_threads = 10
    
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(queue, private_key))
        t.start()
        threads.append(t)
    
    emails_sent_this_session = 0
    
    for i, to_email in enumerate(emails_to_send, 1):
        if should_stop:
            break
        
        emails_sent_this_session += 1
        current_line_in_list = start_line + i
        
        # CHECK CHECKPOINT (based on emails sent THIS SESSION, not line number)
        if emails_sent_this_session in CHECKPOINTS:
            # Wait for queue to finish
            queue.join()
            
            print(f"\n{'='*60}")
            print(f"🎯 CHECKPOINT: {emails_sent_this_session} emails sent this session")
            print(f"📍 Currently at line {current_line_in_list} in list.txt")
            print(f"{'='*60}")
            
            # Run SMTP test using same format
            if not test_smtp(private_key):
                print(f"\n❌ CHECKPOINT FAILED after {emails_sent_this_session} emails!")
                print(f"📍 Stopped at line {current_line_in_list} in list.txt")
                print("Saving progress and exiting...\n")
                
                should_stop = True
                
                # Stop workers
                for _ in range(num_threads):
                    queue.put(None)
                for t in threads:
                    t.join()
                
                # Save current line position in list.txt
                save_progress(current_line_in_list)
                
                # Send notification
                fail_subject = f"⚠️ Script stopped at checkpoint {emails_sent_this_session}"
                fail_body = f"""
                <html><body>
                    <h2>⚠️ Script Stopped!</h2>
                    <p><strong>Reason:</strong> Checkpoint test failed</p>
                    <p><strong>Emails sent this session:</strong> {emails_sent_this_session}</p>
                    <p><strong>Stopped at line:</strong> {current_line_in_list} in list.txt</p>
                    <p><strong>Successful:</strong> {success_count}</p>
                    <p><strong>Progress saved.</strong> Run script again to continue from line {current_line_in_list}.</p>
                </body></html>
                """
                send_email(notify_email, fail_subject, fail_body, private_key)
                
                sys.exit(1)
            
            print(f"✅ Checkpoint {emails_sent_this_session} passed!\n")
        
        queue.put((current_line_in_list, to_email, total_emails_in_list))
        
        # Save progress every 10 emails
        if i % 10 == 0:
            save_progress(current_line_in_list)
        
        time.sleep(0.1)
    
    # Wait for all to finish
    queue.join()
    
    # Stop workers
    for _ in range(num_threads):
        queue.put(None)
    for t in threads:
        t.join()
    
    final_line = start_line + emails_sent_this_session
    save_progress(final_line)


    if total_emails_in_list - final_line == 0:
        save_progress(0)
        
    
    # Final notification
    final_subject = f"✅ Session complete: {emails_sent_this_session} emails sent"
    final_body = f"""
    <html><body>
        <h2>🎉 Session Complete!</h2>
        <p><strong>Emails sent this session:</strong> {emails_sent_this_session}</p>
        <p><strong>Successful:</strong> {success_count}</p>
        <p><strong>Failed:</strong> {emails_sent_this_session - success_count}</p>
        <p><strong>Final position:</strong> Line {final_line} / {total_emails_in_list} in list.txt</p>
        <p><strong>Remaining:</strong> {total_emails_in_list - final_line}</p>
    </body></html>
    """
    
    print(f"\n📧 Sending final notification...")
    send_email(notify_email, final_subject, final_body, private_key)
    
    print(f"\n🎉 Session complete!")
    print(f"✓ Sent {success_count}/{emails_sent_this_session} emails this session")
    print(f"📍 Stopped at line {final_line} in list.txt")
    print(f"📋 Remaining: {total_emails_in_list - final_line}")
    
else:
    print("❌ Initial test failed.")
