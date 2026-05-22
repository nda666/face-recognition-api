import json
import base64
import numpy as np
import cv2
import httpx
from fastapi import UploadFile, HTTPException
from fastapi.responses import JSONResponse
from app.lib.store import _normalize
from app.lib.url_cache import url_cache
from app.lib.recognition import extract_face_embedding_from_image
import uuid
from pathlib import Path


ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

ANNOTATED_DIR = Path("storage/annotated")
ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)


# ── Image readers ─────────────────────────────────────────────────────────────

async def read_image(upload: UploadFile) -> np.ndarray:
    if upload.content_type not in ALLOWED_MIME:
        raise HTTPException(415, f"Unsupported media type: {upload.content_type}. Gunakan JPEG/PNG/WebP.")
    raw = await upload.read()
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Gagal decode image.")
    return img


async def read_image_from_url(url: str) -> np.ndarray:
    if url in url_cache:
        raw = url_cache[url]
    else:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(url)
                r.raise_for_status()
                ct = r.headers.get("content-type", "")
                if not any(t in ct for t in ("jpeg", "png", "webp")):
                    raise HTTPException(415, f"Unsupported media type dari URL: {ct}")
                raw = r.content
                url_cache.set(url, raw, expire=300)  # TTL 5 menit
        except httpx.HTTPError as e:
            raise HTTPException(400, f"Gagal fetch URL: {e}")

    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Gagal decode image dari URL.")
    return img


async def read_image_source(file: UploadFile | None, url: str | None) -> np.ndarray:
    if file and url:
        raise HTTPException(400, "Kirim salah satu saja: file atau url.")
    if url:
        return await read_image_from_url(url)
    if file:
        return await read_image(file)
    raise HTTPException(400, "Wajib isi file atau url.")


# ── Extraction ────────────────────────────────────────────────────────────────

def run_extraction(img: np.ndarray, spoof_check: bool):
    """Pure extraction logic. Returns (img, embedding, err_response)."""
    embedding, face_found, is_spoof = extract_face_embedding_from_image(img, spoof_check)

    if is_spoof:
        return img, None, JSONResponse({"ok": False, "msg": "⚠ Spoof terdeteksi"}, status_code=400)
    if not face_found or embedding is None:
        return img, None, JSONResponse({"ok": False, "msg": "Tidak ada wajah terdeteksi"}, status_code=400)

    return img, embedding, None


async def extract(upload: UploadFile, spoof_check: bool = True):
    """Shortcut: UploadFile → (img, embedding, err)."""
    img = await read_image(upload)
    return run_extraction(img, spoof_check)


async def extract_from_source(
    file: UploadFile | None,
    url: str | None,
    label: str = "image",
):
    """Shortcut: file atau URL → (img, embedding, err)."""
    try:
        img = await read_image_source(file, url)
    except HTTPException as e:
        return None, JSONResponse({"ok": False, "msg": f"[{label}] {e.detail}"}, status_code=e.status_code)

    return img, None



def _annotate_image(
    img: np.ndarray,
    facial_area: dict,
    matched: bool,
    max_size: int = 640,
) -> str:
    """Draw bounding box + eye dots, resize to max_size (longest side), save to file, return URL path."""
    annotated = img.copy()

    x, y, w, h = facial_area["x"], facial_area["y"], facial_area["w"], facial_area["h"]
    color = (0, 255, 0) if matched else (0, 0, 255)

    cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

    for lm_key in ("left_eye", "right_eye", "nose", "mouth_left", "mouth_right"):
        pt = facial_area.get(lm_key)
        if pt and len(pt) == 2:
            cv2.circle(annotated, (int(pt[0]), int(pt[1])), 3, color, 2)

    # crop sesuai bounding box (sebelum resize)
    cropped = annotated[y:y+h, x:x+w]

    # resize crop
    ch, cw = cropped.shape[:2]
    if max(ch, cw) > max_size:
        scale = max_size / max(ch, cw)
        cropped = cv2.resize(
            cropped,
            (int(cw * scale), int(ch * scale)),
            interpolation=cv2.INTER_AREA,
        )

    filename = f"{uuid.uuid4().hex}.jpg"
    filepath = ANNOTATED_DIR / filename
    cv2.imwrite(str(filepath), cropped, [cv2.IMWRITE_JPEG_QUALITY, 85])

    return f"/storage/annotated/{filename}"
# ── Comparison ────────────────────────────────────────────────────────────────

def deepface_compare(img1: np.ndarray, img2: np.ndarray, tolerance: float = 0.8) -> dict:
    from deepface import DeepFace

    try:
        result = DeepFace.verify(
            img1_path=img1,
            img2_path=img2,
            model_name="ArcFace",
            detector_backend="retinaface",
            anti_spoofing=False,
            enforce_detection=True,
            threshold=tolerance,
        )
        result["matched"] = result["verified"]

        # facial_areas = result.get("facial_areas", {})
        # fa1 = facial_areas.get("img1")
        # fa2 = facial_areas.get("img2")

        # result["annotated_image1"] = _annotate_image(img1, fa1, result["matched"]) if fa1 else None
        # result["annotated_image2"] = _annotate_image(img2, fa2, result["matched"]) if fa2 else None

        return result

    except ValueError as e:
        raise HTTPException(400, f"DeepFace error: {e}")