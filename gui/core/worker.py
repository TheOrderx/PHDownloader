"""Background download worker.

Each :class:`DownloadWorker` is a :class:`QThread` that drives the existing
``phvid`` backend :class:`downloader.Downloader` for a single URL, translating
its progress/metadata/cancellation hooks into Qt signals so the UI thread is
never blocked.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Dict

from PyQt6.QtCore import QThread, pyqtSignal


class DownloadWorker(QThread):
    """Runs one download in the background, reporting progress via signals."""

    sig_metadata = pyqtSignal(int, dict)   # item_id, metadata dict
    sig_progress = pyqtSignal(int, dict)   # item_id, progress dict
    sig_status = pyqtSignal(int, str)      # item_id, status string
    sig_finished = pyqtSignal(int, str, object)  # item_id, filepath, size
    sig_failed = pyqtSignal(int, str)      # item_id, error message
    sig_paused = pyqtSignal(int)           # item_id
    sig_cancelled = pyqtSignal(int)        # item_id

    def __init__(self, item_id: int, url: str, opts: Dict[str, object]) -> None:
        super().__init__()
        self.item_id = item_id
        self.url = url
        self.opts = opts
        self._cancel = threading.Event()
        self._mode = "download"  # download | pause | cancel
        self._processing_emitted = False

    # -- control (called from the GUI thread) ------------------------------

    def request_pause(self) -> None:
        self._mode = "pause"
        self._cancel.set()

    def request_cancel(self) -> None:
        self._mode = "cancel"
        self._cancel.set()

    # -- backend hooks (called from this worker thread) --------------------

    def _on_info(self, info, stream, path: Path) -> None:
        from utils import sidecar_path  # backend helper

        self.sig_metadata.emit(
            self.item_id,
            {
                "title": info.title,
                "uploader": info.uploader,
                "duration": info.duration,
                "quality": f"{stream.height}p",
                "protocol": stream.protocol,
                "thumbnail": str(sidecar_path(path, ".jpg")),
                "filepath": str(path),
            },
        )

    def _on_progress(self, data: Dict[str, object]) -> None:
        self.sig_progress.emit(self.item_id, data)
        frac = data.get("frac")
        if (
            not self._processing_emitted
            and isinstance(frac, float)
            and frac >= 0.999
        ):
            self._processing_emitted = True
            self.sig_status.emit(self.item_id, "processing")

    # -- thread body -------------------------------------------------------

    def run(self) -> None:  # noqa: N802 (Qt override)
        import config
        from downloader import DownloadCancelled, Downloader
        from utils import prepare_ffmpeg_environment

        try:
            self.sig_status.emit(self.item_id, "downloading")
            opts = self.opts

            custom_ffmpeg = str(opts.get("ffmpeg_path") or "").strip() or None
            resolved = prepare_ffmpeg_environment(custom_ffmpeg)
            if resolved is None:
                # First-run ffmpeg download may still be in progress in the GUI.
                deadline = time.monotonic() + 300.0
                while resolved is None and time.monotonic() < deadline:
                    if self._cancel.is_set():
                        raise DownloadCancelled()
                    time.sleep(0.5)
                    resolved = prepare_ffmpeg_environment(custom_ffmpeg)
            ffmpeg_ok = resolved is not None

            downloader = Downloader(
                output_dir=Path(str(opts["output_dir"])),
                quality=str(opts.get("quality", "best")),
                file_format=str(opts.get("format", "mp4")),
                threads=int(opts.get("threads", 16)),
                proxies=list(opts.get("proxies") or []),
                cookiefile=(str(opts["cookies_file"]) if opts.get("cookies_file") else None),
                no_metadata=not bool(opts.get("save_metadata", True)),
                no_thumbnail=not bool(opts.get("download_thumbnail", True)),
                rate_limit_mbps=float(opts.get("rate_limit", 0.0) or 0.0),
                filename_template=str(
                    opts.get("filename_template") or config.DEFAULT_FILENAME_TEMPLATE
                ),
                ffmpeg_path=custom_ffmpeg,
                no_ffmpeg=not ffmpeg_ok,
                progress_hook=self._on_progress,
                info_hook=self._on_info,
                cancel_event=self._cancel,
                show_progress_bar=False,
            )

            result = downloader.download(self.url)

            if result.status == "success":
                self.sig_finished.emit(
                    self.item_id, str(result.path or ""), int(result.size)
                )
            elif result.status == "cancelled":
                if self._mode == "pause":
                    self.sig_paused.emit(self.item_id)
                else:
                    self.sig_cancelled.emit(self.item_id)
            else:
                self.sig_failed.emit(self.item_id, result.error or "Unknown error")

        except DownloadCancelled:
            if self._mode == "pause":
                self.sig_paused.emit(self.item_id)
            else:
                self.sig_cancelled.emit(self.item_id)
        except Exception as exc:  # noqa: BLE001 - report any failure to the UI
            self.sig_failed.emit(self.item_id, str(exc))
