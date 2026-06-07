"""Download queue and worker orchestration.

:class:`DownloadManager` owns the queue, enforces the concurrency limit, starts
:class:`DownloadWorker` threads, relays their signals into item-state updates,
and records completed downloads in the history database.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from gui.core.database import HistoryDB
from gui.core.worker import DownloadWorker
from gui.utils.settings import Settings


@dataclass
class DownloadItem:
    """Live state for a single queued/active download."""

    id: int
    url: str
    opts: Dict[str, object]
    title: str = "Resolving…"
    uploader: str = ""
    duration: int = 0
    quality: str = ""
    file_format: str = "mp4"
    status: str = "queued"
    percent: float = 0.0
    speed: float = 0.0
    eta: Optional[float] = None
    downloaded: int = 0
    total: Optional[int] = None
    filepath: str = ""
    thumbnail: str = ""
    size: int = 0
    error: str = ""


def proxies_from_settings(settings: Settings) -> List[str]:
    """Build a proxy URL list from the stored proxy settings."""
    proxy_type = settings.get("proxy_type")
    host = settings.get("proxy_host").strip()
    port = settings.get("proxy_port").strip()
    if proxy_type in ("None", "") or not host:
        return []
    scheme = "socks5" if proxy_type.lower().startswith("socks") else "http"
    netloc = f"{host}:{port}" if port else host
    return [f"{scheme}://{netloc}"]


class DownloadManager(QObject):
    """Manages the download queue and the pool of worker threads."""

    item_added = pyqtSignal(int)
    item_updated = pyqtSignal(int)
    item_removed = pyqtSignal(int)
    history_changed = pyqtSignal()
    counts_changed = pyqtSignal()
    download_complete = pyqtSignal(int, str)  # item_id, title (for notifications)

    def __init__(self, settings: Settings, db_path: Path) -> None:
        super().__init__()
        self.settings = settings
        self.db = HistoryDB(db_path)
        self._items: Dict[int, DownloadItem] = {}
        self._order: List[int] = []
        self._workers: Dict[int, DownloadWorker] = {}
        self._next_id = 1
        self.max_concurrent = max(1, settings.get("concurrent"))

    # -- queue management --------------------------------------------------

    def items(self) -> List[DownloadItem]:
        return [self._items[i] for i in self._order if i in self._items]

    def get(self, item_id: int) -> Optional[DownloadItem]:
        return self._items.get(item_id)

    def add(self, url: str, opts: Dict[str, object]) -> int:
        """Queue a new download and start it if a slot is free."""
        item_id = self._next_id
        self._next_id += 1
        item = DownloadItem(
            id=item_id,
            url=url,
            opts=opts,
            quality=str(opts.get("quality", "best")),
            file_format=str(opts.get("format", "mp4")),
        )
        self._items[item_id] = item
        self._order.append(item_id)
        self.item_added.emit(item_id)
        self.counts_changed.emit()
        self._pump()
        return item_id

    def set_max_concurrent(self, value: int) -> None:
        self.max_concurrent = max(1, int(value))
        self._pump()

    def _active_count(self) -> int:
        return len(self._workers)

    def _pump(self) -> None:
        """Start queued items until the concurrency limit is reached."""
        for item_id in self._order:
            if self._active_count() >= self.max_concurrent:
                break
            item = self._items.get(item_id)
            if item and item.status == "queued" and item_id not in self._workers:
                self._start(item)

    def _start(self, item: DownloadItem) -> None:
        worker = DownloadWorker(item.id, item.url, item.opts)
        worker.sig_metadata.connect(self._on_metadata)
        worker.sig_progress.connect(self._on_progress)
        worker.sig_status.connect(self._on_status)
        worker.sig_finished.connect(self._on_finished)
        worker.sig_failed.connect(self._on_failed)
        worker.sig_paused.connect(self._on_paused)
        worker.sig_cancelled.connect(self._on_cancelled)
        self._workers[item.id] = worker
        item.status = "downloading"
        worker.start()
        self.item_updated.emit(item.id)
        self.counts_changed.emit()

    def _retire_worker(self, item_id: int) -> None:
        worker = self._workers.pop(item_id, None)
        if worker is not None:
            worker.wait(3000)
            worker.deleteLater()

    # -- per-item controls -------------------------------------------------

    def pause(self, item_id: int) -> None:
        item = self._items.get(item_id)
        if not item:
            return
        worker = self._workers.get(item_id)
        if worker is not None:
            worker.request_pause()  # terminal signal will flip status
        elif item.status == "queued":
            item.status = "paused"
            self.item_updated.emit(item_id)
            self.counts_changed.emit()

    def resume(self, item_id: int) -> None:
        item = self._items.get(item_id)
        if item and item.status in ("paused", "failed"):
            item.status = "queued"
            item.error = ""
            self.item_updated.emit(item_id)
            self._pump()
            self.counts_changed.emit()

    def cancel(self, item_id: int) -> None:
        item = self._items.get(item_id)
        if not item:
            return
        worker = self._workers.get(item_id)
        if worker is not None:
            worker.request_cancel()  # terminal signal removes the item
        else:
            self._remove_item(item_id, delete_partial=True)

    def retry(self, item_id: int) -> None:
        self.resume(item_id)

    def pause_all(self) -> None:
        for item_id in list(self._order):
            item = self._items.get(item_id)
            if item and item.status in ("downloading", "queued"):
                self.pause(item_id)

    def resume_all(self) -> None:
        for item_id in list(self._order):
            item = self._items.get(item_id)
            if item and item.status == "paused":
                item.status = "queued"
                item.error = ""
                self.item_updated.emit(item_id)
        self._pump()
        self.counts_changed.emit()

    def clear_completed(self) -> None:
        for item_id in [i for i in self._order if self._items.get(i) and self._items[i].status == "complete"]:
            self._remove_item(item_id, delete_partial=False)

    def clear_failed(self) -> None:
        for item_id in [i for i in self._order if self._items.get(i) and self._items[i].status == "failed"]:
            self._remove_item(item_id, delete_partial=False)

    def _remove_item(self, item_id: int, delete_partial: bool) -> None:
        item = self._items.pop(item_id, None)
        if item_id in self._order:
            self._order.remove(item_id)
        if item and delete_partial:
            self._delete_partials(item)
        self.item_removed.emit(item_id)
        self.counts_changed.emit()
        self._pump()

    @staticmethod
    def _delete_partials(item: DownloadItem) -> None:
        from utils import safe_remove  # backend helper

        if not item.filepath:
            return
        video = Path(item.filepath)
        safe_remove(video.with_name(video.name + ".part"))
        safe_remove(video.with_name(video.stem + ".segments"))

    # -- worker signal handlers (GUI thread) -------------------------------

    def _on_metadata(self, item_id: int, meta: Dict[str, object]) -> None:
        item = self._items.get(item_id)
        if not item:
            return
        item.title = str(meta.get("title") or item.title)
        item.uploader = str(meta.get("uploader") or "")
        item.duration = int(meta.get("duration") or 0)
        item.quality = str(meta.get("quality") or item.quality)
        item.thumbnail = str(meta.get("thumbnail") or "")
        item.filepath = str(meta.get("filepath") or "")
        self.item_updated.emit(item_id)

    def _on_progress(self, item_id: int, data: Dict[str, object]) -> None:
        item = self._items.get(item_id)
        if not item:
            return
        frac = data.get("frac")
        item.percent = float(frac) * 100.0 if isinstance(frac, (int, float)) else item.percent
        item.speed = float(data.get("speed") or 0.0)
        eta = data.get("eta")
        item.eta = float(eta) if isinstance(eta, (int, float)) else None
        item.downloaded = int(data.get("downloaded") or 0)
        total = data.get("total")
        item.total = int(total) if isinstance(total, int) else None
        self.item_updated.emit(item_id)

    def _on_status(self, item_id: int, status: str) -> None:
        item = self._items.get(item_id)
        if item:
            item.status = status
            self.item_updated.emit(item_id)
            self.counts_changed.emit()

    def _on_finished(self, item_id: int, filepath: str, size: object) -> None:
        item = self._items.get(item_id)
        self._retire_worker(item_id)
        if not item:
            return
        item.status = "complete"
        item.filepath = filepath or item.filepath
        item.size = int(size) if size else 0
        item.percent = 100.0
        item.speed = 0.0
        item.eta = 0.0
        self.item_updated.emit(item_id)
        self._record_history(item)
        self.download_complete.emit(item_id, item.title)
        self.counts_changed.emit()
        self._pump()

    def _on_failed(self, item_id: int, error: str) -> None:
        item = self._items.get(item_id)
        self._retire_worker(item_id)
        if not item:
            return
        item.status = "failed"
        item.error = error
        self.item_updated.emit(item_id)
        self.counts_changed.emit()
        self._pump()

    def _on_paused(self, item_id: int) -> None:
        item = self._items.get(item_id)
        self._retire_worker(item_id)
        if not item:
            return
        item.status = "paused"
        self.item_updated.emit(item_id)
        self.counts_changed.emit()
        self._pump()

    def _on_cancelled(self, item_id: int) -> None:
        self._retire_worker(item_id)
        self._remove_item(item_id, delete_partial=True)

    def _record_history(self, item: DownloadItem) -> None:
        self.db.add(
            {
                "url": item.url,
                "title": item.title,
                "uploader": item.uploader,
                "quality": item.quality,
                "file_format": item.file_format,
                "filepath": item.filepath,
                "thumbnail": item.thumbnail,
                "size": item.size,
                "duration": item.duration,
                "status": "complete",
            }
        )
        self.history_changed.emit()

    # -- lifecycle ---------------------------------------------------------

    def shutdown(self) -> None:
        """Stop all workers (keeping partials) and close the database."""
        for worker in list(self._workers.values()):
            worker.request_pause()
        for item_id in list(self._workers.keys()):
            self._retire_worker(item_id)
        self.db.close()
