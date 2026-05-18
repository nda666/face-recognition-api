from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from core.services.pegawai import fetch_pegawai, get_pegawai_by_kode

router = APIRouter(prefix="/pegawai")


@router.get("")
async def pegawai_list():
    """List semua pegawai dari API Doran (cached 5 menit)."""
    data = await fetch_pegawai()
    return JSONResponse(data)


@router.get("/{kode}")
async def pegawai_detail(kode: str):
    """Detail satu pegawai berdasarkan kode_pegawai."""
    p = await get_pegawai_by_kode(kode)
    if p is None:
        raise HTTPException(404, f"Pegawai '{kode}' tidak ditemukan")
    return JSONResponse(p)