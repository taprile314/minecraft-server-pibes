"""Abre (o renueva) un port forward via UPnP en el router para el server de Minecraft.

Uso: python scripts/upnp_forward.py [puerto] [protocolo]
Default: puerto 25569, protocolo TCP (matchea SERVER_PORT en docker-compose.yml).
"""

import socket
import sys

import upnpclient

DEFAULT_PORT = 25569
DEFAULT_PROTOCOL = "TCP"
DESCRIPTION = "minecraft-pibes"


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


def get_igd_service():
    devices = upnpclient.discover()
    for device in devices:
        for service in device.services:
            if "WANIPConn" in service.service_type or "WANPPPConn" in service.service_type:
                return service
    raise RuntimeError("No se encontró un router con soporte UPnP IGD en la red")


def forward_port(port, protocol=DEFAULT_PROTOCOL):
    local_ip = get_local_ip()
    igd = get_igd_service()

    try:
        igd.DeletePortMapping(NewRemoteHost="", NewExternalPort=port, NewProtocol=protocol)
    except Exception:
        pass  # no había mapping previo, no pasa nada

    igd.AddPortMapping(
        NewRemoteHost="",
        NewExternalPort=port,
        NewProtocol=protocol,
        NewInternalPort=port,
        NewInternalClient=local_ip,
        NewEnabled="1",
        NewPortMappingDescription=DESCRIPTION,
        NewLeaseDuration=0,
    )
    print(f"[upnp] {protocol} {port} -> {local_ip}:{port} ({DESCRIPTION})")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    protocol = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PROTOCOL
    try:
        forward_port(port, protocol)
    except Exception as exc:
        print(f"[upnp] WARNING: no se pudo abrir el puerto automáticamente: {exc}")
        # no cortamos el arranque del server por esto
