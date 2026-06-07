"""Locate or auto-install ffmpeg/ffprobe.

Deliberately thin wrapper around :mod:`utils` so the bootstrap launcher can call
it before any third-party packages are installed. On Windows, a static build is
downloaded once into the per-user data directory when nothing else is found.
"""

from __future__ import annotations

import os
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Dict

from utils import prepare_ffmpeg_environment, resolve_ffmpeg

# BtbN publishes reliable, self-contained Windows builds with a stable "latest"
# download URL containing ffmpeg.exe and ffprobe.exe under <root>/bin/.
FFMPEG_WIN_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/latest/download/"
    "ffmpeg-master-latest-win64-gpl.zip"
)

# Progress callback: (message_id, percent). percent is -1 for indeterminate steps.
# ``message_id`` values map to ``ffmpeg.*`` keys in ``gui.utils.i18n``.
ProgressFn = Callable[[str, int], None]

_CONSOLE_MSG: Dict[str, str] = {
    "ffmpeg.preparing": "Preparing ffmpeg download…",
    "ffmpeg.downloading": "Downloading ffmpeg…",
    "ffmpeg.extracting": "Extracting ffmpeg…",
    "ffmpeg.ready": "ffmpeg ready.",
    "ffmpeg.incomplete": "ffmpeg install incomplete.",
    "ffmpeg.not_found_unix": (
        "ffmpeg not found. Install it via your package manager "
        "(e.g. 'brew install ffmpeg' or 'apt install ffmpeg')."
    ),
}


def _default_progress(message_id: str, percent: int = -1) -> None:
    """Console progress reporter used when no callback is supplied."""
    text = _CONSOLE_MSG.get(message_id, message_id)
    print(text if percent < 0 else f"{text} {percent}%")


def data_dir() -> Path:
    """Return the per-user data directory (stdlib-only, no Qt dependency)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "PHDownloader"
    return Path.home() / ".phdownloader"


def bin_dir() -> Path:
    """Directory where a downloaded ffmpeg is stored."""
    return data_dir() / "bin"


def add_known_bins_to_path() -> None:
    """Prepend every known ffmpeg directory onto ``PATH``."""
    prepare_ffmpeg_environment(None)


def has_ffmpeg() -> bool:
    """Return True if both ffmpeg and ffprobe can be located."""
    return resolve_ffmpeg() is not None


def _download(url: str, dest: Path, progress: ProgressFn) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "PHDownloader"})
    with urllib.request.urlopen(request) as response, open(dest, "wb") as handle:
        total = int(response.headers.get("Content-Length") or 0)
        read = 0
        last_pct = -1
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            handle.write(chunk)
            read += len(chunk)
            if total:
                pct = read * 100 // total
                if pct != last_pct:
                    last_pct = pct
                    progress("ffmpeg.downloading", pct)
            else:
                progress("ffmpeg.downloading", -1)


def ensure_ffmpeg(progress: ProgressFn = _default_progress) -> bool:
    """Ensure ffmpeg/ffprobe are available, downloading them on Windows if not.

    ``progress(message, percent)`` is called throughout (percent is -1 for the
    indeterminate phases). Returns True if ffmpeg is available afterwards.
    """
    add_known_bins_to_path()
    if has_ffmpeg():
        return True
    if os.name != "nt":
        progress("ffmpeg.not_found_unix", -1)
        return False

    target = bin_dir()
    target.mkdir(parents=True, exist_ok=True)
    progress("ffmpeg.preparing", 0)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "ffmpeg.zip"
            _download(FFMPEG_WIN_URL, archive, progress)
            progress("ffmpeg.extracting", -1)
            with zipfile.ZipFile(archive) as zf:
                for name in zf.namelist():
                    lower = name.lower().replace("\\", "/")
                    if lower.endswith("/bin/ffmpeg.exe") or lower.endswith("/bin/ffprobe.exe"):
                        (target / Path(name).name).write_bytes(zf.read(name))
        add_known_bins_to_path()
        ok = has_ffmpeg()
        progress("ffmpeg.ready" if ok else "ffmpeg.incomplete", 100)
        return ok
    except Exception as exc:  # noqa: BLE001 - best-effort, never fatal
        _CONSOLE_MSG["ffmpeg.install_failed"] = f"Could not auto-install ffmpeg: {exc}"
        progress("ffmpeg.install_failed", -1)
        return False
