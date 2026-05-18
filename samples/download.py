import os
import requests
from concurrent.futures import ThreadPoolExecutor

TOTAL_FACE = 1000
MAX_WORKERS = 20

FAKE_FACE_URL = "https://thispersondoesnotexist.com/"

SAVE_DIR = "samples"

os.makedirs(SAVE_DIR, exist_ok=True)

session = requests.Session()


def download_face(idx):
    try:
        r = session.get(FAKE_FACE_URL, timeout=30)
        r.raise_for_status()

        filepath = os.path.join(SAVE_DIR, f"{idx:05d}.jpg")

        with open(filepath, "wb") as f:
            f.write(r.content)

        print(f"[OK] {filepath}")

    except Exception as e:
        print(f"[ERR] {idx} -> {e}")


with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    executor.map(download_face, range(TOTAL_FACE))

print("\nDONE")