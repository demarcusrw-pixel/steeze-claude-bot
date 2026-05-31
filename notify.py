#!/usr/bin/env python3
"""
SteezeClaude_Bot - Daily notifications for Demarcus
Runs every hour via Railway cron, sends message at the right times.
"""
import os
import urllib.request
import urllib.parse
import json
from datetime import datetime
import pytz

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])
TZ = pytz.timezone("America/New_York")

SCHEDULE = {
    9: ("morning", """🌅 <b>Good morning Demarcus!</b>

Today's focus:
🎵 Make or work on a beat
📱 Post one piece of content
💪 Do something for your body

Let's get it."""),

    18: ("post_check", """📱 <b>6pm check-in</b>

Have you posted today?
Even a 15-second clip counts.
Consistency > perfection. Get it up."""),

    22: ("beat_session", """🎹 <b>Beat o'clock.</b>

Close everything else.
Open Ableton.
Make something."""),
}

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
        print(f"✅ Message sent at hour {hour}")
    else:
        print(f"❌ Failed: {data}")

if __name__ == "__main__":
    now = datetime.now(TZ)
    hour = now.hour
    print(f"Running at {now.strftime('%Y-%m-%d %H:%M')} ET (hour={hour})")

    if hour in SCHEDULE:
        name, message = SCHEDULE[hour]
        send_message(message)
    else:
        print(f"No message scheduled for hour {hour}, skipping.")
