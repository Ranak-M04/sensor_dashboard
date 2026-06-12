import socket
from datetime import datetime

FIELDS = ["TIME","FSR2","FSR3","FSR4","FSR_TOTAL","FLEX1","AX","AY","AZ","GX","GY","GZ","LAT_UE1"]

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('0.0.0.0', 6002))

print("=" * 50)
print("  PHONE TERMUX - Live Sensor Data")
print("  Waiting for data from UE1...")
print("=" * 50)

while True:
    data, addr      = sock.recvfrom(4096)
    receive_time    = int(datetime.now().timestamp() * 1000)
    msg             = data.decode('utf-8', errors='ignore').strip()
    values          = msg.split(',')

    if len(values) >= 12:
        arduino_time    = int(values[0])
        latency_phone   = receive_time - arduino_time
        latency_ue1     = values[12] if len(values) > 12 else "N/A"
        timestamp       = datetime.now().strftime("%H:%M:%S")

        print("-" * 40)
        print(f"  TIME       : {timestamp}")
        print(f"  AX/AY/AZ   : {values[6]}, {values[7]}, {values[8]}")
        print(f"  GX/GY/GZ   : {values[9]}, {values[10]}, {values[11]}")
        print(f"  FSR Total  : {values[4]}")
        print(f"  FLEX1      : {values[5]}")
        print(f"  LAT→UE1    : {latency_ue1} ms")
        print(f"  LAT→PHONE  : {latency_phone} ms")
    else:
        print(f"[DATA] {msg}")
