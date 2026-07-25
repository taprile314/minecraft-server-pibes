---
name: sync-prism-mods
description: Sync packwiz/ with whatever's actually installed in the pibes Prism Launcher instance (client-side mods folder), for when a mod was added or removed by hand in Prism instead of via the add-mod/remove-mod skills. Use when the user says something like "I installed a mod in Prism, reflect it in the repo" or "sync the modlist with my Prism instance".
---

The source of truth for the client modpack is normally `packwiz/` edited via `packwiz modrinth/curseforge add|remove` (see the `add-mod`/`remove-mod` skills). But sometimes the user installs or removes a mod directly through Prism Launcher's own UI first — this skill detects that drift and brings `packwiz/` in line with it.

`packwiz` (the CLI) is installed at `%USERPROFILE%\bin\packwiz.exe`, on PATH.

## Where the source instance lives

```
%APPDATA%\PrismLauncher\instances\Forge optifine + iris 26.2\minecraft\mods\
```

(Despite the folder name, this instance — `instance.cfg` name `virgocueva` — is Fabric Loader `0.19.3` on MC `26.2`, matching the server and the packwiz pack.) If that path doesn't exist anymore, look for a sibling folder under `...\PrismLauncher\instances\*\minecraft\mods\.index\` and ask the user to confirm which instance is the right one before proceeding — don't guess silently if there's more than one plausible candidate.

Prism keeps its own per-mod metadata at `<instance>\minecraft\mods\.index\*.pw.toml` — this is coincidentally the same format packwiz itself uses, with `x-prismlauncher-*` fields mixed in. That's what makes an exact, deterministic sync possible: each file's `[update.modrinth]` (`mod-id` + `version`) or `[update.curseforge]` (`project-id` + `file-id`) tells you precisely which version the user has installed, no guessing from mod names required.

## Steps

1. List `.pw.toml` files in both:
   - `<prism instance>\minecraft\mods\.index\*.pw.toml` (what's actually installed)
   - `packwiz\mods\*.pw.toml` (what's tracked in the repo)
2. **New in Prism, not in the repo** — for each:
   - Read the Prism `.pw.toml`. If it has an `[update.modrinth]` table:
     ```
     packwiz modrinth add --project-id <mod-id> --version-id <version> -y
     ```
     If it has `[update.curseforge]` instead:
     ```
     packwiz curseforge add --addon-id <project-id> --file-id <file-id> -y
     ```
   - This pins the exact version the user already has installed and tested — don't do a plain slug search here, it could resolve to a newer/different version than what's actually running.
3. **In the repo, no longer in Prism** — these were presumably removed by the user in Prism. List them and ask the user to confirm before removing each one (don't assume — they might have just disabled a mod temporarily, or this instance isn't the only source for the pack). For confirmed removals:
   ```
   packwiz remove "<exact name from packwiz list>"
   ```
4. `packwiz refresh` if you touched anything by hand; the add/remove commands above already refresh on their own otherwise.
5. Show the user a short summary (mods added / mods removed) before pushing.
6. From the repo root:
   ```
   git add packwiz/
   git commit -m "Sync packwiz pack with Prism instance: <short summary>"
   git push
   ```

Never run any `docker compose` command as part of this — the packwiz pack is independent of the running server container, and this skill never needs to touch it.
