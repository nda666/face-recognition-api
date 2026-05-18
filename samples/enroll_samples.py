"""
Enroll semua foto di folder samples/ ke endpoint /enroll.
Kode pegawai urut: EMP00001 s/d EMP01000.
"""

import os
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Config ────────────────────────────────────────────────────

BASE_URL    = "http://127.0.0.1:5000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(BASE_DIR, "faces")
MAX_WORKERS = 10
START_IDX   = 1
MAX_IDX     = 1000

MIME_MAP = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
}

# ── ANSI ──────────────────────────────────────────────────────

GREEN = "\033[92m"
RED   = "\033[91m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"

# ── Load samples ──────────────────────────────────────────────
print(SAMPLE_DIR)
sample_files = sorted(
    f for f in os.listdir(SAMPLE_DIR)
    if os.path.splitext(f)[1].lower() in MIME_MAP
)

if not sample_files:
    print(f"{RED}[ERROR] Tidak ada foto di folder '{SAMPLE_DIR}'{RESET}")
    raise SystemExit(1)

# Batasi sesuai MAX_IDX
sample_files = sample_files[: MAX_IDX - START_IDX + 1]

# Kode pegawai = angka dari nama file (00001.jpg → "1")
def _kode_from_filename(filename: str) -> str:
    stem = os.path.splitext(filename)[0]   # "00001"
    return str(int(stem))                  # "1"

print(f"\n{BOLD}SAMPLE DIR  : {SAMPLE_DIR}{RESET}")
print(f"{BOLD}TOTAL FILE  : {len(sample_files)}{RESET}")
print(f"{DIM}Kode range  : {_kode_from_filename(sample_files[0])} → {_kode_from_filename(sample_files[-1])}")
print(f"Workers     : {MAX_WORKERS}{RESET}\n")

# ── Session ───────────────────────────────────────────────────

session = requests.Session()
session.mount("http://", requests.adapters.HTTPAdapter(
    pool_connections=MAX_WORKERS,
    pool_maxsize=MAX_WORKERS,
))

# ── Worker ────────────────────────────────────────────────────

def enroll(idx: int, filename: str) -> dict:
    filepath = os.path.join(SAMPLE_DIR, filename)
    ext      = os.path.splitext(filename)[1].lower()
    mime     = MIME_MAP[ext]
    kode     = _kode_from_filename(filename)

    try:
        with open(filepath, "rb") as f:
            image_bytes = f.read()
       
        t0 = time.time()
        r  = session.post(
            f"{BASE_URL}/enroll",
            files={"image": (filename, image_bytes, mime)},
            data={"id": kode},
            timeout=60,
        )
        ms = round((time.time() - t0) * 1000, 2)

        ok   = r.status_code == 200
        body = r.text[:120]
        return {"ok": ok, "kode": kode, "file": filename, "ms": ms,
                "status": r.status_code, "body": body}

    except Exception as e:
        return {"ok": False, "kode": kode, "file": filename, "ms": 0,
                "status": -1, "body": str(e)}

# ── Run ───────────────────────────────────────────────────────

success, failed = 0, 0
times = []
t_start = time.time()

tasks = [
    (fname,)
    for fname in sample_files
]

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
    futures = {ex.submit(enroll, 0, fname): fname for fname in sample_files}

    for future in as_completed(futures):
        res = future.result()

        if res["ok"]:
            success += 1
            times.append(res["ms"])
            print(f"  {GREEN}[OK]  {RESET} {res['kode']}  {res['ms']:>7.1f} ms  {DIM}{res['file']}{RESET}")
        else:
            failed += 1
            print(f"  {RED}[FAIL]{RESET} {res['kode']}  status={res['status']}  {DIM}{res['body']}{RESET}")

# ── Summary ───────────────────────────────────────────────────

elapsed = round(time.time() - t_start, 2)

print(f"\n{'─'*44}")
print(f"  {BOLD}DONE{RESET}")
print(f"{'─'*44}")
print(f"  Total   : {len(sample_files)}")
print(f"  {GREEN}Success{RESET} : {success}")
print(f"  {RED}Failed{RESET}  : {failed}")
print(f"  Elapsed : {elapsed} s")

if times:
    avg = round(sum(times) / len(times), 1)
    print(f"  AVG     : {avg} ms")
    print(f"  MIN     : {min(times):.1f} ms")
    print(f"  MAX     : {max(times):.1f} ms")

print(f"{'─'*44}\n")