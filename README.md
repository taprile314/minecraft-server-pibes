# minecraft-server-pibes

Self-hosted Minecraft server (Fabric, MC 26.2) for playing with friends, running in Docker on a home machine behind a residential router.

This repo has two independent parts:

1. **Server infra** — `docker-compose.yml`, `start.ps1`, and `scripts/`: bring the server up and make it reachable from outside despite a dynamic public IP and NAT.
2. **Client modpack (`packwiz/`)** — the mod list players use to connect, distributed via [packwiz](https://packwiz.infra.link/) so it updates itself without wiping anyone's configs or saved progress.

> For detailed instructions aimed at working in this repo with Claude Code, see [`CLAUDE.md`](./CLAUDE.md).

> Everything published in this repo (docs, code comments, in-game/Discord messages) is kept in English, regardless of what language it was worked on in.

## If you're a player: how to install/update mods

1. Create an instance in [Prism Launcher](https://prismlauncher.org/): Fabric Loader `0.19.3`, Minecraft `26.2` (empty, no mods).
2. Download `packwiz-installer-bootstrap.jar` from the [packwiz-installer-bootstrap releases](https://github.com/packwiz/packwiz-installer-bootstrap/releases) and drop it into that instance's `minecraft/` folder.
3. In Prism: **Edit Instance → Settings → Custom Commands** → enable → **Pre-launch command**:
   ```
   "$INST_JAVA" -jar packwiz-installer-bootstrap.jar https://raw.githubusercontent.com/taprile314/minecraft-server-pibes/main/packwiz/pack.toml
   ```
4. Save and launch the game. Mods download automatically the first time, and update automatically every time after that — without losing your settings or your saves.

## If you're maintaining the server: repo layout

```
docker-compose.yml   # Fabric server + Discord notifier sidecar
start.ps1             # firewall + UPnP + DuckDNS + motd + docker compose up
scripts/               # network helpers (UPnP, DuckDNS, motd) and the Discord bot
packwiz/               # client modpack (see below)
.env.example           # variable template (DuckDNS + Discord webhook)
data/                  # live server state (gitignored, not versioned)
```

- **`docker-compose.yml`**: MC version, memory, difficulty, ops, and the *server-side* mod list (`MODRINTH_PROJECTS`).
- **`.env`** (not versioned — copy from `.env.example`): DuckDNS `DOMAIN`/`TOKEN` and `DISCORD_WEBHOOK_URL`.
- **`packwiz/`**: the *client-side* mod list — not a mirror of the server's, tracked by hash in `index.toml`, one `.pw.toml` file per mod under `mods/` (no `.jar`s committed, they're resolved on install). See `CLAUDE.md` for the full workflow on adding/removing mods and publishing an update.
- **`data/`**: world save, `server.properties`, whitelist/ops, logs — live state, gitignored, never committed.

Full detail on every piece (networking, Discord notifications, how to update the modpack) lives in [`CLAUDE.md`](./CLAUDE.md).
