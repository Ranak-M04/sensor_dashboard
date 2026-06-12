import socket
import csv
import os
from datetime import datetime

FIELDS     = ["TIME","FSR2","FSR3","FSR4","FSR_TOTAL","FLEX1","AX","AY","AZ","GX","GY","GZ"]
CSV_FILE   = "/root/sensor_data.csv"
PHONE_IP   = "192.168.1.207"
PHONE_PORT = 6002

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 6001))

phone = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

file_exists = os.path.isfile(CSV_FILE)
csvfile = open(CSV_FILE, 'a', newline='')
writer  = csv.writer(csvfile)
if not file_exists:
    writer.writerow(["TIMESTAMP"] + FIELDS + ["LATENCY_ARDUINO_TO_UE1_MS"])
    csvfile.flush()

print("=" * 60)
print("  UE1 ROOT BASH - Sensor Receiver")
print(f"  CSV     : {CSV_FILE}")
print(f"  Phone   : {PHONE_IP}:{PHONE_PORT}")
print("=" * 60)

while True:
    data, addr = sock.recvfrom(4096)
    receive_time = int(datetime.now().timestamp() * 1000)
    msg    = data.decode('utf-8', errors='ignore').strip()
    values = msg.split(',')

    if len(values) == len(FIELDS):
        arduino_time = int(values[0])
        latency_ms   = receive_time - arduino_time
        timestamp    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Save to CSV
        writer.writerow([timestamp] + values + [latency_ms])
        csvfile.flush()

        # Print formatted
        print("-" * 40)
        print(f"  TIMESTAMP        : {timestamp}")
        for field, val in zip(FIELDS, values):
            print(f"  {field:<12}     : {val}")
        print(f"  LATENCY (A→UE1)  : {latency_ms} ms")

        # Forward to phone with latency appended
        msg_with_lat = msg + f",{latency_ms}"
        phone.sendto(msg_with_lat.encode('utf-8'), (PHONE_IP, PHONE_PORT))
    else:
        print(f"[UE1] {msg}")
