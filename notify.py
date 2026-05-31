#!/usr/bin/env python3
"""
SteezeClaude_Bot - AI-powered daily notifications for Demarcus
Runs every hour via Railway cron, sends personalized message at the right times.
"""
import os
import urllib.request
import urllib.parse
import json
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TZ = pytz.timezone("America/New_York")

CONTEXT = """
You are Claude, Demarcus Walker's personal AI assistant. You know the following about him:
- He's a music producer who works in Ableton Live
- His producer name/brand is SOLO$TEEZE
- He's building toward making music his full-time career
- He produces trap beats, currently working on Future-inspired beats (dark, melodic, minor key, heavy 808s)
- His three main goals: 1) produce & send beats consistently, 2) post content on social media daily, 3) take care of his body
- He has ADHD — executive function is his biggest challenge
- He's a night owl, wakes up around 9am
- He's also a developer (SwapRebel is his app)
- Keep messages short, direct, energetic. No fluff. Talk to him like a real one.
"""

PROMPTS = {
    9: """Write a short morning briefing for Demarcus.
It's 9am, he just woke up. Give him:
1. One hype sentence to start the day
2. His 3 priorities for today (beat work, posting, body)
3. One quick motivational line to close
Keep it under 150 words. Use some emojis. Format it nicely for Telegram.""",

    18: """Write a quick 6pm check-in message for Demarcus.
Ask if he's posted content today. If not, push him to do it — something short, even 15 seconds.
Be direct and real, not corporate. Under 80 words.""",

    22: """Write a 10pm beat session kickoff message for Demarcus.
It's his creative prime time. Get him off his phone and into Ableton.
Be hype, short, direct. Under 60 words.""",
}

def call_claude(prompt):
    payload = json.dumps({
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 300,
        "system": CONTEXT,
        "messages": [{"role": "user", "content": prompt}]
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

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())

    if data["ok"]:
        print(f"✅ Message sent")
    else:
        print(f"❌ Failed: {data}")

if __name__ == "__main__":
    now = datetime.now(TZ)
    hour = now.hour
    print(f"Running at {now.strftime('%Y-%m-%d %H:%M')} ET (hour={hour})")

    if hour in PROMPTS:
        print(f"Generating message for hour {hour}...")
        message = call_claude(PROMPTS[hour])
        print(f"Message: {message[:100]}...")
        send_telegram(message)
    else:
        print(f"No message scheduled for hour {hour}, skipping.")
