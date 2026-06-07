"""Left navigation sidebar with section buttons and a theme toggle."""

from __future__ import annotations

from typing import List, Optional, Tuple

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gui import __version__
from gui.utils.i18n import i18n, tr
from gui.widgets.custom_widgets import (
    ThemedIconLabel,
    ToggleSwitch,
    colored_icon,
)
from gui.utils.theme import theme_manager

# (translation key, icon name) for each navigation entry.
NAV_ITEMS: List[Tuple[str, str]] = [
    ("nav.home", "home"),
    ("nav.queue", "queue"),
    ("nav.history", "history"),
    ("nav.settings", "settings"),
    ("nav.about", "info"),
]


class Sidebar(QWidget):
    """Vertical navigation with an active-item accent and theme switch."""

    navigate = pyqtSignal(int)
    theme_toggled = pyqtSignal(bool)  # True -> dark

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(208)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 16)
        layout.setSpacing(6)

        layout.addWidget(self._build_logo())
        layout.addSpacing(14)

        self._section = QLabel()
        self._section.setObjectName("SidebarSection")
        layout.addWidget(self._section)

        self._buttons: List[QPushButton] = []
        self._nav_keys: List[str] = []
        for index, (key, icon) in enumerate(NAV_ITEMS):
            btn = QPushButton()
            btn.setProperty("nav", True)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIconSize(QSize(18, 18))
            btn.setProperty("icon_name", icon)
            btn.clicked.connect(lambda _checked, i=index: self.set_active(i))
            self._buttons.append(btn)
            self._nav_keys.append(key)
            layout.addWidget(btn)

        layout.addStretch(1)
        layout.addWidget(self._build_theme_row())

        self._version = QLabel(f"v{__version__}")
        self._version.setObjectName("SidebarVersion")
        self._version.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self._version)

        theme_manager.changed.connect(self._refresh_icons)
        i18n.language_changed.connect(lambda _c: self.retranslate_ui())
        self._active = 0
        self.retranslate_ui()
        self.set_active(0)

    def _build_logo(self) -> QWidget:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(4, 0, 0, 0)
        hl.setSpacing(8)
        self._logo_icon = ThemedIconLabel("logo", role="ACCENT", size=22)
        text = QLabel("PHDownloader")
        text.setObjectName("SidebarLogo")
        hl.addWidget(self._logo_icon)
        hl.addWidget(text)
        hl.addStretch(1)
        return row

    def _build_theme_row(self) -> QWidget:
        row = QWidget()
        hl = QHBoxLayout(row)
        hl.setContentsMargins(6, 4, 6, 8)
        hl.setSpacing(8)
        self._moon = ThemedIconLabel("moon", role="TEXT_DIM", size=16)
        self._sun = ThemedIconLabel("sun", role="TEXT_DIM", size=16)
        self._toggle = ToggleSwitch()
        self._toggle.setChecked(theme_manager.name == "light")
        self._toggle.toggled.connect(lambda checked: self.theme_toggled.emit(not checked))
        hl.addWidget(self._moon)
        hl.addStretch(1)
        hl.addWidget(self._toggle)
        hl.addStretch(1)
        hl.addWidget(self._sun)
        return row

    def retranslate_ui(self) -> None:
        self._section.setText(tr("nav.section"))
        for btn, key in zip(self._buttons, self._nav_keys):
            btn.setText(f"  {tr(key)}")

    def set_theme_state(self, is_dark: bool) -> None:
        """Sync the toggle position with the actual theme (no signal echo)."""
        self._toggle.blockSignals(True)
        self._toggle.setChecked(not is_dark)
        self._toggle.blockSignals(False)

    def set_active(self, index: int) -> None:
        self._active = index
        for i, btn in enumerate(self._buttons):
            btn.setProperty("active", i == index)
            btn.setChecked(i == index)
            style = btn.style()
            style.unpolish(btn)
            style.polish(btn)
        self._refresh_icons()
        self.navigate.emit(index)

    def _refresh_icons(self, *_: object) -> None:
        for i, btn in enumerate(self._buttons):
            name = str(btn.property("icon_name"))
            role = "ACCENT" if i == self._active else "TEXT_DIM"
            btn.setIcon(colored_icon(name, theme_manager.color(role), 18))
