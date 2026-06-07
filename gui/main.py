"""Application entry point: configures QApplication and shows the main window.

Run with either:

    python -m gui.main      (from the phvid project root)
    python gui/main.py
"""

from __future__ import annotations

import os
import sys

# Ensure the phvid project root (parent of this ``gui`` package) is importable
# so both the GUI package and the backend modules (config, downloader, …) load
# regardless of how the program is launched.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from PyQt6.QtCore import Qt  # noqa: E402
from PyQt6.QtGui import QFont  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402

from gui.main_window import MainWindow  # noqa: E402
from utils import prepare_ffmpeg_environment  # noqa: E402
from gui.utils.i18n import i18n  # noqa: E402
from gui.utils.settings import Settings  # noqa: E402
from gui.utils.theme import build_stylesheet, theme_manager  # noqa: E402


def main() -> int:
    """Create the application, apply the saved theme, and run the event loop."""
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setApplicationName("PHDownloader")
    QApplication.setOrganizationName("PHDownloader")
    QApplication.setApplicationDisplayName("PHDownloader")

    settings = Settings()
    # Make any bundled or previously-downloaded ffmpeg discoverable.
    prepare_ffmpeg_environment(settings.get("ffmpeg_path") or None)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    i18n.set_language(settings.get("language"))
    theme_manager.set_theme(settings.get("theme"))
    app.setStyleSheet(build_stylesheet(theme_manager.name))

    window = MainWindow(settings)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
