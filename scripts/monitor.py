#!/usr/bin/env python3
"""
lightweight uptime monitor. polls /health every 60s.
posts to discord webhook on state change.
start with: nohup python3 scripts/monitor.py &
"""
import datetime
import json
import os
import time
import urllib.error
import urllib.request

HEALTH_URL = os.environ["MONITOR_HEALTH_URL"]
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
POLL_INTERVAL = int(os.environ.get("MONITOR_INTERVAL", "60"))


def post_discord(message):
    if not WEBHOOK_URL:
        return
    data = json.dumps({"content": message}).encode()
    req = urllib.request.Request(
        WEBHOOK_URL, data=data,
        headers={"Content-Type": "application/json", "User-Agent": "HealthMonitor/1.0"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[monitor] discord post failed: {e}")


def check_health():
    try:
        resp = urllib.request.urlopen(HEALTH_URL, timeout=5)
        return resp.status == 200
    except Exception:
        return False


def main():
    was_up = True
    print(f"[monitor] starting. polling {HEALTH_URL} every {POLL_INTERVAL}s")
    while True:
        is_up = check_health()
        now = datetime.datetime.utcnow().isoformat()
        if is_up and not was_up:
            msg = f"✅ [{now}] Service RECOVERED — {HEALTH_URL} is back up"
            print(msg)
            post_discord(msg)
        elif not is_up and was_up:
            msg = f"🚨 [{now}] Service DOWN — {HEALTH_URL} is not responding"
            print(msg)
            post_discord(msg)
        was_up = is_up
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
