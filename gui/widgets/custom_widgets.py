"""Reusable, fully-styled building blocks: themed-SVG icons, buttons, an
animated toggle switch, status badges and small layout helpers.

All icon-bearing widgets recolour themselves when the global theme changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import (
    QByteArray,
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    pyqtProperty,
)
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QAbstractButton,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QWidget,
)

from gui.utils.theme import theme_manager

ICON_DIR = Path(__file__).resolve().parents[1] / "resources" / "icons"

_RENDER_SCALE = 2  # render SVGs at 2x for crisp high-DPI output


def _resolve_color(role_or_hex: str) -> str:
    """Return a hex colour from either a literal ``#hex`` or a palette role."""
    if role_or_hex.startswith("#"):
        return role_or_hex
    return theme_manager.color(role_or_hex)


def colored_pixmap(name: str, color: str, size: int = 18) -> QPixmap:
    """Render the named SVG icon recoloured to ``color`` at ``size`` px."""
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        empty = QPixmap(size, size)
        empty.fill(Qt.GlobalColor.transparent)
        return empty
    data = path.read_text(encoding="utf-8").replace("currentColor", color)
    renderer = QSvgRenderer(QByteArray(data.encode("utf-8")))
    pixmap = QPixmap(size * _RENDER_SCALE, size * _RENDER_SCALE)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    pixmap.setDevicePixelRatio(_RENDER_SCALE)
    return pixmap


def colored_icon(name: str, color: str, size: int = 18) -> QIcon:
    """Return a :class:`QIcon` for the named SVG recoloured to ``color``."""
    return QIcon(colored_pixmap(name, color, size))


def repolish(widget: QWidget) -> None:
    """Re-apply the stylesheet to ``widget`` after a dynamic property change."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def apply_shadow(
    widget: QWidget, blur: int = 24, x: int = 0, y: int = 6, alpha: int = 150
) -> QGraphicsDropShadowEffect:
    """Attach a soft drop shadow to ``widget`` and return the effect."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(x)
    effect.setYOffset(y)
    effect.setColor(QColor(0, 0, 0, alpha))
    widget.setGraphicsEffect(effect)
    return effect


class IconButton(QPushButton):
    """A square, borderless button showing a single recolourable icon."""

    def __init__(
        self,
        icon_name: str,
        role: str = "TEXT_DIM",
        size: int = 18,
        tooltip: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("IconButton")
        self._icon_name = icon_name
        self._role = role
        self._size = size
        self.setIconSize(QSize(size, size))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
        theme_manager.changed.connect(self._refresh)
        self._refresh()

    def set_role(self, role: str) -> None:
        self._role = role
        self._refresh()

    def set_icon_name(self, name: str) -> None:
        self._icon_name = name
        self._refresh()

    def _refresh(self, *_: object) -> None:
        self.setIcon(colored_icon(self._icon_name, _resolve_color(self._role), self._size))


class TextButton(QPushButton):
    """A labelled button with an optional leading icon and a style variant."""

    def __init__(
        self,
        text: str = "",
        variant: str = "default",
        icon_name: Optional[str] = None,
        icon_role: Optional[str] = None,
        icon_size: int = 16,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(text, parent)
        self.setProperty("variant", variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._icon_name = icon_name
        # Accent buttons get a dark icon for contrast against orange.
        self._icon_role = icon_role or ("#1a1a1a" if variant == "accent" else "TEXT_DIM")
        self._icon_size = icon_size
        if icon_name:
            self.setIconSize(QSize(icon_size, icon_size))
            theme_manager.changed.connect(self._refresh_icon)
            self._refresh_icon()

    def _refresh_icon(self, *_: object) -> None:
        if self._icon_name:
            self.setIcon(
                colored_icon(self._icon_name, _resolve_color(self._icon_role), self._icon_size)
            )


class ThemedIconLabel(QLabel):
    """A decorative label that displays a recolourable SVG icon."""

    def __init__(
        self,
        icon_name: str,
        role: str = "TEXT_DIM",
        size: int = 24,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self._role = role
        self._size = size
        self.setFixedSize(size, size)
        theme_manager.changed.connect(self._refresh)
        self._refresh()

    def set_role(self, role: str) -> None:
        self._role = role
        self._refresh()

    def _refresh(self, *_: object) -> None:
        self.setPixmap(colored_pixmap(self._icon_name, _resolve_color(self._role), self._size))


class StatusBadge(QLabel):
    """A small rounded pill that reflects a download's status."""

    def __init__(self, status: str = "queued", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status = status
        from gui.utils.i18n import i18n

        i18n.language_changed.connect(lambda _c: self.set_status(self._status))
        self.set_status(status)

    def set_status(self, status: str) -> None:
        from gui.utils.i18n import tr

        self._status = status
        self.setProperty("status", status)
        label = tr(f"status.{status}")
        self.setText(label if label != f"status.{status}" else status.upper())
        repolish(self)


class ToggleSwitch(QAbstractButton):
    """An animated on/off switch driven by a :class:`QPropertyAnimation`."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._offset = 0.0
        self.setFixedSize(46, 26)
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:  # noqa: N802 (Qt override)
        return QSize(46, 26)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = pyqtProperty(float, _get_offset, _set_offset)

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool) -> None:  # noqa: N802 (Qt override)
        super().setChecked(checked)
        self._offset = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802 (Qt override)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        on = QColor(theme_manager.color("ACCENT"))
        off = QColor(theme_manager.color("SURFACE_HOVER"))
        track = on if self._offset > 0.5 else off
        painter.setBrush(track)
        painter.setPen(Qt.PenStyle.NoPen)
        radius = rect.height() / 2
        painter.drawRoundedRect(rect, radius, radius)

        diameter = rect.height() - 6
        travel = rect.width() - diameter - 6
        x = rect.x() + 3 + self._offset * travel
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(QRectF(x, rect.y() + 3, diameter, diameter))
        painter.end()


def make_card(object_name: str = "Card") -> QFrame:
    """Return a styled :class:`QFrame` usable as a card/panel container."""
    frame = QFrame()
    frame.setObjectName(object_name)
    return frame


def h_separator() -> QFrame:
    """Return a 1px horizontal divider line."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background-color: {theme_manager.color('BORDER')};")
    return line
