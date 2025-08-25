# Gallery-DL Manager — Usage Guide

## 1. URL-Lists
- Create text files in `URL-Lists/` (one per site).  
  Example: `URL-Lists/redgifs.txt`
- Each line = one URL for that site.
- Lines starting with `#`, `-`, or `*` are **skipped** (comments / disabled).
- Blank lines and pure numbers are also ignored.

Example `redgifs.txt`:
```
https://www.redgifs.com/users/example1
- https://www.redgifs.com/users/skipthis
# This one is disabled
https://www.redgifs.com/users/example2
```
Only `example1` and `example2` are downloaded.

---

## 2. Running Downloads
- **Option 1: Download for one site**  
  Select the site you want, Manager handles archive, delays, and settings.
- **Option 2: Download for ALL**  
  Runs all sites in `URL-Lists/` after preflight checks:
  - Warns if a list is empty
  - Checks DNS resolution

During download:
- Archive `.sqlite` ensures items are **never re-downloaded**, even if you delete files later.
- Ctrl+C = interactive menu:
  - `[A]bort` to quit back to main menu
  - `[S]kip` to skip current URL
  - `[C]ontinue` to keep downloading

---

## 3. Per-site Settings
- **Delay between URLs** = wait time between entries in your list.
- **Base sleep** + **Jitter** = randomized delay.
- **Sleep mode**:
  - `url`: Manager waits before each URL entry.
  - `item`: Manager injects gallery-dl `--sleep low-high`, so **every file** pauses with a random delay.
- **Extra args** = advanced gallery-dl flags  
  (see <https://github.com/mikf/gallery-dl/blob/master/docs/options.md>)  
  Note: Manager strips `--sleep` if it’s already controlling sleep.

---

## 4. Themes & Colors
- Toggle ANSI colors on/off (good for terminals that don’t support color).
- Cycle between themes: `default`, `bright`, `high_contrast`, `mono`.

---

## 5. Backups
- Creates a zip with:
  - `config/` (app settings & site settings)
  - `URL-Lists/` (all lists)
  - `archives/` (per-site .sqlite download archives)
- Useful if you reinstall or move machines.

---

## 6. Logs & Run Stats
- Each run saves JSON log in `logs/`:
  - start time, elapsed, attempted/ok/failed counts
- “Show recent runs” menu lets you quickly review last jobs.

---

## 7. Links Builder
- Takes your `URL-Lists/` and builds `.url` shortcut files in `Links/` for quick opening in browser.
- Also creates a `#site_links_from_lists.txt` file with all URLs de-duplicated.

---

## 8. Update Check
- Detects your current gallery-dl version and the latest on PyPI.
- Can upgrade in-place using the exact Python environment Manager is running in.
- You can override with “Set explicit gallery-dl command/path” if you have multiple installs.

---

## 9. Folder Layout
```
Downloads/      # gallery-dl outputs
URL-Lists/      # one <site>.txt per site
config/         # app-settings.json, site-delays.json
archives/       # per-site .sqlite (download-archive)
logs/           # run summaries (JSON)
backups/        # zip backups of config, lists, archives
Links/          # optional .url shortcuts built from URL lists
```

---

## 10. Tips & Best Practices
- Use **Sleep mode = item** with jitter to look more human-like (e.g. 5 ± 2s).
- Keep archives backed up: if you lose them, gallery-dl will redownload everything.
- Use disabled lines (`-` or `*`) in URL-Lists to temporarily pause a user/channel without deleting.
- Run backups occasionally; they’re small but save headaches.
- Run “Download ALL” sparingly if you have many large lists; better to stagger sites.
