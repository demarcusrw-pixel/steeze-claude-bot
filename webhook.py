#!/usr/bin/env python3
"""
SteezeClaude_Bot - Full agent with task management
"""
import os
import json
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "steeze2026")
TZ = pytz.timezone("America/New_York")
DATA_FILE = "agent_data.json"
COMMAND_QUEUE_FILE = "command_queue.json"
import uuid

def queue_command(command, payload={}):
    """Store command in queue for Mac bridge to pick up via polling."""
    try:
        if os.path.exists(COMMAND_QUEUE_FILE):
            with open(COMMAND_QUEUE_FILE, "r") as f:
                queue = json.load(f)
        else:
            queue = []

        cmd = {
            "id": str(uuid.uuid4()),
            "command": command,
            "payload": payload,
            "status": "pending",
            "created": datetime.now(TZ).isoformat()
        }
        queue.append(cmd)

        with open(COMMAND_QUEUE_FILE, "w") as f:
            json.dump(queue, f)

        print(f"Queued command: {command}")
        return {"ok": True, "id": cmd["id"]}
    except Exception as e:
        print(f"Queue error: {e}")
        return {"ok": False, "error": str(e)}
        return {"ok": False, "error": str(e)}

SYSTEM_PROMPT = """You are SteezeClaude — Demarcus Walker's personal AI agent. You run via Telegram.

Who he is:
- Producer (SOLO$TEEZE), makes Future-inspired trap in Ableton Live
- Has ADHD — executive function is his main challenge
- Goals: music full time, post daily on socials, stay healthy, build SwapRebel (his app)
- Night owl, wakes ~9am

You have tools. Based on his message, decide which tool to use and respond with JSON like:
{
  "tool": "tool_name",
  "data": { ... },
  "reply": "your message to him"
}

Available tools:
- "chat" — just respond, no data needed
- "add_task" — add a task. data: {"task": "task text", "category": "music|content|body|app|other", "priority": "high|medium|low"}
- "list_tasks" — show his tasks. data: {}
- "complete_task" — mark task done. data: {"task_id": "id"}
- "log_activity" — log something he did. data: {"activity": "text", "category": "music|content|body|app|other"}
- "show_summary" — show today's summary of tasks + activity. data: {}
- "clear_tasks" — clear completed tasks. data: {}
- "mac_save_idea" — save an idea/note to his Mac filesystem. data: {"text": "idea text", "category": "beat|lyric|content|app|general"}
- "mac_save_task" — save a task to his Mac filesystem. data: {"text": "task text"}
- "mac_open_ableton" — open Ableton on his Mac. data: {}
- "mac_open_app" — open any app on his Mac. data: {"app": "app name"}
- "mac_run" — run a terminal command on his Mac. data: {"script": "command"}

Use mac_ tools when he wants something saved to his computer or wants to open/control apps.

How to talk:
- SHORT and real. Like a smart friend, not a life coach.
- Never mention streaks. Never say "Great job!" or generic hype.
- React to what he actually said.
- Match his energy.
- Under 60 words in reply always.

Current data will be provided with each message."""

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"tasks": [], "activity": [], "next_task_id": 1}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def call_claude(user_message, data):
    now = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    open_tasks = [t for t in data["tasks"] if not t.get("done")]
    recent_activity = data["activity"][-5:]

    context = f"""Current time: {now} ET

Open tasks ({len(open_tasks)}):
{json.dumps(open_tasks, indent=2) if open_tasks else "none"}

Recent activity:
{json.dumps([a.get('activity') for a in recent_activity], indent=2) if recent_activity else "none"}

Demarcus says: {user_message}"""

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": context}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())

    text = result["content"][0]["text"].strip()

    # extract JSON from response
    try:
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except:
        return {"tool": "chat", "data": {}, "reply": text}

def handle_tool(tool, tool_data, data):
    now = datetime.now(TZ)

    if tool == "add_task":
        task = {
            "id": str(data["next_task_id"]),
            "task": tool_data.get("task", ""),
            "category": tool_data.get("category", "other"),
            "priority": tool_data.get("priority", "medium"),
            "done": False,
            "created": now.strftime("%Y-%m-%d %H:%M")
        }
        data["tasks"].append(task)
        data["next_task_id"] += 1

    elif tool == "complete_task":
        task_id = str(tool_data.get("task_id", ""))
        for t in data["tasks"]:
            if t["id"] == task_id:
                t["done"] = True
                t["completed"] = now.strftime("%Y-%m-%d %H:%M")
                break

    elif tool == "log_activity":
        data["activity"].append({
            "activity": tool_data.get("activity", ""),
            "category": tool_data.get("category", "other"),
            "timestamp": now.strftime("%Y-%m-%d %H:%M")
        })

    elif tool == "clear_tasks":
        data["tasks"] = [t for t in data["tasks"] if not t.get("done")]

    elif tool == "mac_save_idea":
        queue_command("save_idea", tool_data)
    elif tool == "mac_save_task":
        queue_command("save_task", tool_data)
    elif tool == "mac_open_ableton":
        queue_command("open_ableton", tool_data)
    elif tool == "mac_open_app":
        queue_command("open_app", tool_data)
    elif tool == "mac_run":
        queue_command("run_script", tool_data)

    save_data(data)
    return data

def format_tasks_reply(data):
    open_tasks = [t for t in data["tasks"] if not t.get("done")]
    if not open_tasks:
        return "No open tasks. You're clear."

    cats = {"music": "🎵", "content": "📱", "body": "💪", "app": "💻", "other": "•"}
    lines = []
    for t in open_tasks:
        emoji = cats.get(t.get("category", "other"), "•")
        priority = " ‼️" if t.get("priority") == "high" else ""
        lines.append(f"{emoji} [{t['id']}] {t['task']}{priority}")

    return "\n".join(lines)

def send_telegram(text):
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data=payload,
        method="POST"
    )
    urllib.request.urlopen(req)

class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Bridge polls this endpoint for pending commands
        if self.path == "/bridge/poll":
            secret = self.headers.get("X-Bridge-Secret", "")
            if secret != BRIDGE_SECRET:
                self.send_response(403)
                self.end_headers()
                return

            try:
                if os.path.exists(COMMAND_QUEUE_FILE):
                    with open(COMMAND_QUEUE_FILE, "r") as f:
                        queue = json.load(f)
                else:
                    queue = []

                pending = [c for c in queue if c.get("status") == "pending"]
                # mark as dispatched
                for c in pending:
                    c["status"] = "dispatched"
                with open(COMMAND_QUEUE_FILE, "w") as f:
                    json.dump(queue, f)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(pending).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # Bridge acks completed commands
        if self.path == "/bridge/ack":
            try:
                data = json.loads(body)
                if data.get("secret") != BRIDGE_SECRET:
                    self.send_response(403)
                    self.end_headers()
                    return

                cmd_id = data.get("id")
                result = data.get("result", "")

                if os.path.exists(COMMAND_QUEUE_FILE):
                    with open(COMMAND_QUEUE_FILE, "r") as f:
                        queue = json.load(f)
                    for c in queue:
                        if c["id"] == cmd_id:
                            c["status"] = "done"
                            c["result"] = result
                    with open(COMMAND_QUEUE_FILE, "w") as f:
                        json.dump(queue, f)

                self.send_response(200)
                self.end_headers()
                print(f"Ack: {cmd_id} -> {result}")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
            return

        # Telegram webhook
        self.send_response(200)
        self.end_headers()
        update = json.loads(body)

        try:
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            if not text or chat_id != CHAT_ID:
                return

            print(f"Received: {text}")
            data = load_data()
            result = call_claude(text, data)

            tool = result.get("tool", "chat")
            tool_data = result.get("data", {})
            reply = result.get("reply", "")

            if tool != "chat":
                data = handle_tool(tool, tool_data, data)

            # for list_tasks and show_summary, append formatted task list
            if tool == "list_tasks":
                reply = format_tasks_reply(data)
            elif tool == "show_summary":
                task_list = format_tasks_reply(data)
                reply = f"{reply}\n\n{task_list}" if reply else task_list

            send_telegram(reply)
            print(f"Tool: {tool} | Reply: {reply[:80]}")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting webhook server on port {port}...")
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    server.serve_forever()
