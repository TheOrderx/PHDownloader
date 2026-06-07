"""The application main window: frameless chrome, navigation, tray and hotkeys."""

from __future__ import annotations

import os
from pathlib import Path

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QStandardPaths,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QStackedWidget,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui.core.download_manager import DownloadManager
from gui.utils.ffmpeg_setup import ensure_ffmpeg, has_ffmpeg
from utils import prepare_ffmpeg_environment
from gui.pages.home_page import HomePage
from gui.pages.history_page import HistoryPage
from gui.pages.queue_page import QueuePage
from gui.pages.settings_page import SettingsPage
from gui.utils.i18n import i18n, tr
from gui.utils.notifications import notify
from gui.utils.settings import Settings
from gui.utils.theme import build_stylesheet, theme_manager
from gui.widgets.custom_widgets import apply_shadow, colored_icon, repolish
from gui.widgets.sidebar import Sidebar
from gui.widgets.title_bar import TitleBar

# The translucent window reserves a transparent margin (SHADOW) around the root
# frame for the drop shadow. INVARIANT: the shadow must stay inside that margin,
# i.e. SHADOW >= SHADOW_BLUR + SHADOW_OFFSET_Y, otherwise the shadow paints
# outside the window and Windows raises "UpdateLayeredWindowIndirect failed".
SHADOW = 20
SHADOW_BLUR = 14
SHADOW_OFFSET_Y = 4
RESIZE_MARGIN = 7

# Qt edge flag integer values, combined when near a corner.
_LEFT, _RIGHT, _TOP, _BOTTOM = 1, 2, 4, 8
_CURSORS = {
    _LEFT: Qt.CursorShape.SizeHorCursor,
    _RIGHT: Qt.CursorShape.SizeHorCursor,
    _TOP: Qt.CursorShape.SizeVerCursor,
    _BOTTOM: Qt.CursorShape.SizeVerCursor,
    _LEFT | _TOP: Qt.CursorShape.SizeFDiagCursor,
    _RIGHT | _BOTTOM: Qt.CursorShape.SizeFDiagCursor,
    _RIGHT | _TOP: Qt.CursorShape.SizeBDiagCursor,
    _LEFT | _BOTTOM: Qt.CursorShape.SizeBDiagCursor,
}


class _FfmpegEnsureWorker(QThread):
    """Downloads ffmpeg in the background on first run if it is missing."""

    progress = pyqtSignal(int, str)  # percent (-1 = indeterminate), message
    finished_ok = pyqtSignal(bool)

    def run(self) -> None:  # noqa: N802 (Qt override)
        def report(message: str, percent: int = -1) -> None:
            self.progress.emit(percent, message)

        try:
            ok = ensure_ffmpeg(progress=report)
        except Exception:  # noqa: BLE001
            ok = False
        self.finished_ok.emit(ok)


class SetupBanner(QFrame):
    """A slim bottom banner showing first-run ffmpeg download progress."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SetupBanner")
        self.setVisible(False)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        self._label = QLabel()
        self._label.setObjectName("CardSub")
        self._percent = QLabel("")
        self._percent.setObjectName("CardProgressText")
        self._bar = QProgressBar()
        self._bar.setTextVisible(False)
        self._bar.setFixedSize(220, 8)

        layout.addWidget(self._label, 1)
        layout.addWidget(self._percent)
        layout.addWidget(self._bar)
        i18n.language_changed.connect(lambda _c: self._label.setText(tr("setup.working")))

    def set_progress(self, percent: int, message: str) -> None:
        self.setVisible(True)
        self._label.setText(message)
        if percent < 0:
            self._bar.setRange(0, 0)  # indeterminate (animated) bar
            self._percent.setText("")
        else:
            self._bar.setRange(0, 100)
            self._bar.setValue(percent)
            self._percent.setText(f"{percent}%")

    def finish(self, message: str) -> None:
        self._bar.setRange(0, 100)
        self._bar.setValue(100)
        self._percent.setText("")
        self._label.setText(message)
        QTimer.singleShot(3000, lambda: self.setVisible(False))


class MainWindow(QWidget):
    """Top-level frameless window hosting the sidebar and stacked pages."""

    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self._is_max = False
        self._force_quit = False
        self._tray_hint_shown = False
        self._fade_anim: QPropertyAnimation | None = None

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(900, 600)
        self.setMouseTracking(True)
        self.setWindowTitle("PHDownloader")
        self.setWindowIcon(colored_icon("logo", theme_manager.color("ACCENT"), 64))

        data_dir = self._data_dir()
        # Route the backend logger to errors.log so download failures (with the
        # exact HTTP status / cause) are persisted for troubleshooting.
        try:
            from utils import setup_logging

            setup_logging(data_dir)
        except Exception:
            pass
        self._data_path = data_dir
        self.manager = DownloadManager(settings, data_dir / "history.db")

        self._build_ui()
        self._build_tray()
        self._build_shortcuts()
        self._connect_manager()
        i18n.language_changed.connect(lambda _c: self.retranslate_ui())

        self._restore_window_state()
        self.retranslate_ui()
        self._maybe_setup_ffmpeg()

    # -- ffmpeg bootstrap --------------------------------------------------

    def _maybe_setup_ffmpeg(self) -> None:
        """Fetch ffmpeg in the background on first run if it is unavailable."""
        if os.environ.get("PHDL_SKIP_FFMPEG_FETCH") == "1":
            prepare_ffmpeg_environment(None)
            return
        prepare_ffmpeg_environment(self.settings.get("ffmpeg_path") or None)
        if has_ffmpeg():
            self.settings_page._refresh_ffmpeg_status()
            return
        self.setup_banner.set_progress(-1, tr("setup.ffmpeg_first"))
        self._ffmpeg_worker = _FfmpegEnsureWorker()
        self._ffmpeg_worker.progress.connect(self._on_ffmpeg_progress)
        self._ffmpeg_worker.finished_ok.connect(self._on_ffmpeg_ready)
        self._ffmpeg_worker.start()

    def _on_ffmpeg_progress(self, percent: int, message_id: str) -> None:
        text = tr(message_id) if str(message_id).startswith("ffmpeg.") else str(message_id)
        self.setup_banner.set_progress(percent, text)

    def _on_ffmpeg_ready(self, ok: bool) -> None:
        if ok:
            self.setup_banner.finish(tr("setup.ffmpeg_done"))
            notify(self.tray, tr("tray.setup_complete"), tr("tray.ffmpeg_ready"))
        else:
            self.setup_banner.finish(tr("setup.ffmpeg_ts"))
            if self.settings.get("notifications"):
                notify(
                    self.tray,
                    tr("tray.ffmpeg_missing"),
                    tr("tray.ffmpeg_ts_fallback"),
                )
        self.settings_page._refresh_ffmpeg_status()

    # -- data location -----------------------------------------------------

    @staticmethod
    def _data_dir() -> Path:
        base = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        path = Path(base) if base else Path.home() / ".phdownloader"
        path.mkdir(parents=True, exist_ok=True)
        return path

    # -- UI construction ---------------------------------------------------

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(SHADOW, SHADOW, SHADOW, SHADOW)
        self._outer = outer

        self.root = QFrame()
        self.root.setObjectName("Root")
        self.root.setMouseTracking(True)
        self._shadow = apply_shadow(
            self.root, blur=SHADOW_BLUR, y=SHADOW_OFFSET_Y, alpha=150
        )
        outer.addWidget(self.root)

        root_layout = QVBoxLayout(self.root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = TitleBar()
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self.toggle_max_restore)
        self.title_bar.close_clicked.connect(self.close)
        root_layout.addWidget(self.title_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.theme_toggled.connect(lambda is_dark: self.apply_theme("dark" if is_dark else "light"))
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.home_page = HomePage(self.settings, self.manager)
        self.queue_page = QueuePage(self.manager)
        self.history_page = HistoryPage(self.settings, self.manager)
        self.settings_page = SettingsPage(self.settings)
        self.settings_page.theme_changed.connect(self.apply_theme)
        self.home_page.queued.connect(lambda: self.sidebar.set_active(1))
        for page in (self.home_page, self.queue_page, self.history_page, self.settings_page):
            self.stack.addWidget(page)
        body.addWidget(self.stack, 1)

        root_layout.addLayout(body)

        # First-run setup progress banner (hidden until ffmpeg is downloaded).
        self.setup_banner = SetupBanner()
        root_layout.addWidget(self.setup_banner)

        self.sidebar.navigate.connect(self._navigate)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(colored_icon("logo", theme_manager.color("ACCENT"), 64))
        self.tray.setToolTip("PHDownloader")
        menu = QMenu()
        self._tray_show = menu.addAction("", self._toggle_visibility)
        self._tray_pause = menu.addAction("", self.manager.pause_all)
        menu.addSeparator()
        self._tray_quit = menu.addAction("", self._quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

    def _build_shortcuts(self) -> None:
        # Only modifier combos that never conflict with text editing are bound
        # as window shortcuts; Space / Delete / Ctrl+V are handled in
        # keyPressEvent so focused text widgets consume them first.
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._focus_new_download)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self._quit)

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        focus = QApplication.focusWidget()
        editing = isinstance(
            focus, (QLineEdit, QAbstractSpinBox, QComboBox, QAbstractItemView)
        )
        key = event.key()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if not editing:
            if key == Qt.Key.Key_Space:
                self._space_toggle()
                return
            if key == Qt.Key.Key_Delete:
                self._delete_selected()
                return
            if ctrl and key == Qt.Key.Key_V:
                self._paste_new_download()
                return
        super().keyPressEvent(event)

    def _connect_manager(self) -> None:
        self.manager.history_changed.connect(self.history_page.reload)
        self.manager.download_complete.connect(self._on_download_complete)

    # -- navigation --------------------------------------------------------

    def _navigate(self, index: int) -> None:
        # The "About" sidebar entry (4) reuses the Settings page (3) and jumps
        # to its last tab; every other entry maps 1:1 onto a stacked page.
        target = 3 if index == 4 else min(index, self.stack.count() - 1)
        if index == 4:
            tabs = self.settings_page.findChild(QTabWidget)
            if tabs is not None:
                tabs.setCurrentIndex(tabs.count() - 1)
        if target == 2:
            self.history_page.reload(self.history_page.search.text())

        page = self.stack.widget(target)
        self.stack.setCurrentIndex(target)

        effect = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda p=page: p.setGraphicsEffect(None))
        anim.start()
        self._fade_anim = anim

        self.settings.set_raw("last_page", index)

    # -- theme -------------------------------------------------------------

    def apply_theme(self, name: str) -> None:
        theme_manager.set_theme(name)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(build_stylesheet(name))
        self.sidebar.set_theme_state(name == "dark")
        self.tray.setIcon(colored_icon("logo", theme_manager.color("ACCENT"), 64))
        self.settings.set("theme", name)

    # -- tray / lifecycle --------------------------------------------------

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _toggle_visibility(self) -> None:
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()

    def retranslate_ui(self) -> None:
        self.tray.setToolTip(tr("tray.tooltip"))
        self._tray_show.setText(tr("tray.show_hide"))
        self._tray_pause.setText(tr("tray.pause_all"))
        self._tray_quit.setText(tr("tray.quit"))
        self.sidebar.retranslate_ui()
        self.home_page.retranslate_ui()
        self.queue_page.retranslate_ui()
        self.history_page.retranslate_ui()
        self.settings_page.retranslate_ui()

    def _on_download_complete(self, _item_id: int, title: str) -> None:
        if self.settings.get("notifications"):
            notify(self.tray, tr("tray.download_complete"), title)

    def _quit(self) -> None:
        self._force_quit = True
        self.close()

    # -- hotkey handlers ---------------------------------------------------

    def _focus_new_download(self) -> None:
        self.sidebar.set_active(0)
        self.home_page.url_bar.line_edit.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def _paste_new_download(self) -> None:
        self.sidebar.set_active(0)
        self.home_page.url_bar.paste_from_clipboard()

    def _space_toggle(self) -> None:
        self.queue_page.toggle_selected()

    def _delete_selected(self) -> None:
        self.queue_page.cancel_selected()

    # -- maximise / restore ------------------------------------------------

    def toggle_max_restore(self) -> None:
        if self._is_max:
            self.showNormal()
            self._set_maximized(False)
        else:
            self.showMaximized()
            self._set_maximized(True)

    def _set_maximized(self, value: bool) -> None:
        self._is_max = value
        margin = 0 if value else SHADOW
        self._outer.setContentsMargins(margin, margin, margin, margin)
        self._shadow.setEnabled(not value)
        self.root.setProperty("maximized", value)
        repolish(self.root)
        self.title_bar.set_maximized(value)

    # -- frameless resize --------------------------------------------------

    def _edges_at(self, pos) -> int:
        if self._is_max:
            return 0
        rect = self.rect().adjusted(SHADOW, SHADOW, -SHADOW, -SHADOW)
        m = RESIZE_MARGIN
        edges = 0
        within_y = rect.top() - m <= pos.y() <= rect.bottom() + m
        within_x = rect.left() - m <= pos.x() <= rect.right() + m
        if abs(pos.x() - rect.left()) <= m and within_y:
            edges |= _LEFT
        if abs(pos.x() - rect.right()) <= m and within_y:
            edges |= _RIGHT
        if abs(pos.y() - rect.top()) <= m and within_x:
            edges |= _TOP
        if abs(pos.y() - rect.bottom()) <= m and within_x:
            edges |= _BOTTOM
        return edges

    def mouseMoveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        edges = self._edges_at(event.position().toPoint())
        self.setCursor(_CURSORS.get(edges, Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._edges_at(event.position().toPoint())
            if edges:
                handle = self.windowHandle()
                if handle is not None:
                    handle.startSystemResize(Qt.Edge(edges))
                    return
        super().mousePressEvent(event)

    # -- window state ------------------------------------------------------

    def _restore_window_state(self) -> None:
        geometry = self.settings.get_bytes("geometry")
        if not geometry.isEmpty():
            self.restoreGeometry(geometry)
        else:
            self.resize(1100, 720)
            self._center()
        last_page = int(self.settings.get_raw("last_page", 0) or 0)
        self.sidebar.set_active(min(max(last_page, 0), 4))

    def _center(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if not self._force_quit and self.settings.get("minimize_to_tray") and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            if not self._tray_hint_shown:
                notify(self.tray, tr("tray.still_running"), tr("tray.minimized"))
                self._tray_hint_shown = True
            return

        self.settings.set_bytes("geometry", self.saveGeometry())
        self.settings.sync()
        self.manager.shutdown()
        self.tray.hide()
        event.accept()
