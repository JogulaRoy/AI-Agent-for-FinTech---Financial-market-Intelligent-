"""
Tiny SQLite-backed key/value cache with per-entry TTL.

Kept deliberately simple. The schema is generic enough that the same access
pattern can later be pointed at PostgreSQL when a backend is introduced.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional

from app.config.settings import settings

_LOCK = threading.Lock()


class Cache:
    def __init__(self, db_path: Optional[Path] = None, default_ttl: Optional[int] = None):
        self.db_path = Path(db_path or settings.cache_db_path)
        self.default_ttl = default_ttl or settings.cache_ttl_seconds
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with _LOCK, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key         TEXT PRIMARY KEY,
                    value       TEXT NOT NULL,
                    stored_at   REAL NOT NULL,
                    expires_at  REAL NOT NULL
                )
                """
            )

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        with _LOCK, self._connect() as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache_entries WHERE key = ?", (key,)
            ).fetchone()
            if not row:
                return None
            value, expires_at = row
            if expires_at < now:
                conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
                return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = self.default_ttl if ttl is None else ttl
        now = time.time()
        payload = json.dumps(value, default=str)
        with _LOCK, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache_entries (key, value, stored_at, expires_at) "
                "VALUES (?, ?, ?, ?)",
                (key, payload, now, now + ttl),
            )

    def clear(self) -> None:
        with _LOCK, self._connect() as conn:
            conn.execute("DELETE FROM cache_entries")


cache = Cache()
