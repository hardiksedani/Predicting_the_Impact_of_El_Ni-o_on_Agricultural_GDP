"""Dual-mode storage service for the PBL Agriculture project.

Provides seamless fallback:
- If Firebase is configured with credentials, uses Firestore & Cloud Storage.
- If Firebase credentials are not present (e.g. local offline, college PC),
  transparently uses a local SQLite database and local file storage.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.constants import LOCAL_DATA_DIR, LOCAL_MODEL_CACHE_DIR
from app.services.firebase import init_firebase, get_settings

logger = logging.getLogger(__name__)

DB_PATH = Path(LOCAL_DATA_DIR) / "pbl_database.sqlite"
LOCAL_UPLOADS_DIR = Path(LOCAL_DATA_DIR) / "uploads"


def _is_firebase_configured() -> bool:
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if cred_path and os.path.isfile(cred_path):
        return True
    settings = get_settings()
    if settings.firebase_project_id and settings.firebase_storage_bucket:
        return True
    return False


def _get_sqlite_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _init_sqlite_tables(conn)
    return conn


def _init_sqlite_tables(conn: sqlite3.Connection) -> None:
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                collection TEXT,
                doc_id TEXT,
                data TEXT,
                updated_at TEXT,
                PRIMARY KEY (collection, doc_id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS model_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT,
                dataset_version TEXT,
                train_years TEXT,
                test_years TEXT,
                metrics TEXT,
                best_model TEXT,
                parameters TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                intent TEXT,
                response TEXT,
                created_at TEXT
            )
            """
        )


class LocalDoc:
    def __init__(self, doc_id: str, data: dict[str, Any], exists: bool = True):
        self.id = doc_id
        self._data = data
        self.exists = exists

    def to_dict(self) -> dict[str, Any]:
        return self._data.copy()


class LocalCollectionQuery:
    def __init__(self, collection: str, filters: list[tuple] | None = None, order: tuple | None = None, limit_n: int | None = None):
        self.collection = collection
        self.filters = filters or []
        self.order = order
        self.limit_n = limit_n

    def where(self, field: str, op: str, value: Any) -> "LocalCollectionQuery":
        new_filters = list(self.filters)
        new_filters.append((field, op, value))
        return LocalCollectionQuery(self.collection, new_filters, self.order, self.limit_n)

    def order_by(self, field: str, direction: str = "ASCENDING") -> "LocalCollectionQuery":
        return LocalCollectionQuery(self.collection, self.filters, (field, direction), self.limit_n)

    def limit(self, count: int) -> "LocalCollectionQuery":
        return LocalCollectionQuery(self.collection, self.filters, self.order, count)

    def stream(self):
        conn = _get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT doc_id, data FROM documents WHERE collection = ?", (self.collection,))
            rows = cursor.fetchall()
        finally:
            conn.close()

        matched = []
        for r in rows:
            doc_id = r["doc_id"]
            try:
                data = json.loads(r["data"])
            except Exception:
                continue

            matches = True
            for field, op, val in self.filters:
                doc_val = data.get(field)
                if op == "==" and doc_val != val:
                    matches = False
                    break
                elif op == ">=" and (doc_val is None or doc_val < val):
                    matches = False
                    break
                elif op == "<=" and (doc_val is None or doc_val > val):
                    matches = False
                    break
                elif op == ">" and (doc_val is None or doc_val <= val):
                    matches = False
                    break
                elif op == "<" and (doc_val is None or doc_val >= val):
                    matches = False
                    break

            if matches:
                matched.append(LocalDoc(doc_id, data))

        if self.order:
            field, direction = self.order
            reverse = direction.upper() in ("DESCENDING", "DESC")
            matched.sort(key=lambda d: d.to_dict().get(field) or 0, reverse=reverse)

        if self.limit_n:
            matched = matched[:self.limit_n]

        return matched

    def document(self, doc_id: str) -> "LocalDocRef":
        return LocalDocRef(self.collection, doc_id)

    def add(self, data: dict[str, Any]) -> tuple[Any, "LocalDocRef"]:
        import uuid
        doc_id = str(uuid.uuid4())
        ref = LocalDocRef(self.collection, doc_id)
        ref.set(data)
        return (None, ref)


class LocalDocRef:
    def __init__(self, collection: str, doc_id: str):
        self.collection = collection
        self.doc_id = doc_id

    def get(self) -> LocalDoc:
        conn = _get_sqlite_conn()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT data FROM documents WHERE collection = ? AND doc_id = ?",
                (self.collection, self.doc_id),
            )
            row = cursor.fetchone()
        finally:
            conn.close()
        if not row:
            return LocalDoc(self.doc_id, {}, exists=False)
        return LocalDoc(self.doc_id, json.loads(row["data"]), exists=True)

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        conn = _get_sqlite_conn()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            with conn:
                if merge:
                    existing = self.get()
                    if existing.exists:
                        merged_data = existing.to_dict()
                        merged_data.update(data)
                        data = merged_data

                conn.execute(
                    """
                    INSERT INTO documents (collection, doc_id, data, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(collection, doc_id) DO UPDATE SET
                        data = excluded.data,
                        updated_at = excluded.updated_at
                    """,
                    (self.collection, self.doc_id, json.dumps(data), now),
                )
        finally:
            conn.close()


class LocalBatch:
    def __init__(self):
        self._ops = []

    def set(self, doc_ref: LocalDocRef, data: dict[str, Any], merge: bool = False):
        self._ops.append((doc_ref, data, merge))

    def commit(self):
        conn = _get_sqlite_conn()
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            with conn:
                for doc_ref, data, merge in self._ops:
                    final_data = data
                    if merge:
                        cur = conn.cursor()
                        cur.execute(
                            "SELECT data FROM documents WHERE collection = ? AND doc_id = ?",
                            (doc_ref.collection, doc_ref.doc_id),
                        )
                        row = cur.fetchone()
                        if row:
                            try:
                                d = json.loads(row["data"])
                                d.update(data)
                                final_data = d
                            except Exception:
                                pass
                    conn.execute(
                        """
                        INSERT INTO documents (collection, doc_id, data, updated_at)
                        VALUES (?, ?, ?, ?)
                        ON CONFLICT(collection, doc_id) DO UPDATE SET
                            data = excluded.data,
                            updated_at = excluded.updated_at
                        """,
                        (doc_ref.collection, doc_ref.doc_id, json.dumps(final_data), now),
                    )
        finally:
            conn.close()
        self._ops.clear()


class LocalBlob:
    def __init__(self, path: str):
        self.path = path
        self.full_path = Path(LOCAL_DATA_DIR) / path

    def exists(self) -> bool:
        return self.full_path.is_file()

    def upload_from_filename(self, local_path: str) -> None:
        self.full_path.parent.mkdir(parents=True, exist_ok=True)
        if Path(local_path).resolve() == self.full_path.resolve():
            return
        import shutil
        shutil.copy2(local_path, str(self.full_path))

    def upload_from_string(self, data: bytes | str, content_type: str = "text/plain") -> None:
        self.full_path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.full_path.write_bytes(data)

    def download_to_filename(self, target_path: str) -> None:
        Path(target_path).parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(str(self.full_path), target_path)


class LocalBucket:
    def blob(self, path: str) -> LocalBlob:
        return LocalBlob(path)


class LocalFirestoreAdapter:
    def collection(self, name: str) -> LocalCollectionQuery:
        return LocalCollectionQuery(name)

    def batch(self) -> LocalBatch:
        return LocalBatch()


def get_db():
    """Returns Firestore client if configured, otherwise returns local SQLite adapter."""
    if _is_firebase_configured():
        try:
            from app.services.firebase import get_firestore_client
            return get_firestore_client()
        except Exception as exc:
            logger.warning("Firebase not available, falling back to local DB: %s", exc)
    return LocalFirestoreAdapter()


def get_storage():
    """Returns Cloud Storage bucket if configured, otherwise returns local file bucket."""
    if _is_firebase_configured():
        try:
            from app.services.firebase import get_storage_bucket
            return get_storage_bucket()
        except Exception as exc:
            logger.warning("Storage bucket not available, falling back to local storage: %s", exc)
    return LocalBucket()
