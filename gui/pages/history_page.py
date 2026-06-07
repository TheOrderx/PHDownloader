"""History page: a searchable, sortable table backed by the SQLite store."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from gui.core.download_manager import DownloadManager, proxies_from_settings
from gui.utils.i18n import i18n, tr
from gui.utils.settings import Settings
from gui.widgets.custom_widgets import IconButton, colored_icon
from gui.utils.theme import theme_manager
from utils import format_size

_HISTORY_COLUMNS = [
    "history.col.preview",
    "history.col.title",
    "history.col.uploader",
    "history.col.quality",
    "history.col.size",
    "history.col.date",
    "history.col.status",
]


class _NumericItem(QTableWidgetItem):
    """Table item that sorts by a numeric value stored in ``UserRole``."""

    def __lt__(self, other: QTableWidgetItem) -> bool:  # noqa: D401
        a = self.data(Qt.ItemDataRole.UserRole) or 0
        b = other.data(Qt.ItemDataRole.UserRole) or 0
        return float(a) < float(b)


class HistoryPage(QWidget):
    """Displays completed downloads with search and a right-click action menu."""

    def __init__(
        self, settings: Settings, manager: DownloadManager, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.manager = manager
        self.db = manager.db

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)

        root.addLayout(self._build_header())
        root.addWidget(self._build_search())
        root.addWidget(self._build_table(), 1)

        i18n.language_changed.connect(lambda _c: self.retranslate_ui())
        self.reload()
        self.retranslate_ui()

    # -- builders ----------------------------------------------------------

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self._title = QLabel()
        self._title.setObjectName("PageTitle")
        layout.addWidget(self._title)
        layout.addStretch(1)
        return layout

    def _build_search(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.search = QLineEdit()
        self.search.textChanged.connect(lambda text: self.reload(text))
        self.clear_btn = IconButton("trash", role="TEXT_DIM", size=16)
        self.clear_btn.clicked.connect(self._clear_all)
        layout.addWidget(self.search, 1)
        layout.addWidget(self.clear_btn)
        return row

    def _build_table(self) -> QTableWidget:
        self.table = QTableWidget(0, len(_HISTORY_COLUMNS))
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setShowGrid(False)
        self.table.setIconSize(QSize(72, 40))
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_menu)
        self.table.doubleClicked.connect(lambda _i: self._open_file())

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (0, 2, 3, 4, 5, 6):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setHighlightSections(False)
        return self.table

    def retranslate_ui(self) -> None:
        self._title.setText(tr("history.title"))
        self.search.setPlaceholderText(tr("history.search"))
        self.clear_btn.setToolTip(tr("history.clear_tooltip"))
        self.table.setHorizontalHeaderLabels([tr(key) for key in _HISTORY_COLUMNS])

    # -- data --------------------------------------------------------------

    def reload(self, query: str = "") -> None:
        rows = self.db.search(query) if query else self.db.all()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r, rec in enumerate(rows):
            self.table.setRowHeight(r, 48)

            preview = QTableWidgetItem()
            preview.setIcon(self._thumb_icon(str(rec.get("thumbnail") or "")))
            preview.setData(Qt.ItemDataRole.UserRole, int(rec.get("id", 0)))
            self.table.setItem(r, 0, preview)

            title = QTableWidgetItem(str(rec.get("title") or "—"))
            title.setData(Qt.ItemDataRole.UserRole, dict(rec))
            self.table.setItem(r, 1, title)

            self.table.setItem(r, 2, QTableWidgetItem(str(rec.get("uploader") or "—")))
            self.table.setItem(r, 3, QTableWidgetItem(str(rec.get("quality") or "—")))

            size = int(rec.get("size") or 0)
            size_item = _NumericItem(format_size(size) if size else "—")
            size_item.setData(Qt.ItemDataRole.UserRole, size)
            self.table.setItem(r, 4, size_item)

            self.table.setItem(r, 5, QTableWidgetItem(str(rec.get("created_at") or "—")))
            self.table.setItem(r, 6, QTableWidgetItem(str(rec.get("status") or "—").title()))
        self.table.setSortingEnabled(True)

    def _thumb_icon(self, path: str) -> QIcon:
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                return QIcon(
                    pixmap.scaled(
                        QSize(72, 40),
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        return colored_icon("film", theme_manager.color("TEXT_MUTED"), 24)

    def _current_record(self) -> Optional[Dict[str, object]]:
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 1)
        if item is None:
            return None
        record = item.data(Qt.ItemDataRole.UserRole)
        return record if isinstance(record, dict) else None

    # -- actions -----------------------------------------------------------

    def _show_menu(self, pos) -> None:
        record = self._current_record()
        if record is None:
            index = self.table.indexAt(pos)
            if index.isValid():
                self.table.selectRow(index.row())
                record = self._current_record()
        if record is None:
            return

        menu = QMenu(self)
        act_redownload = menu.addAction(tr("history.menu.redownload"))
        act_open_file = menu.addAction(tr("history.menu.open_file"))
        act_open_folder = menu.addAction(tr("history.menu.open_folder"))
        act_copy = menu.addAction(tr("history.menu.copy_url"))
        menu.addSeparator()
        act_remove = menu.addAction(tr("history.menu.remove"))

        chosen = menu.exec(self.table.viewport().mapToGlobal(pos))
        if chosen == act_redownload:
            self._redownload(record)
        elif chosen == act_open_file:
            self._open_file()
        elif chosen == act_open_folder:
            self._open_folder()
        elif chosen == act_copy:
            QApplication.clipboard().setText(str(record.get("url") or ""))
        elif chosen == act_remove:
            self.db.remove(int(record.get("id", 0)))
            self.reload(self.search.text())

    def _redownload(self, record: Dict[str, object]) -> None:
        s = self.settings
        opts = {
            "output_dir": s.get("output_dir"),
            "quality": s.get("quality"),
            "format": s.get("format"),
            "threads": s.get("threads"),
            "proxies": proxies_from_settings(s),
            "cookies_file": s.get("cookies_file"),
            "save_metadata": s.get("save_metadata"),
            "download_thumbnail": s.get("download_thumbnail"),
            "rate_limit": s.get("rate_limit"),
            "filename_template": s.get("filename_template"),
            "ffmpeg_path": s.get("ffmpeg_path"),
        }
        self.manager.add(str(record.get("url") or ""), opts)

    def _open_file(self) -> None:
        record = self._current_record()
        if record and record.get("filepath") and os.path.exists(str(record["filepath"])):
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(record["filepath"])))

    def _open_folder(self) -> None:
        record = self._current_record()
        if not record or not record.get("filepath"):
            return
        folder = Path(str(record["filepath"])).parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _clear_all(self) -> None:
        self.db.clear()
        self.reload()
