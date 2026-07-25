# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A self-hosted Minecraft (Fabric, MC 26.2) server for a private group of friends, run via Docker on a home machine behind a residential router. This is infrastructure/ops, not an application codebase — the "code" is a docker-compose file plus a few small Python helper scripts that make the server reachable from outside the LAN despite a dynamic public IP and NAT, plus a packwiz pack (see below) for distributing the client-side modlist to players.

The repo is published publicly at `https://github.com/taprile314/minecraft-server-pibes` — public specifically so the packwiz pack can be fetched by players' launchers without authentication. `data/` (world save, server config/logs) and the real `.env` files are gitignored and never pushed; see `.gitignore`.

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
- `.env` (gitignored/local, not committed) holds `DOMAIN` and `TOKEN` for DuckDNS, `DISCORD_WEBHOOK_URL` for the `discord-notifier` service, and `RCON_PASSWORD` shared between the `mc` and `backup` services, all in one file; `.env.example` shows the expected shape. `update_duckdns.py` reads it directly via its own parser (it runs on the host, not in a container); `discord-notifier` and `backup` get it via `docker-compose.yml`'s `environment:`/`env_file:`. One file, several consumers — that's fine, each just ignores the keys it doesn't need.
- `data/` is the volume mounted into the container (`./data:/data`) — it's the live server's working directory: world save, `server.properties`, `whitelist.json`, mods, logs, and the full Fabric/Minecraft library jars the server downloaded on first boot. Treat it as runtime state, not source — don't hand-edit files under `data/` except via the scripts above or well-understood Minecraft config files (`server.properties`, `whitelist.json`, `ops.json`). It's also gitignored: the repo is public, and `data/` is where the world save, ban/whitelist lists, and the live public IP (in `server.properties`' motd) actually live.

## Networking model

Port 25569 (TCP) is what's exposed end-to-end: container → host (`docker-compose.yml` ports mapping) → router (UPnP forward) → DuckDNS domain. If connectivity breaks, check in that order: is the container up, is the host port bound, is the UPnP mapping still present on the router (routers can drop these on reboot), does the DuckDNS record match the current public IP.

Port 24454 (UDP) follows the same path for the Simple Voice Chat mod, plus one extra hop: Windows Firewall on the host, which blocks unsolicited inbound UDP by default per network profile. Unlike the game's TCP port (covered by a standing all-profiles firewall rule), the voice chat UDP port needed its own explicit rule — see `start.ps1`'s firewall check step.

## Discord join/leave notifications

The `discord-notifier` service in `docker-compose.yml` is a sidecar container (`python:3.12-alpine`) running `scripts/discord_notify.py`. It tails `data/logs/latest.log` (mounted read-only) for "joined the game" / "left the game" lines and posts a message to a Discord webhook for each. It's a separate long-running container, not part of the `start.ps1` one-shot helper sequence — it starts and restarts independently via `docker compose up -d` / `restart: unless-stopped`, and only depends on the `mc` service existing (not on the log file being present yet — it polls for that).

To enable it: copy `.env.example` to `.env` (if you haven't already for DuckDNS) and set `DISCORD_WEBHOOK_URL` to a webhook URL from the target Discord channel (channel settings → Integrations → Webhooks). No firewall/UPnP/DuckDNS changes are needed since this only makes outbound HTTPS calls to Discord.

## World backups

The `backup` service in `docker-compose.yml` is a sidecar container (`itzg/mc-backup`, the companion image to `itzg/minecraft-server`) that periodically archives the world save out of `data/` into `backups/` (host-mounted, gitignored — runtime output, not source). Like `discord-notifier`, it's a separate long-running container started by `docker compose up -d` alongside `mc`, not part of the `start.ps1` one-shot sequence.

It talks to the server over RCON (`RCON_HOST: mc`, default port 25575, reached over the compose network — not exposed to the host or internet) to run `save-off`/`save-all`/`save-on` around each backup so the world isn't archived mid-write. This is why `mc` has `ENABLE_RCON: "TRUE"` and both `mc` and `backup` share `RCON_PASSWORD` from `.env`. Default schedule: a backup on startup, then every `BACKUP_INTERVAL` (24h), pruning archives older than `PRUNE_BACKUPS_DAYS` (7) — both are env vars on the `backup` service in `docker-compose.yml` if you want to change the cadence or retention.

To restore: stop the `mc` container, extract the desired tarball from `backups/` over `data/` (or the relevant subset — world folder, etc.), then start `mc` again.

To force an immediate backup without waiting for `BACKUP_INTERVAL` (e.g. before a risky change): `docker exec mc-backup backup now`. This runs a one-shot backup in parallel with the container's normal scheduled loop — safe to run anytime, they coordinate over an internal lockfile so they won't clobber each other.

## Client mod distribution (packwiz)

`packwiz/` is a [packwiz](https://packwiz.infra.link/) modpack — how players get the client-side modlist, kept in sync from your PC without anyone re-importing a full instance (which used to wipe their configs and singleplayer saves).

This is a **separate list from `docker-compose.yml`'s `MODRINTH_PROJECTS`**, not a mirror of it. The server list is what the dedicated server needs; `packwiz/` tracks whatever's actually installed in the Prism Launcher instance players connect with — currently sourced from the `Forge optifine + iris 26.2` instance folder (`instance.cfg` name: `virgocueva`; despite the folder name it's Fabric Loader `0.19.3` on MC `26.2`, matching the server). That instance has client-only mods with no server-side component (Sodium, Iris, minimap, HUD/QoL mods) alongside the ones that also run server-side (Simple Voice Chat, Lithium, FerriteCore, etc.), so expect the two lists to diverge — that's expected, not a bug.

Structure:
- `packwiz/pack.toml` — pack metadata: MC version, Fabric loader version, pack name/version. Its `[index]` block pins a hash of `index.toml`, so it's regenerated (not hand-edited) whenever the index changes.
- `packwiz/index.toml` — one entry per tracked file with its hash. This is what a player's installer diffs against to know what changed since last launch.
- `packwiz/mods/*.pw.toml` — one metadata file per mod: a Modrinth or CurseForge project/version reference plus a hash, no `.jar` committed. Jars are resolved and downloaded at install/update time, which is why this directory stays tiny even as the modlist grows.

The pack.toml players' installers point at:
```
https://raw.githubusercontent.com/taprile314/minecraft-server-pibes/master/packwiz/pack.toml
```

### Updating the modlist

`packwiz` (the CLI) is installed at `%USERPROFILE%\bin\packwiz.exe`, which is on PATH — just run `packwiz` from any shell. From inside `packwiz/`:
```
packwiz modrinth add <slug>     # add a Modrinth mod
packwiz curseforge add <slug>   # add a CurseForge mod
packwiz remove <name>           # drop a mod — packwiz list shows current names
packwiz refresh                 # recompute index.toml hashes after any manual edit under mods/
```
`packwiz modrinth/curseforge add` runs the refresh itself — you only need `packwiz refresh` after hand-editing a file under `mods/`. Then `git add packwiz/ && git commit && git push` — players don't do anything manually; see below.

If the binary is ever missing (new machine, `%USERPROFILE%\bin` wiped, etc.): packwiz doesn't publish tagged GitHub releases, only CI build artifacts, so `nightly.link`'s cached redirect can point at an expired artifact. Pull the run/artifact IDs directly instead:
```
gh api "repos/packwiz/packwiz/actions/workflows/60362/runs?branch=main&status=success&per_page=1" --jq '.workflow_runs[0].id'
gh api "repos/packwiz/packwiz/actions/runs/<run-id>/artifacts" --jq '.artifacts[] | select(.name=="Windows 64-bit") | .id'
gh api "repos/packwiz/packwiz/actions/artifacts/<artifact-id>/zip" > packwiz-win64.zip
```
Extract `packwiz.exe` from the zip and drop it in `%USERPROFILE%\bin\` (already on PATH).

Three project skills in `.claude/skills/` wrap this workflow: `/add-mod`, `/remove-mod`, and `/sync-prism-mods` (the last one reconciles `packwiz/` against whatever's actually installed in the Prism instance, for when a mod was added/removed by hand in Prism's own UI instead of through packwiz).

### How players install and get updates

Players run **packwiz-installer-bootstrap.jar** (get it from the [packwiz-installer-bootstrap releases](https://github.com/packwiz/packwiz-installer-bootstrap/releases) — this one does have tagged releases, unlike `packwiz` itself) as a Prism Launcher pre-launch command. One-time setup per friend:

1. Create a Fabric `0.19.3` / MC `26.2` instance in Prism — empty, no mods needed, packwiz installs them.
2. Drop `packwiz-installer-bootstrap.jar` into that instance's `minecraft/` folder.
3. Edit Instance → Settings → Custom Commands → enable, Pre-launch command:
   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/taprile314/minecraft-server-pibes/master/packwiz/pack.toml
   ```

This runs before every launch: it re-reads `pack.toml`/`index.toml` from GitHub, diffs by hash against what's installed, and adds/updates/removes only the tracked mod files — nothing outside `index.toml` (`config/`, `saves/`, `options.txt`, keybinds, resourcepacks, screenshots) is ever touched. That's the point of using packwiz over re-sharing a full instance: players get modlist updates without losing local progress or settings.

## Dependencies

The Python scripts need `upnpclient` and `requests` (no requirements.txt/lockfile currently checked in — install ad hoc if running them standalone). Docker and Docker Compose are required to run the server itself. `packwiz` (the CLI, at `%USERPROFILE%\bin\packwiz.exe`) is only needed to edit `packwiz/` — not required to run the server.

## Documenting new knowledge

If, while working in this repo, you surface a non-obvious fact worth preserving (a gotcha, a decision and its reasoning, a recovery procedure, anything future-you or Claude would otherwise have to rediscover the hard way) and there's no existing place for it in this file, the README, or elsewhere in the repo, add it to `docs/` (create the directory if it doesn't exist yet) rather than letting it evaporate at the end of the session.
