import os

import secrets
from fastapi import Depends, Header, HTTPException

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.models.user import User
from app.lib.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

def _get_api_key() -> str | None:
    # NOTE: `.env` loading sebaiknya dilakukan di entrypoint aplikasi (app.py)
    # namun kita tetap baca dari environment agar bisa langsung di-deploy.
    return os.getenv("API_KEY")


async def require_api_key(
    authorization: str | None = Header(default=None)
):
    api_key = _get_api_key()

    if not api_key:
        raise HTTPException(500, "API_KEY tidak diset di environment")

    if not authorization:
        raise HTTPException(401, "Missing authorization header")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != api_key:
        raise HTTPException(401, "Unauthorized: invalid token")

    return True


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ApiKeyResponse(BaseModel):
    api_key: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    if await User.exists(email=body.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await User.create(
        email=body.email,
        password=hash_password(body.password),
        api_key=secrets.token_urlsafe(32),
    )
    return ApiKeyResponse(api_key=user.api_key)


@router.post("/login", response_model=ApiKeyResponse)
async def login(body: LoginRequest):
    user = await User.get_or_none(email=body.email)
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return ApiKeyResponse(api_key=user.api_key)