# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-hosted Minecraft (Fabric, MC 26.2) server for a private group of friends, run via Docker on a home machine behind a residential router. This is infrastructure/ops, not an application codebase — the "code" is a docker-compose file plus a few small Python helper scripts that make the server reachable from outside the LAN despite a dynamic public IP and NAT.

## Running the server

```
.\start.ps1
```

This runs, in order:
1. Firewall check (inline PowerShell) — makes sure the `Minecraft Voicechat (pibes) 24454 UDP` inbound rule exists in Windows Firewall (all profiles); if missing, triggers a UAC prompt to create it. Needed because Simple Voice Chat's UDP traffic is otherwise dropped on the Private network profile even though the game's TCP port has its own long-standing firewall rule.
2. `scripts/upnp_forward.py 25569 TCP` — opens a UPnP port forward on the router for the Minecraft port.
3. `scripts/upnp_forward.py 24454 UDP` — opens a UPnP port forward on the router for the Simple Voice Chat port.
4. `scripts/update_duckdns.py` — pushes the current public IP to DuckDNS so the domain stays resolvable.
5. `scripts/update_motd.py 25569` — writes the current public IP:port into `data/server.properties`' `motd`, so players see the connection address directly in their in-game server list instead of being told out of band. Must run before the container starts — `server.properties` is only read at container boot, so a change made while the server is running won't take effect until the next restart.
6. `docker compose up -d` — starts the server container (`itzg/minecraft-server` image).

Each helper script fails soft: if UPnP discovery, DuckDNS, the IP lookup, or the firewall rule creation fails, it prints a `WARNING` and lets the startup sequence continue rather than aborting — a broken network helper shouldn't block getting the server up.

## Configuration

- `docker-compose.yml` is the source of truth for server settings: MC version, memory, difficulty, ops, and the mod list (`MODRINTH_PROJECTS`, installed automatically by the `itzg/minecraft-server` image from Modrinth slugs at container start).
- `.duckdns.env` (gitignored/local, not committed) holds `DOMAIN` and `TOKEN` for DuckDNS; `.duckdns.env.example` shows the expected shape. `update_duckdns.py` reads this file directly — there's no other config layer for it.
- `.discord.env` (gitignored/local, not committed) holds `DISCORD_WEBHOOK_URL` for the `discord-notifier` service; `.discord.env.example` shows the expected shape.
- `data/` is the volume mounted into the container (`./data:/data`) — it's the live server's working directory: world save, `server.properties`, `whitelist.json`, mods, logs, and the full Fabric/Minecraft library jars the server downloaded on first boot. Treat it as runtime state, not source — don't hand-edit files under `data/` except via the scripts above or well-understood Minecraft config files (`server.properties`, `whitelist.json`, `ops.json`).

## Networking model

Port 25569 (TCP) is what's exposed end-to-end: container → host (`docker-compose.yml` ports mapping) → router (UPnP forward) → DuckDNS domain. If connectivity breaks, check in that order: is the container up, is the host port bound, is the UPnP mapping still present on the router (routers can drop these on reboot), does the DuckDNS record match the current public IP.

Port 24454 (UDP) follows the same path for the Simple Voice Chat mod, plus one extra hop: Windows Firewall on the host, which blocks unsolicited inbound UDP by default per network profile. Unlike the game's TCP port (covered by a standing all-profiles firewall rule), the voice chat UDP port needed its own explicit rule — see `start.ps1`'s firewall check step.

## Discord join/leave notifications

The `discord-notifier` service in `docker-compose.yml` is a sidecar container (`python:3.12-alpine`) running `scripts/discord_notify.py`. It tails `data/logs/latest.log` (mounted read-only) for "joined the game" / "left the game" lines and posts a message to a Discord webhook for each. It's a separate long-running container, not part of the `start.ps1` one-shot helper sequence — it starts and restarts independently via `docker compose up -d` / `restart: unless-stopped`, and only depends on the `mc` service existing (not on the log file being present yet — it polls for that).

To enable it: copy `.discord.env.example` to `.discord.env` and set `DISCORD_WEBHOOK_URL` to a webhook URL from the target Discord channel (channel settings → Integrations → Webhooks). No firewall/UPnP/DuckDNS changes are needed since this only makes outbound HTTPS calls to Discord.

## Dependencies

The Python scripts need `upnpclient` and `requests` (no requirements.txt/lockfile currently checked in — install ad hoc if running them standalone). Docker and Docker Compose are required to run the server itself.
