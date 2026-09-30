import os, sys, sqlite3, shutil, tempfile, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
DATA = LOCALAPPDATA / "PragmaticRouletteTracker"
PERSIST = DATA / "last_roulette_url.txt"
PROFILE = LOCALAPPDATA / "PragmaticBlackjackChrome"


def good(url):
    u = str(url or "").strip()
    low = u.lower()
    if not u.startswith(("http://", "https://")):
        return False
    blocked = (
        "jsessionid", "pragmaticplaylive", "pragmaticplay.net",
        "/game.do", "/api/", "sessionid=", "token=",
        "livechat", "google.", "facebook.", "youtube.", "cloudflare"
    )
    if any(x in low for x in blocked):
        return False
    return any(x in low for x in (
        "roulette", "rulet", "pragmatic", "opengames=", "searchterm=",
        "live-casino", "livecasino", "casino", "meritbet"
    ))


def stable_entry(url):
    """Keep the exact last visited user URL while stripping only one-time session tokens."""
    u = str(url or "").strip()
    if not good(u):
        return ""
    try:
        x = urllib.parse.urlsplit(u)
        qs = urllib.parse.parse_qsl(x.query, keep_blank_values=True)
        drop = {
            "sessionid", "jsessionid", "token", "auth", "jwt",
            "ticket", "sid", "otk", "keycode", "launchtoken"
        }
        qs = [(k, v) for k, v in qs if str(k).lower() not in drop]
        path = x.path or "/"
        return urllib.parse.urlunsplit((
            x.scheme, x.netloc, path,
            urllib.parse.urlencode(qs, doseq=True), x.fragment or ""
        ))
    except Exception:
        return ""


def save(url):
    url = stable_entry(url)
    if not url:
        return False
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        PERSIST.write_text(url, encoding="utf-8")
        return True
    except Exception:
        return False


def read_file(path):
    try:
        u = Path(path).read_text(encoding="utf-8", errors="ignore").strip()
        return stable_entry(u)
    except Exception:
        return ""

# 1) Persistent shared URL from V2.9.1+ (upgrade stripped legacy URLs if local file has full query)
u_persist = read_file(PERSIST)
u_local = read_file(HERE / "last_roulette_url.txt")
if u_persist and ("?" in u_persist or not u_local):
    print(u_persist); raise SystemExit(0)
if u_local:
    save(u_local); print(u_local); raise SystemExit(0)
if u_persist:
    print(u_persist); raise SystemExit(0)

# 3) Sibling/nearby older program folders (newest first)
try:
    root = HERE.parent
    files = sorted(
        root.glob("**/last_roulette_url.txt"),
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )[:40]
    for f in files:
        if f.resolve() == PERSIST.resolve():
            continue
        u = read_file(f)
        if u:
            save(u); print(u); raise SystemExit(0)
except Exception:
    pass

# 4) Dedicated Chrome profile history. Copy DB first so Chrome locks do not matter.
for history in (PROFILE / "Default" / "History", PROFILE / "History"):
    if not history.exists():
        continue
    tmp = None
    try:
        fd, name = tempfile.mkstemp(prefix="roulette_history_", suffix=".db")
        os.close(fd)
        tmp = Path(name)
        shutil.copy2(history, tmp)
        con = sqlite3.connect(str(tmp))
        cur = con.cursor()
        cur.execute("""
            SELECT url FROM urls
            WHERE (lower(url) LIKE '%roulette%'
               OR lower(url) LIKE '%rulet%'
               OR lower(url) LIKE '%pragmatic%'
               OR lower(url) LIKE '%opengames=%')
            ORDER BY last_visit_time DESC
            LIMIT 100
        """)
        rows = cur.fetchall()
        con.close()
        for row in rows:
            u = stable_entry(str(row[0] or ""))
            if u:
                save(u); print(u); raise SystemExit(0)
    except SystemExit:
        raise
    except Exception:
        pass
    finally:
        try:
            if tmp: tmp.unlink(missing_ok=True)
        except Exception:
            pass

# No safe URL found; launcher opens Chrome normally once.
print("")
