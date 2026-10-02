import base64
import html as html_lib
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import re
import secrets
import socket
import ssl
import subprocess
import struct
import sys
import threading
import time
import urllib.parse
import urllib.request
from collections import Counter
import tkinter as tk
from tkinter import ttk

DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 9222
PRAGMATIC_LOBBY_SCAN_URL = (
    "https://www.meritbet868.com/tr/live-casino/home"
    "?searchTerm=pragmatic+play+lobby"
)
COLLECTOR_MAX_CONCURRENT = 6
COLLECTOR_REFRESH_SECONDS = 600.0
COLLECTOR_RETRY_SECONDS = 60.0
# V2.9.42: finish lobby pass after return and ignore stale game frames.
# After pressing the in-game Lobi button, some old Pragmatic game iframes still
# report SON500/Lobi controls while the visible root page is already back in the
# roulette lobby. A short return grace lets the real lobby scan take priority.
COLLECTOR_PROBE_INITIAL_CONCURRENT = 0
COLLECTOR_PROBE_STEADY_CONCURRENT = 0
COLLECTOR_PROBE_SECONDS = 12.0
COLLECTOR_CARD_CLICK_SECONDS = 10.0
TABLE_SCAN_AUTO_REFRESH_SECONDS = 600.0
TAB_WALK_REFRESH_SECONDS = 300.0
TAB_WALK_TABLE_TIMEOUT_SECONDS = 120.0
TAB_WALK_TABLE_MIN_DWELL_SECONDS = 0.85
TAB_WALK_NO_SON500_SKIP_SECONDS = 16.0
TAB_WALK_EMPTY_SON500_SKIP_SECONDS = 18.0
TAB_WALK_RETURN_GRACE_SECONDS = 8.0
TAB_WALK_BLOCKED_TABLE_LABELS = (
    "POWERUP", "POWER UP",
    "PRIVE LOUNGE", "PRIVÉ LOUNGE",
    "GATES OF OLYMPUS", "OLYMPUS RULET", "OLYMPUS ROULETTE",
    "RULET DELUXE", "ROULETTE DELUXE",
)
PRAGMATIC_LOBBY_TABLES = (
    # Row 1 (image-1 top row)
    {"order": 1, "name": "Türkçe Rulet", "key": "TURKCE RULET", "patterns": ("TURKCE RULET", "TURKISH ROULETTE"), "blocked": False},
    {"order": 2, "name": "Türkçe Mega Rulet", "key": "TURKCE MEGA RULET", "patterns": ("TURKCE MEGA RULET", "TURKCE MEGA", "TURKISH MEGA ROULETTE"), "blocked": False},
    {"order": 3, "name": "Brezilya Portekizcesi Rulet", "key": "BREZILYA PORTEKIZCESI RULET", "patterns": ("BREZILYA PORTEKIZCESI RULET", "BRAZILIAN ROULETTE"), "blocked": False},
    {"order": 4, "name": "Rulet 1", "key": "RULET 1", "patterns": ("RULET 1", "ROULETTE 1"), "blocked": False},
    # Row 2 (image-1 second row)
    {"order": 5, "name": "Immersive Rulet Deluxe", "key": "IMMERSIVE RULET DELUXE", "patterns": ("IMMERSIVE RULET DELUXE", "IMMERSIVE ROULETTE DELUXE"), "blocked": True},
    {"order": 6, "name": "Rulet 2 Extra Time", "key": "RULET 2 EXTRA TIME", "patterns": ("RULET 2 EXTRA TIME", "ROULETTE 2 EXTRA TIME"), "blocked": False},
    {"order": 7, "name": "Rulet Macao", "key": "RULET MACAO", "patterns": ("RULET MACAO", "ROULETTE MACAO"), "blocked": False},
    {"order": 8, "name": "Hızlı Rulet 2", "key": "HIZLI RULET 2", "patterns": ("HIZLI RULET 2", "SPEED ROULETTE 2"), "blocked": False},
    # Row 3 (image-2 top row)
    {"order": 9, "name": "Rulet 3", "key": "RULET 3", "patterns": ("RULET 3", "ROULETTE 3"), "blocked": False},
    {"order": 10, "name": "Fransız Ruleti Geri Ödemeli", "key": "FRANSIZ RULETI GERI ODEMELI", "patterns": ("FRANSIZ RULETI GERI ODEMELI", "FRANSIZ RULETI", "FRENCH ROULETTE"), "blocked": False},
    {"order": 11, "name": "VIP Rulet", "key": "VIP RULET", "patterns": ("VIP RULET", "VIP ROULETTE"), "blocked": False},
    {"order": 12, "name": "Hızlı Rulet 1", "key": "HIZLI RULET 1", "patterns": ("HIZLI RULET 1", "SPEED ROULETTE 1"), "blocked": False},
    # Row 4 (image-2 second row)
    {"order": 13, "name": "Brezilya Portekizcesi Mega Rulet", "key": "BREZILYA PORTEKIZCESI MEGA RULET", "patterns": ("BREZILYA PORTEKIZCESI MEGA RULET", "BREZILYA PORTEKIZCESI MEGA", "MEGA ROLETA BRASIL", "BRAZILIAN MEGA ROULETTE"), "blocked": False},
    {"order": 14, "name": "Hızlı Rulet Latina", "key": "HIZLI RULET LATINA", "patterns": ("HIZLI RULET LATINA", "SPEED ROULETTE LATINA"), "blocked": False},
    {"order": 15, "name": "Amerikan Ruleti", "key": "AMERIKAN RULETI", "patterns": ("AMERIKAN RULETI", "AMERIKAN RULET", "AMERICAN ROULETTE"), "blocked": False},
    {"order": 16, "name": "Kristal Rulet", "key": "KRISTAL RULET", "patterns": ("KRISTAL RULET", "CRYSTAL ROULETTE"), "blocked": False},
    # Row 5 (image-3 top row)
    {"order": 17, "name": "Fortune Rulet", "key": "FORTUNE RULET", "patterns": ("FORTUNE RULET", "FORTUNE ROULETTE"), "blocked": False},
    {"order": 18, "name": "Lucky 6 Rulet", "key": "LUCKY 6 RULET", "patterns": ("LUCKY 6 RULET", "LUCKY 6 ROULETTE"), "blocked": False},
    {"order": 19, "name": "Gates of Olympus Rulet", "key": "GATES OF OLYMPUS RULET", "patterns": ("GATES OF OLYMPUS RULET", "GATES OF OLYMPUS", "OLYMPUS RULET", "OLYMPUS ROULETTE"), "blocked": True},
    {"order": 20, "name": "Mega Rulet", "key": "MEGA RULET", "patterns": ("MEGA RULET", "MEGA ROULETTE"), "blocked": False},
    # Row 6 (image-3 second row)
    {"order": 21, "name": "Mega Rulet 3000", "key": "MEGA RULET 3000", "patterns": ("MEGA RULET 3000", "MEGA ROULETTE 3000"), "blocked": False},
    {"order": 22, "name": "PowerUP Rulet", "key": "POWERUP RULET", "patterns": ("POWERUP RULET", "POWER UP RULET", "POWERUP ROULETTE", "POWER UP ROULETTE"), "blocked": True},
    {"order": 23, "name": "Privé Lounge Rulet Deluxe", "key": "PRIVE LOUNGE RULET DELUXE", "patterns": ("PRIVE LOUNGE RULET DELUXE", "PRIVE LOUNGE ROULETTE DELUXE"), "blocked": True},
    {"order": 24, "name": "Privé Lounge Rulet", "key": "PRIVE LOUNGE RULET", "patterns": ("PRIVE LOUNGE RULET", "PRIVE LOUNGE ROULETTE"), "blocked": True},
    # Row 7 (image-4 top row)
    {"order": 25, "name": "Almanca Rulet", "key": "ALMANCA RULET", "patterns": ("ALMANCA RULET", "GERMAN ROULETTE"), "blocked": False},
    {"order": 26, "name": "Otomatik Rulet", "key": "OTOMATIK RULET", "patterns": ("OTOMATIK RULET", "AUTO ROULETTE"), "blocked": False},
    {"order": 27, "name": "Rusça Rulet", "key": "RUSCA RULET", "patterns": ("RUSCA RULET", "RUSSIAN ROULETTE"), "blocked": False},
    {"order": 28, "name": "Rumence Rulet", "key": "RUMENCE RULET", "patterns": ("RUMENCE RULET", "ROMANIAN ROULETTE"), "blocked": False},
    # Row 8 (image-4 second row)
    {"order": 29, "name": "Rulet Latina", "key": "RULET LATINA", "patterns": ("RULET LATINA", "ROULETTE LATINA"), "blocked": False},
    {"order": 30, "name": "VIP Otomatik Rulet", "key": "VIP OTOMATIK RULET", "patterns": ("VIP OTOMATIK RULET", "VIP AUTO ROULETTE"), "blocked": False},
    {"order": 31, "name": "Otomatik Mega Rulet", "key": "OTOMATIK MEGA RULET", "patterns": ("OTOMATIK MEGA RULET", "AUTO MEGA ROULETTE"), "blocked": False},
    {"order": 32, "name": "Korece Rulet", "key": "KORECE RULET", "patterns": ("KORECE RULET", "KOREAN ROULETTE", "KORE RULET"), "blocked": False},
)


def normalize_lobby_table_text(text):
    s = str(text or "")
    tr_map = str.maketrans({
        "İ": "I", "ı": "I", "Ğ": "G", "ğ": "G",
        "Ü": "U", "ü": "U", "Ş": "S", "ş": "S",
        "Ö": "O", "ö": "O", "Ç": "C", "ç": "C",
        "É": "E", "é": "E", "Â": "A", "â": "A",
    })
    s = s.translate(tr_map).upper()
    s = re.sub(r"\s+", " ", s).strip()
    return s


def canonical_pragmatic_table_info(text):
    norm_txt = normalize_lobby_table_text(text)
    if not norm_txt:
        return None
    # Strip trailing bet/currency/player numbers so "₺ 2 • 1" never looks like "Rulet 1"
    cleaned = re.sub(r"(?:₺|TRY|EUR|USD|\$|€)\s*[0-9.,\s-]+.*$", "", norm_txt).strip()
    target_str = cleaned or norm_txt
    pairs = []
    for item in PRAGMATIC_LOBBY_TABLES:
        for pat in item["patterns"]:
            pairs.append((len(pat), pat, item))
    pairs.sort(key=lambda row: (-row[0], row[2]["order"]))
    for _plen, pat, item in pairs:
        if re.search(r"(?:^|[^A-Z0-9])" + re.escape(pat) + r"(?:$|[^A-Z0-9])", target_str):
            return dict(item)
    return None


def canonical_pragmatic_table_name(text, fallback=""):
    info = canonical_pragmatic_table_info(text)
    if info:
        return str(info["name"])
    return str(fallback or "")
DGA_FEED_WS_URL = "wss://dga.pragmaticplaylive.net/ws"
DGA_DEFAULT_CASINO_ID = "ppcds00000003709"
DGA_DEFAULT_CURRENCY = "TRY"
DGA_SUBSCRIBE_BATCH_SIZE = 80
DGA_RECONNECT_SECONDS = 10.0

EU_WHEEL = [0,32,15,19,4,21,2,25,17,34,6,27,13,36,11,30,8,23,10,5,24,16,33,1,20,14,31,9,22,18,29,7,28,12,35,3,26]
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

VOISINS = {22,18,29,7,28,12,35,3,26,0,32,15,19,4,21,2,25}
TIERS = {27,13,36,11,30,8,23,10,5,24,16,33}
ORPHELINS = {1,20,14,31,9,17,34,6}
REGIONS = {
    "VOISINS DU ZÉRO": VOISINS,
    "TIERS DU CYLINDRE": TIERS,
    "ORPHELINS": ORPHELINS,
}


def color_of(n):
    if n == 0:
        return "YEŞİL"
    return "KIRMIZI" if n in RED else "SİYAH"


def dozen_of(n):
    if n == 0:
        return "0"
    if n <= 12:
        return "1. DÜZİNE"
    if n <= 24:
        return "2. DÜZİNE"
    return "3. DÜZİNE"


def column_of(n):
    if n == 0:
        return "0"
    r = n % 3
    return "3. SÜTUN" if r == 0 else f"{r}. SÜTUN"


def wheel_neighbors(n, radius=2):
    i = EU_WHEEL.index(n)
    out = []
    for d in range(-radius, radius+1):
        out.append(EU_WHEEL[(i+d) % len(EU_WHEEL)])
    return out


def tracking_scores(history):
    """
    Heuristic score, NOT probability:
    recent frequency + wheel-neighbor recurrence.
    """
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36][:20]
    scores = {n: 0.0 for n in range(37)}
    if not hist:
        return scores

    # Recent hits matter more.
    for idx, n in enumerate(hist):
        recency = 1.0 / (1.0 + idx * 0.22)
        scores[n] += 2.4 * recency

        # Physical wheel neighbors get a smaller watch score.
        neigh = wheel_neighbors(n, 2)
        for distance, m in enumerate(neigh):
            d = abs(distance - 2)
            if m != n:
                scores[m] += (0.70 if d == 1 else 0.35) * recency

    # Frequency in last 20.
    freq = Counter(hist)
    for n, c in freq.items():
        scores[n] += c * 0.8

    return scores


def top_watch(history, k=5):
    scores = tracking_scores(history)
    items = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return items[:k]


def model_confidence(history):
    """
    Model confidence score from the lead of the heuristic ranking.
    This is NOT the true roulette probability.
    """
    scores = tracking_scores(history)
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    if not ordered:
        return None, 0.0
    best_n, best_s = ordered[0]
    second_s = ordered[1][1] if len(ordered) > 1 else 0.0
    if best_s <= 0:
        return best_n, 0.0
    gap_ratio = max(0.0, best_s-second_s) / max(best_s, 1e-9)
    spread = sum(max(0.0, s) for _, s in ordered)
    concentration = best_s / max(spread, 1e-9)
    confidence = 20.0 + 55.0*gap_ratio + 25.0*min(1.0, concentration*8.0)
    return best_n, max(1.0, min(99.0, confidence))



EXPERT_NAMES = ("RECENCY", "WHEEL", "TRANSITION", "WEB")


def normalize_probs(scores, floor=0.0005):
    vals = {n: max(0.0, float(scores.get(n, 0.0))) + floor for n in range(37)}
    total = sum(vals.values()) or 1.0
    return {n: vals[n] / total for n in range(37)}


def recency_expert(history):
    """
    Recent exact-number repetitions + frequency.
    This is a model distribution, not a claim about the true RNG probability.
    """
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36][:40]
    scores = {n: 0.18 for n in range(37)}
    freq = Counter(hist)
    for idx, n in enumerate(hist):
        w = 1.0 / (1.0 + idx * 0.24)
        # Do not parrot the last 3 spins (idx 0..2) if they only appeared once in the window.
        if idx <= 2 and freq.get(n, 0) <= 1:
            w *= 0.32
        scores[n] += 2.1 * w
    for n, c in freq.items():
        if c >= 2:
            scores[n] += 0.85 * c
        else:
            scores[n] += 0.30 * c
    return normalize_probs(scores)


def wheel_expert(history):
    """
    Physical-wheel clustering expert: recent hits push score toward their
    neighbouring pockets on the European wheel.
    """
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36][:30]
    scores = {n: 0.20 for n in range(37)}
    freq18 = Counter(hist[:18])

    for idx, n in enumerate(hist):
        w = 1.0 / (1.0 + idx * 0.20)
        i = EU_WHEEL.index(n)
        if idx == 0:
            center_mult = 0.32
        elif idx <= 2 and freq18.get(n, 0) <= 1:
            center_mult = 0.45
        else:
            center_mult = 0.94
        for d, mult in ((0, center_mult), (1, 0.94), (-1, 0.94),
                        (2, 0.64), (-2, 0.64), (3, 0.30), (-3, 0.30)):
            m = EU_WHEEL[(i+d) % 37]
            scores[m] += mult * w

    return normalize_probs(scores)


_WHEEL_LR = {
    n: (
        EU_WHEEL[(EU_WHEEL.index(n) - 1) % 37],
        EU_WHEEL[(EU_WHEEL.index(n) + 1) % 37],
    )
    for n in range(37)
}
_SEQ_PREP_CACHE = {}


def _prep_session_seq(session_results):
    if not session_results:
        return None
    n_raw = len(session_results)
    key = (
        id(session_results),
        n_raw,
        session_results[0] if n_raw else None,
        session_results[n_raw // 2] if n_raw else None,
        session_results[-1] if n_raw else None,
    )
    cached = _SEQ_PREP_CACHE.get(key)
    if cached is not None:
        return cached
    seq = [int(x) for x in session_results if isinstance(x, int) and 0 <= x <= 36]
    pos_by_num = [[] for _ in range(37)]
    for k in range(len(seq) - 1):
        pos_by_num[seq[k]].append(k)
    freq = Counter(seq[-2000:])
    maxf = max(freq.values()) if freq else 1
    res = (seq, pos_by_num, freq, maxf)
    if len(_SEQ_PREP_CACHE) > 32:
        _SEQ_PREP_CACHE.clear()
    _SEQ_PREP_CACHE[key] = res
    return res


def transition_expert(history, session_results):
    """
    V1.7.4 WEB HISTORY FUSION
    Uses all locally recorded spins for the current table:
    - exact 1-step transition: X -> next
    - 2-step pattern: A,X -> next
    - 3-step pattern: A,B,X -> next
    - recent occurrences receive slightly more weight
    - sparse exact transitions fall back to wheel-neighbour predecessors

    This is a ranking model, not knowledge of the next RNG result.
    """
    scores = {n: 0.45 for n in range(37)}
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36]
    prep = _prep_session_seq(session_results)

    if not hist or not prep or len(prep[0]) < 3:
        return normalize_probs(scores)

    seq, pos_by_num, freq, maxf = prep
    current = hist[0]
    nseq = len(seq)
    has2 = len(hist) >= 2 and nseq >= 3
    prev = hist[1] if has2 else -99
    has3 = len(hist) >= 3 and nseq >= 4
    p2 = hist[2] if has3 else -99

    positions = pos_by_num[current]
    exact_obs = len(positions)
    for k in positions:
        b = seq[k + 1]
        age = (nseq - 2) - k
        rec = 1.0 / (1.0 + age / 180.0)
        scores[b] += 3.8 + 1.6 * rec
        left_n, right_n = _WHEEL_LR[b]
        scores[left_n] += 0.28
        scores[right_n] += 0.28
        if has2 and k >= 1 and seq[k - 1] == prev:
            rec2 = 1.0 / (1.0 + age / 220.0)
            scores[b] += 1.5 + 0.7 * rec2
            if has3 and k >= 2 and seq[k - 2] == p2:
                rec3 = 1.0 / (1.0 + age / 260.0)
                scores[b] += 1.8 + 0.8 * rec3

    # Sparse fallback: what followed pockets physically close to current.
    if exact_obs < 4:
        for nb in set(wheel_neighbors(current, 2)):
            for k in pos_by_num[nb]:
                b = seq[k + 1]
                age = (nseq - 2) - k
                rec = 1.0 / (1.0 + age / 150.0)
                scores[b] += 0.16 + 0.18 * rec

    # Long-term frequency gets a tiny stabilizing vote, never dominates.
    for n, c in freq.items():
        scores[n] += 0.30 * (c / maxf)

    return normalize_probs(scores)


# Public observed Pragmatic Speed Auto sample (newest first) used only as a
# fallback seed when the live public stats page cannot be fetched.
# Fresh public observed fallback samples (newest first).
PUBLIC_AUTO_SEED_NEWEST = [
    7,9,2,22,24,3,1,29,14,10,33,36,29,14,0,9,7,22,9,12,
    1,18,25,20,3,19,25,15,5,36,0,23,8,35,20,15,11,32,17,34,
    17,7,24,28,3,34,32,28,18,4,22,15,34,23,35,24,29,25,10,32,
    2,35,23,0,7,25,14,28,2,33,18,33,4,8,29,6,29,35,29,2,
    0,19,20,13,22,19,3,4,6,36,14,22,0,27,32,0,12,25,6,5,
    34,18,34,19,3,13,15,33,30,15,9,3,33,30,25,4,25,36,32,22
]

PUBLIC_MEGA_SEED_NEWEST = [
    24,22,27,20,18,18,2,24,26,8,36,25,7,10,15,14,10,26,3,26,
    30,13,4,36,14,27,33,25,26,0,9,3,11,23,26,33,22,18,33,5,
    8,6,29,13,4,17,24,3,12,18,35,19,16,1,36,26,17,19,17,34,
    3,2,14,28,24,32,21,24,12,7,26,36,6,32,26,22,6,35,31,35,
    4,36,0,35,1,36,32,33,3,13,22,1,7,33,9,24,27,14,0,14,
    4,5,27,29,31,20,6,3,30,29,8,25,28,32,4,22,20,0,21,23
]

PUBLIC_TURKISH_MEGA_SEED_NEWEST = [
    21,25,34,18,31,25,21,35,0,9,6,16,36,17,12,32,6,30,16,2,
    6,8,28,16,22,31,30,25,18,16,33,35,11,32,13,19,20,13,11,16,
    0,19,35,26,18,8,29,30,32,14,7,27,12,27,2,14,1,28,5,10,
    20,11,23,7,8,0,27,16,24,22,25,27,26,23,4,2,3,5,23,21,
    11,18,25,27,32,0,12,8,30,17,20,5,6,28,6,0,20,26,30,30,
    15,36,5,25,25,27,0,21,31,13,9,11,6,21,27,26,9,0,19,25
]


def external_source_for_table(table_name):
    """
    Select only a candidate public source. V2.6.1 does not trust a name match:
    SON500 sequence validation is mandatory before any web data enters the model.
    """
    name = str(table_name or '').strip().lower()

    if ('turk' in name or 'türk' in name) and 'mega' in name:
        return (
            'https://gamedata365.com/games/turkish_mega_roulette',
            'Turkish Mega Roulette',
            list(PUBLIC_TURKISH_MEGA_SEED_NEWEST),
        )

    if 'mega' in name:
        return (
            'https://gamedata365.com/games/mega_roulette',
            'Mega Roulette',
            list(PUBLIC_MEGA_SEED_NEWEST),
        )

    # Pragmatic has distinct Auto Roulette and Speed Auto Roulette products.
    # Speed Auto may be tested as a candidate, but SON500 must prove same-table.
    if (
        'auto' in name or 'otomatik' in name
        or 'speed' in name or 'hızlı' in name
        or name in ('roulette','rulet','pragmatic roulette','pragmatic rulet','')
    ):
        return (
            'https://gamedata365.com/games/pp_speed_auto_roulette',
            'Pragmatic Speed Auto • ADAY',
            list(PUBLIC_AUTO_SEED_NEWEST),
        )

    return (None, f'kaynak adayı yok ({table_name or "masa adı yok"})', [])


def parse_public_recent_results(raw_html):
    if not raw_html:
        return []
    try:
        text = raw_html.decode('utf-8', errors='ignore') if isinstance(raw_html, (bytes, bytearray)) else str(raw_html)
    except Exception:
        return []
    text = html_lib.unescape(text)
    plain = re.sub(r'<[^>]+>', '\n', text)
    pos = plain.lower().find('recent results')
    if pos >= 0:
        plain = plain[pos:pos+40000]
    found = []
    seen_idx = set()
    for m in re.finditer(r'(?<!\d)(\d{1,3})\.\s*([0-9]{1,2})(?!\d)', plain):
        i = int(m.group(1)); n = int(m.group(2))
        if 1 <= i <= 500 and 0 <= n <= 36 and i not in seen_idx:
            found.append((i,n)); seen_idx.add(i)
    if len(found) >= 15:
        found.sort(key=lambda x:x[0])
        return [n for _i,n in found[:200]]
    return []


def find_headless_browser():
    candidates = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return ""


def fetch_rendered_public_page(url, timeout=13.0):
    exe = find_headless_browser()
    if not exe:
        return b""
    profile = os.path.join(
        os.environ.get('TEMP', os.path.dirname(os.path.abspath(__file__))),
        'RoulettePublicFetchProfile',
    )
    try:
        os.makedirs(profile, exist_ok=True)
    except Exception:
        pass
    cmd = [
        exe,'--headless=new','--disable-gpu','--disable-extensions',
        '--no-first-run','--no-default-browser-check','--disable-background-networking',
        '--hide-scrollbars','--virtual-time-budget=4500',f'--user-data-dir={profile}',
        '--dump-dom',url,
    ]
    try:
        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=timeout, creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0),
        )
        return proc.stdout or b""
    except Exception:
        return b""


def fetch_public_history(table_name, timeout=4.0):
    url, label, fallback = external_source_for_table(table_name)
    if not url:
        return [], label, False
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/153 Safari/537.36',
                'Accept-Language':'en-US,en;q=0.8','Cache-Control':'no-cache',
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(1200000)
        recent = parse_public_recent_results(raw)
        if len(recent) >= 15:
            return recent, f'{label} • canlı web', True
    except Exception:
        pass

    raw = fetch_rendered_public_page(url)
    recent = parse_public_recent_results(raw)
    if len(recent) >= 15:
        return recent, f'{label} • headless web', True

    # Never trust fallback just because the name looks similar.
    return list(fallback), f'{label} • eski yedek aday', False


def best_contiguous_overlap(a_newest, b_newest, limit=180):
    a = [int(x) for x in (a_newest or []) if isinstance(x,int) and 0 <= x <= 36][:limit]
    b = [int(x) for x in (b_newest or []) if isinstance(x,int) and 0 <= x <= 36][:limit]
    best = (0,-1,-1)
    for ia in range(len(a)):
        for ib in range(len(b)):
            if a[ia] != b[ib]:
                continue
            run = 0
            while ia+run < len(a) and ib+run < len(b) and a[ia+run] == b[ib+run]:
                run += 1
            if run > best[0]:
                best = (run,ia,ib)
    return best


def web_matches_table(table500, candidate):
    if len(table500 or []) < 20 or len(candidate or []) < 15:
        return False, 0
    run, _ia, _ib = best_contiguous_overlap(table500,candidate,limit=180)
    return run >= 8, run


_EXT_PREP_CACHE = {}
_EXT_WEB_CACHE = {}
_EXT_SNAP_CACHE = {}


def _prep_external_seq(external_newest):
    if not external_newest:
        return None
    n_raw = len(external_newest)
    key = (
        id(external_newest),
        n_raw,
        external_newest[0] if n_raw else None,
        external_newest[n_raw // 2] if n_raw else None,
        external_newest[-1] if n_raw else None,
    )
    cached = _EXT_PREP_CACHE.get(key)
    if cached is not None:
        return cached
    ext = [
        int(x) for x in external_newest[:150000]
        if isinstance(x, int) and -1 <= x <= 36
    ]
    valid_spins = 0
    tables_count = 0
    in_seg = False
    head_120 = []
    for x in ext:
        if 0 <= x <= 36:
            valid_spins += 1
            if len(head_120) < 120:
                head_120.append(x)
            if not in_seg:
                tables_count += 1
                in_seg = True
        else:
            in_seg = False
    seq = list(reversed(ext))
    pos_by_num = [[] for _ in range(37)]
    limit = len(seq) - 1
    for i in range(limit):
        v = seq[i]
        if 0 <= v <= 36 and 0 <= seq[i + 1] <= 36:
            pos_by_num[v].append(i)
    res = (key, ext, seq, valid_spins, tables_count, head_120, pos_by_num)
    if len(_EXT_PREP_CACHE) > 32:
        _EXT_PREP_CACHE.clear()
        _EXT_WEB_CACHE.clear()
        _EXT_SNAP_CACHE.clear()
    _EXT_PREP_CACHE[key] = res
    return res


def external_web_expert(history, external_newest):
    """
    Public-history / multi-table archive expert. It uses observed results as
    another vote: current->next, previous/current->next, 3-step and recency-weighted
    frequencies. Supports -1 boundary markers between separate tables so cross-table
    boundaries never create false transitions.
    """
    scores = {n: 0.42 for n in range(37)}
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36]
    prep = _prep_external_seq(external_newest)
    if not hist or not prep or prep[3] < 10:
        return normalize_probs(scores)

    prep_key, _ext, seq, _valid_spins, _tables_count, head_120, pos_by_num = prep
    cache_key = (prep_key, tuple(hist[:3]))
    cached_dist = _EXT_WEB_CACHE.get(cache_key)
    if cached_dist is not None:
        return dict(cached_dist)

    current = hist[0]
    has2 = len(hist) >= 2
    prev = hist[1] if has2 else -99
    has3 = len(hist) >= 3
    p2 = hist[2] if has3 else -99

    positions = pos_by_num[current]
    exact_obs = len(positions)
    for i in positions:
        b = seq[i + 1]
        scores[b] += 4.8
        left_n, right_n = _WHEEL_LR[b]
        scores[left_n] += 0.26
        scores[right_n] += 0.26
        if has2 and i >= 1 and seq[i - 1] == prev:
            scores[b] += 1.6
            if has3 and i >= 2 and seq[i - 2] == p2:
                scores[b] += 1.8

    # If exact current transitions are sparse, use transitions from physical
    # neighbours of the current pocket with a much smaller vote.
    if exact_obs < 3:
        for nb in set(wheel_neighbors(current, 2)):
            for i in pos_by_num[nb]:
                scores[seq[i + 1]] += 0.55

    # Recent frequency is only a stabilizer on a single table, not a 'due' rule.
    if _tables_count <= 1:
        for idx, n in enumerate(head_120):
            scores[n] += 0.18 / (1.0 + idx * 0.035)

    out = normalize_probs(scores)
    if len(_EXT_WEB_CACHE) > 64:
        _EXT_WEB_CACHE.clear()
    _EXT_WEB_CACHE[cache_key] = dict(out)
    return out


def external_transition_snapshot(history, external_newest):
    """
    Calculate empirical transition counts and % probabilities across a single
    archive or the combined multi-table pool (-1 separates tables).
    """
    hist = [int(x) for x in (history or []) if isinstance(x, int) and 0 <= x <= 36]
    prep = _prep_external_seq(external_newest)
    valid_spins = prep[3] if prep else 0
    tables_count = prep[4] if prep else 0

    cur = hist[0] if hist else None
    prev = hist[1] if len(hist) >= 2 else None

    if not hist or valid_spins < 2:
        return {
            'spins': valid_spins,
            'tables': tables_count,
            'current': cur,
            'prev': prev,
            'exact_obs': 0,
            'exact_top': [],
            'exact_top_pct': [],
            'exact_probs': {},
            'pair_obs': 0,
            'pair_top': [],
            'pair_top_pct': [],
            'pair_probs': {},
        }

    prep_key, _ext, seq, _valid_spins, _tables_count, _head_120, pos_by_num = prep
    cache_key = (prep_key, tuple(hist[:2]))
    cached_snap = _EXT_SNAP_CACHE.get(cache_key)
    if cached_snap is not None:
        return dict(cached_snap)

    exact = Counter()
    pair = Counter()
    has2 = len(hist) >= 2
    for i in pos_by_num[cur]:
        b = seq[i + 1]
        exact[b] += 1
        if has2 and i >= 1 and seq[i - 1] == prev:
            pair[b] += 1
    exact_obs = sum(exact.values())
    pair_obs = sum(pair.values())

    exact_sorted = sorted(
        exact,
        key=lambda n: (-exact[n], -pair.get(n, 0), n),
    )[:5]
    exact_top = [(int(n), int(exact[n])) for n in exact_sorted]
    exact_top_pct = [
        (int(n), int(exact[n]), (exact[n] / exact_obs * 100.0) if exact_obs else 0.0)
        for n in exact_sorted
    ]
    exact_probs = (
        {n: (exact.get(n, 0) / exact_obs) for n in range(37)}
        if exact_obs else {}
    )

    pair_sorted = sorted(
        pair,
        key=lambda n: (-pair[n], -exact.get(n, 0), n),
    )[:5]
    pair_top = [(int(n), int(pair[n])) for n in pair_sorted]
    pair_top_pct = [
        (int(n), int(pair[n]), (pair[n] / pair_obs * 100.0) if pair_obs else 0.0)
        for n in pair_sorted
    ]
    pair_probs = (
        {n: (pair.get(n, 0) / pair_obs) for n in range(37)}
        if pair_obs else {}
    )

    out = {
        'spins': valid_spins,
        'tables': max(1, tables_count) if valid_spins else 0,
        'current': cur,
        'prev': prev,
        'exact_obs': exact_obs,
        'exact_top': exact_top,
        'exact_top_pct': exact_top_pct,
        'exact_probs': exact_probs,
        'pair_obs': pair_obs,
        'pair_top': pair_top,
        'pair_top_pct': pair_top_pct,
        'pair_probs': pair_probs,
    }
    if len(_EXT_SNAP_CACHE) > 64:
        _EXT_SNAP_CACHE.clear()
    _EXT_SNAP_CACHE[cache_key] = dict(out)
    return out


def multi_table_transition_expert(history, pool_newest):
    """
    Empirical multi-table transition probability model.
    When a number (e.g. 1) lands on the main table, this computes the exact
    observed transition percentage P(next | current) across all collected
    tables (plus 2-step P(next | prev, current) tie-breaking) and converts
    it into a normalized 37-number probability distribution for the model.
    """
    base_web = external_web_expert(history, pool_newest)
    snap = external_transition_snapshot(history, pool_newest)
    exact_obs = int(snap.get("exact_obs", 0) or 0)
    if exact_obs <= 0:
        return base_web

    exact_probs = snap.get("exact_probs") or {}
    pair_obs = int(snap.get("pair_obs", 0) or 0)
    pair_probs = snap.get("pair_probs") or {}

    scores = {}
    step_unit = 1.0 / max(1, exact_obs)
    for n in range(37):
        p1 = float(exact_probs.get(n, 0.0) or 0.0)
        pair_cnt = float(pair_probs.get(n, 0.0) or 0.0) * pair_obs if pair_obs > 0 else 0.0
        bw = float(base_web.get(n, 1.0 / 37.0) or 0.0)
        # 2-step count is scaled as a fraction (0.25) of a single 1-step observation
        # so it cleanly breaks ties (e.g. 17x vs 17x) without ever overriding a higher 1-step count.
        eff_p = p1 + 0.25 * step_unit * pair_cnt
        if exact_obs >= 20:
            # Amplify high-percentage transitions so the top ORTAK HAVUZ percentages
            # press with clear, decisive net weight while strictly preserving their order.
            scores[n] = (eff_p ** 1.35) if eff_p > 0.0 else 0.0
        else:
            scores[n] = 0.92 * eff_p + 0.08 * bw

    return normalize_probs(scores, floor=0.0001)


def expert_distributions(history, session_results, external_history=None):
    return {
        "RECENCY": recency_expert(history),
        "WHEEL": wheel_expert(history),
        "TRANSITION": transition_expert(history, session_results),
        "WEB": external_web_expert(history, external_history or []),
    }


def _smoothed_rate(hits, trials, baseline, prior_strength=22.0):
    """
    Bayesian-style shrinkage toward roulette baseline.
    Prevents a few lucky hits from dominating.
    """
    trials = max(0, int(trials or 0))
    hits = max(0, int(hits or 0))
    return (
        hits + baseline * prior_strength
    ) / (
        trials + prior_strength
    )


def adaptive_weights(expert_loss, expert_trials, expert_hits=None):
    """
    V1.6:
    - log-loss quality
    - each expert's own exact / top5 / ±2-neighbour hit rates
    - maturity caps/floors to prevent one expert dominating too early
    """
    priors = {"RECENCY": 0.18, "WHEEL": 0.27, "TRANSITION": 0.35, "WEB": 0.20}
    expert_hits = expert_hits or {
        name: {"trials": 0, "exact": 0, "top5": 0, "neighbor5": 0}
        for name in EXPERT_NAMES
    }

    t = max(0, int(expert_trials or 0))

    if t < 8:
        return priors.copy()

    # --- 1) Log-loss component ---
    avg_loss = {
        name: float(expert_loss.get(name, 0.0)) / max(1, t)
        for name in EXPERT_NAMES
    }
    best_loss = min(avg_loss.values())
    loss_skill = {
        name: math.exp(-0.55 * (avg_loss[name] - best_loss))
        for name in EXPERT_NAMES
    }

    # --- 2) Direct hit-performance component ---
    exact_base = 1.0 / 37.0
    top5_base = 5.0 / 37.0
    neigh_base = 5.0 / 37.0

    direct_skill = {}
    for name in EXPERT_NAMES:
        st = expert_hits.get(name, {})
        n = int(st.get("trials", 0))

        exact_rate = _smoothed_rate(
            st.get("exact", 0), n, exact_base, prior_strength=22.0
        )
        top5_rate = _smoothed_rate(
            st.get("top5", 0), n, top5_base, prior_strength=18.0
        )
        neigh_rate = _smoothed_rate(
            st.get("neighbor5", 0), n, neigh_base, prior_strength=18.0
        )

        exact_ratio = exact_rate / exact_base
        top5_ratio = top5_rate / top5_base
        neigh_ratio = neigh_rate / neigh_base

        # Top5 and physical-neighbour performance are more stable than exact.
        skill = (
            0.20 * exact_ratio
            + 0.45 * top5_ratio
            + 0.35 * neigh_ratio
        )

        # Keep skill within a sane range.
        direct_skill[name] = min(1.65, max(0.35, skill))

    # --- 3) Combine prior, log-loss and observed hits ---
    raw = {}
    for name in EXPERT_NAMES:
        raw[name] = (
            priors[name]
            * loss_skill[name]
            * (direct_skill[name] ** 1.22)
        )

    # Minimum floor so a model can recover later.
    for name in raw:
        raw[name] = max(raw[name], 0.06)

    # Normalize.
    total = sum(raw.values()) or 1.0
    w = {name: raw[name] / total for name in EXPERT_NAMES}

    # --- 4) Maturity cap ---
    if t < 25:
        cap = 0.40
        floor = 0.15
    elif t < 100:
        cap = 0.50
        floor = 0.10
    else:
        cap = 0.60
        floor = 0.08

    # Iterative cap/floor redistribution.
    for _ in range(6):
        changed = False

        # Floors first
        deficit = 0.0
        free = []
        for name in EXPERT_NAMES:
            if w[name] < floor:
                deficit += floor - w[name]
                w[name] = floor
                changed = True
            else:
                free.append(name)

        if deficit > 0 and free:
            pool = sum(w[n] for n in free)
            if pool > 0:
                for n in free:
                    w[n] -= deficit * (w[n] / pool)

        # Caps
        excess = 0.0
        free = []
        for name in EXPERT_NAMES:
            if w[name] > cap:
                excess += w[name] - cap
                w[name] = cap
                changed = True
            else:
                free.append(name)

        if excess > 0 and free:
            pool = sum(w[n] for n in free)
            if pool > 0:
                for n in free:
                    w[n] += excess * (w[n] / pool)

        if not changed:
            break

    total = sum(w.values()) or 1.0
    return {name: w[name] / total for name in EXPERT_NAMES}


def combined_prediction(
    history,
    session_results,
    expert_loss=None,
    expert_trials=0,
    expert_hits=None,
    external_history=None
):
    expert_loss = expert_loss or {name: 0.0 for name in EXPERT_NAMES}
    experts = expert_distributions(history, session_results, external_history)
    weights = adaptive_weights(
        expert_loss,
        expert_trials,
        expert_hits
    )

    combined = {n: 0.0 for n in range(37)}
    for name in EXPERT_NAMES:
        for n in range(37):
            combined[n] += weights[name] * experts[name][n]

    # Mild anti-stickiness: if the exact same pocket repeats back-to-back,
    # reduce the chance of the tracker staying locked on the same pocket again.
    recent = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36][:4]
    if recent:
        last_n = recent[0]
        streak = 1
        for x in recent[1:]:
            if x == last_n:
                streak += 1
            else:
                break
        if streak >= 2:
            penalty = 0.74 if streak == 2 else 0.58
            combined[last_n] *= penalty
            total_p = sum(combined.values()) or 1.0
            combined = {n: combined[n] / total_p for n in range(37)}

    ordered = sorted(combined.items(), key=lambda kv: (-kv[1], kv[0]))
    best_n, best_p = ordered[0]
    second_p = ordered[1][1]
    top5 = [n for n, _p in ordered[:5]]

    # A relative model score, NOT the true roulette probability.
    uniform = 1.0 / 37.0
    lift = max(0.0, (best_p - uniform) / uniform)
    margin = max(0.0, best_p - second_p)
    model_score = 22.0 + 23.0 * min(1.0, lift / 1.3) + 55.0 * min(1.0, margin / 0.025)
    model_score = max(1.0, min(99.0, model_score))

    return {
        "predicted": best_n,
        "model_share": best_p * 100.0,
        "model_score": model_score,
        "top5": top5,
        "combined": combined,
        "experts": experts,
        "weights": weights,
    }



def is_betting_grid_artifact(nums):
    """
    Detect non-history DOM artifacts such as the 37-number betting table (0..36)
    or the physical wheel/racetrack sequence (EU_WHEEL).
    """
    seq = [int(x) for x in (nums or []) if isinstance(x, int) and 0 <= int(x) <= 36]
    if not seq:
        return False
    if 34 <= len(seq) <= 44 and len(set(seq[:37])) >= 34:
        return True
    for i in range(max(0, len(seq) - 5)):
        w = seq[i:i + 6]
        if w == [w[0] + k for k in range(6)] or w == [w[0] + 3 * k for k in range(6)]:
            return True
    if len(seq) >= 7:
        wheel_pos = {n: idx for idx, n in enumerate(EU_WHEEL)}
        for i in range(len(seq) - 6):
            p0 = wheel_pos.get(seq[i], -99)
            if all(wheel_pos.get(seq[i + k], -99) == (p0 + k) % 37 for k in range(1, 7)):
                return True
            if all(wheel_pos.get(seq[i + k], -99) == (p0 - k) % 37 for k in range(1, 7)):
                return True
    return False


def choose_live_dom_candidate(candidates, current_history):
    """
    Choose the single DOM candidate that represents the actual live roulette
    history bar, and determine how it aligns with current_history.

    Never roll history backwards to an older/unrelated widget.
    """
    current = [
        int(x) for x in (current_history or [])
        if isinstance(x, int) and 0 <= x <= 36
    ][:20]

    prepared = []
    for raw in candidates or []:
        if isinstance(raw, dict):
            nums_raw = raw.get("nums", [])
            meta = raw
        else:
            nums_raw = raw
            meta = {}

        nums = []
        for x in nums_raw or []:
            try:
                n = int(x)
            except Exception:
                continue
            if 0 <= n <= 36:
                nums.append(n)

        if len(nums) >= 5 and not is_betting_grid_artifact(nums):
            prepared.append((nums[:30], meta))

    if not prepared:
        return None

    if not current:
        def boot_score(item):
            nums, meta = item
            hint = (
                str(meta.get("testid", "")) + " "
                + str(meta.get("cls", ""))
            ).lower()
            bonus = 0
            if meta.get("son500Grid"):
                bonus += 40
            if meta.get("collapsedBar"):
                bonus += 30
            if "history" in hint:
                bonus += 20
            if "recent" in hint:
                bonus += 15
            if "result" in hint:
                bonus += 10
            return (bonus, len(nums))
        nums, meta = max(prepared, key=boot_score)
        return {
            "nums": nums,
            "meta": meta,
            "relation": "bootstrap",
            "new_count": 0,
            "overlap": 0,
        }

    best = None

    # Pass 1: strictly check forward (newest-first) orientation across all DOM candidates.
    # Never allow a reversed candidate to compete against a valid forward match,
    # and never let a partial/shifted sub-match override an exact shift == 0 head match.
    for nums, meta in prepared:
        cand = nums
        min_tail = 3 if len(cand) <= 12 else 4
        max_shift = min(16, max(0, len(cand) - min_tail))
        is_son500_grid = bool(meta.get("son500Grid"))

        for shift in range(max_shift + 1):
            max_cmp = min(len(current), len(cand) - shift, 20)
            overlap = 0
            for i in range(max_cmp):
                if cand[shift + i] != current[i]:
                    break
                overlap += 1

            if shift == 0:
                req_ov = min(5, len(cand), len(current))
            elif len(cand) <= 12:
                req_ov = 3 if (len(cand) - shift) == 3 else min(4, len(current))
            else:
                req_ov = min(5, max(4, len(cand) - shift), len(current))

            if overlap < req_ov:
                continue

            # For shift > 0, require the entire comparable tail of cand to match
            # current[:max_cmp] (unless cand is >=20 and matched >=10 spins), so a
            # wrapper that appends hot/cold/stat numbers after the 10-number bar is rejected.
            if shift > 0 and overlap < max_cmp and overlap < 10:
                continue

            full_tail = 1 if (overlap == max_cmp or (shift == 0 and is_son500_grid and overlap >= 8)) else 0
            eff_overlap = max_cmp if (shift == 0 and is_son500_grid and overlap >= 8) else overlap
            relation = "ahead" if shift > 0 else "same"

            score = (
                full_tail,
                eff_overlap,
                -shift,
                1 if is_son500_grid else 0,
                len(cand),
            )

            row = {
                "nums": cand,
                "meta": meta,
                "relation": relation,
                "new_count": shift,
                "overlap": overlap,
                "orientation": "forward",
                "_score": score,
            }

            if best is None or row["_score"] > best["_score"]:
                best = row

            if shift == 0 and (full_tail == 1 or overlap >= min(8, len(cand), len(current))):
                break

    # Pass 2: if no forward match exists, check if current[:10] was previously
    # corrupted by a reversed block (e.g. reversed(current[:10]) appears inside cand).
    if best is None and len(current) >= 8:
        rev_cur = list(reversed(current[:10]))
        rev_grams = {
            tuple(rev_cur[i:i + 5])
            for i in range(len(rev_cur) - 4)
        }
        for nums, meta in prepared:
            if len(nums) >= 8:
                cand_grams = {
                    tuple(nums[i:i + 5])
                    for i in range(len(nums) - 4)
                }
                if rev_grams & cand_grams:
                    return {
                        "nums": nums,
                        "meta": meta,
                        "relation": "resync",
                        "new_count": 0,
                        "overlap": 5,
                        "orientation": "forward",
                    }

    if best is None:
        return None

    best.pop("_score", None)
    return best



def align_reference_to_live(current_history, reference_history, max_new=25):
    """
    Strictly align a reference history (e.g. SON500) to current live history.

    Returns only when the reference PROVES continuity:
      reference = [new..., current_head...]
    """
    current = [
        int(x) for x in (current_history or [])
        if isinstance(x, int) and 0 <= x <= 36
    ][:20]
    ref = [
        int(x) for x in (reference_history or [])
        if isinstance(x, int) and 0 <= x <= 36
    ]

    if len(current) < 4 or len(ref) < 20 or is_betting_grid_artifact(ref):
        return None

    best = None
    cand = ref
    limit = min(max_new, max(0, len(cand) - 4))

    for shift in range(0, limit + 1):
        overlap = min(
            len(current),
            len(cand) - shift,
            20,
        )

        if overlap < 5:
            continue

        # Require exact contiguous head continuity.
        if cand[shift:shift + overlap] != current[:overlap]:
            continue

        score = (
            overlap,
            -shift,
        )

        row = {
            "orientation": "forward",
            "reference": cand,
            "new_count": shift,
            "new_items": cand[:shift],
            "overlap": overlap,
            "_score": score,
        }

        if best is None or row["_score"] > best["_score"]:
            best = row
        if shift == 0:
            break

    if best is None:
        return None

    best.pop("_score", None)
    return best


def detect_new_front(old_history, new_history, max_new=16):
    """
    last20Results is newest-first. Detect how many new results were prepended.
    Returns newest-first new items.
    """
    old = list(old_history or [])
    new = list(new_history or [])
    if not old or not new or old == new:
        return []

    ov0 = min(len(old), len(new))
    if ov0 >= 3 and new[:ov0] == old[:ov0]:
        return []

    max_k = min(max_new, len(new))
    for k in range(1, max_k + 1):
        overlap = min(len(new) - k, len(old))
        req_ov = 3 if (len(new) <= 12 and (len(new) - k) == 3 and len(old) >= 3) else 4
        if overlap >= req_ov and new[k:k+overlap] == old[:overlap]:
            return new[:k]
    return []


def region_of_number(n):
    for name, nums in REGIONS.items():
        if n in nums:
            return name
    return None


def region_prediction(history):
    """
    MODEL REGION SCORE (not true roulette probability).

    Uses:
    1) recency-weighted region density
    2) sector-size normalization
    3) number + wheel-neighbor watch-score density
    4) last-5 momentum
    5) top-number neighbor concentration

    Output scores sum to 100%.
    """
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36][:20]
    if not hist:
        return None, 0.0, {name: 0.0 for name in REGIONS}, {}

    watch = tracking_scores(hist)
    top_n, _ = model_confidence(hist)
    region_features = {}

    for name, nums in REGIONS.items():
        size = len(nums)
        baseline = size / 37.0

        recency_sum = 0.0
        total_recency = 0.0
        for idx, n in enumerate(hist):
            w = 1.0 / (1.0 + idx * 0.22)
            total_recency += w
            if n in nums:
                recency_sum += w

        observed_recency = recency_sum / max(1e-9, total_recency)
        recency_ratio = observed_recency / max(1e-9, baseline)

        watch_density = sum(watch.get(n, 0.0) for n in nums) / max(1, size)

        last5 = hist[:5]
        momentum_obs = sum(1 for n in last5 if n in nums) / max(1, len(last5))
        momentum_ratio = momentum_obs / max(1e-9, baseline)

        neighbor_overlap = 0.0
        if top_n is not None:
            neigh = wheel_neighbors(top_n, 2)
            neighbor_overlap = sum(1 for n in neigh if n in nums) / 5.0

        raw = (
            1.40 * recency_ratio +
            0.55 * watch_density +
            0.95 * momentum_ratio +
            0.90 * neighbor_overlap
        )

        region_features[name] = {
            "raw": raw,
            "recency_ratio": recency_ratio,
            "momentum_ratio": momentum_ratio,
            "watch_density": watch_density,
            "neighbor_overlap": neighbor_overlap,
        }

    temperature = 0.72
    vals = {
        name: math.exp(region_features[name]["raw"] / temperature)
        for name in REGIONS
    }
    denom = sum(vals.values()) or 1.0
    normalized = {name: vals[name] / denom * 100.0 for name in REGIONS}

    best = max(normalized, key=normalized.get)
    return best, normalized[best], normalized, region_features

def predicted_number_neighbors(history, radius=2):
    n, _ = model_confidence(history)
    return wheel_neighbors(n, radius) if n is not None else []


class RawWebSocket:
    def __init__(self, url, origin="", connect_timeout=5):
        self.url = url
        self.origin = str(origin or "")
        self.connect_timeout = float(connect_timeout or 5)
        self.sock = None
        self.lock = threading.Lock()
        self._connect()

    def _connect(self):
        u = urllib.parse.urlparse(self.url)
        host = u.hostname
        if not host:
            raise RuntimeError("WebSocket host boş")
        secure = (u.scheme or "ws").lower() == "wss"
        port = u.port or (443 if secure else 80)
        path = u.path or "/"
        if u.query:
            path += "?" + u.query

        raw = socket.create_connection((host, port), timeout=self.connect_timeout)
        raw.settimeout(None)
        if secure:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(raw, server_hostname=host)
        else:
            s = raw

        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        default_port = 443 if secure else 80
        host_header = host if port == default_port else f"{host}:{port}"
        headers = [
            f"GET {path} HTTP/1.1",
            f"Host: {host_header}",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Key: {key}",
            "Sec-WebSocket-Version: 13",
        ]
        if self.origin:
            headers.append(f"Origin: {self.origin}")
        req = ("\r\n".join(headers) + "\r\n\r\n").encode("ascii")
        s.sendall(req)

        response = b""
        while b"\r\n\r\n" not in response:
            chunk = s.recv(4096)
            if not chunk:
                raise RuntimeError("WebSocket bağlantısı açılamadı.")
            response += chunk
            if len(response) > 65536:
                raise RuntimeError("WebSocket handshake cevabı çok büyük")

        if b"101" not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError("WebSocket reddedildi.")

        self.sock = s

    def settimeout(self, seconds):
        try:
            self.sock.settimeout(seconds)
        except Exception:
            pass

    def _read_exact(self, n):
        data = bytearray()
        while len(data) < n:
            chunk = self.sock.recv(n-len(data))
            if not chunk:
                raise ConnectionError("WebSocket bağlantısı kapandı.")
            data.extend(chunk)
        return bytes(data)

    def _send_frame(self, opcode, payload=b""):
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        payload = bytes(payload or b"")
        with self.lock:
            mask = secrets.token_bytes(4)
            n = len(payload)
            if n < 126:
                hdr = bytes([0x80 | (opcode & 0x0F), 0x80 | n])
            elif n < 65536:
                hdr = bytes([0x80 | (opcode & 0x0F), 0x80 | 126]) + struct.pack("!H", n)
            else:
                hdr = bytes([0x80 | (opcode & 0x0F), 0x80 | 127]) + struct.pack("!Q", n)
            if n:
                rep_mask = (mask * ((n // 4) + 1))[:n]
                masked = (
                    int.from_bytes(payload, "big") ^ int.from_bytes(rep_mask, "big")
                ).to_bytes(n, "big")
            else:
                masked = b""
            self.sock.sendall(hdr + mask + masked)

    def send_text(self, text):
        self._send_frame(0x1, str(text or ""))

    def send_pong(self, payload=b""):
        self._send_frame(0xA, payload)

    def recv_text(self):
        fragments = bytearray()
        current_opcode = None
        while True:
            b1, b2 = self._read_exact(2)
            fin = bool(b1 & 0x80)
            opcode = b1 & 0x0F
            masked = bool(b2 & 0x80)
            n = b2 & 0x7F

            if n == 126:
                n = struct.unpack("!H", self._read_exact(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._read_exact(8))[0]

            mask = self._read_exact(4) if masked else None
            payload = self._read_exact(n) if n else b""
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))

            if opcode == 0x8:
                raise ConnectionError("WebSocket kapandı.")
            if opcode == 0x9:
                # Server ping; answer with pong so long-lived DGA feeds stay up.
                try:
                    self.send_pong(payload)
                except Exception:
                    pass
                continue
            if opcode == 0xA:
                continue

            if opcode in (0x1, 0x2):
                current_opcode = opcode
                fragments.extend(payload)
            elif opcode == 0x0:
                fragments.extend(payload)

            if fin:
                if current_opcode == 0x1:
                    return fragments.decode("utf-8", errors="replace")
                if current_opcode == 0x2:
                    return fragments.decode("utf-8", errors="ignore")
                fragments.clear()
                current_opcode = None

    def close(self):
        try:
            self._send_frame(0x8, b"")
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass




REGION_BASELINE = {
    "VOISINS DU ZÉRO": len(VOISINS) / 37.0 * 100.0,
    "TIERS DU CYLINDRE": len(TIERS) / 37.0 * 100.0,
    "ORPHELINS": len(ORPHELINS) / 37.0 * 100.0,
}


def learning_stage(trials):
    trials = int(trials or 0)
    if trials < 25:
        return "ANINDA TAHMİN • ÖN ÖĞRENME"
    if trials < 100:
        return "ADAPTİF ÖĞRENME"
    return "OLGUN MODEL"


def rolling_rates(history, limit=20):
    rows = list(history or [])[-limit:]
    n = len(rows)
    if n == 0:
        return {
            "trials": 0,
            "exact": 0.0,
            "side4": 0.0,
            "top5": 0.0,
            "neighbor5": 0.0,
            "region": 0.0,
        }

    return {
        "trials": n,
        "exact": sum(1 for r in rows if r.get("exact")) / n * 100.0,
        "side4": sum(1 for r in rows if r.get("side4")) / n * 100.0,
        "top5": sum(1 for r in rows if r.get("top5")) / n * 100.0,
        "neighbor5": sum(1 for r in rows if r.get("neighbor5")) / n * 100.0,
        "region": sum(1 for r in rows if r.get("region")) / n * 100.0,
    }


def calibrated_region_scores(raw_scores, trials, validation=None, recent=None):
    """
    Shrink aggressive region model scores toward actual wheel-sector baselines
    until enough out-of-sample validation exists.

    This is still a MODEL SCORE, not a true next-spin probability.
    """
    raw_scores = raw_scores or {}
    validation = validation or {}
    recent = recent or {}

    t = max(0, int(trials or 0))

    # Maturity: deliberately slow. 10 trials => only 8% model influence,
    # 50 => 40%, 150+ => full maturity.
    maturity = min(1.0, t / 125.0)

    total_region_rate = (
        float(validation.get("region", 0)) / max(1, int(validation.get("trials", 0))) * 100.0
        if validation.get("trials", 0)
        else 0.0
    )

    recent_region_rate = float(recent.get("region", 0.0))

    # If the region model has not shown useful validation yet, reduce influence.
    # 45.95% is the largest physical region baseline (Voisins).
    reference = REGION_BASELINE["VOISINS DU ZÉRO"]
    total_skill = min(1.15, max(0.35, total_region_rate / reference)) if t else 0.35

    if recent.get("trials", 0) >= 8:
        recent_skill = min(1.15, max(0.35, recent_region_rate / reference))
        skill = 0.65 * total_skill + 0.35 * recent_skill
    else:
        skill = total_skill

    alpha = min(0.90, maturity * skill)

    out = {}
    for name, baseline in REGION_BASELINE.items():
        raw = float(raw_scores.get(name, baseline))
        out[name] = baseline + alpha * (raw - baseline)

    # Safety cap: do not display extreme certainty as a model score.
    max_name = max(out, key=out.get)
    if out[max_name] > 85.0:
        excess = out[max_name] - 85.0
        out[max_name] = 85.0
        others = [k for k in out if k != max_name]
        denom = sum(out[k] for k in others) or 1.0
        for k in others:
            out[k] += excess * (out[k] / denom)

    total = sum(out.values()) or 1.0
    out = {k: v / total * 100.0 for k, v in out.items()}
    return out


def calibrated_signal(model_score, trials, validation=None, recent=None):
    """
    Calibrate the relative model signal against out-of-sample Top-5 and
    neighbour validation. Result is a conservative SIGNAL score, not odds.
    """
    validation = validation or {}
    recent = recent or {}
    t = max(0, int(trials or 0))

    base = 25.0
    raw = float(model_score or base)

    maturity = min(1.0, t / 120.0)

    # Random baseline for a 5-number set on European roulette.
    random5 = 5.0 / 37.0 * 100.0

    if validation.get("trials", 0):
        top5_rate = float(validation.get("top5", 0)) / max(1, int(validation["trials"])) * 100.0
        neigh_rate = float(validation.get("neighbor5", 0)) / max(1, int(validation["trials"])) * 100.0
        total_skill = ((top5_rate / random5) + (neigh_rate / random5)) / 2.0
    else:
        total_skill = 0.75

    if recent.get("trials", 0) >= 8:
        recent_skill = (
            (float(recent.get("top5", 0.0)) / random5)
            + (float(recent.get("neighbor5", 0.0)) / random5)
        ) / 2.0
        skill = 0.65 * total_skill + 0.35 * recent_skill
    else:
        skill = total_skill

    skill = min(1.25, max(0.35, skill))
    influence = min(1.0, maturity * skill)

    calibrated = base + (raw - base) * influence
    return max(1.0, min(90.0, calibrated))


def prediction_quality(signal, model_share, trials, validation=None, recent=None):
    signal = float(signal or 0.0)
    share = float(model_share or 0.0)
    trials = int(trials or 0)
    validation = validation or {}
    recent = recent or {}

    if trials < 20:
        return "ZAYIF"

    exact_base = 100.0 / 37.0
    top5_base = 5.0 / 37.0 * 100.0
    neigh_base = 5.0 / 37.0 * 100.0

    exact_rate = float(validation.get("exact", 0)) / max(1, trials) * 100.0
    top5_rate = float(validation.get("top5", 0)) / max(1, trials) * 100.0
    neigh_rate = float(validation.get("neighbor5", 0)) / max(1, trials) * 100.0

    r_trials = int(recent.get("trials", 0) or 0)
    recent_top5 = float(recent.get("top5", 0.0)) if r_trials else top5_rate
    recent_neigh = float(recent.get("neighbor5", 0.0)) if r_trials else neigh_rate

    if top5_rate < top5_base * 0.92 and neigh_rate < neigh_base * 0.92 and trials >= 35:
        return "ZAYIF"

    skill = (
        0.15 * min(1.4, exact_rate / exact_base)
        + 0.35 * min(1.4, top5_rate / top5_base)
        + 0.35 * min(1.4, neigh_rate / neigh_base)
        + 0.05 * min(1.3, recent_top5 / top5_base)
        + 0.05 * min(1.3, recent_neigh / neigh_base)
        + 0.05 * min(1.25, signal / 50.0)
    )

    if (
        trials >= 80
        and top5_rate >= top5_base
        and neigh_rate >= neigh_base
        and skill >= 1.00
        and share >= 5.5
    ):
        return "GÜÇLÜ"

    if (
        trials >= 40
        and (top5_rate >= top5_base * 0.96 or neigh_rate >= neigh_base)
        and skill >= 0.93
    ):
        return "ORTA"

    return "ZAYIF"


def _chi_square_number_deviation(history):
    """
    Pearson chi-square style descriptive deviation score for 0..36.
    This is NOT proof of cheating or manipulation.
    """
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36]
    n = len(hist)
    if n < 12:
        return {
            "n": n,
            "chi2": 0.0,
            "ratio": 0.0,
            "level": "VERİ AZ",
            "note": "erken örneklem",
        }

    counts = Counter(hist)
    expected = n / 37.0
    chi2 = 0.0
    for k in range(37):
        obs = counts.get(k, 0)
        chi2 += ((obs - expected) ** 2) / max(expected, 1e-9)

    # df=36. We intentionally avoid claiming a formal p-value here.
    # Ratio around 1 is roughly ordinary dispersion scale.
    ratio = chi2 / 36.0

    if n < 30:
        level = "ERKEN"
    elif ratio < 1.35:
        level = "NORMAL ARALIK"
    elif ratio < 1.75:
        level = "İZLE"
    else:
        level = "SAPMA YÜKSEK"

    return {
        "n": n,
        "chi2": chi2,
        "ratio": ratio,
        "level": level,
        "note": "dağılım sapma göstergesi",
    }


def _repeat_stats(history):
    """
    Back-to-back repeat rate vs European-roulette baseline 1/37.
    """
    seq = list(reversed([
        int(x) for x in history
        if isinstance(x, int) and 0 <= x <= 36
    ]))
    pairs = max(0, len(seq) - 1)
    if pairs <= 0:
        return {
            "pairs": 0,
            "repeats": 0,
            "rate": 0.0,
            "baseline": 100.0 / 37.0,
            "diff": 0.0,
        }

    repeats = sum(1 for a, b in zip(seq, seq[1:]) if a == b)
    rate = repeats / pairs * 100.0
    baseline = 100.0 / 37.0
    return {
        "pairs": pairs,
        "repeats": repeats,
        "rate": rate,
        "baseline": baseline,
        "diff": rate - baseline,
    }


def _sector_observed(history):
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36]
    n = len(hist)
    if not n:
        return {}

    out = {}
    for name, nums in REGIONS.items():
        hits = sum(1 for x in hist if x in nums)
        rate = hits / n * 100.0
        base = len(nums) / 37.0 * 100.0
        out[name] = {
            "hits": hits,
            "rate": rate,
            "baseline": base,
            "diff": rate - base,
        }
    return out


def fairness_snapshot(history):
    """
    Fast descriptive monitoring panel.
    Uses only observed spin history. It does not diagnose cheating.
    """
    hist = [
        int(x) for x in history
        if isinstance(x, int) and 0 <= x <= 36
    ]

    # Fast view uses up to latest 120 spins; useful from ~20 onward.
    h = hist[:120]
    n = len(h)
    dev = _chi_square_number_deviation(h)
    rep = _repeat_stats(h)
    sectors = _sector_observed(h)

    confidence = "ÇOK DÜŞÜK"
    if n >= 100:
        confidence = "ORTA"
    elif n >= 50:
        confidence = "DÜŞÜK-ORTA"
    elif n >= 25:
        confidence = "DÜŞÜK"

    # Simple descriptive alert logic, deliberately conservative.
    alerts = 0
    if n >= 30 and dev["ratio"] >= 1.75:
        alerts += 1
    if n >= 30 and abs(rep["diff"]) >= 5.0:
        alerts += 1
    if n >= 30 and sectors:
        if max(abs(v["diff"]) for v in sectors.values()) >= 12.0:
            alerts += 1

    if n < 20:
        status = "VERİ TOPLANIYOR"
    elif alerts == 0:
        status = "BELİRGİN SAPMA YOK"
    elif alerts == 1:
        status = "İZLE"
    else:
        status = "SAPMA SİNYALİ"

    return {
        "n": n,
        "status": status,
        "confidence": confidence,
        "deviation": dev,
        "repeat": rep,
        "sectors": sectors,
        "alerts": alerts,
    }



def safe_table_key(name):
    raw = str(name or "default").strip().lower()
    raw = re.sub(r"[^a-z0-9]+", "_", raw)
    raw = raw.strip("_") or "default"
    return raw[:64]


def table_storage_paths(data_dir, table_name):
    key = safe_table_key(table_name)
    return (
        os.path.join(data_dir, f"roulette_learning_{key}.json"),
        os.path.join(data_dir, f"roulette_prediction_log_{key}.jsonl"),
    )


def historical_transition_snapshot(history, session_results):
    """Descriptive successor counts from locally recorded spins."""
    hist = [int(x) for x in history if isinstance(x, int) and 0 <= x <= 36]
    seq = [int(x) for x in session_results if isinstance(x, int) and 0 <= x <= 36]
    if not hist or len(seq) < 2:
        return {"spins": len(seq), "exact_obs": 0, "exact_top": [], "pair_obs": 0, "pair_top": []}

    current = hist[0]
    exact = Counter()
    for a,b in zip(seq[:-1], seq[1:]):
        if a == current:
            exact[b] += 1

    pair = Counter()
    if len(hist) >= 2 and len(seq) >= 3:
        prev = hist[1]
        for a,b,c in zip(seq[:-2], seq[1:-1], seq[2:]):
            if a == prev and b == current:
                pair[c] += 1

    return {
        "spins": len(seq),
        "exact_obs": sum(exact.values()),
        "exact_top": exact.most_common(5),
        "pair_obs": sum(pair.values()),
        "pair_top": pair.most_common(5),
    }


def parse_history_file(path):
    """
    User archive format:
    - one roulette result per line OR comma/space separated
    - numbers must be 0..36
    - file order is OLDEST -> NEWEST
    Returns NEWEST -> OLDEST for the external-history model.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    # Only accept standalone 0..36 tokens.
    nums = []
    for token in re.findall(r'(?<!\d)(?:[0-9]|[12][0-9]|3[0-6])(?!\d)', raw):
        try:
            n = int(token)
            if 0 <= n <= 36:
                nums.append(n)
        except Exception:
            pass

    # Keep a generous archive but avoid unbounded RAM growth.
    return list(reversed(nums))


def discover_history_file(app_dir, table_name=""):
    name = str(table_name or "").lower()
    names = []

    # Keep histories separated by table. Never mix Mega and Auto/Roulette.
    if "mega" in name:
        names += [
            "gecmis_mega_roulette.txt",
            "gecmis_mega_roulette.csv",
        ]
    elif "auto" in name or "otomatik" in name:
        names += [
            "gecmis_auto_roulette.txt",
            "gecmis_auto_roulette.csv",
            "gecmis_roulette.txt",
            "gecmis_roulette.csv",
        ]
    elif "roulette" in name or "rulet" in name:
        names += [
            "gecmis_roulette.txt",
            "gecmis_roulette.csv",
            "gecmis_auto_roulette.txt",
            "gecmis_auto_roulette.csv",
        ]

    # Optional generic fallback for future tables.
    names += [
        "gecmis_rulet.txt",
        "gecmis_rulet.csv",
        "roulette_history.txt",
        "roulette_history.csv",
        "pragmatic_history.txt",
        "pragmatic_history.csv",
    ]

    seen = set()
    for fname in names:
        if fname in seen:
            continue
        seen.add(fname)
        p = os.path.join(app_dir, fname)
        if os.path.exists(p):
            return p
    return ""


def theoretical_coverage_text(region_name):
    region_size = len(REGIONS.get(region_name, []))
    region_pct = region_size / 37.0 * 100.0 if region_size else 0.0
    return {
        "single": 100.0 / 37.0,
        "top5": 5.0 / 37.0 * 100.0,
        "region": region_pct,
        "region_size": region_size,
        "need90": 34,  # 34/37 = 91.89%
    }



def wilson_lower_bound(hits, trials, z=1.2815515655446004):
    """One-sided ~90% lower confidence bound for a binomial hit rate."""
    n = max(0, int(trials or 0))
    h = max(0, min(n, int(hits or 0)))
    if n <= 0:
        return 0.0
    p = h / n
    z2 = z * z
    denom = 1.0 + z2 / n
    centre = p + z2 / (2.0 * n)
    margin = z * math.sqrt((p * (1.0 - p) + z2 / (4.0 * n)) / n)
    return max(0.0, (centre - margin) / denom)


WF_MODEL_NAMES = ("RECENCY", "WHEEL", "TRANSITION", "LONG")


def _wf_weights(stats):
    """Weights learned only from already-scored walk-forward predictions."""
    priors = {
        "RECENCY": 0.16,
        "WHEEL": 0.19,
        "TRANSITION": 0.31,
        "LONG": 0.34,
    }
    top5_base = 5.0 / 37.0
    exact_base = 1.0 / 37.0
    raw = {}

    for name in WF_MODEL_NAMES:
        st = (stats or {}).get(name, {})
        n = max(0, int(st.get("trials", 0) or 0))
        t5 = max(0, int(st.get("top5", 0) or 0))
        ex = max(0, int(st.get("exact", 0) or 0))

        # Strong shrinkage prevents lucky short runs from taking over.
        t5_sm = (t5 + top5_base * 45.0) / (n + 45.0)
        ex_sm = (ex + exact_base * 75.0) / (n + 75.0)
        t5_ratio = t5_sm / top5_base
        ex_ratio = ex_sm / exact_base
        skill = 0.86 * t5_ratio + 0.14 * ex_ratio
        skill = min(1.75, max(0.30, skill))

        maturity = min(1.0, n / 100.0)
        effective = (1.0 - maturity) + maturity * skill

        # A mature model below random Top-5 gets sharply reduced.
        if n >= 80 and (t5 / max(1, n)) < top5_base * 0.92:
            effective *= 0.52
        elif n >= 50 and (t5 / max(1, n)) < top5_base:
            effective *= 0.76

        raw[name] = priors[name] * (effective ** 1.75)

    total = sum(raw.values()) or 1.0
    w = {k: v / total for k, v in raw.items()}

    # Recovery floor + domination cap.
    floor, cap = 0.05, 0.52
    for _ in range(8):
        changed = False
        deficit = 0.0
        free = []
        for k in WF_MODEL_NAMES:
            if w[k] < floor:
                deficit += floor - w[k]
                w[k] = floor
                changed = True
            else:
                free.append(k)
        if deficit and free:
            pool = sum(w[k] for k in free) or 1.0
            for k in free:
                w[k] -= deficit * (w[k] / pool)

        excess = 0.0
        free = []
        for k in WF_MODEL_NAMES:
            if w[k] > cap:
                excess += w[k] - cap
                w[k] = cap
                changed = True
            else:
                free.append(k)
        if excess and free:
            pool = sum(w[k] for k in free) or 1.0
            for k in free:
                w[k] += excess * (w[k] / pool)
        if not changed:
            break

    total = sum(w.values()) or 1.0
    return {k: w[k] / total for k in WF_MODEL_NAMES}


def _wf_current_distributions(history, chronological_train, long_newest):
    return {
        "RECENCY": recency_expert(history),
        "WHEEL": wheel_expert(history),
        "TRANSITION": transition_expert(history, chronological_train),
        "LONG": external_web_expert(history, long_newest),
    }


_WF_PROFILE_CACHE = {}


def walk_forward_profile(long_newest, max_trials=220, min_train=120):
    """
    Chronological, no-peeking evaluation on the SAME tableId archive.
    Every tested prediction can only see spins that occurred before its actual.
    """
    clean_new = [
        int(x) for x in (long_newest or [])
        if isinstance(x, int) and 0 <= x <= 36
    ]
    if len(clean_new) < min_train + 25:
        return {
            "trials": 0,
            "exact": 0,
            "top5": 0,
            "exact_rate": 0.0,
            "top5_rate": 0.0,
            "top5_low90": 0.0,
            "top5_base": 5.0 / 37.0 * 100.0,
            "edge_pp": 0.0,
            "qualified": False,
            "status": "VERİ AZ",
            "weights": {name: 1.0 / len(WF_MODEL_NAMES) for name in WF_MODEL_NAMES},
            "experts": {},
        }

    wf_key = (
        len(clean_new),
        tuple(clean_new[:8]),
        tuple(clean_new[-8:]),
        int(max_trials),
        int(min_train),
    )
    cached_wf = _WF_PROFILE_CACHE.get(wf_key)
    if cached_wf is not None:
        return dict(cached_wf)

    # Bound compute cost while keeping the newest relevant same-table archive.
    seq = list(reversed(clean_new[:3000]))  # chronological
    start = max(min_train, len(seq) - max_trials)

    stats = {
        name: {"trials": 0, "exact": 0, "top5": 0}
        for name in WF_MODEL_NAMES
    }
    ensemble = {"trials": 0, "exact": 0, "top5": 0}

    pos_by_num = [[] for _ in range(37)]
    for k in range(start - 1):
        pos_by_num[seq[k]].append(k)
    freq = Counter(seq[max(0, start - 2000):start])

    for t in range(start, len(seq)):
        if t < min_train:
            continue
        if t > start:
            pos_by_num[seq[t - 2]].append(t - 2)
            freq[seq[t - 1]] += 1
            if t - 1 >= 2000:
                old_v = seq[t - 1 - 2000]
                freq[old_v] -= 1
                if freq[old_v] <= 0:
                    del freq[old_v]

        actual = int(seq[t])
        history = [seq[i] for i in range(t - 1, max(-1, t - 21), -1)]
        current = history[0]
        has2 = len(history) >= 2 and t >= 3
        prev = history[1] if has2 else -99
        has3 = len(history) >= 3 and t >= 4
        p2 = history[2] if has3 else -99

        t_scores = {n: 0.45 for n in range(37)}
        positions = pos_by_num[current]
        exact_obs_t = len(positions)
        for k in positions:
            b = seq[k + 1]
            age = (t - 2) - k
            rec = 1.0 / (1.0 + age / 180.0)
            t_scores[b] += 3.8 + 1.6 * rec
            ln, rn = _WHEEL_LR[b]
            t_scores[ln] += 0.28
            t_scores[rn] += 0.28
            if has2 and k >= 1 and seq[k - 1] == prev:
                rec2 = 1.0 / (1.0 + age / 220.0)
                t_scores[b] += 1.5 + 0.7 * rec2
                if has3 and k >= 2 and seq[k - 2] == p2:
                    rec3 = 1.0 / (1.0 + age / 260.0)
                    t_scores[b] += 1.8 + 0.8 * rec3
        if exact_obs_t < 4:
            for nb in set(wheel_neighbors(current, 2)):
                for k in pos_by_num[nb]:
                    b = seq[k + 1]
                    age = (t - 2) - k
                    rec = 1.0 / (1.0 + age / 150.0)
                    t_scores[b] += 0.16 + 0.18 * rec
        maxf = max(freq.values()) if freq else 1
        for n, c in freq.items():
            t_scores[n] += 0.30 * (c / maxf)
        trans_dist = normalize_probs(t_scores)

        w_scores = {n: 0.42 for n in range(37)}
        w_min = max(0, t - 2000)
        exact_obs_w = 0
        for k in positions:
            if k < w_min:
                continue
            b = seq[k + 1]
            w_scores[b] += 4.8
            ln, rn = _WHEEL_LR[b]
            w_scores[ln] += 0.26
            w_scores[rn] += 0.26
            exact_obs_w += 1
            if has2 and k >= w_min + 1 and seq[k - 1] == prev:
                w_scores[b] += 1.6
                if has3 and k >= w_min + 2 and seq[k - 2] == p2:
                    w_scores[b] += 1.8
        if exact_obs_w < 3:
            for nb in set(wheel_neighbors(current, 2)):
                for k in pos_by_num[nb]:
                    if k >= w_min:
                        w_scores[seq[k + 1]] += 0.55
        for idx in range(min(120, t - w_min)):
            w_scores[seq[t - 1 - idx]] += 0.30 / (1.0 + idx * 0.035)
        long_dist = normalize_probs(w_scores)

        dists = {
            "RECENCY": recency_expert(history),
            "WHEEL": wheel_expert(history),
            "TRANSITION": trans_dist,
            "LONG": long_dist,
        }

        # Ensemble weights use only earlier scored walk-forward trials.
        weights = _wf_weights(stats)
        mix = {n: 0.0 for n in range(37)}
        for name, dist in dists.items():
            for n in range(37):
                mix[n] += weights[name] * float(dist.get(n, 0.0))
        mix = normalize_probs(mix, floor=0.0)
        ens_top = _ranked_top(mix, 5)
        ensemble["trials"] += 1
        if actual == ens_top[0]:
            ensemble["exact"] += 1
        if actual in ens_top:
            ensemble["top5"] += 1

        # Score experts AFTER producing the ensemble prediction so this actual
        # never influences the weights used to predict itself.
        for name, dist in dists.items():
            top = _ranked_top(dist, 5)
            st = stats[name]
            st["trials"] += 1
            if actual == top[0]:
                st["exact"] += 1
            if actual in top:
                st["top5"] += 1

    n = int(ensemble["trials"])
    h5 = int(ensemble["top5"])
    ex = int(ensemble["exact"])
    base = 5.0 / 37.0
    t5_rate = h5 / n if n else 0.0
    exact_rate = ex / n if n else 0.0
    low90 = wilson_lower_bound(h5, n) if n else 0.0
    edge_pp = (t5_rate - base) * 100.0

    # Require both practical lift and a one-sided confidence bound above random.
    qualified = bool(
        n >= 120
        and t5_rate >= base + 0.015
        and low90 > base
    )

    expert_view = {}
    for name, st in stats.items():
        tn = int(st["trials"])
        expert_view[name] = {
            "trials": tn,
            "exact": int(st["exact"]),
            "top5": int(st["top5"]),
            "exact_rate": (st["exact"] / tn * 100.0) if tn else 0.0,
            "top5_rate": (st["top5"] / tn * 100.0) if tn else 0.0,
        }

    res_wf = {
        "trials": n,
        "exact": ex,
        "top5": h5,
        "exact_rate": exact_rate * 100.0,
        "top5_rate": t5_rate * 100.0,
        "top5_low90": low90 * 100.0,
        "top5_base": base * 100.0,
        "edge_pp": edge_pp,
        "qualified": qualified,
        "status": "EDGE VAR" if qualified else "EDGE YOK",
        "weights": _wf_weights(stats),
        "experts": expert_view,
    }
    if len(_WF_PROFILE_CACHE) > 24:
        _WF_PROFILE_CACHE.clear()
    _WF_PROFILE_CACHE[wf_key] = dict(res_wf)
    return res_wf


def apply_walk_forward_model(pred, history, session_results, table_long_newest, profile):
    """Re-rank current candidates using only weights earned out-of-sample."""
    profile = profile or {}
    trials = int(profile.get("trials", 0) or 0)
    if trials < 40 or len(table_long_newest or []) < 80:
        pred["walkforward"] = profile
        return pred

    chronological = list(reversed([
        int(x) for x in (table_long_newest or [])[:3000]
        if isinstance(x, int) and 0 <= x <= 36
    ]))
    if not chronological:
        pred["walkforward"] = profile
        return pred

    dists = _wf_current_distributions(
        history,
        chronological,
        list(reversed(chronological[-2000:])),
    )
    weights = profile.get("weights") or _wf_weights({})

    wf_dist = {n: 0.0 for n in range(37)}
    for name in WF_MODEL_NAMES:
        dist = dists[name]
        w = float(weights.get(name, 0.0) or 0.0)
        for n in range(37):
            wf_dist[n] += w * float(dist.get(n, 0.0))
    wf_dist = normalize_probs(wf_dist, floor=0.0)

    # If walk-forward has a proven edge, let it dominate; otherwise it only
    # de-noises the existing ranking while the action gate remains PAS.
    alpha = 0.72 if profile.get("qualified") else 0.48
    base = pred.get("combined") or {n: 1.0 / 37.0 for n in range(37)}
    merged = {
        n: (1.0 - alpha) * float(base.get(n, 0.0))
           + alpha * float(wf_dist.get(n, 0.0))
        for n in range(37)
    }
    merged = normalize_probs(merged, floor=0.0)

    ordered = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    best_n, best_p = ordered[0]
    second_p = ordered[1][1]
    uniform = 1.0 / 37.0
    lift = max(0.0, (best_p - uniform) / uniform)
    margin = max(0.0, best_p - second_p)

    pred["combined"] = merged
    pred["predicted"] = best_n
    pred["top5"] = [n for n, _p in ordered[:5]]
    pred["model_share"] = best_p * 100.0
    pred["model_score"] = max(
        1.0,
        min(
            99.0,
            20.0
            + 22.0 * min(1.0, lift / 1.3)
            + 50.0 * min(1.0, margin / 0.025)
            + (6.0 if profile.get("qualified") else 0.0),
        ),
    )
    pred["walkforward"] = profile
    return pred


def pro_master_decision(
    validation,
    recent20,
    quality,
    signal,
    region_name,
    region_conf,
    source_consensus=None,
    predicted=None,
    walkforward=None,
):
    validation = validation or {}
    recent20 = recent20 or {}
    sc = source_consensus or {}
    wf = walkforward or {}

    trials = int(validation.get("trials", 0) or 0)
    exact = int(validation.get("exact", 0) or 0)
    top5 = int(validation.get("top5", 0) or 0)
    neigh = int(validation.get("neighbor5", 0) or 0)
    region = int(validation.get("region", 0) or 0)

    top5_base = 5.0 / 37.0 * 100.0
    exact_base = 1.0 / 37.0 * 100.0

    if trials:
        exact_rate = exact / trials * 100.0
        top5_rate = top5 / trials * 100.0
        neigh_rate = neigh / trials * 100.0
        region_rate = region / trials * 100.0
    else:
        exact_rate = top5_rate = neigh_rate = region_rate = 0.0

    recent_trials = int(recent20.get("trials", 0) or 0)
    recent_top5 = float(recent20.get("top5", 0.0) or 0.0)
    supporters = (sc.get("agreement") or {}).get(predicted, []) if predicted is not None else []
    support = float((sc.get("support_weight") or {}).get(predicted, 0.0) or 0.0)
    source_count = len(supporters)

    wf_trials = int(wf.get("trials", 0) or 0)
    wf_rate = float(wf.get("top5_rate", 0.0) or 0.0)
    wf_low = float(wf.get("top5_low90", 0.0) or 0.0)
    wf_edge = float(wf.get("edge_pp", 0.0) or 0.0)
    wf_ok = bool(wf.get("qualified", False))

    # The model may still display test candidates, but it is not allowed to
    # suggest a bet unless same-table out-of-sample performance earns it.
    if wf_trials < 80:
        action = "İZLE"
        reason = f"walk-forward az ({wf_trials} tur)"
    elif not wf_ok:
        action = "PAS"
        reason = (
            f"model avantaj göstermiyor • WF Top5 %{wf_rate:.1f} "
            f"(taban %{top5_base:.1f}, edge {wf_edge:+.1f}p)"
        )
    elif trials >= 40 and top5_rate < top5_base * 0.92:
        action = "PAS"
        reason = "canlı Top5 performansı tabanın altında"
    elif recent_trials >= 20 and recent_top5 < top5_base * 0.85:
        action = "PAS"
        reason = "son 20 performansı zayıf"
    elif (
        trials >= 80
        and top5_rate >= top5_base
        and recent_top5 >= top5_base
        and source_count >= 2
        and support >= 0.35
        and float(signal or 0.0) >= 40.0
        and wf_low > top5_base
    ):
        action = "OYNA"
        reason = "WF edge + canlı Top5 + kaynak uzlaşması"
    else:
        action = "TEMKİNLİ"
        reason = "WF edge var; canlı doğrulama henüz sınırlı"

    return {
        "action": action,
        "reason": reason,
        "trials": trials,
        "exact_rate": exact_rate,
        "top5_rate": top5_rate,
        "neighbor_rate": neigh_rate,
        "region_rate": region_rate,
        "exact_base": exact_base,
        "top5_base": top5_base,
        "source_count": source_count,
        "source_support": support,
        "region_name": region_name,
        "region_conf": float(region_conf or 0.0),
        "wf_trials": wf_trials,
        "wf_top5_rate": wf_rate,
        "wf_top5_low90": wf_low,
        "wf_edge_pp": wf_edge,
        "wf_qualified": wf_ok,
    }



SOURCE_NAMES = ("LOCAL", "TABLE500", "TABLE_LONG", "ARCHIVE", "WEB")


def _ranked_top(dist, k=5):
    ordered = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))
    return [n for n, _p in ordered[:k]]


def source_predictions(history, session_results, table500, table_long, archive, public_web):
    """
    Keep each historical source separate. Agreement is evidence of model
    consensus only; it is not an independent-probability multiplication.
    """
    sources = {}

    if session_results and len(session_results) >= 3:
        sources["LOCAL"] = transition_expert(history, session_results)

    if table500 and len(table500) >= 20:
        sources["TABLE500"] = external_web_expert(history, table500)

    if table_long and len(table_long) >= 50:
        sources["TABLE_LONG"] = external_web_expert(history, table_long)

    archive_spins = sum(
        1 for x in (archive or [])
        if isinstance(x, int) and 0 <= x <= 36
    )
    if archive_spins >= 20:
        sources["ARCHIVE"] = multi_table_transition_expert(history, archive)

    if public_web and len(public_web) >= 20:
        sources["WEB"] = external_web_expert(history, public_web)

    return sources


def adaptive_source_weights(source_hits, active_sources):
    """Performance-weighted CANLI / SON500 / ARŞİV / WEB allocation."""
    priors = {
        "ARCHIVE": 0.46,
        "TABLE500": 0.19,
        "TABLE_LONG": 0.19,
        "LOCAL": 0.11,
        "WEB": 0.05,
    }
    top5_base = 5.0 / 37.0
    exact_base = 1.0 / 37.0

    raw = {}
    detail = {}
    for name in active_sources:
        st = (source_hits or {}).get(name, {})
        n = max(0, int(st.get("trials", 0) or 0))
        top5 = max(0, int(st.get("top5", 0) or 0))
        exact = max(0, int(st.get("exact", 0) or 0))

        # Shrink small samples toward roulette baselines.
        top5_rate_sm = (top5 + top5_base * 35.0) / (n + 35.0)
        exact_rate_sm = (exact + exact_base * 60.0) / (n + 60.0)
        top5_ratio = top5_rate_sm / top5_base
        exact_ratio = exact_rate_sm / exact_base

        # Top-5 matters most because the screen actually shows five candidates.
        skill = 0.80 * top5_ratio + 0.20 * exact_ratio
        skill = min(1.70, max(0.45, skill))

        maturity = min(1.0, n / 80.0)
        effective = (1.0 - maturity) + maturity * skill

        # Once sample size is useful, punish a source clearly below baseline.
        if n >= 50 and (top5 / max(1, n)) < top5_base * 0.85:
            effective *= 0.80

        raw[name] = priors.get(name, 0.10) * (effective ** 1.55)
        detail[name] = {
            "trials": n,
            "top5_rate": (top5 / n * 100.0) if n else 0.0,
            "exact_rate": (exact / n * 100.0) if n else 0.0,
            "skill": skill,
        }

    if not raw:
        return {}, detail

    total = sum(raw.values()) or 1.0
    w = {k: v / total for k, v in raw.items()}

    # Never let one source permanently disappear, while allowing ARCHIVE (ORTAK HAVUZ)
    # to hold decisive weight.
    floor, cap = 0.06, 0.64
    for _ in range(8):
        changed = False
        deficit = 0.0
        free = []
        for k in list(w):
            if w[k] < floor:
                deficit += floor - w[k]
                w[k] = floor
                changed = True
            else:
                free.append(k)
        if deficit and free:
            pool = sum(w[k] for k in free) or 1.0
            for k in free:
                w[k] -= deficit * (w[k] / pool)

        excess = 0.0
        free = []
        for k in list(w):
            if w[k] > cap:
                excess += w[k] - cap
                w[k] = cap
                changed = True
            else:
                free.append(k)
        if excess and free:
            pool = sum(w[k] for k in free) or 1.0
            for k in free:
                w[k] += excess * (w[k] / pool)

        if not changed:
            break

    total = sum(w.values()) or 1.0
    return {k: v / total for k, v in w.items()}, detail


def source_consensus(
    history,
    session_results,
    table500,
    table_long,
    archive,
    public_web,
    source_hits=None,
):
    sources = source_predictions(
        history,
        session_results,
        table500,
        table_long,
        archive,
        public_web,
    )

    active = list(sources)
    if not active:
        uniform = {n: 1.0 / 37.0 for n in range(37)}
        return {
            "distribution": uniform,
            "sources": {},
            "top5": [0,1,2,3,4],
            "agreement": {},
            "support_weight": {},
            "active": 0,
            "source_weights": {},
            "source_performance": {},
        }

    source_weight, perf = adaptive_source_weights(source_hits or {}, active)
    total_w = sum(source_weight.get(name, 0.0) for name in active) or 1.0

    dist = {n: 0.0 for n in range(37)}
    details = {}
    for name in active:
        d = sources[name]
        w = source_weight.get(name, 0.0) / total_w
        for n in range(37):
            dist[n] += w * d[n]

        top5 = _ranked_top(d, 5)
        details[name] = {
            "top1": top5[0],
            "top5": top5,
            "dist": dict(d),
            "weight": w,
            "top5_rate": perf.get(name, {}).get("top5_rate", 0.0),
            "exact_rate": perf.get(name, {}).get("exact_rate", 0.0),
        }

    total = sum(dist.values()) or 1.0
    dist = {n: dist[n] / total for n in range(37)}

    agreement = {}
    support_weight = {}
    for n in range(37):
        names = [name for name, d in details.items() if n in d["top5"]]
        if names:
            agreement[n] = names
            support_weight[n] = sum(details[name]["weight"] for name in names)
        else:
            support_weight[n] = 0.0

    # Consensus-first ranking. Better-performing agreeing sources count more.
    boosted = {}
    for n in range(37):
        count = len(agreement.get(n, []))
        support = support_weight.get(n, 0.0)
        boost = 1.0 + 0.38 * support + (0.10 if count >= 3 else 0.0)
        boosted[n] = dist[n] * boost

    total_b = sum(boosted.values()) or 1.0
    boosted = {n: boosted[n] / total_b for n in range(37)}
    top5 = _ranked_top(boosted, 5)

    return {
        "distribution": boosted,
        "sources": details,
        "top5": top5,
        "agreement": agreement,
        "support_weight": support_weight,
        "active": len(active),
        "source_weights": source_weight,
        "source_performance": perf,
    }


def blend_with_consensus(pred, consensus, strength=0.36):
    """
    Blend the existing adaptive model with independently-computed source
    consensus. Re-rank all displayed candidates after the blend.
    """
    if not consensus or consensus.get("active", 0) < 2:
        pred["source_consensus"] = consensus or {}
        return pred

    base = pred["combined"]
    cdist = consensus["distribution"]

    # More sources -> slightly more consensus influence, capped conservatively.
    active = int(consensus.get("active", 0))
    alpha = min(0.46, float(strength) + max(0, active - 2) * 0.03)

    merged = {
        n: (1.0 - alpha) * float(base.get(n, 0.0))
           + alpha * float(cdist.get(n, 0.0))
        for n in range(37)
    }
    total = sum(merged.values()) or 1.0
    merged = {n: merged[n] / total for n in range(37)}

    ordered = sorted(merged.items(), key=lambda kv: (-kv[1], kv[0]))
    best_n, best_p = ordered[0]
    second_p = ordered[1][1]
    top5 = [n for n, _p in ordered[:5]]

    uniform = 1.0 / 37.0
    lift = max(0.0, (best_p - uniform) / uniform)
    margin = max(0.0, best_p - second_p)
    model_score = (
        22.0
        + 23.0 * min(1.0, lift / 1.3)
        + 55.0 * min(1.0, margin / 0.025)
    )
    model_score = max(1.0, min(99.0, model_score))

    pred["combined"] = merged
    pred["predicted"] = best_n
    pred["top5"] = top5
    pred["model_share"] = best_p * 100.0
    pred["model_score"] = model_score
    pred["source_consensus"] = consensus
    return pred




def _bayes_exact_rate(exact, trials, prior_strength):
    baseline = 1.0 / 37.0
    n = max(0, int(trials or 0))
    e = max(0, int(exact or 0))
    prior = max(1.0, float(prior_strength))
    return (e + baseline * prior) / (n + prior)


def _source_alltime_stat(key, source_hits, expert_hits):
    if key.startswith("MODEL_"):
        exp = key.replace("MODEL_", "", 1)
        if exp == "LONG":
            exp = "WEB"
        return dict((expert_hits or {}).get(exp, {}) or {})
    return dict((source_hits or {}).get(key, {}) or {})



def exact_drift_gate(profile):
    """
    Lightweight exact-only drift gate.

    It never creates a new prediction source. It only limits the influence of
    a source whose latest exact-number record deteriorates versus its own
    longer record. Gating starts only after a useful recent sample exists.
    """
    pr = profile or {}
    baseline = 1.0 / 37.0
    n100 = int(pr.get("n100", 0) or 0)
    n300 = int(pr.get("n300", 0) or 0)
    nall = int(pr.get("nall", 0) or 0)
    r100 = float(pr.get("r100", baseline) or baseline)
    r300 = float(pr.get("r300", baseline) or baseline)
    rall = float(pr.get("rall", baseline) or baseline)

    recent_ratio = r100 / baseline
    long_parts = []
    if n300 >= 80:
        long_parts.append((0.65, r300 / baseline))
    if nall >= 150:
        long_parts.append((0.35, rall / baseline))
    if long_parts:
        den = sum(w for w,_ in long_parts) or 1.0
        long_ratio = sum(w*x for w,x in long_parts) / den
    else:
        long_ratio = 1.0

    drift = recent_ratio - long_ratio
    gate = 1.0
    state = "STABİL"

    # Do not react to tiny samples. Exact hits are sparse by nature.
    e100 = int(pr.get("e100", 0) or 0)
    raw100_ratio = ((e100 / n100) / baseline) if n100 > 0 else 1.0
    if n100 >= 45:
        if (e100 == 0 and n100 >= 55) or (recent_ratio < 0.72 and drift < -0.15):
            gate = 0.58
            state = "ZAYIFLIYOR"
        elif recent_ratio < 0.92 and (drift < -0.08 or raw100_ratio < 0.65):
            gate = 0.80
            state = "TEMKİNLİ"
        elif n100 >= 60 and (raw100_ratio >= 1.75 or (recent_ratio > 1.25 and drift > 0.06)):
            gate = min(1.28, 1.08 + 0.08 * min(2.5, max(0.0, raw100_ratio - 1.5)))
            state = "GÜÇLÜ"

    return {
        "gate": float(gate),
        "state": state,
        "recent_ratio": float(recent_ratio),
        "long_ratio": float(long_ratio),
        "drift": float(drift),
    }


def locked_live_summary(rows, limit=None):
    """Out-of-sample summary for predictions captured before each result."""
    seq = [r for r in (rows or []) if isinstance(r, dict)]
    if limit:
        seq = seq[-int(limit):]
    n = len(seq)
    if not n:
        return {
            "trials":0,"exact":0,"top5":0,"k1":0,"k2":0,
            "exact_rate":0.0,"top5_rate":0.0,
            "k1_rate":0.0,"k2_rate":0.0,
            "k1_base":0.0,"k2_base":0.0,
            "k1_edge":0.0,"k2_edge":0.0,
        }
    exact=sum(1 for r in seq if r.get("exact"))
    top5=sum(1 for r in seq if r.get("top5"))
    k1=sum(1 for r in seq if r.get("k1"))
    k2=sum(1 for r in seq if r.get("k2"))
    expected1=sum(float(r.get("cov1",0) or 0)/37.0 for r in seq)
    expected2=sum(float(r.get("cov2",0) or 0)/37.0 for r in seq)
    k1_rate=k1/n*100.0
    k2_rate=k2/n*100.0
    k1_base=expected1/n*100.0
    k2_base=expected2/n*100.0
    return {
        "trials":n,"exact":exact,"top5":top5,"k1":k1,"k2":k2,
        "exact_rate":exact/n*100.0,
        "top5_rate":top5/n*100.0,
        "k1_rate":k1_rate,"k2_rate":k2_rate,
        "k1_base":k1_base,"k2_base":k2_base,
        "k1_edge":k1_rate-k1_base,
        "k2_edge":k2_rate-k2_base,
    }


def locked_live_profiles(locked):
    rows=list((locked or {}).get("rows") or [])
    return {
        "all":locked_live_summary(rows),
        "50":locked_live_summary(rows,50),
        "100":locked_live_summary(rows,100),
        "200":locked_live_summary(rows,200),
    }


def straight_up_risk_profile(label, hits=0, trials=0, coverage=1.0, coverage_sum=None):
    """
    Straight-up roulette risk view for equal 1-unit bets on covered numbers.

    It separates model hit performance from unavoidable European roulette
    payout math. A hit on any covered number returns net profit (36-coverage)
    units for that round; a miss loses coverage units. Therefore the break-even
    hit rate is coverage/36, while random European roulette hit rate is
    coverage/37.
    """
    n = max(0, int(trials or 0))
    h = max(0, int(hits or 0))

    if coverage_sum is None:
        cov_sum = max(0.0, float(coverage or 0.0)) * n
        avg_cov = max(0.0, float(coverage or 0.0))
    else:
        cov_sum = max(0.0, float(coverage_sum or 0.0))
        avg_cov = (cov_sum / n) if n else max(0.0, float(coverage or 0.0))

    random_hit = (avg_cov / 37.0 * 100.0) if avg_cov else 0.0
    breakeven = (avg_cov / 36.0 * 100.0) if avg_cov else 0.0
    required_edge = breakeven - random_hit
    random_ev_round = -avg_cov / 37.0 if avg_cov else 0.0
    random_roi = -100.0 / 37.0 if avg_cov else 0.0

    if n and cov_sum > 0.0:
        hit_rate = h / n * 100.0
        profit_units = h * 36.0 - cov_sum
        roi = profit_units / cov_sum * 100.0
        low90 = wilson_lower_bound(h, n) * 100.0

        if avg_cov > 36.0:
            status = "BAŞABAŞ İMKANSIZ"
        elif low90 >= breakeven and n >= 40:
            status = "KANITLI ARTI"
        elif hit_rate >= breakeven:
            status = "ARTI AMA ERKEN"
        elif hit_rate < random_hit:
            status = "TABAN ALTI"
        else:
            status = "BAŞABAŞ ALTI"
    else:
        hit_rate = 0.0
        profit_units = 0.0
        roi = 0.0
        low90 = 0.0
        status = "VERİ BEKLİYOR"

    return {
        "label": str(label),
        "trials": n,
        "hits": h,
        "avg_coverage": float(avg_cov),
        "coverage_sum": float(cov_sum),
        "random_hit_pct": float(random_hit),
        "breakeven_hit_pct": float(breakeven),
        "required_edge_pp": float(required_edge),
        "random_ev_units_per_round": float(random_ev_round),
        "random_roi_pct": float(random_roi),
        "hit_rate_pct": float(hit_rate),
        "profit_units": float(profit_units),
        "roi_pct": float(roi),
        "wilson_low90_pct": float(low90),
        "status": status,
    }


def risk_analysis_snapshot(validation, neighbor1_total=None, neighbor2_total=None):
    """Current model/risk metrics for the visible straight-up plans."""
    validation = validation or {}
    n = int(validation.get("trials", 0) or 0)

    def nb_profile(label, total):
        total = total or {}
        tn = int(total.get("trials", 0) or 0)
        hits = int(total.get("any_hits", 0) or 0)
        cov_sum = float(total.get("coverage_sum", 0.0) or 0.0)
        avg_cov = (cov_sum / tn) if tn else 0.0
        return straight_up_risk_profile(
            label,
            hits=hits,
            trials=tn,
            coverage=avg_cov,
            coverage_sum=cov_sum,
        )

    return {
        "note": "35:1 düz sayı matematiği; garanti/gerçek olasılık değildir.",
        "net": straight_up_risk_profile(
            "NET",
            hits=int(validation.get("exact", 0) or 0),
            trials=n,
            coverage=1.0,
        ),
        "top5": straight_up_risk_profile(
            "NET+YEDEK TOP5",
            hits=int(validation.get("top5", 0) or 0),
            trials=n,
            coverage=5.0,
        ),
        "k1": nb_profile("K1 PAKET", neighbor1_total),
        "k2": nb_profile("K2 PAKET", neighbor2_total),
    }


def exact_window_profiles(validation_history, source_hits=None, expert_hits=None):
    """
    Exact-number performance only:
      R100 = latest 100 source-scored rounds
      R300 = latest 300 source-scored rounds
      ALL  = persistent all-time counter
    """
    source_hits = source_hits or {}
    expert_hits = expert_hits or {}
    rows = [
        r for r in (validation_history or [])
        if isinstance(r, dict) and isinstance(r.get("source_round"), dict)
    ]

    keys = (
        "LOCAL", "TABLE500", "TABLE_LONG", "ARCHIVE",
        "MODEL_RECENCY", "MODEL_WHEEL",
        "MODEL_TRANSITION", "MODEL_WEB",
    )
    out = {}

    for key in keys:
        seq = []
        for row in rows:
            sd = (row.get("source_round") or {}).get(key)
            if isinstance(sd, dict):
                seq.append(1 if str(sd.get("result","")) == "TAM" else 0)

        x100 = seq[-100:]
        x300 = seq[-300:]
        e100, n100 = sum(x100), len(x100)
        e300, n300 = sum(x300), len(x300)

        all_st = _source_alltime_stat(key, source_hits, expert_hits)
        nall = max(0, int(all_st.get("trials",0) or 0))
        eall = max(0, int(all_st.get("exact",0) or 0))

        baseline = 1.0 / 37.0
        r100 = _bayes_exact_rate(e100, n100, 45.0)
        r300 = _bayes_exact_rate(e300, n300, 90.0)
        rall = _bayes_exact_rate(eall, nall, 140.0)

        w100 = 0.52 * min(1.0, n100 / 80.0)
        w300 = 0.30 * min(1.0, n300 / 220.0)
        wall = 0.18 * min(1.0, nall / 350.0)
        wsum = w100 + w300 + wall

        if wsum > 1e-9:
            ratio = (
                w100 * (r100 / baseline)
                + w300 * (r300 / baseline)
                + wall * (rall / baseline)
            ) / wsum
        else:
            ratio = 1.0

        base_profile = {
            "n100": n100, "e100": e100, "r100": r100,
            "n300": n300, "e300": e300, "r300": r300,
            "nall": nall, "eall": eall, "rall": rall,
            "skill": min(1.55, max(0.62, ratio)),
        }
        gate_info = exact_drift_gate(base_profile)
        base_profile.update(gate_info)
        base_profile["effective_skill"] = min(
            1.55,
            max(0.50, float(base_profile["skill"]) * float(gate_info["gate"])),
        )
        out[key] = base_profile

    return out


def _member_rank_scores(top5, dist=None):
    # Preserve strong #2-#5 transition candidates (e.g. tied 17x or close 16x/15x
    # numbers in ORTAK HAVUZ / TABLO) by blending smooth rank weights with actual
    # probability lift above baseline 1/37.
    bonus = (1.00, 0.76, 0.58, 0.44, 0.32)
    out = {n: 0.0 for n in range(37)}
    clean_top5 = []
    for pos, raw in enumerate((top5 or [])[:5]):
        try:
            n = int(raw)
        except Exception:
            continue
        if 0 <= n <= 36:
            out[n] += bonus[pos]
            clean_top5.append((pos, n))

    if isinstance(dist, dict) and dist:
        base_p = 1.0 / 37.0
        peak_p = max((float(dist.get(n, 0.0) or 0.0) for n in range(37)), default=0.0)
        span = peak_p - base_p
        if span > 1e-6:
            for pos, n in clean_top5:
                p_n = float(dist.get(n, 0.0) or 0.0)
                lift = max(0.0, min(1.0, (p_n - base_p) / span))
                out[n] = 0.52 * bonus[pos] + 0.48 * lift
            ordered_d = sorted(
                range(37),
                key=lambda k: (-float(dist.get(k, 0.0) or 0.0), k),
            )
            top5_set = {n for _pos, n in clean_top5}
            for extra_n in ordered_d[5:8]:
                if extra_n not in top5_set:
                    p_n = float(dist.get(extra_n, 0.0) or 0.0)
                    lift = max(0.0, min(1.0, (p_n - base_p) / span))
                    if lift > 0.0:
                        out[extra_n] = 0.24 * lift
    return out


def _wf_member_skill_map(walkforward):
    wf = walkforward or {}
    wf_experts = wf.get("experts") or {}
    if not wf_experts:
        return {}
    top5_base = 5.0 / 37.0
    exact_base = 1.0 / 37.0
    exp_skills = {}
    for exp_name in ("RECENCY", "WHEEL", "TRANSITION", "LONG"):
        st = wf_experts.get(exp_name) or {}
        tn = int(st.get("trials", 0) or 0)
        if tn < 40:
            continue
        t5 = int(st.get("top5", 0) or 0)
        ex = int(st.get("exact", 0) or 0)
        t5_sm = (t5 + top5_base * 35.0) / (tn + 35.0)
        ex_sm = (ex + exact_base * 65.0) / (tn + 65.0)
        sk = 0.80 * (t5_sm / top5_base) + 0.20 * (ex_sm / exact_base)
        if tn >= 80 and (t5 / tn) < top5_base * 0.88:
            sk *= 0.72
        exp_skills[exp_name] = min(1.55, max(0.52, sk))
    out = {}
    if "RECENCY" in exp_skills:
        out["MODEL_RECENCY"] = exp_skills["RECENCY"]
    if "WHEEL" in exp_skills:
        out["MODEL_WHEEL"] = exp_skills["WHEEL"]
    if "TRANSITION" in exp_skills:
        out["MODEL_TRANSITION"] = exp_skills["TRANSITION"]
        out["LOCAL"] = exp_skills["TRANSITION"]
    if "LONG" in exp_skills:
        out["ARCHIVE"] = max(1.15, exp_skills["LONG"])
        out["MODEL_WEB"] = min(1.25, exp_skills["LONG"])
        out["TABLE500"] = exp_skills["LONG"]
        out["TABLE_LONG"] = exp_skills["LONG"]
    return out


def choose_net_number(
    pred,
    source_hits=None,
    expert_hits=None,
    validation_history=None,
):
    """
    Exact-focused family selector.

    Correlated sources are capped inside three families:
      AKIŞ  = CANLI + RECENCY + TRANSITION
      TABLO = SON500 + UZUN + LONG-M
      ÇARK  = WHEEL

    A family is normalized internally, so having 3 correlated members does
    not create 3 independent votes.
    """
    pred = pred or {}
    source_hits = source_hits or {}
    expert_hits = expert_hits or {}

    profiles = exact_window_profiles(
        validation_history or [],
        source_hits,
        expert_hits,
    )

    sc = pred.get("source_consensus") or {}
    raw_sources = sc.get("sources") or {}
    experts = pred.get("experts") or {}
    wf_skills = _wf_member_skill_map(pred.get("walkforward"))
    members = {}

    def _blended_member_skill(key):
        pr = profiles.get(key) or {}
        live_sk = float(pr.get("effective_skill", pr.get("skill", 1.0)))
        n100 = int(pr.get("n100", 0) or 0)
        wf_sk = wf_skills.get(key)
        if wf_sk is None:
            return live_sk
        # When live rounds on this table are still few (<80), let the 220-round
        # same-table walk-forward evaluation guide member skill immediately.
        wf_w = 0.58 * (1.0 - min(1.0, n100 / 85.0)) + 0.18
        return min(1.55, max(0.52, (1.0 - wf_w) * live_sk + wf_w * float(wf_sk)))

    for key in ("LOCAL","TABLE500","TABLE_LONG","ARCHIVE"):
        sd = raw_sources.get(key) or {}
        top5 = [
            int(x) for x in (sd.get("top5") or [])
            if isinstance(x, int) and 0 <= int(x) <= 36
        ][:5]
        s_dist = sd.get("dist") if isinstance(sd.get("dist"), dict) else None
        if top5:
            members[key] = {
                "top1": top5[0],
                "dist": _member_rank_scores(top5, s_dist),
                "skill": _blended_member_skill(key),
            }

    exp_keys = {
        "RECENCY":"MODEL_RECENCY",
        "WHEEL":"MODEL_WHEEL",
        "TRANSITION":"MODEL_TRANSITION",
        "WEB":"MODEL_WEB",
    }
    for exp, key in exp_keys.items():
        dist = experts.get(exp) or {}
        ordered = sorted(dist.items(), key=lambda kv:(-float(kv[1]), int(kv[0])))
        if ordered:
            top5 = [int(n) for n,_p in ordered[:5]]
            members[key] = {
                "top1": top5[0],
                "dist": _member_rank_scores(top5, dist),
                "skill": _blended_member_skill(key),
            }

    if "ARCHIVE" in members:
        families = {
            "ORTAK": ("ARCHIVE",),
            "TABLO": ("TABLE500","TABLE_LONG"),
            "AKIŞ": ("LOCAL","MODEL_RECENCY","MODEL_TRANSITION"),
            "ÇARK": ("MODEL_WHEEL",),
        }
    else:
        families = {
            "ORTAK": ("ARCHIVE","MODEL_WEB"),
            "TABLO": ("TABLE500","TABLE_LONG"),
            "AKIŞ": ("LOCAL","MODEL_RECENCY","MODEL_TRANSITION"),
            "ÇARK": ("MODEL_WHEEL",),
        }

    family_dists = {}
    family_picks = {}
    family_strength = {}
    family_member_picks = {}

    for fam, keys in families.items():
        active = [k for k in keys if k in members]
        if not active:
            continue

        agg = {n:0.0 for n in range(37)}
        sw = 0.0
        for key in active:
            m = members[key]
            w = min(1.55, max(0.62, float(m["skill"])))
            sw += w
            for n in range(37):
                agg[n] += w * float(m["dist"].get(n,0.0))

        if sw <= 1e-9:
            continue

        for n in range(37):
            agg[n] /= sw

        peak = max(agg.values()) if agg else 0.0
        if peak > 1e-9:
            for n in range(37):
                agg[n] /= peak

        family_dists[fam] = agg
        family_picks[fam] = max(range(37), key=lambda n:(agg[n], -n))
        skills_in_fam = [float(members[k]["skill"]) for k in active]
        avg_sk = sum(skills_in_fam) / len(skills_in_fam)
        max_sk = max(skills_in_fam)
        # Weight toward the strongest proven member in the family so a weak
        # member (e.g. 0/98) does not drag down a hot member (e.g. 7/98).
        family_strength[fam] = 0.68 * max_sk + 0.32 * avg_sk
        family_member_picks[fam] = {
            k:int(members[k]["top1"]) for k in active
        }

    if not family_dists:
        fallback = int(pred.get("predicted",0) or 0)
        if not 0 <= fallback <= 36:
            fallback = 0
        return {
            "number": fallback, "top5":[fallback],
            "family_supporters":[], "family_count":0,
            "family_picks":{}, "family_member_picks":{},
            "family_weights":{}, "member_supporters":[],
            "leader_family":"-", "score":0.0,
            "signal_score":1.0,
            "runner_up":fallback, "exact_profiles":profiles,
            "gates": {
                key:{"gate":float(pr.get("gate",1.0)),"state":str(pr.get("state","STABİL")),"drift":float(pr.get("drift",0.0))}
                for key,pr in profiles.items()
            },
        }

    mt_snap = pred.get("multi_table_transition") or {}
    mt_spins = int(mt_snap.get("spins", 0) or 0)
    mt_tables = int(mt_snap.get("tables", 0) or 0)
    mt_exact_obs = int(mt_snap.get("exact_obs", 0) or 0)
    mt_exact_probs = mt_snap.get("exact_probs") or {}
    mt_top_pct = mt_snap.get("exact_top_pct") or []
    mt_top_list = [
        int(row[0]) for row in mt_top_pct
        if isinstance(row, (list, tuple)) and len(row) >= 1 and isinstance(row[0], int) and 0 <= int(row[0]) <= 36
    ]
    table_long_count = int(pred.get("table_long_count", 0) or 0)

    # Exact-skill adaptation + decisive multi-table pool (ORTAK HAVUZ) dominance.
    raw_fw = {
        fam:min(1.42, max(0.48, family_strength[fam]))
        for fam in family_dists
    }
    live_n100 = max(
        (int(pr.get("n100", 0) or 0) for pr in profiles.values()),
        default=0,
    )
    maturity_gap = max(0.0, (35.0 - min(35.0, float(live_n100))) / 35.0)
    if "TABLO" in raw_fw and table_long_count >= 100:
        tablo_boost = 1.0 + 0.06 * min(1.0, table_long_count / 500.0) + 0.05 * maturity_gap
        raw_fw["TABLO"] = min(1.32, raw_fw["TABLO"] * tablo_boost)
    if "ORTAK" in raw_fw and mt_exact_obs >= 5:
        pool_boost = (
            1.22
            + 0.24 * min(1.0, mt_spins / 4000.0)
            + 0.18 * min(1.0, max(0, mt_tables - 1) / 10.0)
            + 0.18 * min(1.0, mt_exact_obs / 100.0)
            + 0.10 * maturity_gap
        )
        raw_fw["ORTAK"] = min(2.35, raw_fw["ORTAK"] * pool_boost)
    if maturity_gap > 0.0:
        if "AKIŞ" in raw_fw:
            raw_fw["AKIŞ"] = max(0.42, raw_fw["AKIŞ"] * (1.0 - 0.12 * maturity_gap))
        if "ÇARK" in raw_fw:
            raw_fw["ÇARK"] = max(0.40, raw_fw["ÇARK"] * (1.0 - 0.16 * maturity_gap))

    s = sum(raw_fw.values()) or 1.0
    fw = {fam:w/s for fam,w in raw_fw.items()}

    if len(fw) >= 2:
        fam_cap = 0.68 if mt_exact_obs >= 10 else 0.52
        fw = {fam:min(fam_cap, w) for fam,w in fw.items()}
        s2 = sum(fw.values()) or 1.0
        fw = {fam:w/s2 for fam,w in fw.items()}

    total = {n:0.0 for n in range(37)}
    fam_presence = {n:0 for n in range(37)}
    for fam, dist in family_dists.items():
        for n in range(37):
            val = float(dist.get(n,0.0))
            total[n] += fw[fam] * val
            if val >= 0.35:
                fam_presence[n] += 1

    combined = pred.get("combined") or {}
    max_comb = max((float(v or 0.0) for v in combined.values()), default=0.0)
    max_mt_prob = max((float(v or 0.0) for v in mt_exact_probs.values()), default=0.0)
    ortak_dist = family_dists.get("ORTAK") or {}
    tablo_dist = family_dists.get("TABLO") or {}
    mt_w = 0.48 + 0.38 * min(1.0, mt_exact_obs / 80.0) if mt_exact_obs >= 5 else 0.0
    mt_top5_set = set(mt_top_list[:5])

    for n in range(37):
        if max_comb > 1e-9:
            total[n] += 0.18 * (float(combined.get(n, 0.0) or 0.0) / max_comb)
        if mt_w > 0.0 and max_mt_prob > 1e-9:
            rel_mt = float(mt_exact_probs.get(n, 0.0) or 0.0) / max_mt_prob
            total[n] += mt_w * (rel_mt ** 1.35)
            if n in mt_top5_set:
                rank_idx = mt_top_list.index(n)
                total[n] += (0.28 - 0.045 * rank_idx) * rel_mt
        if fam_presence[n] >= 2:
            total[n] += 0.07 * (fam_presence[n] - 1)
        # Cross-family wheel-neighbor synergy (K1/K2 pocket alignment between ORTAK and TABLO)
        ln, rn = _WHEEL_LR[n]
        nb_support = (
            float(ortak_dist.get(ln, 0.0)) + float(ortak_dist.get(rn, 0.0))
            + float(tablo_dist.get(ln, 0.0)) + float(tablo_dist.get(rn, 0.0))
        )
        if nb_support > 0.0:
            total[n] += 0.035 * min(1.8, nb_support)

    # Anti-echo guard: prevent repeating recent spins ONLY when they are NOT
    # backed by ORTAK HAVUZ Top 5 percentage transitions or TABLO Top 2.
    recent_hist = [
        int(x) for x in (pred.get("recent_history") or [])
        if isinstance(x, int) and 0 <= x <= 36
    ]
    deep_top_protected = set(mt_top5_set)
    for deep_key in ("ARCHIVE", "TABLE500", "TABLE_LONG"):
        sd_deep = raw_sources.get(deep_key) or {}
        for x in (sd_deep.get("top5") or [])[:2]:
            if isinstance(x, int) and 0 <= x <= 36:
                deep_top_protected.add(int(x))
    if recent_hist:
        for idx_r, damper in ((0, 0.58), (1, 0.72), (2, 0.82)):
            if idx_r < len(recent_hist):
                r_spin = recent_hist[idx_r]
                if r_spin not in deep_top_protected:
                    total[r_spin] *= damper

    # Anti-stickiness: only dampen a stale number if it is NOT the #1/#2
    # empirical transition in ORTAK HAVUZ.
    recent_rows = [
        r for r in (validation_history or [])[-6:]
        if isinstance(r, dict) and "predicted" in r
    ]
    if len(recent_rows) >= 2:
        miss_counts = Counter()
        hit_Direct = set()
        for r in recent_rows:
            try:
                p_num = int(r.get("predicted"))
            except Exception:
                continue
            if r.get("exact"):
                hit_Direct.add(p_num)
            else:
                miss_counts[p_num] += 1
        for p_num, m_cnt in miss_counts.items():
            if (
                m_cnt >= 2
                and p_num not in hit_Direct
                and p_num not in set(mt_top_list[:2])
                and 0 <= p_num <= 36
            ):
                total[p_num] *= 0.80

    ordered = sorted(
        range(37),
        key=lambda n:(-total[n], -float(mt_exact_probs.get(n, 0.0) or 0.0), -float(combined.get(n,0.0) or 0.0), n),
    )

    # Primary NET SAYI must be led by ORTAK when multi-table empirical transitions
    # are available, or by the strongest active family leader.
    net_score = {n: float(total[n]) for n in range(37)}
    for fam, pick_n in family_picks.items():
        p_int = int(pick_n)
        if 0 <= p_int <= 36:
            net_score[p_int] += 0.42 * float(fw.get(fam, 0.0))

    family_leader_set = {
        int(pick_n) for pick_n in family_picks.values()
        if isinstance(pick_n, int) and 0 <= int(pick_n) <= 36
    }
    if mt_exact_obs >= 12 and mt_top_list:
        mt_leader = int(mt_top_list[0])
        family_picks["ORTAK"] = mt_leader
        family_leader_set.add(mt_leader)
        p_leader = float(mt_exact_probs.get(mt_leader, 0.0) or 0.0)
        # Check if #2 in ORTAK HAVUZ has nearly identical % (within 0.25 percentage points)
        # AND is simultaneously backed as #1 by TABLO or AKIŞ
        chosen = mt_leader
        if len(mt_top_list) >= 2:
            mt_second = int(mt_top_list[1])
            p_second = float(mt_exact_probs.get(mt_second, 0.0) or 0.0)
            other_fam_picks = {
                int(v) for k, v in family_picks.items()
                if k in ("TABLO", "AKIŞ") and isinstance(v, int)
            }
            if (p_leader - p_second) <= 0.0025 and mt_second in other_fam_picks and net_score[mt_second] > net_score[mt_leader]:
                chosen = mt_second
    elif family_leader_set:
        chosen = max(
            family_leader_set,
            key=lambda n: (net_score[n], total[n], float(combined.get(n, 0.0) or 0.0), -n),
        )
    else:
        chosen = int(ordered[0])

    leader_total = max(1e-9, float(total[chosen]))
    # Select the 4 backups (YEDEK-4) by strongly prioritizing the highest-%
    # empirical transitions in ORTAK HAVUZ (exact_top_pct) while using TABLO/AKIŞ
    # and wheel coverage to break ties.
    top5 = [chosen]
    covered_k1 = set(wheel_neighbors(chosen, 1))
    covered_k2 = set(wheel_neighbors(chosen, 2))
    remaining = [int(n) for n in ordered if int(n) != chosen]
    while len(top5) < 5 and remaining:
        def _backup_key(n):
            nb1_set = set(wheel_neighbors(n, 1))
            uncovered = nb1_set - covered_k1
            comb_bonus = (float(combined.get(n, 0.0) or 0.0) / max_comb) * 0.14 if max_comb > 1e-9 else 0.0
            rel_mt = (float(mt_exact_probs.get(n, 0.0) or 0.0) / max_mt_prob) if (mt_exact_obs >= 10 and max_mt_prob > 1e-9) else 0.0
            mt_bonus = (0.62 * (rel_mt ** 1.25)) if rel_mt > 0.0 else 0.0
            if n in mt_top5_set:
                mt_bonus += 0.25
            rel_strength = min(1.0, float(total[n]) / max(1e-9, leader_total * 0.55))
            if max_comb > 1e-9 and uncovered:
                uncovered_mass = sum(float(combined.get(m, 0.0) or 0.0) / max_comb for m in uncovered)
                cov_bonus = 0.025 * rel_strength * uncovered_mass
            else:
                cov_bonus = 0.015 * rel_strength * len(uncovered)
            # Never apply cluster_penalty to top ORTAK HAVUZ percentage transitions!
            cluster_penalty = (
                0.06
                if (n not in mt_top5_set and n in covered_k2 and len(uncovered) <= 1)
                else 0.0
            )
            return (
                total[n] + comb_bonus + mt_bonus + cov_bonus - cluster_penalty,
                float(mt_exact_probs.get(n, 0.0) or 0.0),
                float(combined.get(n, 0.0) or 0.0),
                -n,
            )

        best_b = max(remaining, key=_backup_key)
        top5.append(int(best_b))
        covered_k1.update(wheel_neighbors(best_b, 1))
        covered_k2.update(wheel_neighbors(best_b, 2))
        remaining.remove(best_b)

    family_supporters = [
        fam for fam,pick in family_picks.items()
        if int(pick) == chosen
    ]
    member_supporters = [
        key for key,m in members.items()
        if int(m.get("top1",-1)) == chosen
    ]
    leader_family = max(
        family_dists,
        key=lambda fam:(
            1 if int(family_picks.get(fam, -1)) == chosen else 0,
            fw[fam] * family_dists[fam].get(chosen,0.0),
            fam,
        ),
    )

    # Relative signal-strength indicator, NOT a roulette probability.
    other_Ordered = [n for n in ordered if int(n) != chosen]
    runner_score = float(total[other_Ordered[0]]) if other_Ordered else 0.0
    leader_score = max(float(total[chosen]), float(net_score[chosen]))
    margin_ratio = max(0.0, (leader_score - runner_score) / max(1e-9, leader_score))
    near_supporters = sum(
        1.0 if int(family_picks.get(fam, -1)) == chosen
        else (0.55 if float(dist.get(chosen, 0.0)) >= 0.75 else 0.0)
        for fam, dist in family_dists.items()
    )
    support_ratio = min(1.0, near_supporters / max(1, len(family_dists)))
    avg_family_skill = sum(raw_fw.values()) / max(1, len(raw_fw))
    signal_score = max(1.0, min(
        99.0,
        36.0 + 34.0 * support_ratio + 19.0 * min(1.0, margin_ratio / 0.42)
        + 10.0 * min(1.0, max(0.0, avg_family_skill - 0.75) / 0.55)
    ))

    return {
        "number":chosen,
        "top5":top5,
        "family_supporters":family_supporters,
        "family_count":len(family_dists),
        "family_picks":{fam:int(x) for fam,x in family_picks.items()},
        "family_member_picks":family_member_picks,
        "family_weights":{fam:float(x) for fam,x in fw.items()},
        "member_supporters":member_supporters,
        "leader_family":leader_family,
        "score":float(total[chosen]),
        "signal_score":float(signal_score),
        "runner_up":int(ordered[1]) if len(ordered)>1 else chosen,
        "exact_profiles":profiles,
        "gates": {
            key: {
                "gate": float(pr.get("gate",1.0)),
                "state": str(pr.get("state","STABİL")),
                "drift": float(pr.get("drift",0.0)),
            }
            for key,pr in profiles.items()
        },
    }




def persistent_data_dir():
    """Keep model learning outside version folders."""
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        base = os.path.expanduser("~")
    path = os.path.join(base, "PragmaticRouletteTracker")
    os.makedirs(path, exist_ok=True)
    return path


def migrate_old_learning_if_needed(new_learning_path, new_log_path):
    """Copy legacy learning from the current app folder once, if present."""
    here = os.path.dirname(os.path.abspath(__file__))
    old_learning = os.path.join(here, "roulette_learning.json")
    old_log = os.path.join(here, "roulette_prediction_log.jsonl")

    try:
        if not os.path.exists(new_learning_path) and os.path.exists(old_learning):
            shutil.copy2(old_learning, new_learning_path)
    except Exception:
        pass

    try:
        if not os.path.exists(new_log_path) and os.path.exists(old_log):
            shutil.copy2(old_log, new_log_path)
    except Exception:
        pass


def detect_new_front_large(old_newest, new_newest, max_new=500):
    """
    Both arrays are newest-first sliding windows.
    Find how many genuinely new results were prepended to the new window.
    Uses the longest reliable overlap, not value de-duplication, because
    roulette numbers naturally repeat.
    """
    old = [int(x) for x in (old_newest or []) if isinstance(x, int) and 0 <= x <= 36]
    new = [int(x) for x in (new_newest or []) if isinstance(x, int) and 0 <= x <= 36]
    if not old:
        return list(new)
    if not new or old == new:
        return []

    max_k = min(max_new, len(new))
    # Prefer a reasonably long overlap to avoid accidental matches.
    for k in range(1, max_k + 1):
        overlap = min(len(new) - k, len(old))
        if overlap >= 12 and new[k:k+overlap] == old[:overlap]:
            return new[:k]

    # Fallback 1: search for the old first 12-result signature within new.
    sig_len = min(12, len(old))
    if sig_len >= 8:
        sig = old[:sig_len]
        for k in range(1, min(len(new) - sig_len + 1, max_new + 1)):
            if new[k:k+sig_len] == sig:
                return new[:k]

    # Fallback 2: offset-tolerant 10-gram anchor (handles 1-2 spin DOM/multiplier
    # differences near index 0 of old while still requiring a 10-number exact match).
    anchor_len = 10
    if len(old) >= anchor_len + 8 and len(new) >= anchor_len + 2:
        for off in (1, 2, 3, 5, 8):
            if off + anchor_len > len(old):
                break
            anchor = old[off:off + anchor_len]
            if len(set(anchor)) < 4:
                continue
            limit_pos = min(len(new) - anchor_len, max_new + off)
            for pos in range(off + 1, limit_pos + 1):
                if new[pos:pos + anchor_len] == anchor:
                    k = pos - off
                    if 1 <= k <= max_new:
                        return new[:k]

    return []


_LONG_ARCHIVE_CACHE = {}


def sanitize_long_archive(results_newest_first, window=8):
    """
    Fast, single-pass archive sanitizer (<0.3ms per table).
    Preserves all genuine roulette spins while removing accidental >=10-gram
    duplicate blocks (forward & reversed) or back-to-back tandem block repeats.
    """
    raw = [
        int(x) for x in (results_newest_first or [])
        if isinstance(x, int) and 0 <= x <= 36
    ]
    n_raw = len(raw)
    if n_raw <= 500:
        return raw

    # Pass 1: Collapse only genuine back-to-back tandem block repeats (p >= 6)
    clean = []
    idx = 0
    while idx < n_raw:
        jumped = False
        cur_val = raw[idx]
        max_p = min(20, (n_raw - idx) // 2)
        for p in range(6, max_p + 1):
            if raw[idx + p] != cur_val:
                continue
            if idx + p * 2 > n_raw:
                continue
            unit = raw[idx:idx + p]
            reps = 1
            while idx + (reps + 1) * p <= n_raw and raw[idx + reps * p:idx + (reps + 1) * p] == unit:
                reps += 1
            if reps >= 2:
                idx += (reps - 1) * p
                jumped = True
                break
        if not jumped:
            clean.append(cur_val)
            idx += 1

    n = len(clean)
    if n < 20:
        return clean

    # Pass 2: Deduplicate only >=10-gram duplicate blocks (forward or reversed)
    out = []
    seen_10_fwd = {}
    seen_10_rev = {}

    i = 0
    while i < n:
        cur_len = len(out)

        if i + 10 <= n:
            g10 = tuple(clean[i:i + 10])
            prev_pos = seen_10_fwd.get(g10)
            if prev_pos is not None:
                k = 10
                while i + k < n and prev_pos + k < cur_len and clean[i + k] == out[prev_pos + k]:
                    k += 1
                i += k
                continue
            prev_rev_end = seen_10_rev.get(g10)
            if prev_rev_end is not None:
                k = 10
                while i + k < n and prev_rev_end - 1 - k >= 0 and clean[i + k] == out[prev_rev_end - 1 - k]:
                    k += 1
                i += k
                continue

        val = clean[i]
        out.append(val)
        cur_len = len(out)
        if cur_len >= 10:
            g10_out = tuple(out[-10:])
            if g10_out not in seen_10_fwd:
                seen_10_fwd[g10_out] = cur_len - 10
            rev_g10 = tuple(reversed(g10_out))
            if rev_g10 not in seen_10_rev:
                seen_10_rev[rev_g10] = cur_len
        i += 1

    return out


def table_long_archive_path(data_dir, table_name):
    key = safe_table_key(table_name or "roulette")
    return os.path.join(data_dir, f"table_long_archive_{key}.json")


def load_table_long_archive(data_dir, table_name):
    path = table_long_archive_path(data_dir, table_name)
    try:
        if not os.path.exists(path):
            return []
        mtime = os.path.getmtime(path)
        cached = _LONG_ARCHIVE_CACHE.get(path)
        if cached is not None and cached[0] == mtime:
            return list(cached[1])

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        vals = data.get("results_newest_first", [])
        raw = [
            int(x) for x in vals
            if isinstance(x, int) and 0 <= x <= 36
        ]
        cleaned = sanitize_long_archive(raw)
        if len(cleaned) != len(raw):
            save_table_long_archive(data_dir, table_name, cleaned)
            try:
                mtime = os.path.getmtime(path)
            except Exception:
                pass
        _LONG_ARCHIVE_CACHE[path] = (mtime, tuple(cleaned))
        return list(cleaned)
    except Exception:
        return []


def save_table_long_archive(data_dir, table_name, results_newest_first):
    path = table_long_archive_path(data_dir, table_name)
    clean = sanitize_long_archive(results_newest_first)
    clean_tup = tuple(clean)
    cached = _LONG_ARCHIVE_CACHE.get(path)
    if cached is not None and cached[1] == clean_tup:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "table": str(table_name or ""),
                    "count": len(clean),
                    "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "results_newest_first": clean,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        _LONG_ARCHIVE_CACHE[path] = (os.path.getmtime(path), clean_tup)
    except Exception:
        pass
    return path



def public_long_archive_path(data_dir, table_name):
    key = safe_table_key(table_name or "roulette")
    return os.path.join(data_dir, f"public_long_archive_{key}.json")


def load_public_long_archive(data_dir, table_name):
    path = public_long_archive_path(data_dir, table_name)
    try:
        if not os.path.exists(path):
            return []
        with open(path,'r',encoding='utf-8') as f:
            data = json.load(f)
        return [int(x) for x in data.get('results_newest_first',[]) if isinstance(x,int) and 0 <= x <= 36]
    except Exception:
        return []


def save_public_long_archive(data_dir, table_name, results_newest_first, label=""):
    path = public_long_archive_path(data_dir, table_name)
    clean = [int(x) for x in (results_newest_first or []) if isinstance(x,int) and 0 <= x <= 36]
    try:
        with open(path,'w',encoding='utf-8') as f:
            json.dump({
                'table':str(table_name or ''),'source':str(label or ''),
                'count':len(clean),'updated':time.strftime('%Y-%m-%d %H:%M:%S'),
                'results_newest_first':clean,
            },f,ensure_ascii=False,indent=2)
    except Exception:
        pass
    return path

DIRECT_RESULT_KEYS = (
    "result", "number", "value",
    "winningNumber", "winning_number",
    "winNumber", "win_number",
    "resultNumber", "result_number",
    "rouletteNumber", "roulette_number",
    "winningPocket", "winning_pocket",
    "gameResult", "game_result",
    "spinResult", "spin_result",
    "outcomeNumber", "outcome_number",
    "resultValue", "result_value",
    "slotNumber", "slot_number",
)

def _roulette_num(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if 0 <= value <= 36 else None
    if isinstance(value, float) and value.is_integer():
        n=int(value); return n if 0 <= n <= 36 else None
    if isinstance(value, str):
        s=value.strip()
        if re.fullmatch(r"(?:[0-9]|[12][0-9]|3[0-6])",s):
            return int(s)
    return None


def _roulette_num_loose(value):
    n = _roulette_num(value)
    if n is not None:
        return n
    if isinstance(value, str):
        s = value.strip()
        # For named result fields Pragmatic may return strings like "29 BLACK"
        # or "Winning number: 29". Accept a single roulette number token only.
        nums = re.findall(r"(?<!\d)(?:[0-9]|[12][0-9]|3[0-6])(?!\d)", s)
        if len(nums) == 1:
            return int(nums[0])
    return None


def _find_result_in_record(record, depth=0):
    if depth > 6:
        return None
    if isinstance(record, dict):
        lower={str(k).lower():v for k,v in record.items()}
        for wanted in DIRECT_RESULT_KEYS:
            v=lower.get(wanted.lower())
            n=_roulette_num_loose(v)
            if n is not None:
                return n
            if isinstance(v,(dict,list)):
                n=_find_result_in_record(v,depth+1)
                if n is not None:
                    return n
        for k,v in record.items():
            lk=str(k).lower()
            if any(w in lk for w in ("result","winner","winning","roulette","outcome")):
                n=_find_result_in_record(v,depth+1)
                if n is not None:
                    return n
    elif isinstance(record,list) and len(record) <= 8:
        for v in record:
            n=_roulette_num(v)
            if n is not None:
                return n
            n=_find_result_in_record(v,depth+1)
            if n is not None:
                return n
    return None

def extract_statistic_history(body):
    if not body:
        return []
    if isinstance(body,(bytes,bytearray)):
        body=body.decode("utf-8",errors="ignore")
    if isinstance(body,str):
        s=body.strip()
        try:
            obj=json.loads(s)
        except Exception:
            m=re.search(r"(\{.*\}|\[.*\])",s,flags=re.S)
            if not m:
                return []
            try:
                obj=json.loads(m.group(1))
            except Exception:
                return []
    else:
        obj=body

    candidates=[]
    seen=set()

    def add(vals,path="",strength=0):
        clean=[]
        for v in vals:
            n=_roulette_num(v)
            if n is not None:
                clean.append(n)
        if len(clean) < 20:
            return
        clean=clean[:700]
        key=tuple(clean)
        if key in seen:
            return
        seen.add(key)
        lp=str(path).lower()
        hint=sum(12 for w in ("history","result","game","round","roulette","statistic") if w in lp)
        capped=min(len(clean),500)
        score=strength+hint+capped*0.20+max(0.0,70.0-abs(500-capped)*0.15)
        candidates.append((score,clean))

    def walk(node,path="",depth=0):
        if depth > 8:
            return
        if isinstance(node,list):
            primitive=[_roulette_num(v) for v in node]
            good=[n for n in primitive if n is not None]
            if len(node)>=20 and len(good)>=max(20,int(len(node)*0.80)):
                add(good,path,35)
            elif len(node)>=20:
                loose=[_roulette_num_loose(v) for v in node]
                loose_good=[n for n in loose if n is not None]
                if len(loose_good)>=max(20,int(len(node)*0.80)):
                    add(loose_good,path,25)
            dict_count=sum(isinstance(v,dict) for v in node)
            if len(node)>=20 and dict_count>=int(len(node)*0.60):
                vals=[]
                for item in node:
                    n=_find_result_in_record(item)
                    if n is not None:
                        vals.append(n)
                if len(vals)>=max(20,int(len(node)*0.60)):
                    add(vals,path,95)
            for i,v in enumerate(node[:50]):
                if isinstance(v,(dict,list,str)):
                    walk(v,f"{path}[{i}]",depth+1)
        elif isinstance(node,dict):
            for k,v in node.items():
                child=f"{path}.{k}" if path else str(k)
                if isinstance(v,list):
                    good=[_roulette_num(x) for x in v]
                    good=[n for n in good if n is not None]
                    if len(good)>=20:
                        add(good,child,55)
                walk(v,child,depth+1)
        elif isinstance(node,str):
            s=node.strip()
            if len(s)<2_000_000 and s[:1] in "[{":
                try:
                    walk(json.loads(s),path+".json",depth+1)
                except Exception:
                    pass

    walk(obj)
    if not candidates:
        return []
    candidates.sort(key=lambda row:(-row[0],-len(row[1])))
    return candidates[0][1][:500]


def extract_pragmatic_roulette_tables(body):
    """Return roulette table identities genuinely present in a lobby/API body."""
    if not body:
        return []
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", errors="ignore")
    try:
        obj = json.loads(body) if isinstance(body, str) else body
    except Exception:
        return []

    found = {}
    id_keys = (
        "tableid", "table_id", "tableidentifier", "tablecode",
        "studioid", "studio_id",
    )
    name_keys = (
        "tablename", "table_name", "displayname", "display_name",
        "gamename", "game_name", "title", "name",
    )

    def scalar_text(value):
        if isinstance(value, (str, int)) and not isinstance(value, bool):
            return str(value).strip()
        return ""

    def walk(node, inherited_hint="", depth=0):
        if depth > 10:
            return
        if isinstance(node, list):
            for item in node[:2000]:
                walk(item, inherited_hint, depth + 1)
            return
        if not isinstance(node, dict):
            return

        lower = {str(k).lower(): v for k, v in node.items()}
        combined = " ".join(
            scalar_text(v).lower()
            for v in node.values()
            if isinstance(v, (str, int)) and not isinstance(v, bool)
        )
        hint = (inherited_hint + " " + combined)[-1600:]
        is_roulette = any(x in hint for x in (
            "roulette", "rulet", "mega wheel roulette", "auto roulette",
        ))

        table_id = ""
        for key in id_keys:
            table_id = scalar_text(lower.get(key))
            if table_id:
                break

        # Some Pragmatic lobby objects use gameId/id for the table identity.
        if not table_id and is_roulette:
            table_id = scalar_text(lower.get("gameid") or lower.get("game_id"))
        if not table_id and is_roulette:
            candidate = scalar_text(lower.get("id"))
            if candidate and 3 <= len(candidate) <= 160:
                table_id = candidate

        if table_id and is_roulette and 2 <= len(table_id) <= 180:
            name = ""
            for key in name_keys:
                name = scalar_text(lower.get(key))
                if name and ("roulette" in name.lower() or "rulet" in name.lower()):
                    break
            if not name:
                name = table_id
            old = found.get(table_id) or {}
            found[table_id] = {
                "table_id": table_id,
                "display_name": name if name != table_id or not old else old.get("display_name", table_id),
            }

        for key, value in node.items():
            if isinstance(value, (dict, list)):
                walk(value, hint + " " + str(key).lower(), depth + 1)

    walk(obj)
    return sorted(found.values(), key=lambda row: row.get("display_name", "").lower())

DIRECT_HISTORY_SCAN = r"""
(async () => {
  const resources = performance.getEntriesByType('resource').map(x => x.name || '');
  const reversed = [...resources].reverse();

  function storageGet(k) {
    try {
      return localStorage.getItem(k) || sessionStorage.getItem(k) || '';
    } catch (_) {
      return '';
    }
  }

  let tableId = storageGet('tableid') || storageGet('tableId');

  if (!tableId) {
    for (const raw of reversed) {
      if (!/tableId=/i.test(raw)) continue;
      try {
        const u = new URL(raw);
        tableId = u.searchParams.get('tableId') || '';
        if (tableId) break;
      } catch (_) {}
    }
  }

  let operatorGameId = '';
  for (const raw of reversed) {
    if (!/\/api\/ge\/versions/i.test(raw)) continue;
    try {
      const u = new URL(raw);
      operatorGameId = u.searchParams.get('operatorGameId') || '';
      if (operatorGameId) break;
    } catch (_) {}
  }

  let themeCode = '';
  for (const raw of reversed) {
    const m = raw.match(/\/themes\/([^/]+)\/theme\.json/i);
    if (m) {
      themeCode = m[1] || '';
      break;
    }
  }

  // Best case: browser already recorded the exact endpoint for this tableId.
  let historyUrl = reversed.find(
    u => /\/api\/ui\/statisticHistory\?/i.test(u) &&
         /numberOfGames=500/i.test(u) &&
         (!tableId || new RegExp('[?&]tableId=' + tableId + '(?:&|$)', 'i').test(u))
  ) || '';

  // Second case: derive from /api/ui/stats.
  if (!historyUrl) {
    const statsUrl = reversed.find(
      u => /\/api\/ui\/stats\?/i.test(u) && /tableId=/i.test(u)
    ) || '';

    if (statsUrl) {
      try {
        const u = new URL(statsUrl);
        u.pathname = u.pathname.replace(/\/stats$/i, '/statisticHistory');
        u.searchParams.delete('noOfGames');
        u.searchParams.set('numberOfGames', '500');
        if (tableId) u.searchParams.set('tableId', tableId);
        historyUrl = u.toString();
      } catch (_) {}
    }
  }

  // Third case (V2.7.1 fix):
  // use ANY already-authenticated Pragmatic games API request as a template.
  // This keeps JSESSIONID in browser memory only; it is never returned to Python.
  if (!historyUrl && tableId) {
    const apiSeed = reversed.find(raw => {
      try {
        const u = new URL(raw);
        return /^https?:$/i.test(u.protocol) &&
               /(^|\.)games\./i.test(u.hostname) &&
               /\/api\//i.test(u.pathname) &&
               (
                 u.searchParams.has('JSESSIONID') ||
                 u.searchParams.has('tableId')
               );
      } catch (_) {
        return false;
      }
    }) || '';

    if (apiSeed) {
      try {
        const u = new URL(apiSeed);
        u.pathname = '/api/ui/statisticHistory';

        // Preserve JSESSIONID, remove unrelated request-specific parameters.
        const keepSession = u.searchParams.get('JSESSIONID') || '';
        u.search = '';
        if (keepSession) u.searchParams.set('JSESSIONID', keepSession);
        u.searchParams.set('numberOfGames', '500');
        u.searchParams.set('tableId', tableId);

        historyUrl = u.toString();
      } catch (_) {}
    }
  }

  if (!historyUrl) {
    return {
      ok: false,
      reason: 'Pragmatic games API tabanı görülmedi',
      tableId,
      operatorGameId,
      themeCode,
      title: document.title || ''
    };
  }

  try {
    const r = await fetch(historyUrl, {
      credentials: 'include',
      cache: 'no-store'
    });
    const body = await r.text();

    // Deliberately do NOT return historyUrl/JSESSIONID.
    return {
      ok: !!r.ok,
      status: r.status,
      tableId,
      operatorGameId,
      themeCode,
      title: document.title || '',
      body
    };
  } catch (e) {
    return {
      ok: false,
      reason: String(e && e.message || e || 'fetch failed'),
      tableId,
      operatorGameId,
      themeCode,
      title: document.title || ''
    };
  }
})()
"""



def build_table_api_history_fetch(table_id):
    tid_json = json.dumps(str(table_id or ""))
    return f"""
(async () => {{
  const wantedTableId = {tid_json};
  const resources = performance.getEntriesByType('resource').map(x => x.name || '');
  const reversed = [...resources].reverse();

  let historyUrl = reversed.find(
    u => /\/api\/ui\/statisticHistory\?/i.test(u) && /JSESSIONID=/i.test(u)
  ) || '';

  if (!historyUrl) {{
    const statsUrl = reversed.find(
      u => /\/api\/ui\/stats\?/i.test(u) && /JSESSIONID=/i.test(u)
    ) || '';
    if (statsUrl) {{
      try {{
        const u = new URL(statsUrl);
        u.pathname = u.pathname.replace(/\/stats$/i, '/statisticHistory');
        historyUrl = u.toString();
      }} catch (_) {{}}
    }}
  }}

  if (!historyUrl) {{
    const apiSeed = reversed.find(raw => {{
      try {{
        const u = new URL(raw);
        return /^https?:$/i.test(u.protocol) &&
               /(^|\.)games\./i.test(u.hostname) &&
               /\/api\//i.test(u.pathname) &&
               u.searchParams.has('JSESSIONID');
      }} catch (_) {{ return false; }}
    }}) || '';
    if (apiSeed) {{
      try {{
        const u = new URL(apiSeed);
        u.pathname = '/api/ui/statisticHistory';
        historyUrl = u.toString();
      }} catch (_) {{}}
    }}
  }}

  if (!historyUrl || !wantedTableId) {{
    return {{ok:false, reason:'API şablonu veya tableId yok', tableId:wantedTableId, title:document.title||''}};
  }}

  try {{
    const u = new URL(historyUrl);
    const keepSession = u.searchParams.get('JSESSIONID') || '';
    u.search = '';
    if (keepSession) u.searchParams.set('JSESSIONID', keepSession);
    u.searchParams.set('numberOfGames', '500');
    u.searchParams.set('tableId', wantedTableId);

    const r = await fetch(u.toString(), {{credentials:'include', cache:'no-store'}});
    const body = await r.text();
    return {{ok:!!r.ok, status:r.status, tableId:wantedTableId, title:document.title||'', body}};
  }} catch (e) {{
    return {{ok:false, reason:String(e && e.message || e || 'fetch failed'), tableId:wantedTableId, title:document.title||''}};
  }}
}})()
"""

VISIBILITY_SCAN = r"""
(() => ({
  visibility: document.visibilityState || "",
  focus: !!document.hasFocus(),
  href: String(location.href || ""),
  title: String(document.title || "")
}))()
"""

def safe_lobby_entry_url(url):
    """
    Convert an old/deep roulette URL into a stable casino/live-casino entry URL.
    Never preserves a concrete openGames/gameNames table reference.
    """
    raw = str(url or "").strip()
    if not raw.startswith(("http://", "https://")):
        return ""
    try:
        u = urllib.parse.urlsplit(raw)
        low = raw.lower()
        blocked = (
            "jsessionid", "pragmaticplaylive", "pragmaticplay.net",
            "/game.do", "/api/", "sessionid=", "token="
        )
        if any(x in low for x in blocked):
            return ""

        # Old deep-link examples can contain a dead concrete table in openGames.
        # Keep the authenticated site path, but remove all concrete game/session refs.
        qs = urllib.parse.parse_qsl(u.query, keep_blank_values=False)
        drop = {
            "opengames", "gamenames", "gameid", "tableid", "table_id",
            "operatorgameid", "sessionid", "token", "launchurl", "gameurl"
        }
        cleaned = []
        for k, v in qs:
            if str(k).lower() in drop:
                continue
            # Search terms can lock the UI on an unavailable provider/table state.
            if str(k).lower() == "searchterm":
                continue
            cleaned.append((k, v))

        path = u.path or "/"
        plow = path.lower()
        # If the saved URL already belongs to the live-casino section, start from
        # its stable home route rather than the old opened table.
        if "/live-casino/" in plow:
            idx = plow.find("/live-casino/")
            prefix = path[:idx]
            path = prefix + "/live-casino/home"
        elif "/livecasino/" in plow:
            idx = plow.find("/livecasino/")
            prefix = path[:idx]
            path = prefix + "/livecasino/home"

        return urllib.parse.urlunsplit((
            u.scheme, u.netloc, path,
            urllib.parse.urlencode(cleaned, doseq=True), ""
        ))
    except Exception:
        return ""


def safe_last_page_url(url):
    """
    Keep the exact last visited user page while stripping one-time auth/session
    tokens and normalizing broken non-lobby openGames deep-links (such as
    555575059-real Gates of Olympus Roulette) back to Pragmatic Play Lobby.
    """
    try:
        raw = str(url or "").strip()
        if not raw.startswith(("http://", "https://")):
            return ""
        u = urllib.parse.urlsplit(raw)
        if not u.netloc:
            return ""
        qs = urllib.parse.parse_qsl(u.query, keep_blank_values=True)
        drop = {
            "token", "session", "sessionid", "jsessionid", "auth",
            "jwt", "ticket", "sid", "otk", "keycode", "launchtoken",
        }
        cleaned = [
            (k, v) for k, v in qs
            if str(k).lower() not in drop
        ]
        path = u.path or "/"
        qdict = {str(k).lower(): str(v) for k, v in cleaned}
        if "/live-casino" in path.lower() and "opengames" in qdict:
            og = qdict.get("opengames", "").strip()
            if og and og != "3300922-real":
                cleaned = [
                    ("searchTerm", "pragmatic"),
                    ("openGames", "3300922-real"),
                    ("gameNames", "Pragmatic Play Lobby"),
                ]
        return urllib.parse.urlunsplit((
            u.scheme, u.netloc, path,
            urllib.parse.urlencode(cleaned, doseq=True), u.fragment or ""
        ))
    except Exception:
        return ""


def collector_refresh_due(now, last_success, last_attempt, has_error):
    if last_success and now - last_success < COLLECTOR_REFRESH_SECONDS:
        return False
    if has_error and last_attempt and now - last_attempt < COLLECTOR_RETRY_SECONDS:
        return False
    return True


RECOVERY_PHRASES = [
    "sayfayı yenile",
    "sayfayi yenile",
    "sayfayı yeniden yükle",
    "sayfayi yeniden yukle",
    "lütfen sayfayı yenileyin",
    "lutfen sayfayi yenileyin",
    "sayfayı yenilemeniz",
    "sayfayi yenilemeniz",
    "refresh the page",
    "reload the page",
    "please refresh",
    "please reload",
]
RECOVERY_BUTTON_WORDS = [
    "yenile", "yeniden yükle", "yeniden yukle",
    "refresh", "reload", "tekrar dene", "retry"
]
RECOVERY_ERROR_WORDS = [
    "bağlantı", "baglanti", "connection", "oturum", "session",
    "hata", "error", "bağlantınız kesildi", "connection lost"
]


def recovery_text_score(text, buttons=None):
    """Pure-Python mirror used by self-test and conservative watchdog logic."""
    raw = str(text or "").lower()
    btns = [str(x or "").lower().strip() for x in (buttons or [])]
    phrase_hits = [p for p in RECOVERY_PHRASES if p in raw]
    error_hit = any(w in raw for w in RECOVERY_ERROR_WORDS)
    button_hits = [
        b for b in btns
        if any(w == b or w in b for w in RECOVERY_BUTTON_WORDS)
    ]
    score = (3 if phrase_hits else 0) + (2 if button_hits else 0) + (1 if error_hit else 0)
    hit = bool(phrase_hits) or bool(button_hits and error_hit)
    return {
        "hit": bool(hit and score >= 3),
        "score": int(score),
        "phrases": phrase_hits,
        "buttons": button_hits,
        "error": bool(error_hit),
    }



LOBBY_TEACH_SCAN = r"""
(() => {
  function norm(x) {
    return String(x || '').replace(/\s+/g,' ').trim().slice(0,220);
  }

  function clickable(el) {
    let p=el;
    for (let i=0;i<8 && p;i++,p=p.parentElement) {
      const tag=(p.tagName||'').toLowerCase();
      const role=(p.getAttribute && p.getAttribute('role')) || '';
      if (tag==='a'||tag==='button'||role==='button'||p.onclick||p.tabIndex>=0) return p;
    }
    return el;
  }

  function describe(el) {
    const c=clickable(el);
    if (!c) return null;
    const cls=String(c.className||'').split(/\s+/)
      .filter(x=>x && x.length<80).slice(0,10);
    return {
      tag:String(c.tagName||'').toLowerCase(),
      text:norm(c.innerText||c.textContent||''),
      id:String(c.id||'').slice(0,140),
      href:String(c.href || (c.getAttribute && c.getAttribute('href')) || '').slice(0,700),
      testid:String((c.getAttribute && c.getAttribute('data-testid')) || '').slice(0,180),
      aria:String((c.getAttribute && c.getAttribute('aria-label')) || '').slice(0,180),
      role:String((c.getAttribute && c.getAttribute('role')) || '').slice(0,80),
      placeholder:String((c.getAttribute && c.getAttribute('placeholder')) || '').slice(0,180),
      name:String((c.getAttribute && c.getAttribute('name')) || '').slice(0,120),
      inputType:String((c.getAttribute && c.getAttribute('type')) || '').slice(0,40),
      classes:cls,
      page:String(location.href||'').slice(0,900),
      title:String(document.title||'').slice(0,220),
      ts:Date.now()
    };
  }

  function plainDescribe(el) {
    if (!el || el===document || el===document.documentElement || el===document.body) {
      return {
        tag:'window', text:'', id:'', href:'', testid:'', aria:'',
        role:'', placeholder:'', name:'', inputType:'', classes:[],
        page:String(location.href||'').slice(0,900),
        title:String(document.title||'').slice(0,220),
        ts:Date.now()
      };
    }
    const cls=String(el.className||'').split(/\s+/)
      .filter(x=>x && x.length<80).slice(0,10);
    return {
      tag:String(el.tagName||'').toLowerCase(),
      text:norm(el.innerText||el.textContent||'').slice(0,100),
      id:String(el.id||'').slice(0,140),
      href:'',
      testid:String((el.getAttribute && el.getAttribute('data-testid')) || '').slice(0,180),
      aria:String((el.getAttribute && el.getAttribute('aria-label')) || '').slice(0,180),
      role:String((el.getAttribute && el.getAttribute('role')) || '').slice(0,80),
      placeholder:'',
      name:'',
      inputType:'',
      classes:cls,
      page:String(location.href||'').slice(0,900),
      title:String(document.title||'').slice(0,220),
      ts:Date.now()
    };
  }

  function isSafeSearchInput(el) {
    if (!el) return false;
    const tag=String(el.tagName||'').toLowerCase();
    if (tag!=='input' && tag!=='textarea') return false;

    const type=String(el.getAttribute('type')||'text').toLowerCase();
    if (['password','email','tel','number','date','month','week','time','url'].includes(type))
      return false;

    const probe=[
      el.getAttribute('placeholder')||'',
      el.getAttribute('aria-label')||'',
      el.getAttribute('name')||'',
      el.id||'',
      el.getAttribute('data-testid')||''
    ].join(' ').toLocaleUpperCase('tr-TR');

    const safe=/ARA|SEARCH|FIND|GAME|OYUN|TABLE|MASA|LOBBY|CASINO|PROVIDER|SAĞLAYICI/.test(probe);
    const blocked=/CHAT|MESAJ|MESSAGE|LOGIN|GİRİŞ|PASSWORD|ŞİFRE|MAIL|EMAIL|PHONE|TELEFON|CARD|KART|IBAN|PAY|ÖDEME|DEPOSIT|YATIR/.test(probe);
    return safe && !blocked;
  }

  function inputDescribe(el) {
    const d=describe(el) || {};
    d.tag=String(el.tagName||'').toLowerCase();
    d.action='type';
    d.value=String(el.value||'').slice(0,180);
    d.text='';
    d.href='';
    d.ts=Date.now();
    return d;
  }

  function pushAction(d) {
    if (!d) return;
    const q=window.__rouletteTeachQueue || (window.__rouletteTeachQueue=[]);
    q.push(d);
    if (q.length>100) window.__rouletteTeachQueue=q.slice(-100);
  }

  function flushTyping(force=false) {
    const p=window.__rouletteTeachPendingType;
    if (!p) return;
    if (!force && Date.now()-Number(p.ts||0)<450) return;
    window.__rouletteTeachPendingType=null;
    if (p.value) pushAction(p);
  }

  function scrollPos(target) {
    if (!target || target===document || target===document.documentElement || target===document.body) {
      return {x:Number(window.scrollX||0),y:Number(window.scrollY||0),scope:'window'};
    }
    return {
      x:Number(target.scrollLeft||0),
      y:Number(target.scrollTop||0),
      scope:'element'
    };
  }

  function scrollKey(target) {
    if (!target || target===document || target===document.documentElement || target===document.body)
      return '__WINDOW__';
    let d=plainDescribe(target);
    return [
      d.tag,d.id,d.testid,d.aria,(d.classes||[]).slice(0,3).join('.')
    ].join('|');
  }

  function flushScroll(force=false) {
    const p=window.__rouletteTeachPendingScroll;
    if (!p) return;
    if (!force && Date.now()-Number(p.ts||0)<300) return;
    window.__rouletteTeachPendingScroll=null;

    // Ignore tiny jitter.
    if (Math.abs(Number(p.dx||0))<4 && Math.abs(Number(p.dy||0))<4)
      return;

    pushAction(p);
  }

  if (!window.__rouletteTeachFreeInstalledV4) {
    window.__rouletteTeachFreeInstalledV4=true;
    window.__rouletteTeachQueue=[];
    window.__rouletteTeachPendingType=null;
    window.__rouletteTeachPendingScroll=null;
    window.__rouletteTeachScrollLast={};
    window.__rouletteUserScrollUntil=0;

    document.addEventListener('input', ev => {
      try {
        const el=ev.target;
        if (!isSafeSearchInput(el)) return;
        window.__rouletteTeachPendingType=inputDescribe(el);
      } catch(_) {}
    }, true);

    // Only a recent real user gesture authorizes recording a scroll.
    // Site-driven scrollTo/SPA rerender scrolls are deliberately ignored.
    document.addEventListener('wheel', () => {
      window.__rouletteUserScrollUntil=Date.now()+900;
    }, {capture:true,passive:true});

    document.addEventListener('touchmove', () => {
      window.__rouletteUserScrollUntil=Date.now()+900;
    }, {capture:true,passive:true});

    document.addEventListener('keydown', ev => {
      try {
        const k=String(ev.key||'');
        if (['PageDown','PageUp','Home','End','ArrowDown','ArrowUp',' '].includes(k))
          window.__rouletteUserScrollUntil=Date.now()+900;
      } catch(_) {}
    }, true);

    document.addEventListener('scroll', ev => {
      try {
        const target=(ev.target===document ? document : ev.target);
        const key=scrollKey(target);
        const cur=scrollPos(target);
        const prev=window.__rouletteTeachScrollLast[key];

        window.__rouletteTeachScrollLast[key]={x:cur.x,y:cur.y};

        if (!prev) return;

        // Update position for all scrolls, but RECORD only if a real user
        // wheel/touch/key scroll gesture happened recently.
        if (Date.now()>Number(window.__rouletteUserScrollUntil||0)) {
          window.__rouletteTeachPendingScroll=null;
          return;
        }

        const dx=cur.x-Number(prev.x||0);
        const dy=cur.y-Number(prev.y||0);
        if (Math.abs(dx)<1 && Math.abs(dy)<1) return;

        const base=plainDescribe(target);
        const pending=window.__rouletteTeachPendingScroll;

        // Aggregate a continuous gesture on the same scroll container.
        if (pending && pending.key===key && Date.now()-Number(pending.ts||0)<380) {
          pending.dx=Number(pending.dx||0)+dx;
          pending.dy=Number(pending.dy||0)+dy;
          pending.toX=cur.x;
          pending.toY=cur.y;
          pending.ts=Date.now();
        } else {
          flushScroll(true);
          base.action='scroll';
          base.scope=cur.scope;
          base.dx=dx;
          base.dy=dy;
          base.toX=cur.x;
          base.toY=cur.y;
          base.key=key;
          base.ts=Date.now();
          window.__rouletteTeachPendingScroll=base;
        }
      } catch(_) {}
    }, true);

    document.addEventListener('click', ev => {
      try {
        // Chronology: typing/scroll happens before the click that follows it.
        flushTyping(true);
        flushScroll(true);
        const d=describe(ev.target);
        if (d) {
          d.action='click';
          pushAction(d);
        }
      } catch(_) {}
    }, true);
  }

  flushTyping(false);
  flushScroll(false);

  const out=(window.__rouletteTeachQueue||[]).splice(0,40);
  return {
    actions:out,
    waiting:out.length===0,
    href:String(location.href||''),
    title:String(document.title||'')
  };
})()
"""


def build_learned_lobby_scan(steps, start_index=0):
    """Replay exactly one learned action at a time in strict order."""
    payload = json.dumps(steps or [], ensure_ascii=False)
    try:
        start_index = max(0, int(start_index or 0))
    except Exception:
        start_index = 0

    return r"""
(() => {
  const STEPS=__STEPS__;
  const START=__START__;
  const now=Date.now();
  const st=window.__rouletteLearnedActionsV5 || (window.__rouletteLearnedActionsV5={
    lastAction:0
  });

  function norm(x) {
    return String(x||'').replace(/\s+/g,' ').trim()
      .toLocaleUpperCase('tr-TR')
      .replace(/İ/g,'I').replace(/Ş/g,'S').replace(/Ğ/g,'G')
      .replace(/Ü/g,'U').replace(/Ö/g,'O').replace(/Ç/g,'C');
  }

  function visible(el) {
    try {
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      return r.width>5 && r.height>5 &&
             s.display!=='none' && s.visibility!=='hidden' &&
             Number(s.opacity||1)>.05;
    } catch(_) { return false; }
  }

  function classTokens(el) {
    return String(el.className||'').split(/\s+/).filter(Boolean);
  }

  function score(el,d,structural=false,requireVisible=true) {
    if (!el || !d) return -999;
    if (requireVisible && !visible(el)) return -999;

    const t=norm(el.innerText||el.textContent||'');
    const dt=norm(d.text||'');
    const testid=String(el.getAttribute && el.getAttribute('data-testid')||'');
    const aria=String(el.getAttribute && el.getAttribute('aria-label')||'');
    const placeholder=String(el.getAttribute && el.getAttribute('placeholder')||'');
    const name=String(el.getAttribute && el.getAttribute('name')||'');
    const id=String(el.id||'');
    const href=String(el.href || (el.getAttribute && el.getAttribute('href')) || '');
    const tag=String(el.tagName||'').toLowerCase();

    let s=0;
    if (d.testid && testid===d.testid) s+=18;
    if (d.aria && norm(aria)===norm(d.aria)) s+=14;
    if (d.placeholder && norm(placeholder)===norm(d.placeholder)) s+=13;
    if (d.name && name===d.name) s+=10;
    if (d.id && id===d.id) s+=18;

    if (d.href && href) {
      try {
        const a=new URL(d.href,location.href), b=new URL(href,location.href);
        if (a.pathname===b.pathname) s+=11;
        if (a.search && a.search===b.search) s+=4;
      } catch(_) {
        if (href===d.href) s+=11;
      }
    }

    if (!structural && dt) {
      if (t===dt) s+=12;
      else if (t && (t.includes(dt)||dt.includes(t))) s+=7;
    }

    if (d.tag && tag===d.tag) s+=2;

    const have=new Set(classTokens(el));
    let cm=0;
    for (const c of (d.classes||[])) if (have.has(c)) cm++;
    s+=Math.min(10,cm*2);

    if (visible(el)) s+=2;
    return s;
  }

  function candidatesFor(d,requireVisible=true) {
    let arr;
    if (d && d.action==='type') {
      arr=Array.from(document.querySelectorAll('input,textarea'));
    } else if (d && d.action==='scroll' && d.scope==='element') {
      arr=Array.from(document.querySelectorAll('div,section,main,aside,ul,ol'))
        .filter(el=>{
          try { return el.scrollHeight>el.clientHeight+8; }
          catch(_) { return false; }
        });
    } else {
      arr=Array.from(document.querySelectorAll(
        'a,button,[role="button"],[data-testid],[tabindex],div,span,input'
      ));
    }
    return requireVisible ? arr.filter(visible) : arr;
  }

  function best(d,structural=false,requireVisible=true) {
    let top=null, topScore=-999;
    for (const el of candidatesFor(d,requireVisible)) {
      const sc=score(el,d,structural,requireVisible);
      if (sc>topScore) { top=el; topScore=sc; }
    }
    const need=(d && d.action==='scroll') ? 5 :
               (d && d.action==='type') ? 8 :
               (structural ? 7 : 8);
    return topScore>=need ? {el:top,score:topScore} : null;
  }

  function setNativeValue(el,value) {
    try {
      const proto=(el.tagName||'').toLowerCase()==='textarea'
        ? HTMLTextAreaElement.prototype
        : HTMLInputElement.prototype;
      const desc=Object.getOwnPropertyDescriptor(proto,'value');
      if (desc && desc.set) desc.set.call(el,value);
      else el.value=value;
      try { el.focus(); } catch(_) {}
      el.dispatchEvent(new Event('input',{bubbles:true}));
      el.dispatchEvent(new Event('change',{bubbles:true}));
      return true;
    } catch(_) { return false; }
  }

  function clickElement(el) {
    if (!el) return false;
    try {
      try { el.focus(); } catch(_) {}
      el.click();
      return true;
    } catch(_) {
      try {
        const opts={bubbles:true,cancelable:true,view:window};
        el.dispatchEvent(new MouseEvent('mousedown',opts));
        el.dispatchEvent(new MouseEvent('mouseup',opts));
        el.dispatchEvent(new MouseEvent('click',opts));
        return true;
      } catch(__) {
        return false;
      }
    }
  }

  function wantedLabel(d) {
    if (!d) return '--';
    if (d.action==='type') return 'YAZ: '+String(d.value||'').slice(0,60);
    if (d.action==='scroll')
      return 'KAYDIR: '+String(Math.round(Number(d.dy||0)))+' px';
    return 'TIKLA: '+String(
      d.text||d.aria||d.testid||d.id||d.href||'öğe'
    ).slice(0,70);
  }

  const body=norm(document.body && document.body.innerText || '');
  const markers=['JEU 0','VOISINS','ORPHELINS','TIERS'];
  if (markers.filter(x=>body.includes(x)).length>=3)
    return {stage:'GAME_OPEN',active:true};

  if (!Array.isArray(STEPS)||STEPS.length<1)
    return {stage:'TEACH_REQUIRED',action:'WAIT'};

  if (START>=STEPS.length)
    return {stage:'ROUTE_DONE',action:'WAIT',start:START,total:STEPS.length};

  const d=STEPS[START]||{};
  const wanted=wantedLabel(d);

  if (now-st.lastAction<1050)
    return {
      stage:'COOLDOWN',action:'WAIT',
      start:START,total:STEPS.length,wanted:wanted
    };

  if (d.action==='scroll') {
    const dx=Number(d.dx||0), dy=Number(d.dy||0);

    if (d.scope==='window' || d.tag==='window') {
      try {
        const tx=Number(d.toX), ty=Number(d.toY);
        if (Number.isFinite(tx) && Number.isFinite(ty))
          window.scrollTo({left:tx,top:ty,behavior:'auto'});
        else
          window.scrollBy({left:dx,top:dy,behavior:'auto'});
        st.lastAction=now;
        return {
          stage:'LEARNED_SCROLL',action:'SCROLL',
          step_index:START,total:STEPS.length,
          text:(dy>=0?'+':'')+Math.round(dy)+' px'
        };
      } catch(_) {
        return {
          stage:'LEARNED_NOT_FOUND',action:'WAIT',
          start:START,total:STEPS.length,wanted:wanted
        };
      }
    }

    const scrollHit=best(d,false,false) || best(d,true,false);
    if (!scrollHit) {
      return {
        stage:'LEARNED_NOT_FOUND',action:'WAIT',
        start:START,total:STEPS.length,wanted:wanted
      };
    }

    try {
      const tx=Number(d.toX), ty=Number(d.toY);
      if (Number.isFinite(tx) && Number.isFinite(ty)) {
        if (typeof scrollHit.el.scrollTo==='function')
          scrollHit.el.scrollTo({left:tx,top:ty,behavior:'auto'});
        else {
          scrollHit.el.scrollLeft=tx;
          scrollHit.el.scrollTop=ty;
        }
      } else if (typeof scrollHit.el.scrollBy==='function') {
        scrollHit.el.scrollBy({left:dx,top:dy,behavior:'auto'});
      } else {
        scrollHit.el.scrollLeft=Number(scrollHit.el.scrollLeft||0)+dx;
        scrollHit.el.scrollTop=Number(scrollHit.el.scrollTop||0)+dy;
      }
      st.lastAction=now;
      return {
        stage:'LEARNED_SCROLL',action:'SCROLL',
        step_index:START,total:STEPS.length,
        text:(dy>=0?'+':'')+Math.round(dy)+' px',
        score:scrollHit.score
      };
    } catch(_) {
      return {
        stage:'LEARNED_NOT_FOUND',action:'WAIT',
        start:START,total:STEPS.length,wanted:wanted
      };
    }
  }

  let hit=best(d,false,true) || best(d,false,false);

  if (!hit && d.action!=='type' && START===STEPS.length-1)
    hit=best(d,true,true) || best(d,true,false);

  if (!hit) {
    return {
      stage:'LEARNED_NOT_FOUND',action:'WAIT',
      start:START,total:STEPS.length,wanted:wanted
    };
  }

  if (d.action==='type') {
    const value=String(d.value||'').slice(0,180);
    if (!value) {
      return {
        stage:'LEARNED_NOT_FOUND',action:'WAIT',
        start:START,total:STEPS.length,wanted:wanted
      };
    }

    if (String(hit.el.value||'')===value) {
      return {
        stage:'LEARNED_TYPE',action:'TYPE_DONE',
        step_index:START,total:STEPS.length,text:value.slice(0,80)
      };
    }

    if (setNativeValue(hit.el,value)) {
      st.lastAction=now;
      return {
        stage:'LEARNED_TYPE',action:'TYPE',
        step_index:START,total:STEPS.length,
        text:value.slice(0,80),score:hit.score
      };
    }

    return {
      stage:'LEARNED_NOT_FOUND',action:'WAIT',
      start:START,total:STEPS.length,wanted:wanted
    };
  }

  if (clickElement(hit.el)) {
    st.lastAction=now;
    return {
      stage:'LEARNED_STEP',action:'CLICK',
      step_index:START,total:STEPS.length,score:hit.score,
      text:(hit.el.innerText||hit.el.textContent||d.text||'').trim().slice(0,90)
    };
  }

  return {
    stage:'LEARNED_NOT_FOUND',action:'WAIT',
    start:START,total:STEPS.length,wanted:wanted
  };
})()
""".replace('__STEPS__', payload).replace('__START__', str(start_index))

LOBBY_NAV_SCAN = r"""
(() => {
  const now = Date.now();
  const st = window.__rouletteAutoLobbyNav || (window.__rouletteAutoLobbyNav = {
    lastClick: 0,
    favoritesClickedAt: 0,
    providerClickedAt: 0,
    liveClickedAt: 0,
    joinedAt: 0
  });

  function norm(x) {
    return String(x || '')
      .replace(/\\s+/g, ' ')
      .trim()
      .toLocaleUpperCase('tr-TR')
      .replace(/İ/g,'I').replace(/Ş/g,'S').replace(/Ğ/g,'G')
      .replace(/Ü/g,'U').replace(/Ö/g,'O').replace(/Ç/g,'C');
  }
  function visible(el) {
    try {
      const r=el.getBoundingClientRect();
      const s=getComputedStyle(el);
      return r.width>5 && r.height>5 && r.bottom>0 && r.right>0 &&
             r.top<innerHeight && r.left<innerWidth &&
             s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity||1)>.05;
    } catch(_) { return false; }
  }
  function selected(el) {
    try {
      const cls=norm(el.className || '');
      return el.getAttribute('aria-selected')==='true' ||
             el.getAttribute('aria-current')==='page' ||
             /(^| )(ACTIVE|SELECTED|CURRENT)( |$)/.test(cls);
    } catch(_) { return false; }
  }
  const reject = [
    'BAHIS','BET','SPIN','JETON','CHIP','TOPLAM BAHIS','AUTOMATIC PLAY',
    'OTOMATIK OYUN','REBET','DOUBLE','1 KOMSU','2 KOMSU','KOMSU'
  ];
  function isRejected(el) {
    const t=norm(el && (el.innerText || el.textContent || ''));
    return reject.some(x => t.includes(x));
  }
  function clickable(el) {
    if (!el) return null;
    let p=el;
    for (let i=0;i<5 && p;i++,p=p.parentElement) {
      const tag=(p.tagName||'').toLowerCase();
      const role=(p.getAttribute && p.getAttribute('role')) || '';
      if ((tag==='a'||tag==='button'||role==='button'||p.onclick||p.tabIndex>=0) && visible(p) && !isRejected(p)) return p;
    }
    return visible(el) && !isRejected(el) ? el : null;
  }
  function allTextNodes() {
    return Array.from(document.querySelectorAll('a,button,[role="button"],[data-testid],div,span,p'))
      .filter(visible);
  }
  function findByTerms(terms, exactFirst=true) {
    const nodes=allTextNodes();
    const wanted=terms.map(norm);
    let pool=[];
    for (const el of nodes) {
      if (isRejected(el)) continue;
      const t=norm(el.innerText || el.textContent || '');
      if (!t || t.length>180) continue;
      let rank=99;
      for (const w of wanted) {
        if (t===w) rank=Math.min(rank,0);
        else if (t.startsWith(w)) rank=Math.min(rank,1);
        else if (t.includes(w)) rank=Math.min(rank,2);
      }
      if (rank<99) {
        const c=clickable(el);
        if (c) {
          const r=c.getBoundingClientRect();
          pool.push({el:c,rank,top:r.top,left:r.left,text:t});
        }
      }
    }
    pool.sort((a,b)=>a.rank-b.rank || a.top-b.top || a.left-b.left);
    return pool.length ? pool[0] : null;
  }
  function clickOne(rec, action) {
    if (!rec || !rec.el) return null;
    if (now-st.lastClick<1100) return {stage:'COOLDOWN',action:'WAIT'};
    try {
      rec.el.scrollIntoView({block:'center',inline:'center'});
      rec.el.click();
      st.lastClick=now;
      return {stage:action,action:'CLICK',text:rec.text||norm(rec.el.innerText||rec.el.textContent||'')};
    } catch(_) { return null; }
  }

  const body=norm(document.body && document.body.innerText || '');
  const href=String(location.href||'');
  const title=String(document.title||'');

  // Hard stop inside a real roulette table. No casino/bet control is touched here.
  const gameMarkers=['JEU 0','VOISINS','ORPHELINS','TIERS'];
  const markerCount=gameMarkers.filter(x=>body.includes(x)).length;
  if (markerCount>=3) {
    return {stage:'GAME_OPEN',active:true,href,title,markerCount};
  }

  // Provider lobby clue from the user's screen and common Pragmatic labels.
  const providerLobby = body.includes('TURKISH TABLES LOBBY') ||
                        body.includes('PRAGMATIC PLAY') ||
                        body.includes('PRAGMATICPLAY');

  // 1) In Pragmatic/provider lobby -> Favorites.
  if (providerLobby) {
    const fav=findByTerms(['FAVORILER','FAVORITES','FAVOURITES']);
    if (fav) {
      if (!selected(fav.el) && now-st.favoritesClickedAt>1600) {
        const out=clickOne(fav,'FAVORITES');
        if (out && out.action==='CLICK') st.favoritesClickedAt=now;
        if (out) return {...out,href,title};
      }
      // selected/active favorites or we clicked it recently: wait for cards to settle.
      if (selected(fav.el) || now-st.favoritesClickedAt<7000) {
        if (now-st.favoritesClickedAt && now-st.favoritesClickedAt<1300)
          return {stage:'FAVORITES_WAIT',action:'WAIT',href,title};

        // Prefer an explicit JOIN/PLAY button inside favorite tables.
        const join=findByTerms(['KATIL','JOIN','OYNA','PLAY']);
        if (join && now-st.joinedAt>1800) {
          const out=clickOne(join,'FIRST_FAVORITE');
          if (out && out.action==='CLICK') st.joinedAt=now;
          if (out) return {...out,href,title};
        }

        // Otherwise click the first visible game/table card in visual order.
        const sels=[
          '[data-testid*="game"]','[data-testid*="table"]',
          '[class*="game-card"]','[class*="GameCard"]','[class*="gameCard"]',
          '[class*="table-card"]','[class*="TableCard"]','[class*="tableCard"]',
          '[class*="game-tile"]','[class*="GameTile"]'
        ];
        const cards=[];
        for (const sel of sels) {
          for (const el of document.querySelectorAll(sel)) {
            if (!visible(el) || isRejected(el)) continue;
            const t=norm(el.innerText||el.textContent||'');
            if (t.includes('FAVORILER')||t.includes('FAVORITES')) continue;
            const c=clickable(el);
            if (!c) continue;
            const r=c.getBoundingClientRect();
            if (r.width<70 || r.height<45) continue;
            cards.push({el:c,top:r.top,left:r.left,text:t});
          }
        }
        cards.sort((a,b)=>a.top-b.top || a.left-b.left);
        if (cards.length && now-st.joinedAt>1800) {
          const out=clickOne(cards[0],'FIRST_FAVORITE');
          if (out && out.action==='CLICK') st.joinedAt=now;
          if (out) return {...out,href,title};
        }
        return {stage:'FAVORITES_EMPTY',action:'WAIT',href,title};
      }
    }
  }

  // 2) Live casino page -> Pragmatic Play provider.
  const pragmatic=findByTerms(['PRAGMATIC PLAY','PRAGMATIC']);
  if (pragmatic && now-st.providerClickedAt>1800) {
    const out=clickOne(pragmatic,'PRAGMATIC');
    if (out && out.action==='CLICK') st.providerClickedAt=now;
    if (out) return {...out,href,title};
  }

  // 3) Main casino page -> Live Casino.
  const live=findByTerms(['CANLI CASINO','LIVE CASINO']);
  if (live && now-st.liveClickedAt>1800) {
    const out=clickOne(live,'LIVE_CASINO');
    if (out && out.action==='CLICK') st.liveClickedAt=now;
    if (out) return {...out,href,title};
  }

  return {stage:'SEARCHING',action:'WAIT',href,title,providerLobby};
})()
"""


RECOVERY_SCAN = f"""
(() => {{
  function norm(x) {{
    return String(x || '').replace(/\\s+/g, ' ').trim().toLocaleLowerCase('tr-TR');
  }}
  function visible(el) {{
    try {{
      const r=el.getBoundingClientRect();
      const s=getComputedStyle(el);
      return r.width>2 && r.height>2 && s.display!=='none' && s.visibility!=='hidden' && Number(s.opacity||1)>.05;
    }} catch(_) {{ return false; }}
  }}

  const text = norm((document.body && document.body.innerText) || '').slice(0, 300000);
  const phrases = {json.dumps(RECOVERY_PHRASES, ensure_ascii=False)};
  const buttonWords = {json.dumps(RECOVERY_BUTTON_WORDS, ensure_ascii=False)};
  const errorWords = {json.dumps(RECOVERY_ERROR_WORDS, ensure_ascii=False)};

  const phraseHits = phrases.filter(p => text.includes(norm(p)));
  const errorHit = errorWords.some(w => text.includes(norm(w)));
  const buttonHits = [];

  for (const el of document.querySelectorAll('button,[role="button"],a')) {{
    if (!visible(el)) continue;
    const t = norm(el.innerText || el.textContent || '');
    if (!t || t.length > 80) continue;
    if (buttonWords.some(w => t === norm(w) || t.includes(norm(w)))) buttonHits.push(t);
    if (buttonHits.length >= 8) break;
  }}

  const score = (phraseHits.length ? 3 : 0) + (buttonHits.length ? 2 : 0) + (errorHit ? 1 : 0);
  const hit = (phraseHits.length > 0 || (buttonHits.length > 0 && errorHit)) && score >= 3;

  return {{
    hit: !!hit,
    score,
    phrases: phraseHits.slice(0,4),
    buttons: buttonHits.slice(0,4),
    href: String(location.href || ''),
    title: String(document.title || '')
  }};
}})()
"""


class RouletteState:
    def __init__(self):
        self.lock = threading.RLock()
        self.chrome_connected = False
        self.roulette_seen = False
        self.status = "Chrome bekleniyor"
        self.history = []
        self.hot = []
        self.cold = []
        self.table_name = ""
        self.source = "-"
        self.last_update = 0.0
        self.last_live_result_number = None
        self.last_live_result_time = 0.0

        self.pragmatic_table_id = ""
        self.pragmatic_operator_game_id = ""
        self.pragmatic_theme_code = ""
        self.direct_history_status = "PRAGMATIC DIRECT: endpoint bekleniyor"
        self.direct_history_count = 0
        self.direct_history_last_update = 0.0

        # V2.9.1 lightweight unattended recovery watchdog.
        self.restart_requested = False
        self.restart_reason = ""
        self.autorecover_status = "AUTO KURTARMA: HAZIR"
        self.autorecover_count = 0
        self.autolobby_status = "ÖĞREN: ilk kullanımda BAŞLAT → yolu göster → BİTİR"

        # Self-learning / validation.
        self.session_results = []  # chronological
        self.expert_loss = {name: 0.0 for name in EXPERT_NAMES}
        self.expert_trials = 0
        self.expert_hits = {
            name: {"trials": 0, "exact": 0, "top5": 0, "neighbor5": 0}
            for name in EXPERT_NAMES
        }
        self.pending_prediction = None

        # Same-table out-of-sample model evaluation cache.
        self.walkforward_cache_key = None
        self.walkforward_cache = {}

        self.validation = {
            "trials": 0,
            "exact": 0,
            "side4": 0,
            "top5": 0,
            "neighbor5": 0,
            "region": 0,
        }
        self.validation_history = []

        # UI-only chronological comparison batch. It never feeds prediction.
        self.display_compare_batch = []
        self.neighbor_display_batch = []  # K2
        self.neighbor_stats_total = {       # K2
            "trials": 0,
            "net_hits": 0,
            "backup_hits": 0,
            "any_hits": 0,
            "multi_hits": 0,
            "coverage_sum": 0,
        }

        self.neighbor1_display_batch = []
        self.neighbor1_stats_total = {
            "trials": 0,
            "net_hits": 0,
            "backup_hits": 0,
            "any_hits": 0,
            "multi_hits": 0,
            "coverage_sum": 0,
        }

        # Last completed round shown beside the current NET prediction.
        # "won" means NET + 4 YEDEK package had at least one neighbor hit.
        self.last_neighbor1_package = None
        self.last_neighbor2_package = None

        self.score_error_status = "OK"
        self.locked_live = {
            "version": "V2.9 FINAL CORE",
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "rows": [],
            "frozen": False,
        }

        self.source_hits = {
            name: {
                "trials": 0,
                "exact": 0,
                "top5": 0,
            }
            for name in SOURCE_NAMES
        }

        self.data_dir = persistent_data_dir()
        self.legacy_learning_path = os.path.join(self.data_dir, "roulette_learning.json")
        self.legacy_log_path = os.path.join(self.data_dir, "roulette_prediction_log.jsonl")
        self.learning_path, self.log_path = table_storage_paths(self.data_dir, "default")
        self.loaded_table = None

        self.external_history = []
        self.external_source = "PUBLIC WEB: KAPALI • PRAGMATIC DIRECT"
        self.external_table = ""
        self.external_last_fetch = 0.0
        self.public_long_history = []
        self.public_long_source = "PUBLIC WEB UZUN: KAPALI"
        self.public_long_table = ""
        self.web_match_run = 0
        self.web_verified = False

        # Directly scraped from the game's own SON 500 panel.
        self.table_history_500 = []
        self.table_history_source = "MASA SON500: bekleniyor"
        self.table_history_table = ""
        self.table_history_last_update = 0.0

        self.table_long_history = []
        self.table_long_source = "UZUN MASA ARŞİVİ: bekleniyor"
        self.table_long_table = ""

        self.app_dir = os.path.dirname(os.path.abspath(__file__))

        # Multi-table global pool: combines all collected Pragmatic tableId
        # banks (with -1 boundary separators so cross-table edges never create
        # false transitions).
        self.imported_history = []
        self.imported_source = "ORTAK HAVUZ: masa verisi bekleniyor"
        self.imported_last_check = 0.0
        self.imported_table = ""
        self._pool_disk_cache = {}
        self._pool_memory_tables = {}
        self._memory_table500 = {}
        self._pool_last_disk_scan = 0.0
        self._last_pool_rebuild_ts = 0.0
        self._last_registry_save_ts = 0.0
        self._pool_dirty = True
        self._cached_pool_seq = []
        self._cached_pool_tables = 0
        self._cached_pool_spins = 0

        self.registry_path = os.path.join(
            self.data_dir,
            "pragmatic_table_registry.json",
        )
        self.table_registry = self._load_table_registry()
        self.collector_discovered = 0
        self.collector_refreshed = 0
        self.collector_last_cycle = 0.0
        self.table_scan_status = "MASA TARAMA: hazır • yeniden eğitim gerekmez"
        self.background_status = self._bank_status_text()

        self._external_thread = threading.Thread(target=self._external_loop, daemon=True)
        self._external_thread.start()

    def _refresh_imported_history(self, force=False):
        self._pool_dirty = True
        if force:
            self._pool_last_disk_scan = 0.0
        self._rebuild_multi_table_pool(force_disk=force)

    def _rebuild_multi_table_pool(self, force_disk=False):
        now = time.time()
        scan_disk = (
            force_disk
            or not self._pool_disk_cache
            or (now - float(self._pool_last_disk_scan or 0.0) >= 10.0)
        )
        if scan_disk:
            self._pool_last_disk_scan = now
            seen_paths = set()
            try:
                names = os.listdir(self.data_dir)
            except Exception:
                names = []

            for fname in names:
                is_long = fname.startswith("table_long_archive_") and fname.endswith(".json")
                is_500 = fname.startswith("table_history500_") and fname.endswith(".json")
                if not (is_long or is_500):
                    continue
                fpath = os.path.join(self.data_dir, fname)
                seen_paths.add(fpath)
                try:
                    mtime = os.path.getmtime(fpath)
                except Exception:
                    continue
                cached = self._pool_disk_cache.get(fpath)
                if cached and cached[0] == mtime:
                    continue
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    vals = data.get("results_newest_first", [])
                    raw_clean = [
                        int(x) for x in vals
                        if isinstance(x, int) and 0 <= x <= 36
                    ]
                    tkey = (
                        fname[len("table_long_archive_"):-5]
                        if is_long
                        else fname[len("table_history500_"):-5]
                    )
                    if is_long and len(raw_clean) >= 40:
                        clean = load_table_long_archive(self.data_dir, tkey)
                        try:
                            mtime = os.path.getmtime(fpath)
                        except Exception:
                            pass
                    else:
                        clean = sanitize_long_archive(raw_clean) if len(raw_clean) >= 40 else []
                    if len(clean) >= 40:
                        self._pool_disk_cache[fpath] = (mtime, tkey, clean)
                except Exception:
                    continue

            for stale in list(self._pool_disk_cache):
                if stale not in seen_paths:
                    self._pool_disk_cache.pop(stale, None)

        by_key = {}
        key_mtime = {}
        key_is_long = {}
        for fpath, (mtime, tkey, seq) in self._pool_disk_cache.items():
            if len(seq) < 40:
                continue
            is_long_file = os.path.basename(fpath).startswith("table_long_archive_")
            prev = by_key.get(tkey)
            prev_long = key_is_long.get(tkey, False)
            if (
                prev is None
                or (is_long_file and not prev_long)
                or (is_long_file == prev_long and len(seq) > len(prev))
                or (is_long_file == prev_long and len(seq) == len(prev) and mtime > key_mtime.get(tkey, 0.0))
            ):
                by_key[tkey] = list(seq)
                key_mtime[tkey] = float(mtime or 0.0)
                key_is_long[tkey] = is_long_file

        for tkey, seq in (getattr(self, "_pool_memory_tables", {}) or {}).items():
            if len(seq) >= 40 and tkey.startswith("pragmatic_") and "http_" not in tkey and "https_" not in tkey:
                prev = by_key.get(tkey)
                if prev is None or len(seq) >= len(prev):
                    by_key[tkey] = list(seq)
                    key_mtime[tkey] = now

        def _all_grams(seq, width=12):
            n = len(seq)
            if n < width:
                return {tuple(seq)}
            return {tuple(seq[i:i + width]) for i in range(n - width + 1)}

        def _probe_grams(seq, width=12, step=16):
            n = len(seq)
            if n < width:
                return (tuple(seq),)
            return tuple(tuple(seq[i:i + width]) for i in range(0, n - width + 1, step))

        def _has_real_reg_name(k):
            if not isinstance(self.table_registry, dict) or not k.startswith("pragmatic_"):
                return 1
            tid_k = k[len("pragmatic_"):]
            row_k = self.table_registry.get(tid_k) or {}
            dn = str(row_k.get("display_name") or "").strip().lower()
            src = str(row_k.get("last_source") or "").strip()
            if src in ("AKTİF SON500", "AKTİF MASA SON500", "CANLI SPIN", "ARKA PLAN SON500", "ARKA PLAN statisticHistory"):
                return 2
            if not dn or dn in ("roulette", "rulet") or dn.startswith(("http://", "https://", "client.", "collector_")) or dn == tid_k.lower():
                return 1
            return 0

        def _key_sort(k):
            is_url = 1 if ("http_" in k or "https_" in k) else 0
            is_prag = 0 if (k.startswith("pragmatic_") and not is_url) else 1
            real_name_rank = _has_real_reg_name(k)
            # Prefer real named collector tables first so generic/active duplicates get deduplicated against them
            return (is_url, is_prag, real_name_rank, -len(by_key.get(k, [])), -key_mtime.get(k, 0.0), k)

        ordered_keys = sorted(by_key, key=_key_sort)
        unique_seqs = []
        unique_keys = set()
        duplicate_keys = set()
        combined_existing_grams = set()
        has_pragmatic_keys = any(k.startswith("pragmatic_") and "http_" not in k and "https_" not in k for k in ordered_keys)
        for k in ordered_keys:
            seq = by_key[k]
            if len(seq) < 40 or is_betting_grid_artifact(seq[:50]) or "http_" in k or "https_" in k:
                duplicate_keys.add(k)
                continue
            # Only include pragmatic_<tableId> collector archives in ORTAK HAVUZ & MASA BANKASI
            if has_pragmatic_keys and not k.startswith("pragmatic_"):
                duplicate_keys.add(k)
                continue
            if isinstance(self.table_registry, dict) and k.startswith("pragmatic_"):
                tid_k = k[len("pragmatic_"):]
                row_k = self.table_registry.get(tid_k) or {}
                src_k = str(row_k.get("last_source") or "").strip()
                dn_k = str(row_k.get("display_name") or "").strip().lower()
                if (
                    src_k in ("AKTİF SON500", "AKTİF MASA SON500", "CANLI SPIN", "ARKA PLAN SON500", "ARKA PLAN statisticHistory")
                    or dn_k.startswith(("http://", "https://"))
                    or (src_k == "CLICK SCAN statisticHistory" and dn_k in ("roulette", "rulet"))
                ):
                    duplicate_keys.add(k)
                    continue
            probes = _probe_grams(seq, 12, 16)
            if any(p in combined_existing_grams for p in probes):
                duplicate_keys.add(k)
                continue
            unique_seqs.append(seq)
            unique_keys.add(k)
            combined_existing_grams.update(_all_grams(seq, 12))

        # Keep MASA BANKASI (table_registry) 1-to-1 synchronized with ORTAK HAVUZ
        # deduplication: remove ONLY actual 12-gram duplicates or non-collector entries.
        if isinstance(self.table_registry, dict):
            reg_changed = False
            seen_reg_keys = set()
            for tid in list(self.table_registry.keys()):
                ident = "pragmatic_" + re.sub(r"[^A-Za-z0-9_-]+", "_", str(tid)).strip("_")
                rk = safe_table_key(ident)
                row = self.table_registry.get(tid) or {}
                src_row = str(row.get("last_source") or "").strip()
                dn_row = str(row.get("display_name") or "").strip().lower()
                if (
                    rk in duplicate_keys
                    or rk in seen_reg_keys
                    or (by_key and rk not in unique_keys)
                    or src_row in ("AKTİF SON500", "AKTİF MASA SON500", "CANLI SPIN", "ARKA PLAN SON500", "ARKA PLAN statisticHistory")
                    or dn_row.startswith(("http://", "https://"))
                    or (src_row == "CLICK SCAN statisticHistory" and dn_row in ("roulette", "rulet"))
                ):
                    self.table_registry.pop(tid, None)
                    reg_changed = True
                    continue
                seen_reg_keys.add(rk)
                if rk in by_key:
                    real_len = len(by_key[rk])
                    if int(row.get("long_count", 0) or 0) != real_len:
                        row["long_count"] = real_len
                        self.table_registry[tid] = row
                        reg_changed = True

            # Restore any unique pragmatic_ table in unique_keys that is missing from table_registry
            for rk in unique_keys:
                if rk in seen_reg_keys or not rk.startswith("pragmatic_"):
                    continue
                restored_tid = rk[len("pragmatic_"):]
                restored_name = restored_tid
                restored_source = "SEKMELİ TOPLA sağ-alt SON500"
                try:
                    p500 = os.path.join(self.data_dir, f"table_history500_{rk}.json")
                    if os.path.exists(p500):
                        with open(p500, "r", encoding="utf-8") as f5:
                            meta5 = json.load(f5) or {}
                        restored_tid = str(meta5.get("table_id") or restored_tid).strip() or restored_tid
                        restored_name = str(meta5.get("display_name") or restored_name).strip() or restored_tid
                except Exception:
                    pass
                seq_len = len(by_key.get(rk, []))
                self.table_registry[restored_tid] = {
                    "table_id": restored_tid,
                    "display_name": restored_name[:90],
                    "last_update": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_update_epoch": key_mtime.get(rk, now),
                    "long_count": seq_len,
                    "last_source": restored_source,
                }
                seen_reg_keys.add(rk)
                reg_changed = True

            if reg_changed:
                self._cached_bank_rows_ts = 0.0
                self._save_table_registry()
                self.background_status = self._bank_status_text()

        pooled = []
        for idx, seq in enumerate(unique_seqs):
            if idx > 0:
                pooled.append(-1)
            pooled.extend(seq)

        self._cached_pool_seq = pooled
        self._cached_pool_tables = len(unique_seqs)
        self._cached_pool_spins = sum(len(s) for s in unique_seqs)
        self.imported_history = pooled
        self.imported_source = (
            f"ORTAK HAVUZ: {self._cached_pool_tables} masa • {self._cached_pool_spins} spin"
            if self._cached_pool_spins
            else "ORTAK HAVUZ: masa verisi bekleniyor"
        )
        self._last_pool_rebuild_ts = now
        self._pool_dirty = False
        return pooled

    def multi_table_pool_history(self):
        now = time.time()
        if (
            not self._cached_pool_seq
            or (self._pool_dirty and (now - float(getattr(self, "_last_pool_rebuild_ts", 0.0) or 0.0) >= 2.5))
            or (now - float(self._pool_last_disk_scan or 0.0) >= 15.0)
        ):
            self._rebuild_multi_table_pool()
        return list(self._cached_pool_seq)

    def _load_table_registry(self):
        try:
            if not os.path.exists(self.registry_path):
                return {}
            with open(self.registry_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                cleaned = {}
                for tid, row in raw.items():
                    if not isinstance(row, dict):
                        continue
                    lc = int(row.get("long_count", 0) or 0)
                    name_raw = str(row.get("display_name") or "").strip()
                    name_up = name_raw.upper()
                    src_raw = str(row.get("last_source") or "").strip()
                    if lc < 40:
                        continue
                    if src_raw in (
                        "AKTİF SON500",
                        "AKTİF MASA SON500",
                        "CANLI SPIN",
                        "ARKA PLAN SON500",
                        "ARKA PLAN statisticHistory",
                    ):
                        continue
                    if name_raw.lower().startswith(("http://", "https://")):
                        continue
                    if src_raw == "CLICK SCAN statisticHistory" and name_raw.lower() in ("roulette", "rulet"):
                        continue
                    if any(str(b).upper() in name_up for b in TAB_WALK_BLOCKED_TABLE_LABELS):
                        continue
                    cleaned[tid] = row
                return cleaned
        except Exception:
            pass
        return {}

    def _save_table_registry(self, force=False):
        now = time.time()
        if not force and (now - float(getattr(self, "_last_registry_save_ts", 0.0) or 0.0) < 2.5):
            return
        self._last_registry_save_ts = now
        try:
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(
                    self.table_registry,
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception:
            pass

    def _bank_status_text(self, extra=""):
        rows = self.table_registry if isinstance(self.table_registry, dict) else {}
        bank_count = len(rows)
        total = 0
        for row in rows.values():
            try:
                total += max(0, int((row or {}).get("long_count", 0)))
            except Exception:
                pass

        now = time.time()
        refreshed = 0
        active = 0
        for row in rows.values():
            try:
                age = now - float((row or {}).get("last_update_epoch", 0.0) or 0.0)
                if 0 <= age <= 300.0:
                    refreshed += 1
                if 0 <= age <= 90.0:
                    active += 1
            except Exception:
                pass
        self.collector_refreshed = refreshed
        txt = (
            f"MASA BANKASI: {bank_count} kayıt • {refreshed} son 5dk güncel"
            f" • {total} spin"
        )
        if extra:
            txt += f" • {extra}"
        return txt

    def clear_table_registry(self, reason=""):
        """Clear only the visible table bank registry; archives stay on disk."""
        with self.lock:
            self.table_registry = {}
            self.collector_discovered = 0
            self.collector_refreshed = 0
            self._save_table_registry()
            self.background_status = self._bank_status_text(reason or "banka sıfırlandı")

    def clear_all_past_table_data(self, reason=""):
        """
        Completely delete all previously scanned table archives (MASA BANKASI,
        ORTAK HAVUZ, SON500 and UZUN ARŞİV files on disk and in memory) so fresh
        table scans start 100% clean.
        """
        folders = {self.data_dir, os.path.dirname(os.path.abspath(__file__))}
        removed_files = 0
        for folder in folders:
            if not folder or not os.path.isdir(folder):
                continue
            try:
                for fname in os.listdir(folder):
                    if (
                        fname.startswith("table_long_archive_")
                        or fname.startswith("table_history500_")
                        or fname.startswith("table_history_500_")
                        or fname == "table_registry.json"
                    ) and fname.endswith(".json"):
                        try:
                            os.remove(os.path.join(folder, fname))
                            removed_files += 1
                        except Exception:
                            pass
            except Exception:
                pass

        with self.lock:
            self.table_registry = {}
            self._cached_bank_rows = []
            self._cached_bank_rows_ts = 0.0
            self._memory_table500 = {}
            self._pool_memory_tables = {}
            self._pool_disk_cache = {}
            self._cached_pool_seq = []
            self._cached_pool_tables = 0
            self._cached_pool_spins = 0
            self._cached_pool_meta = {"tables": 0, "spins": 0, "dup_tables": 0}
            self._pool_dirty = False
            self._last_pool_rebuild_ts = time.time()
            self._pool_last_disk_scan = time.time()
            self._last_pool_disk_scan_ts = 0.0
            self.imported_history = []
            self.imported_source = "ORTAK HAVUZ: geçmiş masa verileri silindi • yeni tarama bekleniyor"
            self.table_history_500 = []
            self.table_long_history = []
            self.direct_history_count = 0
            self.table_history_source = "MASA SON500: geçmiş veriler silindi"
            self.table_long_source = "UZUN MASA ARŞİVİ: 0"
            self.archive_source = "ORTAK HAVUZ: geçmiş masa verileri silindi • yeni tarama bekleniyor"
            self.collector_discovered = 0
            self.collector_refreshed = 0
            self.walkforward_cache_key = None
            self.walkforward_cache_value = {}
            self._save_table_registry(force=True)
            self.background_status = (
                f"MASA BANKASI: geçmiş masa verileri silindi ({removed_files} dosya) • 0 spin"
            )
            if self.history:
                self.pending_prediction = self._make_prediction(self.history)
        return removed_files

    def mark_table_discovered(self, table_id, display_name="", source="LOBI"):
        tid = str(table_id or "").strip()
        if not tid:
            return
        name_up = str(display_name or "").upper()
        if any(str(b).upper() in name_up for b in TAB_WALK_BLOCKED_TABLE_LABELS):
            return
        with self.lock:
            # Do not insert unvisited 0-spin lobby cards into MASA BANKASI unless
            # the user explicitly enabled manual API teach mode.
            if tid not in self.table_registry and str(source or "") != "API ÖĞREN":
                return
            row = dict(self.table_registry.get(tid, {}) or {})
            row["table_id"] = tid
            if display_name:
                row["display_name"] = str(display_name)
            row.setdefault("first_seen", time.strftime("%Y-%m-%d %H:%M:%S"))
            row["last_discovered"] = time.strftime("%Y-%m-%d %H:%M:%S")
            row["discovery_source"] = str(source or "LOBI")
            row.setdefault("long_count", 0)
            self.table_registry[tid] = row
            self.collector_discovered = len(self.table_registry)
            self._save_table_registry()
            self.background_status = self._bank_status_text()

    def mark_table_attempt(self, table_id, ok=False, error=""):
        tid = str(table_id or "").strip()
        if not tid:
            return
        with self.lock:
            if tid not in self.table_registry:
                return
            row = dict(self.table_registry.get(tid, {}) or {})
            row["table_id"] = tid
            row["last_attempt"] = time.strftime("%Y-%m-%d %H:%M:%S")
            row["last_attempt_epoch"] = time.time()
            if error:
                row["last_error"] = str(error)[:160]
            elif ok:
                row.pop("last_error", None)
            self.table_registry[tid] = row
            self._save_table_registry()

    def _update_table_registry(
        self,
        table_id,
        display_name="",
        long_count=0,
        source="",
        theme_code="",
        operator_game_id="",
        save_disk=True,
    ):
        tid = str(table_id or "").strip()
        if not tid:
            return
        src_str = str(source or "").strip()
        if src_str in (
            "AKTİF SON500",
            "AKTİF MASA SON500",
            "CANLI SPIN",
            "ARKA PLAN SON500",
            "ARKA PLAN statisticHistory",
        ):
            return

        row = dict(self.table_registry.get(tid, {}) or {})
        row["table_id"] = tid
        raw_dn = str(display_name or "").strip()
        canon_dn = canonical_pragmatic_table_name(raw_dn, fallback="")
        if canon_dn:
            raw_dn = canon_dn
        norm_dn = raw_dn.lower()
        is_generic_dn = (
            not norm_dn
            or norm_dn in ("roulette", "rulet", "pragmatic play", "pragmatic play lobby", "lobby", "lobi")
            or norm_dn.startswith(("http://", "https://", "client.", "games."))
            or "/desktop/" in norm_dn
            or norm_dn == tid.lower()
        )
        prev_dn = str(row.get("display_name") or "").strip()
        prev_canon = canonical_pragmatic_table_name(prev_dn, fallback="")
        if prev_canon:
            prev_dn = prev_canon
            row["display_name"] = prev_dn
        prev_norm = prev_dn.lower()
        prev_is_real = bool(
            prev_dn
            and prev_norm not in ("roulette", "rulet", "pragmatic play", "pragmatic play lobby", "lobby", "lobi")
            and not prev_norm.startswith(("http://", "https://", "client.", "games.", "collector_"))
            and prev_norm != tid.lower()
        )
        if raw_dn and not is_generic_dn:
            row["display_name"] = raw_dn
        elif not prev_is_real and raw_dn and not norm_dn.startswith(("http://", "https://")):
            row["display_name"] = raw_dn
        elif not row.get("display_name"):
            row["display_name"] = tid
        if theme_code:
            row["theme_code"] = str(theme_code)
        if operator_game_id:
            row["operator_game_id"] = str(operator_game_id)

        try:
            row["long_count"] = max(
                int(row.get("long_count", 0) or 0),
                int(long_count or 0),
            )
        except Exception:
            row["long_count"] = int(long_count or 0)

        if source:
            row["last_source"] = str(source)

        row["last_seen"] = time.strftime("%Y-%m-%d %H:%M:%S")
        row["last_update"] = row["last_seen"]
        row["last_update_epoch"] = time.time()
        row["refresh_count"] = int(row.get("refresh_count", 0) or 0) + 1
        row.pop("last_error", None)
        self.table_registry[tid] = row
        self._cached_bank_rows_ts = 0.0
        if save_disk:
            self._save_table_registry()
        self.background_status = self._bank_status_text()

    def _saved_table500(self, identity):
        try:
            key = safe_table_key(identity or "roulette")
            mem = getattr(self, "_memory_table500", None)
            if isinstance(mem, dict) and key in mem:
                return list(mem[key])
            path = os.path.join(
                self.data_dir,
                f"table_history500_{key}.json",
            )
            if not os.path.exists(path):
                return []
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            vals = data.get("results_newest_first", [])
            out = [
                int(x) for x in vals
                if isinstance(x, int) and 0 <= x <= 36
            ][:500]
            if isinstance(mem, dict):
                mem[key] = list(out)
            return out
        except Exception:
            return []

    def _normalize_background_window(self, clean, previous):
        clean = list(clean or [])
        previous = list(previous or [])
        if len(clean) < 10 or len(previous) < 10:
            return clean

        gram = 8
        ref_grams = {
            tuple(previous[i:i + gram])
            for i in range(len(previous) - gram + 1)
        }
        fwd_hits = sum(
            1 for i in range(len(clean) - gram + 1)
            if tuple(clean[i:i + gram]) in ref_grams
        )
        rev = list(reversed(clean))
        rev_hits = sum(
            1 for i in range(len(rev) - gram + 1)
            if tuple(rev[i:i + gram]) in ref_grams
        )
        if rev_hits >= 2 and rev_hits > fwd_hits * 2:
            return rev
        return clean

    def store_background_table_history(
        self,
        results,
        table_id,
        display_name="",
        source_label="ARKA PLAN SON500",
    ):
        """
        Save another table's SON500 into its own tableId bank without changing
        the active table, prediction, validation, or current UI state.
        """
        tid = str(table_id or "").strip()
        if not tid:
            return 0
        name_up = str(display_name or "").upper()
        if any(str(b).upper() in name_up for b in TAB_WALK_BLOCKED_TABLE_LABELS):
            return 0

        clean = []
        for x in results or []:
            try:
                n = int(x)
            except Exception:
                continue
            if 0 <= n <= 36:
                clean.append(n)

        if len(clean) < 20 or is_betting_grid_artifact(clean):
            return 0
        if "SON500" in str(source_label or "").upper() and len(clean) < 40:
            return 0
        clean = clean[:500]

        identity = "pragmatic_" + re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            tid,
        ).strip("_")
        key = safe_table_key(identity)

        clean_grams_12 = {
            tuple(clean[i:i + 12])
            for i in range(max(0, min(80, len(clean)) - 11))
        } if len(clean) >= 12 else set()
        disp_norm = str(display_name or "").strip().upper()
        migrated_long = []

        with self.lock:
            for other_tid in list(self.table_registry.keys()):
                if other_tid == tid:
                    continue
                other_row = self.table_registry.get(other_tid) or {}
                other_disp = str(other_row.get("display_name") or "").strip().upper()
                other_ident = "pragmatic_" + re.sub(r"[^A-Za-z0-9_-]+", "_", str(other_tid)).strip("_")
                other_key = safe_table_key(other_ident)
                other_seq = self._pool_memory_tables.get(other_key) or []
                other_grams_12 = {
                    tuple(other_seq[i:i + 12])
                    for i in range(max(0, min(80, len(other_seq)) - 11))
                } if len(other_seq) >= 12 else set()
                same_table_match = bool(
                    (clean_grams_12 and other_grams_12 and (clean_grams_12 & other_grams_12))
                    or (
                        disp_norm
                        and other_disp
                        and disp_norm == other_disp
                        and (tid.startswith("collector_") or str(other_tid).startswith("collector_"))
                    )
                )
                if not same_table_match:
                    continue
                if tid.startswith("collector_") and not str(other_tid).startswith("collector_"):
                    tid = str(other_tid)
                    identity = other_ident
                    key = other_key
                    if (
                        not display_name
                        or display_name == tid
                        or str(display_name).strip().lower() in ("roulette", "rulet")
                    ) and other_row.get("display_name"):
                        display_name = str(other_row.get("display_name"))
                    break
                elif str(other_tid).startswith("collector_") and not tid.startswith("collector_"):
                    old_row = self.table_registry.pop(other_tid, None) or {}
                    popped_seq = self._pool_memory_tables.pop(other_key, None) or []
                    if len(popped_seq) > len(migrated_long):
                        migrated_long = list(popped_seq)
                    self._memory_table500.pop(other_key, None)
                    if (
                        not display_name
                        or display_name == tid
                        or str(display_name).strip().lower() in ("roulette", "rulet")
                    ) and old_row.get("display_name"):
                        display_name = str(old_row.get("display_name"))

            previous = list(self._memory_table500.get(key) or [])
            long_hist = list(self._pool_memory_tables.get(key) or [])

        if not previous:
            previous = self._saved_table500(identity)
        if not long_hist:
            long_hist = load_table_long_archive(
                self.data_dir,
                identity,
            )
        if not long_hist and migrated_long:
            long_hist = list(migrated_long)

        # CRITICAL: Never create a brand-new table archive from a 20-spin DGA
        # lobby preview! A table must first have a real >= 40 spin (SON 500)
        # history before 20-spin incremental updates are allowed.
        if len(long_hist) < 40 and len(clean) < 40:
            return 0

        ref_window = long_hist[:500] if long_hist else previous
        clean = self._normalize_background_window(clean, ref_window)

        dirty_long = False
        added = []
        if not long_hist:
            long_hist = sanitize_long_archive(list(clean))
            added = list(long_hist)
            dirty_long = True
        else:
            added = detect_new_front_large(
                long_hist[:500],
                clean,
                max_new=250,
            )
            if added:
                long_hist = sanitize_long_archive(list(added) + list(long_hist))
                dirty_long = True
            elif len(long_hist) < 500 and len(clean) > len(long_hist):
                long_hist = sanitize_long_archive(list(clean))
                dirty_long = True

        # Never overwrite a 500-spin file with a shorter DOM frame when no new spins arrived.
        if len(clean) >= len(previous) and (len(clean) >= 498 or not previous or added):
            new_500 = list(clean[:500])
        elif added:
            new_500 = (list(added) + list(previous))[:500]
        else:
            new_500 = list(previous)
        dirty_500 = new_500 != previous

        with self.lock:
            if identity == str(self.table_long_table or ""):
                self.table_long_history = list(long_hist)
            if dirty_500:
                self._memory_table500[key] = list(new_500)

            self._update_table_registry(
                tid,
                display_name=display_name,
                long_count=len(long_hist),
                source=source_label,
                save_disk=False,
            )

            self._pool_memory_tables[key] = list(long_hist)
            if dirty_long:
                self._pool_dirty = True
            if self.history and self.pending_prediction is None:
                self.pending_prediction = self._make_prediction(self.history)

            short_name = str(display_name or tid)
            if len(short_name) > 24:
                short_name = short_name[:21] + "..."

            self.background_status = self._bank_status_text(
                f"arka plan {short_name}"
                + (f" +{len(added)}" if added else "")
            )

        if dirty_long:
            save_table_long_archive(self.data_dir, identity, long_hist)
        if dirty_500:
            try:
                path = os.path.join(
                    self.data_dir,
                    f"table_history500_{key}.json",
                )
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "table": identity,
                            "table_id": tid,
                            "display_name": display_name,
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "results_newest_first": new_500,
                        },
                        f,
                        ensure_ascii=False,
                        indent=2,
                    )
            except Exception:
                pass
        self._save_table_registry()
        return len(added)

    def table_bank_rows(self):
        now = time.time()
        cached_ts = float(getattr(self, "_cached_bank_rows_ts", 0.0) or 0.0)
        cached_rows = getattr(self, "_cached_bank_rows", None)
        if cached_rows is not None and now - cached_ts < 1.0:
            return list(cached_rows)
        out = []
        for tid, raw in (self.table_registry or {}).items():
            row = dict(raw or {})
            updated = float(row.get("last_update_epoch", 0.0) or 0.0)
            age = max(0.0, now - updated) if updated else None
            if age is None:
                freshness = "BEKLİYOR"
            elif age <= 90:
                freshness = "AKTİF"
            elif age <= 300:
                freshness = "GÜNCEL"
            elif age <= 1800:
                freshness = f"{int(age // 60)} dk"
            else:
                freshness = f"{int(age // 3600)} sa"
            out.append({
                "table_id": str(tid),
                "display_name": str(row.get("display_name") or tid),
                "long_count": int(row.get("long_count", 0) or 0),
                "freshness": freshness,
                "last_update": str(row.get("last_update") or "-"),
                "last_source": str(row.get("last_source") or row.get("discovery_source") or "-"),
                "last_error": str(row.get("last_error") or ""),
                "age": age if age is not None else 10**12,
            })
        out.sort(key=lambda row: (row["age"], row["display_name"].lower()))
        self._cached_bank_rows = list(out)
        self._cached_bank_rows_ts = now
        return out


    def update_table_history_500(self, results, table_name="", source_label="MASA SON500"):
        """
        Receive the game's own SON 500 panel.
        - Keep current sliding SON500 window.
        - Maintain a separate long-term table archive.
        - Add only genuinely new front results on later scans.
        - Never score old history as if it were a new live round.
        """
        clean = []
        for x in results or []:
            try:
                n = int(x)
            except Exception:
                continue
            if 0 <= n <= 36:
                clean.append(n)

        if len(clean) < 20 or is_betting_grid_artifact(clean):
            return
        if "SON500" in str(source_label or "").upper() and len(clean) < 40:
            return

        clean = clean[:500]
        save_long_copy = None
        save_500_copy = None

        with self.lock:
            incoming_table = str(self._storage_identity(table_name or self.table_name or ""))
            same_table = (
                not self.table_history_table
                or incoming_table == str(self.table_history_table or "")
            )
            current = list(self.history[:20]) if same_table else []
            table_changed = incoming_table != str(self.table_long_table or "")

            # Switch/load the long archive when table changes.
            if table_changed:
                self.table_long_table = incoming_table
                key_in = safe_table_key(incoming_table)
                mem_long = self._pool_memory_tables.get(key_in)
                self.table_long_history = (
                    list(mem_long)
                    if mem_long
                    else load_table_long_archive(self.data_dir, incoming_table)
                )
                previous_500 = self._saved_table500(incoming_table)
            else:
                previous_500 = list(self.table_history_500) or self._saved_table500(incoming_table)

            # V2.8.1:
            # First try a strict contiguous alignment against the actual live
            # history. This both determines orientation and identifies ONLY
            # genuinely missing new front spins.
            live_alignment = (
                align_reference_to_live(
                    current,
                    clean,
                    max_new=25,
                )
                if current
                else None
            )
            verified_live_new = []

            if live_alignment:
                clean = list(live_alignment["reference"])
                verified_live_new = list(
                    live_alignment.get("new_items", [])
                )
            else:
                ref_win = self.table_long_history[:500] if self.table_long_history else previous_500
                clean = self._normalize_background_window(clean, ref_win)

            new_front = detect_new_front_large(
                self.table_long_history[:500] if self.table_long_history else previous_500,
                clean,
                max_new=500,
            )

            # If authoritative PRAGMATIC statisticHistory (500/500) is already
            # loaded for this table, never let a shorter/unaligned DOM SON 500
            # coordinate scan overwrite 500/500 with 483/500 or double the archive!
            if (
                not table_changed
                and str(source_label or "") == "SON 500"
                and len(self.table_history_500) >= 490
                and len(clean) < len(self.table_history_500)
                and not verified_live_new
                and not new_front
            ):
                return

            dirty_long = False
            # First capture: seed long archive with all visible SON500 only if
            # no long archive exists yet. Later captures add only new results.
            if not self.table_long_history:
                self.table_long_history = sanitize_long_archive(clean)
                added_count = len(self.table_long_history)
                dirty_long = True
            else:
                added = list(new_front)
                if added and len(added) <= 250:
                    self.table_long_history = sanitize_long_archive(
                        added + self.table_long_history
                    )
                    dirty_long = True
                elif len(self.table_long_history) < 500 and len(clean) > len(self.table_long_history):
                    self.table_long_history = sanitize_long_archive(clean)
                    dirty_long = True
                added_count = len(added) if len(added) <= 250 else 0

            had_500_before = len(self.table_history_500) >= 20
            dirty_500 = clean != previous_500
            self.table_history_500 = clean
            self.table_history_table = incoming_table
            self.table_history_last_update = time.time()
            self.table_history_source = f"{source_label}: {len(clean)}/500"
            self.table_long_source = (
                f"UZUN MASA ARŞİVİ: {len(self.table_long_history)}"
                + (f" (+{added_count})" if added_count else "")
            )

            key500 = safe_table_key(incoming_table or "roulette")
            if dirty_500:
                self._memory_table500[key500] = list(clean[:500])
                save_500_copy = None
            if dirty_long:
                save_long_copy = None
                self.walkforward_cache_key = None
            elif table_changed:
                self.walkforward_cache_key = None

            # If normal live-history DOM is still empty, bootstrap current view.
            if not self.history and clean:
                raw_t500 = str(table_name or "").strip()
                norm_t500 = raw_t500.lower()
                is_gen_t500 = (
                    not norm_t500
                    or norm_t500 in ("roulette", "rulet", "pragmatic play", "lobby", "lobi")
                    or norm_t500.startswith(("http://", "https://"))
                    or "/desktop/" in norm_t500
                    or "client." in norm_t500
                )
                if raw_t500 and (not self.table_name or not is_gen_t500):
                    self.table_name = raw_t500
                elif not self.table_name and self.pragmatic_table_id:
                    self.table_name = str(self.pragmatic_table_id)
                self.source = source_label
                self.roulette_seen = True
                self.last_update = time.time()
                self.history = list(clean[:20])

                freq = Counter(self.history)
                self.hot = [
                    n for n, _c in sorted(
                        freq.items(), key=lambda kv: (-kv[1], kv[0])
                    )[:5]
                ]
                cold_sorted = sorted(
                    range(37),
                    key=lambda n: (freq.get(n, 0), n)
                )
                self.cold = cold_sorted[:5]

                self._set_table_paths(self.table_name)
                self.loaded_table = None
                self._try_load_learning(self.table_name, self.history)
                self._refresh_imported_history(force=True)

            if (
                self.history
                and same_table
                and len(clean) >= 50
                and verified_live_new
                and 1 <= len(verified_live_new) <= 10
                and int((live_alignment or {}).get("overlap", 0) or 0) >= min(10, len(self.history))
            ):
                temp_hist = list(self.history)
                for actual in reversed(verified_live_new):
                    self._safe_score_pending(int(actual))
                    self.session_results.append(int(actual))
                    temp_hist = [int(actual)] + temp_hist[:19]
                    self.pending_prediction = self._make_prediction(temp_hist)

                self.history = list(clean[:20])
                self.source = f"SON500 canlı +{len(verified_live_new)}"
                self.roulette_seen = True
                self.status = "CANLI • SON500 SENKRON"
                self.last_update = time.time()
                self.pending_prediction = self._make_prediction(self.history)
                self._save_learning()
            elif self.history and same_table and len(clean) >= 40:
                head_cmp = min(8, len(self.history))
                if (
                    len(self.history) < 20
                    and clean[:len(self.history)] == self.history
                ) or (
                    head_cmp >= 5
                    and clean[:head_cmp] == self.history[:head_cmp]
                    and self.history[:20] != clean[:20]
                ):
                    self.history = list(clean[:20])
                    self.pending_prediction = self._make_prediction(self.history)
                    self._save_learning()
                elif (
                    live_alignment is None
                    and len(clean) >= 50
                    and not detect_new_front(clean[:20], self.history[:20], max_new=6)
                ):
                    # Self-heal only if current[:10] contains a reversed 5-gram
                    rev_cur = list(reversed(self.history[:10]))
                    rev_grams = {
                        tuple(rev_cur[i:i + 5])
                        for i in range(max(0, len(rev_cur) - 4))
                    }
                    clean_grams = {
                        tuple(clean[i:i + 5])
                        for i in range(max(0, min(30, len(clean)) - 4))
                    }
                    if rev_grams and (rev_grams & clean_grams):
                        self.history = list(clean[:20])
                        self.pending_prediction = self._make_prediction(self.history)
                        self._save_learning()
                elif not had_500_before or table_changed or self.pending_prediction is None:
                    self.pending_prediction = self._make_prediction(self.history)
            elif self.history and (not had_500_before or table_changed or self.pending_prediction is None):
                self.pending_prediction = self._make_prediction(self.history)

        if save_long_copy is not None:
            save_table_long_archive(
                self.data_dir,
                incoming_table,
                save_long_copy,
            )
        if save_500_copy is not None:
            try:
                p500 = os.path.join(self.data_dir, f"table_history500_{key500}.json")
                with open(p500, "w", encoding="utf-8") as f5:
                    json.dump(
                        {
                            "table": incoming_table,
                            "table_id": self.pragmatic_table_id,
                            "display_name": table_name or self.table_name,
                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "results_newest_first": save_500_copy,
                        },
                        f5,
                        ensure_ascii=False,
                        indent=2,
                    )
            except Exception:
                pass
        if save_long_copy is not None or save_500_copy is not None:
            self._save_table_registry()

    def update_direct_pragmatic_history(
        self,
        results,
        table_id="",
        operator_game_id="",
        theme_code="",
        title="",
        source="PRAGMATIC statisticHistory",
    ):
        """Apply a direct response only when it belongs to the open table."""
        tid = str(table_id or "").strip()
        if not tid:
            return 0
        with self.lock:
            active = str(self.pragmatic_table_id or "").strip()
            is_bg = bool(active and tid != active)
        if is_bg:
            return 0
        clean = [
            int(x) for x in (results or [])
            if isinstance(x, int) and 0 <= x <= 36
        ][:500]
        if len(clean) < 20:
            return 0
        with self.lock:
            self.set_pragmatic_identity(
                tid,
                operator_game_id=operator_game_id,
                theme_code=theme_code,
                title=title,
            )
            self.direct_history_count = len(clean)
            self.direct_history_last_update = time.time()
            self.direct_history_status = f"PRAGMATIC DIRECT: {len(clean)}/500"
            fallback_title = title or self.table_name
        self.update_table_history_500(
            clean,
            table_name=fallback_title,
            source_label=source,
        )
        return len(clean)

    def update_validated_public_history(self, recent_newest, table_name="", label=""):
        clean = [int(x) for x in (recent_newest or []) if isinstance(x,int) and 0 <= x <= 36]
        if len(clean) < 15:
            return 0
        incoming_table = str(table_name or self.table_name or '')
        if incoming_table != str(self.public_long_table or ''):
            self.public_long_table = incoming_table
            self.public_long_history = load_public_long_archive(self.data_dir,incoming_table)

        previous = list(self.external_history[:200])
        added = []
        if not self.public_long_history:
            self.public_long_history = list(clean)
            added = list(clean)
        else:
            if previous:
                added = detect_new_front_large(previous,clean,max_new=min(500,len(clean)))
            if not added:
                added = detect_new_front_large(
                    self.public_long_history[:max(120,len(clean))],clean,max_new=min(500,len(clean)))
            if added:
                self.public_long_history = list(added) + self.public_long_history

        save_public_long_archive(self.data_dir,incoming_table,self.public_long_history,label)
        self.public_long_source = (
            f"WEB UZUN: {len(self.public_long_history)}" + (f" (+{len(added)})" if added else '')
        )
        return len(added)

    def fused_external_history(self):
        pool = self.multi_table_pool_history()
        if pool:
            return pool
        return (
            list(self.table_history_500[:500])
            + list(self.table_long_history)
        )


    def _external_loop(self):
        while True:
            try:
                with self.lock:
                    self._rebuild_multi_table_pool()
                    self.external_history=[]
                    self.public_long_history=[]
                    self.web_verified=False
                    self.external_source="PUBLIC WEB: KAPALI • doğrudan Pragmatic statisticHistory"
                    self.public_long_source="PUBLIC WEB UZUN: KAPALI"
                time.sleep(10.0)
            except Exception:
                time.sleep(10.0)



    def _storage_identity(self, table_name=""):
        tid = re.sub(r"[^A-Za-z0-9_-]+","_",str(self.pragmatic_table_id or "")).strip("_")
        if tid:
            return f"pragmatic_{tid}"
        raw = str(table_name or "").strip()
        norm = raw.lower()
        is_gen = (
            not norm
            or norm in (
                "roulette",
                "rulet",
                "pragmatic play",
                "pragmatic play live",
                "pragmatic play lobby",
                "live casino",
                "canlı casino",
                "canli casino",
            )
            or "lobby" in norm
            or "lobi" in norm
            or norm.startswith(("http://", "https://"))
            or "/desktop/" in norm
            or "client." in norm
        )
        if is_gen and self.table_name:
            return str(self.table_name)
        return str(raw or self.table_name or "default")

    def set_pragmatic_identity(self, table_id="", operator_game_id="", theme_code="", title=""):
        tid=str(table_id or "").strip()
        if not tid:
            return
        with self.lock:
            changed=bool(self.pragmatic_table_id and self.pragmatic_table_id != tid)
            if changed:
                self._save_learning()
                self.history=[]
                self.hot=[]
                self.cold=[]
                self.table_history_500=[]
                self.table_long_history=[]
                self.table_history_table=""
                self.table_long_table=""
                self.loaded_table=None
                self.pending_prediction=None
                self.display_compare_batch=[]
                self.neighbor_display_batch=[]
                self.neighbor1_display_batch=[]
                self.last_neighbor1_package=None
                self.last_neighbor2_package=None
                self.walkforward_cache_key=None
                self.walkforward_cache={}
                self.pragmatic_operator_game_id=""
                self.pragmatic_theme_code=""
                self.direct_history_count=0
                self.direct_history_last_update=0.0
                self.last_live_result_number=None
                self.last_live_result_time=0.0
                self.direct_history_status=(
                    f"PRAGMATIC DIRECT: yeni aktif masa • tableId {tid}"
                )
            self.pragmatic_table_id=tid
            if operator_game_id:
                self.pragmatic_operator_game_id=str(operator_game_id)
            if theme_code:
                self.pragmatic_theme_code=str(theme_code)
            if title and not self.table_name:
                self.table_name=str(title)
            self._set_table_paths(self.table_name)

    def _set_table_paths(self, table_name):
        identity=self._storage_identity(table_name)
        self.learning_path, self.log_path = table_storage_paths(
            self.data_dir, identity or "default"
        )

        # One-time migration from V1.7.2 single-table storage if it belongs
        # to the same table and no per-table file exists yet.
        if not os.path.exists(self.learning_path) and os.path.exists(self.legacy_learning_path):
            try:
                with open(self.legacy_learning_path, "r", encoding="utf-8") as f:
                    legacy = json.load(f)
                saved = str(legacy.get("table", ""))
                current = str(self._storage_identity(table_name))
                if (not saved) or (not current) or saved == current:
                    shutil.copy2(self.legacy_learning_path, self.learning_path)
            except Exception:
                pass

    def _reset_learning(self, clean, table_name=""):
        self.session_results = list(reversed(clean))
        self.expert_loss = {name: 0.0 for name in EXPERT_NAMES}
        self.expert_trials = 0
        self.expert_hits = {
            name: {"trials": 0, "exact": 0, "top5": 0, "neighbor5": 0}
            for name in EXPERT_NAMES
        }
        self.validation = {
            "trials": 0,
            "exact": 0,
            "side4": 0,
            "top5": 0,
            "neighbor5": 0,
            "region": 0,
        }
        self.validation_history = []
        self.display_compare_batch = []
        self.neighbor_display_batch = []
        self.neighbor_stats_total = {
            "trials": 0,
            "net_hits": 0,
            "backup_hits": 0,
            "any_hits": 0,
            "multi_hits": 0,
            "coverage_sum": 0,
        }
        self.neighbor1_display_batch = []
        self.neighbor1_stats_total = {
            "trials": 0,
            "net_hits": 0,
            "backup_hits": 0,
            "any_hits": 0,
            "multi_hits": 0,
            "coverage_sum": 0,
        }
        self.last_neighbor1_package=None
        self.last_neighbor2_package=None
        self.locked_live = {
            "version": "V2.9 FINAL CORE",
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "rows": [],
            "frozen": False,
        }

        self.source_hits = {
            name: {
                "trials": 0,
                "exact": 0,
                "top5": 0,
            }
            for name in SOURCE_NAMES
        }
        self.loaded_table = self._storage_identity(table_name)
        self.pending_prediction = self._make_prediction(clean)

    def _try_load_learning(self, table_name, clean):
        if self.loaded_table is not None:
            return

        identity = self._storage_identity(table_name)
        self.loaded_table = identity

        try:
            if not os.path.exists(self.learning_path):
                self._reset_learning(clean, table_name)
                return

            with open(self.learning_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            saved_table = str(data.get("table", ""))
            current_table = str(identity)

            # Only reuse learning for the same named table.
            if saved_table and current_table and saved_table != current_table:
                self._reset_learning(clean, table_name)
                return

            seq = [
                int(x) for x in data.get("session_results", [])
                if str(x).isdigit() and 0 <= int(x) <= 36
            ]
            # Self-heal any reversed palindrome tail injected into session_results by
            # the legacy reversed DOM-bar bug.
            for r_len in range(min(10, len(seq) // 2), 4, -1):
                tail = seq[-r_len:]
                if len(set(tail)) < 3:
                    continue
                if seq[-2 * r_len:-r_len] == list(reversed(tail)):
                    seq = seq[:-r_len]
                    break
                if len(seq) >= 2 * r_len + 1 and seq[-2 * r_len - 1:-r_len - 1] == list(reversed(tail)):
                    seq = seq[:-r_len]
                    break

            self.session_results = seq or list(reversed(clean))
            self.expert_loss = {
                name: float(data.get("expert_loss", {}).get(name, 0.0))
                for name in EXPERT_NAMES
            }
            self.expert_trials = int(data.get("expert_trials", 0))

            raw_hits = data.get("expert_hits", {})
            self.expert_hits = {}
            for name in EXPERT_NAMES:
                rh = raw_hits.get(name, {})
                self.expert_hits[name] = {
                    "trials": int(rh.get("trials", 0)),
                    "exact": int(rh.get("exact", 0)),
                    "top5": int(rh.get("top5", 0)),
                    "neighbor5": int(rh.get("neighbor5", 0)),
                }

            val = data.get("validation", {})
            self.validation = {
                "trials": int(val.get("trials", 0)),
                "exact": int(val.get("exact", 0)),
                "side4": int(val.get("side4", 0)),
                "top5": int(val.get("top5", 0)),
                "neighbor5": int(val.get("neighbor5", 0)),
                "region": int(val.get("region", 0)),
            }
            self.validation_history = list(data.get("validation_history", []))[-300:]

            raw_locked = data.get("locked_live") or {}
            if str(raw_locked.get("version") or "") == "V2.9 FINAL CORE":
                self.locked_live = {
                    "version": "V2.9 FINAL CORE",
                    "started": str(raw_locked.get("started") or time.strftime("%Y-%m-%d %H:%M:%S")),
                    "rows": [dict(r) for r in (raw_locked.get("rows") or []) if isinstance(r,dict)][:500],
                    "frozen": bool(raw_locked.get("frozen", False)),
                }
                if len(self.locked_live["rows"]) >= 500:
                    self.locked_live["frozen"] = True
            else:
                # New algorithm version starts a fresh untouched live test.
                self.locked_live = {
                    "version": "V2.9 FINAL CORE",
                    "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "rows": [],
                    "frozen": False,
                }

            raw_neighbor = data.get("neighbor_stats_total", {})
            self.neighbor_stats_total = {
                "trials": int(raw_neighbor.get("trials", 0)),
                "net_hits": int(raw_neighbor.get("net_hits", 0)),
                "backup_hits": int(raw_neighbor.get("backup_hits", 0)),
                "any_hits": int(raw_neighbor.get("any_hits", 0)),
                "multi_hits": int(raw_neighbor.get("multi_hits", 0)),
                "coverage_sum": int(raw_neighbor.get("coverage_sum", 0)),
            }

            raw_neighbor1 = data.get("neighbor1_stats_total", {})
            self.neighbor1_stats_total = {
                "trials": int(raw_neighbor1.get("trials", 0)),
                "net_hits": int(raw_neighbor1.get("net_hits", 0)),
                "backup_hits": int(raw_neighbor1.get("backup_hits", 0)),
                "any_hits": int(raw_neighbor1.get("any_hits", 0)),
                "multi_hits": int(raw_neighbor1.get("multi_hits", 0)),
                "coverage_sum": int(raw_neighbor1.get("coverage_sum", 0)),
            }

            raw_source_hits = data.get("source_hits", {})
            self.source_hits = {}
            for name in SOURCE_NAMES:
                st = raw_source_hits.get(name, {})
                self.source_hits[name] = {
                    "trials": int(st.get("trials", 0)),
                    "exact": int(st.get("exact", 0)),
                    "top5": int(st.get("top5", 0)),
                }

            self.pending_prediction = self._make_prediction(clean)
        except Exception:
            self._reset_learning(clean, table_name)

    def _save_learning(self):
        try:
            data = {
                "table": self._storage_identity(self.table_name),
                "display_table": self.table_name,
                "pragmatic_table_id": self.pragmatic_table_id,
                "operator_game_id": self.pragmatic_operator_game_id,
                "theme_code": self.pragmatic_theme_code,
                "session_results": self.session_results,
                "expert_loss": self.expert_loss,
                "expert_trials": self.expert_trials,
                "expert_hits": self.expert_hits,
                "validation": self.validation,
                "validation_history": self.validation_history[-300:],
                "locked_live": self.locked_live,
                "neighbor_stats_total": self.neighbor_stats_total,
                "neighbor1_stats_total": self.neighbor1_stats_total,
                "source_hits": self.source_hits,
            }
            with open(self.learning_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_walkforward_profile(self):
        long_hist = list(self.table_long_history or [])
        key = (
            str(self.pragmatic_table_id or self.table_long_table or self.table_name),
            len(long_hist),
            tuple(long_hist[:6]),
        )
        if key == self.walkforward_cache_key:
            return dict(self.walkforward_cache or {})

        profile = walk_forward_profile(long_hist)
        self.walkforward_cache_key = key
        self.walkforward_cache = profile
        return dict(profile)

    def _make_prediction(self, hist):
        pool_seq = self.multi_table_pool_history()
        pool_snap = external_transition_snapshot(hist, pool_seq)
        ext_seq = pool_seq if pool_seq else (
            list(self.table_history_500[:500]) + list(self.table_long_history)
        )

        # Keep AKIŞ (LOCAL + MODEL_TRANSITION + MODEL_RECENCY) genuinely focused on
        # the short-term live momentum (last ~42 spins) rather than cloning
        # 260 spins of table_history_500 (which made AKIŞ a duplicate of TABLO!).
        if len(self.session_results) < 42 and len(self.table_history_500) >= 20:
            recent_nf = list(reversed(self.session_results[-30:])) if self.session_results else list(hist[:20])
            new_front_local = detect_new_front_large(
                self.table_history_500[:60],
                recent_nf,
                max_new=30,
            )
            merged_local_nf = (list(new_front_local) + list(self.table_history_500[:42]))[:42]
            local_seq = list(reversed(merged_local_nf))
        else:
            local_seq = list(self.session_results[-60:])

        pred = combined_prediction(
            hist,
            local_seq,
            self.expert_loss,
            self.expert_trials,
            self.expert_hits,
            ext_seq,
        )

        consensus = source_consensus(
            hist,
            local_seq,
            self.table_history_500,
            self.table_long_history,
            pool_seq,
            [],
            self.source_hits,
        )
        pred = blend_with_consensus(pred, consensus)

        wf_profile = self._get_walkforward_profile()
        pred = apply_walk_forward_model(
            pred,
            hist,
            local_seq,
            self.table_long_history,
            wf_profile,
        )

        # Incorporate empirical multi-table transition probabilities
        # P(next | current) across all collected tables directly into the model.
        if int(pool_snap.get("exact_obs", 0) or 0) >= 3:
            mt_dist = multi_table_transition_expert(hist, pool_seq)
            spins_total = int(pool_snap.get("spins", 0) or 0)
            tables_total = int(pool_snap.get("tables", 0) or 0)
            mt_alpha = min(
                0.68,
                0.34
                + 0.22 * min(1.0, spins_total / 4000.0)
                + 0.12 * min(1.0, max(0, tables_total - 1) / 10.0),
            )
            base_comb = pred.get("combined") or {n: 1.0 / 37.0 for n in range(37)}
            merged_comb = {
                n: (1.0 - mt_alpha) * float(base_comb.get(n, 0.0))
                   + mt_alpha * float(mt_dist.get(n, 0.0))
                for n in range(37)
            }
            merged_comb = normalize_probs(merged_comb, floor=0.0)
            ordered_comb = sorted(merged_comb.items(), key=lambda kv: (-kv[1], kv[0]))
            pred["combined"] = merged_comb
            pred["model_share"] = ordered_comb[0][1] * 100.0

        pred["multi_table_transition"] = pool_snap
        pred["recent_history"] = list(hist[:6]) if hist else []
        pred["table_long_count"] = max(
            len(self.table_long_history or []),
            len(self.table_history_500 or []),
        )

        region_name, region_conf, region_scores, region_features = region_prediction(hist)
        pred["region_name"] = region_name
        pred["region_confidence"] = region_conf
        pred["region_scores"] = region_scores
        pred["region_features"] = region_features

        # V2.8.3 FINAL STEP:
        # Convert all sources/models into ONE model pick.
        net_pick = choose_net_number(
            pred,
            self.source_hits,
            self.expert_hits,
            self.validation_history,
        )
        pred["pre_net_predicted"] = pred.get("predicted")
        pred["net_pick"] = net_pick
        pred["predicted"] = int(net_pick["number"])
        pred["top5"] = [int(n) for n in net_pick["top5"]]
        pred["neighbor_zone"] = wheel_neighbors(pred["predicted"], 2)
        return pred

    def _score_pending(self, actual):
        pred = self.pending_prediction
        if not pred:
            return

        actual = int(actual)
        self.validation["trials"] += 1

        exact_hit = actual == pred["predicted"]
        side4 = [n for n in pred["top5"] if n != pred["predicted"]][:4]
        side4_hit = actual in side4
        top5_hit = actual in pred["top5"]

        if exact_hit:
            self.validation["exact"] += 1
        if side4_hit:
            self.validation["side4"] += 1
        if top5_hit:
            self.validation["top5"] += 1
        if actual in pred["neighbor_zone"]:
            self.validation["neighbor5"] += 1
        region_hit = region_of_number(actual) == pred.get("region_name")
        if region_hit:
            self.validation["region"] += 1

        shown_action = str(pred.get("_shown_action") or "TEST")
        shown_mode = (
            "TEST"
            if shown_action in ("PAS", "İZLE", "TEST")
            else "YAN"
        )
        shown_signal = float(
            pred.get("_shown_signal", pred.get("model_score", 0.0)) or 0.0
        )
        shown_quality = str(pred.get("_shown_quality") or "")

        compare_result = (
            "ORTAK"
            if exact_hit
            else "ADAY"
            if side4_hit
            else "DIŞI"
        )

        # V2.8.2 critical fix:
        # Resolve source consensus BEFORE building source_round.
        # Previous code used `consensus` before assignment and could stop
        # the entire live update/catch-up path with NameError.
        consensus = pred.get("source_consensus") or {}

        source_round = {}

        for name, sd in (consensus.get("sources") or {}).items():
            top1 = sd.get("top1")
            top5_src = [int(n) for n in (sd.get("top5") or [])[:5]]
            result = (
                "TAM"
                if actual == top1
                else "TOP5"
                if actual in top5_src
                else "DIŞI"
            )
            source_round[name] = {
                "top1": int(top1) if top1 is not None else None,
                "top5": top5_src,
                "result": result,
            }

        # Internal model experts are logged separately from raw data sources.
        # WEB expert here is the long-table model and is displayed as LONG-M.
        for name, dist in (pred.get("experts") or {}).items():
            ordered = sorted(
                dist.items(),
                key=lambda kv: (-kv[1], kv[0])
            )
            if not ordered:
                continue
            top1 = int(ordered[0][0])
            top5_src = [int(n) for n, _p in ordered[:5]]
            result = (
                "TAM"
                if actual == top1
                else "TOP5"
                if actual in top5_src
                else "DIŞI"
            )
            source_round["MODEL_" + str(name)] = {
                "top1": top1,
                "top5": top5_src,
                "result": result,
            }

        # V2.8.5 KOMŞU:
        # Assumption requested by user:
        # NET number + 2 wheel neighbors, and each of 4 backups + 2 neighbors.
        centers = [int(pred["predicted"])] + [int(n) for n in side4[:4]]

        center_zones = {
            int(center): [int(x) for x in wheel_neighbors(int(center), 2)]
            for center in centers
        }

        net_center = int(pred["predicted"])
        backup_centers = [int(n) for n in side4[:4]]

        net_zone = set(center_zones.get(net_center, []))
        backup_zones = {
            int(c): set(center_zones.get(int(c), []))
            for c in backup_centers
        }

        hit_centers = [
            int(center)
            for center, zone in center_zones.items()
            if int(actual) in set(zone)
        ]

        net_neighbor_hit = int(actual) in net_zone
        backup_neighbor_hits = [
            int(c)
            for c, zone in backup_zones.items()
            if int(actual) in zone
        ]

        all_covered = set()
        for zone in center_zones.values():
            all_covered.update(int(x) for x in zone)

        if net_neighbor_hit:
            neighbor_result = "NET K2"
        elif backup_neighbor_hits:
            neighbor_result = "YEDEK K2"
        else:
            neighbor_result = "DIŞI"

        neighbor_row = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "table_id": str(self.pragmatic_table_id or ""),
            "net": net_center,
            "backups": backup_centers,
            "actual": int(actual),
            "net_zone": sorted(net_zone),
            "backup_zones": {
                str(c): sorted(zone)
                for c, zone in backup_zones.items()
            },
            "hit_centers": hit_centers,
            "net_neighbor_hit": bool(net_neighbor_hit),
            "backup_neighbor_hits": backup_neighbor_hits,
            "any_neighbor_hit": bool(net_neighbor_hit or backup_neighbor_hits),
            "unique_coverage": len(all_covered),
            "covered_numbers": sorted(all_covered),
            "result": neighbor_result,
        }

        self.neighbor_stats_total["trials"] += 1
        if net_neighbor_hit:
            self.neighbor_stats_total["net_hits"] += 1
        elif backup_neighbor_hits:
            self.neighbor_stats_total["backup_hits"] += 1
        if net_neighbor_hit or backup_neighbor_hits:
            self.neighbor_stats_total["any_hits"] += 1
        if len(hit_centers) >= 2:
            self.neighbor_stats_total["multi_hits"] += 1
        self.neighbor_stats_total["coverage_sum"] += len(all_covered)

        # V2.8.6 K1:
        # User's actual play style:
        # left 1 + center + right 1 = 3 wheel numbers per center.
        center_zones_k1 = {
            int(center): [int(x) for x in wheel_neighbors(int(center), 1)]
            for center in centers
        }

        net_zone_k1 = set(center_zones_k1.get(net_center, []))
        backup_zones_k1 = {
            int(c): set(center_zones_k1.get(int(c), []))
            for c in backup_centers
        }

        hit_centers_k1 = [
            int(center)
            for center, zone in center_zones_k1.items()
            if int(actual) in set(zone)
        ]

        net_neighbor1_hit = int(actual) in net_zone_k1
        backup_neighbor1_hits = [
            int(c)
            for c, zone in backup_zones_k1.items()
            if int(actual) in zone
        ]

        all_covered_k1 = set()
        for zone in center_zones_k1.values():
            all_covered_k1.update(int(x) for x in zone)

        if net_neighbor1_hit:
            neighbor1_result = "NET K1"
        elif backup_neighbor1_hits:
            neighbor1_result = "YEDEK K1"
        else:
            neighbor1_result = "DIŞI"

        neighbor1_row = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "table_id": str(self.pragmatic_table_id or ""),
            "net": net_center,
            "backups": backup_centers,
            "actual": int(actual),
            "net_zone": sorted(net_zone_k1),
            "backup_zones": {
                str(c): sorted(zone)
                for c, zone in backup_zones_k1.items()
            },
            "hit_centers": hit_centers_k1,
            "net_neighbor_hit": bool(net_neighbor1_hit),
            "backup_neighbor_hits": backup_neighbor1_hits,
            "any_neighbor_hit": bool(
                net_neighbor1_hit or backup_neighbor1_hits
            ),
            "unique_coverage": len(all_covered_k1),
            "covered_numbers": sorted(all_covered_k1),
            "result": neighbor1_result,
        }

        self.neighbor1_stats_total["trials"] += 1
        if net_neighbor1_hit:
            self.neighbor1_stats_total["net_hits"] += 1
        elif backup_neighbor1_hits:
            self.neighbor1_stats_total["backup_hits"] += 1
        if net_neighbor1_hit or backup_neighbor1_hits:
            self.neighbor1_stats_total["any_hits"] += 1
        if len(hit_centers_k1) >= 2:
            self.neighbor1_stats_total["multi_hits"] += 1
        self.neighbor1_stats_total["coverage_sum"] += len(all_covered_k1)

        # Main-screen K1/K2 result cards use NET + 4 YEDEK as ONE package.
        self.last_neighbor1_package = {
            "won": bool(neighbor1_row["any_neighbor_hit"]),
            "actual": int(actual),
            "net": int(net_center),
            "backups": list(backup_centers),
            "coverage": int(neighbor1_row["unique_coverage"]),
        }
        self.last_neighbor2_package = {
            "won": bool(neighbor_row["any_neighbor_hit"]),
            "actual": int(actual),
            "net": int(net_center),
            "backups": list(backup_centers),
            "coverage": int(neighbor_row["unique_coverage"]),
        }

        # V2.9 LOCKED LIVE 500: append exactly once, after a prediction that
        # existed before the actual result. Never reconstruct old rounds.
        if not isinstance(self.locked_live, dict):
            self.locked_live = {
                "version":"V2.9 FINAL CORE",
                "started":time.strftime("%Y-%m-%d %H:%M:%S"),
                "rows":[],"frozen":False,
            }
        locked_rows = self.locked_live.setdefault("rows", [])
        if len(locked_rows) < 500 and not self.locked_live.get("frozen"):
            net_info = pred.get("net_pick") or {}
            locked_rows.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "table_id": str(self.pragmatic_table_id or ""),
                "predicted": int(pred["predicted"]),
                "top5_numbers": [int(n) for n in pred["top5"][:5]],
                "actual": int(actual),
                "exact": bool(exact_hit),
                "top5": bool(top5_hit),
                "k1": bool(neighbor1_row.get("any_neighbor_hit")),
                "k2": bool(neighbor_row.get("any_neighbor_hit")),
                "cov1": int(neighbor1_row.get("unique_coverage",0) or 0),
                "cov2": int(neighbor_row.get("unique_coverage",0) or 0),
                "family_picks": dict(net_info.get("family_picks") or {}),
                "family_supporters": list(net_info.get("family_supporters") or []),
                "signal_score": float(net_info.get("signal_score",0.0) or 0.0),
            })
            self.locked_live["rows"] = locked_rows[-500:]
            if len(self.locked_live["rows"]) >= 500:
                self.locked_live["frozen"] = True

        comparison_row = {
            "exact": exact_hit,
            "side4": side4_hit,
            "top5": top5_hit,
            "neighbor5": actual in pred["neighbor_zone"],
            "region": region_hit,

            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "table_id": str(self.pragmatic_table_id or ""),
            "predicted": int(pred["predicted"]),
            "side4_numbers": [int(n) for n in side4],
            "top5_numbers": [int(n) for n in pred["top5"]],
            "actual": int(actual),
            "compare_result": compare_result,
            "shown_action": shown_action,
            "shown_mode": shown_mode,
            "shown_signal": shown_signal,
            "shown_quality": shown_quality,
            "predicted_region": str(pred.get("region_name") or ""),
            "actual_region": str(region_of_number(actual) or ""),
            "source_round": source_round,
            "neighbor_bet": neighbor_row,
            "neighbor1_bet": neighbor1_row,
        }

        self.validation_history.append(comparison_row)
        self.validation_history = self.validation_history[-300:]

        # Screen list: 01..12 chronological. The 13th real result starts
        # a fresh batch at 01. This buffer is UI-only.
        if len(self.display_compare_batch) >= 12:
            self.display_compare_batch = []
        self.display_compare_batch.append(dict(comparison_row))

        if len(self.neighbor_display_batch) >= 12:
            self.neighbor_display_batch = []
        self.neighbor_display_batch.append(dict(neighbor_row))

        if len(self.neighbor1_display_batch) >= 12:
            self.neighbor1_display_batch = []
        self.neighbor1_display_batch.append(dict(neighbor1_row))


        # Score each historical source separately using the same captured
        # consensus object.
        for name, sd in (consensus.get("sources") or {}).items():
            if name not in self.source_hits:
                self.source_hits[name] = {
                    "trials": 0,
                    "exact": 0,
                    "top5": 0,
                }
            st = self.source_hits[name]
            st["trials"] += 1
            if actual == sd.get("top1"):
                st["exact"] += 1
            if actual in (sd.get("top5") or []):
                st["top5"] += 1

        # Online log-loss + each expert's own hit performance.
        for name in EXPERT_NAMES:
            dist = pred["experts"][name]
            p = max(1e-6, float(dist.get(actual, 1e-6)))
            self.expert_loss[name] += -math.log(p)

            ordered = sorted(
                dist.items(),
                key=lambda kv: (-kv[1], kv[0])
            )
            expert_top1 = ordered[0][0]
            expert_top5 = [n for n, _p in ordered[:5]]
            expert_neigh5 = wheel_neighbors(expert_top1, 2)

            st = self.expert_hits[name]
            st["trials"] += 1
            if actual == expert_top1:
                st["exact"] += 1
            if actual in expert_top5:
                st["top5"] += 1
            if actual in expert_neigh5:
                st["neighbor5"] += 1

        self.expert_trials += 1

        try:
            record = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "table": self.table_name,
                "predicted": pred["predicted"],
                "top5": pred["top5"],
                "side4": side4,
                "neighbor_zone": pred["neighbor_zone"],
                "region": pred.get("region_name"),
                "source_consensus": pred.get("source_consensus", {}),
                "source_round": source_round,
                "model_share": pred["model_share"],
                "model_score": pred["model_score"],
                "weights": pred["weights"],
                "walkforward": pred.get("walkforward", {}),
                "actual": actual,
                "exact_hit": exact_hit,
                "side4_hit": side4_hit,
                "top5_hit": top5_hit,
                "region_hit": region_of_number(actual) == pred.get("region_name"),
            }
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def _safe_score_pending(self, actual):
        """
        Analytics errors must never freeze SON SAYI / SON20 synchronization.
        """
        try:
            self._score_pending(int(actual))
            self.score_error_status = "OK"
            return True
        except Exception as e:
            self.score_error_status = type(e).__name__
            return False

    def clear_display_comparisons(self):
        """Clear only the visible 01..12 list; keep all learning/performance."""
        with self.lock:
            self.display_compare_batch = []

    def clear_neighbor_comparisons(self):
        """Clear only visible KOMŞU rows; keep accumulated stats/learning."""
        with self.lock:
            self.neighbor_display_batch = []

    def clear_neighbor1_comparisons(self):
        """Clear only visible 1 KOMŞU rows; keep accumulated stats/learning."""
        with self.lock:
            self.neighbor1_display_batch = []

    def reset_performance_stats(self):
        """
        Reset only the visible GERÇEK PERFORMANS scoreboards (PERFORMANS, RİSK/EV,
        LOCKED LIVE, K1/K2 totals, and 12-round lists) WITHOUT touching collected spin
        history (SON20, SON500, UZUN ARŞİV, ORTAK HAVUZ) OR learned model/source
        weights (expert_loss, expert_trials, expert_hits, source_hits).
        """
        with self.lock:
            self.validation = {
                "trials": 0,
                "exact": 0,
                "side4": 0,
                "top5": 0,
                "neighbor5": 0,
                "region": 0,
            }
            self.validation_history = []
            self.display_compare_batch = []
            self.neighbor_display_batch = []
            self.neighbor_stats_total = {
                "trials": 0,
                "net_hits": 0,
                "backup_hits": 0,
                "any_hits": 0,
                "multi_hits": 0,
                "coverage_sum": 0,
            }
            self.neighbor1_display_batch = []
            self.neighbor1_stats_total = {
                "trials": 0,
                "net_hits": 0,
                "backup_hits": 0,
                "any_hits": 0,
                "multi_hits": 0,
                "coverage_sum": 0,
            }
            self.last_neighbor1_package = None
            self.last_neighbor2_package = None
            self.locked_live = {
                "version": "V2.9 FINAL CORE",
                "started": time.strftime("%Y-%m-%d %H:%M:%S"),
                "rows": [],
                "frozen": False,
            }
            if self.history:
                self.pending_prediction = self._make_prediction(self.history)
            self._save_learning()

    def update_results(self, results, hot=None, cold=None, table_name="", source="API"):
        clean = []
        for x in results or []:
            try:
                if isinstance(x, dict):
                    n = int(x.get("result"))
                else:
                    n = int(x)
            except Exception:
                continue
            if 0 <= n <= 36:
                clean.append(n)

        if not clean:
            return

        with self.lock:
            raw_table = str(table_name or "").strip()
            norm_raw = raw_table.lower()
            is_generic_title = (
                not norm_raw
                or norm_raw in (
                    "roulette",
                    "rulet",
                    "pragmatic play",
                    "pragmatic play live",
                    "pragmatic play lobby",
                    "live casino",
                    "canlı casino",
                    "canli casino",
                )
                or "lobby" in norm_raw
                or "lobi" in norm_raw
                or norm_raw.startswith(("http://", "https://"))
                or "/desktop/" in norm_raw
                or "client." in norm_raw
            )
            if self.table_name and is_generic_title:
                incoming_table = str(self.table_name)
            elif is_generic_title and self.pragmatic_table_id:
                incoming_table = str(self.pragmatic_table_id)
            else:
                incoming_table = str(raw_table or self.table_name or self.pragmatic_table_id or "")

            # First usable data.
            if not self.history:
                self.history = clean[:20]
                if incoming_table:
                    self.table_name = incoming_table
                self._set_table_paths(self.table_name)
                self._try_load_learning(self.table_name, self.history)
            else:
                # If table actually changes, do not mix its learned transitions.
                # When pragmatic_table_id is locked, real table switches go through
                # set_pragmatic_identity; do not reset on wrapper title changes.
                if (
                    incoming_table
                    and self.table_name
                    and incoming_table != self.table_name
                    and not self.pragmatic_table_id
                ):
                    # Save the old table before switching; each table now owns
                    # its own long-term history brain.
                    self._save_learning()
                    self.table_name = incoming_table
                    self.history = clean[:20]
                    self.loaded_table = None
                    self._set_table_paths(self.table_name)
                    self._try_load_learning(self.table_name, self.history)
                else:
                    new_items = detect_new_front(self.history, clean[:20], max_new=16)

                    if new_items:
                        # new_items are newest-first; replay chronologically.
                        temp_hist = list(self.history)
                        chronologically_added = list(reversed(new_items))
                        for idx_a, actual in enumerate(chronologically_added):
                            self._safe_score_pending(actual)
                            self.session_results.append(int(actual))
                            self.session_results = self.session_results
                            temp_hist = [int(actual)] + temp_hist[:19]
                            if idx_a + 1 < len(chronologically_added):
                                self.pending_prediction = self._make_prediction(temp_hist)

                        n_new = len(new_items)
                        if (
                            len(clean) >= 20
                            and n_new < 20
                            and clean[n_new:20] == self.history[:20 - n_new]
                        ):
                            self.history = clean[:20]
                        else:
                            self.history = ([int(x) for x in new_items] + list(self.history))[:20]

                        # Immediately advance SON500, UZUN ARŞİV, and ORTAK HAVUZ with the
                        # newly landed spin(s) BEFORE computing pending_prediction so the
                        # calculation is 100% final the instant the spin lands!
                        if self.table_history_500:
                            add_500 = detect_new_front_large(
                                self.table_history_500[:40],
                                self.history[:20],
                                max_new=20,
                            )
                            if add_500:
                                self.table_history_500 = (list(add_500) + list(self.table_history_500))[:500]
                        if self.table_long_history:
                            add_long = detect_new_front_large(
                                self.table_long_history[:40],
                                self.history[:20],
                                max_new=20,
                            )
                            if add_long:
                                self.table_long_history = list(add_long) + list(self.table_long_history)
                                self.table_long_source = (
                                    f"UZUN MASA ARŞİVİ: {len(self.table_long_history)} (+{len(add_long)})"
                                )

                        # Calculate once, immediately, and lock for this round.
                        self.pending_prediction = self._make_prediction(self.history)
                        self._save_learning()
                    elif (
                        len(clean) >= 20
                        and len(self.history) >= 5
                        and clean[:min(8, len(self.history))] == self.history[:min(8, len(self.history))]
                    ):
                        # User expanded SON500 drawer (Genişlet): fill/sync full 20 spins
                        # without scoring fake rounds.
                        if self.history[:20] != clean[:20]:
                            self.history = list(clean[:20])
                            self.pending_prediction = self._make_prediction(self.history)
                            self._save_learning()
                    elif clean[:20] == self.history[:len(clean[:20])]:
                        pass
                    elif str(source or "").endswith("resync"):
                        self.history = (list(clean) + list(self.history[len(clean):]))[:20]
                        self.pending_prediction = self._make_prediction(self.history)
                        self._save_learning()
                    else:
                        return

            if hot:
                self.hot = [
                    int(x) for x in hot
                    if str(x).isdigit() and 0 <= int(x) <= 36
                ][:5]
            if cold:
                self.cold = [
                    int(x) for x in cold
                    if str(x).isdigit() and 0 <= int(x) <= 36
                ][:5]
            if raw_table and (not self.table_name or not is_generic_title):
                self.table_name = raw_table

            self.source = source
            self.roulette_seen = True
            self.status = "CANLI • WEB HISTORY FUSION"
            self.last_update = time.time()

            if self.pending_prediction is None:
                self.pending_prediction = self._make_prediction(self.history)

    def update_live_result(self, number, source="CANLI SONUÇ EKRANI"):
        """Prepend one stable, prominent live result without replacing SON20."""
        try:
            n = int(number)
        except Exception:
            return False
        if not 0 <= n <= 36:
            return False

        with self.lock:
            if not self.history or int(self.history[0]) == n:
                return False
            now = time.time()
            if (
                self.last_live_result_number == n
                and now - float(self.last_live_result_time or 0.0) < 12.0
            ):
                return False

            self._safe_score_pending(n)
            self.session_results.append(n)
            self.history = [n] + list(self.history[:19])
            self.pending_prediction = self._make_prediction(self.history)
            self.source = str(source)
            self.roulette_seen = True
            self.status = "CANLI • SONUÇ EKRANI SENKRON"
            self.last_update = now
            self.last_live_result_number = n
            self.last_live_result_time = now
            self._save_learning()
            return True

    def snapshot(self):
        with self.lock:
            h = list(self.history)
            freq = Counter(h)
            hot_calc = [
                n for n,_ in sorted(
                    freq.items(), key=lambda kv:(-kv[1], kv[0])
                )[:5]
            ]
            cold_calc = [n for n in range(37) if n not in freq][:5]

            if self.pending_prediction is None:
                self.pending_prediction = self._make_prediction(h)
            pred = self.pending_prediction

            watch = [
                (n, pred["combined"][n])
                for n in pred["top5"]
            ]

            recent20 = rolling_rates(self.validation_history, 20)
            wf_profile = pred.get("walkforward") or self._get_walkforward_profile()

            cal_regions = calibrated_region_scores(
                pred["region_scores"],
                self.validation["trials"],
                self.validation,
                recent20,
            )
            cal_region_name = max(cal_regions, key=cal_regions.get)
            cal_region_conf = cal_regions[cal_region_name]

            cal_signal = calibrated_signal(
                pred["model_score"],
                self.validation["trials"],
                self.validation,
                recent20,
            )
            quality = prediction_quality(
                cal_signal,
                pred["model_share"],
                self.validation["trials"],
                self.validation,
                recent20,
            )

            if int(wf_profile.get("trials", 0) or 0) >= 80 and not wf_profile.get("qualified"):
                cal_signal = min(cal_signal, 34.0)
                quality = "ZAYIF"

            # V2.7.8 is a data-collection lab, not an OYNA/PAS gate.
            # Keep the old decision engine out of the visible workflow.
            pro_decision = {
                "action": "KAYNAK-LAB",
                "reason": "Her kaynak bağımsız kaydediliyor",
            }

            pred["_shown_action"] = "KAYNAK-LAB"
            pred["_shown_signal"] = float(cal_signal)
            pred["_shown_quality"] = str(quality)

            source_answers = {}
            sc_now = pred.get("source_consensus") or {}
            for name, sd in (sc_now.get("sources") or {}).items():
                source_answers[name] = {
                    "top1": sd.get("top1"),
                    "top5": list(sd.get("top5") or [])[:5],
                    "weight": float(sd.get("weight", 0.0) or 0.0),
                }

            # Also expose the four internal model answers for research.
            for name, dist in (pred.get("experts") or {}).items():
                ordered = sorted(
                    dist.items(),
                    key=lambda kv: (-kv[1], kv[0])
                )
                if ordered:
                    source_answers["MODEL_" + str(name)] = {
                        "top1": int(ordered[0][0]),
                        "top5": [int(n) for n, _p in ordered[:5]],
                        "weight": 0.0,
                    }

            comparison_records = [
                dict(row)
                for row in self.display_compare_batch
                if isinstance(row, dict)
                and "actual" in row
                and "predicted" in row
            ][:12]

            neighbor_records = [
                dict(row)
                for row in self.neighbor_display_batch
                if isinstance(row, dict) and "actual" in row
            ][:12]

            neighbor1_records = [
                dict(row)
                for row in self.neighbor1_display_batch
                if isinstance(row, dict) and "actual" in row
            ][:12]

            nb = dict(self.neighbor_stats_total)
            nb_trials = int(nb.get("trials",0) or 0)
            neighbor_stats = {
                "trials": nb_trials,
                "net_hits": int(nb.get("net_hits",0) or 0),
                "backup_hits": int(nb.get("backup_hits",0) or 0),
                "any_hits": int(nb.get("any_hits",0) or 0),
                "multi_hits": int(nb.get("multi_hits",0) or 0),
                "avg_coverage": (
                    float(nb.get("coverage_sum",0) or 0) / nb_trials
                    if nb_trials else 0.0
                ),
            }

            nb1 = dict(self.neighbor1_stats_total)
            nb1_trials = int(nb1.get("trials",0) or 0)
            neighbor1_stats = {
                "trials": nb1_trials,
                "net_hits": int(nb1.get("net_hits",0) or 0),
                "backup_hits": int(nb1.get("backup_hits",0) or 0),
                "any_hits": int(nb1.get("any_hits",0) or 0),
                "multi_hits": int(nb1.get("multi_hits",0) or 0),
                "avg_coverage": (
                    float(nb1.get("coverage_sum",0) or 0) / nb1_trials
                    if nb1_trials else 0.0
                ),
            }

            pending_side4 = [
                int(n)
                for n in pred.get("top5", [])
                if int(n) != int(pred.get("predicted"))
            ][:4]

            pending_compare = {
                "predicted": int(pred.get("predicted")),
                "side4": pending_side4,
                "action": "KAYNAK-LAB",
                "mode": "ORTAK",
                "signal": float(cal_signal),
                "quality": str(quality),
                "region": str(cal_region_name),
                "source_count": len(source_answers),
            }

            return {
                "chrome": self.chrome_connected,
                "seen": self.roulette_seen,
                "status": self.status,
                "history": h,
                "hot": self.hot or hot_calc,
                "cold": self.cold or cold_calc,
                "watch": watch,
                "predicted": pred["predicted"],
                "model_confidence": cal_signal,
                "raw_model_confidence": pred["model_score"],
                "model_share": pred["model_share"],
                "prediction_quality": quality,
                "learning_stage": learning_stage(self.validation["trials"]),
                "recent20": recent20,
                "walkforward": wf_profile,
                "weights": pred["weights"],
                "validation": dict(self.validation),
                "learning_spins": len(self.session_results),
                "live_memory_count": len(self.session_results),
                "source_hits": {
                    name: dict(self.source_hits.get(name, {}))
                    for name in SOURCE_NAMES
                },
                "source_consensus": pred.get("source_consensus", {}),
                "expert_trials": self.expert_trials,
                "expert_hits": {
                    name: dict(self.expert_hits[name])
                    for name in EXPERT_NAMES
                },
                "fairness": fairness_snapshot(h),
                "history_brain": historical_transition_snapshot(h, self.session_results),
                "web_history": pred.get("multi_table_transition") or external_transition_snapshot(h, self._cached_pool_seq),
                "web_source": self.external_source,
                "direct_history_status": self.direct_history_status,
                "direct_history_count": int(self.direct_history_count or 0),
                "restart_requested": bool(self.restart_requested),
                "restart_reason": str(self.restart_reason or ""),
                "autorecover_status": str(self.autorecover_status or "AUTO KURTARMA: HAZIR"),
                "autorecover_count": int(self.autorecover_count or 0),
                "autolobby_status": str(self.autolobby_status or "AUTO LOBİ: HAZIR"),
                "pragmatic_table_id": self.pragmatic_table_id,
                "operator_game_id": self.pragmatic_operator_game_id,
                "theme_code": self.pragmatic_theme_code,
                "web_verified": bool(self.web_verified),
                "web_match_run": int(self.web_match_run),
                "public_long_count": len(self.public_long_history),
                "public_long_source": self.public_long_source,
                "table500_count": len(self.table_history_500),
                "table500_source": self.table_history_source,
                "table_long_count": len(self.table_long_history),
                "table_long_source": self.table_long_source,
                "archive_count": int(self._cached_pool_spins or 0),
                "archive_tables": int(self._cached_pool_tables or 0),
                "archive_source": str(self.imported_source or "ORTAK HAVUZ: bekleniyor"),
                "bank_count": len(self.table_registry),
                "bank_total_spins": sum(
                    int((row or {}).get("long_count", 0) or 0)
                    for row in self.table_registry.values()
                ),
                "bank_rows": self.table_bank_rows(),
                "collector_refreshed": int(self.collector_refreshed or 0),
                "table_scan_status": str(self.table_scan_status or "MASA TARAMA: hazır"),
                "background_status": self.background_status,
                "score_error_status": self.score_error_status,
                "locked_live": {
                    "version": str((self.locked_live or {}).get("version") or "V2.9 FINAL CORE"),
                    "started": str((self.locked_live or {}).get("started") or ""),
                    "frozen": bool((self.locked_live or {}).get("frozen",False)),
                    "count": len((self.locked_live or {}).get("rows") or []),
                    "profiles": locked_live_profiles(self.locked_live),
                },
                "risk_profile": risk_analysis_snapshot(
                    self.validation,
                    self.neighbor1_stats_total,
                    self.neighbor_stats_total,
                ),
                "comparison_batch_count": len(self.display_compare_batch),
                "neighbor_records": neighbor_records,
                "neighbor_stats": neighbor_stats,
                "neighbor_batch_count": len(self.neighbor_display_batch),
                "neighbor1_records": neighbor1_records,
                "neighbor1_stats": neighbor1_stats,
                "neighbor1_batch_count": len(self.neighbor1_display_batch),
                "last_neighbor1_package": (
                    dict(self.last_neighbor1_package)
                    if isinstance(self.last_neighbor1_package, dict)
                    else None
                ),
                "last_neighbor2_package": (
                    dict(self.last_neighbor2_package)
                    if isinstance(self.last_neighbor2_package, dict)
                    else None
                ),
                "pro_decision": pro_decision,
                "source_answers": source_answers,
                "net_pick": dict(pred.get("net_pick") or {}),
                "pending_compare": pending_compare,
                "comparison_records": comparison_records,
                "coverage": theoretical_coverage_text(cal_region_name),
                "region_name": cal_region_name,
                "region_confidence": cal_region_conf,
                "region_scores": cal_regions,
                "raw_region_name": pred["region_name"],
                "raw_region_scores": pred["region_scores"],
                "neighbor_zone": pred["neighbor_zone"],
                "region_features": pred["region_features"],
                "table": self.table_name,
                "source": self.source,
                "last_update": self.last_update,
            }


def find_last20(obj):
    """
    Recursively search Pragmatic-style table metadata for:
    last20Results / hotNumbers / coldNumbers / tableName
    """
    if isinstance(obj, dict):
        if isinstance(obj.get("last20Results"), list):
            return {
                "results": obj.get("last20Results", []),
                "hot": obj.get("hotNumbers", []),
                "cold": obj.get("coldNumbers", []),
                "table": obj.get("tableName", ""),
            }

        for v in obj.values():
            found = find_last20(v)
            if found:
                return found

    elif isinstance(obj, list):
        for v in obj:
            found = find_last20(v)
            if found:
                return found

    elif isinstance(obj, str):
        s = obj.strip()
        if "last20Results" in s and len(s) < 2_000_000:
            try:
                nested = json.loads(s)
                return find_last20(nested)
            except Exception:
                pass

    return None


DOM_SCAN = r"""
(() => {
  function vis(el) {
    const r = el.getBoundingClientRect();
    if (r.width <= 1 || r.height <= 1) return false;
    const s = getComputedStyle(el);
    return s.display !== "none" && s.visibility !== "hidden";
  }

  const bodyText = ((document.body && document.body.textContent) || "")
    .slice(0, 120000)
    .replace(/\s+/g, " ")
    .toUpperCase();
  const hasActiveGameUi = /SONRAKI\s+OYUNU\s+BEKLEYIN|WAIT\s+FOR\s+NEXT\s+GAME|TOPLAM\s+BAHIS|TOTAL\s+BET|SICAK\s*&\s*SOGUK|SICAK\s*&\s*SOĞUK|HOT\s*&\s*COLD|VOISINS|ORPHELINS|TIERS|OTOMATIK\s+OYUN|AUTOMATIC\s+PLAY|\bSON\s*500\b|\bLAST\s*500\b/.test(bodyText);
  const tileSel = '[data-gameid],[data-game-id],[data-table-id],[data-tableid],[data-testid="wow-tile"],[data-testid*="tile" i],[class*="tile" i]';
  let lobbyCards = 0;
  if (!hasActiveGameUi) {
    const seenCards = new Set();
    for (const el of document.querySelectorAll(tileSel)) {
      const t = (el.textContent || "").replace(/\s+/g, " ").trim().toUpperCase();
      const hasId = !!(el.getAttribute("data-gameid") || el.getAttribute("data-game-id") || el.getAttribute("data-table-id") || el.getAttribute("data-tableid"));
      if (!hasId && !/(ROULETTE|RULET)/.test(t)) continue;
      if (!vis(el)) continue;
      const k = (t.slice(0, 60) + "|" + (el.getAttribute("data-gameid") || el.getAttribute("data-table-id") || "")).slice(0, 100);
      if (seenCards.has(k)) continue;
      seenCards.add(k);
      lobbyCards += 1;
      if (lobbyCards >= 3) break;
    }
  }
  const lobbyLike = !hasActiveGameUi && (
    lobbyCards >= 3 ||
    /\/lobby/i.test(location.pathname || "") ||
    /pragmatic\s*play\s*lobby/i.test(document.title || "")
  );
  if (lobbyLike) {
    return {
      title: document.title,
      url: location.href,
      lobbyLike: true,
      candidates: [],
      liveCandidates: []
    };
  }

  const exactNumber = /^(?:[0-9]|[12][0-9]|3[0-6])$/;
  const out = [];
  const seen = new Set();

  // 1) Check if the SON 500 / LAST 500 drawer is visibly open.
  // Check lightweight textContent length FIRST before calling vis(el) so we
  // never trigger synchronous layout/style reflow on thousands of DOM nodes!
  let son500Tab = null;
  for (const el of document.querySelectorAll('button,[role="tab"],[role="button"],div,span,a')) {
    if (el.children && el.children.length > 3) continue;
    const raw = el.textContent || "";
    if (raw.length < 5 || raw.length > 28) continue;
    const t = raw.replace(/\s+/g, " ").trim().toUpperCase();
    if ((t === "SON 500" || t === "LAST 500" || (/^(?:SON|LAST)\s*500$/.test(t))) && t.length <= 24) {
      if (vis(el)) {
        son500Tab = el;
        break;
      }
    }
  }

  let son500Open = false;
  if (son500Tab) {
    let p = son500Tab.parentElement;
    for (let depth = 1; depth <= 12 && p; depth++, p = p.parentElement) {
      const pr = p.getBoundingClientRect();
      if (pr.width > 620) break;
      const rawTxt = (p.textContent || "").replace(/\s+/g, " ").trim();
      const idx = rawTxt.toUpperCase().search(/\b(?:SON|LAST)\s*500\b/);
      const sliced = idx >= 0 ? rawTxt.slice(idx).replace(/^(?:SON|LAST)\s*500\b/i, "") : rawTxt;
      if (/%/.test(sliced)) continue;
      const nums = (sliced.match(/\b(?:[0-9]|[12][0-9]|3[0-6])\b/g) || []).map(Number);
      if (nums.length >= 40) {
        son500Open = true;
        seen.add(p);
        out.push({
          testid: p.getAttribute("data-testid") || "son500-drawer",
          cls: p.getAttribute("class") || "history-son500",
          collapsedBar: false,
          son500Grid: true,
          nums: nums.slice(0, 30)
        });
        break;
      }
    }
  }

  // 2) Standard history/recent/result selectors (single combined query).
  const combinedSel = '[data-testid*="history"],[data-testid*="result"],[data-testid*="recent"],[class*="history"],[class*="History"],[class*="recent"],[class*="Recent"],[class*="result"],[class*="Result"]';

  for (const el of document.querySelectorAll(combinedSel)) {
    if (seen.has(el)) continue;
    if (el.closest && el.closest('[data-gameid],[data-game-id],[data-table-id],[data-tableid],[data-testid="wow-tile"]')) continue;
    if (!vis(el)) continue;
    seen.add(el);

    let txt = (el.innerText || el.textContent || "").replace(/\s+/g, " ").trim();
    if (!txt) continue;
    if (/BAKIYE|BALANCE|TOPLAM\s*BAHIS|TOTAL\s*BET|VOISINS|ORPHELINS|TIERS/i.test(txt)) continue;

    const idx500 = txt.toUpperCase().search(/\b(?:SON|LAST)\s*500\b/);
    if (idx500 >= 0) {
      txt = txt.slice(idx500).replace(/^(?:SON|LAST)\s*500\b/i, "");
    } else if (/%|SICAK\s*&\s*SO[ĞG]UK|HOT\s*&\s*COLD|GRAF[İI]KLER/i.test(txt)) {
      const cutIdx = txt.toUpperCase().search(/SICAK\s*&\s*SO[ĞG]UK|HOT\s*&\s*COLD|GRAF[İI]KLER|%/);
      if (cutIdx >= 0) txt = txt.slice(0, cutIdx);
    }

    const nums = (txt.match(/\b(?:[0-9]|[12][0-9]|3[0-6])\b/g) || [])
      .map(Number);

    if (nums.length >= 5) {
      if (nums.length >= 40) son500Open = true;
      const isGrid = son500Open && nums.length >= 20;
      const limit = isGrid ? 30 : 10;
      out.push({
        testid: el.getAttribute("data-testid") || "",
        cls: el.getAttribute("class") || "",
        collapsedBar: !isGrid,
        son500Grid: isGrid,
        nums: nums.slice(0, limit)
      });
    }
  }

  // The large winning-number badge can update before the history grid.
  // Read only prominent numeric leaves; small chips, racetrack numbers and
  // statistic cells are deliberately penalized.
  const liveCandidates = [];
  for (const el of document.querySelectorAll('div,span,p,strong,b')) {
    if (el.children && el.children.length > 0) continue;
    const rawText = el.textContent || '';
    if (rawText.length === 0 || rawText.length > 6) continue;
    const text = rawText.trim();
    if (!exactNumber.test(text) || !vis(el)) continue;

    const r = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const font = parseFloat(style.fontSize || '0') || 0;
    let p = el;
    const hints = [];
    for (let depth = 0; depth < 4 && p; depth++, p = p.parentElement) {
      hints.push([
        p.id || '', p.getAttribute('class') || '',
        p.getAttribute('data-testid') || '', p.getAttribute('aria-label') || ''
      ].join(' '));
    }
    const hint = hints.join(' ').toLowerCase();
    let score = 0;
    if (font >= 30) score += 45;
    else if (font >= 24) score += 25;
    if (r.width >= 35 && r.height >= 35 && r.width <= 180 && r.height <= 180) score += 25;
    if (/(winner|winning|outcome|result|last.?number|number.?display)/i.test(hint)) score += 45;
    if (/(chip|bet|history|recent|statistic|hot|cold|limit|balance|stake|racetrack|tile|card)/i.test(hint)) score -= 80;
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    if (cx > innerWidth * 0.25 && cx < innerWidth * 0.75 && cy < innerHeight * 0.82) score += 10;

    if (score >= 70) {
      liveCandidates.push({
        n: Number(text), score,
        font: Math.round(font),
        x: Math.round(r.x), y: Math.round(r.y),
        w: Math.round(r.width), h: Math.round(r.height)
      });
    }
  }
  liveCandidates.sort((a, b) => b.score - a.score || (b.w*b.h) - (a.w*a.h));

  return {
    title: document.title,
    url: location.href,
    lobbyLike: false,
    candidates: out,
    liveCandidates: liveCandidates.slice(0, 5)
  };
})()
"""


HISTORY500_SCAN = r"""
(async () => {
  const ALLOW_EXPAND = true;
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => (s || "").replace(/\s+/g, " ").trim().toUpperCase();
  const numRe = /^(?:[0-9]|[12][0-9]|3[0-6])$/;

  function visibleStyle(el) {
    try {
      const win = (el.ownerDocument && el.ownerDocument.defaultView) || window;
      const s = win.getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return r.width > 1 && r.height > 1 &&
             s.display !== "none" && s.visibility !== "hidden" &&
             Number(s.opacity || 1) !== 0;
    } catch (_) {
      return false;
    }
  }

  function deepQueryAll(root, selector) {
    const out = [];
    const seenNodes = new Set();
    const seenRoots = new Set();
    const pushUnique = el => {
      if (el && !seenNodes.has(el)) {
        seenNodes.add(el);
        out.push(el);
      }
    };
    function visit(r) {
      if (!r || seenRoots.has(r)) return;
      seenRoots.add(r);
      let nodes = [];
      try { nodes = r.querySelectorAll(selector); } catch (_) { nodes = []; }
      for (const n of nodes) pushUnique(n);
      let all = [];
      try { all = r.querySelectorAll('*'); } catch (_) { all = []; }
      for (const el of all) {
        try { if (el.shadowRoot) visit(el.shadowRoot); } catch (_) {}
        try {
          if (String(el.tagName || '').toUpperCase() === 'IFRAME' && el.contentDocument) {
            visit(el.contentDocument);
          }
        } catch (_) {}
      }
    }
    visit(root);
    return out;
  }

  function ownTexts(el) {
    const vals = [];
    try {
      const tc = el.textContent || '';
      if (tc.length <= 16) vals.push(tc);
    } catch (_) {}
    for (const a of ['aria-label','title','data-value','data-number','data-result','data-role','value']) {
      try {
        const v = el.getAttribute(a);
        if (v) vals.push(v);
      } catch (_) {}
    }
    return vals;
  }

  function numericValue(el) {
    for (const raw of ownTexts(el)) {
      const t = norm(raw);
      if (numRe.test(t)) return Number(t);
    }
    return null;
  }

  function readableText(el) {
    try { return el.textContent || ''; } catch (_) { return ''; }
  }

  function parentOf(el) {
    if (!el) return null;
    if (el.parentElement) return el.parentElement;
    try {
      const root = el.getRootNode && el.getRootNode();
      if (root && root.host) return root.host;
    } catch (_) {}
    return null;
  }

  function sortedNumericLeaves(root, minTop = -1) {
    const recs = [];
    if (!root) return recs;
    const seenEls = new Set();
    for (const el of deepQueryAll(root, "*")) {
      if (seenEls.has(el)) continue;
      if (el.children && el.children.length > 3) continue;
      const n = numericValue(el);
      if (n === null || n < 0 || n > 36) continue;
      if (!visibleStyle(el)) continue;
      let childHasSameNumeric = false;
      try {
        for (const ch of el.children || []) {
          if (numericValue(ch) !== null) {
            childHasSameNumeric = true;
            break;
          }
        }
      } catch (_) {}
      if (childHasSameNumeric) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 4 || r.height < 4 || r.width > 75 || r.height > 65) continue;
      const cy = r.top + r.height / 2;
      if (minTop >= 0 && cy < minTop) continue;
      const ptxt = norm(readableText(parentOf(el) || el));
      if (/%|BAKIYE|BALANCE|TOPLAM\s*BAHIS|TOTAL\s*BET|VOISINS|ORPHELINS|TIERS|KOMŞU|KOMSU/.test(ptxt)) continue;
      seenEls.add(el);
      recs.push({n, x: r.left + r.width / 2, y: cy});
    }
    recs.sort((a, b) => Math.round(a.y / 8) - Math.round(b.y / 8) || a.x - b.x);
    return recs.map(r => r.n);
  }

  let all = deepQueryAll(document,
    'button,[role="tab"],[role="button"],div,span,a,svg'
  );

  function findHistoryTab() {
    let found = all.find(el => {
      if (el.children && el.children.length > 3) return false;
      const raw = readableText(el);
      if (raw.length < 5 || raw.length > 28) return false;
      const t = norm(raw);
      return (t === "SON 500" || t === "LAST 500") && visibleStyle(el);
    });
    if (found) return found;
    return all.find(el => {
      if (el.children && el.children.length > 3) return false;
      const raw = readableText(el);
      if (raw.length < 5 || raw.length > 28) return false;
      const t = norm(raw);
      return /\b(?:SON|LAST)\s*500\b/.test(t) && t.length <= 28 && visibleStyle(el);
    });
  }

  let tab = findHistoryTab();
  const autoButtons = (!tab && ALLOW_EXPAND) ? all.filter(el => {
    const raw = readableText(el);
    if (raw.length < 6 || raw.length > 40) return false;
    return /OTOMAT[İI]K\s*OYUN|AUTOMATIC\s*(PLAY|GAME)|AUTO\s*PLAY/.test(norm(raw)) && visibleStyle(el);
  }) : [];
  const autoFound = autoButtons.length > 0;
  let expandedDrawer = false;
  // CRITICAL: Only attempt to click the drawer expand toggle when ALLOW_EXPAND
  // is true (background collector only) AND the in-game OTOMATİK OYUN button
  // (autoFound) is visibly present on screen. Never click anything in a lobby!
  if (!tab && ALLOW_EXPAND && autoFound) {
    const autoRect = autoButtons[0].getBoundingClientRect();
    const toggles = [];
    for (const el of deepQueryAll(document, 'button,[role="button"],a,div,span,svg')) {
      if (!visibleStyle(el)) continue;
      if (el.closest && el.closest('[data-gameid],[data-game-id],[data-table-id],[data-tableid],[data-testid="wow-tile"]')) continue;
      const r = el.getBoundingClientRect();
      const text = norm(readableText(el));
      if (r.width < 10 || r.height < 10 || r.width > 95 || r.height > 80) continue;
      if (r.top < innerHeight * 0.42 || r.top > innerHeight * 0.97) continue;
      if (/OTOMAT|AUTOMATIC|BET|BAHİS|SPIN|VOISIN|ORPHELIN|TIERS|ROULETTE|RULET/.test(text)) continue;
      if (numRe.test(text)) continue;
      const dy = autoRect.top - r.bottom;
      const dx = Math.abs((r.left + r.width / 2) - autoRect.right);
      if (dy < -12 || dy > 95 || r.left < autoRect.left - 120 || r.right > autoRect.right + 120) continue;
      const hint = [
        el.id || '', el.getAttribute('class') || '',
        el.getAttribute('aria-label') || '', el.getAttribute('title') || '',
        el.getAttribute('data-testid') || '',
        (parentOf(el) && (parentOf(el).getAttribute('class') || '')) || ''
      ].join(' ').toLowerCase();
      let score = 65 - Math.min(40, Math.abs(dy - 22) / 2) - Math.min(25, dx / 8);
      if (/(history|statistic|result|drawer|expand|collapse|chevron|arrow|toggle|recent)/.test(hint)) score += 75;
      if (text === '' || text === '⌃' || text === '▲' || text === '˄' || text === '^') score += 25;
      if (score >= 55) {
        toggles.push({el, score});
      }
    }
    toggles.sort((a, b) => b.score - a.score);
    if (toggles.length) {
      try {
        toggles[0].el.click();
        expandedDrawer = true;
        await sleep(600);
        all = deepQueryAll(document,
          'button,[role="tab"],[role="button"],div,span,a,svg'
        );
        tab = findHistoryTab();
      } catch (_) {}
    }
  }

  let roots = [];

  function collectFromTab() {
    if (!tab) return;
    const tr = tab.getBoundingClientRect();
    let r = tab;
    for (let depth = 0; depth < 12 && r; depth++, r = parentOf(r)) {
      const rr = r.getBoundingClientRect();
      if (rr.width > 620) break;
      let nums = [];
      const rawTxt = (readableText(r) || "").replace(/\s+/g, " ").trim();
      const idx = rawTxt.toUpperCase().search(/\b(?:SON|LAST)\s*500\b/);
      const sliced = idx >= 0 ? rawTxt.slice(idx).replace(/^(?:SON|LAST)\s*500\b/i, "") : rawTxt;
      if (!/%/.test(sliced)) {
        const noMult = sliced.replace(/[0-9]{2,4}\s*[xX]/g, " ");
        nums = (noMult.match(/\b(?:[0-9]|[12][0-9]|3[0-6])\b/g) || []).map(Number);
      }
      if (nums.length < 40) {
        nums = sortedNumericLeaves(r, tr.bottom - 4);
      }
      if (nums.length >= 40 && nums.length <= 650) {
        roots.push({
          root: r,
          nums: nums.slice(0, 500),
          count: Math.min(500, nums.length),
          depth,
          source: 'son500-tab',
          score: Math.min(500, nums.length) * 3 + 250 - depth * 4
        });
      }
    }
  }

  collectFromTab();
  if (tab && ALLOW_EXPAND && !roots.length) {
    try { tab.click(); } catch (_) {}
    await sleep(350);
    collectFromTab();
  }

  // CRITICAL: Only read SON 500 numbers when the SON 500 tab is genuinely visible!
  // Never read the 430x390 box above OTOMATİK OYUN or whole-page clusters when
  // the drawer is collapsed, because that captures the 3D wheel (23, 10...) and
  // the 37-number betting grid!
  if (tab) {
    const tr = tab.getBoundingClientRect();

    // Tight drawer-bounded rectangle below the SON 500 tab header (never reaching
    // 430px left into the spinning 3D wheel).
    try {
      let leftBound = Math.max(0, tr.right - 345);
      const sicakEl = all.find(el => {
        const t = norm(readableText(el));
        return /SICAK\s*&\s*SO[ĞG]UK|HOT\s*&\s*COLD/.test(t) && visibleStyle(el);
      });
      if (sicakEl) {
        const sr = sicakEl.getBoundingClientRect();
        if (Math.abs(sr.top - tr.top) <= 30 && sr.left < tr.left) {
          leftBound = Math.max(0, sr.left - 14);
        }
      }
      let bottomBound = Math.min(innerHeight * 0.96, tr.bottom + 360);
      if (autoButtons.length) {
        const ar = autoButtons[0].getBoundingClientRect();
        if (ar.top > tr.bottom + 40) {
          bottomBound = Math.min(bottomBound, ar.top - 2);
        }
      }
      const rectRecs = [];
      const seenRectEls = new Set();
      for (const el of deepQueryAll(document, '*')) {
        if (!visibleStyle(el) || seenRectEls.has(el)) continue;
        const n = numericValue(el);
        if (n === null || n < 0 || n > 36) continue;
        let childNum = false;
        try {
          for (const ch of el.children || []) {
            if (numericValue(ch) !== null) { childNum = true; break; }
          }
        } catch (_) {}
        if (childNum) continue;
        const er = el.getBoundingClientRect();
        if (er.width < 4 || er.height < 4 || er.width > 55 || er.height > 50) continue;
        const cx = er.left + er.width / 2;
        const cy = er.top + er.height / 2;
        if (cx < leftBound || cx > tr.right + 28 || cy < tr.bottom - 2 || cy > bottomBound) continue;
        seenRectEls.add(el);
        rectRecs.push({n, x: cx, y: cy});
      }
      rectRecs.sort((a, b) => Math.round(a.y / 8) - Math.round(b.y / 8) || a.x - b.x);
      const rectNums = rectRecs.map(x => x.n);
      if (rectNums.length >= 40 && rectNums.length <= 650) {
        roots.push({
          root: document.body,
          nums: rectNums,
          count: rectNums.length,
          depth: 1,
          source: 'son500-tab',
          score: rectNums.length * 3 + 220
        });
      }
    } catch (_) {}
  }

  const lobbyTileSelector = [
    '[data-gameid]','[data-game-id]','[data-table-id]','[data-tableid]',
    '[data-testid="wow-tile"]','[data-testid*="tile" i]',
    '[data-testid*="game" i]','[data-testid*="table" i]',
    '[class*="tile" i]','[class*="card" i]','[class*="game" i]'
  ].join(',');
  let lobbyCardCount = 0;
  try {
    const seenCards = new Set();
    for (const el of deepQueryAll(document, lobbyTileSelector)) {
      if (!visibleStyle(el)) continue;
      const txt = norm(readableText(el));
      const hasId = !!(el.getAttribute('data-gameid') || el.getAttribute('data-game-id') || el.getAttribute('data-table-id') || el.getAttribute('data-tableid'));
      if (!hasId && !/(ROULETTE|RULET|ROLETA|PORTEKIZCESI\s*MEGA)/.test(txt)) continue;
      if (/BLACKJACK|BACCARAT|POKER|HISTORY|SON\s*500|LAST\s*500|OTOMATIK\s+OYUN|AUTOMATIC\s+PLAY|SIMDI\s+OYNANIYOR|OYUNA\s+DON/.test(txt)) continue;
      const key = (txt.slice(0,80) + '|' + (el.getAttribute('data-gameid') || el.getAttribute('data-table-id') || '')).slice(0,140);
      if (seenCards.has(key)) continue;
      seenCards.add(key);
      lobbyCardCount += 1;
    }
  } catch (_) {}
  const bodyT = norm(readableText(document.body || document.documentElement));
  const titleT = norm(document.title || '');
  const hasInGameLobbyButton = all.some(el => {
    try {
      if (!visibleStyle(el)) return false;
      const r = el.getBoundingClientRect();
      const t = norm([readableText(el), el.getAttribute && el.getAttribute('aria-label'), el.getAttribute && el.getAttribute('title')].join(' '));
      return /\b(LOBI|LOBBY)\b/.test(t) && r.top <= innerHeight * 0.24 && r.left >= innerWidth * 0.50;
    } catch (_) { return false; }
  });
  const activeGameUi = /SONRAKI\s+OYUNU\s+BEKLEYIN|WAIT\s+FOR\s+NEXT\s+GAME|BAKIYE|BALANCE|TOPLAM\s+BAHIS|TOTAL\s+BET|SICAK\s*&\s*SOGUK|SICAK\s*&\s*SOĞUK|HOT\s*&\s*COLD|KAZANCI|WINNINGS|JEU\s*0|VOISINS|ORPHELINS|TIERS/.test(bodyT);
  const earlyLobbyLike = !autoFound && !tab && !hasInGameLobbyButton && (
    lobbyCardCount >= 3 ||
    /\/lobby/i.test(location.pathname || '') ||
    (/\bRULET\b|\bROULETTE\b/.test(bodyT) && /STANDART|TURKCE|TÜRKÇE|HIZLI|PRIVE|PRIVÉ|VERSIYON/.test(bodyT) && lobbyCardCount >= 1)
  );

  roots.sort((a,b) => (b.score || b.count) - (a.score || a.count) || b.count - a.count || a.depth - b.depth);
  const best = roots[0] || null;
  const lobbyLike = earlyLobbyLike || (!autoFound && !best && (
    lobbyCardCount >= 3 ||
    (/\bRULET\b|\bROULETTE\b/.test(bodyT) && /STANDART|TURKCE|TÜRKÇE|HIZLI|PRIVE|PRIVÉ|VERSIYON/.test(bodyT) && lobbyCardCount >= 1)
  ));
  const hasHotColdPanel = /SICAK\s*&\s*SOGUK|SICAK\s*&\s*SOĞUK|HOT\s*&\s*COLD/.test(bodyT);
  const blockedTable = !lobbyLike && lobbyCardCount < 2 && hasInGameLobbyButton && /POWER\s*UP|PRIVE\s*LOUNGE|PRIVÉ\s*LOUNGE|GATES\s*OF\s*OLYMPUS|RULET\s*DELUXE|ROULETTE\s*DELUXE/.test(titleT + ' ' + bodyT);
  const hotColdOnly = !lobbyLike && lobbyCardCount < 2 && hasInGameLobbyButton && activeGameUi && hasHotColdPanel && !tab;
  const gameNoSon500 = blockedTable || hotColdOnly;

  return {
    title: document.title,
    url: location.href,
    expandedDrawer,
    foundTab: !!tab,
    autoFound,
    lobbyLike,
    lobbyCardCount,
    activeGameUi,
    blockedTable,
    hotColdOnly,
    gameNoSon500,
    source: best ? (best.source || '') : '',
    count: best ? best.nums.length : 0,
    nums: best ? best.nums.slice(0, 500) : []
  };
})()
"""

ACTIVE_HISTORY500_SCAN = HISTORY500_SCAN.replace(
    "const ALLOW_EXPAND = true;",
    "const ALLOW_EXPAND = false;",
)

COLLECTOR_LOBBY_CLICK_SCRIPT = r"""
(() => {
  const norm = s => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[İı]/g, 'I').replace(/\s+/g, ' ').trim().toUpperCase();
  const visible = el => {
    try {
      const s = getComputedStyle(el), r = el.getBoundingClientRect();
      return r.width > 4 && r.height > 4 &&
             s.display !== 'none' && s.visibility !== 'hidden' &&
             Number(s.opacity || 1) !== 0;
    } catch (_) { return false; }
  };
  function deepAll(root, selector) {
    const out = [];
    const seenRoots = new Set();
    const add = el => { if (el && !out.includes(el)) out.push(el); };
    function walk(r) {
      if (!r || seenRoots.has(r)) return;
      seenRoots.add(r);
      let nodes = [];
      try { nodes = Array.from(r.querySelectorAll(selector)); } catch (_) { nodes = []; }
      for (const n of nodes) add(n);
      let all = [];
      try { all = Array.from(r.querySelectorAll('*')); } catch (_) { all = []; }
      for (const el of all) {
        try { if (el.shadowRoot) walk(el.shadowRoot); } catch (_) {}
        try {
          if (String(el.tagName || '').toUpperCase() === 'IFRAME' && el.contentDocument) walk(el.contentDocument);
        } catch (_) {}
      }
    }
    walk(root);
    return out;
  }
  function metaText(el) {
    const vals = [];
    try { vals.push(el.innerText || ''); } catch (_) {}
    try { vals.push(el.textContent || ''); } catch (_) {}
    for (const a of ['aria-label','title','alt','data-testid','data-test','id','class']) {
      try { vals.push(el.getAttribute(a) || ''); } catch (_) {}
    }
    return vals.join(' ');
  }
  function clickIt(el) {
    try { el.scrollIntoView({block:'center', inline:'center'}); } catch (_) {}
    try {
      for (const t of ['pointerover','mouseover','mouseenter','mousemove','pointerdown','mousedown','pointerup','mouseup']) {
        el.dispatchEvent(new MouseEvent(t, {bubbles:true, cancelable:true, view:window}));
      }
    } catch (_) {}
    try { el.click(); return true; } catch (_) { return false; }
  }
  function clickable(el) {
    let p = el;
    for (let i = 0; i < 7 && p; i++, p = p.parentElement) {
      try {
        if (p.matches && p.matches('button,a,[role="button"],[tabindex]')) return p;
        if (p.onclick || getComputedStyle(p).cursor === 'pointer') return p;
      } catch (_) {}
    }
    return el;
  }

  const candidates = deepAll(document, 'button,a,[role="button"],[tabindex],div,span');
  const scored = [];
  for (const el of candidates) {
    if (!visible(el)) continue;
    const hit = clickable(el);
    if (!hit || !visible(hit)) continue;
    const r = hit.getBoundingClientRect();
    const text = norm(metaText(el) + ' ' + metaText(hit));
    let score = 0;
    if (/\b(LOBI|LOBBY)\b/.test(text)) score += 300;
    if (/PRAGMATIC\s*(PLAY)?\s*(LOBI|LOBBY)/.test(text)) score += 80;
    if (r.top <= innerHeight * 0.24) score += 55;
    if (r.left >= innerWidth * 0.55) score += 55;
    if (r.width >= 35 && r.width <= 180 && r.height >= 24 && r.height <= 90) score += 30;
    if (/ARAMA|SEARCH|OYUN\s*ARA|BAHIS|BET|SPIN|OTOMAT|AUTOMATIC|CHAT|SOUND|SES|AYAR|SETTING|GECMIS|HISTORY|SON\s*500|LAST\s*500/.test(text)) score -= 220;
    if (score >= 260) scored.push({el:hit, score, text:text.slice(0,80), x:Math.round(r.x), y:Math.round(r.y)});
  }
  scored.sort((a,b) => b.score - a.score || b.x - a.x);
  if (scored.length) {
    const ok = clickIt(scored[0].el);
    return {
      ok,
      clicked: ok,
      stage: 'in-game-lobby-button',
      text: scored[0].text,
      title: document.title || '',
      url: location.href
    };
  }

  // Fallback inside the same game UI: the round back arrow next to the Lobi
  // button usually goes to the Pragmatic lobby too. Do NOT navigate to the
  // operator search page from here.
  const backScored = [];
  for (const el of candidates) {
    if (!visible(el)) continue;
    const hit = clickable(el);
    if (!hit || !visible(hit)) continue;
    const r = hit.getBoundingClientRect();
    const text = norm(metaText(el) + ' ' + metaText(hit));
    let score = 0;
    if (/\b(BACK|GERI|GERİ|ARROW|CHEVRON|CLOSE|KAPAT)\b/.test(text)) score += 120;
    if (r.top <= innerHeight * 0.22) score += 45;
    if (r.left >= innerWidth * 0.50) score += 35;
    if (r.width >= 24 && r.width <= 75 && r.height >= 24 && r.height <= 75) score += 35;
    if (/CHAT|SOUND|SES|AYAR|SETTING|LOBI|LOBBY/.test(text)) score -= 40;
    if (score >= 170) backScored.push({el:hit, score, text:text.slice(0,80), x:Math.round(r.x), y:Math.round(r.y)});
  }
  backScored.sort((a,b) => b.score - a.score || b.x - a.x);
  if (backScored.length) {
    const ok = clickIt(backScored[0].el);
    return {
      ok,
      clicked: ok,
      stage: 'in-game-back-button',
      text: backScored[0].text,
      title: document.title || '',
      url: location.href
    };
  }

  return {
    ok: false,
    clicked: false,
    stage: 'lobby-button-not-found',
    title: document.title || '',
    url: location.href
  };
})()
"""


def build_multi_table_nav_scan(clicked_keys=None, click_cards=True):
    clicked_json = json.dumps(
        [str(x) for x in list(clicked_keys or [])[:2500]],
        ensure_ascii=False,
    )
    blocked_json = json.dumps(
        [str(x) for x in TAB_WALK_BLOCKED_TABLE_LABELS],
        ensure_ascii=False,
    )
    canonical_json = json.dumps(
        [dict(x) for x in PRAGMATIC_LOBBY_TABLES],
        ensure_ascii=False,
    )
    click_cards_json = json.dumps(bool(click_cards))
    return rf"""
(() => {{
  const norm = s => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[İı]/g, 'I').replace(/[Ğğ]/g, 'G').replace(/[Üü]/g, 'U')
    .replace(/[Şş]/g, 'S').replace(/[Öö]/g, 'O').replace(/[Çç]/g, 'C')
    .replace(/[Éé]/g, 'E').replace(/\s+/g, ' ').trim().toUpperCase();
  const PY_CLICKED_KEYS = new Set({clicked_json});
  const PY_BLOCKED_TABLE_LABELS = {blocked_json};
  const CANONICAL_TABLES = {canonical_json};
  const CANONICAL_PATTERNS = [];
  for (const item of CANONICAL_TABLES) {{
    for (const pat of (item.patterns || [])) {{
      const np = norm(pat);
      if (np) {{
        const esc = np.replace(/[.*+?^${{}}()|[\]\\]/g, '\\$&');
        CANONICAL_PATTERNS.push({{
          pat: np,
          re: new RegExp('(?:^|[^A-Z0-9])' + esc + '(?:$|[^A-Z0-9])'),
          item
        }});
      }}
    }}
  }}
  CANONICAL_PATTERNS.sort((a, b) => b.pat.length - a.pat.length || a.item.order - b.item.order);
  function matchCanonicalTable(rawText) {{
    const full = norm(rawText || '').replace(/(?:₺|TRY|EUR|USD|\$|€)\s*[0-9.,\s-]+.*$/g, '').trim();
    if (!full) return null;
    for (const row of CANONICAL_PATTERNS) {{
      if (row.re.test(full)) return row.item;
    }}
    return null;
  }}
  const blockedLabel = s => {{
    const t = norm(s || '');
    return PY_BLOCKED_TABLE_LABELS.some(b => b && t.includes(b));
  }};
  const PY_CLICK_CARDS = {click_cards_json};
  const visible = el => {{
    if (!el) return false;
    try {{
      const r=el.getBoundingClientRect(), s=getComputedStyle(el);
      return r.width>2 && r.height>2 && s.display!=='none' && s.visibility!=='hidden';
    }} catch (_) {{ return false; }}
  }};
  function deepQueryAll(root, selector) {{
    const out = [];
    const seenRoots = new Set();
    function walk(r) {{
      if (!r || seenRoots.has(r)) return;
      seenRoots.add(r);
      try {{
        for (const n of r.querySelectorAll(selector)) out.push(n);
      }} catch (_) {{}}
      try {{
        for (const el of r.querySelectorAll('*')) {{
          try {{ if (el.shadowRoot) walk(el.shadowRoot); }} catch (_) {{}}
          try {{
            if (String(el.tagName || '').toUpperCase() === 'IFRAME' && el.contentDocument) walk(el.contentDocument);
          }} catch (_) {{}}
        }}
      }} catch (_) {{}}
    }}
    walk(root);
    return out;
  }}
  const clickable = el => {{
    let p=el;
    for(let i=0;i<7 && p;i++,p=p.parentElement) {{
      if (p.matches && p.matches('button,a,[role="button"],[tabindex]')) return p;
      try {{
        if (p.onclick || getComputedStyle(p).cursor === 'pointer') return p;
      }} catch (_) {{}}
    }}
    return null;
  }};
  const href=String(location.href||'');
  const title=String(document.title||'');
  const host=String(location.hostname||'').toLowerCase();
  const path=String(location.pathname||'').toLowerCase();
  const bodyText=norm(document.body && document.body.innerText || '');
  const lobbyTileElements = deepQueryAll(
    document,
    '[data-testid="wow-tile"],[data-gameid],[data-game-id],[data-table-id],[data-tableid]'
  ).filter(visible);
  const providerContext = host.startsWith('games.')
    || host.startsWith('client.')
    || path.includes('/apps/lobby/')
    || path.includes('/desktop/roulette')
    || path.includes('/desktop/lobby')
    || norm(title).includes('PRAGMATIC PLAY LOBBY')
    || lobbyTileElements.length >= 2
    || !!matchCanonicalTable(bodyText);

  function hoverAndClick(el) {{
    if (!el) return false;
    try {{ el.scrollIntoView({{block:'center', inline:'center'}}); }} catch (_) {{}}
    try {{
      for (const type of ['mouseover','mouseenter','mousemove']) {{
        el.dispatchEvent(new MouseEvent(type, {{bubbles:true, cancelable:true, view:window}}));
      }}
    }} catch (_) {{}}
    try {{ el.click(); return true; }} catch (_) {{ return false; }}
  }}

  function operatorLobbyLauncher() {{
    const lobbyRe=/PRAGMATIC\s*PLAY\s*LOBBY/;
    const playRe=/\b(OYNA|PLAY|OPEN|AÇ|AC|BAŞLAT|BASLAT|GİR|GIR|ENTER)\b/;
    const tileSel='[data-testid*="tile" i],[data-testid*="game" i],[class*="card" i],[class*="game" i],[class*="tile" i],article,section';
    const raw=Array.from(document.querySelectorAll(tileSel+',button,a,[role="button"]')).filter(visible);
    const tiles=[];
    const seenTiles=new Set();
    for (const el of raw) {{
      const tile=(el.closest && el.closest(tileSel)) || el;
      if (!tile || !visible(tile) || seenTiles.has(tile)) continue;
      seenTiles.add(tile);
      tiles.push(tile);
    }}
    for (const tile of tiles) {{
      const text=norm([
        tile.innerText,tile.textContent,
        tile.getAttribute && tile.getAttribute('aria-label'),
        tile.getAttribute && tile.getAttribute('title'),
        tile.getAttribute && tile.getAttribute('data-testid')
      ].join(' '));
      if (!lobbyRe.test(text)) continue;
      if (/BLACKJACK|BACCARAT|POKER|SLOT|SWEET|BONANZA/.test(text)) continue;
      try {{
        tile.dispatchEvent(new MouseEvent('mouseover', {{bubbles:true, cancelable:true, view:window}}));
        tile.dispatchEvent(new MouseEvent('mouseenter', {{bubbles:true, cancelable:true, view:window}}));
      }} catch (_) {{}}
      const buttons=Array.from(tile.querySelectorAll('button,a,[role="button"],[tabindex]')).filter(visible);
      const play=buttons.find(b => playRe.test(norm([
        b.innerText,b.textContent,
        b.getAttribute && b.getAttribute('aria-label'),
        b.getAttribute && b.getAttribute('title')
      ].join(' ')))) || null;
      const hit=play || clickable(tile) || tile;
      if (hoverAndClick(hit)) {{
        return {{
          ok:true,mode:'navigating',stage:'pragmatic-lobby-card-play',
          clickedLabel:text.slice(0,120),title,url:href
        }};
      }}
    }}

    // If the search result has not loaded yet, actively type the exact term
    // shown in the user's screenshot into the casino search field.
    const inputs=Array.from(document.querySelectorAll('input,textarea,[contenteditable="true"],[role="searchbox"]')).filter(visible);
    const search=inputs.find(el => {{
      const meta=norm([
        el.getAttribute && el.getAttribute('placeholder'),
        el.getAttribute && el.getAttribute('aria-label'),
        el.getAttribute && el.getAttribute('title'),
        el.getAttribute && el.getAttribute('name'),
        el.id, typeof el.className==='string'?el.className:''
      ].join(' '));
      return /ARA|ARAMA|SEARCH|FIND|GAME|OYUN/.test(meta)
        || String(el.type||'').toLowerCase()==='search';
    }}) || null;
    if (search) {{
      try {{
        const wanted='pragmatic play lobby';
        const cur=String(search.value || search.textContent || '').toLowerCase();
        if (!cur.includes('pragmatic')) {{
          search.focus();
          if ('value' in search) search.value=wanted;
          else search.textContent=wanted;
          search.dispatchEvent(new Event('input', {{bubbles:true}}));
          search.dispatchEvent(new Event('change', {{bubbles:true}}));
          search.dispatchEvent(new KeyboardEvent('keyup', {{bubbles:true,key:'Enter',code:'Enter'}}));
          return {{ok:true,mode:'navigating',stage:'pragmatic-lobby-search-typed',title,url:href}};
        }}
      }} catch (_) {{}}
    }}
    return null;
  }}

  if (!providerContext) {{
    const launched=operatorLobbyLauncher();
    if (launched) return launched;
    return {{ok:true,mode:'waiting',stage:'provider-context',title,url:href}};
  }}

  const visibleControls = deepQueryAll(
    document,
    'button,a,[role="button"],[tabindex],li,nav *,aside *,div,span,p,h1,h2,h3'
  ).filter(visible);

  // V2.9.42: if a real game overlay is visible, stop before the
  // generic lobby/card scanner. Some operators keep the lobby DOM behind the
  // table; the presence of visible SON500 or the in-game Lobi button is more
  // important than stale lobby cards.
  const hasSon500Control = visibleControls.some(el => {{
    const t = norm([
      el.innerText, el.textContent,
      el.getAttribute && el.getAttribute('aria-label'),
      el.getAttribute && el.getAttribute('title'),
      el.getAttribute && el.getAttribute('data-testid')
    ].join(' '));
    return /\b(SON|LAST)\s*500\b/.test(t);
  }});
  const hasInGameLobbyButton = visibleControls.some(el => {{
    const r = el.getBoundingClientRect();
    const t = norm([
      el.innerText, el.textContent,
      el.getAttribute && el.getAttribute('aria-label'),
      el.getAttribute && el.getAttribute('title'),
      el.getAttribute && el.getAttribute('data-testid')
    ].join(' '));
    return /\b(LOBI|LOBBY)\b/.test(t) && r.top <= innerHeight * 0.28 && r.left >= innerWidth * 0.45;
  }});
  const lobbyTileCount = lobbyTileElements.length;
  const activeGameUi = /SONRAKI\s+OYUNU\s+BEKLEYIN|WAIT\s+FOR\s+NEXT\s+GAME|BAKIYE|BALANCE|TOPLAM\s+BAHIS|TOTAL\s+BET|SICAK\s*&\s*SOGUK|SICAK\s*&\s*SOĞUK|HOT\s*&\s*COLD|KAZANCI|WINNINGS|JEU\s*0|VOISINS|ORPHELINS|TIERS|OTOMATIK\s+OYUN|AUTOMATIC\s+PLAY/.test(bodyText);
  const blockedActiveTable = blockedLabel(title + ' ' + bodyText);
  const gameOverlayLikely = lobbyTileCount < 2 && (hasInGameLobbyButton || (hasSon500Control && /BAKIYE|BALANCE|OTOMATIK|AUTOMATIC|BAHIS|BET|SICAK|HOT|VOISINS|TIERS|ORPHELINS|JEU/.test(bodyText)));
  if (gameOverlayLikely) {{
    if (blockedActiveTable) {{
      return {{
        ok:true,
        mode:'game_blocked',
        stage:'active-game-blocked',
        title,url:href,
        reason:'bloklu masa'
      }};
    }}
    if (hasSon500Control) {{
      return {{
        ok:true,
        mode:'game_has_son500',
        stage:'active-game-has-son500',
        title,url:href,
        reason:'SON500 paneli var'
      }};
    }}
    if (activeGameUi) {{
      return {{
        ok:true,
        mode:'game_no_son500',
        stage:'active-game-no-son500',
        title,url:href,
        reason:'SON500 paneli yok'
      }};
    }}
  }}

  // If we are in the lobby and a floating mini-player bar ("Şimdi oynanıyor / Oyuna dön > | ✕")
  // is open at the bottom-right from the previous table, close its ✕ button immediately.
  if (lobbyTileCount >= 2) {{
    for (const el of visibleControls) {{
      const t = norm(el.innerText || el.textContent || '');
      if (!/SIMDI\s+OYNANIYOR|OYUNA\s+DON|NOW\s+PLAYING|RETURN\s+TO\s+GAME/.test(t)) continue;
      let box = el;
      for (let k = 0; k < 5 && box && box.parentElement; k++, box = box.parentElement) {{
        const br = box.getBoundingClientRect();
        if (br.top >= innerHeight * 0.65 && br.width >= 180 && br.height <= 140) {{
          const btns = Array.from(box.querySelectorAll('button,a,[role="button"],svg,[class*="close" i]')).filter(visible);
          btns.sort((a, b) => b.getBoundingClientRect().right - a.getBoundingClientRect().right);
          const closeHit = btns[0] && (clickable(btns[0]) || btns[0]);
          if (closeHit && closeHit.getBoundingClientRect().left >= br.left + br.width * 0.72) {{
            try {{ closeHit.click(); }} catch (_) {{}}
          }}
          break;
        }}
      }}
    }}
  }}

  const scanState=window.__rouletteLobbyScanState
    || (window.__rouletteLobbyScanState={{
      menuAttemptAt:0,
      categoryAttemptAt:0,
      categoryAttempts:0,
      categoryFirstSeenAt:0,
      rouletteRoomEntered:false
    }});
  const selected=el => {{
    if (!el) return false;
    const cls=String(el.className && el.className.baseVal || el.className || '');
    return el.getAttribute('aria-selected')==='true'
      || el.getAttribute('aria-pressed')==='true'
      || el.getAttribute('aria-current')==='true'
      || el.getAttribute('data-active')==='true'
      || /(^|[\s_-])(active|selected|current|checked)([\s_-]|$)/i.test(cls);
  }};

  const categoryLabels=new Set(['RULET','ROULETTE','RULET MASALARI','ROULETTE TABLES']);
  const sidebarCandidates = visibleControls.map(el => {{
    const label = norm(el.innerText || el.textContent || '');
    const aria = norm([
      el.getAttribute && el.getAttribute('aria-label'),
      el.getAttribute && el.getAttribute('title'),
      el.getAttribute && el.getAttribute('data-testid')
    ].join(' '));
    if (!categoryLabels.has(label) && !/\b(RULET|ROULETTE)\b/.test(aria)) return null;
    if (el.closest && el.closest('[data-testid*="tile" i],[class*="tile" i],[class*="card" i]')) return null;
    const r = el.getBoundingClientRect();
    if (r.left > Math.max(280, window.innerWidth * 0.30) || r.top < 70 || r.width > 300 || r.height > 95) return null;
    const hit = clickable(el) || (el.closest && el.closest('li,a,button,[role="button"],[tabindex]')) || el.parentElement || el;
    const exactScore = categoryLabels.has(label) ? 200 : 80;
    return {{el, hit, score: exactScore - r.left - Math.abs(r.height - 36)}};
  }}).filter(Boolean).sort((a, b) => b.score - a.score);
  const category = sidebarCandidates[0] ? sidebarCandidates[0].hit : null;
  const categoryEl = sidebarCandidates[0] ? sidebarCandidates[0].el : null;

  // Detect whether we are inside the dedicated "Rulet" room vs still on the
  // "Size Özel" (For You) landing page of Pragmatic Play Lobby.
  const hasRouletteFilterPills = /\b(STANDART|STANDARD)\b/.test(bodyText)
    && /\b(ANA\s*DILINIZDE|VERSIYONLAR|VERSIONS|OTOMATIK|AUTO)\b/.test(bodyText);
  const hasTopRouletteHeader = visibleControls.some(el => {{
    const r = el.getBoundingClientRect();
    const t = norm(el.innerText || el.textContent || '');
    return (t === 'RULET' || t === 'ROULETTE') && r.top <= 105 && r.left >= 32 && r.left <= 260 && r.height <= 64;
  }});
  const hasExpandedHomeSidebar = /\bSIZE\s*OZEL\b|\bFOR\s*YOU\b/.test(bodyText)
    || (/\bBLACKJACK\b/.test(bodyText) && /\bBACCARAT\b/.test(bodyText) && /\bPOKER\b/.test(bodyText));
  const hasHomeBannerOrRecent = /\bSON\s+OYNANAN\s+OYUNLAR\b|\bRECENTLY\s+PLAYED\b|\bONE\s+BLACKJACK\b/.test(bodyText);

  if ((hasRouletteFilterPills || hasTopRouletteHeader) && !hasHomeBannerOrRecent) {{
    scanState.rouletteRoomEntered = true;
  }} else if (hasExpandedHomeSidebar || hasHomeBannerOrRecent) {{
    scanState.rouletteRoomEntered = false;
  }}

  const inRouletteRoom = !hasHomeBannerOrRecent && (
    hasRouletteFilterPills
    || (!hasExpandedHomeSidebar && (
      hasTopRouletteHeader
      || !!scanState.rouletteRoomEntered
      || (lobbyTileCount >= 6 && !/\b(BLACKJACK|BACCARAT|POKER|SLOT|OYUN\s*SOVU|ASYA\s*OYUNLARI)\b/.test(bodyText))
    ))
  );

  let categoryState = inRouletteRoom ? 'selected' : 'missing';
  if (!inRouletteRoom) {{
    if (category || categoryEl) {{
      categoryState = 'unconfirmed';
      if (!scanState.categoryFirstSeenAt) scanState.categoryFirstSeenAt = Date.now();
      if (Date.now() - scanState.categoryAttemptAt >= 850) {{
        try {{
          const targetEl = categoryEl || category;
          const r = targetEl.getBoundingClientRect();
          const cx = Math.round(r.left + r.width * 0.5);
          const cy = Math.round(r.top + r.height * 0.5);
          const clickNodes = [];
          const ptEl = document.elementFromPoint ? document.elementFromPoint(cx, cy) : null;
          if (ptEl) clickNodes.push(ptEl);
          let p = categoryEl || category;
          for (let k = 0; k < 4 && p && p !== document.body; k++, p = p.parentElement) {{
            const pr = p.getBoundingClientRect();
            if (pr.height <= 85 && pr.width <= 320 && !clickNodes.includes(p)) {{
              clickNodes.push(p);
            }}
          }}
          if (category && !clickNodes.includes(category)) clickNodes.push(category);
          for (const node of clickNodes) {{
            if (!node) continue;
            for (const evType of ['pointerover','mouseover','mouseenter','mousemove','pointerdown','mousedown','pointerup','mouseup']) {{
              try {{
                node.dispatchEvent(new MouseEvent(evType, {{bubbles:true, cancelable:true, view:window, clientX:cx, clientY:cy}}));
              }} catch (_) {{}}
            }}
            try {{ node.click(); }} catch (_) {{}}
          }}
          scanState.categoryAttemptAt = Date.now();
          scanState.categoryAttempts = (scanState.categoryAttempts || 0) + 1;
        }} catch (e) {{
          return {{ok:false,mode:'waiting',stage:'roulette-click-failed',reason:String(e)}};
        }}
      }}
      // Do NOT fall through to card clicking while still on "Size Özel"; wait for
      // the "Rulet" room to open first!
      return {{
        ok:true,mode:'navigating',stage:'roulette-selecting',
        attempts:scanState.categoryAttempts,title,url:href
      }};
    }} else if (Date.now()-scanState.menuAttemptAt>=2000) {{
      const menuWords=/MENU|CATEGORY|CATEGORIES|SIDEBAR|DRAWER|EXPAND|COLLAPSE|NAVIGATION|ARROW|CHEVRON/;
      const arrows=visibleControls.map(el => {{
        const hit=clickable(el) || el;
        if (!hit || !visible(hit)) return null;
        const r=hit.getBoundingClientRect();
        if (r.left > Math.max(150,window.innerWidth*0.18) || r.width>100 || r.height>100) return null;
        const meta=norm([
          hit.getAttribute && hit.getAttribute('aria-label'),
          hit.getAttribute && hit.getAttribute('title'),
          hit.getAttribute && hit.getAttribute('data-testid'),
          hit.id,
          typeof hit.className==='string'?hit.className:''
        ].join(' '));
        const icon=hit.querySelector && hit.querySelector('svg,[class*="arrow" i],[class*="chevron" i]');
        const text=norm(hit.innerText || hit.textContent);
        if (!menuWords.test(meta) && !(icon && !text)) return null;
        return {{hit,score:(menuWords.test(meta)?100:0)+(icon?20:0)-r.left}};
      }}).filter(Boolean).sort((a,b)=>b.score-a.score);
      if (arrows.length) {{
        try {{
          arrows[0].hit.click();
          scanState.menuAttemptAt=Date.now();
        }} catch (e) {{
          return {{ok:false,mode:'waiting',stage:'menu-click-failed',reason:String(e)}};
        }}
        return {{ok:true,mode:'navigating',stage:'menu-opened',title,url:href}};
      }}
    }}
    return {{ok:true,mode:'navigating',stage:'roulette-selecting',title,url:href}};
  }}

  const cards=[];
  const cardHits=[];
  const seen=new Set();
  const badCardText=/TOURNAMENT|HISTORY|SON 500|LAST 500|BLACKJACK|BACCARAT|POKER|AUTO PLAY|OTOMATIK OYUN|BAHIS|BET|CHIP|ÇIP|SIMDI OYNANIYOR|ŞİMDİ OYNANIYOR|OYUNA DON|OYUNA DÖN|NOW PLAYING|RETURN TO GAME/;
  function attrAny(el,names) {{
    for (const n of names) {{
      try {{
        const v=el.getAttribute(n);
        if (v) return String(v).trim();
      }} catch (_) {{}}
    }}
    return '';
  }}
  function firstAttrInTree(el,names) {{
    let p=el;
    for(let i=0;i<6 && p;i++,p=p.parentElement) {{
      const v=attrAny(p,names);
      if (v) return v;
    }}
    return '';
  }}
  function hrefOf(el) {{
    let p=el;
    for(let i=0;i<6 && p;i++,p=p.parentElement) {{
      const h=String(p.href || p.getAttribute && (
        p.getAttribute('href') || p.getAttribute('data-href') ||
        p.getAttribute('data-url') || p.getAttribute('data-launch-url') ||
        p.getAttribute('data-game-url') || ''
      ) || '').trim();
      if (h) {{
        try {{ return new URL(h, location.href).toString(); }} catch (_) {{ return h; }}
      }}
    }}
    return '';
  }}

  const tileSelector=[
    '[data-gameid]','[data-game-id]','[data-table-id]','[data-tableid]',
    '[data-testid="wow-tile"]','[data-testid*="tile" i]',
    '[data-testid*="table" i]','[class*="tile" i]'
  ].join(',');
  let candidates=deepQueryAll(document, tileSelector);
  if (!candidates.length) {{
    candidates=deepQueryAll(document, '[class*="card" i],[class*="game" i],a,div,span');
  }}

  const rouletteHeading=Array.from(document.querySelectorAll('h1,h2,h3,[role="heading"]'))
    .some(el => visible(el) && /^(RULET|ROULETTE)$/.test(norm(el.innerText || el.textContent)));
  const rouletteContext = rouletteHeading
    || categoryState === 'selected'
    || ((path.includes('/apps/lobby/') || path.includes('/desktop/roulette') || host.startsWith('client.')) && /\b(RULET|ROULETTE)\b/.test(bodyText))
    || lobbyTileCount >= 2;

  function findCardBox(el) {{
    if (!el) return null;
    if (el.closest) {{
      const wow = el.closest('[data-testid="wow-tile"],[data-gameid],[data-game-id],[data-table-id],[data-tableid]');
      if (wow && visible(wow)) {{
        const wr = wow.getBoundingClientRect();
        if (wr.width >= 75 && wr.width <= 490 && wr.height >= 60 && wr.height <= 450) {{
          return wow;
        }}
      }}
    }}
    let p = el;
    for (let i = 0; i < 8 && p && p !== document.body; i++, p = p.parentElement) {{
      if (!visible(p)) continue;
      const r = p.getBoundingClientRect();
      if (r.width >= 85 && r.width <= 470 && r.height >= 65 && r.height <= 430) {{
        return p;
      }} else if (r.width > 500 || r.height > 460) {{
        break;
      }}
    }}
    return null;
  }}

  function extractCleanTableTitle(tile, rawFallback) {{
    const rawStr = String(tile.innerText || tile.textContent || rawFallback || '');
    const canon = matchCanonicalTable(rawStr);
    if (canon) return canon.name;
    const lines = rawStr
      .split(/[\r\n]+/)
      .map(s => norm(s))
      .filter(Boolean);
    for (let idx = 0; idx < lines.length; idx++) {{
      let ln = lines[idx];
      if (!/(ROULETTE|RULET|ROLETA)/.test(ln)) continue;
      if (idx + 1 < lines.length && /^(?:[0-9]{{1,3}}|VIP|AZURE|RUBY|MACAO|ITALIANA|THE\s*CLUB)$/.test(lines[idx + 1])) {{
        ln = (ln + ' ' + lines[idx + 1]).trim();
      }}
      let cleaned = ln
        .replace(/(?:₺|TRY|EUR|USD|\$|€)\s*[0-9.,\s-]+.*$/g, '')
        .replace(/^(?:[0-9]{{1,2}}\s+){{2,}}/g, '')
        .trim();
      if (cleaned.length >= 4 && /(ROULETTE|RULET|ROLETA)/.test(cleaned)) return cleaned.slice(0, 120);
    }}
    let full = norm(rawStr)
      .replace(/(?:₺|TRY|EUR|USD|\$|€)\s*[0-9.,\s-]+.*$/g, '')
      .replace(/^(?:[0-9]{{1,2}}\s+){{2,}}/g, '')
      .replace(/\s+/g, ' ')
      .trim();
    const m = full.match(/([A-Z0-9 ._-]{{0,32}}(?:ROULETTE|RULET|ROLETA)[A-Z0-9 ._-]{{0,32}})/);
    if (m && m[1].trim().length >= 4) return m[1].trim().slice(0, 120);
    return full.slice(0, 120);
  }}

  function cardImageSignature(tile) {{
    if (!tile || !tile.querySelector) return '';
    try {{
      const img = tile.querySelector('img[src]');
      if (img && img.src) {{
        const u = new URL(img.src, location.href);
        const seg = (u.pathname || '').split('/').filter(Boolean).pop() || '';
        if (seg) return seg.toUpperCase().slice(0, 64);
      }}
    }} catch (_) {{}}
    return '';
  }}

  function clickCardThumbnail(tile) {{
    if (!tile) return false;
    const isHeartEl = el => {{
      if (!el) return false;
      const tr = tile.getBoundingClientRect();
      let p = el;
      for (let i = 0; i < 5 && p && p !== tile; i++, p = p.parentElement) {{
        const meta = norm([
          p.getAttribute && p.getAttribute('aria-label'),
          p.getAttribute && p.getAttribute('title'),
          p.getAttribute && p.getAttribute('data-testid'),
          typeof p.className === 'string' ? p.className : ''
        ].join(' '));
        if (/FAV|HEART|LIKE|BOOKMARK|WISH/.test(meta)) return true;
        const pr = p.getBoundingClientRect();
        if (pr.width < 52 && pr.height < 52 && pr.top > tr.top + tr.height * 0.60 && pr.left > tr.left + tr.width * 0.65) {{
          return true;
        }}
      }}
      return false;
    }};

    let innerHit = null;
    try {{
      const innerCandidates = Array.from(tile.querySelectorAll('a,button,[role="button"],img,div')).filter(el => visible(el) && !isHeartEl(el));
      innerHit = innerCandidates.find(el => {{
        const r = el.getBoundingClientRect();
        const tr = tile.getBoundingClientRect();
        return r.width >= tr.width * 0.45 && r.height >= tr.height * 0.35;
      }}) || null;
    }} catch (_) {{}}
    let hit = innerHit || tile;
    if (isHeartEl(hit)) hit = tile;
    try {{
      const r = tile.getBoundingClientRect();
      const cx = Math.round(r.left + r.width * 0.48);
      const cy = Math.round(r.top + r.height * 0.36);
      for (const target of [hit, tile]) {{
        if (!target) continue;
        for (const evType of ['pointerover','mouseover','mouseenter','mousemove','pointerdown','mousedown','pointerup','mouseup']) {{
          target.dispatchEvent(new MouseEvent(evType, {{bubbles:true, cancelable:true, view:window, clientX:cx, clientY:cy}}));
        }}
      }}
    }} catch (_) {{}}
    try {{
      hit.click();
      if (hit !== tile) {{
        try {{ tile.click(); }} catch (_) {{}}
      }}
      return true;
    }} catch (_) {{
      try {{ tile.click(); return true; }} catch (__) {{ return false; }}
    }}
  }}

  const rawCardItems = [];
  const seenTiles = new Set();
  const seenBoxes = [];
  for (const raw of candidates.slice(0,3500)) {{
    if (!visible(raw)) continue;
    const tile = findCardBox(raw);
    if (!tile || !visible(tile) || seenTiles.has(tile)) continue;
    const rect = tile.getBoundingClientRect();
    if (seenBoxes.some(b => Math.abs(b.left - rect.left) < 24 && Math.abs(b.top - rect.top) < 24)) continue;

    let tableId=firstAttrInTree(tile, ['data-table-id','data-tableid','tableid','table-id','data-table_id']);
    let gameId=firstAttrInTree(tile, ['data-gameid','data-game-id','gameid','game-id','data-game_id']);
    const rawTileText = [
      tile.innerText, tile.textContent,
      tile.getAttribute && tile.getAttribute('aria-label'),
      tile.getAttribute && tile.getAttribute('title')
    ].join('\n');
    const text = norm(rawTileText);
    if ((!text && !tableId && !gameId) || text.length>420) continue;
    if (badCardText.test(text)) continue;

    const canon = matchCanonicalTable(rawTileText);
    if (canon && canon.blocked) continue;
    if (blockedLabel(text)) continue;

    const textLooksRoulette = !!canon || /(ROULETTE|RULET|ROLETA)/.test(text);
    if (!textLooksRoulette && !(rouletteContext && (tableId || gameId))) continue;

    let cleanTitle = canon ? canon.name : extractCleanTableTitle(tile, text);
    if (blockedLabel(cleanTitle)) continue;
    if (!canon && !/(ROULETTE|RULET|ROLETA)/.test(norm(cleanTitle)) && !(rouletteContext && (gameId || tableId))) continue;
    if (badCardText.test(norm(cleanTitle))) continue;

    let cardHref = hrefOf(tile);
    const testid = String(tile.getAttribute && tile.getAttribute('data-testid') || '');
    if (cardHref) {{
      try {{
        const u = new URL(cardHref, location.href);
        tableId = tableId || u.searchParams.get('tableId') || u.searchParams.get('table_id') || '';
        gameId = gameId || u.searchParams.get('gameId') || u.searchParams.get('game_id') || u.searchParams.get('openGames') || '';
        cardHref = u.toString();
      }} catch (_) {{}}
    }}

    if (!cleanTitle && (gameId || tableId)) cleanTitle = 'ROULETTE ' + (gameId || tableId);
    const imgSig = cardImageSignature(tile);
    const key = canon
      ? canon.key
      : (tableId || gameId || (norm(cleanTitle) + (imgSig ? '|' + imgSig : ''))).slice(0, 200);
    if (!key) continue;
    seenTiles.add(tile);
    seenBoxes.push(rect);
    rawCardItems.push({{
      key,
      label: cleanTitle,
      canonOrder: canon ? canon.order : 999,
      href: cardHref,
      testid,
      table_id: tableId,
      game_id: gameId,
      tile,
      rect
    }});
  }}

  // Sort by canonical 1..32 lobby order first, then row-by-row (top to bottom) and column-by-column (left to right)!
  rawCardItems.sort((a, b) => {{
    if (a.canonOrder !== b.canonOrder) {{
      return a.canonOrder - b.canonOrder;
    }}
    const rowTol = Math.max(22, Math.min(a.rect.height, b.rect.height) * 0.45);
    if (Math.abs(a.rect.top - b.rect.top) > rowTol) {{
      return a.rect.top - b.rect.top;
    }}
    return a.rect.left - b.rect.left;
  }});

  const titleCounts = new Map();
  for (const item of rawCardItems) {{
    const dupIdx = (titleCounts.get(item.key) || 0) + 1;
    titleCounts.set(item.key, dupIdx);
    const isCanon = item.canonOrder < 999;
    const uniqueKey = (!isCanon && !item.table_id && dupIdx > 1) ? (item.key + ' #' + dupIdx) : item.key;
    const uniqueLabel = (!isCanon && !item.table_id && dupIdx > 1) ? (item.label + ' #' + dupIdx) : item.label;
    if (seen.has(uniqueKey)) continue;
    seen.add(uniqueKey);
    cards.push({{
      key: uniqueKey,
      label: uniqueLabel,
      order: item.canonOrder,
      href: item.href,
      testid: item.testid,
      table_id: item.table_id,
      game_id: item.game_id
    }});
    cardHits.push({{
      key: uniqueKey,
      label: uniqueLabel,
      order: item.canonOrder,
      hit: item.tile,
      rect: item.rect
    }});
  }}

  if (!scanState.clickedKeys) scanState.clickedKeys = {{}};
  const nowMs = Date.now();
  const clickReady = nowMs - Number(scanState.lastCardClickAt || 0) >= 420;

  // If the "Masa dolu" (Table full) modal from a VIP/Privé table is open on screen,
  // dismiss it by clicking "Tamam" / "OK" and skip that card without stopping the scan.
  if (/\bMASA\s+DOLU\b|\bBU\s+OZEL\s+MASA\s+SU\s+ANDA\s+DOLU\b|\bTABLE\s+FULL\b/.test(bodyText)) {{
    const okBtns = Array.from(document.querySelectorAll('button,[role="button"],div,span')).filter(el => {{
      if (!visible(el)) return false;
      const t = norm(el.innerText || el.textContent || '');
      return t === 'TAMAM' || t === 'OK' || t === 'KAPAT' || t === 'CLOSE';
    }});
    if (okBtns.length) {{
      try {{ (clickable(okBtns[0]) || okBtns[0]).click(); }} catch (_) {{}}
    }}
    return {{
      ok: true,
      mode: 'masa_dolu_skip',
      stage: 'masa-dolu-modal-closed',
      clickedLabel: 'Masa dolu (atlandı)',
      cards,
      title,
      url: href
    }};
  }}

  const isCardClicked = c =>
    PY_CLICKED_KEYS.has(c.key)
    || PY_CLICKED_KEYS.has(norm(c.key))
    || PY_CLICKED_KEYS.has(c.label)
    || PY_CLICKED_KEYS.has(norm(c.label));
  const unclickedCards = cardHits.filter(c => !isCardClicked(c));

  // If Korece Rulet (Korean Roulette) at the end of the lobby has already been
  // clicked and collected AND there are no remaining unclicked cards in the row,
  // stop the lobby scan right at Korece Rulet!
  const koreceDone = cardHits.some(c =>
    /\bKORECE\s*RULET\b|\bKOREAN\s*ROULETTE\b|\bKORE\s*RULET\b/.test(norm(c.label)) &&
    isCardClicked(c)
  ) || PY_CLICKED_KEYS.has('KORECE RULET') || PY_CLICKED_KEYS.has('Korece Rulet');
  if (koreceDone && unclickedCards.length === 0) {{
    return {{
      ok: true,
      mode: 'korece_rulet_stop',
      stage: 'korece-rulet-completed',
      clickedLabel: 'Korece Rulet',
      cards,
      title,
      url: href
    }};
  }}

  const scrollCandidates=[];
  if (cardHits.length && cardHits[0].hit) {{
    let p = cardHits[0].hit.parentElement;
    while (p && p !== document.body && p !== document.documentElement) {{
      if (p.scrollHeight > p.clientHeight + 10 && p.clientHeight > 100) {{
        scrollCandidates.push(p);
      }}
      p = p.parentElement;
    }}
  }}
  const root=document.scrollingElement || document.documentElement || document.body;
  if (root && root.scrollHeight>root.clientHeight+12 && !scrollCandidates.includes(root)) scrollCandidates.push(root);
  for (const el of Array.from(document.querySelectorAll('*')).slice(0,2500)) {{
    if (scrollCandidates.includes(el)) continue;
    const style=getComputedStyle(el);
    const r=el.getBoundingClientRect();
    if ((style.overflowY==='auto' || style.overflowY==='scroll' || style.overflowY==='overlay')
        && el.scrollHeight>el.clientHeight+12 && r.width>120 && r.height>100) {{
      scrollCandidates.push(el);
    }}
  }}
  const scrollTarget=scrollCandidates[0] || null;
  let scrollTop=0,scrollHeight=0,clientHeight=0,atBottom=false;
  if (scrollTarget) {{
    scrollTop=scrollTarget.scrollTop;
    scrollHeight=scrollTarget.scrollHeight;
    clientHeight=scrollTarget.clientHeight;
    atBottom=(scrollHeight > clientHeight + 40) && (scrollTop + clientHeight >= scrollHeight - 12);
    if (atBottom) scanState.atBottomSeen = true;
  }}

  const next = unclickedCards[0] || null;
  if (PY_CLICK_CARDS && next && clickReady && (nowMs - Number(scanState.clickedKeys[next.key] || 0)) >= 1600) {{
    // Scroll the card cleanly into view synchronously and click it immediately
    // in the same evaluation (never return early without clicking!).
    const inViewport = next.rect.top >= 16 && next.rect.bottom <= (window.innerHeight - 10);
    if (!inViewport) {{
      try {{
        next.hit.scrollIntoView({{block: 'center', inline: 'nearest', behavior: 'instant'}});
      }} catch (_) {{}}
      if (scrollTarget && next.rect.bottom > (window.innerHeight - 10)) {{
        try {{
          scrollTarget.scrollBy({{
            top: Math.max(160, Math.round(next.rect.top - window.innerHeight * 0.28)),
            behavior: 'instant'
          }});
        }} catch (_) {{}}
      }}
    }}
    scanState.clickedKeys[next.key] = nowMs;
    scanState.lastCardClickAt = nowMs;
    try {{
      try {{ performance.clearResourceTimings(); }} catch (_) {{}}
      clickCardThumbnail(next.hit);
      return {{
        ok:true,
        mode:'card_clicked',
        stage:'card-clicked',
        clickedKey:next.key,
        clickedLabel:next.label,
        cards,
        title,url:href
      }};
    }} catch (e) {{
      return {{
        ok:false,
        mode:'provider_lobby',
        stage:'card-click-failed',
        clickedKey:next.key,
        clickedLabel:next.label,
        reason:String(e),
        cards,
        title,url:href
      }};
    }}
  }}

  if (cards.length > 0 && unclickedCards.length === 0 && clickReady) {{
    const nextWantedCanon = CANONICAL_TABLES.find(
      t => !t.blocked && !PY_CLICKED_KEYS.has(t.key) && !PY_CLICKED_KEYS.has(norm(t.name))
    ) || null;
    const visOrders = cardHits.map(c => c.order).filter(o => o < 999);
    const minVisOrder = visOrders.length ? Math.min(...visOrders) : 1;
    const scrollUp = !!(nextWantedCanon && visOrders.length && nextWantedCanon.order < minVisOrder);
    const step = (scrollUp ? -1 : 1) * Math.max(260, Math.floor((clientHeight || window.innerHeight || 600) * 0.55));
    if (scrollTarget) {{
      const prevTop = scrollTarget.scrollTop;
      try {{ scrollTarget.scrollBy({{top: step, behavior: 'instant'}}); }} catch (_) {{}}
      if (scrollTarget.scrollTop === prevTop && cardHits.length) {{
        const anchorCard = scrollUp ? cardHits[0].hit : cardHits[cardHits.length - 1].hit;
        try {{ anchorCard.scrollIntoView({{block: scrollUp ? 'end' : 'start', behavior: 'instant'}}); }} catch (_) {{}}
        try {{ anchorCard.dispatchEvent(new WheelEvent('wheel', {{deltaY: step, bubbles: true, cancelable: true}})); }} catch (_) {{}}
      }}
      scrollTop = scrollTarget.scrollTop;
      scrollHeight = scrollTarget.scrollHeight;
      clientHeight = scrollTarget.clientHeight;
      atBottom = (scrollHeight > clientHeight + 40) && (scrollTop + clientHeight >= scrollHeight - 12);
    }}
  }}

  return {{
    ok:true,
    mode:'provider_lobby',
    stage:category?(categoryState==='selected'?'roulette-selected':'roulette-unconfirmed'):'scanning',
    cards,
    scrollTop,scrollHeight,clientHeight,atBottom,
    atBottomSeen: !!scanState.atBottomSeen,
    bodyLength:bodyText.length,
    title,url:href
  }};
}})()
"""


def _dga_last20_numbers(last20):
    nums = []
    if not isinstance(last20, list):
        return nums
    for item in last20:
        val = None
        if isinstance(item, dict):
            for key in ("result", "number", "value", "winningNumber"):
                if key in item:
                    val = item.get(key)
                    break
        else:
            val = item
        try:
            n = int(val)
        except Exception:
            continue
        if 0 <= n <= 36:
            nums.append(n)
    return nums


def extract_dga_feed_tables(payload):
    """Return [{table_id, display_name, nums}] from Pragmatic DGA websocket JSON."""
    rows = []
    seen = set()

    def add(tid, name, nums):
        tid = str(tid or "").strip()
        if not tid or len(nums or []) < 1:
            return
        key = (tid, tuple(nums[:20]))
        if key in seen:
            return
        seen.add(key)
        rows.append({
            "table_id": tid,
            "display_name": str(name or tid).strip() or tid,
            "nums": list(nums),
        })

    def walk(obj, hinted_tid="", hinted_name=""):
        if isinstance(obj, dict):
            table_obj = obj.get("pragmaticTable")
            if isinstance(table_obj, dict):
                tid_hint = hinted_tid
                tcid = str(obj.get("tableAndCurrencyID") or "")
                if tcid and not tid_hint:
                    tid_hint = tcid.split(":", 1)[0]
                walk(table_obj, tid_hint, hinted_name)

            tid = str(
                obj.get("tableId")
                or obj.get("tableID")
                or obj.get("table_id")
                or hinted_tid
                or ""
            ).strip()
            name = str(
                obj.get("tableName")
                or obj.get("table_name")
                or obj.get("name")
                or obj.get("languageSpecificTableInfo")
                or hinted_name
                or tid
            ).strip()
            nums = _dga_last20_numbers(obj.get("last20Results"))
            if tid and nums:
                add(tid, name, nums)

            # Some delta frames nest the actual table state below generic keys.
            for key, val in obj.items():
                if key in (
                    "pragmaticTable",
                    "last20Results",
                    "tableLimits",
                    "dealer",
                ):
                    continue
                if isinstance(val, (dict, list)):
                    walk(val, tid or hinted_tid, name or hinted_name)
        elif isinstance(obj, list):
            for item in obj:
                walk(item, hinted_tid, hinted_name)

    walk(payload)
    return rows


class DgaLiveFeedCollector(threading.Thread):
    def __init__(self, state):
        super().__init__(daemon=True, name="PragmaticDgaLiveFeed")
        self.state = state
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.enabled = False
        self.ws_url = DGA_FEED_WS_URL
        self.casino_id = ""
        self.currency = ""
        self.reason = ""
        self.last_keys = {}
        self.updated_tables = set()
        self.received_frames = 0
        self.connected = False
        self.last_error = ""
        self.individual_mode = False
        self.currency_cycle = list(dict.fromkeys([
            DGA_DEFAULT_CURRENCY, "USD", "EUR", "BRL", "CAD"
        ]))
        self.currency_index = 0

    def configure(self, casino_id="", currency="", ws_url="", enable=True, reason=""):
        with self.lock:
            if casino_id:
                self.casino_id = str(casino_id).strip()
            if currency:
                self.currency = str(currency).strip().upper()
            if ws_url:
                self.ws_url = str(ws_url).strip()
            self.enabled = bool(enable)
            if reason:
                self.reason = str(reason)
        if not self.is_alive():
            try:
                self.start()
            except RuntimeError:
                pass
        self._set_status("DGA CANLI: başlatıldı • websocket bağlantısı hazırlanıyor")
        return True

    def stop_collection(self, reason="kullanıcı durdurdu"):
        with self.lock:
            self.enabled = False
            self.connected = False
        self._set_status(f"DGA CANLI: durdu • {reason}")

    def _config(self):
        with self.lock:
            explicit_currency = bool(str(self.currency or "").strip())
            cur = (
                self.currency
                if explicit_currency
                else self.currency_cycle[self.currency_index % len(self.currency_cycle)]
            )
            return {
                "enabled": bool(self.enabled),
                "ws_url": self.ws_url or DGA_FEED_WS_URL,
                "casino_id": self.casino_id or DGA_DEFAULT_CASINO_ID,
                "currency": cur or DGA_DEFAULT_CURRENCY,
                "explicit_currency": explicit_currency,
                "reason": self.reason,
            }

    def _table_rows(self):
        with self.state.lock:
            rows = dict(getattr(self.state, "table_registry", {}) or {})
        out = []
        seen = set()
        for tid, row in rows.items():
            tid = str(tid or "").strip()
            if not tid or tid in seen:
                continue
            seen.add(tid)
            out.append({
                "table_id": tid,
                "display_name": str((row or {}).get("display_name") or tid),
            })
        out.sort(key=lambda r: r["display_name"].lower())
        return out

    def _set_status(self, text):
        try:
            with self.state.lock:
                self.state.table_scan_status = str(text)[:220]
        except Exception:
            pass

    def _send_subscribe(self, ws, rows, casino_id, currency, individual=False):
        ids = [str(r.get("table_id") or "").strip() for r in rows]
        ids = [x for x in ids if x]
        if not ids:
            return 0
        sent = 0
        # Pragmatic examples differ: some use key:"tableId", some use
        # key:["tableId"]. Large multi-key batches caused ConnectionResetError
        # for the user's operator, so the fallback path now sends one table per
        # subscribe frame.
        for tid in ids:
            msg = {
                "type": "subscribe",
                "isDeltaEnabled": True,
                "casinoId": casino_id,
                "key": [tid] if individual else tid,
                "currency": currency,
            }
            ws.send_text(json.dumps(msg, separators=(",", ":")))
            sent += 1
        return sent

    def _handle_payload(self, payload, display_names=None):
        rows = extract_dga_feed_tables(payload)
        if not rows:
            return 0
        display_names = display_names or {}
        applied = 0
        now = time.time()
        for row in rows:
            tid = str(row.get("table_id") or "").strip()
            nums = [int(x) for x in (row.get("nums") or []) if isinstance(x, int)]
            if not tid or len(nums) < 3:
                continue
            key = tuple(nums[:20])
            if self.last_keys.get(tid) == key:
                continue
            self.last_keys[tid] = key
            name = str(row.get("display_name") or display_names.get(tid) or tid)
            if len(nums) >= 20:
                self.state.store_background_table_history(
                    nums,
                    table_id=tid,
                    display_name=name,
                    source_label="DGA WebSocket liveFeed",
                )
            else:
                self.state.mark_table_discovered(tid, name, source="DGA WebSocket")
            self.state.mark_table_attempt(tid, ok=True)
            self.updated_tables.add(tid)
            applied += 1
        if applied:
            sample = rows[0]
            self._set_status(
                f"DGA CANLI: {len(self.updated_tables)} masa güncellendi • "
                f"son {sample.get('display_name') or sample.get('table_id')} • "
                f"{time.strftime('%H:%M:%S')}"
            )
        return applied

    def run(self):
        while not self.stop_event.is_set():
            cfg = self._config()
            if not cfg["enabled"]:
                time.sleep(0.8)
                continue

            rows = self._table_rows()
            if not rows:
                self._set_status("DGA CANLI: kayıtlı masa bankası yok")
                time.sleep(2.0)
                continue

            casino_id = str(cfg["casino_id"] or DGA_DEFAULT_CASINO_ID)
            currency = str(cfg["currency"] or DGA_DEFAULT_CURRENCY).upper()
            ws_url = str(cfg["ws_url"] or DGA_FEED_WS_URL)
            display_names = {r["table_id"]: r["display_name"] for r in rows}
            using_default = not bool((self.casino_id or "").strip())

            ws = None
            try:
                self._set_status(
                    f"DGA CANLI: bağlanıyor • {len(rows)} masa • "
                    f"casino {casino_id}{' yedek' if using_default else ''} • {currency}"
                )
                ws = RawWebSocket(ws_url, connect_timeout=8)
                ws.settimeout(2.0)
                with self.lock:
                    self.connected = True
                    self.last_error = ""
                    self.individual_mode = False
                sent = self._send_subscribe(ws, rows, casino_id, currency, individual=False)
                self._set_status(
                    f"DGA CANLI: bağlı • {sent} masa abone • veri bekleniyor"
                )
                started = time.time()
                last_ping = 0.0
                last_any = time.time()
                individual_sent = False
                snapshot_ids = [r["table_id"] for r in rows]

                while not self.stop_event.is_set() and self._config()["enabled"]:
                    now = time.time()
                    if now - started >= TABLE_SCAN_AUTO_REFRESH_SECONDS:
                        break
                    current_ids = [r["table_id"] for r in self._table_rows()]
                    current_cfg = self._config()
                    if (
                        current_ids != snapshot_ids
                        or str(current_cfg.get("casino_id") or DGA_DEFAULT_CASINO_ID) != casino_id
                        or str(current_cfg.get("currency") or DGA_DEFAULT_CURRENCY).upper() != currency
                        or str(current_cfg.get("ws_url") or DGA_FEED_WS_URL) != ws_url
                    ):
                        break
                    if now - last_ping >= 15.0:
                        try:
                            ws.send_text(json.dumps({
                                "type": "ping",
                                "pingTime": int(now * 1000),
                            }, separators=(",", ":")))
                        except Exception:
                            raise
                        last_ping = now
                    try:
                        raw = ws.recv_text()
                    except socket.timeout:
                        if not individual_sent and now - last_any >= 20.0:
                            sent2 = self._send_subscribe(
                                ws,
                                rows,
                                casino_id,
                                currency,
                                individual=True,
                            )
                            individual_sent = True
                            with self.lock:
                                self.individual_mode = True
                            self._set_status(
                                f"DGA CANLI: toplu abonelik sessiz • "
                                f"{sent2} masa tek tek deneniyor"
                            )
                        elif individual_sent and now - last_any >= 45.0 and not cfg.get("explicit_currency"):
                            with self.lock:
                                self.currency_index += 1
                            self._set_status(
                                "DGA CANLI: veri gelmedi • başka para birimi deneniyor"
                            )
                            break
                        continue
                    if not raw:
                        continue
                    last_any = time.time()
                    with self.lock:
                        self.received_frames += 1
                    try:
                        payload = json.loads(raw)
                    except Exception:
                        continue
                    self._handle_payload(payload, display_names=display_names)
            except Exception as exc:
                with self.lock:
                    self.connected = False
                    self.last_error = f"{type(exc).__name__}: {exc}"
                self._set_status(
                    f"DGA CANLI: bağlantı hatası • {type(exc).__name__} • tekrar denenecek"
                )
                time.sleep(DGA_RECONNECT_SECONDS)
            finally:
                with self.lock:
                    self.connected = False
                if ws is not None:
                    try:
                        ws.close()
                    except Exception:
                        pass
                time.sleep(1.0)


def build_chrome_dga_start_script(rows, casino_id="", currency="", ws_url=""):
    rows_json = json.dumps(rows or [], ensure_ascii=False)
    casino_json = json.dumps(str(casino_id or ""), ensure_ascii=False)
    currency_json = json.dumps(str(currency or ""), ensure_ascii=False)
    ws_json = json.dumps(str(ws_url or DGA_FEED_WS_URL), ensure_ascii=False)
    return f"""
(() => {{
  const rows = {rows_json};
  const cfg = {{
    wsUrl: {ws_json} || 'wss://dga.pragmaticplaylive.net/ws',
    casinoId: {casino_json} || '',
    currency: ({currency_json} || '').toUpperCase()
  }};
  const norm = v => String(v == null ? '' : v).trim();
  function storageBlob() {{
    const out=[];
    for (const store of [window.localStorage, window.sessionStorage]) {{
      try {{
        for (let i=0;i<store.length;i++) {{
          const k=store.key(i);
          if (!k) continue;
          const v=store.getItem(k);
          if (/(casino|currency|table|dga|pragmatic)/i.test(k+' '+String(v).slice(0,500))) {{
            out.push(k+'='+String(v).slice(0,1000));
          }}
        }}
      }} catch (_) {{}}
    }}
    return out.join('\n');
  }}
  const resourceBlob = (() => {{
    try {{ return performance.getEntriesByType('resource').map(x => x.name || '').join('\n'); }}
    catch (_) {{ return ''; }}
  }})();
  const allText = [location.href, document.title || '', resourceBlob, storageBlob()].join('\n');
  function firstMatch(patterns) {{
    for (const re of patterns) {{
      const m = allText.match(re);
      if (m && m[1]) return decodeURIComponent(String(m[1])).trim();
    }}
    return '';
  }}
  if (!cfg.casinoId) {{
    cfg.casinoId = firstMatch([
      /[?&]casinoId=([^&#\s]+)/i,
      /[?&]casinoID=([^&#\s]+)/i,
      /["']casinoId["']\s*[:=]\s*["']([^"']+)/i,
      /["']casinoID["']\s*[:=]\s*["']([^"']+)/i,
      /casinoId\s*[:=]\s*([A-Za-z0-9_-]{{6,}})/i
    ]);
  }}
  if (!cfg.currency) {{
    cfg.currency = firstMatch([
      /[?&]currency=([^&#\s]+)/i,
      /[?&]currencyId=([^&#\s]+)/i,
      /["']currency["']\s*[:=]\s*["']([^"']+)/i,
      /["']currencyId["']\s*[:=]\s*["']([^"']+)/i,
      /currency\s*[:=]\s*([A-Z]{{3}})/i
    ]).toUpperCase();
  }}
  if (!cfg.casinoId) cfg.casinoId = 'ppcds00000003709';
  if (!cfg.currency) cfg.currency = 'TRY';

  const ids = Array.from(new Set(rows.map(r => norm(r.table_id)).filter(Boolean)));
  const old = window.__rouletteChromeDgaFeed;
  try {{ if (old && old.pingTimer) clearInterval(old.pingTimer); }} catch (_) {{}}
  try {{ if (old && old.ws) old.ws.close(); }} catch (_) {{}}

  const state = window.__rouletteChromeDgaFeed = {{
    ok: true,
    mode: 'chrome-runtime-dga',
    status: 'opening',
    wsUrl: cfg.wsUrl,
    casinoId: cfg.casinoId,
    currency: cfg.currency,
    ids,
    sent: 0,
    frames: 0,
    errors: 0,
    openedAt: 0,
    closedAt: 0,
    closeCode: 0,
    closeReason: '',
    lastError: '',
    lastMessageAt: 0,
    buffer: []
  }};

  function push(kind, data) {{
    try {{
      state.buffer.push(JSON.stringify({{__kind:kind, data, t:Date.now()}}));
      if (state.buffer.length > 1000) state.buffer.splice(0, state.buffer.length - 1000);
    }} catch (_) {{}}
  }}
  function sendSubscribe(ws, asArray) {{
    for (const tid of ids) {{
      const keyValue = asArray ? [tid] : tid;
      ws.send(JSON.stringify({{
        type: 'subscribe',
        isDeltaEnabled: true,
        casinoId: cfg.casinoId,
        key: keyValue,
        currency: cfg.currency
      }}));
      state.sent += 1;
    }}
  }}

  try {{
    const ws = new WebSocket(cfg.wsUrl);
    state.ws = ws;
    ws.onopen = () => {{
      state.status = 'open';
      state.openedAt = Date.now();
      try {{ sendSubscribe(ws, false); }} catch (e) {{ state.lastError=String(e && e.message || e); }}
      // Some Pragmatic builds/examples use key:[tableId]. Try that too after
      // the string form, but only once and without closing the feed.
      setTimeout(() => {{
        try {{ if (ws.readyState === 1) sendSubscribe(ws, true); }} catch (e) {{}}
      }}, 4500);
      push('opened', {{sent: state.sent, casinoId: cfg.casinoId, currency: cfg.currency}});
    }};
    ws.onmessage = ev => {{
      state.frames += 1;
      state.lastMessageAt = Date.now();
      if (typeof ev.data === 'string') {{
        state.buffer.push(ev.data);
        if (state.buffer.length > 1000) state.buffer.splice(0, state.buffer.length - 1000);
      }}
    }};
    ws.onerror = ev => {{
      state.errors += 1;
      state.status = 'error';
      state.lastError = String((ev && (ev.message || ev.type)) || 'websocket error');
      push('error', state.lastError);
    }};
    ws.onclose = ev => {{
      state.status = 'closed';
      state.closedAt = Date.now();
      state.closeCode = ev && ev.code || 0;
      state.closeReason = ev && ev.reason || '';
      push('closed', {{code:state.closeCode, reason:state.closeReason}});
    }};
    state.pingTimer = setInterval(() => {{
      try {{
        if (ws.readyState === 1) ws.send(JSON.stringify({{type:'ping', pingTime:Date.now()}}));
      }} catch (_) {{}}
    }}, 15000);
  }} catch (e) {{
    state.status = 'failed';
    state.lastError = String(e && e.message || e || 'WebSocket failed');
  }}

  return {{
    ok: true,
    mode: 'chrome-runtime-dga',
    status: state.status,
    sent: state.sent,
    tables: ids.length,
    casinoId: state.casinoId,
    currency: state.currency,
    title: document.title || '',
    url: location.href
  }};
}})()
"""


CHROME_DGA_POLL_SCRIPT = r"""
(() => {
  const st = window.__rouletteChromeDgaFeed;
  if (!st) return {ok:false, reason:'Chrome DGA state yok', title:document.title||'', url:location.href};
  const messages = [];
  try { messages.push(...st.buffer.splice(0, 120)); } catch (_) {}
  return {
    ok: true,
    mode: 'chrome-runtime-dga',
    status: st.status || '',
    readyState: st.ws ? st.ws.readyState : -1,
    sent: st.sent || 0,
    tables: (st.ids || []).length,
    frames: st.frames || 0,
    errors: st.errors || 0,
    casinoId: st.casinoId || '',
    currency: st.currency || '',
    closeCode: st.closeCode || 0,
    closeReason: st.closeReason || '',
    lastError: st.lastError || '',
    lastMessageAt: st.lastMessageAt || 0,
    messages,
    title: document.title || '',
    url: location.href
  };
})()
"""


CHROME_DGA_STOP_SCRIPT = r"""
(() => {
  const st = window.__rouletteChromeDgaFeed;
  if (!st) return {ok:true, stopped:false};
  try { if (st.pingTimer) clearInterval(st.pingTimer); } catch (_) {}
  try { if (st.ws) st.ws.close(); } catch (_) {}
  st.status = 'stopped';
  return {ok:true, stopped:true};
})()
"""


class ChromeBridge(threading.Thread):
    TARGET_TYPES = {"page","iframe","worker","shared_worker","service_worker","other","webview"}

    def __init__(self, state):
        super().__init__(daemon=True)
        self.state = state
        self.stop_event = threading.Event()
        self.ws = None
        self.next_id = 1
        self.send_lock = threading.Lock()
        self.pending = {}
        self.target_info = {}
        self.target_sessions = {}
        self.session_targets = {}
        self.target_parent = {}
        self.session_info = {}
        self.execution_contexts = {}
        self.direct_api_seen = {}
        self.direct_api_inflight = set()
        self.auth_templates = {}
        self.collector_seen = {}
        self.collector_inflight = set()
        self.collector_lock = threading.Lock()
        self.collector_last_start = 0.0
        self.api_refresh_mode = False
        self.api_refresh_remaining = []
        self.api_refresh_started = 0.0
        self.api_refresh_total = 0
        self.api_refresh_success = 0
        self.api_refresh_fail = 0
        self.dga_ws_url = DGA_FEED_WS_URL
        self.dga_casino_id = ""
        self.dga_currency = ""
        self.dga_frame_last_keys = {}
        self.dga_feed = DgaLiveFeedCollector(state)
        self.chrome_dga_enabled = False
        self.chrome_dga_session = ""
        self.chrome_dga_context_id = None
        self.chrome_dga_contexts = []
        self.chrome_dga_context_states = {}
        self.chrome_dga_last_start = 0.0
        self.chrome_dga_last_poll = 0.0
        self.chrome_dga_no_data_since = 0.0
        self.chrome_dga_last_rows_key = ()
        self.manual_api_teach = False
        self.manual_api_teach_started = 0.0
        self.live_result_probe = {}
        self.table_scan_enabled = False
        self.table_scan_visited = set()
        self.table_scan_found_ids = set()
        self.table_scan_no_progress = 0
        self.table_scan_last_scroll_height = 0
        self.table_scan_started = 0.0
        self.table_scan_last_view = 0.0
        self.table_scan_target_id = ""
        self.table_scan_entry_url = ""
        self.table_scan_auto_cycle = False
        self.table_scan_next_cycle = 0.0
        self.table_scan_tab_walk = False
        self.table_scan_cycle_seconds = TABLE_SCAN_AUTO_REFRESH_SECONDS
        self.table_scan_probe_done = set()
        self.table_scan_probe_success = set()
        self.table_scan_probe_fail = set()
        self.table_scan_probe_skip = set()
        self.table_scan_probe_queue = []
        self.table_scan_probe_targets = {}
        self.table_scan_probe_urls = set()
        self.table_scan_probed_keys = set()
        self.table_scan_clicked_keys = set()
        self.table_scan_click_deadlines = {}
        self.table_scan_click_started_at = {}
        self.table_scan_current_click_key = ""
        self.table_scan_current_click_label = ""
        self.table_scan_last_clicked_label = ""
        self.table_scan_returning_until = 0.0
        self.table_scan_lobby_seen_at = 0.0
        for _tid, _row in (getattr(state, "table_registry", {}) or {}).items():
            self.collector_seen[str(_tid)] = {
                "table_id": str(_tid),
                "display_name": str((_row or {}).get("display_name") or _tid),
                "last_discovered": 0.0,
                "last_requested": 0.0,
                "source": "KAYITLI BANKA",
            }

        self.recovery_hits = {}
        self.recovery_last_hit = {}
        self.recovery_last_scan = {}
        self.recovery_last_request = 0.0
        self.lobby_last_scan = {}
        self.lobby_last_action = {}

        # V2.9.5 user-taught navigation. No random scroll/search.
        self.lobby_teach_path = os.path.join(
            persistent_data_dir(), "lobby_teach_actions_v5.json"
        )
        self.lobby_teaching = False
        self.lobby_teach_index = 0
        self.lobby_teach_steps = []
        self.lobby_teach_last_ts = {}
        self.lobby_replay_index = 0
        self.lobby_route_started = False
        self.chrome_self_launch_last = 0.0
        self._load_lobby_teach()

        self.persistent_url_path = os.path.join(
            persistent_data_dir(), "last_roulette_url.txt"
        )
        self.recovery_guard_path = os.path.join(
            persistent_data_dir(), "autorecover_guard.json"
        )

        self.session_visibility = {}
        self.session_table_activity = {}
        self.session_theme = {}
        self.session_operator_game = {}
        self.active_game_sid = ""
        self.active_table_id = ""

        self.attaching = set()
        self.last_url_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "last_roulette_url.txt"
        )

    def _find_interactive_chrome(self):
        candidates = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for path in candidates:
            if path and os.path.exists(path):
                return path
        return ""

    def _saved_lobby_url(self):
        candidates = [
            self.persistent_url_path,
            self.last_url_path,
        ]
        for path in candidates:
            try:
                u = open(path, "r", encoding="utf-8", errors="ignore").read().strip()
                if u.startswith(("http://", "https://")):
                    low = u.lower()
                    blocked = (
                        "jsessionid", "sessionid=", "token=",
                        "pragmaticplaylive", "pragmaticplay.net", "/game.do", "/api/",
                    )
                    if not any(x in low for x in blocked):
                        cleaned = safe_last_page_url(u)
                        if cleaned:
                            return cleaned
            except Exception:
                pass
        return ""

    def _self_launch_debug_chrome(self):
        """
        Fallback only when port 9222 is not reachable.
        The BAT remains the normal launcher; this makes direct Python/restart
        starts self-healing instead of silently waiting forever.
        """
        now = time.time()
        if now - float(self.chrome_self_launch_last or 0.0) < 8.0:
            return False
        self.chrome_self_launch_last = now

        exe = self._find_interactive_chrome()
        if not exe:
            return False

        profile = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.dirname(os.path.abspath(__file__))),
            "PragmaticBlackjackChrome",
        )
        try:
            os.makedirs(profile, exist_ok=True)
        except Exception:
            pass

        url = self._saved_lobby_url()
        cmd = [
            exe,
            "--remote-debugging-address=127.0.0.1",
            f"--remote-debugging-port={DEBUG_PORT}",
            "--remote-allow-origins=*",
            f"--user-data-dir={profile}",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-features=CalculateNativeWinOcclusion,IntensiveWakeUpThrottling",
            "--start-maximized",
        ]
        if url:
            cmd.append(url)

        try:
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return True
        except Exception:
            return False

    def start_learned_route(self):
        if not self.lobby_teach_steps:
            with self.state.lock:
                self.state.autolobby_status = "ÖĞREN: kayıtlı yol yok"
            return False
        self.lobby_replay_index = 0
        self.lobby_route_started = True
        self.lobby_last_scan.clear()
        with self.state.lock:
            self.state.autolobby_status = (
                f"ÖĞREN: YOL BAŞLIYOR • 0/{len(self.lobby_teach_steps)}"
            )
        return True

    def _dga_table_rows(self):
        merged = {}
        with self.collector_lock:
            for tid, row in (self.collector_seen or {}).items():
                tid = str(tid or "").strip()
                if tid:
                    merged[tid] = dict(row or {})
        with self.state.lock:
            for tid, row in (self.state.table_registry or {}).items():
                tid = str(tid or "").strip()
                if not tid:
                    continue
                old = dict(merged.get(tid, {}) or {})
                old.update(dict(row or {}))
                old.setdefault("table_id", tid)
                merged[tid] = old
        rows = []
        for tid, row in merged.items():
            if str(tid).strip():
                rows.append({
                    "table_id": str(tid).strip(),
                    "display_name": str(row.get("display_name") or tid),
                })
        rows.sort(key=lambda row: row["display_name"].lower())
        return rows

    def start_dga_live_collection(self, reason="kayıtlı masa canlı feed"):
        rows = self._dga_table_rows()
        if not rows:
            with self.state.lock:
                self.state.table_scan_status = "CHROME DGA: kayıtlı masa bankası yok"
            return False
        self.table_scan_auto_cycle = False
        self.table_scan_next_cycle = 0.0
        self.chrome_dga_enabled = True
        self.chrome_dga_session = ""
        self.chrome_dga_context_id = None
        self.chrome_dga_last_start = 0.0
        self.chrome_dga_last_poll = 0.0
        self.chrome_dga_no_data_since = time.time()
        self.chrome_dga_last_rows_key = tuple(r["table_id"] for r in rows)
        # V2.9.25: direct Python DGA caused ConnectionResetError on the user's
        # operator. Stop that path and open the websocket inside Chrome instead.
        try:
            self.dga_feed.stop_collection("Chrome Runtime DGA devrede")
        except Exception:
            pass
        ok = self._start_chrome_dga_runtime(rows=rows, reason=reason)
        if not ok:
            # Fallback only when Chrome context is not available at all.
            self.dga_feed.configure(
                casino_id=self.dga_casino_id,
                currency=self.dga_currency,
                ws_url=self.dga_ws_url or DGA_FEED_WS_URL,
                enable=True,
                reason=reason,
            )
        return ok

    def _chrome_dga_runtime_contexts(self, limit=3):
        """Return several Chrome execution contexts to try for DGA WebSocket.

        V2.9.25 used one context; on the user's machine polling returned 0/0
        because that context did not keep the injected window state. V2.9.26
        starts/polls multiple Pragmatic/page contexts and uses whichever returns
        feed data first.
        """
        candidates = []
        sids = []
        if self.active_game_sid:
            sids.append(self.active_game_sid)
        for sid in self.session_info.keys():
            if sid not in sids:
                sids.append(sid)
        for sid in sids:
            if self._is_collector_session(sid):
                continue
            if not self.is_direct_probe_target(sid):
                continue
            info = self.session_info.get(sid, {}) or {}
            url = str(info.get("url", "") or "").lower()
            title = str(info.get("title", "") or "").lower()
            text = url + " " + title
            if any(x in text for x in (
                "livechat", "gamedata365", "youtube", "facebook", "google",
            )):
                continue
            base = 0
            if sid == self.active_game_sid:
                base += 1000
            if "games." in url or "pragmatic" in text:
                base += 400
            if "roulette" in text or "rulet" in text:
                base += 120
            if "live-casino" in url or "livecasino" in url:
                base += 60
            has_default_ctx = False
            for ctx in (self.execution_contexts.get(sid) or {}).values():
                cid = ctx.get("id")
                if cid is None:
                    continue
                aux = ctx.get("auxData") or {}
                origin = str(ctx.get("origin") or "").lower()
                name = str(ctx.get("name") or "").lower()
                score = base
                if bool(aux.get("isDefault", False)):
                    score += 60
                    has_default_ctx = True
                if "games." in origin or "pragmatic" in origin:
                    score += 500
                if origin.startswith(("http://", "https://")):
                    score += 20
                if "isolated" in name:
                    score -= 80
                candidates.append((score, sid, int(cid)))
            if not has_default_ctx:
                candidates.append((base + 10, sid, None))
        candidates.sort(key=lambda row: -row[0])
        out = []
        seen = set()
        for _score, sid, cid in candidates:
            key = (sid, cid)
            if key in seen:
                continue
            seen.add(key)
            out.append({"session": sid, "context_id": cid})
            if len(out) >= max(1, int(limit or 3)):
                break
        return out

    def _start_chrome_dga_runtime(self, rows=None, reason=""):
        if self.ws is None:
            with self.state.lock:
                self.state.table_scan_status = "CHROME DGA: Chrome bağlantısı bekleniyor"
            return False
        rows = rows or self._dga_table_rows()
        if not rows:
            with self.state.lock:
                self.state.table_scan_status = "CHROME DGA: kayıtlı masa bankası yok"
            return False
        contexts = self._chrome_dga_runtime_contexts(limit=3)
        if not contexts:
            with self.state.lock:
                self.state.table_scan_status = (
                    "CHROME DGA: uygun Pragmatic/Chrome context yok • "
                    "bir rulet masası veya lobi açık olsun"
                )
            return False
        now = time.time()
        self.chrome_dga_contexts = list(contexts)
        self.chrome_dga_context_states = {}
        self.chrome_dga_session = str(contexts[0].get("session") or "")
        self.chrome_dga_context_id = contexts[0].get("context_id")
        self.chrome_dga_last_start = now
        self.chrome_dga_no_data_since = now
        self.chrome_dga_last_rows_key = tuple(r["table_id"] for r in rows)
        expr = build_chrome_dga_start_script(
            rows,
            casino_id=self.dga_casino_id,
            currency=self.dga_currency,
            ws_url=self.dga_ws_url or DGA_FEED_WS_URL,
        )
        sent_contexts = 0
        for ctx in contexts:
            sid = str(ctx.get("session") or "")
            context_id = ctx.get("context_id")
            if not sid:
                continue
            params = {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True,
            }
            if context_id is not None:
                params["contextId"] = int(context_id)
            self.send(
                "Runtime.evaluate",
                params,
                session_id=sid,
                kind="chromedgastart",
                context={
                    "session": sid,
                    "context_id": context_id,
                    "rows": len(rows),
                    "reason": reason,
                },
            )
            sent_contexts += 1
        with self.state.lock:
            self.state.table_scan_status = (
                f"CHROME DGA: Chrome içinde websocket açılıyor • {len(rows)} masa • "
                f"{sent_contexts} context"
            )
        return sent_contexts > 0

    def _poll_chrome_dga_runtime(self):
        if not self.chrome_dga_enabled or self.ws is None:
            return False
        now = time.time()
        rows = self._dga_table_rows()
        rows_key = tuple(r["table_id"] for r in rows)
        should_restart = (
            not self.chrome_dga_contexts
            or rows_key != tuple(self.chrome_dga_last_rows_key or ())
            or now - float(self.chrome_dga_last_start or 0.0) >= TABLE_SCAN_AUTO_REFRESH_SECONDS
        )
        # If every polled context says 0 tables/no state for a while, the page
        # probably navigated or the previous injection ran in the wrong frame.
        if not should_restart and now - float(self.chrome_dga_last_start or 0.0) >= 10.0:
            states = [
                st for st in (self.chrome_dga_context_states or {}).values()
                if now - float(st.get("last", 0.0) or 0.0) <= 8.0
            ]
            if states and not any(int(st.get("tables", 0) or 0) > 0 for st in states):
                should_restart = True
            if (
                now - float(self.chrome_dga_no_data_since or now) >= 45.0
                and states
                and not any(int(st.get("frames", 0) or 0) > 0 for st in states)
            ):
                should_restart = True
        if should_restart:
            if now - float(self.chrome_dga_last_start or 0.0) >= 3.0:
                return self._start_chrome_dga_runtime(rows=rows, reason="context yenile")
            return False
        if now - float(self.chrome_dga_last_poll or 0.0) < 2.0:
            return False
        self.chrome_dga_last_poll = now
        sent = 0
        for ctx in list(self.chrome_dga_contexts or []):
            sid = str(ctx.get("session") or "")
            context_id = ctx.get("context_id")
            if not sid:
                continue
            params = {
                "expression": CHROME_DGA_POLL_SCRIPT,
                "returnByValue": True,
                "awaitPromise": True,
            }
            if context_id is not None:
                params["contextId"] = int(context_id)
            self.send(
                "Runtime.evaluate",
                params,
                session_id=sid,
                kind="chromedgapoll",
                context={"session": sid, "context_id": context_id},
            )
            sent += 1
        return sent > 0

    def _handle_chrome_dga_runtime(self, obj, context=None, started=False):
        try:
            value = obj.get("result", {}).get("result", {}).get("value")
            meta = context if isinstance(context, dict) else {}
            sid_key = str(meta.get("session") or "")
            ctx_id = meta.get("context_id")
            ctx_key = f"{sid_key}:{ctx_id if ctx_id is not None else 'default'}"
            if not isinstance(value, dict):
                self.chrome_dga_context_states[ctx_key] = {
                    "ok": False,
                    "tables": 0,
                    "sent": 0,
                    "frames": 0,
                    "status": "cevap yok",
                    "last": time.time(),
                }
                return
            now = time.time()
            casino_id = str(value.get("casinoId") or "").strip()
            currency = str(value.get("currency") or "").strip().upper()
            if casino_id or currency:
                self._record_dga_config(
                    casino_id=casino_id,
                    currency=currency,
                    ws_url=self.dga_ws_url,
                    source="Chrome Runtime DGA",
                )

            messages = value.get("messages") or []
            handled = 0
            for raw in messages if isinstance(messages, list) else []:
                if self._handle_dga_ws_payload(raw, source_label="Chrome Runtime DGA"):
                    handled += 1
            ok_value = bool(value.get("ok", True))
            status = str(value.get("status") or "")
            frames = int(value.get("frames", 0) or 0)
            sent = int(value.get("sent", 0) or 0)
            tables = int(value.get("tables", 0) or 0)
            err = str(value.get("lastError") or value.get("reason") or value.get("closeReason") or "")
            close_code = int(value.get("closeCode", 0) or 0)

            self.chrome_dga_context_states[ctx_key] = {
                "ok": ok_value,
                "tables": tables,
                "sent": sent,
                "frames": frames,
                "status": status,
                "error": err,
                "last": now,
            }

            if messages or frames > 0 or handled:
                self.chrome_dga_no_data_since = now
            elif frames <= 0 and not self.chrome_dga_no_data_since:
                self.chrome_dga_no_data_since = now

            if handled:
                # _handle_dga_ws_payload already wrote a data-specific status.
                return

            recent_states = [
                st for st in (self.chrome_dga_context_states or {}).values()
                if now - float(st.get("last", 0.0) or 0.0) <= 8.0
            ]
            valid = [st for st in recent_states if int(st.get("tables", 0) or 0) > 0]
            total_frames = sum(int(st.get("frames", 0) or 0) for st in valid)
            max_tables = max([int(st.get("tables", 0) or 0) for st in valid] or [0])
            max_sent = max([int(st.get("sent", 0) or 0) for st in valid] or [0])
            context_count = len(self.chrome_dga_contexts or [])

            # Do not leave the user stuck at 0/0. That means the injected state
            # was not found in the polled context; force a reinjection cycle.
            if (
                not valid
                and not started
                and now - float(self.chrome_dga_last_start or 0.0) >= 10.0
            ):
                self.chrome_dga_contexts = []
                self.chrome_dga_session = ""
                self.chrome_dga_last_start = 0.0
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"CHROME DGA: context state boş • {context_count} context • "
                        "yeniden başlatılıyor"
                    )
                return

            if (
                valid
                and total_frames <= 0
                and now - float(self.chrome_dga_no_data_since or now) >= 45.0
            ):
                self.chrome_dga_contexts = []
                self.chrome_dga_session = ""
                self.chrome_dga_last_start = 0.0
                with self.state.lock:
                    self.state.table_scan_status = (
                        "CHROME DGA: 45 sn frame yok • context yenileniyor"
                    )
                return

            if status in ("closed", "error", "failed") and now - float(self.chrome_dga_last_start or 0.0) >= 5.0:
                if not any(str(st.get("status") or "") == "open" for st in valid):
                    self.chrome_dga_contexts = []
                    self.chrome_dga_session = ""
                    self.chrome_dga_last_start = 0.0
                    with self.state.lock:
                        self.state.table_scan_status = (
                            f"CHROME DGA: {status}"
                            + (f" {close_code}" if close_code else "")
                            + (f" • {err[:60]}" if err else "")
                            + " • yeniden deneniyor"
                        )
                    return

            if started:
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"CHROME DGA: başlatıldı • {tables or meta.get('rows', 0)} masa • "
                        f"{context_count} context • casino {casino_id or self.dga_casino_id or '?'} • "
                        f"{currency or self.dga_currency or '?'}"
                    )
            else:
                wait_sec = int(now - float(self.chrome_dga_no_data_since or now))
                extra = ""
                if not ok_value:
                    extra = (f" • {err[:70]}" if err else " • state yok")
                elif total_frames > 0:
                    extra = " • frame var, tablo verisi bekleniyor"
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"CHROME DGA: {status or 'bekleniyor'} • "
                        f"{max_sent}/{max_tables} abonelik • {total_frames} frame • "
                        f"{context_count} context • {wait_sec}s veri bekliyor{extra}"
                    )
        except Exception:
            pass

    def _record_dga_config(self, casino_id="", currency="", ws_url="", source=""):
        changed = False
        casino_id = str(casino_id or "").strip()
        currency = str(currency or "").strip().upper()
        ws_url = str(ws_url or "").strip()
        if ws_url and "dga." in ws_url.lower() and ws_url != self.dga_ws_url:
            self.dga_ws_url = ws_url
            changed = True
        if casino_id and casino_id != self.dga_casino_id:
            self.dga_casino_id = casino_id
            changed = True
        if currency and currency != self.dga_currency:
            self.dga_currency = currency
            changed = True
        if changed:
            with self.state.lock:
                self.state.table_scan_status = (
                    "DGA CANLI: Chrome feed bilgisi yakalandı • "
                    f"casino {self.dga_casino_id or '?'} • {self.dga_currency or '?'}"
                )
            # If the user already started DGA collection with the fallback id,
            # update the running worker to the real operator parameters.
            if self.chrome_dga_enabled:
                self.chrome_dga_session = ""
                self.chrome_dga_contexts = []
                self.chrome_dga_context_states = {}
                self.chrome_dga_last_start = 0.0
            if getattr(self.dga_feed, "enabled", False):
                self.dga_feed.configure(
                    casino_id=self.dga_casino_id,
                    currency=self.dga_currency,
                    ws_url=self.dga_ws_url or DGA_FEED_WS_URL,
                    enable=True,
                    reason=source or "Chrome DGA config",
                )
        return changed

    def _handle_dga_ws_payload(self, payload_text, sid="", direction="", source_label="Chrome DGA WebSocket"):
        raw = str(payload_text or "")
        if not raw:
            return False
        if direction == "sent":
            if self.dga_casino_id and self.dga_currency:
                return False
            if "casinoid" not in raw.lower():
                return False
        else:
            seen_dga = getattr(self, "_recent_dga_payloads", None)
            if not isinstance(seen_dga, dict):
                seen_dga = {}
                self._recent_dga_payloads = seen_dga
            now_dga = time.time()
            raw_sig = (len(raw), hash(raw))
            if now_dga - float(seen_dga.get(raw_sig, 0.0) or 0.0) < 2.5:
                return False
            if len(seen_dga) > 600:
                seen_dga.clear()
            seen_dga[raw_sig] = now_dga
        try:
            payload = json.loads(raw)
        except Exception:
            return False
        handled = False
        if isinstance(payload, dict):
            typ = str(payload.get("type") or "").lower()
            casino_id = str(payload.get("casinoId") or payload.get("casinoID") or "").strip()
            currency = str(payload.get("currency") or payload.get("currencyId") or "").strip()
            if typ == "subscribe" or casino_id:
                self._record_dga_config(
                    casino_id=casino_id,
                    currency=currency,
                    ws_url=self.dga_ws_url,
                    source="Chrome websocket subscribe",
                )
                keys = payload.get("key") or payload.get("keys") or []
                if isinstance(keys, str):
                    keys = [keys]
                discovered = []
                for key in keys if isinstance(keys, list) else []:
                    tid = str(key or "").strip()
                    if tid and tid not in self.collector_seen:
                        discovered.append({"table_id": tid, "display_name": tid})
                if discovered and not self.manual_api_teach:
                    self._register_discovered_tables(discovered, source="DGA websocket subscribe")
                handled = True
        # CRITICAL: Do NOT save 20-spin Chrome DGA WebSocket lobby previews in
        # the background unless the user explicitly enabled DGA live collection
        # (and is NOT running TEK SEKME LOBİ TOPLA). Even then, only update
        # tables that already have a >= 40 spin SON 500 bank!
        dga_active = bool(
            (self.chrome_dga_enabled or getattr(self.dga_feed, "enabled", False))
            and not self.table_scan_tab_walk
        )
        if not dga_active:
            return handled

        rows = extract_dga_feed_tables(payload)
        if rows:
            handled = True
            for row in rows:
                tid = str(row.get("table_id") or "").strip()
                nums = [int(x) for x in (row.get("nums") or []) if isinstance(x, int)]
                name = str(row.get("display_name") or tid)
                if not tid:
                    continue
                if self._is_blocked_table_label(name):
                    continue
                with self.state.lock:
                    existing_row = self.state.table_registry.get(tid) or {}
                    existing_count = int(existing_row.get("long_count", 0) or 0)
                if len(nums) >= 20 and existing_count >= 40:
                    key = tuple(nums[:20])
                    if self.dga_frame_last_keys.get(tid) == key:
                        continue
                    self.dga_frame_last_keys[tid] = key
                    self.state.store_background_table_history(
                        nums,
                        table_id=tid,
                        display_name=name,
                        source_label=source_label,
                    )
                    with self.state.lock:
                        self.state.table_scan_status = (
                            f"DGA CANLI: Chrome feed veri aldı • {name[:48]}"
                        )
        return handled

    def _collector_launch_url(self):
        return PRAGMATIC_LOBBY_SCAN_URL

    def _target_id_for_session(self, sid):
        for tid, known_sid in self.target_sessions.items():
            if known_sid == sid:
                return tid
        return ""

    def _collector_root_session(self):
        root = str(self.table_scan_target_id or "")
        if not root:
            return ""
        return str(self.target_sessions.get(root, "") or "")

    def _is_collector_target_id(self, target_id):
        root = str(self.table_scan_target_id or "")
        tid = str(target_id or "")
        if not tid:
            return False

        def is_probe_target(tid_value):
            probe_targets = getattr(self, "table_scan_probe_targets", {}) or {}
            probe_urls = getattr(self, "table_scan_probe_urls", set()) or set()
            if tid_value in probe_targets:
                return True
            info = self.target_info.get(tid_value, {}) or {}
            url = str(info.get("url", "") or "")
            return bool(url and url in probe_urls)

        if is_probe_target(tid):
            return True

        known_tids = getattr(self, "collector_known_target_ids", None)
        if known_tids is None:
            known_tids = set()
            self.collector_known_target_ids = known_tids
        if tid in known_tids:
            return True

        seen = set()
        cur = tid
        for _ in range(8):
            if (root and cur == root) or cur in known_tids or is_probe_target(cur):
                known_tids.add(tid)
                return True
            if not cur or cur in seen:
                return False
            seen.add(cur)
            info = self.target_info.get(cur, {}) or {}
            cur = str(
                self.target_parent.get(cur)
                or info.get("openerId")
                or ""
            )
        return False

    def _is_collector_session(self, sid):
        s = str(sid or "")
        if not s:
            return False
        known_sids = getattr(self, "collector_known_session_ids", None)
        if known_sids is None:
            known_sids = set()
            self.collector_known_session_ids = known_sids
        if s in known_sids:
            return True
        if self._is_collector_target_id(self._target_id_for_session(s)):
            known_sids.add(s)
            return True
        return False

    def _is_korece_table(self, table_id="", label="", theme_code=""):
        tid_low = str(table_id or "").lower()
        thm_low = str(theme_code or "").lower()
        lbl_up = str(label or "").upper()
        if "korean" in tid_low or "381rwkr" in tid_low or "korean" in thm_low:
            return True
        return any(
            x in lbl_up
            for x in ("KORECE RULET", "KOREAN ROULETTE", "KORE RULET", "KORECE")
        )

    def _mark_current_scan_card_done(self, table_id="", label="", theme_code=""):
        key = str(getattr(self, "table_scan_current_click_key", "") or "").strip()
        if key:
            self.table_scan_clicked_keys.add(key)
        cur_label = str(
            label
            or getattr(self, "table_scan_current_click_label", "")
            or getattr(self, "table_scan_last_clicked_label", "")
            or ""
        )
        canon = canonical_pragmatic_table_info(cur_label) or canonical_pragmatic_table_info(key)
        if canon:
            self.table_scan_clicked_keys.add(str(canon["key"]))
            self.table_scan_clicked_keys.add(str(canon["name"]))
        if self._is_korece_table(table_id=table_id, label=cur_label, theme_code=theme_code):
            self.table_scan_stop_after_current = True

    def _close_table_scan_target(self):
        tids = []
        root = str(self.table_scan_target_id or "")
        if root:
            tids.append(root)
            getattr(self, "collector_known_target_ids", set()).add(root)
        tids.extend(list(self.table_scan_probe_targets.keys()))
        for scan_sid in list(self.session_table_activity.keys()):
            if self._is_collector_session(scan_sid):
                self.session_table_activity.pop(scan_sid, None)
        self.table_scan_target_id = ""
        self.table_scan_probe_targets = {}
        self.table_scan_probe_urls = set()
        self.table_scan_probe_queue = []
        self.table_scan_probe_done = set()
        self.table_scan_probe_success = set()
        self.table_scan_probe_fail = set()
        self.table_scan_probe_skip = set()
        self.table_scan_click_deadlines = {}
        self.table_scan_click_started_at = {}
        self.table_scan_returning_until = 0.0
        self.table_scan_lobby_seen_at = 0.0
        self.table_scan_lobby_settle_until = 0.0
        self.table_scan_last_card_click_ts = 0.0
        self.table_scan_stop_after_current = False
        if self.ws is not None:
            for tid in tids:
                try:
                    self.send("Target.closeTarget", {"targetId": tid})
                except Exception:
                    pass

    def _start_lobby_collector_target(self, status_text):
        self.table_scan_visited = set()
        self.table_scan_found_ids = set()
        self.table_scan_no_progress = 0
        self.table_scan_last_scroll_height = 0
        self.table_scan_started = time.time()
        self.table_scan_last_view = 0.0
        self.table_scan_entry_url = self._collector_launch_url()
        self.table_scan_probe_queue = []
        self.table_scan_probe_targets = {}
        self.table_scan_probe_urls = set()
        self.table_scan_probed_keys = set()
        self.table_scan_clicked_keys = set()
        self.table_scan_click_attempts = {}
        self.table_scan_click_deadlines = {}
        self.table_scan_click_started_at = {}
        self.table_scan_probe_done = set()
        self.table_scan_probe_success = set()
        self.table_scan_probe_fail = set()
        self.table_scan_probe_skip = set()
        self.table_scan_current_click_key = ""
        self.table_scan_current_click_label = ""
        self.table_scan_last_clicked_label = ""
        self.table_scan_returning_until = 0.0
        self.table_scan_lobby_seen_at = 0.0
        self.table_scan_lobby_settle_until = 0.0
        self.table_scan_last_card_click_ts = 0.0
        self.table_scan_stop_after_current = False
        self.send(
            "Target.createTarget",
            {
                "url": self.table_scan_entry_url,
                "background": not bool(self.table_scan_tab_walk),
            },
            kind="collectorcreate",
            context={"url": self.table_scan_entry_url},
        )
        with self.state.lock:
            self.state.table_scan_status = status_text
        return True

    def start_table_scan(self, auto_cycle=True):
        self.table_scan_tab_walk = False
        self.table_scan_cycle_seconds = TABLE_SCAN_AUTO_REFRESH_SECONDS
        with self.state.lock:
            bank_count = len(getattr(self.state, "table_registry", {}) or {})
        if bank_count:
            # DGA remains available for already-learned banks, but the separate
            # V2.9.27 tab-walk button below forces visible table-by-table visits.
            return self.start_dga_live_collection("PRAGMATIC MASALARI TARA")

        self._close_table_scan_target()
        self.table_scan_tab_walk = False
        self.table_scan_cycle_seconds = TABLE_SCAN_AUTO_REFRESH_SECONDS
        self.table_scan_auto_cycle = bool(auto_cycle)
        self.table_scan_next_cycle = 0.0
        self.table_scan_enabled = True
        return self._start_lobby_collector_target(
            "MASA TARAMA: Pragmatic Play lobisi arka planda açılıyor"
        )

    def start_tab_walk_scan(self, auto_cycle=True):
        """Open roulette lobby and collect tables in one side tab.

        The user keeps playing in their own tab. This collector tab enters the
        Pragmatic lobby, clicks one real table card, waits on the lower-right
        SON 500 panel above Automatic Play, saves it, returns to lobby, then
        clicks the next table. A completed pass repeats every 5 minutes.
        """
        self._close_table_scan_target()
        self.chrome_dga_enabled = False
        try:
            self.dga_feed.stop_collection("sekmeli lobi toplayıcı")
        except Exception:
            pass
        self.manual_api_teach = False
        self.table_scan_tab_walk = True
        self.table_scan_cycle_seconds = TAB_WALK_REFRESH_SECONDS
        self.table_scan_auto_cycle = bool(auto_cycle)
        self.table_scan_next_cycle = 0.0
        self.table_scan_enabled = True
        return self._start_lobby_collector_target(
            "TEK SEKME TOPLA: Pragmatic Play lobisi açılıyor • aynı yan sekmede masalar tek tek gezilecek"
        )

    def stop_table_scan(self, reason="kullanıcı durdurdu"):
        manual_stop = "kullanıcı" in str(reason).lower()
        self.table_scan_enabled = False
        self.manual_api_teach = False
        self._close_table_scan_target()
        if manual_stop:
            self.table_scan_auto_cycle = False
            self.table_scan_next_cycle = 0.0
            self.chrome_dga_enabled = False
            if self.ws is not None and self.chrome_dga_session:
                try:
                    self.send(
                        "Runtime.evaluate",
                        {"expression": CHROME_DGA_STOP_SCRIPT, "returnByValue": True},
                        session_id=self.chrome_dga_session,
                        kind="chromedgastop",
                        context={},
                    )
                except Exception:
                    pass
            try:
                self.dga_feed.stop_collection("kullanıcı durdurdu")
            except Exception:
                pass
        elif self.table_scan_auto_cycle:
            delay = float(
                self.table_scan_cycle_seconds
                if self.table_scan_tab_walk
                else TABLE_SCAN_AUTO_REFRESH_SECONDS
            )
            self.table_scan_next_cycle = time.time() + delay
        with self.state.lock:
            if self.table_scan_auto_cycle and not manual_stop:
                mins = int(round(float(
                    self.table_scan_cycle_seconds
                    if self.table_scan_tab_walk
                    else TABLE_SCAN_AUTO_REFRESH_SECONDS
                ) / 60.0))
                prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
                self.state.table_scan_status = (
                    f"{prefix}: {reason} • {mins} dk sonra otomatik tekrar"
                )
            else:
                self.state.table_scan_status = f"MASA TARAMA/API ÖĞREN: durdu • {reason}"
        return True

    def _is_blocked_table_label(self, text):
        up = str(text or "").upper()
        if not up:
            return False
        return any(str(x or "").upper() in up for x in TAB_WALK_BLOCKED_TABLE_LABELS)

    def _clean_collector_label(self, text, fallback="Roulette"):
        label = re.sub(r"\s+", " ", str(text or "")).strip()
        if not label:
            return fallback
        low = label.lower()
        if (
            low in ("roulette", "rulet", "pragmatic play", "pragmatic play lobby", "lobby", "lobi")
            or low.startswith(("http://", "https://", "client.", "games."))
            or "client." in low
            or "/client" in low
            or "/desktop/" in low
        ):
            return fallback
        canon_name = canonical_pragmatic_table_name(label, fallback="")
        if canon_name:
            return canon_name
        nums = re.findall(r"\b(?:[0-9]|[12][0-9]|3[0-6])\b", label)
        upper = label.upper()
        if len(nums) >= 8:
            m = re.search(
                r"([A-ZÇĞİÖŞÜ0-9 ._-]{0,28}(?:ROULETTE|RULET)[A-ZÇĞİÖŞÜ0-9 ._-]{0,28})",
                upper,
                flags=re.I,
            )
            if m:
                label = m.group(1).strip(" -_•|")
            else:
                label = fallback
        return label[:80] or fallback

    def _collector_table_identity(self, sid="", real_table_id="", title=""):
        real = str(real_table_id or "").strip()
        if not real:
            best_ts = 0.0
            for s_id, act in list(self.session_table_activity.items()):
                if not self._is_collector_session(s_id):
                    continue
                cand_tid = str((act or {}).get("table_id") or "").strip()
                cand_ts = float((act or {}).get("last", 0.0) or 0.0)
                if cand_tid and cand_ts >= best_ts:
                    real = cand_tid
                    best_ts = cand_ts
        click_label = self._clean_collector_label(
            self.table_scan_current_click_label or self.table_scan_last_clicked_label,
            fallback="",
        )
        title_label = self._clean_collector_label(title, fallback="")
        label = click_label or title_label or real or "Roulette"
        if real:
            return real, (label or real)
        raw = str(self.table_scan_current_click_key or label or sid or "collector")
        digest = hashlib.sha1(raw.encode("utf-8", "ignore")).hexdigest()[:12]
        return f"collector_{digest}", (label or f"Roulette {digest}")

    def _schedule_collector_return(self, sid, delay=0.25):
        now = time.time()
        delay = float(delay or 0.25)
        sid = str(sid or "")
        if self.table_scan_tab_walk:
            started = 0.0
            if sid:
                started = float(self.table_scan_click_started_at.get(sid, 0.0) or 0.0)
            if not started:
                for v in self.table_scan_click_started_at.values():
                    try:
                        started = max(started, float(v or 0.0))
                    except Exception:
                        pass
            if started:
                delay = max(
                    delay,
                    max(0.22, TAB_WALK_TABLE_MIN_DWELL_SECONDS - (now - started)),
                )
        due = now + delay
        if sid:
            self.table_scan_click_deadlines[sid] = due
        if self.table_scan_tab_walk:
            root_sid = self._collector_root_session()
            for scan_sid in list(self.session_info.keys()):
                if not self._is_collector_session(scan_sid):
                    continue
                if scan_sid == sid or scan_sid == root_sid or scan_sid in self.table_scan_click_deadlines:
                    old = float(self.table_scan_click_deadlines.get(scan_sid, 0.0) or 0.0)
                    self.table_scan_click_deadlines[scan_sid] = min(old, due) if old else due
                    self.table_scan_click_started_at.setdefault(scan_sid, (started or now) if self.table_scan_tab_walk else now)
        return due

    def _return_collector_to_lobby(self, sid, reason="sıradaki masa"):
        if not sid or self.ws is None:
            return False
        url = str(self.table_scan_entry_url or self._collector_launch_url() or "")
        now = time.time()
        if self.table_scan_tab_walk:
            # V2.9.42: once we have intentionally pressed in-game Lobi, the old
            # game iframe can keep reporting SON500/Lobi controls for a few
            # seconds even though the visible root page is already the lobby.
            # During this grace window the lobby scanner is allowed to win and
            # stale game detections must not recreate a table wait.
            self.table_scan_returning_until = max(
                float(getattr(self, "table_scan_returning_until", 0.0) or 0.0),
                now + TAB_WALK_RETURN_GRACE_SECONDS,
            )
        self.table_scan_click_deadlines.pop(sid, None)
        self.table_scan_click_started_at.pop(sid, None)
        tid = self._target_id_for_session(sid)
        root = str(self.table_scan_target_id or "")
        try:
            if self.table_scan_tab_walk:
                # V2.9.34: after reading the game's lower-right SON500 panel,
                # return by clicking the in-game top-right Lobi/Lobby button.
                # Do not history.back() to the operator search page; that caused
                # the collector to get stuck typing "pragmatic play lobby" again.
                for scan_sid in list(self.table_scan_click_deadlines.keys()):
                    if self._is_collector_session(scan_sid):
                        self.table_scan_click_deadlines.pop(scan_sid, None)
                        self.table_scan_click_started_at.pop(scan_sid, None)
                        self.session_table_activity.pop(scan_sid, None)
                for scan_sid in list(self.session_info.keys()):
                    if self._is_collector_session(scan_sid):
                        self.session_table_activity.pop(scan_sid, None)
                self.table_scan_current_click_key = ""
                self.table_scan_current_click_label = ""
                root_sid = self._collector_root_session() or sid
                return_sids = []
                for candidate in (sid, root_sid):
                    if candidate and candidate not in return_sids:
                        return_sids.append(candidate)
                # The button may live in the root page or a Pragmatic OOPIF.
                # Send the same safe click probe to every collector session.
                for scan_sid in list(self.session_info.keys()):
                    if scan_sid not in return_sids and self._is_collector_session(scan_sid):
                        return_sids.append(scan_sid)
                for return_sid in return_sids[:10]:
                    ctx_ids = [None]
                    for ctx in (self.execution_contexts.get(return_sid) or {}).values():
                        cid = ctx.get("id")
                        aux = ctx.get("auxData") or {}
                        origin = str(ctx.get("origin") or "").lower()
                        if cid is not None and bool(aux.get("isDefault", False)) and origin.startswith(("http://", "https://")):
                            ctx_ids.append(int(cid))
                    for cid in list(dict.fromkeys(ctx_ids))[:4]:
                        params = {
                            "expression": COLLECTOR_LOBBY_CLICK_SCRIPT,
                            "returnByValue": True,
                            "awaitPromise": True,
                        }
                        if cid is not None:
                            params["contextId"] = int(cid)
                        self.send(
                            "Runtime.evaluate",
                            params,
                            session_id=return_sid,
                            kind="collectorback",
                            context={"session": return_sid, "from": sid, "reason": reason, "context_id": cid},
                        )
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"SEKMELİ TOPLA: {reason} • oyun içi Lobi düğmesine basılıyor"
                    )
                if getattr(self, "table_scan_stop_after_current", False):
                    self.table_scan_stop_after_current = False
                    with self.state.lock:
                        bank_count = len(self.state.table_registry)
                    self.stop_table_scan(
                        f"Korece Rulet masası tamamlandı • tarama durduruldu • kayıtlı banka {bank_count}"
                    )
            elif tid and root and tid != root:
                self.send("Target.closeTarget", {"targetId": tid})
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"MASA TARAMA: {reason} • sekme kapatılıyor"
                    )
            else:
                if not url:
                    return False
                self.send("Page.navigate", {"url": url}, session_id=sid)
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"MASA TARAMA: {reason} • lobiye dönülüyor"
                    )
            return True
        except Exception:
            return False

    def _cleanup_table_scan_probes(self):
        if not self.table_scan_probe_targets:
            return
        now = time.time()
        close_ids = []
        for tid, row in list(self.table_scan_probe_targets.items()):
            opened = float(row.get("opened", 0.0) or 0.0)
            seen_at = float(row.get("table_seen_at", 0.0) or 0.0)
            done_at = float(row.get("done_at", 0.0) or 0.0)
            if done_at and now - done_at >= 0.8:
                close_ids.append(tid)
            elif self.table_scan_tab_walk and opened and now - opened >= TAB_WALK_TABLE_TIMEOUT_SECONDS:
                self.table_scan_probe_done.add(str(row.get("key") or tid))
                self.table_scan_probe_fail.add(str(row.get("key") or tid))
                row["done_at"] = now
                close_ids.append(tid)
                with self.state.lock:
                    self.state.table_scan_status = (
                        "SEKMELİ TOPLA: masa veri zaman aşımı • "
                        f"{str(row.get('label') or row.get('table_id') or tid)[:48]} • sıradaki masaya geçiliyor"
                    )
            elif (not self.table_scan_tab_walk) and seen_at and now - seen_at >= 3.0:
                close_ids.append(tid)
            elif (not self.table_scan_tab_walk) and opened and now - opened >= COLLECTOR_PROBE_SECONDS:
                close_ids.append(tid)
        for tid in close_ids:
            row = self.table_scan_probe_targets.pop(tid, None) or {}
            url = str(row.get("url") or "")
            if url:
                self.table_scan_probe_urls.discard(url)
            if self.ws is not None:
                try:
                    self.send("Target.closeTarget", {"targetId": tid})
                except Exception:
                    pass

    def _operator_table_probe_url(self, game_id, label=""):
        gid = str(game_id or "").strip()
        if not gid:
            return ""
        base = str(self.table_scan_entry_url or PRAGMATIC_LOBBY_SCAN_URL)
        try:
            u = urllib.parse.urlsplit(base)
            qs = urllib.parse.parse_qsl(u.query, keep_blank_values=False)
            drop = {"opengames", "gamenames", "gameid", "tableid", "table_id"}
            cleaned = [(k, v) for k, v in qs if str(k).lower() not in drop]
            cleaned.append(("openGames", gid))
            cleaned.append(("gameNames", str(label or "Roulette")[:120]))
            return urllib.parse.urlunsplit((
                u.scheme,
                u.netloc,
                u.path or "/",
                urllib.parse.urlencode(cleaned, doseq=True),
                "",
            ))
        except Exception:
            return ""

    def _queue_table_probe(self, row):
        if not isinstance(row, dict):
            return False
        if COLLECTOR_PROBE_INITIAL_CONCURRENT <= 0 and not self.table_scan_tab_walk:
            return False
        href = str(row.get("href") or "").strip()
        label = str(row.get("label") or "").strip()
        game_id = str(row.get("game_id") or "").strip()
        table_id = str(row.get("table_id") or "").strip()
        key = str(row.get("key") or table_id or game_id or href or label).strip()

        url = href if href.startswith(("http://", "https://")) else ""
        # Direct games.* / provider-lobby URLs can stay on a black splash
        # screen. Prefer the operator wrapper URL when game_id is available.
        try:
            host = urllib.parse.urlsplit(url).hostname or ""
            if game_id and host.lower().startswith("games."):
                url = ""
        except Exception:
            pass
        if not url and game_id:
            url = self._operator_table_probe_url(game_id, label)

        if not url or not url.startswith(("http://", "https://")):
            return False
        if not key:
            return False
        if key in self.table_scan_probed_keys:
            return False
        if url in self.table_scan_probe_urls:
            return False
        if any(str(q.get("key") or "") == key for q in self.table_scan_probe_queue):
            return False
        self.table_scan_probe_queue.append({
            "key": key,
            "url": url,
            "label": label[:160],
            "table_id": table_id,
            "game_id": game_id,
            "queued": time.time(),
        })
        return True

    def _pump_table_scan_probes(self):
        if not self.table_scan_enabled or self.ws is None:
            return
        self._cleanup_table_scan_probes()
        active = len(self.table_scan_probe_targets)
        if self.table_scan_tab_walk:
            limit = 1
        else:
            limit = (
                COLLECTOR_PROBE_STEADY_CONCURRENT
                if self.table_scan_found_ids
                else COLLECTOR_PROBE_INITIAL_CONCURRENT
            )
        limit = max(0, int(limit or 0))
        if limit <= 0:
            self.table_scan_probe_queue = []
            return
        while active < limit and self.table_scan_probe_queue:
            row = self.table_scan_probe_queue.pop(0)
            key = str(row.get("key") or "")
            url = str(row.get("url") or "")
            if not url or not key or key in self.table_scan_probed_keys:
                continue
            self.table_scan_probed_keys.add(key)
            self.table_scan_probe_urls.add(url)
            self.send(
                "Target.createTarget",
                {"url": url, "background": not bool(self.table_scan_tab_walk)},
                kind="collectorprobecreate",
                context=row,
            )
            active += 1

    def browser_ws_url(self):
        with urllib.request.urlopen(
            f"http://{DEBUG_HOST}:{DEBUG_PORT}/json/version",
            timeout=2
        ) as r:
            return json.loads(r.read().decode("utf-8"))["webSocketDebuggerUrl"]

    def send(self, method, params=None, session_id=None, kind=None, context=None):
        with self.send_lock:
            i = self.next_id
            self.next_id += 1
            msg = {"id":i, "method":method, "params":params or {}}
            if session_id:
                msg["sessionId"] = session_id
            self.pending[i] = (kind, context)
            self.ws.send_text(json.dumps(msg, separators=(",",":")))
            return i

    def _safe_return_url(self, ti):
        """Persist the exact user-visited casino/lobby/game-wrapper page URL, never ephemeral Pragmatic iframe tokens."""
        try:
            url = str((ti or {}).get("url", "") or "").strip()
            title = str((ti or {}).get("title", "") or "").lower()
            typ = str((ti or {}).get("type", "") or "").lower()
            tid = str((ti or {}).get("targetId", "") or "").strip()
            low = url.lower()
            if typ and typ != "page":
                return ""
            if tid and (
                tid == str(getattr(self, "table_scan_target_id", "") or "")
                or tid in getattr(self, "table_scan_probe_targets", {})
            ):
                return ""
            if url and url in getattr(self, "table_scan_probe_urls", set()):
                return ""
            if not url.startswith(("http://", "https://")):
                return ""
            # Avoid persisting direct iframe game/session URLs, credentials/tokens, or third-party widgets.
            blocked = (
                "jsessionid", "pragmaticplaylive", "pragmaticplay.net",
                "/game.do", "/api/", "sessionid=", "token=",
                "livechat", "google.", "facebook.", "youtube.", "cloudflare"
            )
            if any(x in low for x in blocked):
                return ""
            wanted = (
                "roulette" in low or "roulette" in title
                or "rulet" in low or "rulet" in title
                or "pragmatic" in low or "pragmatic" in title
                or "opengames=" in low or "searchterm=" in low
                or "live-casino" in low or "livecasino" in low
                or "casino" in low or "casino" in title
                or "meritbet" in low
            )
            if not wanted:
                return ""
            return safe_last_page_url(url)
        except Exception:
            return ""

    def save_roulette_url(self, ti):
        try:
            url = self._safe_return_url(ti)
            if not url or url == getattr(self, "_last_saved_roulette_url", ""):
                return
            self._last_saved_roulette_url = url
            for path in (self.last_url_path, self.persistent_url_path):
                try:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(url)
                except Exception:
                    pass
        except Exception:
            pass

    def _load_lobby_teach(self):
        try:
            with open(self.lobby_teach_path, 'r', encoding='utf-8') as f:
                raw=json.load(f)
            steps=raw.get('steps') or []
            if isinstance(steps,list) and len(steps)>=1:
                self.lobby_teach_steps=[dict(x) for x in steps[:40] if isinstance(x,dict)]
                self.lobby_replay_index=0
                self.lobby_route_started=False
                with self.state.lock:
                    self.state.autolobby_status=(
                        f'ÖĞREN: HAZIR ✓ • {len(self.lobby_teach_steps)} kayıtlı işlem'
                    )
                return True
        except Exception:
            pass
        self.lobby_teach_steps=[]
        self.lobby_replay_index=0
        return False

    def _save_lobby_teach(self):
        try:
            os.makedirs(os.path.dirname(self.lobby_teach_path),exist_ok=True)
            with open(self.lobby_teach_path,'w',encoding='utf-8') as f:
                json.dump({
                    'version':2,
                    'saved_at':time.strftime('%Y-%m-%d %H:%M:%S'),
                    'steps':self.lobby_teach_steps[:40],
                },f,ensure_ascii=False,indent=2)
            return True
        except Exception:
            return False

    def lobby_teach_ready(self):
        return bool(self.lobby_teach_steps) and not self.lobby_teaching

    def start_lobby_teaching(self):
        # Do not overwrite the last good route until user presses ÖĞREN BİTİR.
        self.lobby_teaching=True
        self.lobby_teach_index=0
        self.lobby_teach_last_ts.clear()
        self._teach_working_steps=[]
        self.lobby_replay_index=0
        self.lobby_route_started=False
        with self.state.lock:
            self.state.autolobby_status=(
                'ÖĞREN AÇIK • site üzerinde yolu elle göster • bitince ÖĞREN BİTİR'
            )
        return True

    def finish_lobby_teaching(self):
        if not self.lobby_teaching:
            with self.state.lock:
                self.state.autolobby_status='ÖĞREN: kayıt modu açık değil'
            return False,0
        working=list(getattr(self,'_teach_working_steps',[]) or [])
        self.lobby_teaching=False
        self.lobby_teach_last_ts.clear()
        if not working:
            with self.state.lock:
                self.state.autolobby_status=(
                    'ÖĞREN: işlem kaydedilmedi • eski eğitim korunuyor'
                )
            return False,0
        self.lobby_teach_steps=working[:40]
        self.lobby_teach_index=len(self.lobby_teach_steps)
        self.lobby_replay_index=0
        self.lobby_route_started=False
        ok=self._save_lobby_teach()
        with self.state.lock:
            self.state.autolobby_status=(
                f'ÖĞREN TAMAM ✓ • {len(self.lobby_teach_steps)} işlem kaydedildi'
                if ok else 'ÖĞREN: kayıt dosyası yazılamadı'
            )
        return ok,len(self.lobby_teach_steps)

    def reset_lobby_teaching(self):
        self.lobby_teaching=False
        self.lobby_teach_index=0
        self.lobby_teach_steps=[]
        self.lobby_teach_last_ts.clear()
        self.lobby_replay_index=0
        self.lobby_route_started=False
        self._teach_working_steps=[]
        try:
            os.remove(self.lobby_teach_path)
        except Exception:
            pass
        with self.state.lock:
            self.state.autolobby_status='ÖĞREN: kayıt silindi • yeniden BAŞLAT'

    def _handle_lobby_teach(self,sid,value):
        if not self.lobby_teaching or not isinstance(value,dict):
            return
        clicks=value.get('actions') or value.get('clicks') or []
        if not isinstance(clicks,list):
            return
        working=getattr(self,'_teach_working_steps',None)
        if not isinstance(working,list):
            working=[]
            self._teach_working_steps=working

        blocked=('BAHİS',' BET ','SPIN','JETON','CHIP','OTOMATİK OYUN','AUTOMATIC PLAY')
        added=0
        for item in clicks:
            if not isinstance(item,dict):
                continue
            try:
                ts=int(item.get('ts',0) or 0)
            except Exception:
                ts=0
            if ts<=0:
                continue
            last=int(self.lobby_teach_last_ts.get(sid,0) or 0)
            if ts<=last:
                continue
            self.lobby_teach_last_ts[sid]=ts

            txt=' '+str(item.get('text') or '').upper()+' '
            if any(x in txt for x in blocked):
                continue
            action=str(item.get('action') or 'click').lower()
            if action not in ('click','type','scroll'):
                continue
            value=str(item.get('value') or '')[:180] if action == 'type' else ''
            if action == 'type' and not value:
                continue

            try:
                dx=float(item.get('dx',0) or 0)
                dy=float(item.get('dy',0) or 0)
                toX=float(item.get('toX',0) or 0)
                toY=float(item.get('toY',0) or 0)
            except Exception:
                dx=0.0; dy=0.0; toX=0.0; toY=0.0
            if action == 'scroll' and abs(dx) < 4 and abs(dy) < 4:
                continue

            clean={
                'action':action,
                'tag':str(item.get('tag') or '')[:40],
                'text':str(item.get('text') or '')[:220],
                'id':str(item.get('id') or '')[:140],
                'href':str(item.get('href') or '')[:700],
                'testid':str(item.get('testid') or '')[:180],
                'aria':str(item.get('aria') or '')[:180],
                'placeholder':str(item.get('placeholder') or '')[:180],
                'name':str(item.get('name') or '')[:120],
                'inputType':str(item.get('inputType') or '')[:40],
                'role':str(item.get('role') or '')[:80],
                'classes':[str(x)[:80] for x in (item.get('classes') or [])[:10] if str(x).strip()],
                'page':str(item.get('page') or '')[:900],
                'value':value,
                'scope':str(item.get('scope') or '')[:20] if action == 'scroll' else '',
                'dx':dx if action == 'scroll' else 0.0,
                'dy':dy if action == 'scroll' else 0.0,
                'toX':toX if action == 'scroll' else 0.0,
                'toY':toY if action == 'scroll' else 0.0,
            }
            # Ignore exact duplicate consecutive click descriptors.
            if working:
                prev=working[-1]
                sig=lambda d:(
                    d.get('action'),d.get('tag'),d.get('text'),d.get('id'),
                    d.get('href'),d.get('testid'),d.get('aria'),
                    d.get('placeholder'),d.get('name'),d.get('value'),
                    d.get('scope'),round(float(d.get('dx',0) or 0),1),
                    round(float(d.get('dy',0) or 0),1),
                    round(float(d.get('toX',0) or 0),1),
                    round(float(d.get('toY',0) or 0),1)
                )
                if sig(prev)==sig(clean):
                    continue
            working.append(clean)
            if len(working)>40:
                del working[:-40]
            added+=1

        if added:
            self.lobby_teach_index=len(working)
            with self.state.lock:
                self.state.autolobby_status=(
                    f'ÖĞREN AÇIK • {len(working)} işlem kaydedildi • bitince ÖĞREN BİTİR'
                )

    def _recovery_guard_allows(self):
        """Prevent restart storms: maximum 4 automatic restarts per 10 minutes."""
        now = time.time()
        events = []
        try:
            with open(self.recovery_guard_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            events = [float(x) for x in (raw.get("events") or [])]
        except Exception:
            events = []
        events = [x for x in events if 0 <= now - x <= 600.0]
        if len(events) >= 4:
            return False, events
        events.append(now)
        try:
            os.makedirs(os.path.dirname(self.recovery_guard_path), exist_ok=True)
            with open(self.recovery_guard_path, "w", encoding="utf-8") as f:
                json.dump({"events": events}, f)
        except Exception:
            pass
        return True, events

    def request_auto_restart(self, reason):
        now = time.time()
        if now - float(self.recovery_last_request or 0.0) < 15.0:
            return False
        with self.state.lock:
            if self.state.restart_requested:
                return False

        allowed, events = self._recovery_guard_allows()
        if not allowed:
            with self.state.lock:
                self.state.autorecover_status = (
                    "AUTO KURTARMA: KİLİTLİ • 10 dk içinde 4 yeniden başlatma"
                )
            return False

        self.recovery_last_request = now
        with self.state.lock:
            self.state.restart_requested = True
            self.state.restart_reason = str(reason or "Pragmatic yenileme isteği")
            self.state.autorecover_count = len(events)
            self.state.autorecover_status = (
                f"AUTO KURTARMA: YENİDEN BAŞLATILIYOR • {self.state.restart_reason}"
            )
        return True

    def _handle_recovery_scan(self, sid, value):
        # Never exit with code 77 or kill the user's Chrome session from DOM
        # text matches (words like "yenile" + "bağlantı"/"oturum" appear on
        # normal casino pages and would close Chrome unexpectedly).
        self.recovery_hits[sid] = 0
        return

    def _handle_live_result_candidates(self, sid, candidates):
        # Disabled standalone single-number injection: a single prominent number on
        # screen (e.g. a 20 chip, timer, or wheel graphic) has no sequence context
        # and can prepend a false spin that desynchronizes SON20 continuity.
        # Only sequence-verified sources (DOM history bar, Pragmatic API, DGA, SON500)
        # are allowed to advance self.state.history.
        self.live_result_probe.pop(sid, None)
        return False

    def _handle_table_nav_scan(self, scan_context, value):
        meta = scan_context if isinstance(scan_context, dict) else {
            "session": str(scan_context or ""),
            "context_id": None,
        }
        sid = str(meta.get("session") or "")
        if not self.table_scan_enabled or not sid or not isinstance(value, dict):
            return
        if not self._is_collector_session(sid):
            return
        now = time.time()
        if now - float(self.table_scan_started or now) > 1200.0:
            self.stop_table_scan("20 dakika sınırı tamamlandı")
            return
        mode = str(value.get("mode") or "unknown")
        stage = str(value.get("stage") or "")
        if mode in ("provider_lobby", "navigating"):
            self.table_scan_last_view = now

        prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
        returning_to_lobby = bool(
            self.table_scan_tab_walk
            and float(getattr(self, "table_scan_returning_until", 0.0) or 0.0) > now
        )
        recent_lobby_visible = bool(
            self.table_scan_tab_walk
            and not self.table_scan_current_click_key
            and float(getattr(self, "table_scan_lobby_seen_at", 0.0) or 0.0)
            and now - float(getattr(self, "table_scan_lobby_seen_at", 0.0) or 0.0) <= 30.0
        )
        if (returning_to_lobby or recent_lobby_visible) and mode in ("game_has_son500", "game_no_son500", "game_blocked"):
            # V2.9.42: ignore stale child game frames just after we pressed the
            # in-game Lobi button or after the root page has already shown real
            # lobby cards. The visible lobby scan will continue/finish the pass.
            return

        if mode in ("korece_rulet_stop", "prive_lounge_stop"):
            with self.state.lock:
                bank_count = len(self.state.table_registry)
            self.stop_table_scan(
                f"Korece Rulet masasına ulaşıldı • tarama tamamlandı • kayıtlı banka {bank_count}"
            )
            return

        if mode == "masa_dolu_skip":
            self._mark_current_scan_card_done()
            key = str(self.table_scan_current_click_key or self.table_scan_last_clicked_label or sid)
            if key:
                self.table_scan_probe_done.add(key)
                self.table_scan_probe_skip.add(key)
            for scan_sid in list(self.table_scan_click_deadlines.keys()):
                if self._is_collector_session(scan_sid):
                    self.table_scan_click_deadlines.pop(scan_sid, None)
                    self.table_scan_click_started_at.pop(scan_sid, None)
            self.table_scan_current_click_key = ""
            self.table_scan_current_click_label = ""
            with self.state.lock:
                self.state.table_scan_status = (
                    f"{prefix}: Masa dolu uyarısı kapatıldı • sıradaki masaya geçiliyor"
                )
            return

        if mode in ("game_no_son500", "game_blocked"):
            if self.table_scan_tab_walk and not self.table_scan_click_deadlines:
                return
            self._mark_current_scan_card_done(label=str(value.get("title") or ""))
            key = str(self.table_scan_current_click_key or self.table_scan_last_clicked_label or sid)
            if key:
                self.table_scan_probe_done.add(key)
                self.table_scan_probe_skip.add(key)
            label = self._clean_collector_label(
                self.table_scan_current_click_label
                or self.table_scan_last_clicked_label
                or str(value.get("title") or "Roulette"),
                fallback="Roulette",
            )
            reason = "bloklu masa" if mode == "game_blocked" else "SON500 paneli yok"
            with self.state.lock:
                self.state.table_scan_status = (
                    f"{prefix}: {reason} • {label[:44]} • anında es geçiliyor"
                )
            self._return_collector_to_lobby(sid, f"{reason} • es geçildi")
            self.table_scan_current_click_key = ""
            self.table_scan_current_click_label = ""
            return

        if mode == "game_has_son500":
            # V2.9.39: The game screen is open and SON500 is visible. Do not
            # let the generic lobby/card scanner interpret betting grid numbers
            # as roulette cards. Recreate the table wait if it was lost; the
            # next scan loop will run HISTORY500_SCAN and save 500/500.
            self._mark_current_scan_card_done(label=str(value.get("title") or ""))
            if not self.table_scan_click_deadlines:
                self.table_scan_click_deadlines[sid] = now + TAB_WALK_TABLE_TIMEOUT_SECONDS
                self.table_scan_click_started_at.setdefault(sid, now)
            label = self._clean_collector_label(
                self.table_scan_current_click_label
                or self.table_scan_last_clicked_label
                or str(value.get("title") or "Roulette"),
                fallback="Roulette",
            )
            try:
                collector_tid = str(
                    (self.session_table_activity.get(sid, {}) or {}).get("table_id", "")
                    or ""
                )
                fallback_tid, fallback_title = self._collector_table_identity(
                    sid,
                    real_table_id=collector_tid,
                    title=label,
                )
                params = {
                    "expression": HISTORY500_SCAN,
                    "returnByValue": True,
                    "awaitPromise": True,
                }
                context_id = meta.get("context_id")
                if context_id is not None:
                    params["contextId"] = int(context_id)
                self.send(
                    "Runtime.evaluate",
                    params,
                    session_id=sid,
                    kind="background500",
                    context={
                        "session": sid,
                        "table_id": fallback_tid,
                        "real_table_id": collector_tid,
                        "title": fallback_title,
                        "collector": True,
                    },
                )
            except Exception:
                pass
            with self.state.lock:
                self.state.table_scan_status = (
                    f"{prefix}: masa açık • SON500 paneli görüldü • {label[:44]} • 500 spin okunuyor"
                )
            return

        if mode == "waiting":
            if now - float(self.table_scan_last_view or 0.0) < 8.0:
                return
            if stage == "provider-context":
                message = "Pragmatic Play sağlayıcı lobisi bekleniyor"
            elif stage.endswith("-failed"):
                message = f"lobi menüsü açılamadı • {stage}"
            else:
                message = "lobi görünümü bekleniyor"
            with self.state.lock:
                self.state.table_scan_status = f"{prefix}: {message}"
            return

        if mode == "navigating":
            if stage == "pragmatic-lobby-card-play":
                message = "site aramasındaki Pragmatic Play Lobby kartında Oyna tıklandı"
            elif stage == "pragmatic-lobby-search-typed":
                message = "arama kutusuna pragmatic play lobby yazıldı"
            elif stage == "menu-opened":
                message = "sol kategori menüsü açıldı • Rulet seçiliyor"
            elif stage == "roulette-selecting":
                message = "Rulet kategorisi seçiliyor"
            elif stage == "roulette-selected":
                message = "Rulet kategorisi seçildi • masa listesi yükleniyor"
            else:
                message = "Pragmatic lobi içinde geziniliyor"
            with self.state.lock:
                self.state.table_scan_status = f"{prefix}: {message}"
            return

        if mode == "card_clicked":
            self.table_scan_returning_until = 0.0
            self.table_scan_lobby_seen_at = 0.0
            self.table_scan_last_card_click_ts = now
            clicked_key = str(value.get("clickedKey") or "").strip()
            clicked_label = str(value.get("clickedLabel") or "").strip()
            if clicked_label:
                self.table_scan_current_click_label = clicked_label
                self.table_scan_last_clicked_label = clicked_label
            if clicked_key:
                self.table_scan_current_click_key = clicked_key
                attempts_map = getattr(self, "table_scan_click_attempts", None)
                if attempts_map is None:
                    attempts_map = {}
                    self.table_scan_click_attempts = attempts_map
                attempts = int(attempts_map.get(clicked_key, 0) or 0) + 1
                attempts_map[clicked_key] = attempts
                if attempts >= 3:
                    self.table_scan_clicked_keys.add(clicked_key)
            if self._is_korece_table(label=clicked_label):
                self.table_scan_stop_after_current = True
            for row in [r for r in (value.get("cards") or []) if isinstance(r, dict)]:
                key = str(row.get("key") or "").strip()
                if key:
                    self.table_scan_visited.add(key)
                table_id = str(row.get("table_id") or "").strip()
                if table_id:
                    self.table_scan_found_ids.add(table_id)
                    self._register_discovered_tables([{
                        "table_id": table_id,
                        "display_name": str(row.get("label") or table_id),
                    }], source="PRAGMATIC LOBI KARTI")
            wait_seconds = (
                TAB_WALK_TABLE_TIMEOUT_SECONDS
                if self.table_scan_tab_walk
                else COLLECTOR_CARD_CLICK_SECONDS
            )
            self.table_scan_click_deadlines[sid] = now + wait_seconds
            self.table_scan_click_started_at = {sid: now}
            # Clear stale table activity from the previous table; otherwise a
            # cached statisticHistory/resource entry can be mistaken for the
            # newly clicked table and make the collector return immediately.
            for scan_sid in list(self.session_info.keys()):
                if self._is_collector_session(scan_sid):
                    self.session_table_activity.pop(scan_sid, None)
            clean_clicked_label = self._clean_collector_label(clicked_label, fallback="veri bekleniyor")
            with self.state.lock:
                self.state.table_scan_status = (
                    f"{prefix}: masa kartı tıklandı • "
                    + (clean_clicked_label[:60] if clean_clicked_label else "veri bekleniyor")
                    + " • sağ-alt SON500 paneli bekleniyor"
                )
            return

        if mode != "provider_lobby":
            return

        cards = [row for row in (value.get("cards") or []) if isinstance(row, dict)]
        if not cards and self.table_scan_visited:
            return
        if self.table_scan_tab_walk and cards:
            self.table_scan_lobby_seen_at = now
            last_click_age = now - float(getattr(self, "table_scan_last_card_click_ts", 0.0) or 0.0)
            if returning_to_lobby:
                self.table_scan_returning_until = 0.0
                self.table_scan_lobby_settle_until = now + 0.32
                for scan_sid in list(self.session_info.keys()):
                    if self._is_collector_session(scan_sid):
                        self.table_scan_click_deadlines.pop(scan_sid, None)
                        self.table_scan_click_started_at.pop(scan_sid, None)
                        self.session_table_activity.pop(scan_sid, None)
                self.table_scan_current_click_key = ""
                self.table_scan_current_click_label = ""
            elif self.table_scan_click_deadlines and last_click_age >= 2.4:
                for scan_sid in list(self.session_info.keys()):
                    if self._is_collector_session(scan_sid):
                        self.table_scan_click_deadlines.pop(scan_sid, None)
                        self.table_scan_click_started_at.pop(scan_sid, None)
                        self.session_table_activity.pop(scan_sid, None)
        before = len(self.table_scan_visited)
        queued_probes = 0
        for row in cards:
            key = str(row.get("key") or "").strip()
            if not key:
                key = str(row.get("label") or "") + "|" + str(row.get("href") or "")
            if key:
                self.table_scan_visited.add(key)
            table_id = str(row.get("table_id") or "").strip()
            if table_id:
                self.table_scan_found_ids.add(table_id)
                self._register_discovered_tables([{
                    "table_id": table_id,
                    "display_name": str(row.get("label") or table_id),
                }], source="PRAGMATIC LOBI KARTI")
            if (not self.table_scan_tab_walk) and (not table_id) and self._queue_table_probe(row):
                queued_probes += 1

        if queued_probes:
            self._pump_table_scan_probes()

        new_cards = len(self.table_scan_visited) - before
        try:
            scroll_height = int(value.get("scrollHeight", 0) or 0)
            scroll_top = int(value.get("scrollTop", 0) or 0)
            client_height = int(value.get("clientHeight", 0) or 0)
        except (TypeError, ValueError):
            scroll_height = scroll_top = client_height = 0
        at_bottom = bool(value.get("atBottom", False))

        if scroll_height != self.table_scan_last_scroll_height:
            self.table_scan_last_scroll_height = scroll_height
            self.table_scan_no_progress = 0
        elif at_bottom and new_cards == 0 and self.table_scan_visited:
            self.table_scan_no_progress += 1
        else:
            self.table_scan_no_progress = 0

        self._pump_table_scan_probes()
        probe_active = len(self.table_scan_probe_targets)
        probe_waiting = len(self.table_scan_probe_queue)
        scan_id_count = len(self.table_scan_found_ids)
        remaining_clicks = max(0, len(self.table_scan_visited) - len(self.table_scan_clicked_keys))
        with self.state.lock:
            bank_count = len(self.state.table_registry)
        if (
            at_bottom
            and self.table_scan_no_progress >= 4
            and probe_active == 0
            and probe_waiting == 0
            and remaining_clicks <= 0
            and not self.table_scan_click_deadlines
        ):
            self.stop_table_scan(
                f"lobi sonuna ulaşıldı • {len(self.table_scan_visited)} kart, "
                f"bu taramada {scan_id_count} gerçek masa ID • kayıtlı banka {bank_count}"
            )
            return

        active_limit = (
            1 if self.table_scan_tab_walk else (
                COLLECTOR_PROBE_STEADY_CONCURRENT
                if self.table_scan_found_ids
                else COLLECTOR_PROBE_INITIAL_CONCURRENT
            )
        )
        if self.table_scan_tab_walk:
            done_count = len(self.table_scan_probe_done)
            ok_count = len(self.table_scan_probe_success)
            fail_count = len(self.table_scan_probe_fail)
            skip_count = len(getattr(self, "table_scan_probe_skip", set()) or set())
            waiting = bool(self.table_scan_click_deadlines)
            probe_text = (
                f"tek yan sekme • {'masada veri bekliyor' if waiting else f'kalan {remaining_clicks} kart'} • "
                f"tamam {done_count} OK {ok_count} atla {skip_count} hata {fail_count} • "
            )
        else:
            probe_text = (
                f"ek sekme hattı {probe_active}/{active_limit} aktif {probe_waiting} bekliyor • "
                if active_limit > 0
                else f"tek sekme tıklama • kalan görünen {remaining_clicks} • "
            )
        with self.state.lock:
            self.state.table_scan_status = (
                f"{prefix}: Rulet lobisi • "
                f"{len(self.table_scan_visited)} kart / bu taramada {scan_id_count} gerçek masa ID "
                f"/ kayıtlı banka {bank_count} • "
                f"{probe_text}"
                f"kaydırma {min(scroll_top + client_height, scroll_height)}/"
                f"{scroll_height or 'bekleniyor'}"
            )

    def attach_target(self, ti):
        tid = ti.get("targetId")
        typ = ti.get("type")
        if not tid or typ not in self.TARGET_TYPES:
            return

        self.target_info[tid] = dict(ti)
        if (
            typ == "iframe"
            and self.table_scan_enabled
            and self.table_scan_target_id
            and tid not in self.target_parent
        ):
            self.target_parent[tid] = str(self.table_scan_target_id)
        self.save_roulette_url(ti)

        if tid in self.target_sessions or tid in self.attaching:
            return

        self.attaching.add(tid)
        self.send(
            "Target.attachToTarget",
            {"targetId":tid, "flatten":True},
            kind="attach",
            context=tid
        )

    def enable_session(self, sid):
        try:
            self.send("Network.enable", {}, session_id=sid)
            self.send("Runtime.enable", {}, session_id=sid)
            self.send(
                "Target.setAutoAttach",
                {
                    "autoAttach":True,
                    "waitForDebuggerOnStart":False,
                    "flatten":True
                },
                session_id=sid
            )
            if not getattr(self, "_startup_url_restored", False):
                info = self.session_info.get(sid, {}) or {}
                raw_cur_url = str(info.get("url", "") or "").strip()
                cur_url = raw_cur_url.lower()
                if (
                    str(info.get("type", "") or "").lower() == "page"
                    and "/live-casino" in cur_url
                    and "opengames=" in cur_url
                    and "3300922-real" not in cur_url
                ):
                    healed_url = safe_last_page_url(raw_cur_url)
                    if healed_url and healed_url != raw_cur_url:
                        self._startup_url_restored = True
                        self.save_roulette_url({"type": "page", "url": healed_url, "title": "Pragmatic Play Lobby"})
                        self.send("Page.navigate", {"url": healed_url}, session_id=sid)
                        return

                has_web_page = any(
                    str(ti.get("type", "") or "").lower() == "page"
                    and str(ti.get("url", "") or "").startswith(("http://", "https://"))
                    for ti in self.target_info.values()
                )
                if has_web_page:
                    self._startup_url_restored = True
                else:
                    if (
                        str(info.get("type", "") or "").lower() == "page"
                        and not cur_url.startswith(("http://", "https://", "devtools://", "chrome-extension://"))
                    ):
                        saved_url = self._saved_lobby_url()
                        if saved_url:
                            self._startup_url_restored = True
                            self.send("Page.navigate", {"url": saved_url}, session_id=sid)
        except Exception:
            pass

    def _handle_lobby_nav(self, sid, value):
        if not isinstance(value, dict):
            return
        stage = str(value.get("stage") or "SEARCHING")
        action = str(value.get("action") or "WAIT")
        text = str(value.get("text") or "").strip()
        wanted = str(value.get("wanted") or "").strip()
        labels = {
            "LEARNED_STEP": "öğrenilen tıklama uygulanıyor",
            "LEARNED_TYPE": "öğrenilen arama metni yazılıyor",
            "LEARNED_SCROLL": "öğrenilen kullanıcı kaydırması uygulanıyor",
            "ROUTE_DONE": "öğrenilen yol tamamlandı",
            "TEACH_REQUIRED": "ÖĞREN GEREKİYOR • otomatik arama kapalı",
            "LEARNED_NOT_FOUND": "sıradaki adım bekleniyor • GERİ SARMA YOK",
            "GAME_OPEN": "MASA AÇIK • veri toplama aktif",
            "COOLDOWN": "menü geçişi bekleniyor",
        }
        msg = labels.get(stage, stage)
        if action in ("CLICK","TYPE","TYPE_DONE","SCROLL"):
            try:
                idx=int(value.get("step_index",-1))
                total=int(value.get("total",len(self.lobby_teach_steps)) or len(self.lobby_teach_steps))
                if idx >= 0:
                    self.lobby_replay_index=min(total,idx+1)
                    msg += f" • {idx+1}/{total}"
            except Exception:
                pass
            if text:
                prefix = (
                    "YAZ " if action in ("TYPE","TYPE_DONE")
                    else "KAYDIR " if action == "SCROLL"
                    else ""
                )
                msg += f" • {prefix}{text[:42]}"
        if stage == "LEARNED_NOT_FOUND" and wanted:
            try:
                msg += (
                    f" • {self.lobby_replay_index+1}/{len(self.lobby_teach_steps)}"
                    f" • ARIYOR: {wanted[:58]}"
                )
            except Exception:
                msg += f" • ARIYOR: {wanted[:58]}"

        if stage == "GAME_OPEN":
            self.lobby_route_started = False
        elif stage == "ROUTE_DONE":
            self.lobby_route_started = False
        with self.state.lock:
            self.state.autolobby_status = f"ÖĞREN: {msg}"

    def _recent_active_game(self):
        sid = str(self.active_game_sid or "")
        if not sid:
            return False
        act = self.session_table_activity.get(sid, {}) or {}
        last = float(act.get("last", 0.0) or 0.0)
        return bool(last and time.time() - last <= 45.0)

    def is_lobby_nav_target(self, sid):
        info = self.session_info.get(sid, {}) or {}
        typ = str(info.get("type", "") or "").lower()
        url = str(info.get("url", "") or "")
        low = url.lower()
        if typ != "page":
            return False
        if not url.startswith(("http://", "https://")):
            return False
        if "devtools://" in low or "gamedata365.com" in low:
            return False
        return True

    def is_roulette_target(self, sid):
        info = self.session_info.get(sid,{})
        txt = (str(info.get("url",""))+" "+str(info.get("title",""))).lower()
        if any(
            x in txt
            for x in (
                "roulette", "rulet", "pragmatic", "/desktop/", "/gs2c/game/",
                "opengames=", "live-casino", "livecasino",
            )
        ):
            return True
        for ctx in (self.execution_contexts.get(sid) or {}).values():
            origin = str(ctx.get("origin") or "").lower()
            name = str(ctx.get("name") or "").lower()
            if any(x in (origin + " " + name) for x in ("pragmatic", "games.", "client.", "roulette", "rulet")):
                return True
        return False

    def is_recovery_target(self, sid):
        info = self.session_info.get(sid,{})
        url = str(info.get("url","") or "").lower()
        title = str(info.get("title","") or "").lower()
        txt = url + " " + title
        return (
            self.is_roulette_target(sid)
            or "opengames=" in url
            or "searchterm=pragmatic" in url
            or "live-casino" in url
            or "livecasino" in url
        )

    def is_direct_probe_target(self, sid):
        info = self.session_info.get(sid,{})
        url = str(info.get("url","")).lower()
        typ = str(info.get("type","")).lower()

        if not url.startswith(("http://","https://")):
            return False
        if "devtools://" in url or "gamedata365.com" in url:
            return False

        # Main page and OOPIF targets can hold different ResourceTiming entries.
        if typ and typ not in ("page","iframe"):
            return False
        return True

    def is_table_scan_target(self, sid):
        if not self.is_direct_probe_target(sid):
            return False
        info = self.session_info.get(sid, {}) or {}
        url = str(info.get("url", "") or "").lower()
        title = str(info.get("title", "") or "").lower()
        text = url + " " + title
        if any(x in text for x in (
            "livechat", "gamedata365", "youtube", "facebook", "google",
        )):
            return False
        return (
            sid == self.active_game_sid
            or self._is_collector_session(sid)
            or "client." in url
            or "games." in url
            or "/desktop/" in url
            or "/gs2c/game/" in url
            or "/apps/lobby/" in url
            or "roulette" in text
            or "rulet" in text
            or "pragmatic" in text
        )

    def _record_theme_and_game_meta(self, sid, url):
        raw = str(url or "")
        try:
            m = re.search(r"/themes/([^/]+)/theme\.json", raw, flags=re.I)
            if m and sid:
                self.session_theme[sid] = m.group(1)
        except Exception:
            pass

        try:
            u = urllib.parse.urlsplit(raw)
            qs = urllib.parse.parse_qs(u.query)
            casino_id = str((
                qs.get("casinoId")
                or qs.get("casinoID")
                or qs.get("casinoid")
                or [""]
            )[0] or "")
            currency = str((
                qs.get("currency")
                or qs.get("currencyId")
                or qs.get("currencyID")
                or [""]
            )[0] or "")
            if casino_id or currency:
                self._record_dga_config(
                    casino_id=casino_id,
                    currency=currency,
                    source="Pragmatic URL",
                )
            if "/api/ge/versions" in u.path.lower():
                game = str((qs.get("operatorGameId") or [""])[0] or "")
                if game and sid:
                    self.session_operator_game[sid] = game
        except Exception:
            pass

    def _note_table_activity(self, sid, template, url=""):
        if not sid or not isinstance(template, dict):
            return False
        table_id = str(template.get("table_id") or "")
        if not table_id:
            return False

        is_col = self._is_collector_session(sid)
        if is_col and self.table_scan_tab_walk and not self.table_scan_click_deadlines:
            return False

        now = time.time()
        raw_title = str(self.session_info.get(sid, {}).get("title", "") or table_id)
        if is_col:
            title = self._clean_collector_label(
                self.table_scan_current_click_label
                or self.table_scan_last_clicked_label
                or raw_title,
                fallback=table_id,
            )
        else:
            title = raw_title
        should_persist = False
        if is_col or self.manual_api_teach:
            with self.collector_lock:
                seen = self.collector_seen.get(table_id, {}) or {}
                should_persist = (
                    not seen
                    or now - float(seen.get("last_discovered", 0.0) or 0.0) >= 60.0
                )
                if should_persist:
                    merged = dict(seen)
                    merged.update({
                        "table_id": table_id,
                        "display_name": title,
                        "last_discovered": now,
                        "source": "AÇIK PRAGMATIC MASA",
                    })
                    merged.setdefault("last_requested", 0.0)
                    self.collector_seen[table_id] = merged
        if should_persist:
            self.state.mark_table_discovered(
                table_id,
                display_name=title,
                source="API ÖĞREN" if self.manual_api_teach else "AÇIK PRAGMATIC MASA",
            )

        if self.manual_api_teach:
            with self.state.lock:
                learned_count = len(self.state.table_registry)
                self.state.table_scan_status = (
                    f"MASA API ÖĞREN: {learned_count} masa öğrendi • "
                    f"son: {title[:42]} • SON500/API bekleniyor"
                )

        if self._is_collector_session(sid):
            self.table_scan_found_ids.add(table_id)
            # V2.9.35: once the collector is back in the Pragmatic lobby, lobby
            # preview/card API calls may still contain tableId. Do not recreate
            # a table wait from those stale/lobby-preview requests; only extend
            # the wait if a real card click is already in progress.
            if self.table_scan_tab_walk and not self.table_scan_click_deadlines:
                pass
            else:
                self._mark_current_scan_card_done(
                    table_id=table_id,
                    label=title,
                    theme_code=str(self.session_theme.get(sid, "") or ""),
                )
                wait_seconds = (
                    TAB_WALK_TABLE_TIMEOUT_SECONDS
                    if self.table_scan_tab_walk
                    else 8.0
                )
                self.table_scan_click_deadlines[sid] = now + wait_seconds
                if self.table_scan_tab_walk:
                    started = max([float(x or 0.0) for x in self.table_scan_click_started_at.values()] or [0.0])
                    self.table_scan_click_started_at.setdefault(sid, started or now)
                with self.state.lock:
                    prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
                    self.state.table_scan_status = (
                        f"{prefix}: tableId yakalandı • {table_id} • sağ-alt SON500 paneli bekleniyor"
                    )
                probe_tid = self._target_id_for_session(sid)
                if probe_tid in self.table_scan_probe_targets:
                    self.table_scan_probe_targets[probe_tid]["table_id_seen"] = table_id
                    self.table_scan_probe_targets[probe_tid]["table_seen_at"] = now

        old = self.session_table_activity.get(sid, {})
        hits = (
            int(old.get("hits", 0)) + 1
            if str(old.get("table_id") or "") == table_id
            else 1
        )
        self.session_table_activity[sid] = {
            "table_id": table_id,
            "last": now,
            "hits": min(hits, 1000),
        }
        return self._select_active_table()

    def _select_active_table(self):
        now = time.time()
        candidates = []

        for sid, act in list(self.session_table_activity.items()):
            # The collector has its own hidden Chrome target. It must never
            # become the user's active prediction table.
            if self._is_collector_session(sid):
                continue
            age = now - float(act.get("last", 0.0) or 0.0)
            if age > 45.0:
                continue

            vis = self.session_visibility.get(sid, {})
            visibility = str(vis.get("visibility", "") or "").lower()
            focus = bool(vis.get("focus", False))

            score = 0.0
            if visibility == "visible":
                score += 1000.0
            if focus:
                score += 300.0
            score += min(int(act.get("hits", 0)), 20) * 4.0
            score += max(0.0, 80.0 - age * 10.0)

            candidates.append((score, float(act.get("last", 0.0)), sid, act))

        if not candidates:
            return False

        candidates.sort(key=lambda row: (-row[0], -row[1]))
        _score, _last, sid, act = candidates[0]
        table_id = str(act.get("table_id") or "")
        if not table_id:
            return False

        changed = sid != self.active_game_sid or table_id != self.active_table_id
        if changed:
            self.active_game_sid = sid
            self.active_table_id = table_id

            info = self.session_info.get(sid, {})
            self.state.set_pragmatic_identity(
                table_id=table_id,
                operator_game_id=str(self.session_operator_game.get(sid, "") or ""),
                theme_code=str(self.session_theme.get(sid, "") or ""),
                title=str(info.get("title", "") or ""),
            )
            with self.state.lock:
                self.state.direct_history_status = (
                    f"PRAGMATIC DIRECT: aktif masa seçildi • tableId {table_id}"
                )
        return changed

    def _is_active_session(self, sid):
        if self._is_collector_session(sid):
            return False
        if (not self.active_game_sid) or sid == self.active_game_sid:
            return True
        act = self.session_table_activity.get(sid, {}) or {}
        tid = str(act.get("table_id", "") or "")
        if not tid or (self.active_table_id and tid == self.active_table_id):
            return True
        return False

    def scan_dom_loop(self):
        last_500_scan = {}
        last_background_scan = {}
        last_direct_scan = {}
        last_visibility_scan = {}
        last_table_nav_scan = {}

        while not self.stop_event.is_set():
            try:
                now = time.time()

                if (
                    self.table_scan_auto_cycle
                    and not self.table_scan_enabled
                    and not self.manual_api_teach
                    and float(self.table_scan_next_cycle or 0.0) > 0.0
                    and now >= float(self.table_scan_next_cycle or 0.0)
                ):
                    if self.table_scan_tab_walk:
                        self.start_tab_walk_scan(auto_cycle=True)
                    else:
                        self.start_table_scan(auto_cycle=True)

                # V2.9.5 ÖĞRET MODU:
                # No blind scrolling and no generic text-based wandering.
                # During training we only observe the user's own four clicks.
                # Afterwards only the learned descriptors are used.
                if self._recent_active_game():
                    with self.state.lock:
                        self.state.autolobby_status = (
                            "ÖĞREN: MASA AÇIK • veri toplama aktif"
                        )
                elif self.table_scan_enabled:
                    with self.state.lock:
                        self.state.autolobby_status = (
                            "ÖĞREN: Pragmatic masa taraması sırasında beklemede"
                        )
                elif self.lobby_teaching:
                    for nav_sid in list(self.session_info.keys()):
                        if (
                            self.is_lobby_nav_target(nav_sid)
                            and not self._is_collector_session(nav_sid)
                            and now - float(self.lobby_last_scan.get(nav_sid, 0.0)) >= 0.18
                        ):
                            self.lobby_last_scan[nav_sid] = now
                            self.send(
                                "Runtime.evaluate",
                                {
                                    "expression": LOBBY_TEACH_SCAN,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                },
                                session_id=nav_sid,
                                kind="lobbyteach",
                                context=nav_sid,
                            )
                elif self.lobby_teach_ready() and self.lobby_route_started:
                    learned_js = build_learned_lobby_scan(
                        self.lobby_teach_steps,
                        self.lobby_replay_index,
                    )
                    for nav_sid in list(self.session_info.keys()):
                        if (
                            self.is_lobby_nav_target(nav_sid)
                            and not self._is_collector_session(nav_sid)
                            and now - float(self.lobby_last_scan.get(nav_sid, 0.0)) >= 1.5
                        ):
                            self.lobby_last_scan[nav_sid] = now
                            self.send(
                                "Runtime.evaluate",
                                {
                                    "expression": learned_js,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                },
                                session_id=nav_sid,
                                kind="lobbylearned",
                                context=nav_sid,
                            )
                elif self.lobby_teach_ready():
                    # Do NOT auto-start learned route replay on startup; Chrome
                    # already opens the user's last visited URL and auto-replay
                    # would force-scroll the page or click lobby cards while the
                    # user is browsing with the mouse.
                    with self.state.lock:
                        self.state.autolobby_status = (
                            f"ÖĞREN: HAZIR ({len(self.lobby_teach_steps)} adım) • manuel kontrolde"
                        )
                else:
                    with self.state.lock:
                        self.state.autolobby_status = (
                            "ÖĞREN: PASİF • son sayfa otomatik açıldı"
                        )

                for sid in list(self.session_info.keys()):
                    if self.table_scan_enabled and self._is_collector_session(sid):
                        due = float(self.table_scan_click_deadlines.get(sid, 0.0) or 0.0)
                        if due and now >= due:
                            if self.table_scan_tab_walk:
                                probe_tid = self._target_id_for_session(sid)
                                key = str(self.table_scan_current_click_key or probe_tid or sid)
                                if probe_tid in self.table_scan_probe_targets:
                                    row = self.table_scan_probe_targets[probe_tid]
                                    key = str(row.get("key") or key)
                                    row["done_at"] = now
                                success_seen = key in self.table_scan_probe_success
                                skip_seen = key in getattr(self, "table_scan_probe_skip", set())
                                if not success_seen and not skip_seen:
                                    self.table_scan_probe_done.add(key)
                                    self.table_scan_probe_fail.add(key)
                                self.table_scan_current_click_key = ""
                                self.table_scan_current_click_label = ""
                                if success_seen:
                                    reason = "veri alındı"
                                elif skip_seen:
                                    reason = "SON500 yok • es geçildi"
                                else:
                                    reason = "veri zaman aşımı"
                                self._return_collector_to_lobby(sid, reason)
                            else:
                                self._return_collector_to_lobby(sid, "masa denemesi tamamlandı")
                            continue

                    if self.is_direct_probe_target(sid):
                        if now - float(last_visibility_scan.get(sid, 0.0)) >= 2.0:
                            last_visibility_scan[sid] = now
                            self.send(
                                "Runtime.evaluate",
                                {
                                    "expression": VISIBILITY_SCAN,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                },
                                session_id=sid,
                                kind="visibility",
                                context=sid,
                            )

                    if self.is_roulette_target(sid) and self._is_active_session(sid):
                        # When a dedicated Pragmatic game iframe target is active
                        # (e.g. client.*/desktop/roulette), do NOT hammer the parent
                        # casino page DOM and do NOT duplicate the default context!
                        active_info = self.session_info.get(self.active_game_sid, {}) or {}
                        active_url = str(active_info.get("url", "") or "").lower()
                        has_dedicated_game_target = bool(
                            self.active_game_sid
                            and (
                                "/desktop/roulette" in active_url
                                or "client." in active_url
                                or "games." in active_url
                            )
                        )
                        if has_dedicated_game_target and sid != self.active_game_sid:
                            active_ctx_ids = []
                        elif has_dedicated_game_target:
                            active_ctx_ids = [None]
                        else:
                            sid_url = str((self.session_info.get(sid, {}) or {}).get("url", "") or "").lower()
                            sid_host = urllib.parse.urlsplit(sid_url).netloc.lower()
                            active_ctx_ids = [None]
                            for ctx in (self.execution_contexts.get(sid) or {}).values():
                                cid = ctx.get("id")
                                aux = ctx.get("auxData") or {}
                                origin = str(ctx.get("origin") or "").lower()
                                if cid is None or not bool(aux.get("isDefault", False)):
                                    continue
                                if not origin.startswith(("http://", "https://")):
                                    continue
                                ctx_host = urllib.parse.urlsplit(origin).netloc.lower()
                                if sid_host and ctx_host == sid_host:
                                    continue
                                if any(b in origin for b in ("livechat", "gamedata365", "google", "facebook", "youtube")):
                                    continue
                                active_ctx_ids.append(int(cid))
                            active_ctx_ids = list(dict.fromkeys(active_ctx_ids))[:3]

                        for ctx_id in active_ctx_ids:
                            dom_params = {
                                "expression": DOM_SCAN,
                                "returnByValue": True,
                                "awaitPromise": True,
                            }
                            if ctx_id is not None:
                                dom_params["contextId"] = int(ctx_id)
                            self.send(
                                "Runtime.evaluate",
                                dom_params,
                                session_id=sid,
                                kind="domscan",
                                context={"session": sid, "context_id": ctx_id},
                            )

                        if active_ctx_ids and now - float(last_500_scan.get(sid, 0.0)) >= 3.5:
                            last_500_scan[sid] = now
                            # CRITICAL: On the user's active tab, ALWAYS use
                            # ACTIVE_HISTORY500_SCAN (ALLOW_EXPAND = false) so
                            # the program never clicks or expands anything while
                            # the user is browsing the lobby or playing!
                            for ctx_id in active_ctx_ids:
                                h500_params = {
                                    "expression": ACTIVE_HISTORY500_SCAN,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                }
                                if ctx_id is not None:
                                    h500_params["contextId"] = int(ctx_id)
                                self.send(
                                    "Runtime.evaluate",
                                    h500_params,
                                    session_id=sid,
                                    kind="history500",
                                    context={"session": sid, "context_id": ctx_id},
                                )

                    if self.is_direct_probe_target(sid) and self._is_active_session(sid):
                        active_info = self.session_info.get(self.active_game_sid, {}) or {}
                        active_url = str(active_info.get("url", "") or "").lower()
                        has_dedicated_game_target = bool(
                            self.active_game_sid
                            and (
                                "/desktop/roulette" in active_url
                                or "client." in active_url
                                or "games." in active_url
                            )
                        )
                        if has_dedicated_game_target and sid != self.active_game_sid:
                            direct_ctx_ids = []
                        elif has_dedicated_game_target:
                            direct_ctx_ids = [None]
                        else:
                            sid_url = str((self.session_info.get(sid, {}) or {}).get("url", "") or "").lower()
                            sid_host = urllib.parse.urlsplit(sid_url).netloc.lower()
                            direct_ctx_ids = [None]
                            for ctx in (self.execution_contexts.get(sid) or {}).values():
                                cid = ctx.get("id")
                                aux = ctx.get("auxData") or {}
                                origin = str(ctx.get("origin") or "").lower()
                                if cid is None or not bool(aux.get("isDefault", False)):
                                    continue
                                if not origin.startswith(("http://", "https://")):
                                    continue
                                ctx_host = urllib.parse.urlsplit(origin).netloc.lower()
                                if sid_host and ctx_host == sid_host:
                                    continue
                                if any(b in origin for b in ("livechat", "gamedata365", "google", "facebook", "youtube")):
                                    continue
                                direct_ctx_ids.append(int(cid))
                            direct_ctx_ids = list(dict.fromkeys(direct_ctx_ids))[:3]
                        for ctx_id in direct_ctx_ids:
                            key = (sid, ctx_id if ctx_id is not None else "default")
                            if now - float(last_direct_scan.get(key, 0.0)) >= 5.0:
                                last_direct_scan[key] = now
                                d_params = {
                                    "expression": DIRECT_HISTORY_SCAN,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                }
                                if ctx_id is not None:
                                    d_params["contextId"] = int(ctx_id)
                                self.send(
                                    "Runtime.evaluate",
                                    d_params,
                                    session_id=sid,
                                    kind="directhistory",
                                    context={
                                        "session": sid,
                                        "context_id": ctx_id,
                                        "origin": "",
                                        "name": "default",
                                    },
                                )

                    if (
                        self.table_scan_enabled
                        and self.table_scan_target_id
                        and self._is_collector_session(sid)
                        and (
                            self.is_table_scan_target(sid)
                            or self.is_recovery_target(sid)
                        )
                    ):
                        # Pragmatic lobby is commonly a cross-origin iframe
                        # inside the operator page. Chrome does not always list
                        # that iframe as a separate Target, but Runtime exposes
                        # its default execution context. Probe those contexts
                        # and keep clicks in the exact context that found cards.
                        scan_contexts = []
                        if self.is_table_scan_target(sid):
                            scan_contexts.append(None)
                        for ctx in (self.execution_contexts.get(sid) or {}).values():
                            cid = ctx.get("id")
                            aux = ctx.get("auxData") or {}
                            origin = str(ctx.get("origin") or "").lower()
                            if cid is None or not bool(aux.get("isDefault", False)):
                                continue
                            if not origin.startswith(("http://", "https://")):
                                continue
                            scan_contexts.append(int(cid))

                        # Preserve order while removing duplicate context ids.
                        scan_contexts = list(dict.fromkeys(scan_contexts))
                        for context_id in scan_contexts:
                            returning_to_lobby = bool(
                                self.table_scan_tab_walk
                                and float(getattr(self, "table_scan_returning_until", 0.0) or 0.0) > now
                            )
                            wait_started = max(
                                [float(x or 0.0) for x in self.table_scan_click_started_at.values()] or [0.0]
                            )
                            skip_runtime_direct = bool(self.table_scan_tab_walk)
                            direct_key = (sid, context_id, "collector_direct")
                            if (not skip_runtime_direct) and now - float(last_direct_scan.get(direct_key, 0.0)) >= 2.0:
                                last_direct_scan[direct_key] = now
                                direct_params = {
                                    "expression": DIRECT_HISTORY_SCAN,
                                    "returnByValue": True,
                                    "awaitPromise": True,
                                }
                                if context_id is not None:
                                    direct_params["contextId"] = int(context_id)
                                self.send(
                                    "Runtime.evaluate",
                                    direct_params,
                                    session_id=sid,
                                    kind="directhistory",
                                    context={
                                        "session": sid,
                                        "context_id": context_id,
                                        "origin": "collector",
                                        "name": "collector",
                                    },
                                )

                            # V2.9.33: in single-tab mode read visible SON 500
                            # only while a clicked table is actually being
                            # waited on. Do not keep scanning stale tableId after
                            # returning to the lobby; that caused confusing
                            # 'bulunan 0' statuses in the lobby.
                            collector_tid = str(
                                (self.session_table_activity.get(sid, {}) or {}).get("table_id", "")
                                or ""
                            )
                            fallback_tid, fallback_title = self._collector_table_identity(
                                sid,
                                real_table_id=collector_tid,
                                title=str(
                                    self.session_info.get(sid, {}).get("title", "")
                                    or self.table_scan_current_click_label
                                ),
                            )
                            history_active = bool(
                                self.table_scan_click_deadlines
                                or self.table_scan_current_click_key
                            )
                            if self.table_scan_tab_walk and history_active and not returning_to_lobby:
                                hist_key = (sid, context_id, "collector_history500")
                                if now - float(last_500_scan.get(hist_key, 0.0)) >= 0.65:
                                    last_500_scan[hist_key] = now
                                    hist_params = {
                                        "expression": HISTORY500_SCAN,
                                        "returnByValue": True,
                                        "awaitPromise": True,
                                    }
                                    if context_id is not None:
                                        hist_params["contextId"] = int(context_id)
                                    self.send(
                                        "Runtime.evaluate",
                                        hist_params,
                                        session_id=sid,
                                        kind="background500",
                                        context={
                                            "session": sid,
                                            "table_id": fallback_tid,
                                            "real_table_id": collector_tid,
                                            "title": fallback_title,
                                            "collector": True,
                                        },
                                    )

                            if (
                                self.table_scan_tab_walk
                                and self.table_scan_click_deadlines
                                and not returning_to_lobby
                            ):
                                continue

                            scan_key = (sid, context_id)
                            if now - float(last_table_nav_scan.get(scan_key, 0.0)) < (0.38 if self.table_scan_tab_walk else 1.5):
                                continue
                            settle_until = float(getattr(self, "table_scan_lobby_settle_until", 0.0) or 0.0)
                            can_click_cards = bool(
                                not returning_to_lobby
                                and not self.table_scan_click_deadlines
                                and now >= settle_until
                            )
                            last_table_nav_scan[scan_key] = now
                            params = {
                                "expression": build_multi_table_nav_scan(
                                    self.table_scan_clicked_keys,
                                    click_cards=can_click_cards,
                                ),
                                "returnByValue": True,
                                "awaitPromise": True,
                            }
                            if context_id is not None:
                                params["contextId"] = int(context_id)
                            self.send(
                                "Runtime.evaluate",
                                params,
                                session_id=sid,
                                kind="collectornavscan",
                                context={
                                    "session": sid,
                                    "context_id": context_id,
                                },
                            )

                self._select_active_table()
                if getattr(self, "api_refresh_mode", False):
                    self._collector_tick()
                self._poll_chrome_dga_runtime()
                self._pump_table_scan_probes()
            except Exception:
                pass

            time.sleep(0.25 if self.table_scan_enabled else 0.5)



    def _direct_template_from_url(self, url):
        try:
            u = urllib.parse.urlsplit(str(url or ""))
            host = str(u.hostname or "")
            if not host or not host.lower().startswith(("games.", "client.")):
                return None
            qs = urllib.parse.parse_qs(u.query)
            table_id = str((qs.get("tableId") or [""])[0] or "")
            session_id = str((qs.get("JSESSIONID") or [""])[0] or "")
            if not table_id or not session_id:
                return None
            return {
                "scheme": u.scheme or "https",
                "netloc": u.netloc,
                "table_id": table_id,
                "session_id": session_id,
            }
        except Exception:
            return None

    def _auth_template_from_url(self, url, sid=""):
        """Capture only an authenticated Pragmatic games endpoint seen in Chrome."""
        try:
            u = urllib.parse.urlsplit(str(url or ""))
            host = str(u.hostname or "")
            if not host or not host.lower().startswith("games."):
                return None
            qs = urllib.parse.parse_qs(u.query)
            jsession = str((qs.get("JSESSIONID") or [""])[0] or "")
            if not jsession:
                return None
            template = {
                "scheme": u.scheme or "https",
                "netloc": u.netloc,
                "session_id": jsession,
                "sid": str(sid or ""),
                "seen": time.time(),
            }
            with self.collector_lock:
                self.auth_templates[u.netloc] = template
            return template
        except Exception:
            return None

    def _register_discovered_tables(self, rows, source="PRAGMATIC LOBI"):
        count = 0
        persist_rows = []
        now = time.time()
        with self.collector_lock:
            for item in rows or []:
                if not isinstance(item, dict):
                    continue
                tid = str(item.get("table_id") or "").strip()
                if not tid:
                    continue
                name = str(item.get("display_name") or tid).strip()
                old = self.collector_seen.get(tid, {}) or {}
                should_persist = (
                    not old
                    or now - float(old.get("last_discovered", 0.0) or 0.0) >= 60.0
                    or (name and name != str(old.get("display_name") or ""))
                )
                merged = dict(old)
                merged.update({
                    "table_id": tid,
                    "display_name": name,
                    "last_discovered": now,
                    "source": str(source or "PRAGMATIC LOBI"),
                })
                merged.setdefault("last_requested", 0.0)
                self.collector_seen[tid] = merged
                if self.table_scan_enabled:
                    self.table_scan_found_ids.add(tid)
                if should_persist:
                    persist_rows.append((tid, name))
                count += 1
        for tid, name in persist_rows:
            self.state.mark_table_discovered(tid, name, source=source)
        return count

    def _start_background_history_request(self, template, table_id, display_name="", force=False):
        if not isinstance(template, dict):
            return False
        tid = str(table_id or "").strip()
        jsession = str(template.get("session_id") or "")
        scheme = str(template.get("scheme") or "https")
        netloc = str(template.get("netloc") or "")
        if not tid or not jsession or not netloc:
            return False

        key = (netloc, tid)
        now = time.time()
        with self.state.lock:
            registry_row = dict(self.state.table_registry.get(tid, {}) or {})
        last_success = float(registry_row.get("last_update_epoch", 0.0) or 0.0)
        last_attempt = float(registry_row.get("last_attempt_epoch", 0.0) or 0.0)
        if not force and not collector_refresh_due(
            now,
            last_success,
            last_attempt,
            bool(registry_row.get("last_error")),
        ):
            return False
        with self.collector_lock:
            if key in self.collector_inflight:
                return False
            seen = self.collector_seen.setdefault(tid, {})
            if not force and now - float(seen.get("last_requested", 0.0) or 0.0) < 1.0:
                return False
            seen["last_requested"] = now
            self.collector_inflight.add(key)
        self.collector_last_start = now
        self.state.mark_table_attempt(tid)

        def worker():
            try:
                query = urllib.parse.urlencode({
                    "JSESSIONID": jsession,
                    "numberOfGames": "500",
                    "tableId": tid,
                })
                url = f"{scheme}://{netloc}/api/ui/statisticHistory?{query}"
                req = urllib.request.Request(url, headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 Chrome/153 Safari/537.36"
                    ),
                    "Accept": "application/json,text/plain,*/*",
                    "Cache-Control": "no-cache",
                })
                with urllib.request.urlopen(req, timeout=8.0) as response:
                    body = response.read(3_000_000)
                nums = extract_statistic_history(body)
                if len(nums) < 20:
                    raise ValueError(f"sonuç ayrıştırılamadı ({len(nums)})")
                self.state.store_background_table_history(
                    nums,
                    table_id=tid,
                    display_name=display_name,
                    source_label="MULTI TABLE statisticHistory",
                )
                self.state.mark_table_attempt(tid, ok=True)
                if self.api_refresh_mode:
                    with self.collector_lock:
                        self.api_refresh_success = int(self.api_refresh_success or 0) + 1
                if self.table_scan_enabled and tid in self.table_scan_found_ids:
                    now_done = time.time()
                    for scan_sid in list(self.table_scan_click_deadlines.keys()):
                        if self.table_scan_tab_walk:
                            self._schedule_collector_return(scan_sid, 0.8)
                        else:
                            self.table_scan_click_deadlines[scan_sid] = min(
                                float(self.table_scan_click_deadlines.get(scan_sid, now_done + 1.0) or 0.0),
                                now_done + 1.0,
                            )
                    for probe_tid, probe_row in list(self.table_scan_probe_targets.items()):
                        if str(probe_row.get("table_id_seen") or probe_row.get("table_id") or "") == tid:
                            probe_row["done_at"] = now_done
                            probe_key = str(probe_row.get("key") or probe_tid)
                            self.table_scan_probe_done.add(probe_key)
                            self.table_scan_probe_success.add(probe_key)
                    with self.state.lock:
                        prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
                        self.state.table_scan_status = (
                            f"{prefix}: API SON500 kaydedildi • {str(display_name or tid)[:44]} • {len(nums)}/500 • minimum bekleme sonrası lobiye dönülecek"
                            if self.table_scan_tab_walk
                            else f"{prefix}: veri alındı • {tid} • sıradaki masaya geçiliyor"
                        )
            except Exception as exc:
                if self.api_refresh_mode:
                    with self.collector_lock:
                        self.api_refresh_fail = int(self.api_refresh_fail or 0) + 1
                if self.table_scan_enabled and tid in self.table_scan_found_ids:
                    now_fail = time.time()
                    if self.table_scan_tab_walk:
                        # Python/API fallback can fail before the visible table
                        # finishes loading. Do not close the real tab for this;
                        # keep waiting for Chrome network/DOM SON500 until the
                        # per-table timeout expires.
                        for scan_sid in list(self.table_scan_click_deadlines.keys()):
                            self.table_scan_click_deadlines[scan_sid] = max(
                                float(self.table_scan_click_deadlines.get(scan_sid, 0.0) or 0.0),
                                now_fail + 12.0,
                            )
                    else:
                        for scan_sid in list(self.table_scan_click_deadlines.keys()):
                            self.table_scan_click_deadlines[scan_sid] = min(
                                float(self.table_scan_click_deadlines.get(scan_sid, now_fail + 2.0) or 0.0),
                                now_fail + 2.0,
                            )
                        for probe_tid, probe_row in list(self.table_scan_probe_targets.items()):
                            if str(probe_row.get("table_id_seen") or probe_row.get("table_id") or "") == tid:
                                probe_row["done_at"] = now_fail
                                probe_key = str(probe_row.get("key") or probe_tid)
                                self.table_scan_probe_done.add(probe_key)
                                self.table_scan_probe_fail.add(probe_key)
                self.state.mark_table_attempt(
                    tid,
                    error=f"{type(exc).__name__}: {exc}",
                )
            finally:
                with self.collector_lock:
                    self.collector_inflight.discard(key)

        threading.Thread(
            target=worker,
            name="PragmaticMultiTableCollector",
            daemon=True,
        ).start()
        return True

    def start_manual_api_teach(self):
        """Reset the visible bank and learn table APIs while user opens tables."""
        self.table_scan_enabled = False
        self.table_scan_auto_cycle = False
        self.table_scan_next_cycle = 0.0
        self.table_scan_tab_walk = False
        self.chrome_dga_enabled = False
        try:
            self.dga_feed.stop_collection("API öğren modu")
        except Exception:
            pass
        self._close_table_scan_target()
        self.manual_api_teach = True
        self.manual_api_teach_started = time.time()
        self.collector_seen.clear()
        self.direct_api_seen.clear()
        self.state.clear_table_registry("API öğren başladı")
        with self.state.lock:
            self.state.table_scan_status = (
                "MASA API ÖĞREN: açık • bankayı sıfırladım • "
                "masaları tek tek sen aç, API/tableId kaydedilecek"
            )
        return True

    def start_api_refresh_all(self):
        """Refresh known tableId banks through Pragmatic DGA live websocket.

        Earlier statisticHistory HTTP refreshes returned OK 0 on the user's
        operator because the endpoint is bound to browser/runtime context. The
        public GitHub examples for Pragmatic live roulette use the DGA websocket;
        use that as the primary bank refresh path.
        """
        rows = []
        with self.collector_lock:
            seen_rows = {
                str(k): dict(v or {})
                for k, v in (self.collector_seen or {}).items()
            }
        with self.state.lock:
            registry_rows = {
                str(k): dict(v or {})
                for k, v in (self.state.table_registry or {}).items()
            }
        merged = {}
        merged.update(seen_rows)
        for tid, row in registry_rows.items():
            old = dict(merged.get(tid, {}) or {})
            old.update(row)
            old.setdefault("table_id", tid)
            merged[tid] = old
        for tid, row in merged.items():
            if str(tid).strip():
                rows.append({
                    "table_id": str(tid).strip(),
                    "display_name": str(row.get("display_name") or tid),
                    "last_requested": 0.0,
                })
        rows.sort(key=lambda row: row["display_name"].lower())

        with self.collector_lock:
            self.api_refresh_remaining = []
            self.api_refresh_total = len(rows)
            self.api_refresh_started = time.time()
            self.api_refresh_success = 0
            self.api_refresh_fail = 0
            self.api_refresh_mode = False
            for row in rows:
                tid = str(row.get("table_id") or "")
                if tid:
                    old = self.collector_seen.get(tid, {}) or {}
                    merged_row = dict(old)
                    merged_row.update(row)
                    self.collector_seen[tid] = merged_row

        if not rows:
            with self.state.lock:
                self.state.table_scan_status = "DGA CANLI: kayıtlı masa bankası yok"
            return False

        self.start_dga_live_collection("KAYITLI MASALARI API/DGA YENİLE")
        with self.state.lock:
            self.state.table_scan_status = (
                f"DGA CANLI: {len(rows)} kayıtlı masa aboneliği başladı • "
                "yeni spin geldikçe arşive eklenecek"
            )
        return True

    def _api_refresh_runtime_context(self):
        """Pick a Chrome Runtime context that can fetch Pragmatic games APIs."""
        candidates = []
        sids = []
        if self.active_game_sid:
            sids.append(self.active_game_sid)
        sids.extend([sid for sid in self.session_info.keys() if sid not in sids])
        for sid in sids:
            if self._is_collector_session(sid):
                continue
            if not self.is_direct_probe_target(sid):
                continue
            info = self.session_info.get(sid, {}) or {}
            url = str(info.get("url", "") or "").lower()
            title = str(info.get("title", "") or "").lower()
            base_score = 0
            if sid == self.active_game_sid:
                base_score += 1000
            if "pragmatic" in url or "pragmatic" in title:
                base_score += 100
            if "roulette" in url or "rulet" in url or "roulette" in title or "rulet" in title:
                base_score += 80
            contexts = list((self.execution_contexts.get(sid) or {}).values())
            for ctx in contexts:
                cid = ctx.get("id")
                origin = str(ctx.get("origin") or "").lower()
                if cid is None:
                    continue
                score = base_score
                if "games." in origin:
                    score += 500
                if origin.startswith(("http://", "https://")):
                    score += 20
                candidates.append((score, sid, int(cid)))
            candidates.append((base_score, sid, None))
        if not candidates:
            return None, None
        candidates.sort(key=lambda row: -row[0])
        _score, sid, cid = candidates[0]
        return sid, cid

    def _start_api_refresh_runtime_request(self, row):
        tid = str((row or {}).get("table_id") or "").strip()
        if not tid:
            return False
        sid, context_id = self._api_refresh_runtime_context()
        if not sid:
            return False
        key = ("runtime", tid)
        now = time.time()
        with self.collector_lock:
            if key in self.collector_inflight:
                return False
            self.collector_inflight.add(key)
        self.state.mark_table_attempt(tid)
        params = {
            "expression": build_table_api_history_fetch(tid),
            "returnByValue": True,
            "awaitPromise": True,
        }
        if context_id is not None:
            params["contextId"] = int(context_id)
        self.send(
            "Runtime.evaluate",
            params,
            session_id=sid,
            kind="apirefreshruntime",
            context={
                "table_id": tid,
                "display_name": str((row or {}).get("display_name") or tid),
                "key": key,
                "session": sid,
                "context_id": context_id,
                "started": now,
            },
        )
        return True

    def _collector_tick(self):
        now = time.time()
        with self.collector_lock:
            templates = [
                dict(row) for row in self.auth_templates.values()
                if now - float(row.get("seen", 0.0) or 0.0) <= 900.0
            ]
            candidates = [dict(row) for row in self.collector_seen.values()]
            api_mode = bool(getattr(self, "api_refresh_mode", False))
            api_remaining = list(getattr(self, "api_refresh_remaining", []) or [])
            api_total = int(getattr(self, "api_refresh_total", 0) or 0)
        if not templates:
            return
        templates.sort(key=lambda row: float(row.get("seen", 0.0) or 0.0), reverse=True)
        template = templates[0]
        with self.collector_lock:
            available = COLLECTOR_MAX_CONCURRENT - len(self.collector_inflight)
            inflight_now = len(self.collector_inflight)
            ok_now = int(getattr(self, "api_refresh_success", 0) or 0)
            fail_now = int(getattr(self, "api_refresh_fail", 0) or 0)
        if available <= 0:
            if api_mode:
                with self.state.lock:
                    self.state.table_scan_status = (
                        f"API TOPLA: çalışıyor • OK {ok_now} / HATA {fail_now} • "
                        f"{inflight_now} aktif • {len(api_remaining)} bekliyor"
                    )
            return

        if api_mode:
            dispatched = 0
            kept = []
            for row in api_remaining:
                if available <= 0:
                    kept.append(row)
                    continue
                if self._start_api_refresh_runtime_request(row):
                    available -= 1
                    dispatched += 1
                elif self._start_background_history_request(
                    template,
                    row.get("table_id", ""),
                    row.get("display_name", ""),
                    force=True,
                ):
                    available -= 1
                    dispatched += 1
                else:
                    # If already inflight or no suitable context yet, keep it
                    # queued; the API refresh will continue on the next tick.
                    kept.append(row)
            with self.collector_lock:
                self.api_refresh_remaining = kept
                remaining = len(self.api_refresh_remaining)
                inflight = len(self.collector_inflight)
                ok_now = int(getattr(self, "api_refresh_success", 0) or 0)
                fail_now = int(getattr(self, "api_refresh_fail", 0) or 0)
                if remaining == 0 and inflight == 0:
                    self.api_refresh_mode = False
            done = max(0, api_total - remaining)
            fallback_lobby = bool(remaining == 0 and inflight == 0 and ok_now == 0 and fail_now > 0)
            with self.state.lock:
                if fallback_lobby:
                    self.state.table_scan_status = (
                        f"API TOPLA: OK 0 / HATA {fail_now} • "
                        "lobi sekme toplayıcıya geçiliyor"
                    )
                elif remaining == 0 and inflight == 0:
                    self.state.table_scan_status = (
                        f"API TOPLA: tamamlandı • OK {ok_now} / HATA {fail_now} • "
                        f"{done}/{api_total} masa denendi"
                    )
                else:
                    self.state.table_scan_status = (
                        f"API TOPLA: {done}/{api_total} gönderildi • OK {ok_now} / HATA {fail_now} • "
                        f"{inflight} aktif • {remaining} bekliyor"
                    )
            if fallback_lobby:
                self.start_table_scan(auto_cycle=True)
            return

        if getattr(self, "table_scan_tab_walk", False):
            return

        candidates.sort(key=lambda row: float(row.get("last_requested", 0.0) or 0.0))
        for row in candidates:
            if available <= 0:
                break
            if self._start_background_history_request(
                template,
                row.get("table_id", ""),
                row.get("display_name", ""),
            ):
                available -= 1

    def _start_direct_history_request(self, template, session_id="", title=""):
        if not isinstance(template, dict):
            return

        table_id = str(template.get("table_id") or "")
        jsession = str(template.get("session_id") or "")
        scheme = str(template.get("scheme") or "https")
        netloc = str(template.get("netloc") or "")
        if not table_id or not jsession or not netloc:
            return

        key = (netloc, table_id)
        now = time.time()
        last = float(self.direct_api_seen.get(key, 0.0) or 0.0)
        if now - last < 12.0 or key in self.direct_api_inflight:
            return

        self.direct_api_seen[key] = now
        self.direct_api_inflight.add(key)

        def worker():
            try:
                query = urllib.parse.urlencode({
                    "JSESSIONID": jsession,
                    "numberOfGames": "500",
                    "tableId": table_id,
                })
                history_url = (
                    f"{scheme}://{netloc}/api/ui/statisticHistory?{query}"
                )

                req = urllib.request.Request(
                    history_url,
                    headers={
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/153 Safari/537.36"
                        ),
                        "Accept": "application/json,text/plain,*/*",
                        "Cache-Control": "no-cache",
                    },
                )
                with urllib.request.urlopen(req, timeout=8.0) as r:
                    body = r.read(3_000_000)

                nums = extract_statistic_history(body)
                if len(nums) >= 20:
                    fallback_title = title
                    if not fallback_title and table_id == self.state.pragmatic_table_id:
                        fallback_title = self.state.table_name
                    self.state.update_direct_pragmatic_history(
                        nums,
                        table_id=table_id,
                        operator_game_id=self.state.pragmatic_operator_game_id,
                        theme_code=self.state.pragmatic_theme_code,
                        title=fallback_title,
                        source="PRAGMATIC statisticHistory network-template",
                    )
                    with self.state.lock:
                        self.state.direct_history_status += " • NETWORK"
                else:
                    with self.state.lock:
                        if int(self.state.direct_history_count or 0) < 20:
                            if len(self.state.table_history_500) >= 20:
                                self.state.direct_history_status = (
                                    "PRAGMATIC DIRECT: API bağlı • cevap şeması farklı • "
                                    f"DOM SON500 {len(self.state.table_history_500)}/500 kullanılıyor"
                                )
                            else:
                                self.state.direct_history_status = (
                                    "PRAGMATIC DIRECT: statisticHistory cevap verdi "
                                    f"ama sonuç ayrıştırılamadı ({len(nums)})"
                                )
            except Exception as e:
                with self.state.lock:
                    if int(self.state.direct_history_count or 0) < 20:
                        self.state.direct_history_status = (
                            "PRAGMATIC DIRECT: network-template başarısız "
                            f"({type(e).__name__})"
                        )
            finally:
                self.direct_api_inflight.discard(key)

        threading.Thread(
            target=worker,
            name="PragmaticDirectHistory",
            daemon=True,
        ).start()

    def handle_direct_body(self, obj, context=None):
        try:
            result=obj.get("result",{})
            body=result.get("body","")
            if result.get("base64Encoded"):
                body=base64.b64decode(body).decode("utf-8",errors="ignore")
            meta=context if isinstance(context,dict) else {}
            table_id = str(meta.get("table_id","") or "")
            sid_ctx = str(meta.get("session","") or "")
            nums=extract_statistic_history(body)

            if (sid_ctx and self._is_collector_session(sid_ctx)) or bool(meta.get("collector")):
                if table_id:
                    self.table_scan_found_ids.add(table_id)
                if self.table_scan_tab_walk and not self.table_scan_click_deadlines:
                    return
                if table_id and len(nums) >= 20:
                    display_name = self._clean_collector_label(
                        str(
                            self.table_scan_current_click_label
                            or self.table_scan_last_clicked_label
                            or meta.get("title")
                            or table_id
                        ),
                        fallback=table_id,
                    )
                    self._mark_current_scan_card_done(
                        table_id=table_id,
                        label=display_name,
                        theme_code=str(meta.get("theme_code") or ""),
                    )
                    self.state.store_background_table_history(
                        nums,
                        table_id=table_id,
                        display_name=display_name,
                        source_label="SEKMELİ TOPLA statisticHistory network",
                    )
                    self.state.mark_table_attempt(table_id, ok=True)
                    now_done = time.time()
                    self._schedule_collector_return(sid_ctx, 0.25)
                    probe_tid = self._target_id_for_session(sid_ctx)
                    if probe_tid in self.table_scan_probe_targets:
                        row = self.table_scan_probe_targets[probe_tid]
                        row["done_at"] = now_done
                        row["table_id_seen"] = table_id
                        key = str(row.get("key") or probe_tid)
                    else:
                        key = str(self.table_scan_current_click_key or sid_ctx)
                    self.table_scan_probe_done.add(key)
                    self.table_scan_probe_success.add(key)
                    with self.state.lock:
                        prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
                        self.state.table_scan_status = (
                            f"{prefix}: NETWORK SON500 kaydedildi • {display_name[:44]} • {len(nums)}/500 • minimum bekleme sonrası lobiye dönülecek"
                        )
                elif table_id and self.table_scan_tab_walk:
                    self._mark_current_scan_card_done(
                        table_id=table_id,
                        theme_code=str(meta.get("theme_code") or ""),
                    )
                    with self.state.lock:
                        self.state.table_scan_status = (
                            f"SEKMELİ TOPLA: network cevap var ama SON500 ayrıştırılamadı ({len(nums)}) • bekleniyor"
                        )
                return

            if (
                self.active_table_id
                and table_id
                and table_id != self.active_table_id
            ):
                return
            self.state.update_direct_pragmatic_history(
                nums,
                table_id=meta.get("table_id",""),
                operator_game_id=meta.get("operator_game_id",""),
                theme_code=meta.get("theme_code",""),
                title=meta.get("title",""),
                source="PRAGMATIC statisticHistory network",
            )
        except Exception:
            pass

    def handle_direct_runtime(self, obj, context=None):
        try:
            value=obj.get("result",{}).get("result",{}).get("value")
            if not isinstance(value,dict):
                return

            ctx_meta = context if isinstance(context,dict) else {}
            ctx_name = str(ctx_meta.get("name","") or "")
            ctx_origin = str(ctx_meta.get("origin","") or "")

            table_id=str(value.get("tableId") or "")
            operator_game_id=str(value.get("operatorGameId") or "")
            theme_code=str(value.get("themeCode") or "")
            title=str(value.get("title") or "")
            sid_ctx = str(ctx_meta.get("session","") or "")

            if sid_ctx and self._is_collector_session(sid_ctx):
                if self.table_scan_tab_walk and not self.table_scan_click_deadlines:
                    return
                if table_id:
                    self.table_scan_found_ids.add(table_id)
                if value.get("ok") and value.get("body") and table_id:
                    nums = extract_statistic_history(value.get("body"))
                    if len(nums) >= 20:
                        display_name = self._clean_collector_label(
                            self.table_scan_current_click_label
                            or self.table_scan_last_clicked_label
                            or title
                            or table_id,
                            fallback=table_id,
                        )
                        self._mark_current_scan_card_done(
                            table_id=table_id,
                            label=display_name,
                            theme_code=theme_code,
                        )
                        self.state.store_background_table_history(
                            nums,
                            table_id=table_id,
                            display_name=display_name,
                            source_label="SEKMELİ TOPLA statisticHistory",
                        )
                        self.state.mark_table_attempt(table_id, ok=True)
                        now_done = time.time()
                        self._schedule_collector_return(sid_ctx, 0.25)
                        probe_tid = self._target_id_for_session(sid_ctx)
                        if probe_tid in self.table_scan_probe_targets:
                            row = self.table_scan_probe_targets[probe_tid]
                            row["done_at"] = now_done
                            key = str(row.get("key") or probe_tid)
                        else:
                            key = str(self.table_scan_current_click_key or sid_ctx)
                        self.table_scan_probe_done.add(key)
                        self.table_scan_probe_success.add(key)
                        with self.state.lock:
                            prefix = "SEKMELİ TOPLA" if self.table_scan_tab_walk else "MASA TARAMA"
                            self.state.table_scan_status = (
                                f"{prefix}: runtime SON500 kaydedildi • {display_name[:44]} • {len(nums)}/500 • minimum bekleme sonrası lobiye dönülecek"
                            )
                    elif table_id:
                        # tableId arrived but usable SON500/statisticHistory has not
                        # arrived yet. In sekmeli mode do NOT close early; the
                        # tab stays open until real data or timeout.
                        if self.table_scan_tab_walk:
                            self.table_scan_click_deadlines[sid_ctx] = max(
                                float(self.table_scan_click_deadlines.get(sid_ctx, 0.0) or 0.0),
                                time.time() + 12.0,
                            )
                            with self.state.lock:
                                self.state.table_scan_status = (
                                    f"SEKMELİ TOPLA: tableId {table_id} • veri henüz yok • bekleniyor"
                                )
                        else:
                            self.table_scan_click_deadlines[sid_ctx] = min(
                                float(self.table_scan_click_deadlines.get(sid_ctx, time.time() + 2.0) or 0.0),
                                time.time() + 2.0,
                            )
                return

            if table_id:
                if self.active_table_id and table_id != self.active_table_id:
                    return
                self.state.set_pragmatic_identity(
                    table_id,
                    str(self.session_operator_game.get(sid_ctx,"") or operator_game_id),
                    str(self.session_theme.get(sid_ctx,"") or theme_code),
                    title,
                )

            if value.get("ok") and value.get("body"):
                nums=extract_statistic_history(value.get("body"))
                self.state.update_direct_pragmatic_history(
                    nums,table_id,operator_game_id,theme_code,title,
                    source="PRAGMATIC statisticHistory direct fetch",
                )
                if len(nums) >= 20:
                    with self.state.lock:
                        ctx_label = (
                            ctx_name
                            or ctx_origin.replace("https://","").replace("http://","")
                            or "execution-context"
                        )
                        if len(ctx_label) > 42:
                            ctx_label = ctx_label[:39] + "..."
                        self.state.direct_history_status += (
                            f" • ctx {ctx_label}"
                        )
            else:
                with self.state.lock:
                    # Multiple page/iframe targets are probed. A frame that has
                    # no endpoint must not overwrite a successful 500-result state.
                    if (
                        int(self.state.direct_history_count or 0) < 20
                        and table_id
                        and not self.direct_api_inflight
                    ):
                        reason = str(
                            value.get("reason")
                            or f"HTTP {value.get('status','-')}"
                        )
                        ctx_label = (
                            ctx_name
                            or ctx_origin.replace("https://","").replace("http://","")
                            or "context"
                        )
                        if len(ctx_label) > 34:
                            ctx_label = ctx_label[:31] + "..."
                        self.state.direct_history_status = (
                            f"PRAGMATIC DIRECT: {reason} • ctx {ctx_label}"
                        )
        except Exception:
            pass

    def handle_body(self, obj, context=None):
        try:
            result = obj.get("result",{})
            body = result.get("body","")
            if not body or len(body) > 1_500_000:
                return
            if result.get("base64Encoded"):
                body = base64.b64decode(body).decode("utf-8",errors="ignore")
            if not body or len(body) > 1_200_000:
                return

            meta = context if isinstance(context, dict) else {}
            discovered = extract_pragmatic_roulette_tables(body)
            if discovered and not self.manual_api_teach:
                source_url = urllib.parse.urlsplit(str(meta.get("url") or ""))
                source_label = (
                    f"{source_url.scheme}://{source_url.netloc}{source_url.path}"
                    if source_url.scheme and source_url.netloc
                    else "PRAGMATIC LOBI"
                )
                self._register_discovered_tables(
                    discovered,
                    source=source_label[:140],
                )

            # V2.9.33: while the single-tab collector is inside a real table,
            # accept generic network history only from history/stat/result-like
            # endpoints. Do not treat lobby/game-list JSON as a table success;
            # that made the tab leave the table too quickly.
            collector_sid = str(meta.get("session") or "")
            if self._is_collector_session(collector_sid):
                if self.table_scan_tab_walk and self.table_scan_click_deadlines:
                    source_url = str(meta.get("url") or "")
                    low_url = source_url.lower()
                    historyish = any(x in low_url for x in (
                        "statistic", "history", "recent", "result", "round",
                        "shoe", "roadmap", "statistics"
                    ))
                    if historyish:
                        nums = extract_statistic_history(body)
                        if len(nums) >= 20:
                            try:
                                u = urllib.parse.urlsplit(source_url)
                                qs = urllib.parse.parse_qs(u.query)
                                real_tid = str((qs.get("tableId") or [""])[0] or "")
                            except Exception:
                                real_tid = ""
                            if not real_tid:
                                real_tid = str(
                                    (self.session_table_activity.get(collector_sid, {}) or {}).get("table_id", "")
                                    or ""
                                )
                            table_id, display_name = self._collector_table_identity(
                                collector_sid,
                                real_table_id=real_tid,
                                title=str(self.table_scan_last_clicked_label or ""),
                            )
                            self._mark_current_scan_card_done(
                                table_id=table_id,
                                label=display_name,
                            )
                            self.state.store_background_table_history(
                                nums,
                                table_id=table_id,
                                display_name=display_name,
                                source_label="SEKMELİ TOPLA genel network SON500",
                            )
                            self.state.mark_table_attempt(table_id, ok=True)
                            now_done = time.time()
                            self._schedule_collector_return(collector_sid, 0.8)
                            key = str(self.table_scan_current_click_key or table_id)
                            self.table_scan_probe_done.add(key)
                            self.table_scan_probe_success.add(key)
                            with self.state.lock:
                                self.state.table_scan_status = (
                                    f"SEKMELİ TOPLA: genel network SON500 kaydedildi • {display_name[:44]} • {len(nums)}/500 • panel bekleme tamamlanınca lobiye dönülecek"
                                )
                return

            if "last20Results" not in body:
                return

            parsed = None
            try:
                parsed = json.loads(body)
            except Exception:
                # Some endpoints wrap JSON in text/javascript.
                m = re.search(r'(\{.*"last20Results".*\})', body, re.S)
                if m:
                    try:
                        parsed = json.loads(m.group(1))
                    except Exception:
                        parsed = None

            if parsed is None:
                return

            found = find_last20(parsed)
            if found:
                self.state.update_results(
                    found["results"],
                    found["hot"],
                    found["cold"],
                    found["table"],
                    source="Pragmatic API"
                )
        except Exception:
            pass

    def handle(self, obj):
        if "id" in obj:
            kind, context = self.pending.pop(obj["id"], (None,None))

            if kind == "targets":
                for ti in obj.get("targetInfos",[]) if "targetInfos" in obj else obj.get("result",{}).get("targetInfos",[]):
                    self.attach_target(ti)

            elif kind == "collectorcreate":
                tid = str(obj.get("result", {}).get("targetId", "") or "")
                if tid and self.table_scan_enabled:
                    self.table_scan_target_id = tid
                    known_tids = getattr(self, "collector_known_target_ids", None)
                    if known_tids is None:
                        known_tids = set()
                        self.collector_known_target_ids = known_tids
                    known_tids.add(tid)
                    ti = self.target_info.get(tid)
                    if ti:
                        self.attach_target(ti)
                    with self.state.lock:
                        self.state.table_scan_status = (
                            "MASA TARAMA: arka plan sekmesi hazır • Pragmatic lobi bekleniyor"
                        )
                else:
                    self.table_scan_enabled = False
                    with self.state.lock:
                        self.state.table_scan_status = (
                            "MASA TARAMA: arka plan sekmesi açılamadı"
                        )

            elif kind == "collectorprobecreate":
                tid = str(obj.get("result", {}).get("targetId", "") or "")
                meta = context if isinstance(context, dict) else {}
                if tid and self.table_scan_enabled:
                    row = dict(meta)
                    row["opened"] = time.time()
                    self.table_scan_probe_targets[tid] = row
                    url = str(row.get("url") or "")
                    if url:
                        self.table_scan_probe_urls.add(url)
                    ti = self.target_info.get(tid)
                    if ti:
                        self.attach_target(ti)
                else:
                    url = str(meta.get("url") or "")
                    if url:
                        self.table_scan_probe_urls.discard(url)

            elif kind == "attach":
                tid = context
                self.attaching.discard(tid)
                sid = obj.get("result",{}).get("sessionId")
                if sid:
                    self.target_sessions[tid] = sid
                    self.session_targets[sid] = tid
                    self.session_info[sid] = dict(self.target_info.get(tid,{}))
                    self.enable_session(sid)

            elif kind == "body":
                self.handle_body(obj, context)

            elif kind == "directbody":
                self.handle_direct_body(obj, context)

            elif kind == "directhistory":
                self.handle_direct_runtime(obj, context)

            elif kind == "chromedgastart":
                self._handle_chrome_dga_runtime(obj, context, started=True)

            elif kind == "chromedgapoll":
                self._handle_chrome_dga_runtime(obj, context, started=False)

            elif kind == "chromedgastop":
                pass

            elif kind == "apirefreshruntime":
                meta = context if isinstance(context, dict) else {}
                tid = str(meta.get("table_id") or "")
                key = meta.get("key") or ("runtime", tid)
                ok = False
                err = ""
                try:
                    value = obj.get("result", {}).get("result", {}).get("value")
                    if not isinstance(value, dict):
                        err = "runtime cevap yok"
                    elif value.get("ok") and value.get("body"):
                        nums = extract_statistic_history(value.get("body"))
                        if len(nums) >= 20:
                            self.state.store_background_table_history(
                                nums,
                                table_id=tid or value.get("tableId", ""),
                                display_name=str(meta.get("display_name") or value.get("title") or tid),
                                source_label="API REFRESH runtime fetch",
                            )
                            self.state.mark_table_attempt(tid, ok=True)
                            ok = True
                        else:
                            err = f"sonuç ayrıştırılamadı ({len(nums)})"
                    else:
                        err = str(
                            (value or {}).get("reason")
                            or f"HTTP {(value or {}).get('status','-')}"
                        )
                except Exception as exc:
                    err = f"{type(exc).__name__}: {exc}"
                finally:
                    with self.collector_lock:
                        self.collector_inflight.discard(key)
                        if ok:
                            self.api_refresh_success = int(getattr(self, "api_refresh_success", 0) or 0) + 1
                        else:
                            self.api_refresh_fail = int(getattr(self, "api_refresh_fail", 0) or 0) + 1
                    if not ok and tid:
                        self.state.mark_table_attempt(tid, error=err[:160])

            elif kind == "lobbyteach": 
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    self._handle_lobby_teach(str(context or ""), value)
                except Exception:
                    pass

            elif kind == "lobbylearned":
                try:
                    result = obj.get("result",{}) or {}
                    exc = result.get("exceptionDetails") or {}
                    if exc:
                        desc = str(exc.get("text") or "")
                        ex = exc.get("exception") or {}
                        if isinstance(ex,dict):
                            desc = str(ex.get("description") or desc)
                        with self.state.lock:
                            self.state.autolobby_status = (
                                "ÖĞREN: REPLAY JS HATASI • "
                                + desc.replace("\n"," ")[:90]
                            )
                    else:
                        value = result.get("result",{}).get("value")
                        self._handle_lobby_nav(str(context or ""), value)
                except Exception:
                    pass

            elif kind == "lobbynav":
                # Legacy V2.9.4 response handler retained only for compatibility.
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    self._handle_lobby_nav(str(context or ""), value)
                except Exception:
                    pass

            elif kind == "recoveryscan":
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    self._handle_recovery_scan(str(context or ""), value)
                except Exception:
                    pass

            elif kind == "collectornavscan":
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    self._handle_table_nav_scan(context, value)
                except Exception:
                    pass

            elif kind == "collectorback":
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    if isinstance(value, dict):
                        stage = str(value.get("stage") or "")
                        clicked = bool(value.get("clicked"))
                        if clicked:
                            now_back = time.time()
                            self.table_scan_last_view = now_back
                            if self.table_scan_tab_walk:
                                self.table_scan_returning_until = max(
                                    float(getattr(self, "table_scan_returning_until", 0.0) or 0.0),
                                    now_back + TAB_WALK_RETURN_GRACE_SECONDS,
                                )
                                for scan_sid in list(self.session_info.keys()):
                                    if self._is_collector_session(scan_sid):
                                        self.table_scan_click_deadlines.pop(scan_sid, None)
                                        self.table_scan_click_started_at.pop(scan_sid, None)
                                        self.session_table_activity.pop(scan_sid, None)
                            with self.state.lock:
                                self.state.table_scan_status = (
                                    "SEKMELİ TOPLA: oyun içi Lobi düğmesi tıklandı • Pragmatic Rulet lobisi bekleniyor"
                                )
                        elif stage == "lobby-button-not-found":
                            with self.state.lock:
                                if "Lobi düğmesine basılıyor" in str(self.state.table_scan_status):
                                    self.state.table_scan_status = (
                                        "SEKMELİ TOPLA: oyun içi Lobi düğmesi aranıyor • arama sayfasına dönülmeyecek"
                                    )
                except Exception:
                    pass

            elif kind == "visibility":
                try:
                    value = obj.get("result",{}).get("result",{}).get("value")
                    sid_ctx = context if isinstance(context,str) else ""
                    if sid_ctx and isinstance(value,dict):
                        href_val = str(value.get("href","") or "")
                        title_val = str(value.get("title","") or "")
                        self.session_visibility[sid_ctx] = {
                            "visibility": str(value.get("visibility","") or ""),
                            "focus": bool(value.get("focus",False)),
                            "href": href_val,
                            "title": title_val,
                            "time": time.time(),
                        }
                        if href_val and not self._is_collector_session(sid_ctx):
                            tid_ctx = self.session_targets.get(sid_ctx, "")
                            self.save_roulette_url({
                                "targetId": tid_ctx,
                                "type": "page",
                                "url": href_val,
                                "title": title_val,
                            })
                        self._select_active_table()
                except Exception:
                    pass

            elif kind == "domscan":
                try:
                    sid_ctx = (
                        str(context.get("session") or "")
                        if isinstance(context, dict)
                        else (context if isinstance(context, str) else "")
                    )
                    if sid_ctx and not self._is_active_session(sid_ctx):
                        return

                    value = obj.get("result",{}).get("result",{}).get("value")
                    if isinstance(value,dict):
                        if value.get("lobbyLike"):
                            if not self._recent_active_game():
                                with self.state.lock:
                                    if self.state.history:
                                        self.state.status = "LOBİ AÇIK • masa seçilmesi bekleniyor"
                            return
                        title = value.get("title","")

                        with self.state.lock:
                            current_hist = list(self.state.history[:20])

                        chosen = choose_live_dom_candidate(
                            value.get("candidates",[]),
                            current_hist,
                        )

                        if chosen and len(chosen.get("nums",[])) >= 5:
                            if sid_ctx and sid_ctx in self.session_table_activity:
                                self.session_table_activity[sid_ctx]["last"] = time.time()
                            relation = str(chosen.get("relation",""))
                            new_count = int(chosen.get("new_count",0) or 0)

                            src = "DOM canlı kilitli"
                            if relation == "ahead" and new_count:
                                src = f"DOM canlı kilitli +{new_count}"
                            elif relation == "resync":
                                src = "DOM canlı kilitli resync"

                            self.state.update_results(
                                chosen["nums"],
                                table_name=title,
                                source=src,
                            )

                        self._handle_live_result_candidates(
                            sid_ctx,
                            value.get("liveCandidates", []),
                        )
                except Exception:
                    pass

            elif kind == "background500":
                try:
                    meta = context if isinstance(context,dict) else {}
                    value = obj.get("result",{}).get("result",{}).get("value")
                    if isinstance(value,dict):
                        nums = value.get("nums",[])
                        title = (
                            value.get("title","")
                            or meta.get("title","")
                        )
                        raw_table_id = str(meta.get("table_id","") or "")
                        is_collector = bool(meta.get("collector"))
                        panel_seen = bool(
                            value.get("foundTab")
                            or str(value.get("source") or "") == "son500-tab"
                        )
                        sid_meta = str(meta.get("session") or "")
                        table_id, display_name = self._collector_table_identity(
                            sid_meta,
                            real_table_id=str(meta.get("real_table_id") or raw_table_id),
                            title=title,
                        ) if is_collector else (raw_table_id, title)
                        now_value = time.time()
                        returning_to_lobby = bool(
                            is_collector
                            and self.table_scan_tab_walk
                            and float(getattr(self, "table_scan_returning_until", 0.0) or 0.0) > now_value
                        )
                        recent_lobby_visible = bool(
                            is_collector
                            and self.table_scan_tab_walk
                            and not self.table_scan_current_click_key
                            and float(getattr(self, "table_scan_lobby_seen_at", 0.0) or 0.0)
                            and now_value - float(getattr(self, "table_scan_lobby_seen_at", 0.0) or 0.0) <= 30.0
                        )
                        if (returning_to_lobby or recent_lobby_visible) and not bool(value.get("lobbyLike")):
                            return
                        blocked_or_no_son500 = bool(
                            is_collector
                            and self.table_scan_tab_walk
                            and self.table_scan_click_deadlines
                            and not bool(value.get("lobbyLike"))
                            and int(value.get("lobbyCardCount", 0) or 0) < 2
                            and (
                                value.get("blockedTable")
                                or value.get("gameNoSon500")
                                or value.get("hotColdOnly")
                                or self._is_blocked_table_label(display_name)
                                or self._is_blocked_table_label(self.table_scan_current_click_label)
                                or self._is_blocked_table_label(self.table_scan_last_clicked_label)
                            )
                        )
                        if blocked_or_no_son500:
                            self._mark_current_scan_card_done(
                                table_id=table_id,
                                label=display_name,
                            )
                            key = str(self.table_scan_current_click_key or table_id or sid_meta)
                            if key:
                                self.table_scan_probe_done.add(key)
                                self.table_scan_probe_skip.add(key)
                            return_sid = (
                                sid_meta
                                or next(iter(self.table_scan_click_deadlines.keys()), "")
                                or self._collector_root_session()
                            )
                            reason = "bloklu masa" if (
                                value.get("blockedTable")
                                or self._is_blocked_table_label(display_name)
                                or self._is_blocked_table_label(self.table_scan_current_click_label)
                                or self._is_blocked_table_label(self.table_scan_last_clicked_label)
                            ) else "SON500 paneli yok"
                            with self.state.lock:
                                self.state.table_scan_status = (
                                    f"SEKMELİ TOPLA: {reason} • {display_name[:44]} • anında es geçiliyor"
                                )
                            self._return_collector_to_lobby(return_sid, f"{reason} • es geçildi")
                            self.table_scan_current_click_key = ""
                            self.table_scan_current_click_label = ""
                            return
                        wait_started_at = max(
                            [float(x or 0.0) for x in self.table_scan_click_started_at.values()] or [0.0]
                        )
                        if (
                            is_collector
                            and bool(value.get("lobbyLike"))
                            and (returning_to_lobby or not wait_started_at or (now_value - wait_started_at) >= 2.4)
                        ):
                            if returning_to_lobby:
                                self.table_scan_lobby_settle_until = time.time() + 0.32
                            self.table_scan_returning_until = 0.0
                            self.table_scan_lobby_seen_at = time.time()
                            for scan_sid in list(self.session_info.keys()):
                                if self._is_collector_session(scan_sid):
                                    self.table_scan_click_deadlines.pop(scan_sid, None)
                                    self.table_scan_click_started_at.pop(scan_sid, None)
                                    self.session_table_activity.pop(scan_sid, None)
                            self.table_scan_current_click_key = ""
                            self.table_scan_current_click_label = ""
                            with self.state.lock:
                                self.state.table_scan_status = (
                                    f"SEKMELİ TOPLA: Pragmatic Rulet lobisine dönüldü • {int(value.get('lobbyCardCount',0) or 0)} kart • sıradaki masa seçiliyor"
                                )
                            return
                        if (
                            is_collector
                            and self.table_scan_tab_walk
                            and not self.table_scan_click_deadlines
                            and not (
                                panel_seen
                                or value.get("gameNoSon500")
                                or value.get("blockedTable")
                                or value.get("hotColdOnly")
                                or value.get("foundTab")
                            )
                        ):
                            return
                        if len(nums) >= 40 and table_id and panel_seen:
                            if not is_collector:
                                return
                            self._mark_current_scan_card_done(
                                table_id=table_id,
                                label=display_name,
                            )
                            source_label = "SEKMELİ TOPLA sağ-alt SON500 paneli"
                            self.state.store_background_table_history(
                                nums,
                                table_id=table_id,
                                display_name=display_name,
                                source_label=source_label,
                            )
                            self.state.mark_table_attempt(table_id, ok=True)
                            if is_collector:
                                sid_ctx = str(meta.get("session") or "")
                                now_done = time.time()
                                if sid_ctx:
                                    self._schedule_collector_return(sid_ctx, 0.25)
                                key = str(self.table_scan_current_click_key or table_id)
                                self.table_scan_probe_done.add(key)
                                self.table_scan_probe_success.add(key)
                                with self.state.lock:
                                    self.state.table_scan_status = (
                                        f"SEKMELİ TOPLA: sağ-alt SON500 paneli kaydedildi • {display_name[:44]} • {len(nums)}/500 • minimum bekleme sonrası lobiye dönülecek"
                                    )
                        elif is_collector and table_id:
                            now_wait = time.time()
                            started = 0.0
                            if sid_meta:
                                started = float(self.table_scan_click_started_at.get(sid_meta, 0.0) or 0.0)
                            if not started:
                                for v in self.table_scan_click_started_at.values():
                                    try:
                                        started = max(started, float(v or 0.0))
                                    except Exception:
                                        pass
                            elapsed = max(0.0, now_wait - started) if started else 0.0
                            has_son500_tab = bool(value.get("foundTab") or str(value.get("source") or "") == "son500-tab")
                            active_game_ui = bool(value.get("activeGameUi"))
                            skip_no_panel = elapsed >= TAB_WALK_NO_SON500_SKIP_SECONDS and active_game_ui and not has_son500_tab
                            skip_empty_panel = elapsed >= TAB_WALK_EMPTY_SON500_SKIP_SECONDS and has_son500_tab and len(nums) < 40
                            if skip_no_panel or skip_empty_panel:
                                self._mark_current_scan_card_done(
                                    table_id=table_id,
                                    label=display_name,
                                )
                                key = str(self.table_scan_current_click_key or table_id)
                                self.table_scan_probe_done.add(key)
                                self.table_scan_probe_skip.add(key)
                                return_sid = (
                                    sid_meta
                                    or next(iter(self.table_scan_click_deadlines.keys()), "")
                                    or self._collector_root_session()
                                )
                                with self.state.lock:
                                    self.state.table_scan_status = (
                                        f"SEKMELİ TOPLA: SON500 yok • {display_name[:44]} • es geçiliyor"
                                    )
                                # V2.9.37: do not merely schedule this return;
                                # repeated DOM scans could keep refreshing the
                                # due time and leave the UI stuck at
                                # "es geçiliyor". Clear the wait and click the
                                # in-game Lobby button immediately.
                                self._return_collector_to_lobby(
                                    return_sid,
                                    "SON500 yok • es geçildi",
                                )
                                self.table_scan_current_click_key = ""
                                self.table_scan_current_click_label = ""
                            else:
                                with self.state.lock:
                                    if has_son500_tab:
                                        panel_text = "SON500 paneli görüldü"
                                    elif panel_seen:
                                        panel_text = "masa paneli var, SON500 aranıyor"
                                    else:
                                        panel_text = "masa paneli bekleniyor"
                                    self.state.table_scan_status = (
                                        f"SEKMELİ TOPLA: sağ-alt SON500 okunuyor • {display_name[:44]} • {panel_text} • bulunan {len(nums)}"
                                    )
                except Exception:
                    pass

            elif kind == "history500":
                try:
                    sid_ctx = (
                        str(context.get("session") or "")
                        if isinstance(context, dict)
                        else (context if isinstance(context, str) else "")
                    )
                    if sid_ctx and not self._is_active_session(sid_ctx):
                        return
                    value = obj.get("result",{}).get("result",{}).get("value")
                    if isinstance(value,dict):
                        if value.get("lobbyLike"):
                            return
                        nums = value.get("nums",[])
                        title = value.get("title","")
                        if len(nums) >= 40 and bool(value.get("foundTab")):
                            if sid_ctx and sid_ctx in self.session_table_activity:
                                self.session_table_activity[sid_ctx]["last"] = time.time()
                            self.state.update_table_history_500(
                                nums,
                                table_name=title
                            )
                except Exception:
                    pass
            return

        method = obj.get("method","")
        params = obj.get("params",{})
        sid = obj.get("sessionId")

        if method == "Runtime.executionContextCreated":
            try:
                ctx = params.get("context", {}) or {}
                cid = ctx.get("id")
                if sid and cid is not None:
                    self.execution_contexts.setdefault(sid, {})[int(cid)] = {
                        "id": int(cid),
                        "origin": str(ctx.get("origin", "") or ""),
                        "name": str(ctx.get("name", "") or ""),
                        "auxData": ctx.get("auxData", {}) or {},
                    }
            except Exception:
                pass
            return

        if method == "Runtime.executionContextDestroyed":
            try:
                cid = int(params.get("executionContextId"))
                if sid in self.execution_contexts:
                    self.execution_contexts[sid].pop(cid, None)
            except Exception:
                pass
            return

        if method == "Runtime.executionContextsCleared":
            if sid:
                self.execution_contexts[sid] = {}
            return

        if method == "Inspector.targetCrashed":
            return

        if method == "Target.targetCreated":
            self.attach_target(params.get("targetInfo",{}))
            return

        if method == "Target.targetInfoChanged":
            ti = params.get("targetInfo",{})
            tid = ti.get("targetId")
            if tid:
                self.target_info[tid] = dict(ti)
                self.save_roulette_url(ti)
                known = self.target_sessions.get(tid)
                if known:
                    self.session_info[known] = dict(ti)
            return

        if method == "Target.attachedToTarget":
            child_sid = params.get("sessionId")
            parent_sid = obj.get("sessionId")
            ti = params.get("targetInfo",{})
            tid = ti.get("targetId")
            if tid and child_sid:
                parent_tid = self.session_targets.get(str(parent_sid or ""), "")
                if parent_tid:
                    self.target_parent[tid] = parent_tid
                elif (
                    str(ti.get("type") or "") == "iframe"
                    and self.table_scan_enabled
                    and self.table_scan_target_id
                    and tid not in self.target_parent
                ):
                    self.target_parent[tid] = str(self.table_scan_target_id)
                self.target_info[tid] = dict(ti)
                self.target_sessions[tid] = child_sid
                self.session_targets[child_sid] = tid
                self.session_info[child_sid] = dict(ti)
                self.attaching.discard(tid)
                self.save_roulette_url(ti)
                self.enable_session(child_sid)
            return

        if method == "Target.detachedFromTarget":
            try:
                child_sid = params.get("sessionId")
                if child_sid:
                    self.execution_contexts.pop(child_sid, None)
                    self.session_visibility.pop(child_sid, None)
                    self.session_table_activity.pop(child_sid, None)
                    self.session_theme.pop(child_sid, None)
                    self.session_operator_game.pop(child_sid, None)
                    self.session_info.pop(child_sid, None)
                    if child_sid == self.active_game_sid:
                        self.active_game_sid = ""
                        self.active_table_id = ""
                        self._select_active_table()
                    dead = [
                        tid for tid, sess in self.target_sessions.items()
                        if sess == child_sid
                    ]
                    for tid in dead:
                        self.target_sessions.pop(tid, None)
                        self.target_parent.pop(tid, None)
                        probe_row = self.table_scan_probe_targets.pop(tid, None)
                        if probe_row:
                            probe_url = str(probe_row.get("url") or "")
                            if probe_url:
                                self.table_scan_probe_urls.discard(probe_url)
                    self.session_targets.pop(child_sid, None)
            except Exception:
                pass
            return

        if method == "Network.webSocketCreated":
            try:
                url = str(params.get("url", "") or "")
                if "dga." in url.lower() and "pragmatic" in url.lower():
                    self._record_dga_config(ws_url=url, source="Chrome websocket created")
            except Exception:
                pass
            return

        if method in ("Network.webSocketFrameSent", "Network.webSocketFrameReceived"):
            try:
                response = params.get("response", {}) or {}
                payload = str(response.get("payloadData", "") or "")
                self._handle_dga_ws_payload(
                    payload,
                    sid=sid,
                    direction="sent" if method.endswith("Sent") else "received",
                )
            except Exception:
                pass
            return

        if method == "Network.requestWillBeSent":
            try:
                req_obj = params.get("request", {}) or {}
                url = str(req_obj.get("url", "") or "")

                self._record_theme_and_game_meta(sid, url)
                self._auth_template_from_url(url, sid)

                template = self._direct_template_from_url(url)
                if template:
                    self._note_table_activity(sid, template, url)

                    if self._is_active_session(sid):
                        table_id = str(template.get("table_id") or "")
                        if table_id and table_id == self.active_table_id:
                            self.state.set_pragmatic_identity(
                                table_id=table_id,
                                operator_game_id=str(
                                    self.session_operator_game.get(sid, "")
                                ),
                                theme_code=str(
                                    self.session_theme.get(sid, "")
                                ),
                                title=str(
                                    self.session_info.get(sid, {}).get("title", "")
                                ),
                            )
                            self._start_direct_history_request(
                                template,
                                session_id=sid,
                                title=str(
                                    self.session_info.get(sid, {}).get("title", "")
                                ),
                            )
            except Exception:
                pass

        if method == "Network.responseReceived":
            try:
                req = params.get("requestId")
                response = params.get("response",{})
                url = str(response.get("url",""))
                mime = str(response.get("mimeType","")).lower()
                low = url.lower()

                self._record_theme_and_game_meta(sid, url)
                self._auth_template_from_url(url, sid)

                direct_template = self._direct_template_from_url(url)
                if direct_template:
                    try:
                        self._note_table_activity(sid, direct_template, url)
                        if self._is_active_session(sid):
                            current_table_id = str(
                                direct_template.get("table_id", "") or ""
                            )
                            if current_table_id and current_table_id == self.active_table_id:
                                self.state.set_pragmatic_identity(
                                    table_id=current_table_id,
                                    operator_game_id=str(
                                        self.session_operator_game.get(sid, "")
                                    ),
                                    theme_code=str(
                                        self.session_theme.get(sid, "")
                                    ),
                                    title=str(
                                        self.session_info.get(sid, {}).get("title", "")
                                    ),
                                )
                                self._start_direct_history_request(
                                    direct_template,
                                    session_id=sid,
                                    title=str(
                                        self.session_info.get(sid, {}).get("title", "")
                                    ),
                                )
                    except Exception:
                        pass

                if "/api/ui/statistichistory" in low:
                    try:
                        u=urllib.parse.urlsplit(url)
                        qs=urllib.parse.parse_qs(u.query)
                        table_id=str((qs.get("tableId") or [""])[0])
                    except Exception:
                        table_id=""

                    is_collector_req = bool(
                        self._is_collector_session(sid)
                        or (
                            self.table_scan_enabled
                            and table_id
                            and self.active_table_id
                            and table_id != self.active_table_id
                        )
                    )
                    if is_collector_req and table_id:
                        collector_title = self._clean_collector_label(
                            str(
                                self.table_scan_current_click_label
                                or self.table_scan_last_clicked_label
                                or self.session_info.get(sid, {}).get("title", "")
                                or table_id
                            ),
                            fallback=table_id,
                        )
                        self.send(
                            "Network.getResponseBody",
                            {"requestId":req},
                            session_id=sid,
                            kind="directbody",
                            context={
                                "session": sid,
                                "table_id": table_id,
                                "operator_game_id": str(
                                    self.session_operator_game.get(sid, "")
                                ),
                                "theme_code": str(
                                    self.session_theme.get(sid, "")
                                ),
                                "title": collector_title,
                                "collector": True,
                            }
                        )
                    elif (
                        self._is_active_session(sid)
                        and table_id
                        and table_id == self.active_table_id
                    ):
                        self.send(
                            "Network.getResponseBody",
                            {"requestId":req},
                            session_id=sid,
                            kind="directbody",
                            context={
                                "session": sid,
                                "table_id":table_id,
                                "operator_game_id":str(
                                    self.session_operator_game.get(sid,"")
                                ),
                                "theme_code":str(
                                    self.session_theme.get(sid,"")
                                ),
                                "title":str(
                                    self.session_info.get(sid,{}).get("title","")
                                ),
                            }
                        )
                    return

                # Pragmatic/table metadata responses are small JSON/text requests.
                # NEVER call getResponseBody on video/audio/stream segments or empty-mime
                # media requests, which would stall the WebGL video decoder.
                low_path = low.split("?", 1)[0]
                is_static_asset = low_path.endswith((
                    ".js", ".mjs", ".css", ".html", ".htm", ".png", ".jpg", ".jpeg",
                    ".gif", ".webp", ".svg", ".woff", ".woff2", ".ttf", ".otf",
                    ".mp3", ".mp4", ".ogg", ".wav", ".webm", ".wasm", ".ico", ".map",
                    ".ts", ".m4s", ".fmp4", ".m3u8", ".mpd", ".aac", ".flac", ".bin", ".dat", ".pbf",
                ))
                is_media_mime = any(
                    m in mime for m in ("video", "audio", "image", "font", "octet-stream", "mpegurl", "dash", "mp2t", "mp4", "webm")
                )
                if (
                    not is_static_asset
                    and not is_media_mime
                    and (
                        "pragmatic" in low
                        or "roulette" in low
                        or "table" in low
                        or "lobby" in low
                        or "game" in low
                    )
                    and "json" in mime
                ):
                    self.send(
                        "Network.getResponseBody",
                        {"requestId":req},
                        session_id=sid,
                        kind="body",
                        context={"request_id": req, "url": url, "session": sid}
                    )
            except Exception:
                pass
            return

    def run(self):
        threading.Thread(target=self.scan_dom_loop,daemon=True).start()

        while not self.stop_event.is_set():
            try:
                with self.state.lock:
                    self.state.chrome_connected = False
                    self.state.status = "Chrome aranıyor..."

                try:
                    ws_url = self.browser_ws_url()
                except Exception:
                    with self.state.lock:
                        self.state.chrome_connected = False
                        self.state.status = "CHROME BEKLENİYOR • debug bağlantısı yok"
                        if self.lobby_teach_steps:
                            self.state.autolobby_status = (
                                f"ÖĞREN: CHROME BEKLENİYOR • {len(self.lobby_teach_steps)} işlem hazır"
                            )
                    self._self_launch_debug_chrome()
                    time.sleep(2.0)
                    ws_url = self.browser_ws_url()

                self.ws = RawWebSocket(ws_url)

                with self.state.lock:
                    self.state.chrome_connected = True
                    self.state.status = "CHROME BAĞLI • son sayfa hazır"

                # Do NOT auto-start learned route on connect/reconnect; Chrome
                # already opens the user's last visited URL and auto-replay
                # would scroll the page or click lobby cards on its own.
                self.lobby_route_started = False

                self.pending.clear()
                self.target_info.clear()
                self.target_sessions.clear()
                self.session_targets.clear()
                self.target_parent.clear()
                self.session_info.clear()
                self.execution_contexts.clear()
                self.direct_api_seen.clear()
                self.direct_api_inflight.clear()
                self.recovery_hits.clear()
                self.recovery_last_hit.clear()
                self.recovery_last_scan.clear()
                self.lobby_last_scan.clear()
                self.lobby_last_action.clear()
                self.session_visibility.clear()
                self.session_table_activity.clear()
                self.session_theme.clear()
                self.session_operator_game.clear()
                self.active_game_sid = ""
                self.active_table_id = ""
                self.attaching.clear()

                self.send("Target.setDiscoverTargets", {"discover":True})
                self.send(
                    "Target.setAutoAttach",
                    {
                        "autoAttach":True,
                        "waitForDebuggerOnStart":False,
                        "flatten":True
                    }
                )
                self.send("Target.getTargets", {}, kind="targets")

                last_refresh = time.time()

                while not self.stop_event.is_set():
                    if time.time()-last_refresh > 2:
                        self.send("Target.getTargets", {}, kind="targets")
                        last_refresh = time.time()

                    raw = self.ws.recv_text()
                    if raw:
                        try:
                            self.handle(json.loads(raw))
                        except Exception:
                            pass

            except Exception:
                try:
                    if self.ws:
                        self.ws.close()
                except Exception:
                    pass
                self.ws = None

                with self.state.lock:
                    self.state.chrome_connected = False
                    self.state.status = "CHROME BAĞLANTISI BEKLENİYOR"
                    if self.lobby_teach_steps:
                        self.state.autolobby_status = (
                            f"ÖĞREN: CHROME BEKLENİYOR • {len(self.lobby_teach_steps)} işlem hazır"
                        )

                self._self_launch_debug_chrome()
                time.sleep(2)

    def stop(self):
        self.stop_event.set()
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass



def flash_formula_self_test():
    """Deterministic tests for the exact European wheel neighbor formula."""
    cases = [
        (28, 1, {7, 28, 12}),
        (28, 2, {29, 7, 28, 12, 35}),
        (0, 1, {26, 0, 32}),
        (0, 2, {3, 26, 0, 32, 15}),
        (23, 1, {8, 23, 10}),
        (23, 2, {30, 8, 23, 10, 5}),
    ]
    for center, k, expected in cases:
        got = set(int(x) for x in wheel_neighbors(center, k))
        if got != expected:
            raise AssertionError(
                f"Komşu formülü hatalı: center={center} K{k} "
                f"got={sorted(got)} expected={sorted(expected)}"
            )
    return True


class App:
    BG = "#101214"
    PANEL = "#171a1f"
    PANEL2 = "#1d2128"
    TEXT = "#f3f5f7"
    MUTED = "#9da6b2"
    GREEN = "#55d187"
    RED = "#ff6b6b"
    BLUE = "#62a8ff"
    YELLOW = "#f6c85f"

    def __init__(self):
        self.state = RouletteState()
        self.bridge = ChromeBridge(self.state)
        self.bridge.start()
        self.exit_code = 0
        self._restart_in_progress = False

        self.root = tk.Tk()
        self.root.title("Roulette Pro AI V2.9.42 • Lobi Bitti Düzeltme")
        self.root.configure(bg=self.BG)
        self.root.attributes("-topmost", True)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = 410
        h = min(900, max(720, sh-80))
        self.root.geometry(f"{w}x{h}+{max(0,sw-w-8)}+8")
        self.root.minsize(370,680)

        self.build()
        self.root.bind_all("<MouseWheel>", self._on_detail_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_detail_mousewheel, add="+")
        self.root.bind_all("<Button-5>", self._on_detail_mousewheel, add="+")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(200,self.refresh)

    def box(self):
        f = tk.Frame(
            self.root,bg=self.PANEL,
            highlightthickness=1,
            highlightbackground="#292e36"
        )
        f.pack(fill="x",padx=7,pady=(0,5))
        return f

    def _detail_frame(self):
        shell = tk.Frame(
            self.root,bg=self.PANEL,
            highlightthickness=1,highlightbackground="#292e36"
        )
        scrollbar = tk.Scrollbar(shell, orient="vertical")
        canvas = tk.Canvas(
            shell,
            bg=self.PANEL,
            highlightthickness=0,
            bd=0,
            height=260,
            yscrollcommand=scrollbar.set,
        )
        scrollbar.config(command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg=self.PANEL)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        last_state = {"bbox": None, "w": None}

        def sync_scrollregion(_event=None):
            bbox = canvas.bbox("all")
            if bbox != last_state["bbox"]:
                last_state["bbox"] = bbox
                canvas.configure(scrollregion=bbox)

        def sync_width(event):
            w = max(1, int(event.width))
            if w != last_state["w"]:
                last_state["w"] = w
                canvas.itemconfigure(window_id, width=w)

        content.bind("<Configure>", sync_scrollregion)
        canvas.bind("<Configure>", sync_width)
        shell._scroll_canvas = canvas
        shell._scroll_content = content
        return shell, content

    def _on_detail_mousewheel(self, event):
        key = getattr(self, "_open_panel", None)
        shell = getattr(self, "detail_frames", {}).get(key)
        canvas = getattr(shell, "_scroll_canvas", None) if shell else None
        if canvas is None:
            return None
        try:
            x, y = int(event.x_root), int(event.y_root)
            left, top = canvas.winfo_rootx(), canvas.winfo_rooty()
            if not (
                left <= x < left + canvas.winfo_width()
                and top <= y < top + canvas.winfo_height()
            ):
                return None
            if getattr(event, "num", None) == 4:
                units = -3
            elif getattr(event, "num", None) == 5:
                units = 3
            else:
                delta = int(getattr(event, "delta", 0) or 0)
                units = -max(1, abs(delta) // 120) if delta > 0 else max(1, abs(delta) // 120)
            canvas.yview_scroll(units, "units")
            return "break"
        except Exception:
            return None

    def _save_last_ui_panel(self, key):
        try:
            p = os.path.join(persistent_data_dir(), "last_ui_panel.txt")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(str(key or ""))
        except Exception:
            pass

    def _restore_last_ui_panel(self):
        try:
            p = os.path.join(persistent_data_dir(), "last_ui_panel.txt")
            if os.path.exists(p):
                saved = open(p, "r", encoding="utf-8", errors="ignore").read().strip()
            else:
                saved = "data"
            if saved and saved in self.detail_frames:
                self.toggle_panel(saved)
        except Exception:
            pass

    def toggle_panel(self, key):
        current = getattr(self,"_open_panel",None)
        for frame in self.detail_frames.values():
            frame.pack_forget()
        if current == key:
            self._open_panel = None
            self._save_last_ui_panel("")
            return
        frame = self.detail_frames.get(key)
        if frame is not None:
            frame.pack(fill="both",expand=True,padx=7,pady=(0,5),after=self.nav)
            self._open_panel = key
            self._save_last_ui_panel(key)

    def open_table_banks(self):
        win = getattr(self, "_banks_window", None)
        try:
            if win is not None and win.winfo_exists():
                win.lift()
                win.focus_force()
                return
        except Exception:
            pass

        win = tk.Toplevel(self.root)
        self._banks_window = win
        win.title("V2.9.12 • Masa Bankaları")
        win.configure(bg=self.BG)
        win.geometry("860x430")
        win.minsize(680, 320)

        top_bar = tk.Frame(win, bg=self.BG)
        top_bar.pack(fill="x", padx=10, pady=(10, 6))
        summary = tk.Label(
            top_bar, text="Masa bankaları yükleniyor...",
            font=("Segoe UI", 10, "bold"), fg=self.GREEN, bg=self.BG,
        )
        summary.pack(side="left", fill="x", expand=True)
        tk.Button(
            top_bar,
            text="GEÇMİŞ MASA VERİLERİNİ SİL",
            command=self.clear_past_tables_ui,
            font=("Segoe UI", 8, "bold"),
            bg=self.PANEL2,
            fg=self.YELLOW,
            activebackground=self.PANEL2,
            activeforeground=self.RED,
            relief="flat",
            bd=0,
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="right")
        frame = tk.Frame(win, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        columns = ("name", "count", "fresh", "updated", "source")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for key, label in (
            ("name", "MASA"), ("count", "SPIN"), ("fresh", "DURUM"),
            ("updated", "SON GÜNCELLEME"), ("source", "KAYNAK"),
        ):
            tree.heading(key, text=label)
        tree.column("name", width=250, anchor="w")
        tree.column("count", width=70, anchor="center")
        tree.column("fresh", width=80, anchor="center")
        tree.column("updated", width=145, anchor="center")
        tree.column("source", width=240, anchor="w")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        def refresh_rows():
            try:
                if not win.winfo_exists():
                    return
                snap = self.state.snapshot()
                rows = snap.get("bank_rows") or []
                summary.config(text=(
                    f"{snap.get('background_status', 'ÇOKLU TOPLAYICI')}"
                    f" • {len(rows)} banka"
                ))
                for item in tree.get_children():
                    tree.delete(item)
                for row in rows:
                    source = row.get("last_source", "-")
                    if row.get("last_error"):
                        source = "HATA: " + row.get("last_error", "")
                    tree.insert("", "end", values=(
                        row.get("display_name", row.get("table_id", "-")),
                        row.get("long_count", 0),
                        row.get("freshness", "-"),
                        row.get("last_update", "-"),
                        source,
                    ))
                win.after(2000, refresh_rows)
            except Exception:
                pass

        refresh_rows()

    def build(self):
        head = tk.Frame(self.root,bg=self.BG)
        head.pack(fill="x",padx=10,pady=(7,4))
        tk.Label(head,text="ROULETTE PRO AI",font=("Segoe UI",14,"bold"),fg=self.TEXT,bg=self.BG).pack(side="left")
        tk.Label(head,text="V2.9.42 LOBİ BİTTİ",font=("Segoe UI",8,"bold"),fg=self.GREEN,bg=self.BG).pack(side="right")
        self.status = tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)

        master = tk.Frame(self.root,bg=self.PANEL,highlightthickness=1,highlightbackground="#292e36")
        master.pack(fill="x",padx=7,pady=(0,5))
        tk.Label(master,text="TEK SAYI MODU",font=("Segoe UI",9,"bold"),fg=self.MUTED,bg=self.PANEL).pack(pady=(7,1))
        self.action_line = tk.Label(
            master,
            text="KAYNAKLAR HESAPLANIYOR",
            font=("Consolas",9,"bold"),
            fg=self.BLUE,
            bg=self.PANEL,
        )
        self.action_line.pack(pady=(0,2))
        tk.Label(
            master,
            text="NET SAYI",
            font=("Segoe UI",10,"bold"),
            fg=self.GREEN,
            bg=self.PANEL,
        ).pack()
        main_result_row=tk.Frame(master,bg=self.PANEL)
        main_result_row.pack(fill="x",padx=8,pady=(1,0))

        k1_card=tk.Frame(
            main_result_row,
            bg=self.PANEL2,
            highlightthickness=1,
            highlightbackground=self.MUTED,
        )
        k1_card.pack(side="left",fill="both",expand=True,padx=(0,5))
        tk.Label(
            k1_card,text="1 KOMŞU",
            font=("Segoe UI",8,"bold"),
            fg=self.MUTED,bg=self.PANEL2,
        ).pack(pady=(5,0))
        self.k1_main_result=tk.Label(
            k1_card,text="BEKLİYOR",
            font=("Segoe UI",11,"bold"),
            fg=self.MUTED,bg=self.PANEL2,
        )
        self.k1_main_result.pack(pady=(1,5))

        net_card=tk.Frame(main_result_row,bg=self.PANEL)
        net_card.pack(side="left",fill="both",expand=True)
        self.main_pick = tk.Label(
            net_card,text="--",
            font=("Segoe UI",52,"bold"),
            fg=self.YELLOW,bg=self.PANEL,
        )
        self.main_pick.pack(pady=(0,0))

        k2_card=tk.Frame(
            main_result_row,
            bg=self.PANEL2,
            highlightthickness=1,
            highlightbackground=self.MUTED,
        )
        k2_card.pack(side="left",fill="both",expand=True,padx=(5,0))
        tk.Label(
            k2_card,text="2 KOMŞU",
            font=("Segoe UI",8,"bold"),
            fg=self.MUTED,bg=self.PANEL2,
        ).pack(pady=(5,0))
        self.k2_main_result=tk.Label(
            k2_card,text="BEKLİYOR",
            font=("Segoe UI",11,"bold"),
            fg=self.MUTED,bg=self.PANEL2,
        )
        self.k2_main_result.pack(pady=(1,5))
        self.main_region_line = tk.Label(master,text="BÖLGE: --",font=("Segoe UI",12,"bold"),fg=self.BLUE,bg=self.PANEL)
        self.main_region_line.pack(pady=(0,2))
        self.instant_line = tk.Label(master,text="YEDEKLER (KAYIT): --",font=("Segoe UI",10,"bold"),fg=self.GREEN,bg=self.PANEL)
        self.instant_line.pack(pady=(0,2))
        self.confidence = tk.Label(master,text="KAYNAK UYUMU: --",font=("Segoe UI",8,"bold"),fg=self.TEXT,bg=self.PANEL,wraplength=390,justify="center")
        self.confidence.pack(padx=6)
        self.quality_line = tk.Label(master,text="VERİ MODU: KAYNAKLAR KAYDEDİLİYOR",font=("Segoe UI",9,"bold"),fg=self.GREEN,bg=self.PANEL)
        self.quality_line.pack()

        # V2.8.8 - manual play helper only.
        # These buttons NEVER click the casino UI and NEVER place a bet.
        # They only calculate/highlight the current NET + 4 YEDEK coverage.
        helper_bar=tk.Frame(master,bg=self.PANEL)
        helper_bar.pack(fill="x",padx=8,pady=(5,2))

        tk.Button(
            helper_bar,
            text="1K HAZIRLA",
            command=lambda: self.open_neighbor_helper(1),
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,fg=self.TEXT,
            activebackground=self.PANEL2,activeforeground=self.TEXT,
            relief="flat",bd=0,padx=6,pady=4,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(0,2))

        tk.Button(
            helper_bar,
            text="1K FLAŞ AUTO",
            command=lambda: self.flash_neighbor_on_game(1),
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,fg=self.GREEN,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=6,pady=4,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=2)

        tk.Button(
            helper_bar,
            text="2K HAZIRLA",
            command=lambda: self.open_neighbor_helper(2),
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,fg=self.TEXT,
            activebackground=self.PANEL2,activeforeground=self.TEXT,
            relief="flat",bd=0,padx=6,pady=4,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=2)

        tk.Button(
            helper_bar,
            text="2K FLAŞ AUTO",
            command=lambda: self.flash_neighbor_on_game(2),
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,fg=self.GREEN,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=6,pady=4,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(2,0))

        tk.Button(
            master,
            text="FLAŞI KAPAT",
            command=self.stop_game_flash,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL,fg=self.MUTED,
            activebackground=self.PANEL,activeforeground=self.TEXT,
            relief="flat",bd=0,padx=5,pady=1,cursor="hand2",
        ).pack(pady=(0,2))

        # V2.9.21: old learned-route controls are hidden from the main screen.
        # Widgets still exist for compatibility, but are not packed.
        teach_bar=tk.Frame(master,bg=self.PANEL)
        # teach_bar.pack(fill="x",padx=8,pady=(1,2))
        tk.Button(
            teach_bar,
            text="ÖĞREN BAŞLAT",
            command=self.start_lobby_teach_ui,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.GREEN,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=5,pady=3,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(0,2))
        tk.Button(
            teach_bar,
            text="ÖĞREN BİTİR",
            command=self.finish_lobby_teach_ui,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.BLUE,
            activebackground=self.PANEL2,activeforeground=self.BLUE,
            relief="flat",bd=0,padx=5,pady=3,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=2)
        tk.Button(
            teach_bar,
            text="YOLU BAŞLAT",
            command=self.start_learned_route_ui,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.YELLOW,
            activebackground=self.PANEL2,activeforeground=self.YELLOW,
            relief="flat",bd=0,padx=5,pady=3,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=2)
        tk.Button(
            teach_bar,
            text="SIFIRLA",
            command=self.reset_lobby_teach_ui,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.MUTED,
            activebackground=self.PANEL2,activeforeground=self.TEXT,
            relief="flat",bd=0,padx=5,pady=3,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(2,0))

        self.lobby_teach_line=tk.Label(
            master,
            text="ÖĞREN: durum bekleniyor",
            font=("Consolas",7,"bold"),
            fg=self.BLUE,bg=self.PANEL,
            wraplength=390,
        )
        # self.lobby_teach_line.pack(pady=(0,1))

        self.chrome_link_line=tk.Label(
            master,
            text="CHROME: bağlantı kontrol ediliyor...",
            font=("Consolas",7,"bold"),
            fg=self.YELLOW,bg=self.PANEL,
            wraplength=390,
        )
        # self.chrome_link_line.pack(pady=(0,2))

        self.top_last_line = tk.Label(master,text="SON: --",font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL)
        self.top_last_line.pack(pady=(1,2))
        self.global_pool_line = tk.Label(
            master,
            text="ORTAK HAVUZ: masa verileri bekleniyor",
            font=("Consolas",8,"bold"),
            fg=self.YELLOW,
            bg=self.PANEL,
            wraplength=390,
            justify="center",
        )
        self.global_pool_line.pack(pady=(0,6))

        self.nav = tk.Frame(self.root,bg=self.BG)
        self.nav.pack(fill="x",padx=7,pady=(0,5))
        for key,label in (
            ("data","VERİ"),
            ("sources","KAYNAKLAR"),
            ("perf","PERFORMANS"),
            ("history","GEÇMİŞ"),
            ("neighbor","2 KOMŞU"),
            ("neighbor1","1 KOMŞU"),
        ):
            tk.Button(
                self.nav,text=label,command=lambda k=key:self.toggle_panel(k),
                font=("Segoe UI",8,"bold"),bg=self.PANEL2,fg=self.TEXT,
                activebackground=self.PANEL,activeforeground=self.GREEN,
                relief="flat",bd=0,padx=7,pady=5
            ).pack(side="left",expand=True,fill="x",padx=1)

        self.detail_frames = {}
        self._open_panel = None

        data_shell,data=self._detail_frame(); self.detail_frames["data"]=data_shell
        tk.Label(data,text="VERİ DURUMU",font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL).pack(anchor="w",padx=8,pady=(6,1))
        self.archive_line=tk.Label(data,text="Veri bekleniyor...",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.BLUE,bg=self.PANEL,wraplength=380)
        self.archive_line.pack(fill="x",padx=8,pady=(1,2))
        self.collector_line=tk.Label(data,text="ÇOKLU TOPLAYICI: keşif bekleniyor",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.GREEN,bg=self.PANEL,wraplength=380)
        self.collector_line.pack(fill="x",padx=8,pady=(1,2))
        bank_bar=tk.Frame(data,bg=self.PANEL)
        bank_bar.pack(fill="x",padx=8,pady=(1,5))
        tk.Button(
            bank_bar,text="MASA BANKALARINI GÖR",command=self.open_table_banks,
            font=("Segoe UI",8,"bold"),bg=self.PANEL2,fg=self.TEXT,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=7,pady=5,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(0,2))
        tk.Button(
            bank_bar,text="GEÇMİŞ MASA VERİLERİNİ SİL",command=self.clear_past_tables_ui,
            font=("Segoe UI",8,"bold"),bg=self.PANEL2,fg=self.YELLOW,
            activebackground=self.PANEL2,activeforeground=self.RED,
            relief="flat",bd=0,padx=7,pady=5,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(2,0))
        scan_bar=tk.Frame(data,bg=self.PANEL)
        scan_bar.pack(fill="x",padx=8,pady=(0,5))
        tk.Button(
            scan_bar,text="TEK SEKME LOBİ TOPLA • 5 DK",command=self.start_tab_walk_scan_ui,
            font=("Segoe UI",8,"bold"),bg=self.PANEL2,fg=self.BLUE,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=7,pady=5,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(0,2))
        tk.Button(
            scan_bar,text="TARAMAYI DURDUR",command=self.stop_table_scan_ui,
            font=("Segoe UI",8,"bold"),bg=self.PANEL2,fg=self.RED,
            activebackground=self.PANEL2,activeforeground=self.RED,
            relief="flat",bd=0,padx=7,pady=5,cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(2,0))
        self.history_brain_line=tk.Label(data,text="Geçmiş sinyali bekleniyor...",font=("Consolas",8),justify="left",anchor="w",fg=self.TEXT,bg=self.PANEL,wraplength=380)
        self.history_brain_line.pack(fill="x",padx=8,pady=(0,6))

        sources_shell,sources=self._detail_frame(); self.detail_frames["sources"]=sources_shell
        tk.Label(sources,text="KAYNAK LABORATUVARI • HER TUR AYRI ÖLÇÜLÜR",font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL).pack(anchor="w",padx=8,pady=(6,1))
        self.consensus_line=tk.Label(sources,text="Kaynak uyumu bekleniyor...",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.GREEN,bg=self.PANEL,wraplength=380)
        self.consensus_line.pack(fill="x",padx=8,pady=(1,2))
        self.weight_line=tk.Label(sources,text="",font=("Segoe UI",8),justify="left",anchor="w",fg=self.BLUE,bg=self.PANEL,wraplength=380)
        self.weight_line.pack(fill="x",padx=8,pady=(0,6))

        perf_shell,perf=self._detail_frame(); self.detail_frames["perf"]=perf_shell
        perf_head=tk.Frame(perf,bg=self.PANEL)
        perf_head.pack(fill="x",padx=8,pady=(6,1))
        tk.Label(
            perf_head,text="GERÇEK PERFORMANS",
            font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL
        ).pack(side="left")
        tk.Button(
            perf_head,text="PERFORMANSI SIFIRLA",
            command=self.clear_performance_view,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.YELLOW,
            activebackground=self.PANEL2,activeforeground=self.GREEN,
            relief="flat",bd=0,padx=7,pady=2,cursor="hand2"
        ).pack(side="right")
        self.validation_line=tk.Label(perf,text="Henüz doğrulama yok.",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.TEXT,bg=self.PANEL)
        self.validation_line.pack(fill="x",padx=8,pady=(1,1))
        self.recent20_line=tk.Label(perf,text="",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.GREEN,bg=self.PANEL)
        self.recent20_line.pack(fill="x",padx=8,pady=(0,2))
        self.walkforward_line=tk.Label(perf,text="WALK-FORWARD: veri bekleniyor",font=("Consolas",8,"bold"),justify="left",anchor="w",fg=self.BLUE,bg=self.PANEL,wraplength=380)
        self.walkforward_line.pack(fill="x",padx=8,pady=(0,2))
        self.locked_line=tk.Label(
            perf,text="LOCKED LIVE 500: yeni V2.9 turları bekleniyor",
            font=("Consolas",8,"bold"),justify="left",anchor="w",
            fg=self.YELLOW,bg=self.PANEL,wraplength=380,
        )
        self.locked_line.pack(fill="x",padx=8,pady=(0,2))
        self.risk_line=tk.Label(
            perf,text="RİSK/EV: veri bekleniyor",
            font=("Consolas",8,"bold"),justify="left",anchor="w",
            fg=self.YELLOW,bg=self.PANEL,wraplength=380,
        )
        self.risk_line.pack(fill="x",padx=8,pady=(0,6))

        hist_shell,hist=self._detail_frame(); self.detail_frames["history"]=hist_shell
        top=tk.Frame(hist,bg=self.PANEL); top.pack(fill="x",padx=8,pady=(5,1))
        tk.Label(top,text="SON SAYI",font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL).pack(side="left")
        self.last_num=tk.Label(top,text="-",font=("Segoe UI",24,"bold"),fg=self.TEXT,bg=self.PANEL); self.last_num.pack(side="right")
        self.last_meta=tk.Label(hist,text="-",font=("Segoe UI",8),fg=self.TEXT,bg=self.PANEL); self.last_meta.pack(anchor="e",padx=8,pady=(0,3))

        self.pending_compare_line=tk.Label(
            hist,text="BEKLEYEN TAHMİN: --",
            font=("Consolas",8,"bold"),justify="left",anchor="w",
            fg=self.BLUE,bg=self.PANEL,wraplength=470
        )
        self.pending_compare_line.pack(fill="x",padx=8,pady=(3,3))

        compare_head=tk.Frame(hist,bg=self.PANEL)
        compare_head.pack(fill="x",padx=8,pady=(4,1))
        tk.Label(
            compare_head,text="TAHMİN / ÇIKAN KARŞILAŞTIRMASI",
            font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL
        ).pack(side="left")
        tk.Button(
            compare_head,text="TEMİZLE",
            command=self.clear_compare_view,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,fg=self.TEXT,
            activebackground=self.PANEL2,activeforeground=self.TEXT,
            relief="flat",bd=0,padx=6,pady=1,cursor="hand2"
        ).pack(side="right")

        self.compare_history_line=tk.Label(
            hist,text="Henüz doğrulanmış tur yok.",
            font=("Consolas",8,"bold"),justify="left",anchor="w",
            fg=self.TEXT,bg=self.PANEL,wraplength=470
        )
        self.compare_history_line.pack(fill="x",padx=8,pady=(1,5))

        tk.Label(
            hist,text="SON 20 ÇIKAN SAYI",
            font=("Segoe UI",8,"bold"),fg=self.MUTED,bg=self.PANEL
        ).pack(anchor="w",padx=8,pady=(3,1))

        self.history=tk.Label(hist,text="-",font=("Consolas",9,"bold"),justify="left",anchor="w",fg=self.TEXT,bg=self.PANEL,wraplength=470)
        self.history.pack(fill="x",padx=8,pady=(1,6))


        neighbor_shell,neighbor=self._detail_frame(); self.detail_frames["neighbor"]=neighbor_shell

        nb_head=tk.Frame(neighbor,bg=self.PANEL)
        nb_head.pack(fill="x",padx=8,pady=(6,2))
        tk.Label(
            nb_head,
            text="2 KOMŞU • NET + 4 YEDEK",
            font=("Segoe UI",8,"bold"),
            fg=self.MUTED,
            bg=self.PANEL,
        ).pack(side="left")
        tk.Button(
            nb_head,
            text="TEMİZLE",
            command=self.clear_neighbor_view,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,
            fg=self.TEXT,
            activebackground=self.PANEL2,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
        ).pack(side="right")

        self.neighbor_summary=tk.Label(
            neighbor,
            text="Henüz komşu istatistiği yok.",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.TEXT,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor_summary.pack(fill="x",padx=8,pady=(2,5))

        self.neighbor_pending=tk.Label(
            neighbor,
            text="BEKLEYEN KOMŞU OYUNU: --",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.BLUE,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor_pending.pack(fill="x",padx=8,pady=(2,5))

        self.neighbor_history=tk.Label(
            neighbor,
            text="Yeni gerçek sonuç bekleniyor.",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.TEXT,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor_history.pack(fill="x",padx=8,pady=(2,7))


        neighbor1_shell,neighbor1=self._detail_frame(); self.detail_frames["neighbor1"]=neighbor1_shell

        nb1_head=tk.Frame(neighbor1,bg=self.PANEL)
        nb1_head.pack(fill="x",padx=8,pady=(6,2))
        tk.Label(
            nb1_head,
            text="1 KOMŞU • SOL 1 + MERKEZ + SAĞ 1",
            font=("Segoe UI",8,"bold"),
            fg=self.MUTED,
            bg=self.PANEL,
        ).pack(side="left")
        tk.Button(
            nb1_head,
            text="TEMİZLE",
            command=self.clear_neighbor1_view,
            font=("Segoe UI",7,"bold"),
            bg=self.PANEL2,
            fg=self.TEXT,
            activebackground=self.PANEL2,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=6,
            pady=1,
            cursor="hand2",
        ).pack(side="right")

        self.neighbor1_summary=tk.Label(
            neighbor1,
            text="Henüz 1 komşu istatistiği yok.",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.TEXT,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor1_summary.pack(fill="x",padx=8,pady=(2,5))

        self.neighbor1_pending=tk.Label(
            neighbor1,
            text="BEKLEYEN 1 KOMŞU OYUNU: --",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.BLUE,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor1_pending.pack(fill="x",padx=8,pady=(2,5))

        self.neighbor1_history=tk.Label(
            neighbor1,
            text="Yeni gerçek sonuç bekleniyor.",
            font=("Consolas",8,"bold"),
            justify="left",
            anchor="w",
            fg=self.TEXT,
            bg=self.PANEL,
            wraplength=380,
        )
        self.neighbor1_history.pack(fill="x",padx=8,pady=(2,7))

        # Region details are calculated but only the top BÖLGE line is visible.
        self.region_main=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.region_conf=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.region_breakdown=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.neighbor_zone=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.region_reason=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)

        # Compatibility / diagnostics hidden until requested by future UI changes.
        self.coverage_line=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.model_share=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.stage_line=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.watch_list=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.reserve_line=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.expert_line=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.hot=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.cold=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.distribution=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.fairness_status=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.fairness_line=tk.Label(self.root,text="",font=("Segoe UI",1),fg=self.BG,bg=self.BG)
        self.source=tk.Label(self.root,text="Kaynak: -",font=("Segoe UI",7),fg=self.MUTED,bg=self.BG)
        self.source.pack(pady=(0,4))
        self._restore_last_ui_panel()

    def clear_compare_view(self):
        self.state.clear_display_comparisons()
        self._last_render_sig = None
        self.compare_history_line.config(
            text="Liste temizlendi • yeni gerçek sonuç 01 olarak başlayacak."
        )

    def clear_neighbor_view(self):
        self.state.clear_neighbor_comparisons()
        self._last_render_sig = None
        self.neighbor_history.config(
            text="Liste temizlendi • yeni gerçek sonuç 01 olarak başlayacak."
        )

    def clear_neighbor1_view(self):
        self.state.clear_neighbor1_comparisons()
        self._last_render_sig = None
        self.neighbor1_history.config(
            text="Liste temizlendi • yeni gerçek sonuç 01 olarak başlayacak."
        )

    def clear_performance_view(self):
        self.state.reset_performance_stats()
        self._last_render_sig = None
        self._last_status_sig = None
        try:
            self.refresh()
        except Exception:
            pass

    def clear_past_tables_ui(self):
        self.state.clear_all_past_table_data()
        try:
            self.bridge.chrome_dga_enabled = False
            try:
                self.bridge.dga_feed.stop_collection("geçmiş masa verileri silindi")
            except Exception:
                pass
            with self.bridge.collector_lock:
                self.bridge.collector_seen = {}
                self.bridge.collector_inflight = set()
            self.bridge.dga_frame_last_keys = {}
            self.bridge._recent_dga_payloads = {}
            self.bridge.direct_api_seen = {}
            self.bridge.table_scan_probed_keys = set()
            self.bridge.table_scan_probe_done = set()
            self.bridge.table_scan_probe_success = set()
            self.bridge.table_scan_probe_fail = set()
            self.bridge.table_scan_probe_skip = set()
            self.bridge.table_scan_visited = set()
        except Exception:
            pass
        self._last_render_sig = None
        self._last_status_sig = None
        try:
            self.refresh()
        except Exception:
            pass


    def _current_neighbor_helper_data(self, neighbor_count):
        """Return current NET + 4 YEDEK manual coverage for K1/K2."""
        try:
            s = self.state.snapshot()
        except Exception:
            return None

        pending = s.get("pending_compare") or {}
        if not pending:
            return None

        try:
            net = int(pending.get("predicted"))
        except Exception:
            return None

        backups = []
        for x in (pending.get("side4") or [])[:4]:
            try:
                backups.append(int(x))
            except Exception:
                pass

        centers = [net] + backups
        if not centers:
            return None

        by_center = {}
        unique = set()
        for center in centers:
            zone = [int(x) for x in wheel_neighbors(int(center), int(neighbor_count))]
            by_center[int(center)] = zone
            unique.update(zone)

        return {
            "net": net,
            "backups": backups,
            "centers": centers,
            "by_center": by_center,
            "unique": sorted(unique),
            "neighbor_count": int(neighbor_count),
        }

    def _copy_neighbor_numbers(self, numbers, button=None):
        text = " ".join(str(int(x)) for x in sorted(set(numbers)))
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update_idletasks()
            if button is not None:
                old = button.cget("text")
                button.config(text="KOPYALANDI ✓", fg=self.GREEN)
                self.root.after(
                    1200,
                    lambda: button.config(text=old, fg=self.TEXT)
                )
        except Exception:
            pass

    def _game_flash_js(self, numbers, neighbor_count, net=None, backups=None):
        """Build JS overlay that only highlights visible roulette number elements."""
        nums_json = json.dumps(sorted(set(int(x) for x in numbers)))
        k = int(neighbor_count)
        try:
            net_txt = f"{int(net):02d}"
        except Exception:
            net_txt = "--"
        backup_txt = "/".join(
            f"{int(x):02d}" for x in (backups or [])[:4]
        )
        pred_txt = f"NET {net_txt} • Y {backup_txt}"
        return fr"""
(() => {{
  const TARGETS = new Set({nums_json});
  const ROOT_ID = '__roulette_ai_flash_root';
  const STYLE_ID = '__roulette_ai_flash_style';

  try {{
    const old = document.getElementById(ROOT_ID);
    if (old) old.remove();
    const oldStyle = document.getElementById(STYLE_ID);
    if (oldStyle) oldStyle.remove();
    if (window.__rouletteAiFlashTimer) {{
      clearInterval(window.__rouletteAiFlashTimer);
      window.__rouletteAiFlashTimer = null;
    }}
  }} catch (_) {{}}

  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    @keyframes rouletteAiFlash {{
      0%,100% {{ opacity: .78; box-shadow: 0 0 8px 3px #7CFF6B, inset 0 0 5px #7CFF6B; }}
      50% {{ opacity: 1; box-shadow: 0 0 18px 7px #7CFF6B, inset 0 0 11px #F7FF63; }}
    }}
    .roulette-ai-flash-box {{
      position: fixed;
      pointer-events: none !important;
      z-index: 2147483647 !important;
      border: 3px solid #7CFF6B;
      border-radius: 7px;
      background: rgba(90,255,90,.15);
      animation: rouletteAiFlash .55s infinite;
      box-sizing: border-box;
    }}
    .roulette-ai-flash-badge {{
      position: fixed;
      pointer-events: none !important;
      z-index: 2147483647 !important;
      left: 50%; top: 8px; transform: translateX(-50%);
      padding: 5px 10px;
      border-radius: 8px;
      background: rgba(0,0,0,.78);
      color: #7CFF6B;
      border: 1px solid #7CFF6B;
      font: 700 13px Arial,sans-serif;
      letter-spacing: .4px;
    }}
  `;
  (document.head || document.documentElement).appendChild(style);

  const root = document.createElement('div');
  root.id = ROOT_ID;
  root.style.pointerEvents = 'none';
  root.style.position = 'fixed';
  root.style.inset = '0';
  root.style.zIndex = '2147483647';
  document.documentElement.appendChild(root);

  const badge = document.createElement('div');
  badge.className = 'roulette-ai-flash-badge';
  badge.textContent = '{k} KOMŞU • {pred_txt} • ' + TARGETS.size + ' SAYI';
  root.appendChild(badge);

  function visible(el) {{
    try {{
      const r = el.getBoundingClientRect();
      const s = getComputedStyle(el);
      return r.width >= 4 && r.height >= 6 && r.width <= 100 && r.height <= 100 &&
             r.bottom > 0 && r.right > 0 && r.top < innerHeight && r.left < innerWidth &&
             s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity || 1) > .05;
    }} catch (_) {{ return false; }}
  }}

  function numericLeaves(scope=document) {{
    const out = [];
    const all = scope.querySelectorAll('div,span,button,p,text,tspan');
    for (const el of all) {{
      if (!visible(el)) continue;
      const t = (el.textContent || el.innerText || '').trim();
      if (!/^(?:[0-9]|[12][0-9]|3[0-6])$/.test(t)) continue;
      let childNum = false;
      for (const ch of el.children) {{
        const ct = (ch.textContent || '').trim();
        if (/^(?:[0-9]|[12][0-9]|3[0-6])$/.test(ct)) {{ childNum = true; break; }}
      }}
      if (childNum) continue;
      out.push({{el, n:Number(t), r:el.getBoundingClientRect()}});
    }}
    return out;
  }}

  function normText(x) {{
    return String(x || '')
      .replace(/\s+/g,' ')
      .trim()
      .toLocaleUpperCase('tr-TR');
  }}

  function findTrackLabel(label) {{
    const wanted = normText(label);
    const nodes = document.querySelectorAll('div,span,button,p,text,tspan');
    let best = null;
    for (const el of nodes) {{
      if (!visible(el)) continue;
      const t = normText(el.textContent || el.innerText || '');
      if (t !== wanted) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 12 || r.height < 8) continue;
      const area = r.width * r.height;
      if (!best || area < best.area) best = {{el,r,area}};
    }}
    return best;
  }}

  function labelLockedTrackRect() {{
    const names = ['JEU 0','VOISINS','ORPHELINS','TIERS'];
    const found = names.map(findTrackLabel).filter(Boolean);
    if (found.length < 2) return null;

    let left = Math.min(...found.map(x => x.r.left));
    let right = Math.max(...found.map(x => x.r.right));
    let top = Math.min(...found.map(x => x.r.top));
    let bottom = Math.max(...found.map(x => x.r.bottom));

    const centerWidth = Math.max(120, right-left);
    const centerHeight = Math.max(24, bottom-top);

    // Sector labels sit INSIDE the oval. Expand to the numbered perimeter.
    const padX = Math.max(78, centerWidth * 0.23);
    const padTop = Math.max(42, centerHeight * 1.9);
    const padBottom = Math.max(44, centerHeight * 2.0);

    left -= padX;
    right += padX;
    top -= padTop;
    bottom += padBottom;

    // Keep within viewport.
    left = Math.max(0,left);
    top = Math.max(0,top);
    right = Math.min(innerWidth,right);
    bottom = Math.min(innerHeight,bottom);

    return {{
      left,right,top,bottom,
      width:right-left,height:bottom-top,
      cx:(left+right)/2,cy:(top+bottom)/2,
      labelCount:found.length
    }};
  }}

  function insideRectByCenter(r, tr) {{
    const cx = r.left + r.width/2;
    const cy = r.top + r.height/2;
    return cx >= tr.left && cx <= tr.right && cy >= tr.top && cy <= tr.bottom;
  }}

  function edgeDistance(r, tr) {{
    const cx = r.left + r.width/2;
    const cy = r.top + r.height/2;
    return Math.min(
      Math.abs(cx-tr.left),
      Math.abs(cx-tr.right),
      Math.abs(cy-tr.top),
      Math.abs(cy-tr.bottom)
    );
  }}

  function chooseRacetrack(leaves) {{
    // Score ancestors by how many UNIQUE roulette numbers they contain.
    const m = new Map();
    for (const item of leaves) {{
      let a = item.el.parentElement;
      for (let d=0; d<8 && a; d++, a=a.parentElement) {{
        let rec = m.get(a);
        if (!rec) {{ rec={{nums:new Set(), depth:d}}; m.set(a,rec); }}
        rec.nums.add(item.n);
      }}
    }}
    let best = null;
    for (const [el,rec] of m.entries()) {{
      const count = rec.nums.size;
      if (count < 25) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 250 || r.height < 80) continue;
      const area = Math.max(1,r.width*r.height);
      // Prefer ~37 unique numbers in a compact, visible racetrack-like block.
      const score = count*100000 - Math.abs(37-count)*30000 - area;
      if (!best || score > best.score) best={{el,score,r,count}};
    }}
    return best;
  }}

  function redraw() {{
    for (const x of Array.from(root.querySelectorAll('.roulette-ai-flash-box'))) x.remove();

    const leaves = numericLeaves(document);

    // PRIMARY METHOD:
    // Lock directly to the visible racetrack sector labels.
    const labelRect = labelLockedTrackRect();
    const track = chooseRacetrack(leaves);

    let candidates = leaves;
    let activeRect = null;
    let lockMode = 'GENEL';

    if (labelRect) {{
      activeRect = labelRect;
      lockMode = 'RACETRACK LOCK';

      candidates = leaves.filter(x =>
        insideRectByCenter(x.el.getBoundingClientRect(), labelRect)
      );

      // The racetrack numbers form the outer perimeter.
      // For duplicate text nodes choose the copy nearest that perimeter.
      candidates.sort((a,b) => {{
        const ar=a.el.getBoundingClientRect();
        const br=b.el.getBoundingClientRect();
        return edgeDistance(ar,labelRect) - edgeDistance(br,labelRect);
      }});
    }} else if (track) {{
      const tr = track.el.getBoundingClientRect();
      activeRect = {{
        left:tr.left,right:tr.right,top:tr.top,bottom:tr.bottom,
        width:tr.width,height:tr.height,
        cx:tr.left+tr.width/2,cy:tr.top+tr.height/2
      }};
      lockMode = 'FALLBACK';

      const marginX = Math.max(18, tr.width * 0.04);
      const marginY = Math.max(14, tr.height * 0.12);
      candidates = leaves.filter(x => {{
        if (track.el.contains(x.el)) return true;
        const r = x.el.getBoundingClientRect();
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height / 2;
        return (
          cx >= tr.left-marginX && cx <= tr.right+marginX &&
          cy >= tr.top-marginY && cy <= tr.bottom+marginY
        );
      }});

      candidates.sort((a,b) => {{
        const ar=a.el.getBoundingClientRect();
        const br=b.el.getBoundingClientRect();
        return edgeDistance(ar,activeRect) - edgeDistance(br,activeRect);
      }});
    }}

    // One primary highlight per target number.
    const seen = [];
    const drawnNumbers = new Set();
    for (const item of candidates) {{
      if (!TARGETS.has(item.n)) continue;
      if (drawnNumbers.has(item.n)) continue;

      const r = item.el.getBoundingClientRect();
      const key = `${{item.n}}:${{Math.round(r.left/4)}}:${{Math.round(r.top/4)}}`;
      if (seen.includes(key)) continue;
      seen.push(key);
      drawnNumbers.add(item.n);

      const box = document.createElement('div');
      box.className = 'roulette-ai-flash-box';
      const pad = 3;
      box.style.left = (r.left-pad) + 'px';
      box.style.top = (r.top-pad) + 'px';
      box.style.width = (r.width+pad*2) + 'px';
      box.style.height = (r.height+pad*2) + 'px';
      root.appendChild(box);
    }}

    const missing = Array.from(TARGETS).filter(n => !drawnNumbers.has(n));
    badge.textContent =
      '{k} KOMŞU • {pred_txt} • ' + TARGETS.size + ' SAYI • ' + lockMode +
      ' • İŞARETLİ ' + drawnNumbers.size + '/' + TARGETS.size +
      (missing.length ? ' • EKSİK: ' + missing.join('/') : ' • TAM ✓');
  }}

  redraw();
  window.__rouletteAiFlashTimer = setInterval(redraw, 350);
  return {{ok:true, targets:Array.from(TARGETS), k:{k}}};
}})()
"""

    def flash_neighbor_on_game(self, neighbor_count):
        """
        Arm K1/K2 visual flash mode.
        Once armed, refresh() keeps the overlay synchronized with the
        CURRENT NET + 4 YEDEK prediction automatically.
        """
        self._flash_mode = int(neighbor_count)
        self._flash_signature = None
        self._refresh_game_flash(force=True)

    def _refresh_game_flash(self, force=False):
        """Refresh flash targets only when current prediction actually changes."""
        k = getattr(self, "_flash_mode", None)
        if k not in (1, 2):
            return

        data = self._current_neighbor_helper_data(k)
        if not data:
            return

        sid = str(getattr(self.bridge, "active_game_sid", "") or "")
        ws = getattr(self.bridge, "ws", None)
        if not sid or ws is None:
            return

        signature = (
            sid,
            int(k),
            int(data["net"]),
            tuple(int(x) for x in data["backups"]),
            tuple(sorted(int(x) for x in data["unique"])),
        )

        if not force and signature == getattr(self, "_flash_signature", None):
            return

        try:
            js = self._game_flash_js(
                data["unique"],
                k,
                net=data["net"],
                backups=data["backups"],
            )
            self.bridge.send(
                "Runtime.evaluate",
                {
                    "expression": js,
                    "returnByValue": True,
                    "awaitPromise": True,
                },
                session_id=sid,
                kind="manual_flash",
                context={
                    "k": int(k),
                    "net": int(data["net"]),
                    "backups": [int(x) for x in data["backups"]],
                    "count": len(data["unique"]),
                },
            )
            self._flash_signature = signature
        except Exception:
            # Keep mode armed; next UI refresh retries automatically.
            self._flash_signature = None

    def stop_game_flash(self):
        """Remove injected visual overlay and disarm AUTO SYNC."""
        self._flash_mode = None
        self._flash_signature = None
        sid = str(getattr(self.bridge, 'active_game_sid', '') or '')
        ws = getattr(self.bridge, 'ws', None)
        if not sid or ws is None:
            return
        js = r"""
(() => {
  try {
    const x=document.getElementById('__roulette_ai_flash_root'); if(x)x.remove();
    const s=document.getElementById('__roulette_ai_flash_style'); if(s)s.remove();
    if(window.__rouletteAiFlashTimer){clearInterval(window.__rouletteAiFlashTimer);window.__rouletteAiFlashTimer=null;}
  } catch(_) {}
  return true;
})()
"""
        try:
            self.bridge.send(
                'Runtime.evaluate',
                {'expression':js,'returnByValue':True,'awaitPromise':True},
                session_id=sid,
                kind='manual_flash_off',
                context=None,
            )
        except Exception:
            pass

    def open_neighbor_helper(self, neighbor_count):
        """Manual helper window. No automated clicks/bets are performed."""
        data = self._current_neighbor_helper_data(neighbor_count)
        if not data:
            try:
                import tkinter.messagebox as messagebox
                messagebox.showinfo(
                    "Komşu Hazırla",
                    "Henüz hazır NET + YEDEK tahmini yok."
                )
            except Exception:
                pass
            return

        title = f"{neighbor_count} KOMŞU HAZIRLA"
        win = tk.Toplevel(self.root)
        win.title(title)
        win.configure(bg=self.BG)
        win.resizable(False, False)
        try:
            win.transient(self.root)
            win.attributes("-topmost", True)
        except Exception:
            pass

        top = tk.Frame(win, bg=self.PANEL)
        top.pack(fill="x", padx=8, pady=(8,4))

        tk.Label(
            top,
            text=title,
            font=("Segoe UI",12,"bold"),
            fg=self.GREEN,
            bg=self.PANEL,
        ).pack(anchor="w")

        centers_text = (
            f"NET {data['net']:02d}  •  YEDEK "
            + " / ".join(f"{x:02d}" for x in data["backups"])
        )
        tk.Label(
            top,
            text=centers_text,
            font=("Consolas",9,"bold"),
            fg=self.TEXT,
            bg=self.PANEL,
        ).pack(anchor="w", pady=(2,0))

        tk.Label(
            top,
            text=(
                f"BENZERSİZ KAPSAM: {len(data['unique'])}/37  •  "
                f"MANUEL YARDIMCI — OTOMATİK BAHİS YOK"
            ),
            font=("Segoe UI",8,"bold"),
            fg=self.MUTED,
            bg=self.PANEL,
        ).pack(anchor="w", pady=(2,4))

        # Per-center lines so user can see exactly what each NET/backup means.
        details = tk.Frame(win, bg=self.PANEL)
        details.pack(fill="x", padx=8, pady=(0,5))

        for i, center in enumerate(data["centers"]):
            prefix = "NET" if i == 0 else f"Y{i}"
            zone = data["by_center"][center]
            tk.Label(
                details,
                text=(
                    f"{prefix} {center:02d} → "
                    + " / ".join(f"{x:02d}" for x in zone)
                ),
                font=("Consolas",8,"bold"),
                fg=self.TEXT,
                bg=self.PANEL,
                anchor="w",
                justify="left",
            ).pack(fill="x", pady=1)

        # 0-36 manual number board; covered values are green.
        board = tk.Frame(win, bg=self.BG)
        board.pack(padx=8, pady=(2,6))

        covered = set(data["unique"])
        cols = 10
        for n in range(37):
            r, c = divmod(n, cols)
            is_hit = n in covered
            tk.Label(
                board,
                text=f"{n:02d}",
                width=4,
                height=2,
                font=("Consolas",9,"bold"),
                bg=self.GREEN if is_hit else self.PANEL2,
                fg="#07120a" if is_hit else self.MUTED,
                relief="flat",
                bd=0,
            ).grid(row=r, column=c, padx=2, pady=2)

        bottom = tk.Frame(win, bg=self.BG)
        bottom.pack(fill="x", padx=8, pady=(0,8))

        copy_btn = tk.Button(
            bottom,
            text="SAYILARI KOPYALA",
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,
            fg=self.TEXT,
            activebackground=self.PANEL2,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
        )
        copy_btn.config(
            command=lambda: self._copy_neighbor_numbers(
                data["unique"], copy_btn
            )
        )
        copy_btn.pack(side="left",fill="x",expand=True,padx=(0,3))

        tk.Button(
            bottom,
            text="KAPAT",
            command=win.destroy,
            font=("Segoe UI",8,"bold"),
            bg=self.PANEL2,
            fg=self.TEXT,
            activebackground=self.PANEL2,
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
        ).pack(side="left",fill="x",expand=True,padx=(3,0))

    def start_lobby_teach_ui(self):
        self.bridge.start_lobby_teaching()
        try:
            from tkinter import messagebox
            messagebox.showinfo(
                'Öğren Başlat',
                'Kayıt başladı.\n\n'
                'Şimdi tarayıcıda normal şekilde istediğin yolu SEN göster.\n'
                'Canlı Casino, aşağı kaydırma, Pragmatic, arama kutusuna yazı, Favoriler, masa... yolu normal şekilde göster.\n\n'
                'Masaya ulaştığında programdan ÖĞREN BİTİR\'e bas.\n'
                'Bu sırada otomatik hareket yok; SENİN yaptığın kaydırma da eğitim olarak kaydedilir.'
            )
        except Exception:
            pass

    def finish_lobby_teach_ui(self):
        ok,count=self.bridge.finish_lobby_teaching()
        try:
            from tkinter import messagebox
            messagebox.showinfo(
                'Öğren Bitir',
                (f'Öğretim kaydedildi: {count} işlem.\n'
                 'Sonraki açılışlarda program bu yolu kullanacak.')
                if ok else
                'Kaydedilecek işlem yok. Eski öğretim varsa korunuyor.'
            )
        except Exception:
            pass

    def start_learned_route_ui(self):
        ok=self.bridge.start_learned_route()
        try:
            from tkinter import messagebox
            if not ok:
                messagebox.showinfo(
                    "Yolu Başlat",
                    "Kayıtlı eğitim yolu yok. Önce ÖĞREN BAŞLAT ile yolu öğret."
                )
        except Exception:
            pass

    def start_table_scan_ui(self):
        threading.Thread(target=self.bridge.start_table_scan, daemon=True).start()

    def start_tab_walk_scan_ui(self):
        threading.Thread(
            target=lambda: self.bridge.start_tab_walk_scan(auto_cycle=True),
            daemon=True,
        ).start()

    def stop_table_scan_ui(self):
        threading.Thread(
            target=lambda: self.bridge.stop_table_scan("kullanıcı durdurdu"),
            daemon=True,
        ).start()

    def start_api_refresh_ui(self):
        threading.Thread(target=self.bridge.start_api_refresh_all, daemon=True).start()

    def start_api_teach_ui(self):
        self.bridge.start_manual_api_teach()
        try:
            from tkinter import messagebox
            messagebox.showinfo(
                "Masa API Öğren",
                "Masa bankası sıfırlandı.\n\n"
                "Şimdi tarayıcıda rulet masalarını tek tek sen aç.\n"
                "Program her açtığın Pragmatic masanın tableId/API bilgisini "
                "kaydedip SON500 verisini almaya çalışacak.\n\n"
                "Bitince TARAMAYI DURDUR düğmesine basabilirsin."
            )
        except Exception:
            pass

    def reset_lobby_teach_ui(self):
        self.bridge.reset_lobby_teaching()
        try:
            from tkinter import messagebox
            messagebox.showinfo(
                'Öğren Sıfırla',
                'Öğrenilmiş yol silindi. Tekrar ÖĞREN BAŞLAT ile gösterebilirsin.'
            )
        except Exception:
            pass

    def refresh(self):
        try:
            if str(self.root.state()) == "iconic":
                self.root.after(350, self.refresh)
                return
        except Exception:
            pass

        s = self.state.snapshot()

        if bool(s.get("restart_requested")) and not self._restart_in_progress:
            self._restart_in_progress = True
            self.exit_code = 77
            try:
                self.bridge.stop()
            except Exception:
                pass
            try:
                self.root.after(80, self.root.quit)
            except Exception:
                self.root.quit()
            return

        status_sig = (
            int(s.get("collector_refreshed", 0) or 0),
            str(s.get("status") or ""),
            str(s.get("source") or ""),
            str(s.get("table") or ""),
            str(s.get("direct_history_status") or ""),
            str(s.get("background_status") or ""),
            str(s.get("table_scan_status") or ""),
            str(s.get("autolobby_status") or ""),
            str(s.get("table500_source") or ""),
            str(s.get("table_long_source") or ""),
            str(s.get("archive_source") or ""),
            bool(s.get("chrome")),
            bool(s.get("seen")),
        )
        core_render_sig = (
            tuple(s.get("history") or ()),
            s.get("predicted"),
            int((s.get("validation") or {}).get("trials", 0) or 0),
            int(s.get("archive_count", 0) or 0),
            int(s.get("archive_tables", 0) or 0),
            int(s.get("table500_count", 0) or 0),
            int(s.get("table_long_count", 0) or 0),
            int(s.get("live_memory_count", 0) or 0),
            str(s.get("pragmatic_table_id") or ""),
            bool(s.get("seen")),
        )

        if status_sig != getattr(self, "_last_status_sig", None):
            self._last_status_sig = status_sig
            try:
                self.collector_line.config(
                    text=(
                        str(s.get("background_status") or "ÇOKLU TOPLAYICI: keşif bekleniyor")
                        + "\n"
                        + str(s.get("table_scan_status") or "MASA TARAMA: hazır")
                    ),
                    fg=self.GREEN if int(s.get("collector_refreshed", 0) or 0) else self.YELLOW,
                )
            except Exception:
                pass
            try:
                connected=bool(s.get("chrome"))
                self.chrome_link_line.config(
                    text=(
                        "CHROME: BAĞLI ✓ • öğrenilen yol çalışabilir"
                        if connected
                        else "CHROME: BEKLİYOR • program otomatik bağlanmayı deniyor"
                    ),
                    fg=self.GREEN if connected else self.YELLOW,
                )
            except Exception:
                pass
            try:
                self.lobby_teach_line.config(
                    text=str(s.get("autolobby_status") or "ÖĞREN: --"),
                    fg=(
                        self.GREEN
                        if "TAMAM" in str(s.get("autolobby_status","")) or "MASA AÇIK" in str(s.get("autolobby_status",""))
                        else self.YELLOW
                        if "BEKLİYOR" in str(s.get("autolobby_status","")) or "GEREKLİ" in str(s.get("autolobby_status",""))
                        else self.BLUE
                    ),
                )
            except Exception:
                pass
            self.status.config(text=s["status"])
            self.status.config(
                fg=self.GREEN if s["seen"]
                else self.BLUE if s["chrome"]
                else self.YELLOW
            )
            tid=s.get("pragmatic_table_id") or "-"
            theme=s.get("theme_code") or "-"
            game_id=s.get("operator_game_id") or "-"
            self.archive_line.config(text=(
                f"{s.get('direct_history_status','PRAGMATIC DIRECT: bekleniyor')}\n"
                f"MASA KİMLİĞİ: {tid}\n"
                f"OPERATOR GAME: {game_id} • TEMA: {theme}\n"
                f"{s.get('table500_source','SON500: bekleniyor')}\n"
                f"{s.get('table_long_source','UZUN MASA ARŞİVİ: bekleniyor')}\n"
                f"{s.get('archive_source','ORTAK HAVUZ: bekleniyor')}\n"
                f"{s.get('background_status','MASA BANKALARI: bekleniyor')}\n"
                f"CANLI HAFIZA: {s.get('live_memory_count',0)} spin\n"
                f"CANLI SYNC: {s.get('source','-')}\n"
                f"SON500 LIVE: SADECE DOĞRULANMIŞ +YENİ\n"
                f"PUANLAMA: {s.get('score_error_status','OK')}\n"
                f"{s.get('autorecover_status','AUTO KURTARMA: HAZIR')}"
            ))
            table = f" • {s['table']}" if s["table"] else ""
            self.source.config(text=f"Kaynak: {s['source']}{table}")

        if core_render_sig == getattr(self, "_last_render_sig", None):
            try:
                self._refresh_game_flash(force=False)
            except Exception:
                pass
            self.root.after(250, self.refresh)
            return
        self._last_render_sig = core_render_sig

        # V2.8.12: if K1/K2 flash is armed, keep it synced to the
        # CURRENT prediction. Signature check prevents needless reinjection.
        try:
            self._refresh_game_flash(force=False)
        except Exception:
            pass

        h = s["history"]
        watch = s["watch"]
        self.top_last_line.config(text=f"SON: {h[0]}" if h else "SON: --")

        if watch:
            predicted = s.get("predicted")
            conf = float(s.get("model_confidence") or 0.0)
            share = float(s.get("model_share") or 0.0)

            self.main_pick.config(
                text=str(predicted if predicted is not None else watch[0][0])
            )
            self.model_share.config(text=f"MODEL PAYI: %{share:.2f}")

            quality = s.get("prediction_quality","ZAYIF")
            wf_info = s.get("walkforward") or {}
            if wf_info.get("qualified"):
                wf_edge_val = float(wf_info.get("edge_pp", 0.0) or 0.0)
                wf_label = f"GÜÇLÜ (+{wf_edge_val:.1f}p EDGE)"
            elif float(wf_info.get("edge_pp", -1.0) or -1.0) >= 0.0 and int(wf_info.get("trials", 0) or 0) >= 40:
                wf_label = "ORTA"
            else:
                wf_label = quality
            stage = s.get("learning_stage","TEMKİNLİ ÖĞRENME")
            self.quality_line.config(
                text=f"VERİ MODU: KAYNAKLAR KAYDEDİLİYOR • WF {wf_label}",
                fg=self.GREEN,
            )
            cov = s.get("coverage") or {}
            self.coverage_line.config(text=(
                f"TEORİK KAPSAMA • 1 sayı %{float(cov.get('single',0)):.1f} • "
                f"5 aday %{float(cov.get('top5',0)):.1f} • "
                f"bölge %{float(cov.get('region',0)):.1f}"
            ))
            self.stage_line.config(text=f"ÖĞRENME AŞAMASI: {stage}")

            src_now = s.get("source_answers") or {}
            net = s.get("net_pick") or {}

            name_map = {
                "LOCAL": "CANLI",
                "TABLE500": "SON500",
                "TABLE_LONG": "UZUN",
                "ARCHIVE": "ORTAK",
                "MODEL_RECENCY": "RECENCY",
                "MODEL_WHEEL": "WHEEL",
                "MODEL_TRANSITION": "TRANSITION",
                "MODEL_WEB": "LONG-M",
                "BLEND": "BLEND",
                "ENSEMBLE": "ENSEMBLE",
            }

            family_supporters = list(net.get("family_supporters") or [])
            family_count = int(net.get("family_count",0) or 0)
            family_picks = net.get("family_picks") or {}
            leader_family = str(net.get("leader_family") or "-")

            self.action_line.config(
                text=(
                    "AİLE SEÇEN: " + " + ".join(family_supporters)
                    if family_supporters
                    else f"AİLE LİDERİ: {leader_family}"
                ),
                fg=self.GREEN if family_supporters else self.BLUE,
            )

            picks_text = " • ".join(
                f"{fam} {int(num):02d}"
                for fam,num in family_picks.items()
            )
            net_signal = float(net.get("signal_score",0.0) or 0.0)
            self.confidence.config(
                text=(
                    f"NET SİNYAL: %{net_signal:.0f} • AİLE DESTEĞİ: {len(family_supporters)}/{family_count}"
                    + (f" • {picks_text}" if picks_text else "")
                    if family_count
                    else "NET SİNYAL: -- • AİLE DESTEĞİ: veri bekleniyor"
                )
            )
            tid=s.get("pragmatic_table_id") or "-"
            theme=s.get("theme_code") or "-"
            game_id=s.get("operator_game_id") or "-"
            self.archive_line.config(text=(
                f"{s.get('direct_history_status','PRAGMATIC DIRECT: bekleniyor')}\n"
                f"MASA KİMLİĞİ: {tid}\n"
                f"OPERATOR GAME: {game_id} • TEMA: {theme}\n"
                f"{s.get('table500_source','SON500: bekleniyor')}\n"
                f"{s.get('table_long_source','UZUN MASA ARŞİVİ: bekleniyor')}\n"
                f"{s.get('archive_source','ORTAK HAVUZ: bekleniyor')}\n"
                f"{s.get('background_status','MASA BANKALARI: bekleniyor')}\n"
                f"CANLI HAFIZA: {s.get('live_memory_count',0)} spin\n"
                f"CANLI SYNC: {s.get('source','-')}\n"
                f"SON500 LIVE: SADECE DOĞRULANMIŞ +YENİ\n"
                f"PUANLAMA: {s.get('score_error_status','OK')}\n"
                f"{s.get('autorecover_status','AUTO KURTARMA: HAZIR')}"
            ))

            sc = s.get("source_consensus") or {}
            src_now = s.get("source_answers") or {}

            labels = {
                "LOCAL": "CANLI",
                "TABLE500": "SON500",
                "TABLE_LONG": "UZUN",
                "ARCHIVE": "ORTAK",
                "MODEL_RECENCY": "RECENCY",
                "MODEL_WHEEL": "WHEEL",
                "MODEL_TRANSITION": "TRANSITION",
                "MODEL_WEB": "LONG-M",
            }

            answer_rows = []
            for key in (
                "LOCAL","TABLE500","TABLE_LONG","ARCHIVE",
                "MODEL_RECENCY","MODEL_WHEEL","MODEL_TRANSITION","MODEL_WEB"
            ):
                sd = src_now.get(key) or {}
                if sd.get("top1") is None:
                    continue
                top5s = [int(x) for x in (sd.get("top5") or [])[:5]]
                answer_rows.append(
                    f"{labels.get(key,key):10s} → {int(sd['top1']):02d}  | T5 "
                    + "/".join(f"{n:02d}" for n in top5s)
                )

            self.consensus_line.config(
                text=(
                    "ANLIK CEVAPLAR\n"
                    + ("\n".join(answer_rows) if answer_rows else "veri bekleniyor")
                ),
                fg=self.GREEN,
            )

            perf_rows = []
            exact_profiles = net.get("exact_profiles") or {}
            exact_labels = {
                "LOCAL":"CANLI",
                "TABLE500":"SON500",
                "TABLE_LONG":"UZUN",
                "ARCHIVE":"ORTAK",
                "MODEL_RECENCY":"RECENCY",
                "MODEL_WHEEL":"WHEEL",
                "MODEL_TRANSITION":"TRANSITION",
                "MODEL_WEB":"LONG-M",
            }

            for key in (
                "LOCAL","TABLE500","TABLE_LONG","ARCHIVE",
                "MODEL_RECENCY","MODEL_WHEEL",
                "MODEL_TRANSITION","MODEL_WEB"
            ):
                pr = exact_profiles.get(key) or {}
                if not pr:
                    continue
                n100,e100 = int(pr.get("n100",0)),int(pr.get("e100",0))
                n300,e300 = int(pr.get("n300",0)),int(pr.get("e300",0))
                nall,eall = int(pr.get("nall",0)),int(pr.get("eall",0))
                p100 = e100/n100*100.0 if n100 else 0.0
                p300 = e300/n300*100.0 if n300 else 0.0
                pall = eall/nall*100.0 if nall else 0.0
                gate=float(pr.get("gate",1.0) or 1.0)
                gstate=str(pr.get("state","STABİL") or "STABİL")
                perf_rows.append(
                    f"{exact_labels[key]:10s} "
                    f"R100 {e100}/{n100} %{p100:.1f} • "
                    f"R300 %{p300:.1f} • ALL %{pall:.1f} • "
                    f"{gstate} x{gate:.2f}"
                )

            family_line = " • ".join(
                f"{fam}→{int(num):02d}"
                for fam,num in (net.get("family_picks") or {}).items()
            )

            self.weight_line.config(
                text=(
                    "NET EXACT YARIŞI • Top5 ağırlıkta YOK\n"
                    + ("\n".join(perf_rows) if perf_rows else "henüz exact profil yok")
                    + ("\nAİLELER: " + family_line if family_line else "")
                    + "\nTek sayı rastgele taban: %2.70"
                )
            )

            maxs = watch[0][1] or 1e-9
            ranked = [n for n, _score in watch]
            top3 = ranked[:3]
            backup = ranked[3:5]
            side = ranked[1:5] if len(ranked) > 1 else []

            candidate_prefix = "YEDEKLER (KAYIT): "
            self.instant_line.config(
                text=candidate_prefix + "  •  ".join(str(n) for n in side)
                if side else candidate_prefix + "--"
            )
            hb = s.get("history_brain") or {}
            wh = s.get("web_history") or {}
            exact_top = hb.get("exact_top") or []
            pair_top = hb.get("pair_top") or []
            web_exact_pct = wh.get("exact_top_pct") or []
            web_pair_pct = wh.get("pair_top_pct") or []
            web_tables = int(wh.get("tables", 0) or s.get("archive_tables", 0) or 0)
            web_spins = int(wh.get("spins", 0) or s.get("archive_count", 0) or 0)
            web_exact_obs = int(wh.get("exact_obs", 0) or 0)
            web_pair_obs = int(wh.get("pair_obs", 0) or 0)
            cur_num = h[0] if h else None
            prev_num = h[1] if len(h) >= 2 else None

            exact_txt = " ".join(f"{n}({c})" for n,c in exact_top[:3]) or "-"
            pair_txt = " ".join(f"{n}({c})" for n,c in pair_top[:3]) or "-"
            web_pct_txt = (
                " • ".join(f"{int(n):02d} %{pct:.1f}({cnt}x)" for n, cnt, pct in web_exact_pct[:5])
                if web_exact_pct
                else "-"
            )
            web_pair_txt = (
                " • ".join(f"{int(n):02d} %{pct:.1f}({cnt}x)" for n, cnt, pct in web_pair_pct[:3])
                if web_pair_pct
                else "-"
            )

            if cur_num is not None and web_exact_pct:
                self.global_pool_line.config(
                    text=(
                        f"ORTAK HAVUZ ({web_tables} masa • {web_spins} spin) • "
                        f"{cur_num} SONRASI ({web_exact_obs}x):\n"
                        f"{web_pct_txt}"
                    ),
                    fg=self.YELLOW,
                )
            else:
                self.global_pool_line.config(
                    text=f"ORTAK HAVUZ: {web_tables} masa • {web_spins} spin",
                    fg=self.MUTED,
                )

            pair_label = f"{prev_num}→{cur_num}" if (prev_num is not None and cur_num is not None) else "çift"
            self.history_brain_line.config(text=(
                f"Yerel geçiş: {exact_txt}  •  Çift desen: {pair_txt}\n"
                f"Tüm masalar ({web_tables} masa/{web_spins} spin) {cur_num if cur_num is not None else '-'} sonrası ({web_exact_obs}x):\n"
                f"  {web_pct_txt}\n"
                f"Ortak çift ({pair_label}, {web_pair_obs}x): {web_pair_txt}"
            ))

            val = s.get("validation") or {}
            trials = int(val.get("trials",0))
            exact = int(val.get("exact",0))
            top5 = int(val.get("top5",0))
            neighbor5 = int(val.get("neighbor5",0))
            region_hits = int(val.get("region",0))

            if trials:
                side4 = int(val.get("side4", 0))
                self.validation_line.config(text=(
                    f"NET {exact}/{trials} %{exact/trials*100:4.1f}  •  "
                    f"YEDEK-4 {side4}/{trials} %{side4/trials*100:4.1f}\n"
                    f"NET+YEDEK TOP5 {top5}/{trials} %{top5/trials*100:4.1f}  •  "
                    f"KOMŞU {neighbor5}/{trials} %{neighbor5/trials*100:4.1f}  •  "
                    f"BÖLGE {region_hits}/{trials} %{region_hits/trials*100:4.1f}"
                ))
            else:
                self.validation_line.config(
                    text="Henüz doğrulanan tahmin yok • yeni spin bekleniyor."
                )

            r20 = s.get("recent20") or {}
            if int(r20.get("trials",0)):
                self.recent20_line.config(text=(
                    f"SON {int(r20.get('trials',0)):2d}: "
                    f"Tam %{r20.get('exact',0):4.1f} • "
                    f"Top5 %{r20.get('top5',0):4.1f} • "
                    f"Komşu %{r20.get('neighbor5',0):4.1f} • "
                    f"Bölge %{r20.get('region',0):4.1f}"
                ))
            else:
                self.recent20_line.config(text="SON 20: veri bekleniyor")

            wf = s.get("walkforward") or {}
            wf_trials = int(wf.get("trials",0) or 0)
            if wf_trials:
                wf_rate = float(wf.get("top5_rate",0.0) or 0.0)
                wf_base = float(wf.get("top5_base",5/37*100) or 0.0)
                wf_low = float(wf.get("top5_low90",0.0) or 0.0)
                wf_edge = float(wf.get("edge_pp",0.0) or 0.0)
                wf_ok = bool(wf.get("qualified",False))
                experts = wf.get("experts") or {}
                erows = []
                for name, shortn in (("RECENCY","R"),("WHEEL","W"),("TRANSITION","T"),("LONG","L")):
                    est = experts.get(name,{})
                    if int(est.get("trials",0) or 0):
                        erows.append(f"{shortn} %{float(est.get('top5_rate',0)):.1f}")
                self.walkforward_line.config(
                    text=(
                        f"NET MOD: EXACT+AİLE • WALK-FORWARD {wf_trials}: Top5 %{wf_rate:.1f} • "
                        f"taban %{wf_base:.1f} • alt90 %{wf_low:.1f} • "
                        f"edge {wf_edge:+.1f}p • {'EDGE VAR' if wf_ok else 'EDGE YOK'}"
                        + ("\nAlt modeller: " + "  ".join(erows) if erows else "")
                    ),
                    fg=self.GREEN if wf_ok else self.RED,
                )
            else:
                self.walkforward_line.config(
                    text="WALK-FORWARD: aynı masa uzun arşivi büyüyor",
                    fg=self.BLUE,
                )

            ll = s.get("locked_live") or {}
            lprof = ll.get("profiles") or {}
            la = lprof.get("all") or {}
            ln = int(la.get("trials",0) or 0)
            if ln:
                lines = [
                    f"LOCKED LIVE {ln}/500{' • DONDU' if ll.get('frozen') else ''}: "
                    f"NET %{float(la.get('exact_rate',0)):.1f} • TOP5 %{float(la.get('top5_rate',0)):.1f}",
                    f"K1 %{float(la.get('k1_rate',0)):.1f} / taban %{float(la.get('k1_base',0)):.1f} "
                    f"= {float(la.get('k1_edge',0)):+.1f}p • "
                    f"K2 %{float(la.get('k2_rate',0)):.1f} / taban %{float(la.get('k2_base',0)):.1f} "
                    f"= {float(la.get('k2_edge',0)):+.1f}p",
                ]
                win_parts=[]
                for tag in ("50","100","200"):
                    pr=lprof.get(tag) or {}
                    pn=int(pr.get("trials",0) or 0)
                    if pn:
                        win_parts.append(
                            f"{tag}: K1 {float(pr.get('k1_edge',0)):+.1f}p "
                            f"K2 {float(pr.get('k2_edge',0)):+.1f}p"
                        )
                if win_parts:
                    lines.append("SON " + " • ".join(win_parts))
                self.locked_line.config(
                    text="\n".join(lines),
                    fg=self.GREEN if ln >= 100 else self.YELLOW,
                )
            else:
                self.locked_line.config(
                    text="LOCKED LIVE 0/500 • V2.9'dan sonraki gerçek turlar ayrı kaydedilecek",
                    fg=self.YELLOW,
                )

            risk = s.get("risk_profile") or {}

            def risk_text(row):
                row = row or {}
                label = str(row.get("label") or "-")
                trials_r = int(row.get("trials", 0) or 0)
                base = float(row.get("random_hit_pct", 0.0) or 0.0)
                be = float(row.get("breakeven_hit_pct", 0.0) or 0.0)
                cov_r = float(row.get("avg_coverage", 0.0) or 0.0)
                if trials_r:
                    hit = float(row.get("hit_rate_pct", 0.0) or 0.0)
                    roi = float(row.get("roi_pct", 0.0) or 0.0)
                    low = float(row.get("wilson_low90_pct", 0.0) or 0.0)
                    return (
                        f"{label}: K {cov_r:.1f}/37 • %{hit:.1f} "
                        f"(alt90 %{low:.1f}) • BE %{be:.1f} • ROI {roi:+.1f}% • "
                        f"{row.get('status','')}"
                    )
                return f"{label}: K {cov_r:.1f}/37 • taban %{base:.1f} • BE %{be:.1f}"

            rnet = risk.get("net") or {}
            rtop5 = risk.get("top5") or {}
            rk1 = risk.get("k1") or {}
            rk2 = risk.get("k2") or {}
            risk_lines = [
                "RİSK/EV: düz sayı 35:1 • rastgele uzun vade ROI -%2.70",
                risk_text(rnet),
                risk_text(rtop5),
            ]
            if int(rk1.get("trials", 0) or 0) or int(rk2.get("trials", 0) or 0):
                risk_lines.append(risk_text(rk1))
                risk_lines.append(risk_text(rk2))
            else:
                risk_lines.append("K1/K2: canlı paket ROI için doğrulanmış tur bekleniyor")

            statuses = [
                str(row.get("status") or "")
                for row in (rnet, rtop5, rk1, rk2)
                if int(row.get("trials", 0) or 0)
            ]
            self.risk_line.config(
                text="\n".join(risk_lines),
                fg=(
                    self.GREEN if any("KANITLI" in x for x in statuses)
                    else self.RED if statuses and all("TABAN ALTI" in x for x in statuses)
                    else self.YELLOW
                ),
            )

            w = s.get("weights") or {}
            learn_summary = (
                f"Öğrenme: {s.get('learning_spins',0)} spin • "
                f"R %{w.get('RECENCY',0)*100:.0f}  "
                f"W %{w.get('WHEEL',0)*100:.0f}  "
                f"T %{w.get('TRANSITION',0)*100:.0f}  "
                f"O %{w.get('WEB',0)*100:.0f}"
            )
            sh = s.get("source_hits") or {}
            src_perf = []
            for name in SOURCE_NAMES:
                st = sh.get(name, {})
                n = int(st.get("trials",0) or 0)
                if n:
                    src_perf.append(
                        f"{name}:T5 %{int(st.get('top5',0))/n*100:.0f}"
                    )
            extra_weight_txt = "\n" + learn_summary
            if src_perf:
                extra_weight_txt += "\nKaynak T5: " + " • ".join(src_perf)
            current_text = self.weight_line.cget("text")
            self.weight_line.config(text=current_text + extra_weight_txt)

            eh = s.get("expert_hits") or {}
            expert_rows = []
            short = {
                "RECENCY": "R",
                "WHEEL": "W",
                "TRANSITION": "T",
                "WEB": "ORTAK-M",
            }
            for name in EXPERT_NAMES:
                st = eh.get(name, {})
                n = int(st.get("trials",0))
                if n:
                    top5p = st.get("top5",0) / n * 100.0
                    neighp = st.get("neighbor5",0) / n * 100.0
                    exactp = st.get("exact",0) / n * 100.0
                    expert_rows.append(
                        f"{short[name]}: Tm {exactp:.1f}%  T5 {top5p:.1f}%  K {neighp:.1f}%"
                    )
                else:
                    expert_rows.append(f"{short[name]}: veri bekleniyor")
            self.expert_line.config(text="\n".join(expert_rows))
        else:
            self.main_pick.config(text="--")
            self.coverage_line.config(text="TEORİK KAPSAMA: --")
            self.action_line.config(text="NET SAYI HESAPLANIYOR", fg=self.BLUE)
            self.global_pool_line.config(
                text=str(s.get("archive_source") or "ORTAK HAVUZ: masa verileri bekleniyor"),
                fg=self.MUTED,
            )
            self.archive_line.config(text="ARŞİV: dosya yok")
            self.consensus_line.config(text="KAYNAK UYUMU: veri bekleniyor")
            self.instant_line.config(text="YEDEKLER (KAYIT): --")
            self.history_brain_line.config(text="KAYITLI GEÇMİŞ: veri bekleniyor")
            self.reserve_line.config(text="YEDEK: --")
            self.confidence.config(text="KAYNAK UYUMU: --")
            self.model_share.config(text="MODEL PAYI: --")
            self.quality_line.config(text="VERİ MODU: KAYNAKLAR KAYDEDİLİYOR", fg=self.GREEN)
            self.stage_line.config(text="ÖĞRENME AŞAMASI: --")
            self.watch_list.config(text="Rulet masasını aç")
            self.validation_line.config(text="Henüz veri yok.")
            self.recent20_line.config(text="")
            self.walkforward_line.config(text="WALK-FORWARD: veri bekleniyor", fg=self.BLUE)
            self.locked_line.config(text="LOCKED LIVE 0/500 • yeni tur bekleniyor", fg=self.YELLOW)
            self.risk_line.config(text="RİSK/EV: veri bekleniyor", fg=self.YELLOW)
            self.weight_line.config(text="")
            self.expert_line.config(text="")

        fair = s.get("fairness") or {}
        if fair:
            fstatus = fair.get("status","VERİ TOPLANIYOR")
            fconf = fair.get("confidence","ÇOK DÜŞÜK")
            fn = int(fair.get("n",0))
            dev = fair.get("deviation") or {}
            rep = fair.get("repeat") or {}
            sectors = fair.get("sectors") or {}

            self.fairness_status.config(
                text=f"ADİLLİK / SAPMA: {fstatus} • {fn} spin"
            )
            self.fairness_status.config(
                fg=self.GREEN if fstatus == "BELİRGİN SAPMA YOK"
                else self.YELLOW if fstatus in ("VERİ TOPLANIYOR","İZLE")
                else self.RED
            )

            max_sector = ""
            if sectors:
                name, sv = max(
                    sectors.items(),
                    key=lambda kv: abs(float(kv[1].get("diff",0.0)))
                )
                shortn = {
                    "VOISINS DU ZÉRO": "V",
                    "TIERS DU CYLINDRE": "T",
                    "ORPHELINS": "O",
                }.get(name, name)
                max_sector = (
                    f" • Bölge {shortn} fark {float(sv.get('diff',0.0)):+.1f}p"
                )

            self.fairness_line.config(text=(
                f"Güven: {fconf} • Dağılım oranı {float(dev.get('ratio',0.0)):.2f}\n"
                f"Tekrar {float(rep.get('rate',0.0)):.1f}% "
                f"(taban {float(rep.get('baseline',100/37)):.1f}%)"
                f"{max_sector}\n"
                f"Not: Bu panel hile kanıtlamaz; yalnızca istatistiksel sapmayı izler."
            ))
        else:
            self.fairness_status.config(text="ADİLLİK / SAPMA: veri bekleniyor", fg=self.BLUE)
            self.fairness_line.config(text="")

        region_name = s.get("region_name")
        region_conf = float(s.get("region_confidence") or 0.0)
        region_scores = s.get("region_scores") or {}
        region_features = s.get("region_features") or {}
        neigh = s.get("neighbor_zone") or []

        if region_name:
            v = round(region_scores.get("VOISINS DU ZÉRO",0.0), 1)
            t = round(region_scores.get("TIERS DU CYLINDRE",0.0), 1)
            o = round(100.0 - v - t, 1)

            self.region_main.config(text=region_name)
            self.main_region_line.config(text=f"NET SAYI BÖLGESİ: {region_of_number(int(s.get('predicted',0)))}")
            self.region_conf.config(
                text=f"BÖLGE MODEL SKORU: %{region_conf:.1f}"
            )
            self.region_breakdown.config(text=(
                f"VOISINS   %{v:4.1f}\n"
                f"TIERS     %{t:4.1f}\n"
                f"ORPHELINS %{o:4.1f}"
            ))

            f = region_features.get(region_name, {})
            reasons = []
            if float(f.get("recency_ratio",0.0)) >= 1.15:
                reasons.append("son sonuç yoğunluğu yüksek")
            if float(f.get("momentum_ratio",0.0)) >= 1.20:
                reasons.append("son 5 spin momentumu güçlü")
            if float(f.get("neighbor_overlap",0.0)) >= 0.60:
                reasons.append("komşu sayı kümelenmesi güçlü")
            if not reasons:
                reasons.append("toplam geçmiş skoru önde")

            if hasattr(self, "region_reason"):
                self.region_reason.config(
                    text="Mantık: " + " • ".join(reasons)
                )

            self.neighbor_zone.config(
                text="Çark komşuları: " + " - ".join(str(x) for x in neigh)
                if neigh else "Çark komşuları: -"
            )
        else:
            self.region_main.config(text="--")
            self.main_region_line.config(text="BÖLGE: --")
            self.region_conf.config(text="BÖLGE MODEL SKORU: --")
            self.region_breakdown.config(text="")
            if hasattr(self, "region_reason"):
                self.region_reason.config(text="")
            self.neighbor_zone.config(text="Çark komşuları: -")

        pending_cmp = s.get("pending_compare") or {}
        if pending_cmp:
            pmain = pending_cmp.get("predicted")
            pside = pending_cmp.get("side4") or []
            source_count = int(pending_cmp.get("source_count",0) or 0)
            current_batch = int(s.get("comparison_batch_count",0) or 0)
            next_no = 1 if current_batch >= 12 else current_batch + 1

            self.pending_compare_line.config(
                text=(
                    f"BEKLEYEN #{next_no:02d} • NET {int(pmain):02d} • YEDEK "
                    + "/".join(f"{int(x):02d}" for x in pside)
                    + f" • {source_count} kaynak/model kaydediliyor\n"
                    "Yeni sonuç geldiğinde tüm kaynaklar ayrı ayrı puanlanacak."
                ),
                fg=self.BLUE,
            )
        else:
            self.pending_compare_line.config(text="BEKLEYEN TAHMİN: --")

        cmp_rows = s.get("comparison_records") or []
        if cmp_rows:
            ana_hits = sum(
                1 for r in cmp_rows
                if str(r.get("compare_result","")) in ("ANA","ORTAK")
            )
            yan_hits = sum(
                1 for r in cmp_rows
                if str(r.get("compare_result","")) in ("YAN","ADAY")
            )
            misses = sum(
                1 for r in cmp_rows
                if str(r.get("compare_result","")) in ("KAÇTI","DIŞI")
            )

            rows = [
                f"SERİ {len(cmp_rows)}/12 • NET {ana_hits} • YEDEK {yan_hits} • DIŞI {misses}"
            ]

            for i, r in enumerate(cmp_rows, 1):
                try:
                    main_n = int(r.get("predicted"))
                    actual_n = int(r.get("actual"))
                except Exception:
                    continue

                side_nums = []
                for x in r.get("side4_numbers", []) or []:
                    try:
                        n = int(x)
                        if 0 <= n <= 36:
                            side_nums.append(n)
                    except Exception:
                        pass
                side_nums = side_nums[:4]

                result = str(r.get("compare_result") or "DIŞI")

                if result in ("ANA","ORTAK"):
                    result_txt = "NET ✓"
                elif result in ("YAN","ADAY"):
                    result_txt = "YEDEK ✓"
                else:
                    result_txt = "DIŞI"

                side_txt = "/".join(f"{n:02d}" for n in side_nums) or "--"

                src_round = r.get("source_round") or {}
                exact_src = []
                top5_src = []
                short_src = {
                    "LOCAL":"C",
                    "TABLE500":"500",
                    "TABLE_LONG":"U",
                    "MODEL_RECENCY":"R",
                    "MODEL_WHEEL":"W",
                    "MODEL_TRANSITION":"T",
                    "MODEL_WEB":"L",
                }
                for skey, sval in src_round.items():
                    lab = short_src.get(skey, skey)
                    if str(sval.get("result","")) == "TAM":
                        exact_src.append(lab)
                    elif str(sval.get("result","")) == "TOP5":
                        top5_src.append(lab)

                source_hit_txt = ""
                if exact_src:
                    source_hit_txt += " • K:TAM " + ",".join(exact_src)
                if top5_src:
                    source_hit_txt += " • K:T5 " + ",".join(top5_src)

                rows.append(
                    f"{i:02d} | NET {main_n:02d} | "
                    f"YEDEK {side_txt} | "
                    f"ÇIKAN {actual_n:02d} | {result_txt}"
                    + source_hit_txt
                )

            # New V2.7.8+ rows also contain per-source TAM/TOP5 results.
            # Older carried-over rows remain basic ORTAK/ADAY comparisons.
            self.compare_history_line.config(text="\n".join(rows))
        else:
            self.compare_history_line.config(
                text="Henüz doğrulanmış tahmin yok • yeni spin bekleniyor."
            )

        # MAIN SCREEN: result of LAST completed round.
        # Current NET number in the center is for the NEXT round.
        last_k1 = s.get("last_neighbor1_package")
        if isinstance(last_k1, dict):
            self.k1_main_result.config(
                text="KAZANDI" if last_k1.get("won") else "KAYBETTİ",
                fg=self.GREEN if last_k1.get("won") else self.RED,
            )
        else:
            self.k1_main_result.config(text="BEKLİYOR",fg=self.MUTED)

        last_k2 = s.get("last_neighbor2_package")
        if isinstance(last_k2, dict):
            self.k2_main_result.config(
                text="KAZANDI" if last_k2.get("won") else "KAYBETTİ",
                fg=self.GREEN if last_k2.get("won") else self.RED,
            )
        else:
            self.k2_main_result.config(text="BEKLİYOR",fg=self.MUTED)

        # 1 KOMŞU TAB: left 1 + center + right 1 = 3 numbers per center.
        nb1_stats = s.get("neighbor1_stats") or {}
        nb1_trials = int(nb1_stats.get("trials",0) or 0)
        nb1_net = int(nb1_stats.get("net_hits",0) or 0)
        nb1_backup = int(nb1_stats.get("backup_hits",0) or 0)
        nb1_any = int(nb1_stats.get("any_hits",0) or 0)
        nb1_multi = int(nb1_stats.get("multi_hits",0) or 0)
        nb1_cov = float(nb1_stats.get("avg_coverage",0.0) or 0.0)

        if nb1_trials:
            nb1_random_cover_pct = nb1_cov / 37.0 * 100.0
            nb1_actual_any_pct = nb1_any / nb1_trials * 100.0
            self.neighbor1_summary.config(
                text=(
                    f"K1 TOPLAM {nb1_any}/{nb1_trials} %{nb1_actual_any_pct:.1f}\n"
                    f"NET katkı {nb1_net} • YEDEK katkı {nb1_backup} • "
                    f"ÇOKLU {nb1_multi}\n"
                    f"ORT. KAPSAM {nb1_cov:.1f}/37 • "
                    f"KAPSAM TABANI ~%{nb1_random_cover_pct:.1f}"
                )
            )
        else:
            self.neighbor1_summary.config(text="Henüz 1 komşu istatistiği yok.")

        pending_nb1 = s.get("pending_compare") or {}
        if pending_nb1:
            net1 = int(pending_nb1.get("predicted",0) or 0)
            backups1 = [int(x) for x in (pending_nb1.get("side4") or [])[:4]]
            centers1 = [net1] + backups1
            coverage1 = set()
            for c in centers1:
                coverage1.update(int(x) for x in wheel_neighbors(c,1))

            cur1 = int(s.get("neighbor1_batch_count",0) or 0)
            next1 = 1 if cur1 >= 12 else cur1 + 1

            self.neighbor1_pending.config(
                text=(
                    f"BEKLEYEN #{next1:02d} • NET {net1:02d} K1 • "
                    f"Y " + "/".join(f"{x:02d}" for x in backups1)
                    + f" K1 • KAPSAM {len(coverage1)}/37"
                )
            )
        else:
            self.neighbor1_pending.config(text="BEKLEYEN 1 KOMŞU OYUNU: --")

        nb1_rows = s.get("neighbor1_records") or []
        if nb1_rows:
            nb1_hit_count = sum(
                1 for r in nb1_rows if r.get("any_neighbor_hit")
            )
            nb1_lines = [
                f"SERİ {len(nb1_rows)}/12 • K1 TUTTU {nb1_hit_count} • "
                f"DIŞI {len(nb1_rows)-nb1_hit_count}"
            ]

            for i,r in enumerate(nb1_rows,1):
                net1 = int(r.get("net",0) or 0)
                backups1 = [int(x) for x in (r.get("backups") or [])[:4]]
                btxt1 = "/".join(f"{x:02d}" for x in backups1) or "--"
                actual1 = int(r.get("actual",0) or 0)
                hitc1 = [int(x) for x in (r.get("hit_centers") or [])]
                cov1 = int(r.get("unique_coverage",0) or 0)
                result1 = str(r.get("result") or "DIŞI")

                if result1 == "NET K1":
                    rtxt1 = "NET K1 ✓"
                elif result1 == "YEDEK K1":
                    rtxt1 = "YEDEK K1 ✓"
                else:
                    rtxt1 = "DIŞI"

                multi1 = ""
                if len(hitc1) >= 2:
                    multi1 = " • ÇOKLU:" + ",".join(
                        f"{x:02d}" for x in hitc1
                    )

                nb1_lines.append(
                    f"{i:02d} | N {net1:02d} K1 | "
                    f"Y {btxt1} K1 | "
                    f"ÇIKAN {actual1:02d} | {rtxt1} | K {cov1}/37"
                    + multi1
                )

            self.neighbor1_history.config(text="\n".join(nb1_lines))
        else:
            self.neighbor1_history.config(text="Yeni gerçek sonuç bekleniyor.")

        # KOMŞU TAB • requested scenario: every displayed center is played with 2 neighbors.
        nb_stats = s.get("neighbor_stats") or {}
        nb_trials = int(nb_stats.get("trials",0) or 0)
        nb_net = int(nb_stats.get("net_hits",0) or 0)
        nb_backup = int(nb_stats.get("backup_hits",0) or 0)
        nb_any = int(nb_stats.get("any_hits",0) or 0)
        nb_multi = int(nb_stats.get("multi_hits",0) or 0)
        nb_cov = float(nb_stats.get("avg_coverage",0.0) or 0.0)

        if nb_trials:
            random_cover_pct = nb_cov / 37.0 * 100.0
            actual_any_pct = nb_any / nb_trials * 100.0
            self.neighbor_summary.config(
                text=(
                    f"K2 TOPLAM {nb_any}/{nb_trials} %{actual_any_pct:.1f}\n"
                    f"NET katkı {nb_net} • YEDEK katkı {nb_backup} • "
                    f"ÇOKLU {nb_multi}\n"
                    f"ORT. KAPSAM {nb_cov:.1f}/37 • "
                    f"KAPSAM TABANI ~%{random_cover_pct:.1f}"
                )
            )
        else:
            self.neighbor_summary.config(text="Henüz komşu istatistiği yok.")

        pending_nb = s.get("pending_compare") or {}
        if pending_nb:
            net_n = int(pending_nb.get("predicted",0) or 0)
            backups_n = [int(x) for x in (pending_nb.get("side4") or [])[:4]]
            centers_n = [net_n] + backups_n
            coverage = set()
            for c in centers_n:
                coverage.update(int(x) for x in wheel_neighbors(c,2))

            current_nb = int(s.get("neighbor_batch_count",0) or 0)
            next_nb = 1 if current_nb >= 12 else current_nb + 1

            self.neighbor_pending.config(
                text=(
                    f"BEKLEYEN #{next_nb:02d} • NET {net_n:02d} K2 • "
                    f"Y " + "/".join(f"{x:02d}" for x in backups_n)
                    + f" K2 • KAPSAM {len(coverage)}/37"
                )
            )
        else:
            self.neighbor_pending.config(text="BEKLEYEN KOMŞU OYUNU: --")

        nb_rows = s.get("neighbor_records") or []
        if nb_rows:
            hit_count = sum(1 for r in nb_rows if r.get("any_neighbor_hit"))
            rows = [
                f"SERİ {len(nb_rows)}/12 • K2 TUTTU {hit_count} • DIŞI {len(nb_rows)-hit_count}"
            ]

            for i,r in enumerate(nb_rows,1):
                net_n = int(r.get("net",0) or 0)
                backups = [int(x) for x in (r.get("backups") or [])[:4]]
                backups_txt = "/".join(f"{x:02d}" for x in backups) or "--"
                actual_n = int(r.get("actual",0) or 0)
                hit_centers = [int(x) for x in (r.get("hit_centers") or [])]
                cov = int(r.get("unique_coverage",0) or 0)
                result = str(r.get("result") or "DIŞI")

                if result == "NET K2":
                    result_txt = "NET K2 ✓"
                elif result == "YEDEK K2":
                    result_txt = "YEDEK K2 ✓"
                else:
                    result_txt = "DIŞI"

                multi_txt = ""
                if len(hit_centers) >= 2:
                    multi_txt = " • ÇOKLU:" + ",".join(
                        f"{x:02d}" for x in hit_centers
                    )

                rows.append(
                    f"{i:02d} | N {net_n:02d} K2 | "
                    f"Y {backups_txt} K2 | "
                    f"ÇIKAN {actual_n:02d} | {result_txt} | K {cov}/37"
                    + multi_txt
                )

            self.neighbor_history.config(text="\n".join(rows))
        else:
            self.neighbor_history.config(text="Yeni gerçek sonuç bekleniyor.")

        if h:
            n = h[0]
            self.last_num.config(
                text=str(n),
                fg=self.GREEN if n == 0 else self.RED if n in RED else self.TEXT
            )
            parity = "-" if n == 0 else ("TEK" if n%2 else "ÇİFT")
            high = "-" if n == 0 else ("1-18" if n <= 18 else "19-36")
            self.last_meta.config(
                text=f"{color_of(n)} • {parity} • {high} • {dozen_of(n)} • {column_of(n)}"
            )

            rows = []
            for i in range(0,min(20,len(h)),10):
                rows.append("  ".join(f"{x:02d}" for x in h[i:i+10]))
            self.history.config(text="\n".join(rows))

            self.hot.config(text="SICAK\n" + "  ".join(map(str,s["hot"])))
            self.cold.config(text="SOĞUK\n" + "  ".join(map(str,s["cold"])))

            red = sum(1 for x in h if x in RED)
            black = sum(1 for x in h if x in BLACK)
            zero = h.count(0)
            odd = sum(1 for x in h if x and x%2)
            even = sum(1 for x in h if x and x%2==0)
            low = sum(1 for x in h if 1 <= x <= 18)
            high = sum(1 for x in h if 19 <= x <= 36)

            d1 = sum(1 for x in h if 1 <= x <= 12)
            d2 = sum(1 for x in h if 13 <= x <= 24)
            d3 = sum(1 for x in h if 25 <= x <= 36)

            self.distribution.config(text=(
                f"Kırmızı {red:2d}   Siyah {black:2d}   0 {zero}\n"
                f"Tek     {odd:2d}   Çift  {even:2d}\n"
                f"1-18    {low:2d}   19-36 {high:2d}\n"
                f"Düzine  1:{d1}   2:{d2}   3:{d3}"
            ))
        else:
            self.last_num.config(text="-",fg=self.TEXT)
            self.last_meta.config(text="-")
            self.pending_compare_line.config(text="BEKLEYEN TAHMİN: --")
            self.compare_history_line.config(text="Henüz doğrulanmış tahmin yok.")
            self.history.config(text="-")
            self.hot.config(text="SICAK\n-")
            self.cold.config(text="SOĞUK\n-")
            self.distribution.config(text="-")

        table = f" • {s['table']}" if s["table"] else ""
        self.source.config(text=f"Kaynak: {s['source']}{table}")

        self.root.after(250,self.refresh)

    def close(self):
        self.exit_code = 0
        self.bridge.stop()
        self.root.after(100,self.root.destroy)

    def run(self):
        self.root.mainloop()
        try:
            self.root.destroy()
        except Exception:
            pass
        return int(self.exit_code or 0)


def lobby_teach_self_test():
    mixed = [
        {'action':'click','text':'CANLI CASINO','tag':'a','classes':['nav'],'testid':'live'},
        {'action':'scroll','scope':'window','dx':0,'dy':420,'toX':0,'toY':420,'tag':'window'},
        {'action':'click','text':'PRAGMATIC PLAY','tag':'button','classes':['provider'],'testid':'pp'},
        {'action':'type','value':'pragmatic','tag':'input','placeholder':'Oyun ara','classes':['search']},
        {'action':'click','text':'Pragmatic','tag':'div','classes':['game-card']},
    ]
    js=build_learned_lobby_scan(mixed,0)
    assert "const d=STEPS[START]" in js
    assert "continue;" not in js
    assert "stage:'LEARNED_SCROLL'" in js
    assert "stage:'LEARNED_TYPE'" in js
    assert "stage:'LEARNED_STEP'" in js
    assert 'pragmatic' in js

    for i in range(len(mixed)):
        jsi=build_learned_lobby_scan(mixed,i)
        assert "continue;" not in jsi
        assert "const d=STEPS[START]" in jsi
    return True


def table_scan_self_test():
    nav_script = build_multi_table_nav_scan()
    assert PRAGMATIC_LOBBY_SCAN_URL == (
        "https://www.meritbet868.com/tr/live-casino/home"
        "?searchTerm=pragmatic+play+lobby"
    )
    assert "pragmatic-lobby-card-play" in nav_script
    assert "open_card" not in nav_script
    assert "scrollTarget.scrollBy" in nav_script
    assert "roulette-selecting" in nav_script
    assert "findCardBox" in nav_script
    assert "extractCleanTableTitle" in nav_script
    assert "clickCardThumbnail" in nav_script
    assert "rawCardItems.sort" in nav_script
    assert "unclickedCards.length === 0" in nav_script
    assert COLLECTOR_MAX_CONCURRENT == 6
    assert collector_refresh_due(1000.0, 0.0, 0.0, False)
    assert not collector_refresh_due(1000.0, 500.0, 0.0, False)
    assert collector_refresh_due(1101.0, 500.0, 0.0, False)
    assert not collector_refresh_due(1050.0, 0.0, 1020.0, True)

    bridge = object.__new__(ChromeBridge)
    bridge.collector_lock = threading.Lock()
    bridge.collector_inflight = set()
    bridge.auth_templates = {
        "games.example": {"seen": time.time(), "session_id": "test"}
    }
    bridge.collector_seen = {
        str(i): {"table_id": str(i), "display_name": str(i), "last_requested": 0.0}
        for i in range(20)
    }
    dispatched = []
    bridge._start_background_history_request = (
        lambda template, table_id, display_name:
        dispatched.append(table_id) or True
    )
    bridge._collector_tick()
    assert len(dispatched) == COLLECTOR_MAX_CONCURRENT

    bridge.table_scan_target_id = "collector-root"
    bridge.target_parent = {"provider-iframe": "collector-root"}
    bridge.target_info = {}
    assert bridge._is_collector_target_id("provider-iframe")
    bridge.table_scan_target_id = ""
    assert bridge._is_collector_target_id("provider-iframe")
    assert bridge._is_korece_table(table_id="381rwkr381korean")
    assert bridge._is_korece_table(theme_code="pp_roulette_crl_chroma_korean_roulette")
    assert bridge._is_korece_table(label="Korece Rulet")
    assert not bridge._is_korece_table(label="Almanca Rulet")
    assert bridge._is_blocked_table_label("Privé Lounge Rulet Deluxe")
    assert bridge._is_blocked_table_label("Privé Lounge Rulet")
    assert bridge._is_blocked_table_label("Gates of Olympus Rulet")
    assert bridge._is_blocked_table_label("PowerUP Rulet")
    assert bridge._is_blocked_table_label("Rulet Deluxe")
    assert not bridge._is_blocked_table_label("Hızlı Rulet 1")
    assert not bridge._is_blocked_table_label("Hızlı Rulet 3")
    assert not bridge._is_blocked_table_label("VIP Otomatik Rulet")

    discovered = extract_pragmatic_roulette_tables({
        "games": [{"tableId": "table-17", "gameName": "Roulette Table 17"}]
    })
    assert discovered == [{
        "table_id": "table-17",
        "display_name": "Roulette Table 17",
    }]
    old_window = [(i * 7 + (i // 9)) % 37 for i in range(500)]
    next_window = [8, 19] + old_window[:498]
    assert detect_new_front_large(old_window, old_window) == []
    assert detect_new_front_large(old_window, next_window) == [8, 19]
    # Offset-tolerant anchor match when old[0] had a 1-spin DOM discrepancy
    old_glitched = [36] + old_window[1:]
    next_glitched = [14, 23, 5] + old_window[:497]
    assert detect_new_front_large(old_glitched, next_glitched) == [14, 23, 5]
    assert "noMult" in HISTORY500_SCAN

    # Verify multi-pass re-scans monotonically increase table_long_archive & ORTAK HAVUZ
    # even when background500 arrives with collector_<hash> or exceeds 550 spins.
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        st = object.__new__(RouletteState)
        st.lock = threading.Lock()
        st.data_dir = tmpdir
        st.pragmatic_table_id = ""
        st.table_name = ""
        st.table_long_table = ""
        st.history = []
        st.pending_prediction = None
        st.table_registry = {}
        st._pool_memory_tables = {}
        st._memory_table500 = {}
        st._pool_dirty = False
        base_500 = [((i * 11 + (i * i) % 17 + (i // 7) * 3) % 37) for i in range(500)]
        r_scan1 = st.store_background_table_history(
            base_500, "204", display_name="Mega Rulet", source_label="PRAGMATIC statisticHistory"
        )
        assert r_scan1 == 500
        assert st.table_registry["204"]["long_count"] == 500
        # Pass 2: arrives first from DOM SON 500 with collector_<hash> and 12 new spins
        scan2_500 = [((i * 5 + 3) % 37) for i in range(12)] + base_500[:488]
        r_scan2 = st.store_background_table_history(
            scan2_500, "collector_deadbeef", display_name="Mega Rulet", source_label="ARKA PLAN SON 500"
        )
        assert "collector_deadbeef" not in st.table_registry
        assert r_scan2 == 12
        assert st.table_registry["204"]["long_count"] == 512
        assert len(st._pool_memory_tables["pragmatic_204"]) == 512
        # Pass 3: arrives from statisticHistory with 55 more new spins (total 567 > 550)
        scan3_500 = [((i * 13 + (i * i) % 29 + (i // 5) * 7 + 2) % 37) for i in range(55)] + scan2_500[:445]
        r_scan3 = st.store_background_table_history(
            scan3_500, "204", display_name="Mega Rulet", source_label="PRAGMATIC statisticHistory"
        )
        assert r_scan3 == 55
        assert st.table_registry["204"]["long_count"] == 567
        assert len(st._pool_memory_tables["pragmatic_204"]) == 567
        # Verify generic "Roulette" or "AKTİF SON500" never pollutes or overwrites MASA BANKASI
        st._update_table_registry("204", display_name="Roulette", long_count=567, source="SEKMELİ TOPLA statisticHistory", save_disk=False)
        assert st.table_registry["204"]["display_name"] == "Mega Rulet"
        st._update_table_registry("999", display_name="https://client.example/desktop/roulette/", long_count=500, source="AKTİF SON500", save_disk=False)
        assert "999" not in st.table_registry
    assert "host.startsWith('client.')" in nav_script
    assert "path.includes('/desktop/roulette')" in nav_script
    assert "SIMDI OYNANIYOR" in nav_script
    assert "CANONICAL_TABLES" in nav_script
    assert "matchCanonicalTable" in nav_script
    assert "scrolling-card-into-view" not in nav_script
    assert len(PRAGMATIC_LOBBY_TABLES) == 32
    assert canonical_pragmatic_table_name("34 1 23 34 3 27 Brezilya Portekizcesi Mega ... ₺ 2 49") == "Brezilya Portekizcesi Mega Rulet"
    for item in PRAGMATIC_LOBBY_TABLES:
        info = canonical_pragmatic_table_info(f"14 27 25 16 25 7 {item['name']} ₺ 2 94")
        assert info is not None and info["order"] == item["order"] and info["name"] == item["name"]
    bridge.session_table_activity = {}
    bridge.table_scan_current_click_label = "RULET MACAO"
    bridge.table_scan_last_clicked_label = "RULET MACAO"
    bridge.table_scan_current_click_key = "RULET MACAO"
    assert bridge._collector_table_identity("s1", real_table_id="203", title="Roulette") == ("203", "Rulet Macao")
    return True


def self_test():
    assert lobby_teach_self_test() is True
    assert table_scan_self_test() is True
    loss = {
        "RECENCY": 3.5,
        "WHEEL": 3.1,
        "TRANSITION": 3.6,
        "WEB": 3.4,
    }
    hits = {
        "RECENCY": {"trials": 43, "exact": 2, "top5": 7, "neighbor5": 6},
        "WHEEL": {"trials": 43, "exact": 0, "top5": 3, "neighbor5": 3},
        "TRANSITION": {"trials": 43, "exact": 1, "top5": 6, "neighbor5": 5},
        "WEB": {"trials": 43, "exact": 1, "top5": 5, "neighbor5": 5},
    }
    w = adaptive_weights(loss, 43, hits)
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert all(0.0 < x < 0.51 for x in w.values())

    # Public-history parser sanity.
    sample = b"<h2>Recent results</h2><p>1. 7</p><p>2. 9</p><p>3. 22</p>" + b"".join(
        f"<p>{i}. {i%37}</p>".encode() for i in range(4, 25)
    )
    parsed = parse_public_recent_results(sample)
    assert len(parsed) >= 20
    assert parsed[0] == 7

    # External expert remains a valid probability distribution.
    ext = external_web_expert([17, 34, 7], PUBLIC_AUTO_SEED_NEWEST)
    assert abs(sum(ext.values()) - 1.0) < 1e-9
    assert set(ext.keys()) == set(range(37))

    # Risk/EV math: five straight-up numbers break even at 5/36,
    # while random European coverage is 5/37 and ROI is -1/37 per stake unit.
    rp = straight_up_risk_profile("T5", hits=14, trials=100, coverage=5)
    assert abs(rp["random_hit_pct"] - (5/37*100)) < 1e-9
    assert abs(rp["breakeven_hit_pct"] - (5/36*100)) < 1e-9
    assert abs(rp["random_roi_pct"] + (100/37)) < 1e-9
    assert rp["roi_pct"] > 0.0

    # V2.9.1 unattended recovery message tests.
    r1 = recovery_text_score("Bağlantı hatası. Lütfen sayfayı yenileyin.", ["Yenile"])
    assert r1["hit"] is True and r1["score"] >= 3
    r2 = recovery_text_score("Please refresh the page to continue.", ["Refresh"])
    assert r2["hit"] is True
    r3 = recovery_text_score("Canlı rulet masası açık. Sonuçlar gösteriliyor.", ["Lobi"])
    assert r3["hit"] is False

    # V2.9.4 old/dead table URLs must resolve to stable live-casino home.
    u = safe_lobby_entry_url(
        "https://example.com/tr/live-casino/home?searchTerm=pragmatic%20play&openGames=3300922-real&gameNames=OldTable"
    )
    assert u == "https://example.com/tr/live-casino/home"
    assert safe_lobby_entry_url("https://example.com/tr/live-casino/home") == "https://example.com/tr/live-casino/home"
    assert safe_lobby_entry_url("https://pragmaticplaylive.net/game.do?token=SECRET") == ""

    # Multi-table global pool (20 tables x 500 spins = 10,000 spins) test:
    # Verify boundary safety (-1 prevents false cross-table transitions) and
    # exact % calculation when 1 lands on the main table.
    pool_20_tables = []
    for t_idx in range(20):
        if t_idx > 0:
            pool_20_tables.append(-1)
        # Build a 500-spin newest-first sequence per table where 1 -> 14 occurs often
        # (in newest-first order, [14, 1] means 1 was followed by 14).
        table_seq = []
        for s_idx in range(250):
            if s_idx % 8 == 0:
                table_seq.extend([14, 1])
            elif s_idx % 13 == 0:
                table_seq.extend([25, 1])
            else:
                table_seq.extend([(s_idx + t_idx) % 37, (s_idx * 3 + t_idx + 2) % 37])
        pool_20_tables.extend(table_seq[:500])

    snap_mt = external_transition_snapshot([1, 7, 22], pool_20_tables)
    assert snap_mt["tables"] == 20
    assert snap_mt["spins"] == 10000
    assert snap_mt["exact_obs"] > 0
    assert snap_mt["exact_top_pct"][0][0] == 14
    assert snap_mt["exact_top_pct"][0][2] > 20.0

    mt_dist = multi_table_transition_expert([1, 7, 22], pool_20_tables)
    assert abs(sum(mt_dist.values()) - 1.0) < 1e-9
    assert max(mt_dist, key=mt_dist.get) == 14

    sc_mt = source_consensus([1, 7, 22], [22, 7, 1], pool_20_tables[:500], pool_20_tables[:500], pool_20_tables, [])
    assert "ARCHIVE" in sc_mt["sources"]
    assert sc_mt["sources"]["ARCHIVE"]["top1"] == 14

    net_mt = choose_net_number({
        "predicted": 25,
        "combined": mt_dist,
        "experts": expert_distributions([1, 7, 22], [22, 7, 1], pool_20_tables[:500]),
        "source_consensus": sc_mt,
        "multi_table_transition": snap_mt,
        "table_long_count": 500,
        "recent_history": [1, 7, 22],
    })
    assert net_mt["number"] == 14
    assert net_mt["leader_family"] == "ORTAK"
    assert 14 in net_mt["top5"] and 25 in net_mt["top5"]

    # Lobby exit guard assertions:
    assert "lobbyLike: true" in DOM_SCAN
    assert "earlyLobbyLike" in HISTORY500_SCAN

    # Narrow 10-number DOM bar catch-up & anti-repeat assertions:
    cur_20 = [31, 14, 15, 18, 20, 2, 11, 32, 16, 14, 19, 10, 17, 6, 35, 34, 12, 27, 4, 8]
    narrow_same_10 = cur_20[:10]
    assert detect_new_front(cur_20, narrow_same_10, max_new=16) == []
    narrow_bar_10 = [9, 29, 13, 13, 11, 16, 31, 14, 15, 18]
    dom_cand = choose_live_dom_candidate([{"nums": narrow_bar_10, "cls": "recent-results"}], cur_20)
    assert dom_cand is not None and dom_cand["new_count"] == 6
    assert detect_new_front(cur_20, narrow_bar_10, max_new=16) == [9, 29, 13, 13, 11, 16]

    return True


if __name__ == "__main__":
    sys.exit(App().run())
