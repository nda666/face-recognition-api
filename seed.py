# seed.py — run with: python seed.py
# - Buat 1 user
# - Update semua embedding yang face_id-nya kosong: set face_id = embedding.id
#   (buat Face record baru kalau belum ada)

import asyncio
import uuid
import secrets
from dotenv import load_dotenv
load_dotenv()

from tortoise import Tortoise
from app.lib.database import TORTOISE_ORM
from app.lib.security import hash_password   # lihat catatan di bawah


async def main():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas(safe=True)

    from app.models.user import User
    from app.models.face import Face
    from app.models.embedding import Embedding

    # ── 1. Buat seed user ─────────────────────────────────────────────────────
    user, created = await User.get_or_create(
        email="adhabakhtiar@gmail.com",
        defaults={
            "password": hash_password("akumakannasi12"),
            "api_key": secrets.token_urlsafe(32),
        },
    )
    if created:
        print(f"✓ User created  : {user.email}")
        print(f"  id            : {user.id}")
        print(f"  api_key       : {user.api_key}")
    else:
        print(f"• User already exists: {user.email}")

    # ── 2. Fix embeddings yang face_id-nya kosong ─────────────────────────────
    # face_id kosong = NULL di DB
    empty = await Embedding.filter(face_id=None).all()
    print(f"\n→ Found {len(empty)} embedding(s) with empty face_id")

    for emb in empty:
        face_id = str(emb.id)   # hardcode: face_id = embedding.id

        # Buat Face kalau belum ada
        face, f_created = await Face.get_or_create(
            id=face_id,
            defaults={"user": user},
        )
        if f_created:
            print(f"  ✓ Face created  : {face.id}")
        else:
            print(f"  • Face exists   : {face.id}")

        # Update embedding
        await Embedding.filter(id=emb.id).update(face=face)
        print(f"  ✓ Embedding {emb.id} → face_id={face_id}")

    print("\n✓ Seed done.")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(main())