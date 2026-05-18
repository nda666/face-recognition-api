from dotenv import load_dotenv
load_dotenv()

import os
import sys
import time
import random
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ────────────────────────────────────────────────────

API_KEY       = os.getenv("API_KEY")
BASE_URL      = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "faces")
VERIFY_REPEAT = 100
MAX_WORKERS   = 1

# ── ANSI ──────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"
CLR    = "\033[2K"   # clear line
UP     = "\033[1A"   # cursor up 1

# ── Helpers ───────────────────────────────────────────────────

def _bar(value, max_value, width=28, fill="█", empty="░") -> str:
    filled = int(round(value / max_value * width)) if max_value else 0
    return fill * filled + empty * (width - filled)


def _live(done: int, total: int, ok: int, hit: int, times: list[float], label: str):
    """Redraw 3-line live block in place."""
    pct     = done / total * 100 if total else 0
    bar     = _bar(done, total)
    avg     = f"{np.mean(times):.0f}ms" if times else "---"
    last    = f"{times[-1]:.0f}ms"      if times else "---"
    fail    = done - ok

    line1 = f"  {BOLD}{label}{RESET}  {done}/{total}  ({pct:.0f}%)"
    line2 = f"  {GREEN}{bar}{RESET}  ok={GREEN}{ok}{RESET} fail={RED}{fail}{RESET} hit={CYAN}{hit}{RESET}"
    line3 = f"  avg={YELLOW}{avg}{RESET}  last={YELLOW}{last}{RESET}"

    # move cursor up 3 lines and overwrite (skip on first call)
    if done > 1:
        sys.stdout.write(UP * 3)

    sys.stdout.write(f"{CLR}{line1}\n{CLR}{line2}\n{CLR}{line3}\n")
    sys.stdout.flush()


def _stats_block(label: str, times: list[float], success: int, total: int, elapsed: float):
    if not times:
        print(f"  {RED}No data{RESET}")
        return

    arr = sorted(times)
    avg = np.mean(arr)
    p50 = np.percentile(arr, 50)
    p95 = np.percentile(arr, 95)
    p99 = np.percentile(arr, 99)
    rps = round(total / elapsed, 2) if elapsed else 0

    print(f"\n{BOLD}{CYAN}{'─'*46}{RESET}")
    print(f"{BOLD}  {label}{RESET}")
    print(f"{'─'*46}{DIM}")
    print(f"  Total   : {total}")
    print(f"  Success : {GREEN}{success}{RESET}{DIM}  {_bar(success, total)}")
    print(f"  Failed  : {RED}{total-success}{RESET}{DIM}  {_bar(total-success, total)}")
    print(f"  RPS     : {YELLOW}{rps}{RESET}")
    print(f"{'─'*46}")
    print(f"  AVG     : {avg:>8.1f} ms")
    print(f"  MIN     : {arr[0]:>8.1f} ms")
    print(f"  p50     : {p50:>8.1f} ms")
    print(f"  p95     : {p95:>8.1f} ms")
    print(f"  p99     : {p99:>8.1f} ms")
    print(f"  MAX     : {arr[-1]:>8.1f} ms")
    print(f"  Elapsed : {elapsed:>8.2f} s")
    print(f"{CYAN}{'─'*46}{RESET}")


# ── Load samples ──────────────────────────────────────────────

sample_files = sorted(
    os.path.join(SAMPLE_DIR, f)
    for f in os.listdir(SAMPLE_DIR)
    if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
)

if not sample_files:
    print(f"{RED}[ERROR] Tidak ada sample di folder '{SAMPLE_DIR}'{RESET}")
    raise SystemExit(1)

print(f"\n{BOLD}SAMPLE DIR : {SAMPLE_DIR}{RESET}")
print(f"{BOLD}TOTAL FILE : {len(sample_files)}{RESET}")
print(f"{DIM}Workers    : {MAX_WORKERS}")
print(f"Verify repeat : {VERIFY_REPEAT}{RESET}\n")

session = requests.Session()
session.mount("http://", requests.adapters.HTTPAdapter(
    pool_connections=MAX_WORKERS,
    pool_maxsize=MAX_WORKERS,
))

# ── Verify ────────────────────────────────────────────────────

def _verify(i: int, filepath: str) -> dict:
    try:
        with open(filepath, "rb") as f:
            image_bytes = f.read()
        ext      = os.path.splitext(filepath)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png",  ".webp": "image/webp"}
        mime = mime_map.get(ext, "image/jpeg")

        t0 = time.time()
        r  = session.post(
            f"{BASE_URL}/verify",
            files={"image": ("verify" + ext, image_bytes, mime)},
            timeout=60,
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        ms      = round((time.time() - t0) * 1000, 2)
        body    = r.json() if "application/json" in r.headers.get("content-type", "") else {}
        matched = body.get("ok", False)
        return {"ok": r.status_code == 200, "matched": matched, "time_ms": ms}

    except Exception as e:
        return {"ok": False, "matched": False, "time_ms": 0}


print(f"{BOLD}=== VERIFY BENCHMARK  (x{MAX_WORKERS} workers, n={VERIFY_REPEAT}) ==={RESET}\n")
# reserve 3 lines untuk live block
print("\n\n")

verify_pool    = [random.choice(sample_files) for _ in range(VERIFY_REPEAT)]
verify_times, verify_ok, verify_matched, done = [], 0, 0, 0
t_start = time.time()

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = {ex.submit(_verify, i, fp): i for i, fp in enumerate(verify_pool)}

    for future in as_completed(futures):
        res  = future.result()
        done += 1

        if res["ok"]:
            verify_ok += 1
            verify_times.append(res["time_ms"])
        if res["matched"]:
            verify_matched += 1

        _live(done, VERIFY_REPEAT, verify_ok, verify_matched, verify_times, "VERIFY")

t_verify = round(time.time() - t_start, 2)

# newline setelah live block selesai
print()

_stats_block("VERIFY SUMMARY", verify_times, verify_ok, VERIFY_REPEAT, t_verify)

if VERIFY_REPEAT:
    hit_pct = round(verify_matched / VERIFY_REPEAT * 100, 1)
    print(f"\n  {BOLD}Face match rate : {hit_pct}%{RESET}  {_bar(verify_matched, VERIFY_REPEAT)}\n")