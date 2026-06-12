from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import threading

app = Flask(__name__)

# Store latest data and history
latest  = {}
history = []
lock    = threading.Lock()

MAX_HISTORY = 50  # keep last 50 readings

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data', methods=['POST'])
def receive_data():
    raw = request.data.decode('utf-8').strip()
    fields = ["TIME","FSR2","FSR3","FSR4","FSR_TOTAL","FLEX1","AX","AY","AZ","GX","GY","GZ"]
    values = raw.split(',')
    if len(values) == len(fields):
        arduino_time = int(values[0])
        server_time  = int(datetime.now().timestamp() * 1000)
        latency_ms   = server_time - arduino_time

        entry = {f: v for f, v in zip(fields, values)}
        entry['TIMESTAMP']        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry['SERVER_TIME']      = server_time
        entry['ARDUINO_TIME']     = arduino_time
        entry['LATENCY_ARDUINO_TO_CLOUD_MS'] = latency_ms

        with lock:
            global latest, history
            latest = entry
            history.append(entry)
            if len(history) > MAX_HISTORY:
                history.pop(0)

        print(f"[DATA] {entry['TIMESTAMP']} | Latency: {latency_ms}ms | {raw}")
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
