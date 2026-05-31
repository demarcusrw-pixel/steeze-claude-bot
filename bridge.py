#!/usr/bin/env python3
"""
SteezeClaude Local Bridge
Runs on Demarcus's Mac, receives commands from Railway and executes them locally.
"""
import os
import json
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "steeze2026")
BASE_DIR = os.path.expanduser("~/Documents")
NOTES_DIR = os.path.join(BASE_DIR, "SteezNotes")
IDEAS_FILE = os.path.join(NOTES_DIR, "ideas.md")
TASKS_FILE = os.path.join(NOTES_DIR, "tasks.md")

os.makedirs(NOTES_DIR, exist_ok=True)

def handle_command(command, payload):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if command == "save_idea":
        text = payload.get("text", "")
        category = payload.get("category", "general")
        with open(IDEAS_FILE, "a") as f:
            f.write(f"\n## [{now}] {category}\n{text}\n")
        return f"Saved idea to {IDEAS_FILE}"

    elif command == "save_task":
        text = payload.get("text", "")
        with open(TASKS_FILE, "a") as f:
            f.write(f"- [ ] [{now}] {text}\n")
        return f"Saved task to {TASKS_FILE}"

    elif command == "open_ableton":
        project = payload.get("project", "")
        if project:
            subprocess.Popen(["open", project])
            return f"Opening {project}"
        else:
            subprocess.Popen(["open", "-a", "Ableton Live 12 Suite"])
            return "Opening Ableton"

    elif command == "open_app":
        app = payload.get("app", "")
        subprocess.Popen(["open", "-a", app])
        return f"Opening {app}"

    elif command == "write_file":
        path = os.path.join(BASE_DIR, payload.get("path", "steeze_note.md"))
        content = payload.get("content", "")
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote file: {path}"

    elif command == "append_file":
        path = os.path.join(BASE_DIR, payload.get("path", "steeze_note.md"))
        content = payload.get("content", "")
        with open(path, "a") as f:
            f.write(f"\n[{now}] {content}\n")
        return f"Appended to: {path}"

    elif command == "list_files":
        path = os.path.join(BASE_DIR, payload.get("path", ""))
        files = os.listdir(path)
        return json.dumps(files)

    elif command == "run_script":
        script = payload.get("script", "")
        result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr

    elif command == "ping":
        return "pong — bridge is alive"

    else:
        return f"Unknown command: {command}"

class BridgeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except:
            self.send_response(400)
            self.end_headers()
            return

        # verify secret
        if data.get("secret") != BRIDGE_SECRET:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"Unauthorized")
            return

        command = data.get("command", "")
        payload = data.get("payload", {})

        print(f"Command: {command} | Payload: {payload}")

        try:
            result = handle_command(command, payload)
            response = json.dumps({"ok": True, "result": result}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response)
            print(f"Result: {result}")
        except Exception as e:
            error = json.dumps({"ok": False, "error": str(e)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(error)
            print(f"Error: {e}")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"SteezeClaude bridge is running")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = 7777
    print(f"SteezeClaude bridge running on port {port}")
    print(f"Notes dir: {NOTES_DIR}")
    server = HTTPServer(("0.0.0.0", port), BridgeHandler)
    server.serve_forever()
