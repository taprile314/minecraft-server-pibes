# Resource packs needed by a datapack: two independent delivery paths

Some datapacks (e.g. Pool and Billiards) ship textures/models in a separate, required resource pack. Not every player uses the Prism instance wired up to packwiz, so packwiz alone isn't a reliable way to get a resource pack to everyone — it only reaches players who launch through that specific instance.

**Solution: do both, they don't conflict.**

1. **packwiz** (`packwiz/resourcepacks/*.pw.toml`) — same mechanism as mods, just placed in `resourcepacks/` instead of `mods/` (packwiz auto-detects the Modrinth/CurseForge project type). Reaches players on the packwiz-managed Prism instance automatically on next launch. They still need to enable it once under Options → Resource Packs — packwiz deliberately never touches `options.txt`.

2. **Server-push** (`docker-compose.yml`'s `mc` service env vars: `RESOURCE_PACK`, `RESOURCE_PACK_SHA1`, `RESOURCE_PACK_ENFORCE`) — the `itzg/minecraft-server` image maps these directly to vanilla's `resource-pack`/`resource-pack-sha1`/`require-resource-pack` server.properties fields. The server prompts *any* client to download and apply the pack on join, regardless of launcher/mod setup. This is what actually covers players who don't use packwiz.

   - `RESOURCE_PACK` can point straight at the Modrinth CDN file URL (the same URL packwiz's `.pw.toml` resolved to) — no need to self-host.
   - `RESOURCE_PACK_SHA1` must be the file's SHA1 (not packwiz's sha512) — get it from the Modrinth API version endpoint (`hashes.sha1` on the file entry), not by hand-hashing.
   - `RESOURCE_PACK_ENFORCE: "FALSE"` (the default here) means players who decline the prompt just get vanilla fallback textures instead of being kicked. Set to `"TRUE"` if a future datapack is unplayable without its textures.
   - Only one resource pack can be server-pushed at a time — this field isn't a list. If a second datapack ever needs its own resource pack too, they'd need to be merged into one pack (or only the more important one wins this slot, with the rest packwiz-only).
