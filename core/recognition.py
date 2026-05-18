"""
Shared business logic — dipanggil oleh Flask routes MAUPUN wxPython UI.
Tidak ada dependency ke Flask atau wx di sini.
"""
from deepface import DeepFace
import random
from core.store import EmbeddingStore
import numpy as np
from typing import Generator, Callable


# ── Save ─────────────────────────────────────────────────────

def verify_face(img, store):
    embedding, face_found, is_spoof = extract_face_embedding_from_image(img)

    if is_spoof:
        return {"ok": False, "msg": "⚠ Spoof terdeteksi"}

    if not face_found or embedding is None:
        return {"ok": False, "msg": "Tidak ada wajah terdeteksi"}

    matches = store.compare(embedding)

    if matches:
        return {"ok": True, "msg": "Match found", "data": matches}

    return {"ok": False, "msg": "No match"}

def extract_face_embedding_from_image(img: np.ndarray, check_spoof: bool = True) -> tuple:
    """
    Ekstrak embedding ArcFace dari numpy BGR image.

    Returns:
        (embedding, face_found: bool, is_spoof: bool)
    """
    try:
        result = DeepFace.represent(
            img_path=img,
            model_name="ArcFace",
            detector_backend="opencv",
            enforce_detection=False,
            anti_spoofing=check_spoof,
        )
        if not result:
            return None, False, False
        face = result[0]
        if face.get("is_real") is False:
            return None, False, True
        return face["embedding"], True, False
    except Exception as e:
        print("extract_face_embedding_from_image error:", e)
        return None, False, False


def verify_face(img: np.ndarray, store) -> dict:
    """
    Verify langsung dari image — tanpa challenge.
    """
    embedding, face_found, is_spoof = extract_face_embedding_from_image(img)

    if is_spoof:
        return {"ok": False, "msg": "⚠ Spoof terdeteksi"}
    if not face_found or embedding is None:
        return {"ok": False, "msg": "Tidak ada wajah terdeteksi"}

    matches = store.compare(embedding)
    if matches:
        return {"ok": True, "msg": "Match found", "data": matches}
    return {"ok": False, "msg": "No match"}