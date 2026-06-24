import socket
import csv
import os
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText

FIELDS     = ["TIME","FSR2","FSR3","FSR4","FSR_TOTAL","FLEX1","AX","AY","AZ","GX","GY","GZ"]
CSV_FILE   = "/root/sensor_data.csv"
PHONE_IP   = "192.168.1.207"
PHONE_PORT = 6002

GMAIL_USER  = "ranak015m@gmail.com"
GMAIL_PASS  = "tftzpwualawcshny"
PHONE_EMAIL = "8777357142@jiophone.net"

SMS_INTERVAL   = 600
last_sms_time  = 0
last_recv_time = None

sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 6001))
phone = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

file_exists = os.path.isfile(CSV_FILE)
csvfile = open(CSV_FILE, 'a', newline='')
writer  = csv.writer(csvfile)
if not file_exists:
    writer.writerow(["TIMESTAMP"] + FIELDS + ["LATENCY_MS"])
    csvfile.flush()

def send_sms(data, latency):
    try:
        msg_body = f"""5G IoT Sensor Update
Time: {datetime.now().strftime('%H:%M:%S')}
AX:{data['AX']} AY:{data['AY']} AZ:{data['AZ']}
GX:{data['GX']} GY:{data['GY']} GZ:{data['GZ']}
FSR Total:{data['FSR_TOTAL']}
Flex:{data['FLEX1']}
Latency:{latency}ms"""
        msg            = MIMEText(msg_body)
        msg['From']    = GMAIL_USER
        msg['To']      = PHONE_EMAIL
        msg['Subject'] = '5G Sensor Alert'
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print("[SMS] Sent!")
    except Exception as e:
        print(f"[SMS ERROR] {e}")

print("=" * 60)
print("  UE1 ROOT BASH - Sensor Receiver")
print(f"  CSV   : {CSV_FILE}")
print(f"  SMS   : every 10 mins")
print("=" * 60)

while True:
    data, addr   = sock.recvfrom(4096)
    recv_time    = datetime.now()
    msg          = data.decode('utf-8', errors='ignore').strip()
    values       = msg.split(',')

    if len(values) == len(FIELDS):
        if last_recv_time is not None:
            latency_ms = int((recv_time - last_recv_time).total_seconds() * 1000)
        else:
            latency_ms = 0
        last_recv_time = recv_time

        timestamp = recv_time.strftime("%Y-%m-%d %H:%M:%S")
        entry     = {f: v for f, v in zip(FIELDS, values)}

        writer.writerow([timestamp] + values + [latency_ms])
        csvfile.flush()

        print("-" * 40)
        print(f"  TIMESTAMP       : {timestamp}")
        for field, val in zip(FIELDS, values):
            print(f"  {field:<12}    : {val}")
        print(f"  LATENCY         : {latency_ms} ms")

        phone.sendto((msg + f",{latency_ms}").encode('utf-8'), (PHONE_IP, PHONE_PORT))

        now = datetime.now().timestamp()
        if now - last_sms_time >= SMS_INTERVAL:
            threading.Thread(target=send_sms, args=(entry, latency_ms), daemon=True).start()
            last_sms_time = now
    else:
        print(f"[UE1] {msg}")
