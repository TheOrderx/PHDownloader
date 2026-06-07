"""Persistent application settings backed by :class:`QSettings`.

A small typed wrapper provides sane defaults and coercion so callers never deal
with the platform-specific string serialisation that ``QSettings`` performs.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import QByteArray, QSettings

ORG = "PHDownloader"
APP = "PHDownloader"


def _default_output_dir() -> str:
    return str(Path.home() / "Downloads" / "PHDownloader")


# Every user-facing setting with its default value. The default's *type* drives
# coercion when reading the value back from disk.
DEFAULTS: Dict[str, Any] = {
    # General
    "output_dir": _default_output_dir(),
    "quality": "best",
    "format": "mp4",
    "theme": "dark",
    "language": "en",
    # Concurrency / network
    "concurrent": 3,
    "threads": 16,
    "proxy_type": "None",  # None | HTTP | SOCKS5
    "proxy_host": "",
    "proxy_port": "",
    "timeout": 60,
    "retries": 3,
    "rate_limit": 0.0,
    # Advanced
    "ffmpeg_path": "",       # empty -> auto-detect from PATH
    "user_agent": "",        # empty -> rotate built-in pool
    "cookies_file": "",
    "filename_template": "%(uploader)s/%(title)s_%(id)s.%(ext)s",
    # Toggles
    "download_thumbnail": True,
    "save_metadata": True,
    "embed_subtitles": False,
    "notifications": True,
    "minimize_to_tray": True,
}


class Settings:
    """Typed convenience wrapper around :class:`QSettings`."""

    def __init__(self) -> None:
        self._qs = QSettings(ORG, APP)

    def get(self, key: str) -> Any:
        """Return the value for ``key``, coerced to the default's type."""
        if key not in DEFAULTS:
            raise KeyError(f"Unknown setting: {key}")
        default = DEFAULTS[key]
        value = self._qs.value(key, default)
        if key == "language":
            from gui.utils.i18n import normalize_language

            return normalize_language(value)
        kind = type(default)
        if kind is bool:
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("1", "true", "yes", "on")
        if kind is int:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        if kind is float:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        return str(value)

    def set(self, key: str, value: Any) -> None:
        """Persist ``value`` for ``key``."""
        self._qs.setValue(key, value)

    def update(self, values: Dict[str, Any]) -> None:
        """Persist several settings at once."""
        for key, value in values.items():
            self.set(key, value)

    def all(self) -> Dict[str, Any]:
        """Return every known setting as a dict."""
        return {key: self.get(key) for key in DEFAULTS}

    # -- raw (non-typed) storage for window state etc. ---------------------

    def get_bytes(self, key: str) -> QByteArray:
        """Return a stored :class:`QByteArray` (e.g. window geometry)."""
        value = self._qs.value(key)
        return value if isinstance(value, QByteArray) else QByteArray()

    def set_bytes(self, key: str, value: QByteArray) -> None:
        self._qs.setValue(key, value)

    def get_raw(self, key: str, default: Any = None) -> Any:
        return self._qs.value(key, default)

    def set_raw(self, key: str, value: Any) -> None:
        self._qs.setValue(key, value)

    def sync(self) -> None:
        self._qs.sync()
