"""Actualiza el registro DuckDNS con la IP publica actual.

Lee dominio y token desde .duckdns.env en la raiz del proyecto:

    DOMAIN=mi-server
    TOKEN=00000000-0000-0000-0000-000000000000

Uso: python scripts/update_duckdns.py
"""

import sys
from pathlib import Path

import requests

ENV_PATH = Path(__file__).resolve().parent.parent / ".duckdns.env"


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
        raise RuntimeError(f"DuckDNS respondio '{response.text.strip()}'")
    print(f"[duckdns] {domain}.duckdns.org actualizado")


if __name__ == "__main__":
    try:
        if not ENV_PATH.exists():
            raise RuntimeError(f"no existe {ENV_PATH}, copia .duckdns.env.example y completalo")
        env = load_env(ENV_PATH)
        domain = env.get("DOMAIN")
        token = env.get("TOKEN")
        if not domain or not token:
            raise RuntimeError(f"faltan DOMAIN/TOKEN en {ENV_PATH}")
        update_duckdns(domain, token)
    except Exception as exc:
        print(f"[duckdns] WARNING: no se pudo actualizar DuckDNS: {exc}")
        # no cortamos el arranque del server por esto
