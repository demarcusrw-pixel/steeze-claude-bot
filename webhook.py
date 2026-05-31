#!/usr/bin/env python3
"""
SteezeClaude_Bot - Webhook server
Receives Telegram messages, calls Claude, responds and logs activity.
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
TZ = pytz.timezone("America/New_York")
LOG_FILE = "activity_log.json"

SYSTEM_PROMPT = """You are SteezeClaude, Demarcus Walker's personal AI agent.

About Demarcus:
- Music producer, brand name SOLO$TEEZE
- Makes trap beats in Ableton Live (Future-inspired, dark, minor key, heavy 808s)
- Goals: produce consistently, post daily on socials, take care of his body
- Has ADHD — executive function is his main challenge
- Night owl, wakes ~9am
- Also a developer (SwapRebel app)

Your job:
- Track what he tells you he did (beat work, posting, gym, etc.)
- Be his accountability partner
- Keep responses SHORT and real — no corporate fluff
- When he logs something, acknowledge it and update his streak
- When he's slipping, call it out directly but supportively
- You have access to his activity log

Activity log context will be provided with each message.
"""

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    return {"entries": [], "streaks": {"beats": 0, "posts": 0, "body": 0}}

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def call_claude(user_message, log):
    recent = log["entries"][-10:] if log["entries"] else []
    streaks = log["streaks"]

    context = f"""Recent activity log (last 10 entries):
{json.dumps(recent, indent=2)}

Current streaks:
- Beats: {streaks['beats']} days
- Posts: {streaks['posts']} days
- Body: {streaks['body']} days

User message: {user_message}

Respond naturally. If they logged an activity, acknowledge it, update relevant streaks in your response, and end with a short motivational line. Keep it under 100 words."""

    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 200,
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
        data = json.loads(response.read())

    return data["content"][0]["text"]

def log_activity(message, log):
    now = datetime.now(TZ)
    entry = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "message": message
    }
    log["entries"].append(entry)

    msg_lower = message.lower()
    if any(w in msg_lower for w in ["beat", "ableton", "produced", "made a beat", "worked on music"]):
        log["streaks"]["beats"] += 1
    if any(w in msg_lower for w in ["posted", "post", "uploaded", "went live"]):
        log["streaks"]["posts"] += 1
    if any(w in msg_lower for w in ["gym", "worked out", "ran", "exercised", "body", "fitness"]):
        log["streaks"]["body"] += 1

    return log

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
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)
        update = json.loads(body)

        self.send_response(200)
        self.end_headers()

        try:
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")

            if not text or chat_id != CHAT_ID:
                return

            print(f"Received: {text}")

            log = load_log()
            log = log_activity(text, log)
            save_log(log)

            response = call_claude(text, log)
            send_telegram(response)
            print(f"Replied: {response[:80]}...")

        except Exception as e:
            print(f"Error: {e}")

    def log_message(self, format, *args):
        pass  # suppress default logging

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting webhook server on port {port}...")
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    server.serve_forever()
