# Gallery-DL Manager (v1.0)

A friendly, menu-driven companion for [gallery-dl](https://github.com/mikf/gallery-dl).
It adds per-site settings (delay/base sleep/jitter/extra args), health checks,
backups (including archives), run stats, update checks (with matching Python env),
and a simple Windows launcher.

## Features
- Per-site settings with sensible defaults (delay=30s, base sleep=1s, jitter=±1s)
- Randomized sleeps (base ± jitter), auto-removes `--sleep` in extra args to avoid double sleeps
- Health checks before “Download ALL” (empty list, DNS resolution)
- Backups to zip: `config/`, `URL-Lists/`, and `archives/` (download archives)
- Run stats saved as JSON in `logs/`
- Check/Install: uses the same Python environment as the `gallery-dl` invocation
- Optional color UI (toggle in Settings)
- Ctrl+C: Abort/Skip/Continue without killing the whole batch window
- MG_DEBUG=1: prints full `gallery-dl` command lines

## Getting Started
1. Install Python 3.10+ and `gallery-dl` (e.g. `python -m pip install gallery-dl`).
2. Place your URL lists as text files in `URL-Lists/` (one URL per line).
3. Run `Launch-Gallery-DL-Manager.bat` (Windows) or `python gallery_dl_manager_v1_0.py`.
4. Use **Settings** to tweak per-site delay/sleep/jitter and optional extra args.

If you have multiple `gallery-dl` installs, use **Check/Install** →
**Set explicit gallery-dl command/path**, e.g. `python -m gallery_dl`.

## Folder Layout
```
Downloads/      # gallery-dl outputs
URL-Lists/      # one <site>.txt per site
config/         # app-settings.json, site-delays.json (auto-seeded from URL-Lists)
archives/       # per-site .sqlite (download-archive)
logs/           # run summaries
backups/        # zip backups of config, lists, archives
Links/          # optional .url shortcuts built from URL lists
```

## License
MIT (see LICENSE)

## Credits
- Powered by the amazing [gallery-dl](https://github.com/mikf/gallery-dl).
