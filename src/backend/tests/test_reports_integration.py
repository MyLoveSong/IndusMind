import os
import time
import json
import requests
import subprocess
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

LLM_PORT = 9999
NODE_PORT = 3011

class StubHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        # simple heuristic: if prompt asks to generate outline (contains '为"' or '大纲'), return JSON
        if '大纲' in body or '为\"' in body:
            content = json.dumps({
                "outline": [{"title":"执行摘要","bullets":["要点1","要点2"]}],
                "highlights": ["亮点1"],
                "metrics": {"timeline":"1天"}
            }, ensure_ascii=False)
        else:
            content = "这是生成的章节内容。示例段落，供测试使用。"
        resp = {"choices":[{"message":{"content": content}}]}
        resp_bytes = json.dumps(resp, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

def start_stub_server():
    server = HTTPServer(('0.0.0.0', LLM_PORT), StubHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

def start_node_server():
    node_bin = "/home/xzy/QWEN3-8B/node.js/bin/node"
    server_js = "/home/xzy/QWEN3-8B/ZJU-SEM-Project-master/backend/server.js"
    env = os.environ.copy()
    env.update({
        "PORT": str(NODE_PORT),
        "SILICONFLOW_BASE_URL": f"http://127.0.0.1:{LLM_PORT}",
        "SILICONFLOW_API_KEY": "test"
    })
    # If server is already healthy, return a dummy terminator
    try:
        r = requests.get(f"http://127.0.0.1:{NODE_PORT}/health", timeout=1)
        if r.status_code == 200:
            class DummyProc:
                def terminate(self_inner): pass
            return DummyProc()
    except Exception:
        pass

    proc = subprocess.Popen([node_bin, server_js], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # wait for health
    for _ in range(30):
        try:
            r = requests.get(f"http://127.0.0.1:{NODE_PORT}/health", timeout=1)
            if r.status_code == 200:
                return proc
        except Exception:
            time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("Node server failed to start")

def test_reports_flow():
    stub = start_stub_server()
    node_proc = start_node_server()
    try:
        url = f"http://127.0.0.1:{NODE_PORT}"
        headers = {}
        # If SKIP_AUTH is set, bypass registration/login and let server middleware inject a test user
        if os.environ.get("SKIP_AUTH") == "1":
            headers = {"Authorization": "Bearer skip"}
        else:
            # register user
            reg = requests.post(url + "/api/auth/register", json={"username":"tuser","email":"t@test","password":"pass"}, timeout=5)
            # allow already-exists (409) from previous runs
            assert reg.status_code in (200, 201, 409)
            # login
            login = requests.post(url + "/api/auth/login", json={"username":"tuser","password":"pass"}, timeout=5)
            assert login.status_code == 200
            token = login.json().get("token")
            assert token
            headers = {"Authorization": f"Bearer {token}"}
        # create report
        resp = requests.post(url + "/api/reports", headers=headers, data={"title":"T","industry":"I"}, timeout=30)
        assert resp.status_code == 201
        reportId = resp.json().get("reportId")
        assert reportId
        # generate full report
        gen = requests.post(f"{url}/api/reports/{reportId}/generate", headers=headers, timeout=60)
        assert gen.status_code == 200
        j = gen.json()
        assert j.get("success") is True
        assert j.get("content")
        # chat
        chat = requests.post(f"{url}/api/reports/{reportId}/chat", headers=headers, json={"message":"请总结"}, timeout=30)
        assert chat.status_code == 201
        body = chat.json()
        assert "reply" in body or "messageId" in body
    finally:
        try:
            node_proc.terminate()
        except:
            pass
        try:
            stub.shutdown()
        except:
            pass

