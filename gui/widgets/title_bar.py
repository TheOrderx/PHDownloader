"""Custom frameless-window title bar with drag-to-move and window controls."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gui.widgets.custom_widgets import IconButton, ThemedIconLabel


class TitleBar(QWidget):
    """Draggable title bar exposing minimise / maximise / close actions."""

    minimize_clicked = pyqtSignal()
    maximize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)

        self._logo = ThemedIconLabel("logo", role="ACCENT", size=20)
        title = QLabel("PHDownloader")
        title.setObjectName("TitleBarTitle")

        layout.addWidget(self._logo)
        layout.addWidget(title)
        layout.addStretch(1)

        self._min_btn = IconButton("minus", role="TEXT_DIM", size=15, tooltip="Minimize")
        self._max_btn = IconButton("square", role="TEXT_DIM", size=13, tooltip="Maximize")
        self._close_btn = IconButton("x", role="TEXT_DIM", size=15, tooltip="Close")
        self._min_btn.setObjectName("TBMin")
        self._max_btn.setObjectName("TBMax")
        self._close_btn.setObjectName("TBClose")

        self._min_btn.clicked.connect(self.minimize_clicked.emit)
        self._max_btn.clicked.connect(self.maximize_clicked.emit)
        self._close_btn.clicked.connect(self.close_clicked.emit)

        for btn in (self._min_btn, self._max_btn, self._close_btn):
            layout.addWidget(btn)

    def set_maximized(self, maximized: bool) -> None:
        """Swap the maximise/restore glyph to match the window state."""
        self._max_btn.set_icon_name("restore" if maximized else "square")
        self._max_btn.setToolTip("Restore" if maximized else "Maximize")

    # -- dragging ----------------------------------------------------------

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_clicked.emit()
        super().mouseDoubleClickEvent(event)
