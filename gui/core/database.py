"""SQLite-backed download history storage.

Kept deliberately framework-free (plain :mod:`sqlite3`) so it is easy to test
and reuse. A lock guards the single shared connection because completions are
written from the GUI thread while reads may happen from the same thread.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional


class HistoryDB:
    """Persists completed/failed downloads in ``history.db``."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create()

    def _create(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    url         TEXT NOT NULL,
                    title       TEXT,
                    uploader    TEXT,
                    quality     TEXT,
                    file_format TEXT,
                    filepath    TEXT,
                    thumbnail   TEXT,
                    size        INTEGER DEFAULT 0,
                    duration    INTEGER DEFAULT 0,
                    status      TEXT,
                    created_at  TEXT
                )
                """
            )

    def add(self, record: Dict[str, object]) -> int:
        """Insert a history row and return its new id."""
        row = (
            str(record.get("url", "")),
            str(record.get("title", "")),
            str(record.get("uploader", "")),
            str(record.get("quality", "")),
            str(record.get("file_format", "")),
            str(record.get("filepath", "")),
            str(record.get("thumbnail", "")),
            int(record.get("size", 0) or 0),
            int(record.get("duration", 0) or 0),
            str(record.get("status", "complete")),
            str(record.get("created_at") or time.strftime("%Y-%m-%d %H:%M")),
        )
        with self._lock, self._conn:
            cur = self._conn.execute(
                """
                INSERT INTO history
                    (url, title, uploader, quality, file_format, filepath,
                     thumbnail, size, duration, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            return int(cur.lastrowid)

    def all(self) -> List[Dict[str, object]]:
        """Return all history rows, newest first."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM history ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def search(self, query: str) -> List[Dict[str, object]]:
        """Return rows whose title/uploader/url match ``query``."""
        if not query.strip():
            return self.all()
        like = f"%{query.strip()}%"
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT * FROM history
                WHERE title LIKE ? OR uploader LIKE ? OR url LIKE ?
                ORDER BY id DESC
                """,
                (like, like, like),
            ).fetchall()
        return [dict(r) for r in rows]

    def get(self, row_id: int) -> Optional[Dict[str, object]]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM history WHERE id = ?", (row_id,)
            ).fetchone()
        return dict(row) if row else None

    def remove(self, row_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM history WHERE id = ?", (row_id,))

    def clear(self) -> None:
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM history")

    def close(self) -> None:
        with self._lock:
            self._conn.close()
