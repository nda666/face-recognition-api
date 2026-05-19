import os
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

password_hash = PasswordHash((BcryptHasher(),))
bearer  = HTTPBearer()


# ── Password ──────────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)):
    from app.models.user import User
    user = await User.get_or_none(api_key=creds.credentials)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return user