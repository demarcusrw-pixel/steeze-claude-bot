#!/usr/bin/env python3
"""
SteezeClaude Local Bridge - Polling version
Polls Railway for pending commands and executes them locally.
No tunnel needed.
"""
import os
import json
import time
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime

RAILWAY_URL = os.environ.get("RAILWAY_URL", "https://steeze-claude-bot-production.up.railway.app")
BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "steeze2026")
BASE_DIR = os.path.expanduser("~/Documents")
NOTES_DIR = os.path.join(BASE_DIR, "SteezNotes")
IDEAS_FILE = os.path.join(NOTES_DIR, "ideas.md")
TASKS_FILE = os.path.join(NOTES_DIR, "tasks.md")
POLL_INTERVAL = 3  # seconds

os.makedirs(NOTES_DIR, exist_ok=True)

def poll_commands():
    try:
        req = urllib.request.Request(
            f"{RAILWAY_URL}/bridge/poll",
            headers={"X-Bridge-Secret": BRIDGE_SECRET},
            method="GET"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return []

def ack_command(command_id, result):
    try:
        data = json.dumps({"id": command_id, "result": result, "secret": BRIDGE_SECRET}).encode()
        req = urllib.request.Request(
            f"{RAILWAY_URL}/bridge/ack",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Ack error: {e}")

def execute(command, payload):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    if command == "save_idea":
        text = payload.get("text", "")
        category = payload.get("category", "general")
        with open(IDEAS_FILE, "a") as f:
            f.write(f"\n## [{now}] {category}\n{text}\n")
        return f"Saved idea"

    elif command == "save_task":
        text = payload.get("text", "")
        with open(TASKS_FILE, "a") as f:
            f.write(f"- [ ] [{now}] {text}\n")
        return f"Saved task"

    elif command == "open_ableton":
        project = payload.get("project", "")
        if project:
            subprocess.Popen(["open", project])
        else:
            subprocess.Popen(["open", "-a", "Ableton Live 12 Suite"])
        return "Opened Ableton"

    elif command == "open_app":
        app = payload.get("app", "")
        subprocess.Popen(["open", "-a", app])
        return f"Opened {app}"

    elif command == "write_file":
        path = os.path.join(BASE_DIR, payload.get("path", "steeze_note.md"))
        content = payload.get("content", "")
        with open(path, "w") as f:
            f.write(content)
        return f"Wrote {path}"

    elif command == "append_file":
        path = os.path.join(BASE_DIR, payload.get("path", "steeze_note.md"))
        content = payload.get("content", "")
        with open(path, "a") as f:
            f.write(f"\n[{now}] {content}\n")
        return f"Appended to {path}"

    elif command == "run_script":
        script = payload.get("script", "")
        result = subprocess.run(script, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout or result.stderr or "Done"

    elif command == "ping":
        return "pong"

    return f"Unknown command: {command}"

if __name__ == "__main__":
    print(f"SteezeClaude bridge polling {RAILWAY_URL} every {POLL_INTERVAL}s")
    print(f"Notes dir: {NOTES_DIR}")

    while True:
        try:
            commands = poll_commands()
            for cmd in commands:
                cid = cmd.get("id")
                command = cmd.get("command")
                payload = cmd.get("payload", {})
                print(f"Executing: {command} {payload}")
                result = execute(command, payload)
                print(f"Result: {result}")
                ack_command(cid, result)
        except Exception as e:
            print(f"Poll error: {e}")

        time.sleep(POLL_INTERVAL)
