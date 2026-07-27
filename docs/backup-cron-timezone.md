# Backup schedule runs in UTC, not `TZ`

The `backup` service uses `itzg/mc-backup`'s `CRON_SCHEDULE` for clock-based backups (e.g. fixed daily times instead of "every 6h since container start"). This overrides `BACKUP_INTERVAL`/`INITIAL_DELAY` entirely — see the image's README.

**Gotcha:** `CRON_SCHEDULE` runs in UTC regardless of the `TZ` environment variable set on the service. `TZ` only affects log/RCON timestamps inside the container. The image's documented fix is to bind-mount `/etc/localtime` and `/etc/timezone` from the host so its cron picks up local time — but that path doesn't exist on a Windows Docker Desktop host, so it's not viable here.

**Workaround:** write the cron expression directly in UTC. Argentina is a fixed UTC-3 offset with no DST, so the conversion never needs revisiting:

```
CRON_SCHEDULE: "0 3,9,15,21 * * *"   # = 00:00 / 06:00 / 12:00 / 18:00 America/Argentina/Buenos_Aires
```

If the cadence or start-of-day time changes, recompute by adding 3 hours to the desired GMT-3 times.

Also note: setting `CRON_SCHEDULE` means no backup runs immediately on container start (unlike `BACKUP_INTERVAL`, which backs up once at startup then every interval) — the first backup after a restart happens at the next matching cron time.
