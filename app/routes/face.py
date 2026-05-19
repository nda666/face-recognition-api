import numpy as np
from fastapi import APIRouter, Form, UploadFile, File
from fastapi.responses import JSONResponse

from app.lib.store import EmbeddingStore
from app.lib.face_helpers import extract, extract_from_source, deepface_compare

router = APIRouter()
store: EmbeddingStore = None


def init(emb_store: EmbeddingStore):
    global store
    store = emb_store


@router.post("/enroll")
async def enroll(
    id: str = Form(...),
    image: UploadFile = File(...),
):
    kode = id.strip()
    if not kode:
        return JSONResponse({"ok": False, "msg": "id wajib diisi"}, status_code=400)

    _, embedding, err = await extract(image, spoof_check=False)
    if err:
        return err

    filename = store.save(kode, embedding)
    return JSONResponse({"ok": True, "msg": "Wajah berhasil didaftarkan", "id": kode, "file": filename})


@router.post("/verify")
async def verify(image: UploadFile = File(...)):
    _, embedding, err = await extract(image)
    if err:
        return err

    matches = store.compare(embedding)
    if not matches:
        return JSONResponse({"ok": False, "msg": "No match"})

    return JSONResponse({
        "ok": True,
        "matches": [
            {"id": m["name"], "distance": m["distance"], "confidence": m["confidence"]}
            for m in matches
        ],
    })


@router.post("/compare")
async def compare(
    tolerance:  float      = Form(0.45),
    image1:     UploadFile = File(None),
    image1_url: str        = Form(None),
    image2:     UploadFile = File(None),
    image2_url: str        = Form(None),
):
    img1, _, err1 = await extract_from_source(image1, image1_url, False, label="image1")
    if err1:
        return err1

    img2, _, err2 = await extract_from_source(image2, image2_url, label="image2")
    if err2:
        return err2

    try:
        result = deepface_compare(img1, img2)
    except HTTPException as e:
        return JSONResponse({"ok": False, "msg": e.detail}, status_code=e.status_code)

    return JSONResponse({"ok": True, **result})


@router.delete("/delete-id")
async def delete(id: str):
    kode = id.strip()
    if not kode:
        return JSONResponse({"ok": False, "msg": "id wajib diisi"}, status_code=400)

    deleted = store.delete(kode)
    if deleted <= 0:
        return JSONResponse({"ok": False, "msg": "Data tidak ditemukan"}, status_code=404)

    return JSONResponse({"ok": True, "msg": "ID berhasil dihapus", "id": kode})