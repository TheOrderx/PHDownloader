"""Queue page: a live, scrollable list of download cards with bulk actions."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.core.download_manager import DownloadManager
from gui.utils.i18n import i18n, tr
from gui.widgets.custom_widgets import TextButton, ThemedIconLabel
from gui.widgets.download_card import DownloadCard


class QueuePage(QWidget):
    """Shows every active/queued download and lets the user manage them."""

    def __init__(self, manager: DownloadManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.manager = manager
        self.cards: Dict[int, DownloadCard] = {}
        self.selected_id: Optional[int] = None

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)

        root.addLayout(self._build_header())
        root.addWidget(self._build_toolbar())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        self.cards_layout = QVBoxLayout(content)
        self.cards_layout.setContentsMargins(0, 0, 6, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch(1)
        self.scroll.setWidget(content)
        root.addWidget(self.scroll, 1)

        self.empty = self._build_empty_state()
        root.addWidget(self.empty, 1)

        manager.item_added.connect(self._on_item_added)
        manager.item_updated.connect(self._on_item_updated)
        manager.item_removed.connect(self._on_item_removed)
        manager.counts_changed.connect(self._update_count)
        i18n.language_changed.connect(lambda _c: self.retranslate_ui())

        self._sync_empty_state()
        self.retranslate_ui()

    # -- builders ----------------------------------------------------------

    def _build_header(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self._title = QLabel()
        self._title.setObjectName("PageTitle")
        self.count_label = QLabel("")
        self.count_label.setObjectName("PageSubtitle")
        layout.addWidget(self._title)
        layout.addSpacing(10)
        layout.addWidget(self.count_label)
        layout.addStretch(1)
        return layout

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.pause_all_btn = TextButton(variant="ghost", icon_name="pause")
        self.resume_all_btn = TextButton(variant="ghost", icon_name="play")
        self.clear_done_btn = TextButton(variant="subtle", icon_name="check-circle")
        self.clear_failed_btn = TextButton(variant="subtle", icon_name="trash")
        self.pause_all_btn.clicked.connect(self.manager.pause_all)
        self.resume_all_btn.clicked.connect(self.manager.resume_all)
        self.clear_done_btn.clicked.connect(self.manager.clear_completed)
        self.clear_failed_btn.clicked.connect(self.manager.clear_failed)
        layout.addWidget(self.pause_all_btn)
        layout.addWidget(self.resume_all_btn)
        layout.addStretch(1)
        layout.addWidget(self.clear_done_btn)
        layout.addWidget(self.clear_failed_btn)
        return bar

    def _build_empty_state(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)
        icon = ThemedIconLabel("inbox", role="TEXT_MUTED", size=56)
        self._empty_title = QLabel()
        self._empty_title.setObjectName("EmptyTitle")
        self._empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_text = QLabel()
        self._empty_text.setObjectName("EmptyText")
        self._empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._empty_title)
        layout.addWidget(self._empty_text)
        return widget

    def retranslate_ui(self) -> None:
        self._title.setText(tr("queue.title"))
        self.pause_all_btn.setText(tr("queue.pause_all"))
        self.resume_all_btn.setText(tr("queue.resume_all"))
        self.clear_done_btn.setText(tr("queue.clear_done"))
        self.clear_failed_btn.setText(tr("queue.clear_failed"))
        self._empty_title.setText(tr("queue.empty_title"))
        self._empty_text.setText(tr("queue.empty_text"))
        self._update_count()
        for card in self.cards.values():
            card.retranslate_ui()

    # -- manager signal handlers ------------------------------------------

    def _on_item_added(self, item_id: int) -> None:
        item = self.manager.get(item_id)
        if not item or item_id in self.cards:
            return
        card = DownloadCard(item)
        card.pause_clicked.connect(self.manager.pause)
        card.resume_clicked.connect(self.manager.resume)
        card.cancel_clicked.connect(self.manager.cancel)
        card.open_clicked.connect(self._open_folder)
        card.selected.connect(self._select)
        self.cards[item_id] = card
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)
        self._sync_empty_state()

    def _on_item_updated(self, item_id: int) -> None:
        item = self.manager.get(item_id)
        if not item:
            return
        card = self.cards.get(item_id)
        if card is None:
            self._on_item_added(item_id)
        else:
            card.update_from_item(item)

    def _on_item_removed(self, item_id: int) -> None:
        card = self.cards.pop(item_id, None)
        if card is not None:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        if self.selected_id == item_id:
            self.selected_id = None
        self._sync_empty_state()

    # -- selection & keyboard actions -------------------------------------

    def _select(self, item_id: int) -> None:
        for cid, card in self.cards.items():
            card.set_selected(cid == item_id)
        self.selected_id = item_id

    def toggle_selected(self) -> None:
        item = self.manager.get(self.selected_id) if self.selected_id else None
        if not item:
            return
        if item.status in ("downloading", "queued"):
            self.manager.pause(item.id)
        elif item.status in ("paused", "failed"):
            self.manager.resume(item.id)

    def cancel_selected(self) -> None:
        if self.selected_id is not None:
            self.manager.cancel(self.selected_id)

    # -- helpers -----------------------------------------------------------

    def _update_count(self) -> None:
        items = self.manager.items()
        active = sum(1 for i in items if i.status in ("downloading", "processing"))
        self.count_label.setText(tr("queue.count", total=len(items), active=active))

    def _sync_empty_state(self) -> None:
        has_items = bool(self.cards)
        self.scroll.setVisible(has_items)
        self.empty.setVisible(not has_items)
        self._update_count()

    def _open_folder(self, item_id: int) -> None:
        item = self.manager.get(item_id)
        if not item or not item.filepath:
            return
        folder = Path(item.filepath).parent
        if folder.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))
