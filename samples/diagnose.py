"""
Cek berapa foto di samples/ yang bisa dideteksi wajahnya.
Test pakai beberapa detector backend sekaligus.
"""
import os
import cv2
import numpy as np
from deepface import DeepFace

SAMPLE_DIR = "samples"
TEST_LIMIT = 10   # cek N foto pertama saja

BACKENDS = ["opencv", "ssd", "mtcnn", "retinaface"]

MIME_EXT = {".jpg", ".jpeg", ".png", ".webp"}

files = sorted(
    f for f in os.listdir(SAMPLE_DIR)
    if os.path.splitext(f)[1].lower() in MIME_EXT
)[:TEST_LIMIT]

print(f"\nCek {len(files)} foto pertama di '{SAMPLE_DIR}'\n")
print(f"{'FILE':<20}", end="")
for b in BACKENDS:
    print(f"  {b:<12}", end="")
print()
print("─" * (20 + 16 * len(BACKENDS)))

for fname in files:
    path = os.path.join(SAMPLE_DIR, fname)
    img  = cv2.imread(path)
    if img is None:
        print(f"{fname:<20}  [CANNOT READ]")
        continue

    h, w = img.shape[:2]
    print(f"{fname:<20}", end="")

    for backend in BACKENDS:
        try:
            result = DeepFace.represent(
                img_path=img,
                model_name="ArcFace",
                detector_backend=backend,
                enforce_detection=True,   # strict — kalau gagal akan throw
                anti_spoofing=False,
            )
            found = len(result) > 0
        except Exception:
            found = False

        mark = "  \033[92m✓\033[0m           " if found else "  \033[91m✗\033[0m           "
        print(mark[:14], end="")

    print(f"  [{w}x{h}]")

print("\nDone.")