
import numpy as np
import cv2
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from core.store import EmbeddingStore
from core.recognition import extract_face_embedding_from_image


router = APIRouter()
store: EmbeddingStore = None

ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}


def init( emb_store: EmbeddingStore):
    global  store
    store = emb_store


async def _read_image(upload: UploadFile) -> np.ndarray:
    if upload.content_type not in ALLOWED_MIME:
        raise HTTPException(
            415,
            f"Unsupported media type: {upload.content_type}. Gunakan JPEG/PNG/WebP.",
        )
    raw = await upload.read()
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Gagal decode image.")
    return img


async def _extract(upload: UploadFile, spoof_check: bool = True):
    img = await _read_image(upload)
    embedding, face_found, is_spoof = extract_face_embedding_from_image(img, spoof_check)

    if is_spoof:
        return img, None, JSONResponse({"ok": False, "msg": "⚠ Spoof terdeteksi"}, status_code=400)
    if not face_found or embedding is None:
        return img, None, JSONResponse({"ok": False, "msg": "Tidak ada wajah terdeteksi"}, status_code=400)

    return img, embedding, None


# ── Enroll ────────────────────────────────────────────────────

@router.post("/enroll")
async def enroll(
    id: str = Form(...),
    image: UploadFile = File(...),
):
    kode = id.strip()
    if not kode:
        return JSONResponse({"ok": False, "msg": "id wajib diisi"}, status_code=400)

    _, embedding, err = await _extract(image, False)
    if err:
        return err

    filename = store.save(kode, embedding)

    return JSONResponse({
        "ok": True,
        "msg": "Wajah berhasil didaftarkan",
        "id": kode,
        "file": filename,
    })


# ── Verify ────────────────────────────────────────────────────

@router.post("/verify")
async def verify(image: UploadFile = File(...)):
    _, embedding, err = await _extract(image)
    if err:
        return err

    raw_matches = store.compare(embedding)
    if not raw_matches:
        return JSONResponse({"ok": False, "msg": "No match"})

    enriched = [
        {
            "id": m["name"],
            "distance": m["distance"],
            "confidence": m["confidence"],
        }
        for m  in raw_matches
    ]

    return JSONResponse({"ok": True, "matches": enriched})