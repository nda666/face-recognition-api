from fastapi import APIRouter, Depends
from core.store import EmbeddingStore

from web import face, misc, pegawai, index as index_route
from web.auth import require_api_key

# State shared antar sub-router

store: EmbeddingStore = None


def init(emb_store: EmbeddingStore):
    global store
    store = emb_store

    face.init(store)


def create_router() -> APIRouter:
    # Proteksi semua route dalam router ini
    r = APIRouter(dependencies=[Depends(require_api_key)])
    r.include_router(face.router, tags=["face"])
    r.include_router(misc.router, tags=["misc"])
    r.include_router(pegawai.router, tags=["pegawai"])
    r.include_router(index_route.router)
    return r

