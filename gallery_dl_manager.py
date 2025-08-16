#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gallery-DL Manager v1.0.1
- NEW: Theme support (default, bright, high_contrast, mono) + persisted in config
- Settings menu: pick theme and toggle color on/off
- All v1.0 features retained: Ctrl+C Abort/Skip/Continue, CMD titles, defaults, updater, etc.
"""

from __future__ import annotations
import os, sys, json, time, random, socket, zipfile, datetime as dt, subprocess, shlex, re, signal, ctypes
from pathlib import Path
from typing import Dict, List, Tuple, Optional

APP_NAME = "Gallery-DL Manager"
APP_VERSION = "v1.0.1"

# ----------------------------- THEMES & UI ---------------------------------
THEMES = {
    "default": {
        "RESET":"\033[0m","CYAN":"\033[36m","YELLOW":"\033[33m","GREEN":"\033[32m",
        "RED":"\033[31m","MAGENTA":"\033[35m","WHITE":"\033[97m","BLUE":"\033[34m",
        "TITLE":"\033[36m",
    },
    "bright": {
        "RESET":"\033[0m","CYAN":"\033[96m","YELLOW":"\033[33m","GREEN":"\033[92m",
        "RED":"\033[31m","MAGENTA":"\033[95m","WHITE":"\033[97m","BLUE":"\033[94m",
        "TITLE":"\033[33m",
    },
    "high_contrast": {
        "RESET":"\033[0m","CYAN":"\033[96m","YELLOW":"\033[33m","GREEN":"\033[92m",
        "RED":"\033[91m","MAGENTA":"\033[95m","WHITE":"\033[97m","BLUE":"\033[94m",
        "TITLE":"\033[97m",
    },
    "mono": {
        "RESET":"\033[0m","CYAN":"\033[0m","YELLOW":"\033[0m","GREEN":"\033[0m",
        "RED":"\033[0m","MAGENTA":"\033[0m","WHITE":"\033[0m","BLUE":"\033[0m",
        "TITLE":"\033[0m",
    },
}

# runtime color vars (filled by apply_theme)
RESET=CYAN=YELLOW=GREEN=RED=MAGENTA=WHITE=BLUE=TITLE=None
USE_COLOR=True  # can be toggled in settings

def apply_theme(name: str):
    t = THEMES.get(name, THEMES["default"])
    global RESET, CYAN, YELLOW, GREEN, RED, MAGENTA, WHITE, BLUE, TITLE
    RESET=t["RESET"]; CYAN=t["CYAN"]; YELLOW=t["YELLOW"]; GREEN=t["GREEN"]
    RED=t["RED"]; MAGENTA=t["MAGENTA"]; WHITE=t["WHITE"]; BLUE=t["BLUE"]
    TITLE=t["TITLE"]

def c(t, col): return f"{col}{t}{RESET}" if USE_COLOR else t

def banner(title: str, root: Path):
    line = c("="*60, CYAN)
    print(line)
    print(c(f"  {title}   ", TITLE), c(f"Root: {root}", WHITE))
    print(line)

def section(title: str):
    print()
    print(c(title, YELLOW))

def prompt(label: str) -> str:
    return input(c(label, GREEN))

def set_console_title(title: str):
    if os.name == "nt":
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(str(title))
        except Exception:
            pass

# ----------------------------- PATHS/DEFAULTS ------------------------------
ROOT=Path(__file__).resolve().parent
DIR_DOWNLOADS=ROOT/"Downloads"; DIR_LINKS=ROOT/"Links"; DIR_URL_LISTS=ROOT/"URL-Lists"
DIR_CONFIG=ROOT/"config"; DIR_ARCHIVES=ROOT/"archives"; DIR_LOGS=ROOT/"logs"; DIR_BACKUPS=ROOT/"backups"
FILE_APP_SETTINGS=DIR_CONFIG/"app-settings.json"; FILE_SITE_SETTINGS=DIR_CONFIG/"site-delays.json"
GDL_OPTIONS_URL="https://github.com/mikf/gallery-dl/blob/master/docs/options.md"

DEFAULT_DELAY=30
DEFAULT_BASE_SLEEP=1
DEFAULT_JITTER=1.0

ABORT = {"want": False}
def _sigint_handler(signum, frame):
    ABORT["want"] = True
signal.signal(signal.SIGINT, _sigint_handler)

# ----------------------------- UTILITIES -----------------------------------
def now_ts(): return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
def ts_for_filename(): return dt.datetime.now().strftime("%Y%m%d-%H%M%S")
def ensure_dirs():
    for d in [DIR_DOWNLOADS,DIR_LINKS,DIR_URL_LISTS,DIR_CONFIG,DIR_ARCHIVES,DIR_LOGS,DIR_BACKUPS]:
        d.mkdir(parents=True, exist_ok=True)
def load_json(p:Path,default):
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8"))
        except Exception: return default
    return default
def save_json(p:Path,data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
def clear_screen(): os.system("cls" if os.name=="nt" else "clear")
def which(cmd:str)->Optional[str]:
    from shutil import which as _which; return _which(cmd)
def input_default(prompt_txt:str, default_val:str)->str:
    s=input(c(f"{prompt_txt} [{default_val}]: ", YELLOW)).strip()
    return s if s else default_val
def _normalize_args_to_string(val)->str:
    if isinstance(val, list):
        flat=[]
        for x in val:
            if isinstance(x, list): flat += [str(i) for i in x]
            else: flat.append(str(x))
        return " ".join(flat).strip()
    return str(val or "").strip()

# ----------------------------- SETTINGS ------------------------------------
def load_app_settings()->Dict:
    s=load_json(FILE_APP_SETTINGS, {})
    if "gallery_dl_path" not in s: s["gallery_dl_path"]=None
    if "global_extra_args" not in s: s["global_extra_args"]=""
    if "use_color" not in s: s["use_color"]=True
    if "theme" not in s: s["theme"]="default"  # NEW
    s["global_extra_args"]=_normalize_args_to_string(s.get("global_extra_args",""))
    save_json(FILE_APP_SETTINGS, s)
    # reflect prefs
    global USE_COLOR; USE_COLOR = bool(s.get("use_color", True))
    apply_theme(s.get("theme","default"))
    return s

def get_sites()->List[str]: return sorted([p.stem for p in DIR_URL_LISTS.glob("*.txt")])

def seed_site_defaults(site_cfg:Dict[str,Dict], sites:List[str])->bool:
    changed=False
    for s in sites:
        if s not in site_cfg:
            site_cfg[s]={
                "delay_between_urls_sec": DEFAULT_DELAY,
                "base_sleep_sec": DEFAULT_BASE_SLEEP,
                "jitter_sec": DEFAULT_JITTER,
                "extra_args": ""
            }
            changed=True
    return changed

def load_site_settings()->Dict[str,Dict]:
    s=load_json(FILE_SITE_SETTINGS, {}); changed=False
    for site,cfg in list(s.items()):
        if "delay_between_urls_sec" not in cfg: cfg["delay_between_urls_sec"]=DEFAULT_DELAY; changed=True
        if "base_sleep_sec" not in cfg: cfg["base_sleep_sec"]=DEFAULT_BASE_SLEEP; changed=True
        if "jitter_sec" not in cfg: cfg["jitter_sec"]=DEFAULT_JITTER; changed=True
        extra=_normalize_args_to_string(cfg.get("extra_args",""))
        if cfg.get("base_sleep_sec", DEFAULT_BASE_SLEEP)>0 and extra:
            toks=shlex.split(extra); kept=[]; i=0
            while i<len(toks):
                if toks[i]=="--sleep" and i+1<len(toks): i+=2; continue
                kept.append(toks[i]); i+=1
            extra=" ".join(kept)
        if extra!=cfg.get("extra_args",""): cfg["extra_args"]=extra; changed=True
    if seed_site_defaults(s, get_sites()): changed=True
    if changed: save_json(FILE_SITE_SETTINGS, s)
    return s

# ----------------------------- URL LISTS -----------------------------------
def read_site_urls(site:str)->List[str]:
    f=DIR_URL_LISTS/f"{site}.txt"
    if not f.exists(): return []
    lines=[ln.strip() for ln in f.read_text(encoding="utf-8", errors="ignore").splitlines()]
    urls=[ln for ln in lines if ln and not ln.lstrip().startswith("#") and not ln.isdigit()]
    return urls

# ----------------------------- GALLERY-DL ----------------------------------
def find_gallery_dl(app:Dict)->Tuple[Optional[str], Optional[str]]:
    path=app.get("gallery_dl_path")
    if path and Path(path.split()[0]).exists():
        exe = path.split()[0]
        resolved = which(exe) if " " not in path else which(exe)
        return path, resolved or exe
    for candidate in ["gallery-dl","gallery_dl","python -m gallery_dl","py -m gallery_dl"]:
        exe = which(candidate.split()[0]) if " " not in candidate else which(candidate.split()[0])
        if exe: return candidate, exe
    return None, None

def interpreter_for_script(script_path:str)->Optional[str]:
    try:
        with open(script_path, "r", encoding="utf-8") as f:
            first=f.readline().strip()
        if first.startswith("#!"): return first[2:].strip().strip('"')
    except Exception:
        pass
    return None

def gallery_dl_version(invocation:str)->str:
    try:
        parts = invocation.split(" ")+["--version"]
        out = subprocess.check_output(parts, text=True, stderr=subprocess.STDOUT)
        return out.strip()
    except Exception as e:
        return f"(failed: {e})"

def latest_gallery_dl_version()->Optional[str]:
    exe = which("pip") or which("pip3") or which("py")
    if not exe: return None
    try:
        cmdline = [exe,"index","versions","gallery-dl"] if "py" not in exe else [exe,"-m","pip","index","versions","gallery-dl"]
        out = subprocess.check_output(cmdline, text=True, stderr=subprocess.STDOUT, timeout=30)
        for line in out.splitlines():
            if "LATEST:" in line.upper(): return line.split(":",1)[1].strip()
        m=re.search(r"\b\d+\.\d+\.\d+\b", out); return m.group(0) if m else None
    except Exception: return None

def matching_pip_for(invocation:str, resolved_path:str)->Optional[List[str]]:
    if invocation.startswith("python ") or invocation.startswith("py "):
        interp = invocation.split()[0]
        return [interp, "-m", "pip"]
    if resolved_path:
        sheb = interpreter_for_script(resolved_path)
        if sheb: return [sheb, "-m", "pip"]
    exe = which("pip") or which("pip3") or which("py")
    if exe:
        return [exe] if exe!="py" else [exe,"-m","pip"]
    return None

def run_gallery_dl(invocation:str, url:str, dest_dir:Path, archive_path:Path, global_args:str, site_args:str)->int:
    parts: List[str] = invocation.split(" ") if " " in invocation else [invocation]
    parts += ["--download-archive", str(archive_path), "--dest", str(dest_dir)]
    gdl_conf = ROOT / "gallery-dl.conf"
    if gdl_conf.exists(): parts += ["--config", str(gdl_conf)]
    ga=_normalize_args_to_string(global_args); sa=_normalize_args_to_string(site_args)
    if ga: parts += shlex.split(ga)
    if sa: parts += shlex.split(sa)
    parts += [url]
    if os.environ.get("MG_DEBUG")=="1":
        print(c("DEBUG:", MAGENTA), " ".join(parts))
    try:
        proc=subprocess.Popen(parts)
        while True:
            rc = proc.poll()
            if rc is not None:
                return rc
            if ABORT["want"]:
                try: proc.terminate()
                except Exception: pass
                try: proc.kill()
                except Exception: pass
                return 130
            time.sleep(0.1)
    except KeyboardInterrupt:
        return 130

# ----------------------------- BACKUPS/LOGS --------------------------------
class RunStats:
    def __init__(self):
        self.start=time.time(); self.per_site={}; self.attempted=0; self.succeeded=0; self.failed=0; self.skipped=0
    def to_dict(self):
        return {"start": dt.datetime.fromtimestamp(self.start).isoformat(timespec="seconds"),
                "elapsed_sec": round(time.time()-self.start,2),
                "attempted": self.attempted, "succeeded": self.succeeded,
                "failed": self.failed, "skipped": self.skipped, "per_site": self.per_site}

def write_run_log(stats:RunStats, tag:str):
    p=DIR_LOGS/f"run-{tag}-{ts_for_filename()}.json"; save_json(p, stats.to_dict()); return p
def list_run_logs(): return sorted(DIR_LOGS.glob("run-*.json"))
def print_recent_runs(limit:int=10):
    logs=list_run_logs()[-limit:]
    if not logs: print("No run logs yet."); return
    for p in logs:
        d=load_json(p, {}); print(f"- {p.name}: start={d.get('start')} elapsed={d.get('elapsed_sec')}s ok={d.get('succeeded')} fail={d.get('failed')} attempted={d.get('attempted')}")

# ----------------------------- HEALTH/LINKS --------------------------------
def extract_host(url:str)->Optional[str]:
    try:
        from urllib.parse import urlparse; return urlparse(url).netloc
    except Exception: return None
def dns_ok(host:str)->bool:
    try: socket.gethostbyname(host); return True
    except Exception: return False
def preflight_report()->List[Tuple[str,str]]:
    rep=[]; 
    for site in get_sites():
        urls=read_site_urls(site)
        if not urls: rep.append((site,"EMPTY list")); continue
        host=None
        for u in urls:
            host=extract_host(u)
            if host: break
        if host and not dns_ok(host): rep.append((site,f"DNS FAIL for {host}"))
        else: rep.append((site,f"OK ({len(urls)} URLs)"))
    return rep

INI_TEMPLATE="[InternetShortcut]\nURL={url}\n"
SKIP_SEGMENTS={"user","users","profile","channel","channels"}
def url_to_filename(url:str)->str:
    from urllib.parse import urlparse
    path=urlparse(url).path.strip("/")
    if not path: return "root"
    parts=[p for p in path.split("/") if p and p.lower() not in SKIP_SEGMENTS]
    base=parts[-1] if parts else "link"
    safe="".join(ch for ch in base if ch.isalnum() or ch in ("-","_"))
    return safe or "link"
def build_links_from_lists():
    sites=get_sites()
    if not sites: print("No URL-Lists/*.txt found."); return
    for site in sites:
        site_dir=DIR_LINKS/site; site_dir.mkdir(parents=True, exist_ok=True)
        urls=read_site_urls(site); uniq=[]; seen=set()
        for u in urls:
            if u not in seen: uniq.append(u); seen.add(u)
        for url in uniq:
            (site_dir/(url_to_filename(url)+".url")).write_text(INI_TEMPLATE.format(url=url), encoding="utf-8")
        (DIR_LINKS/f"#{site}_links_from_lists.txt").write_text("\n".join(uniq), encoding="utf-8")
    print("Links built under", DIR_LINKS)

# ----------------------------- CORE FLOW -----------------------------------
def compute_sleep(base:int, jitter:float)->float:
    if base<=0: return 0.0
    low=max(0.0, base-jitter); high=base+jitter
    return random.uniform(low, high)

def _maybe_handle_sigint():
    if ABORT["want"]:
        ABORT["want"] = False
        choice = input("\nCtrl+C detected — [A]bort to menu, [S]kip this URL, [C]ontinue? ").strip().lower() or "a"
        if choice.startswith("a"):
            print("Aborting to menu..."); return "abort"
        if choice.startswith("s"):
            print("Skipping this URL..."); return "skip"
        print("Continuing..."); return "continue"
    return None

def download_for_site(site:str, app:Dict, site_cfg:Dict[str,Dict], stats:RunStats):
    urls=read_site_urls(site)
    if not urls: print(f"No URLs for {site}."); return
    cfg=site_cfg.get(site, {"delay_between_urls_sec":DEFAULT_DELAY,"base_sleep_sec":DEFAULT_BASE_SLEEP,"jitter_sec":DEFAULT_JITTER,"extra_args":""})
    per_url_delay=int(cfg.get("delay_between_urls_sec", DEFAULT_DELAY))
    base_sleep=int(cfg.get("base_sleep_sec", DEFAULT_BASE_SLEEP))
    jitter=float(cfg.get("jitter_sec", DEFAULT_JITTER))
    site_args=_normalize_args_to_string(cfg.get("extra_args",""))

    invocation, resolved=find_gallery_dl(app)
    if not invocation: print(c("gallery-dl not found. Use menu option to install/check.", RED)); return

    set_console_title(f"{APP_NAME} {APP_VERSION} · {site}")
    dest=DIR_DOWNLOADS; archive=DIR_ARCHIVES/f"{site}.sqlite"; archive.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n[{now_ts()}] {site}: {len(urls)} URLs. Using base_sleep={base_sleep}±{jitter}s and delay_between_urls={per_url_delay}s")

    site_stats={"attempted":0,"ok":0,"fail":0}
    for idx,url in enumerate(urls,1):
        act = _maybe_handle_sigint()
        if act == "abort": break
        if act == "skip": continue

        s=compute_sleep(base_sleep, jitter)
        if s>0: print(f"  → Sleeping {s:.2f}s before URL {idx}/{len(urls)}"); time.sleep(s)

        t0=time.time(); set_console_title(f"{APP_NAME} {APP_VERSION} · {site} · {idx}/{len(urls)}")
        print(f"[{now_ts()}] {site} [{idx}/{len(urls)}] START: {url}")
        rc=run_gallery_dl(invocation,url,dest,archive,load_app_settings().get("global_extra_args",""),site_args)
        elapsed=time.time()-t0
        stats.attempted+=1; site_stats["attempted"]+=1
        if rc==0:
            stats.succeeded+=1; site_stats["ok"]+=1; print(c(f"[{now_ts()}] {site} [{idx}/{len(urls)}] OK in {elapsed:.1f}s", GREEN))
        elif rc==130:
            act = _maybe_handle_sigint()
            if act == "abort":
                break
            elif act == "skip":
                stats.failed+=1; site_stats["fail"]+=1; print(c(f"[{now_ts()}] {site} [{idx}/{len(urls)}] SKIPPED after Ctrl+C", YELLOW))
                continue
            else:
                print(c("Retrying after Ctrl+C...", YELLOW))
                rc=run_gallery_dl(invocation,url,dest,archive,load_app_settings().get("global_extra_args",""),site_args)
                elapsed=time.time()-t0
                if rc==0:
                    stats.succeeded+=1; site_stats["ok"]+=1; print(c(f"[{now_ts()}] {site} [{idx}/{len(urls)}] OK in {elapsed:.1f}s", GREEN))
                else:
                    stats.failed+=1; site_stats["fail"]+=1; print(c(f"[{now_ts()}] {site} [{idx}/{len(urls)}] FAIL rc={rc} in {elapsed:.1f}s", RED))
        else:
            stats.failed+=1; site_stats["fail"]+=1; print(c(f"[{now_ts()}] {site} [{idx}/{len(urls)}] FAIL rc={rc} in {elapsed:.1f}s", RED))

        if per_url_delay>0 and idx<len(urls):
            print(f"  → Inter-URL delay {per_url_delay}s"); time.sleep(per_url_delay)

    stats.per_site[site]=site_stats
    set_console_title(f"{APP_NAME} {APP_VERSION}")
    print(f"\n{site} done. ok={site_stats['ok']} fail={site_stats['fail']} attempted={site_stats['attempted']}")

# ----------------------------- MENU & ACTIONS ------------------------------
def site_settings_menu():
    sites=get_sites()
    if not sites: print("No sites yet. Add *.txt to URL-Lists/"); return
    cfg=load_site_settings()
    while True:
        clear_screen(); banner("Site settings (delay, base sleep ± jitter, extra args)", ROOT)
        for i,s in enumerate(sites,1):
            csite=cfg.get(s, {"delay_between_urls_sec":DEFAULT_DELAY,"base_sleep_sec":DEFAULT_BASE_SLEEP})
            print(c(f"  {i} – {s} [delay_between_urls={csite.get('delay_between_urls_sec',DEFAULT_DELAY)}s, base_sleep={csite.get('base_sleep_sec',DEFAULT_BASE_SLEEP)}s]", BLUE))
        print(c("  0 – Back", BLUE))
        try: ch=int(prompt("Choose: ").strip() or "0")
        except Exception: return
        if ch==0: return
        idx=ch-1
        if not (0<=idx<len(sites)): continue
        s=sites[idx]
        cur=cfg.get(s, {"delay_between_urls_sec":DEFAULT_DELAY,"base_sleep_sec":DEFAULT_BASE_SLEEP,"jitter_sec":DEFAULT_JITTER,"extra_args":""})
        delay=int(input_default(f"Delay between URLs for {s} in seconds", str(cur.get("delay_between_urls_sec", DEFAULT_DELAY))))
        base_sleep=int(input_default(f"Base sleep seconds for {s} (randomized ±1s)", str(cur.get("base_sleep_sec", DEFAULT_BASE_SLEEP))))
        jitter=float(input_default(f"Jitter seconds (±) for {s}", str(cur.get("jitter_sec", DEFAULT_JITTER))))
        print(f"\nAdvanced: per-site extra gallery-dl args (see {GDL_OPTIONS_URL})")
        warn=" (note: --sleep here is ignored when base_sleep > 0)" if base_sleep>0 else ""
        extra=input_default(f"Args for {s}{warn}", str(cur.get("extra_args","")))
        extra=_normalize_args_to_string(extra)
        if base_sleep>0 and extra:
            toks=shlex.split(extra); kept=[]; i=0
            while i<len(toks):
                if toks[i]=="--sleep" and i+1<len(toks): i+=2; continue
                kept.append(toks[i]); i+=1
            extra=" ".join(kept)
        cfg[s]={"delay_between_urls_sec":delay,"base_sleep_sec":base_sleep,"jitter_sec":jitter,"extra_args":extra}
        save_json(FILE_SITE_SETTINGS, cfg)
        print(c("Saved.", GREEN)); input("Enter to continue...")

def check_install_gallery_dl():
    while True:
        clear_screen(); banner("Check/Install gallery-dl", ROOT)
        app=load_app_settings()
        invocation, resolved = find_gallery_dl(app)
        latest = latest_gallery_dl_version()
        if invocation:
            cur = gallery_dl_version(invocation)
            print(c(f"Using: {invocation}", WHITE))
            if resolved: print(c(f"Resolved path: {resolved}", WHITE))
            if latest and latest not in cur:
                print(c(f"You are running {cur}, but latest is {latest}", YELLOW))
            else:
                print(c(f"Current version: {cur}", GREEN))
        else:
            print(c("Not found on PATH.", RED))
        print("\nOptions:\n  1) pip install --upgrade gallery-dl (matches the interpreter above)\n  2) Re-check\n  3) Set explicit gallery-dl command/path\n  0) Back")
        ch=prompt("Choose: ")
        if ch=="1":
            invocation, resolved = find_gallery_dl(app)
            pip_cmd = matching_pip_for(invocation or "", resolved or "")
            if not pip_cmd:
                print(c("No suitable pip found. Install Python/pip.", RED)); input("Enter to continue..."); continue
            cmdline = pip_cmd + ["install","--upgrade","gallery-dl"]
            print(c("Running: ", MAGENTA) + " ".join(cmdline))
            subprocess.call(cmdline)
            continue
        elif ch=="2":
            continue
        elif ch=="3":
            new = input_default("Enter full command to run gallery-dl (e.g., 'python -m gallery_dl' or full path to gallery-dl)", (app.get("gallery_dl_path") or ""))
            app["gallery_dl_path"] = new.strip() or None
            save_json(FILE_APP_SETTINGS, app)
            continue
        elif ch=="0":
            break

def show_recent_runs():
    clear_screen(); banner("Recent runs", ROOT); print_recent_runs(); input("Enter to continue...")

def make_backup_zip()->Path:
    ts=ts_for_filename(); out=DIR_BACKUPS/f"gallery-dl-manager-backup-{ts}.zip"
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in DIR_CONFIG.rglob("*"):
            if p.is_file(): z.write(p, p.relative_to(ROOT))
        for p in DIR_URL_LISTS.rglob("*.txt"): z.write(p, p.relative_to(ROOT))
        if DIR_ARCHIVES.exists():
            for p in DIR_ARCHIVES.rglob("*"):
                if p.is_file(): z.write(p, p.relative_to(ROOT))
    return out

def settings_menu():
    app = load_app_settings()
    theme_order = ["default","bright","high_contrast","mono"]
    while True:
        clear_screen(); banner("Settings", ROOT)
        print(c(f"  1 – Site settings (per-site delay, base sleep ± jitter, extra args)", BLUE))
        print(c(f"  2 – Toggle menu colors (currently {'ON' if app.get('use_color', True) else 'OFF'})", BLUE))
        print(c(f"  3 – Theme (current: {app.get('theme','default')})", BLUE))
        print(c("  0 – Back", BLUE))
        ch = prompt("Choose: ").strip()
        if ch == "1":
            site_settings_menu()
        elif ch == "2":
            app["use_color"] = not app.get("use_color", True)
            save_json(FILE_APP_SETTINGS, app)
            global USE_COLOR; USE_COLOR = app["use_color"]
            print(f"Colors are now {'ON' if USE_COLOR else 'OFF'}."); input("Enter to continue...")
        elif ch == "3":
            cur = app.get("theme","default")
            idx = (theme_order.index(cur) + 1) % len(theme_order) if cur in theme_order else 0
            new = theme_order[idx]
            app["theme"] = new
            save_json(FILE_APP_SETTINGS, app)
            apply_theme(new)
            print(f"Theme set to: {new}"); input("Enter to continue...")
        elif ch == "0":
            return

# ----------------------------- MAIN ----------------------------------------
def main_menu():
    ensure_dirs(); app=load_app_settings(); site_cfg=load_site_settings()
    while True:
        clear_screen(); banner(f"{APP_NAME} {APP_VERSION}", ROOT)
        print(c("  1 – Download for one site (gallery-dl)", BLUE))
        print(c("  2 – Download for ALL (with preflight checks)", BLUE))
        print(c("  3 – Settings", BLUE))
        print(c("  4 – Build links FROM URL-Lists (exact URLs)", BLUE))
        print(c("  5 – Check/Install gallery-dl", BLUE))
        print(c("  6 – Show recent run stats", BLUE))
        print(c("  7 – Backup: config + URL-Lists + archives → zip", BLUE))
        print(c("  0 – Exit", BLUE))
        ch=prompt("Choose: ").strip()
        if ch=="1":
            s = prompt_site_choice()
            if not s: continue
            stats=RunStats(); download_for_site(s, app, load_site_settings(), stats)
            log_path=write_run_log(stats, tag=s); print("Run log:", log_path); input("Enter to continue...")
        elif ch=="2":
            clear_screen(); banner("Preflight checks", ROOT)
            rep=preflight_report(); bad=[]
            for site,status in rep:
                good=status.startswith("OK"); mark=c("OK", GREEN) if good else c("!!", RED)
                print(f"  {mark} {site}: {status}")
                if not good: bad.append(site)
            if bad: print(c("\nSome sites have issues and will be skipped: "+", ".join(bad), YELLOW))
            stats=RunStats()
            for site in get_sites():
                if site in bad: continue
                download_for_site(site, app, load_site_settings(), stats)
            log_path=write_run_log(stats, tag="all")
            print(f"\nALL DONE. attempted={stats.attempted} ok={stats.succeeded} fail={stats.failed}")
            print("Run log:", log_path); input("Enter to continue...")
        elif ch=="3":
            settings_menu()
        elif ch=="4":
            build_links_from_lists(); input("Enter to continue...")
        elif ch=="5":
            check_install_gallery_dl()
        elif ch=="6":
            show_recent_runs()
        elif ch=="7":
            p=make_backup_zip(); print(c("Backup written:", GREEN), p); input("Enter to continue...")
        elif ch=="0":
            break

def prompt_site_choice()->Optional[str]:
    sites=get_sites()
    if not sites: print("No sites. Add *.txt files to URL-Lists/ first."); return None
    section("Download for one site (with per-site breaks)")
    cfg=load_site_settings()
    for i,s in enumerate(sites,1):
        d=cfg.get(s,{}).get("delay_between_urls_sec", DEFAULT_DELAY)
        print(c(f"  {i} – {s} [break={d}s]", BLUE))
    print(c("  0 – Back", BLUE))
    try: ch=int(prompt("Choose: ").strip() or "0")
    except Exception: return None
    if ch==0 or ch>len(sites): return None
    return sites[ch-1]

if __name__=="__main__":
    try: 
        set_console_title(f"{APP_NAME} {APP_VERSION}")
        main_menu()
    except KeyboardInterrupt:
        print("\nBye!")
