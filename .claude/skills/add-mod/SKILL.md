---
name: add-mod
description: Add a mod to the pibes packwiz client modpack (packwiz/) from Modrinth or CurseForge, then commit and push. Use when the user asks to add/install a mod to the client modlist for this Minecraft server repo.
---

Adds a mod to `packwiz/`, the client-side modpack players fetch via `packwiz-installer-bootstrap.jar`. This is separate from the server's `MODRINTH_PROJECTS` in `docker-compose.yml` — don't touch that file unless the user explicitly asks for a server-side mod too.

`packwiz` (the CLI) is installed at `%USERPROFILE%\bin\packwiz.exe`, on PATH. If it's missing, see the "Updating the modlist" section of `CLAUDE.md` for how to refetch it.

## Steps

1. Get the mod name/slug/URL from the user. If they didn't say which provider (Modrinth vs CurseForge), default to Modrinth first — most mods are there.
2. From the repo root:
   ```
   cd packwiz
   packwiz modrinth add <slug-or-search-term> -y
   ```
   If that fails to find the project (or the user specifically wants a CurseForge mod), try:
   ```
   packwiz curseforge add <slug-or-search-term> -y
   ```
   `-y` accepts the top search result non-interactively — after adding, always check `packwiz list` and read the new `mods/<name>.pw.toml` to confirm it resolved to the mod the user actually meant (mod names can collide). If it picked the wrong project, remove the wrong `.pw.toml` and retry with a more specific search term or the exact Modrinth/CurseForge project URL.
3. `packwiz modrinth add`/`packwiz curseforge add` already run the refresh — no need for a separate `packwiz refresh` unless you hand-edited something.
4. From the repo root:
   ```
   git add packwiz/
   git commit -m "Add <Mod Name> to the packwiz pack"
   git push
   ```
5. Tell the user what was added and confirm the push succeeded. Nothing else needs to happen — players get it automatically next time they launch (see `CLAUDE.md`'s packwiz section for why).

Never run any `docker compose` command as part of this — the packwiz pack is independent of the running server container.
