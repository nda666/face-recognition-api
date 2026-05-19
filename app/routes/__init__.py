from fastapi import APIRouter, Depends
from app.lib.store import EmbeddingStore

from app.routes import face, index as index_route
from app.routes import misc
from app.routes.auth import require_api_key

store: EmbeddingStore = None


def init(emb_store: EmbeddingStore):
    global store
    store = emb_store

    face.init(store)
    misc.init(store)


def create_router() -> APIRouter:
    root = APIRouter()

    # Public route
    root.include_router(index_route.router)

    # Protected route
    protected = APIRouter(
        dependencies=[Depends(require_api_key)]
    )

    protected.include_router(face.router, tags=["face"])
    protected.include_router(misc.router, tags=["misc"])

    root.include_router(protected)

    return root