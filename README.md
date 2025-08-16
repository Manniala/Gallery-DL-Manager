# Gallery-DL Manager (v1.0.1)

A friendly, menu-driven companion for [gallery-dl](https://github.com/mikf/gallery-dl).
It adds per-site settings (delay/base sleep/jitter/extra args), health checks,
backups (including archives), run stats, update checks (with matching Python env),
and a simple Windows launcher.

## Features
- NEW: **Theme** support (default, bright, high_contrast, mono) + color toggle
- Per-site settings with sensible defaults (delay=30s, base sleep=1s, jitter=±1s)
- Randomized sleeps (base ± jitter), auto-removes `--sleep` in extra args to avoid double sleeps
- Health checks before “Download ALL” (empty list, DNS resolution)
- Backups to zip: `config/`, `URL-Lists/`, and `archives/` (download archives)
- Run stats saved as JSON in `logs/`
- Check/Install: uses the same Python environment as the `gallery-dl` invocation
- Ctrl+C: Abort/Skip/Continue without killing the whole batch window
- `MG_DEBUG=1`: prints full `gallery-dl` command lines
- **Per-site download archive (.sqlite)**: prevents re-downloading previously fetched items—even if you delete files later. One archive per site lives under `archives/`. Backed up by the built-in Backup command.

### How the download archive works
- Each site uses its own SQLite archive in `archives/<site>.sqlite`.
- `gallery-dl` records each downloaded item’s unique ID there.
- On future runs, items already in the archive are skipped—even if you manually deleted the files.

**Force a re-download?**  
- Temporarily use `--no-download-archive` in per-site “extra args” (not recommended), or  
- Delete/rename that site’s archive DB (you’ll re-download everything), or  
- Use targeted options from gallery-dl (e.g., `--range`) to pick specific items.  
  _(See gallery-dl options: <https://github.com/mikf/gallery-dl/blob/master/docs/options.md>)_

## Getting Started
1. Install Python 3.10+ and `gallery-dl` (e.g., `python -m pip install gallery-dl`).
2. Place your URL lists as text files in `URL-Lists/` (one URL per line).
3. Run `Launch-Gallery-DL-Manager.bat` (Windows) or `python gallery_dl_manager.py`.
4. Use **Settings** to tweak per-site delay/sleep/jitter and optional extra args; choose a **Theme** if desired.

If you have multiple `gallery-dl` installs, use **Check/Install** →  
**Set explicit gallery-dl command/path**, e.g., `python -m gallery_dl`.

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
