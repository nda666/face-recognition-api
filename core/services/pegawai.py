"""
Service data pegawai.
Sumber: pegawai.json di root project.
Format: [{"kode": "EMP001", "nama": "Budi"}, ...]

API Doran di-comment dulu — uncomment kalau sudah siap.
"""
import json
import time
from pathlib import Path
from typing import Optional

# ── Config ────────────────────────────────────────────────────

PEGAWAI_JSON = Path(__file__).parent.parent.parent / "pegawai.json"

# PEGAWAI_API_URL = "https://kasir.doran.id/api/master-pegawai"
# CACHE_TTL       = 300  # detik

# ── Cache (tetap ada biar mudah switch ke API nanti) ──────────

_cache: dict = {"data": None, "ts": 0.0}
CACHE_TTL = 60  # detik — local file, refresh lebih cepat


# ── Load dari file ────────────────────────────────────────────

def _load_from_file() -> list[dict]:
    with open(PEGAWAI_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


async def fetch_pegawai(force_refresh: bool = False) -> list[dict]:
    """
    Baca pegawai.json dari root project.
    Di-cache CACHE_TTL detik supaya tidak baca disk tiap request.

    # ── API version (uncomment kalau sudah siap) ──────────────
    # import httpx
    # now = time.time()
    # if not force_refresh and _cache["data"] is not None and (now - _cache["ts"]) < CACHE_TTL:
    #     return _cache["data"]
    # async with httpx.AsyncClient(timeout=10.0) as client:
    #     resp = await client.get(PEGAWAI_API_URL)
    #     resp.raise_for_status()
    #     data = resp.json()
    # pegawai_list = data if isinstance(data, list) else data.get("data", [])
    # _cache["data"] = pegawai_list
    # _cache["ts"] = now
    # return pegawai_list
    # ─────────────────────────────────────────────────────────
    """
    now = time.time()
    if not force_refresh and _cache["data"] is not None and (now - _cache["ts"]) < CACHE_TTL:
        return _cache["data"]

    pegawai_list = _load_from_file()

    _cache["data"] = pegawai_list
    _cache["ts"] = now
    return pegawai_list


async def get_pegawai_by_kode(kode_pegawai: str) -> Optional[dict]:
    pegawai_list = await fetch_pegawai()
    kode = str(kode_pegawai).strip()
    for p in pegawai_list:
        if str(p.get("kode", "")).strip() == kode:
            return p
    return None


async def invalidate_cache():
    _cache["data"] = None
    _cache["ts"] = 0.0