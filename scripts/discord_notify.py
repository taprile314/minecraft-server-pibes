"""Tails data/logs/latest.log and notifies joins/leaves to a Discord webhook.

Runs as a long-lived process inside the `discord-notifier` service in
docker-compose.yml (not part of the start.ps1 startup sequence).

Config via environment variables (see .env / .env.example):
    DISCORD_WEBHOOK_URL   Discord webhook URL (required)
    MC_LOG_PATH           path to the server log (default /data/logs/latest.log)
"""

import os
import re
import time
from pathlib import Path

import requests

LOG_PATH = Path(os.environ.get("MC_LOG_PATH", "/data/logs/latest.log"))
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

JOIN_RE = re.compile(r"\]: (\w+) joined the game")
LEAVE_RE = re.compile(r"\]: (\w+) left the game")


def notify(message):
    try:
        response = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        print(f"[discord-notify] WARNING: failed to send to Discord: {exc}")


def follow(path):
    while not path.exists():
        print(f"[discord-notify] waiting for {path} to exist...")
        time.sleep(5)

    file = path.open("r", encoding="utf-8", errors="replace")
    file.seek(0, os.SEEK_END)
    size = path.stat().st_size

    while True:
        line = file.readline()
        if line:
            yield line
            continue

        time.sleep(1)
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            continue
        # log was rotated/truncated (server restart): reopen from the start
        if current_size < size:
            print("[discord-notify] log rotation detected, reopening")
            file.close()
            file = path.open("r", encoding="utf-8", errors="replace")
        size = current_size


def main():
    if not WEBHOOK_URL:
        raise RuntimeError("DISCORD_WEBHOOK_URL is missing from the environment")

    print(f"[discord-notify] watching {LOG_PATH}")
    for line in follow(LOG_PATH):
        join = JOIN_RE.search(line)
        if join:
            notify(f"**{join.group(1)}** joined the server")
            continue
        leave = LEAVE_RE.search(line)
        if leave:
            notify(f"**{leave.group(1)}** left the server")


if __name__ == "__main__":
    main()
