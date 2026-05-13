import http.server
import socketserver
import os
import sys
import json
import subprocess
import uuid
import datetime
import threading
import queue
import fcntl
from contextlib import contextmanager

PORT = 8000
LOG_TAIL_BYTES = 60000
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_BIN = "/home/ubuntu/.pyenv/versions/3.12.2/bin/python3"
LOG_FILE = os.path.join(BASE_DIR, "auto_blog.log")
PIPELINES_FILE = os.path.join(BASE_DIR, "config", "pipelines.json")
ONEOFF_HISTORY_FILE = os.path.join(BASE_DIR, "config", "oneoff_history.json")
ONEOFF_HISTORY_LOCK_FILE = os.path.join(BASE_DIR, "config", "oneoff_history.lock")
ONEOFF_REQUEST_DIR = os.path.join(BASE_DIR, "config", "oneoff_requests")
RUN_QUEUE = queue.Queue()
QUEUE_LOCK = threading.Lock()
RUN_STATUS = {
    "running": None,
    "queued": [],
    "history": []
}

if not os.path.exists(os.path.dirname(PIPELINES_FILE)):
    os.makedirs(os.path.dirname(PIPELINES_FILE))
if not os.path.exists(PIPELINES_FILE):
    with open(PIPELINES_FILE, 'w') as f:
        json.dump([], f)
if not os.path.exists(ONEOFF_REQUEST_DIR):
    os.makedirs(ONEOFF_REQUEST_DIR)

def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")

def append_history(item, status, message=None):
    finished = dict(item)
    finished["status"] = status
    finished["finished_at"] = now_iso()
    if message:
        finished["message"] = message
    RUN_STATUS["history"].insert(0, finished)
    RUN_STATUS["history"] = RUN_STATUS["history"][:20]

def pipeline_exists(pid):
    pipelines = load_json_file(PIPELINES_FILE, [])
    return next((p for p in pipelines if p.get('id') == pid), None)

def load_json_file(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default

def save_json_file(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@contextmanager
def file_lock(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)

def add_oneoff_history(item):
    with file_lock(ONEOFF_HISTORY_LOCK_FILE):
        history = load_json_file(ONEOFF_HISTORY_FILE, [])
        history.insert(0, item)
        save_json_file(ONEOFF_HISTORY_FILE, history[:100])

def read_log_tail(path, max_bytes=LOG_TAIL_BYTES):
    if not os.path.exists(path):
        return "No logs yet."

    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        if size > max_bytes:
            f.seek(-max_bytes, os.SEEK_END)
            f.readline()
        data = f.read()
    return data.decode('utf-8', errors='replace')

def run_worker():
    while True:
        item = RUN_QUEUE.get()
        with QUEUE_LOCK:
            RUN_STATUS["queued"] = [q for q in RUN_STATUS["queued"] if q["run_id"] != item["run_id"]]
            RUN_STATUS["running"] = item

        kind = item.get("kind", "pipeline")
        job_id = item.get("pipeline_id") or item.get("oneoff_id")
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            if kind == "oneoff":
                cmd = [PYTHON_BIN, "-u", "run_oneoff.py", item["request_path"]]
            else:
                cmd = [PYTHON_BIN, "-u", "run_pipeline.py", item["pipeline_id"]]
            with open(LOG_FILE, "a", buffering=1) as log:
                log.write(f"\n--- Queued run started: {kind}:{job_id} ({item['run_id']}) ---\n")
                proc = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    start_new_session=True,
                )
                code = proc.wait()
                log.write(f"\n--- Queued run finished: {kind}:{job_id} ({item['run_id']}) exit={code} ---\n")
            with QUEUE_LOCK:
                append_history(item, "completed" if code == 0 else "failed", f"exit={code}")
        except Exception as e:
            with open(LOG_FILE, "a", buffering=1) as log:
                log.write(f"\n--- Queued run failed: {kind}:{job_id} ({item['run_id']}) {e} ---\n")
            with QUEUE_LOCK:
                append_history(item, "failed", str(e))
        finally:
            with QUEUE_LOCK:
                if RUN_STATUS["running"] and RUN_STATUS["running"]["run_id"] == item["run_id"]:
                    RUN_STATUS["running"] = None
            RUN_QUEUE.task_done()

threading.Thread(target=run_worker, daemon=True).start()

def sync_cron(pipelines):
    try:
        current_cron = subprocess.check_output(["crontab", "-l"]).decode()
    except:
        current_cron = ""
        
    # Remove all run_pipeline.py jobs
    lines = [l for l in current_cron.strip('\n').split('\n') if l and "run_pipeline.py" not in l]
    
    # Add active pipelines
    for p in pipelines:
        schedule = p.get('schedule', '0 9 * * *')
        pid = p.get('id')
        job = f"{schedule} cd {BASE_DIR} && PYTHONUNBUFFERED=1 {PYTHON_BIN} -u run_pipeline.py {pid} >> {LOG_FILE} 2>&1"
        lines.append(job)
        
    new_cron = '\n'.join(lines) + '\n'
    proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE)
    proc.communicate(new_cron.encode())

class AutoBloggerHandler(http.server.SimpleHTTPRequestHandler):
    def read_json_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        return {}

    def safe_read_json_body(self):
        try:
            return self.read_json_body()
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON body."}, 400)
            return None

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == '/api/logs':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(read_log_tail(LOG_FILE).encode())
        elif self.path == '/api/pipelines':
            pipelines = load_json_file(PIPELINES_FILE, [])
            self.send_json({"pipelines": pipelines})
        elif self.path == '/api/queue':
            with QUEUE_LOCK:
                self.send_json({
                    "running": RUN_STATUS["running"],
                    "queued": RUN_STATUS["queued"],
                    "history": RUN_STATUS["history"]
                })
        elif self.path == '/api/oneoff/history':
            with file_lock(ONEOFF_HISTORY_LOCK_FILE):
                history = load_json_file(ONEOFF_HISTORY_FILE, [])
            self.send_json({"history": history[:100]})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/api/run':
            data = self.safe_read_json_body()
            if data is None:
                return
            pid = data.get('id')
            if not pid:
                self.send_json({"error": "Pipeline ID is required."}, 400)
                return

            pipeline = pipeline_exists(pid)
            if not pipeline:
                self.send_json({"error": f"Pipeline {pid} not found."}, 404)
                return

            with QUEUE_LOCK:
                if RUN_STATUS["running"] and RUN_STATUS["running"].get("pipeline_id") == pid:
                    self.send_json({"status": "already_running", "running": RUN_STATUS["running"]}, 409)
                    return
                duplicate = next((q for q in RUN_STATUS["queued"] if q.get("pipeline_id") == pid), None)
                if duplicate:
                    self.send_json({"status": "already_queued", "queued": duplicate}, 409)
                    return

                item = {
                    "kind": "pipeline",
                    "run_id": str(uuid.uuid4())[:8],
                    "pipeline_id": pid,
                    "topic": pipeline.get("topic", ""),
                    "status": "queued",
                    "queued_at": now_iso()
                }
                RUN_STATUS["queued"].append(item)
                RUN_QUEUE.put(item)

            with open(LOG_FILE, "a", buffering=1) as log:
                log.write(f"\n--- Pipeline queued: {pid} ({item['run_id']}) ---\n")

            self.send_json({"status": "queued", "item": item})

        elif self.path == '/api/oneoff/run':
            data = self.safe_read_json_body()
            if data is None:
                return
            topic = (data.get('topic') or '').strip()
            prompt = (data.get('prompt') or '').strip()
            persona = data.get('persona') or 'Masterpiece'
            publish_mode = data.get('publish_mode') or 'live'

            if not prompt:
                self.send_json({"error": "Prompt is required."}, 400)
                return
            auto_title = not topic

            oneoff_id = str(uuid.uuid4())[:8]
            request_path = os.path.join(ONEOFF_REQUEST_DIR, f"{oneoff_id}.json")
            request_data = {
                "id": oneoff_id,
                "topic": topic,
                "prompt": prompt,
                "auto_title": auto_title,
                "persona": persona,
                "publish_mode": publish_mode,
                "created_at": now_iso()
            }
            save_json_file(request_path, request_data)

            history_item = {
                "id": oneoff_id,
                "topic": topic or "제목 자동 생성",
                "persona": persona,
                "publish_mode": publish_mode,
                "status": "queued",
                "created_at": now_iso(),
                "prompt_preview": prompt[:260]
            }
            add_oneoff_history(history_item)

            with QUEUE_LOCK:
                item = {
                    "kind": "oneoff",
                    "run_id": str(uuid.uuid4())[:8],
                    "oneoff_id": oneoff_id,
                    "request_path": request_path,
                    "topic": topic or "제목 자동 생성",
                    "status": "queued",
                    "queued_at": now_iso()
                }
                RUN_STATUS["queued"].append(item)
                RUN_QUEUE.put(item)

            with open(LOG_FILE, "a", buffering=1) as log:
                log.write(f"\n--- One-off queued: {oneoff_id} ({item['run_id']}) topic={topic} ---\n")

            self.send_json({"status": "queued", "item": item})
            
        elif self.path == '/api/pipeline/save':
            data = self.safe_read_json_body()
            if data is None:
                return
            pid = data.get('id')
            
            pipelines = load_json_file(PIPELINES_FILE, [])
                
            if pid:
                # Update
                found = False
                for i, p in enumerate(pipelines):
                    if p.get('id') == pid:
                        pipelines[i] = data
                        found = True
                        break
                if not found:
                    pipelines.append(data)
            else:
                # Add
                data['id'] = str(uuid.uuid4())[:8]
                pipelines.append(data)
                
            save_json_file(PIPELINES_FILE, pipelines)
                
            sync_cron(pipelines)
            self.send_json({"status": "success", "pipeline": data})
            
        elif self.path == '/api/pipeline/delete':
            data = self.safe_read_json_body()
            if data is None:
                return
            pid = data.get('id')
            
            pipelines = load_json_file(PIPELINES_FILE, [])
            pipelines = [p for p in pipelines if p.get('id') != pid]
            save_json_file(PIPELINES_FILE, pipelines)
                
            sync_cron(pipelines)
            self.send_json({"status": "success"})
            
        elif self.path == '/api/logs/clear':
            import datetime
            if os.path.exists(LOG_FILE):
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_name = f"{LOG_FILE}.{timestamp}.bak"
                os.rename(LOG_FILE, backup_name)
            # 빈 파일 생성
            with open(LOG_FILE, 'w') as f:
                f.write("")
            self.send_json({"status": "success"})
        else:
            self.send_json({"error": "Not Found"}, 404)

def main():
    os.chdir(WEB_DIR)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), AutoBloggerHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
