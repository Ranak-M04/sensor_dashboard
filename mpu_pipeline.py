import socket
import subprocess
import threading
import urllib.request
import time
from datetime import datetime

PC_IP        = '0.0.0.0'
LISTEN_PORT  = 5005
UE_PORT      = 6001
RENDER_URL   = 'https://sensor-dashboard-jqak.onrender.com/data'
UE_CONTAINER = 'rfsim5g-oai-nr-ue'

def get_ue_ip():
    try:
        result = subprocess.run([
            'sudo', 'docker', 'exec', UE_CONTAINER,
            'ip', 'addr', 'show', 'oaitun_ue1'
        ], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if 'inet ' in line:
                ip = line.strip().split()[1].split('/')[0]
                return ip
    except Exception as e:
        print(f"[UE IP ERROR] {e}")
    return None

def send_to_ue1(msg):
    ue_ip = get_ue_ip()
    if not ue_ip:
        print("[UE] Tunnel not found, skipping")
        return
    python_cmd = (
        'import socket;'
        's=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);'
        f's.bind(("{ue_ip}",0));'
        f's.sendto("{msg}".encode("utf-8"),("{ue_ip}",{UE_PORT}))'
    )
    subprocess.run([
        'sudo', 'docker', 'exec', UE_CONTAINER,
        'python3', '-c', python_cmd
    ])

def send_to_render(msg, pc_recv_ms):
    try:
        # Append PC receive timestamp so cloud can compute transit time
        msg_with_ts = msg + f",{pc_recv_ms}"
        req = urllib.request.Request(
            RENDER_URL,
            data=msg_with_ts.encode('utf-8'),
            method='POST',
            headers={'Content-Type': 'text/plain'}
        )
        urllib.request.urlopen(req, timeout=15)
        cloud_recv_ms = int(datetime.now().timestamp() * 1000)
        latency = cloud_recv_ms - pc_recv_ms
        print(f"[CLOUD] Sent | PC→Cloud latency: {latency}ms")
    except Exception as e:
        print(f"[CLOUD ERROR] {e}")

def handle_client(conn, addr):
    with conn:
        data = b''
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        raw = data.decode('utf-8', errors='ignore')
        payload = raw.split('\r\n\r\n', 1)[1].strip() if '\r\n\r\n' in raw else raw.strip()
        if payload:
            pc_recv_ms = int(datetime.now().timestamp() * 1000)
            print(f"[ARDUINO] {payload}")
            t1 = threading.Thread(target=send_to_ue1,    args=(payload,))
            t2 = threading.Thread(target=send_to_render, args=(payload, pc_recv_ms))
            t1.start()
            t2.start()
            t1.join()
            t2.join()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((PC_IP, LISTEN_PORT))
server.listen(10)

print("=" * 60)
print("  Arduino -> PC -> UE1 (5G) + Render (Cloud)")
print("=" * 60)
print(f"  Listening   : port {LISTEN_PORT}")
print(f"  Cloud URL   : {RENDER_URL}")
ue_ip = get_ue_ip()
print(f"  UE1 IP      : {ue_ip}")
print("=" * 60)

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
