"""A single download represented as a rich, self-updating card."""

from __future__ import annotations

import os
from typing import Optional

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from gui.core.download_manager import DownloadItem
from gui.utils.i18n import i18n, tr
from gui.widgets.custom_widgets import IconButton, StatusBadge, colored_pixmap, repolish
from gui.utils.theme import theme_manager
from utils import format_duration, format_size

THUMB_W, THUMB_H = 120, 68


class DownloadCard(QFrame):
    """Displays one :class:`DownloadItem` with live progress and actions."""

    pause_clicked = pyqtSignal(int)
    resume_clicked = pyqtSignal(int)
    cancel_clicked = pyqtSignal(int)
    open_clicked = pyqtSignal(int)
    selected = pyqtSignal(int)

    def __init__(self, item: DownloadItem, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Card")
        self.item_id = item.id
        self._status = item.status
        self._title_text = item.title
        self.item = item

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(14)

        self.thumb = QLabel()
        self.thumb.setObjectName("CardThumb")
        self.thumb.setFixedSize(THUMB_W, THUMB_H)
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.thumb)

        middle = QVBoxLayout()
        middle.setSpacing(6)
        self.title_label = QLabel(item.title)
        self.title_label.setObjectName("CardTitle")
        self.sub_label = QLabel("")
        self.sub_label.setObjectName("CardSub")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)

        self.progress_text = QLabel("")
        self.progress_text.setObjectName("CardProgressText")

        middle.addWidget(self.title_label)
        middle.addWidget(self.sub_label)
        middle.addStretch(1)
        middle.addWidget(self.progress)
        middle.addWidget(self.progress_text)
        root.addLayout(middle, 1)

        right = QVBoxLayout()
        right.setSpacing(8)
        self.badge = StatusBadge(item.status)
        right.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignRight)
        right.addStretch(1)

        actions = QHBoxLayout()
        actions.setSpacing(4)
        self.pause_btn = IconButton("pause", role="TEXT_DIM", size=16)
        self.open_btn = IconButton("folder", role="TEXT_DIM", size=16)
        self.cancel_btn = IconButton("x", role="TEXT_DIM", size=16)
        self.pause_btn.clicked.connect(self._on_pause_resume)
        self.open_btn.clicked.connect(lambda: self.open_clicked.emit(self.item_id))
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.item_id))
        actions.addWidget(self.pause_btn)
        actions.addWidget(self.open_btn)
        actions.addWidget(self.cancel_btn)
        right.addLayout(actions)
        root.addLayout(right)

        self.setMinimumHeight(THUMB_H + 28)
        theme_manager.changed.connect(self._on_theme_changed)
        i18n.language_changed.connect(lambda _c: self.retranslate_ui())
        self.update_from_item(item)

    def retranslate_ui(self) -> None:
        self.update_from_item(self.item)

    def _on_theme_changed(self, *_: object) -> None:
        self._set_thumbnail(self.item.thumbnail)

    # -- updates -----------------------------------------------------------

    def update_from_item(self, item: DownloadItem) -> None:
        """Refresh every visual element from the current item state."""
        self.item = item
        self._status = item.status
        self._title_text = item.title or tr("card.resolving")
        self._apply_elide()

        sub_parts = [p for p in (
            item.uploader or "",
            format_duration(item.duration) if item.duration else "",
            item.quality or "",
        ) if p]
        self.sub_label.setText("  •  ".join(sub_parts) or "—")

        self._set_thumbnail(item.thumbnail)
        self.badge.set_status(item.status)
        self.progress.setValue(int(round(item.percent)))
        self._set_progress_state(item.status)
        self.progress_text.setText(self._progress_text(item))
        self.progress_text.setToolTip(item.error if item.status == "failed" else "")
        self._update_buttons(item.status)

    def _progress_text(self, item: DownloadItem) -> str:
        if item.status == "queued":
            return tr("card.waiting")
        if item.status == "downloading":
            speed = f"{format_size(item.speed)}/s" if item.speed else "—"
            eta = (
                tr("card.eta", value=format_duration(item.eta))
                if item.eta
                else tr("card.eta_unknown")
            )
            return tr(
                "card.progress",
                percent=item.percent,
                speed=speed,
                eta=eta,
            )
        if item.status == "processing":
            return tr("card.merging")
        if item.status == "paused":
            return tr("card.paused_at", percent=item.percent)
        if item.status == "complete":
            return (
                tr("card.complete_size", size=format_size(item.size))
                if item.size
                else tr("card.complete")
            )
        if item.status == "failed":
            return (
                tr("card.failed_detail", error=item.error[:80])
                if item.error
                else tr("card.failed")
            )
        return ""

    def _set_progress_state(self, status: str) -> None:
        mapping = {
            "complete": "complete",
            "failed": "failed",
            "paused": "paused",
        }
        self.progress.setProperty("state", mapping.get(status, "downloading"))
        repolish(self.progress)

    def _update_buttons(self, status: str) -> None:
        if status in ("downloading", "queued", "processing"):
            self.pause_btn.setVisible(status != "processing")
            self.pause_btn.set_icon_name("pause")
            self.pause_btn.setToolTip(tr("card.tooltip.pause"))
        elif status in ("paused", "failed"):
            self.pause_btn.setVisible(True)
            self.pause_btn.set_icon_name("play")
            self.pause_btn.setToolTip(
                tr("card.tooltip.resume")
                if status == "paused"
                else tr("card.tooltip.retry")
            )
        else:
            self.pause_btn.setVisible(False)

        self.open_btn.setVisible(status == "complete")
        self.open_btn.setToolTip(tr("card.tooltip.open_folder"))
        self.cancel_btn.setVisible(status != "complete")
        self.cancel_btn.setToolTip(tr("card.tooltip.cancel"))

    def _on_pause_resume(self) -> None:
        if self._status in ("downloading", "queued"):
            self.pause_clicked.emit(self.item_id)
        elif self._status in ("paused", "failed"):
            self.resume_clicked.emit(self.item_id)

    # -- thumbnail / elide -------------------------------------------------

    def _set_thumbnail(self, path: str) -> None:
        pixmap = QPixmap(path) if path and os.path.exists(path) else QPixmap()
        if pixmap.isNull():
            self.thumb.setPixmap(colored_pixmap("film", theme_manager.color("TEXT_MUTED"), 30))
            return
        scaled = pixmap.scaled(
            QSize(THUMB_W, THUMB_H),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        x = max(0, (scaled.width() - THUMB_W) // 2)
        y = max(0, (scaled.height() - THUMB_H) // 2)
        self.thumb.setPixmap(scaled.copy(x, y, THUMB_W, THUMB_H))

    def _apply_elide(self) -> None:
        metrics = QFontMetrics(self.title_label.font())
        width = max(120, self.title_label.width())
        self.title_label.setText(
            metrics.elidedText(self._title_text, Qt.TextElideMode.ElideRight, width)
        )

    def set_selected(self, value: bool) -> None:
        self.setProperty("selected", value)
        repolish(self)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.item_id)
        super().mousePressEvent(event)

    def resizeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        super().resizeEvent(event)
        self._apply_elide()
