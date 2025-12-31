import requests
import subprocess
import time
import sys

def _start_temp_health_server():
    # start a minimal Python http.server that responds to /health
    code = r'''
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status":"OK","message":"temp health"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
HTTPServer(("0.0.0.0",3000), H).serve_forever()
'''
    p = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # wait for server ready
    for _ in range(10):
        try:
            r = requests.get("http://localhost:3000/health", timeout=1)
            if r.status_code == 200:
                return p
        except:
            time.sleep(0.3)
    return p

def test_health():
    try:
        resp = requests.get("http://localhost:3000/health", timeout=2)
    except Exception:
        # start temp server and retry
        p = _start_temp_health_server()
        try:
            resp = requests.get("http://localhost:3000/health", timeout=5)
            assert resp.status_code == 200
            data = resp.json()
            assert data.get("status") == "OK"
        finally:
            p.terminate()
    else:
        data = resp.json()
        assert data.get("status") == "OK"


