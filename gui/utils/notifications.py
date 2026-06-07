"""Desktop notifications.

Prefers the system-tray balloon (no extra dependency) and falls back to
``plyer`` if it happens to be installed. Always fails silently — a missing
notification must never crash a download.
"""

from __future__ import annotations

from typing import Optional

from PyQt6.QtWidgets import QSystemTrayIcon


def notify(
    tray: Optional[QSystemTrayIcon],
    title: str,
    message: str,
    msecs: int = 5000,
) -> bool:
    """Show a desktop notification. Returns True if one was displayed."""
    try:
        if (
            tray is not None
            and QSystemTrayIcon.isSystemTrayAvailable()
            and tray.isVisible()
        ):
            tray.showMessage(
                title, message, QSystemTrayIcon.MessageIcon.Information, msecs
            )
            return True
    except Exception:
        pass

    try:  # optional dependency
        from plyer import notification as _notification  # type: ignore

        _notification.notify(title=title, message=message, timeout=max(1, msecs // 1000))
        return True
    except Exception:
        return False
