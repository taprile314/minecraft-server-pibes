"""Updates the server MOTD with the current public IP + port.

This way players see the IP to connect directly in the Minecraft server list,
without needing to be told by hand every time it changes (dynamic IP).

Runs BEFORE the container starts: server.properties is only read at boot,
so a hot change won't take effect until the next restart.

Usage: python scripts/update_motd.py [port]
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
    # fallback if the router doesn't respond over UPnP
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
        print(f"[motd] WARNING: failed to update the MOTD: {exc}")
