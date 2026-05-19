import os
import logging
import sqlite3
import numpy as np
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH")
EMBEDDING_DIM = 512


def _normalize(embedding) -> np.ndarray:
    v = np.asarray(embedding, dtype=np.float32)
    return v / (np.linalg.norm(v) + 1e-9)


def _to_blob(arr: np.ndarray) -> bytes:
    return arr.astype(np.float32).tobytes()


def _from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


class EmbeddingStore:
    def __init__(self, db_path: str = DB_PATH, logger=None):
        self.db_path = db_path
        self._init_db()
        self.logger = logger or logging.getLogger(__name__)

        # In-memory cache (same pattern as before)
        self.names: np.ndarray = np.array([], dtype=object)
        self.ids: np.ndarray = np.array([], dtype=np.int64)
        self.embeddings: np.ndarray = np.empty((0, EMBEDDING_DIM), dtype=np.float32)

        self.load_all()

    # ------------------------------------------------------------------ #
    #  DB helpers                                                          #
    # ------------------------------------------------------------------ #

    @contextmanager
    def _conn(self):
        con = sqlite3.connect(self.db_path)
        con.execute("PRAGMA journal_mode=WAL")   # safe concurrent reads
        con.execute("PRAGMA foreign_keys=ON")
        try:
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_db(self):
        print("init db")
        # with self._conn() as con:
        #     con.execute("""
        #         CREATE TABLE IF NOT EXISTS embeddings (
        #             id        INTEGER PRIMARY KEY AUTOINCREMENT,
        #             name      TEXT    NOT NULL,
        #             embedding BLOB    NOT NULL,
        #             created_at TEXT   NOT NULL DEFAULT (datetime('now','localtime'))
        #         )
        #     """)
        #     con.execute("CREATE INDEX IF NOT EXISTS idx_name ON embeddings(name)")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def load_all(self):
        """Load every row from DB into in-memory numpy arrays."""
        with self._conn() as con:
            rows = con.execute(
                "SELECT id, name, embedding FROM embeddings ORDER BY id"
            ).fetchall()

        if not rows:
            self.ids = np.array([], dtype=np.int64)
            self.names = np.array([], dtype=object)
            self.embeddings = np.empty((0, EMBEDDING_DIM), dtype=np.float32)
            self.logger.info("[EmbeddingStore] loaded 0 embeddings")
            return

        ids, names, blobs = zip(*rows)
        self.ids = np.array(ids, dtype=np.int64)
        self.names = np.array(names, dtype=object)
        self.embeddings = np.vstack([
            _normalize(_from_blob(b)) for b in blobs
        ]).astype(np.float32)

        self.logger.info(f"[EmbeddingStore] loaded {len(self.names)} embeddings")

    def save(self, name: str, embedding) -> int:
        """Persist one embedding, update in-memory cache. Returns row id."""
        normalized = _normalize(embedding)
        blob = _to_blob(normalized)

        with self._conn() as con:
            cur = con.execute(
                "INSERT INTO embeddings (name, embedding) VALUES (?, ?)",
                (name, blob)
            )
            row_id = cur.lastrowid

        # Update cache
        self.ids = np.append(self.ids, row_id)
        self.names = np.append(self.names, name)

        if self.embeddings.size == 0:
            self.embeddings = normalized.reshape(1, -1)
        else:
            self.embeddings = np.vstack([self.embeddings, normalized])

        return row_id

    def delete(self, name: str) -> int:
        """Delete all embeddings for a person. Returns rows deleted."""
        mask = self.names != name
        with self._conn() as con:
            cur = con.execute("DELETE FROM embeddings WHERE name = ?", (name,))
            deleted = cur.rowcount

        # Rebuild cache without deleted entries
        self.ids = self.ids[mask]
        self.names = self.names[mask]
        self.embeddings = self.embeddings[mask] if self.embeddings.shape[0] else self.embeddings

        return deleted

    def get_names(self) -> list[str]:
        return sorted(set(self.names.tolist()))

    def compare(self, target_embedding, tolerance: float = 0.45) -> list[dict]:
        if self.embeddings.shape[0] == 0:
            return []

        target = _normalize(target_embedding)
        similarities = self.embeddings @ target
        distances = 1.0 - similarities

        matched_idx = np.where(distances < tolerance)[0]
        if len(matched_idx) == 0:
            return []

        order = np.argsort(distances[matched_idx])
        results = []
        for idx in matched_idx[order]:
            dist = float(distances[idx])
            results.append({
                "id": int(self.ids[idx]),
                "name": str(self.names[idx]),
                "distance": round(dist, 4),
                "confidence": round(max(0.0, 1.0 - dist / tolerance) * 100, 2),
            })

        return results