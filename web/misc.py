import numpy as np
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from core.store import EmbeddingStore

router = APIRouter()
store: EmbeddingStore = None


def init(emb_store: EmbeddingStore):
    global  store
    store = emb_store


class SaveBody(BaseModel):
    name: str = ""


class CanvasBody(BaseModel):
    image: str = ""


@router.get("/names")
def names():
    return JSONResponse(store.get_names())
