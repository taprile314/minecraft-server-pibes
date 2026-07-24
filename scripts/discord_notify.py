"""Sigue data/logs/latest.log y notifica joins/leaves a un webhook de Discord.

Corre como proceso de larga duracion dentro del servicio `discord-notifier`
de docker-compose.yml (no es parte de la secuencia de arranque en start.ps1).

Config via variables de entorno (ver .discord.env / .discord.env.example):
    DISCORD_WEBHOOK_URL   URL del webhook de Discord (obligatoria)
    MC_LOG_PATH           ruta al log del server (default /data/logs/latest.log)
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
        print(f"[discord-notify] WARNING: no se pudo enviar a Discord: {exc}")


def follow(path):
    while not path.exists():
        print(f"[discord-notify] esperando a que exista {path}...")
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
        # el log se roto/trunco (restart del server): reabrir desde el principio
        if current_size < size:
            print("[discord-notify] rotacion de log detectada, reabriendo")
            file.close()
            file = path.open("r", encoding="utf-8", errors="replace")
        size = current_size


def main():
    if not WEBHOOK_URL:
        raise RuntimeError("falta DISCORD_WEBHOOK_URL en el entorno")

    print(f"[discord-notify] escuchando {LOG_PATH}")
    for line in follow(LOG_PATH):
        join = JOIN_RE.search(line)
        if join:
            notify(f"**{join.group(1)}** se conecto al servidor")
            continue
        leave = LEAVE_RE.search(line)
        if leave:
            notify(f"**{leave.group(1)}** se desconecto del servidor")


if __name__ == "__main__":
    main()
