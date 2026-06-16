import socket
import subprocess
import threading
import urllib.request
import time

PC_IP       = '0.0.0.0'
LISTEN_PORT = 5005
UE1_IP      = '12.1.1.3'
UE_PORT     = 6001
RENDER_URL  = 'https://sensor-dashboard-jqak.onrender.com/data'

def send_to_ue1(msg):
    python_cmd = (
        'import socket;'
        's=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);'
        's.bind(("12.1.1.3",0));'
        f's.sendto("{msg}".encode("utf-8"),("12.1.1.3",6001))'
    )
    subprocess.run([
        'sudo', 'docker', 'exec', 'rfsim5g-oai-nr-ue',
        'python3', '-c', python_cmd
    ])

def send_to_render(msg):
    try:
        data = msg.encode('utf-8')
        req  = urllib.request.Request(
            RENDER_URL,
            data=data,
            method='POST',
            headers={'Content-Type': 'text/plain'}
        )
        urllib.request.urlopen(req, timeout=15)
        print(f"[CLOUD] Sent to Render")
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
        if '\r\n\r\n' in raw:
            payload = raw.split('\r\n\r\n', 1)[1].strip()
        else:
            payload = raw.strip()
        if payload:
            print(f"[ARDUINO] {payload}")
            t1 = threading.Thread(target=send_to_ue1,    args=(payload,))
            t2 = threading.Thread(target=send_to_render, args=(payload,))
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
print(f"  UE1 tunnel  : {UE1_IP}:{UE_PORT}")
print(f"  Cloud URL   : {RENDER_URL}")
print("=" * 60)

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
