from flask import Flask, render_template, request, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

latest  = {}
history = []
lock    = threading.Lock()
MAX_HISTORY = 50

@app.route('/')
def index():
    return render_template('index.html', active='overview')

@app.route('/motion')
def motion():
    return render_template('motion.html', active='motion')

@app.route('/pressure')
def pressure():
    return render_template('pressure.html', active='pressure')

@app.route('/network')
def network():
    return render_template('network.html', active='network')

@app.route('/data', methods=['POST'])
def receive_data():
    raw = request.data.decode('utf-8').strip()
    fields = ["TIME","FSR2","FSR3","FSR4","FSR_TOTAL","FLEX1","AX","AY","AZ","GX","GY","GZ","PC_RECV_MS"]
    values = raw.split(',')
    if len(values) == len(fields):
        cloud_recv_ms = int(datetime.now().timestamp() * 1000)
        pc_recv_ms    = int(values[12])
        latency_ms    = cloud_recv_ms - pc_recv_ms  # real PC→Cloud latency

        entry = {f: v for f, v in zip(fields[:12], values[:12])}
        entry['TIMESTAMP']                   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry['SERVER_TIME_MS']              = cloud_recv_ms
        entry['PC_RECV_MS']                  = pc_recv_ms
        entry['LATENCY_ARDUINO_TO_CLOUD_MS'] = latency_ms
        entry['ARDUINO_TIME']                = values[0]

        with lock:
            global latest, history
            latest = entry
            history.append(entry)
            if len(history) > MAX_HISTORY:
                history.pop(0)

        print(f"[DATA] {entry['TIMESTAMP']} | PC→Cloud: {latency_ms}ms")
    return 'OK', 200

@app.route('/api/latest')
def api_latest():
    with lock:
        return jsonify(latest)

@app.route('/api/history')
def api_history():
    with lock:
        return jsonify(history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
