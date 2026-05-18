import os

from fastapi import Depends, Header, HTTPException


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
