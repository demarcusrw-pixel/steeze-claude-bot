#!/usr/bin/env python3
"""
SteezeClaude_Bot - Daily notification script for Demarcus
"""
import sys
import os
import urllib.request
import urllib.parse
import json

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

def send_message(text):
    payload = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }).encode()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    req = urllib.request.Request(url, data=payload, method="POST")

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())

    if data["ok"]:
        print(f"✅ Sent: {text[:50]}...")
    else:
        print(f"❌ Failed: {data}")
        sys.exit(1)

MESSAGES = {
    "morning": """🌅 <b>Good morning Demarcus!</b>

Today's focus:
🎵 Make or work on a beat
📱 Post one piece of content
💪 Do something for your body

What's the #1 thing you're getting done today?""",

    "post_check": """📱 <b>6pm check-in</b>

Have you posted today?
If not — even a 15-second clip counts.
Consistency > perfection. Get it up.""",

    "beat_session": """🎹 <b>It's beat o'clock.</b>

Close everything else.
Open Ableton.
Make something."""
}

if __name__ == "__main__":
    msg_type = sys.argv[1] if len(sys.argv) > 1 else "morning"
    message = MESSAGES.get(msg_type, sys.argv[1] if len(sys.argv) > 1 else "Hey Demarcus!")
    send_message(message)
