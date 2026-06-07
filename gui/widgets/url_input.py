"""URL entry bar with a paste-from-clipboard helper button."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLineEdit, QWidget

from gui.utils.i18n import i18n, tr
from gui.widgets.custom_widgets import IconButton


class UrlInputBar(QWidget):
    """A line edit plus a clipboard button; emits :attr:`submitted` on Enter."""

    submitted = pyqtSignal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("UrlInput")
        self.line_edit.setClearButtonEnabled(True)
        self.line_edit.returnPressed.connect(self._emit_submit)

        self.paste_btn = IconButton("clipboard", role="TEXT_DIM", size=18)
        self.paste_btn.clicked.connect(self.paste_from_clipboard)

        layout.addWidget(self.line_edit, 1)
        layout.addWidget(self.paste_btn)

        i18n.language_changed.connect(lambda _c: self.retranslate_ui())
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        self.line_edit.setPlaceholderText(tr("home.url_placeholder"))
        self.paste_btn.setToolTip(tr("home.paste_tooltip"))

    def _emit_submit(self) -> None:
        text = self.text()
        if text:
            self.submitted.emit(text)

    def paste_from_clipboard(self) -> None:
        clip = QApplication.clipboard().text().strip()
        if clip:
            self.line_edit.setText(clip)
            self.line_edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def text(self) -> str:
        return self.line_edit.text().strip()

    def clear(self) -> None:
        self.line_edit.clear()

    def set_text(self, value: str) -> None:
        self.line_edit.setText(value)
