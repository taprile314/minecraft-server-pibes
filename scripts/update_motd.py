"""Actualiza el MOTD del server con la IP publica + puerto actuales.

Asi los chicos ven la IP para conectarse directo en la lista de servers de Minecraft,
sin que haya que avisarles a mano cada vez que cambia (IP dinamica).

Corre ANTES de levantar el container: server.properties solo se lee al arrancar,
asi que un cambio en caliente no se refleja hasta el proximo restart.

Uso: python scripts/update_motd.py [puerto]
"""

import re
import sys
from pathlib import Path

import requests
import upnpclient

DEFAULT_PORT = 25569
PROPERTIES_PATH = Path(__file__).resolve().parent.parent / "data" / "server.properties"


def get_public_ip():
    try:
        devices = upnpclient.discover()
        for device in devices:
            for service in device.services:
                if "WANIPConn" in service.service_type or "WANPPPConn" in service.service_type:
                    return service.GetExternalIPAddress()["NewExternalIPAddress"]
    except Exception:
        pass
    # fallback si el router no responde por UPnP
    return requests.get("https://api.ipify.org", timeout=5).text.strip()


def update_motd(ip, port):
    text = PROPERTIES_PATH.read_text(encoding="latin-1")
    new_line = f"motd=IP: {ip}:{port}"
    if re.search(r"(?m)^motd=", text):
        text = re.sub(r"(?m)^motd=.*$", new_line, text)
    else:
        text += f"\n{new_line}\n"
    PROPERTIES_PATH.write_text(text, encoding="latin-1")
    print(f"[motd] {new_line}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    try:
        ip = get_public_ip()
        update_motd(ip, port)
    except Exception as exc:
        print(f"[motd] WARNING: no se pudo actualizar el MOTD: {exc}")
