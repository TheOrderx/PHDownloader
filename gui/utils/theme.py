"""Theme palettes and QSS stylesheet generation.

The stylesheet lives in ``resources/styles.qss`` with ``@token@`` placeholders.
:func:`build_stylesheet` substitutes the palette for the requested theme so the
same sheet drives both dark and light modes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from PyQt6.QtCore import QObject, pyqtSignal

DARK: Dict[str, str] = {
    "BG": "#1a1a1a",
    "SURFACE": "#222222",
    "SURFACE_ALT": "#2a2a2a",
    "SURFACE_HOVER": "#313131",
    "BORDER": "#333333",
    "ACCENT": "#ff9000",
    "ACCENT_HOVER": "#ffa733",
    "ACCENT_PRESS": "#e07f00",
    "ACCENT_SOFT": "#3a2a10",
    "TEXT": "#f2f2f2",
    "TEXT_DIM": "#9a9a9a",
    "TEXT_MUTED": "#6f6f6f",
    "DANGER": "#ff4d4d",
    "DANGER_HOVER": "#ff6b6b",
    "SUCCESS": "#3ddc84",
    "WARNING": "#ffb020",
    "SIDEBAR_BG": "#161616",
    "TITLEBAR_BG": "#141414",
    "SCROLL": "#3a3a3a",
    "SCROLL_HOVER": "#4d4d4d",
    "SELECTION": "#3a2a10",
}

LIGHT: Dict[str, str] = {
    "BG": "#f5f5f7",
    "SURFACE": "#ffffff",
    "SURFACE_ALT": "#eeeef1",
    "SURFACE_HOVER": "#e6e6ea",
    "BORDER": "#dcdce0",
    "ACCENT": "#ff9000",
    "ACCENT_HOVER": "#ffa733",
    "ACCENT_PRESS": "#e07f00",
    "ACCENT_SOFT": "#fff1dd",
    "TEXT": "#1b1b1d",
    "TEXT_DIM": "#5f5f66",
    "TEXT_MUTED": "#8a8a90",
    "DANGER": "#e23b3b",
    "DANGER_HOVER": "#f15454",
    "SUCCESS": "#1faa59",
    "WARNING": "#d9870f",
    "SIDEBAR_BG": "#ededf0",
    "TITLEBAR_BG": "#e6e6ea",
    "SCROLL": "#cfcfd4",
    "SCROLL_HOVER": "#b8b8be",
    "SELECTION": "#ffe3bd",
}

THEMES: Dict[str, Dict[str, str]] = {"dark": DARK, "light": LIGHT}

_QSS_PATH = Path(__file__).resolve().parents[1] / "resources" / "styles.qss"


def palette(name: str) -> Dict[str, str]:
    """Return the colour palette dict for ``name`` (falls back to dark)."""
    return THEMES.get(name, DARK)


def build_stylesheet(name: str) -> str:
    """Load ``styles.qss`` and substitute the palette tokens for ``name``.

    Also resolves asset tokens (``@ICONDIR@`` and ``@CHEVRON@``) to absolute,
    forward-slash URLs so QSS ``url(...)`` references work regardless of the
    process working directory.
    """
    qss = _QSS_PATH.read_text(encoding="utf-8")
    for key, value in palette(name).items():
        qss = qss.replace(f"@{key}@", value)
    icon_dir = (_QSS_PATH.parent / "icons").as_posix()
    chevron = f"{icon_dir}/chevron_{'dark' if name == 'dark' else 'light'}.svg"
    qss = qss.replace("@ICONDIR@", icon_dir)
    qss = qss.replace("@CHEVRON@", chevron)
    return qss


class ThemeManager(QObject):
    """App-wide current theme holder; emits :attr:`changed` on theme switch.

    Widgets that render recolourable icons connect to :attr:`changed` so they
    can refresh their pixmaps when the user toggles dark/light mode.
    """

    changed = pyqtSignal(str)

    def __init__(self, name: str = "dark") -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def palette(self) -> Dict[str, str]:
        return palette(self._name)

    def color(self, key: str) -> str:
        return palette(self._name).get(key, "#ffffff")

    def stylesheet(self) -> str:
        return build_stylesheet(self._name)

    def set_theme(self, name: str) -> None:
        if name != self._name and name in THEMES:
            self._name = name
            self.changed.emit(name)

    def toggle(self) -> str:
        self.set_theme("light" if self._name == "dark" else "dark")
        return self._name


# Process-wide singleton shared by every widget.
theme_manager = ThemeManager()
