"""Updates the DuckDNS record with the current public IP.

Reads domain and token from .env at the project root:

    DOMAIN=my-server
    TOKEN=00000000-0000-0000-0000-000000000000

Usage: python scripts/update_duckdns.py
"""

import sys
from pathlib import Path

import requests

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().upper()] = value.strip()
    return values


def update_duckdns(domain, token):
    url = "https://www.duckdns.org/update"
    params = {"domains": domain, "token": token, "ip": ""}
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    if response.text.strip() != "OK":
        raise RuntimeError(f"DuckDNS responded '{response.text.strip()}'")
    print(f"[duckdns] {domain}.duckdns.org updated")


if __name__ == "__main__":
    try:
        if not ENV_PATH.exists():
            raise RuntimeError(f"{ENV_PATH} does not exist, copy .env.example and fill it in")
        env = load_env(ENV_PATH)
        domain = env.get("DOMAIN")
        token = env.get("TOKEN")
        if not domain or not token:
            raise RuntimeError(f"DOMAIN/TOKEN missing from {ENV_PATH}")
        update_duckdns(domain, token)
    except Exception as exc:
        print(f"[duckdns] WARNING: failed to update DuckDNS: {exc}")
        # don't block server startup over this
