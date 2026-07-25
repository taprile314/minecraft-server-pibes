---
name: remove-mod
description: Remove a mod from the pibes packwiz client modpack (packwiz/), then commit and push. Use when the user asks to remove/drop a mod from the client modlist for this Minecraft server repo.
---

Removes a mod from `packwiz/`, the client-side modpack players fetch via `packwiz-installer-bootstrap.jar`. This is separate from the server's `MODRINTH_PROJECTS` in `docker-compose.yml` — don't touch that file unless the user explicitly asks to also drop it from the server.

`packwiz` (the CLI) is installed at `C:\Users\tomas\bin\packwiz.exe`, on PATH.

## Steps

1. From the repo root, run `cd packwiz && packwiz list` to see the exact tracked names (these are the `name` field from each `mods/*.pw.toml`, not always identical to the slug or filename).
2. Match the user's request to the exact name from that list. If ambiguous, ask which one.
3. ```
   packwiz remove "<exact name>"
   ```
4. Confirm it's gone: `packwiz list` should no longer show it, and its `mods/*.pw.toml` file should be deleted.
5. From the repo root:
   ```
   git add packwiz/
   git commit -m "Remove <Mod Name> from the packwiz pack"
   git push
   ```
6. Tell the user what was removed and confirm the push succeeded. Players lose the mod automatically next time they launch — packwiz-installer deletes files no longer in the index.

Never run any `docker compose` command as part of this — the packwiz pack is independent of the running server container.
