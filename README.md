# Face Recognition

Project ini adalah layanan **verifikasi wajah** berbasis embedding menggunakan **DeepFace (ArcFace)**. Layanan dibuat dengan **FastAPI** dan menyimpan embedding ke **SQLite**.

---

## Fitur Utama

- **Enroll wajah**: mendaftarkan wajah seseorang ke database embedding.
- **Verify wajah**: membandingkan wajah dari input dengan embedding yang sudah tersimpan.
- **Anti-spoofing (opsional)**: deteksi spoofing dilakukan saat verifikasi.
- **Penyimpanan embedding**: SQLite (`storage/embeddings.db`).

---

## Arsitektur Singkat

- `core/recognition.py`
  - Mengambil embedding ArcFace via `DeepFace.represent()`
- `core/store.py`
  - `EmbeddingStore`: load/save embedding ke SQLite, dan bandingkan embedding dengan cosine similarity.
- `web/face.py`
  - Endpoint:
    - `POST /enroll`
    - `POST /verify`
- `web/auth.py`
  - Middleware sederhana berbasis `API_KEY` via header `Authorization: Bearer <API_KEY>`.

---

## Prasyarat

- Python **3.12+**
- Model & dependensi sesuai `pyproject.toml` (DeepFace, Torch, OpenCV, dll.)

---

## Setup Lokal

### 1) Install dependency

Menggunakan `uv` (sesuai `pyproject.toml`).

```bash
uv sync
```

### 2) Set environment variable

Buat `.env` (atau export environment variable) dengan minimal:

```bash
API_KEY=isi_dengan_token_rahasia
DB_PATH=storage/embeddings.db
```

> `DB_PATH` opsional: jika tidak di-set, implementasi akan memakai nilai default dari environment.

### 3) Jalankan server

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Server akan melayani endpoint di `http://localhost:8000`.

---

## Format Input

Untuk endpoint face:

- `image` harus berupa file upload **JPEG/PNG/WebP**.

Untuk `enroll`:

- `id` wajib diisi (string).

---

## Endpoint API

> Catatan: semua route di router face/misc dilindungi dengan API key.

### Header autentikasi

- `Authorization: Bearer <API_KEY>`

### 1) Enroll Wajah

**POST** `/enroll`

Body (multipart/form-data):

- `id` (string)
- `image` (file)

Contoh (curl):

```bash
curl -X POST 'http://localhost:8000/enroll' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'id=EMP001' \
  -F 'image=@/path/foto.jpg'
```

Output (contoh):

- `ok: true`
- `id`
- `file` (id row / filename internal dari store)

---

### 2) Verify Wajah

**POST** `/verify`

Body (multipart/form-data):

- `image` (file)

Contoh (curl):

```bash
curl -X POST 'http://localhost:8000/verify' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -F 'image=@/path/foto_verify.jpg'
```

Output:

- Jika cocok: `{ ok: true, matches: [...] }`
- Jika tidak cocok: `{ ok: false, msg: 'No match' }`

Elemen pada `matches`:

- `id` (nama di database dianggap sebagai name)
- `distance`
- `confidence`

---

## Cara Pakai Script Samples

Folder `samples/` berisi contoh untuk enroll, verify benchmark, download dataset wajah sintetis, dll.

### Enroll Massal

`samples/enroll_samples.py`

- Mengambil foto dari `samples/faces`
- Mengirim ke endpoint `/enroll`
- Mapping `id` dari nama file (contoh: `00001.jpg` → `1`)

Jalankan:

```bash
python samples/enroll_samples.py
```

---

### Verify Benchmark

`samples/benchmark.py`

- Melakukan verify berkali-kali untuk mengukur latency dan success rate.

Jalankan:

```bash
python samples/benchmark.py
```

---

## Docker

Build & run:

```bash
docker build -t face-recognition .
docker run --rm -p 8000:8000 \
  -e API_KEY=YOUR_API_KEY \
  -v $(pwd)/storage:/storage \
  face-ai
```

> Container memakai volume `/storage` agar database embedding tetap persisten.

---

## Catatan Teknis (Tuning)

- Threshold pencocokan embedding ada di `core/store.py` pada parameter `tolerance` (default `0.45`).
- Anti-spoofing dilakukan di `extract_face_embedding_from_image()` saat verifikasi (default `check_spoof=True`).

---

## Troubleshooting

- **HTTP 401 Unauthorized**
  - API key belum benar atau header `Authorization` tidak ada.
- **HTTP 415 Unsupported media type**
  - Pastikan format gambar: JPEG/PNG/WebP.
- **Tidak ada wajah terdeteksi**
  - Coba gunakan gambar dengan wajah yang lebih jelas / lebih dekat.

---

## Lisensi

Belum ditentukan.
