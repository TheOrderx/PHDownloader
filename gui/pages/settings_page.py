"""Settings page with General / Network / Advanced / About tabs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Tuple

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from gui import __version__
from gui.utils.i18n import (
    LANGUAGE_CHOICES,
    i18n,
    normalize_language,
    quality_label,
    tr,
)
from gui.utils.settings import Settings
from gui.widgets.custom_widgets import TextButton, ThemedIconLabel

QUALITY_VALUES = ["best", "2160", "1440", "1080", "720", "480"]


class SettingsPage(QWidget):
    """Edits and persists every application setting."""

    theme_changed = pyqtSignal(str)
    language_changed = pyqtSignal(str)

    def __init__(self, settings: Settings, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self._form_labels: List[Tuple[QLabel, str]] = []
        self._browse_buttons: List[TextButton] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)

        self._page_title = QLabel()
        self._page_title.setObjectName("PageTitle")
        root.addWidget(self._page_title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._general_tab(), "")
        self._tabs.addTab(self._network_tab(), "")
        self._tabs.addTab(self._advanced_tab(), "")
        self._tabs.addTab(self._about_tab(), "")
        root.addWidget(self._tabs, 1)

        self.retranslate_ui()

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _tab_form() -> tuple[QWidget, QFormLayout]:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(22, 22, 22, 22)
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        outer.addLayout(form)
        outer.addStretch(1)
        return widget, form

    def _add_row(self, form: QFormLayout, key: str, widget: QWidget) -> None:
        label = QLabel()
        self._form_labels.append((label, key))
        form.addRow(label, widget)

    def _path_field(
        self,
        value: str,
        on_change: Callable[[str], None],
        pick_dir: bool,
        caption_key: str,
    ) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        edit = QLineEdit(value)
        edit.editingFinished.connect(lambda: on_change(edit.text()))
        browse = TextButton(variant="ghost", icon_name="folder")
        browse.setProperty("caption_key", caption_key)

        def _pick() -> None:
            caption = tr(caption_key)
            if pick_dir:
                chosen = QFileDialog.getExistingDirectory(
                    self, caption, edit.text() or str(Path.home())
                )
            else:
                chosen, _ = QFileDialog.getOpenFileName(
                    self, caption, edit.text() or str(Path.home())
                )
            if chosen:
                edit.setText(chosen)
                on_change(chosen)

        browse.clicked.connect(_pick)
        self._browse_buttons.append(browse)
        layout.addWidget(edit, 1)
        layout.addWidget(browse)
        return row

    def _fill_quality_combo(self, combo: QComboBox) -> None:
        current = combo.currentData() if combo.count() else None
        combo.blockSignals(True)
        combo.clear()
        for value in QUALITY_VALUES:
            combo.addItem(quality_label(value), value)
        if current:
            idx = combo.findData(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    def _fill_language_combo(self) -> None:
        current = normalize_language(self.settings.get("language"))
        self._language.blockSignals(True)
        self._language.clear()
        for code, label in LANGUAGE_CHOICES.items():
            self._language.addItem(label, code)
        idx = self._language.findData(current)
        if idx >= 0:
            self._language.setCurrentIndex(idx)
        self._language.blockSignals(False)

    # -- tabs --------------------------------------------------------------

    def _general_tab(self) -> QWidget:
        widget, form = self._tab_form()
        s = self.settings

        self._add_row(
            form,
            "settings.output_folder",
            self._path_field(
                s.get("output_dir"),
                lambda v: s.set("output_dir", v),
                True,
                "settings.choose_output",
            ),
        )

        self._quality = QComboBox()
        self._fill_quality_combo(self._quality)
        idx = self._quality.findData(s.get("quality"))
        if idx >= 0:
            self._quality.setCurrentIndex(idx)
        self._quality.currentIndexChanged.connect(
            lambda _i: s.set("quality", self._quality.currentData())
        )
        self._add_row(form, "settings.default_quality", self._quality)

        self._format = QComboBox()
        self._format.addItem(tr("format.mp4"), "mp4")
        self._format.addItem(tr("format.mkv"), "mkv")
        fmt_idx = self._format.findData(s.get("format"))
        if fmt_idx >= 0:
            self._format.setCurrentIndex(fmt_idx)
        self._format.currentIndexChanged.connect(
            lambda _i: s.set("format", self._format.currentData())
        )
        self._add_row(form, "settings.default_format", self._format)

        self._theme = QComboBox()
        self._theme.addItem(tr("theme.dark"), "dark")
        self._theme.addItem(tr("theme.light"), "light")
        theme_idx = self._theme.findData(s.get("theme"))
        if theme_idx >= 0:
            self._theme.setCurrentIndex(theme_idx)
        self._theme.currentIndexChanged.connect(self._on_theme_data)
        self._add_row(form, "settings.theme", self._theme)

        self._language = QComboBox()
        self._fill_language_combo()
        self._language.currentIndexChanged.connect(self._on_language)
        self._add_row(form, "settings.language", self._language)

        return widget

    def _network_tab(self) -> QWidget:
        widget, form = self._tab_form()
        s = self.settings

        self._proxy_type = QComboBox()
        self._proxy_type.addItem(tr("proxy.none"), "None")
        self._proxy_type.addItem("HTTP", "HTTP")
        self._proxy_type.addItem("SOCKS5", "SOCKS5")
        pidx = self._proxy_type.findData(s.get("proxy_type"))
        if pidx >= 0:
            self._proxy_type.setCurrentIndex(pidx)
        self._proxy_type.currentIndexChanged.connect(
            lambda _i: s.set("proxy_type", self._proxy_type.currentData())
        )
        self._add_row(form, "settings.proxy_type", self._proxy_type)

        self._proxy_host = QLineEdit(s.get("proxy_host"))
        self._proxy_host.editingFinished.connect(lambda: s.set("proxy_host", self._proxy_host.text()))
        self._add_row(form, "settings.proxy_host", self._proxy_host)

        self._proxy_port = QLineEdit(s.get("proxy_port"))
        self._proxy_port.editingFinished.connect(lambda: s.set("proxy_port", self._proxy_port.text()))
        self._add_row(form, "settings.proxy_port", self._proxy_port)

        self._timeout = QSpinBox()
        self._timeout.setRange(5, 600)
        self._timeout.setSuffix(" s")
        self._timeout.setValue(s.get("timeout"))
        self._timeout.valueChanged.connect(lambda v: s.set("timeout", v))
        self._add_row(form, "settings.timeout", self._timeout)

        self._retries = QSpinBox()
        self._retries.setRange(0, 10)
        self._retries.setValue(s.get("retries"))
        self._retries.valueChanged.connect(lambda v: s.set("retries", v))
        self._add_row(form, "settings.retries", self._retries)

        self._rate = QDoubleSpinBox()
        self._rate.setRange(0.0, 1000.0)
        self._rate.setDecimals(1)
        self._rate.setSuffix(" MB/s")
        self._rate.setValue(s.get("rate_limit"))
        self._rate.valueChanged.connect(lambda v: s.set("rate_limit", v))
        self._add_row(form, "settings.rate_limit", self._rate)

        self._threads = QSpinBox()
        self._threads.setRange(1, 64)
        self._threads.setValue(s.get("threads"))
        self._threads.valueChanged.connect(lambda v: s.set("threads", v))
        self._add_row(form, "settings.threads", self._threads)

        return widget

    def _advanced_tab(self) -> QWidget:
        widget, form = self._tab_form()
        s = self.settings

        ffmpeg_row = QWidget()
        ffmpeg_layout = QHBoxLayout(ffmpeg_row)
        ffmpeg_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_layout.setSpacing(8)
        self._ffmpeg_edit = QLineEdit(s.get("ffmpeg_path"))
        self._ffmpeg_edit.editingFinished.connect(
            lambda: self._save_ffmpeg_path(self._ffmpeg_edit.text())
        )
        self._ffmpeg_auto_btn = TextButton(variant="ghost", icon_name="refresh")
        self._ffmpeg_auto_btn.clicked.connect(self._auto_detect_ffmpeg)
        self._ffmpeg_browse_btn = TextButton(variant="ghost", icon_name="folder")
        self._ffmpeg_browse_btn.clicked.connect(self._browse_ffmpeg)
        self._browse_buttons.extend([self._ffmpeg_auto_btn, self._ffmpeg_browse_btn])
        ffmpeg_layout.addWidget(self._ffmpeg_edit, 1)
        ffmpeg_layout.addWidget(self._ffmpeg_auto_btn)
        ffmpeg_layout.addWidget(self._ffmpeg_browse_btn)
        self._add_row(form, "settings.ffmpeg_path", ffmpeg_row)

        self._ffmpeg_hint = QLabel()
        self._ffmpeg_hint.setObjectName("Hint")
        self._ffmpeg_hint.setWordWrap(True)
        form.addRow("", self._ffmpeg_hint)

        self._add_row(
            form,
            "settings.cookies_file",
            self._path_field(
                s.get("cookies_file"),
                lambda v: s.set("cookies_file", v),
                False,
                "settings.choose_cookies",
            ),
        )

        self._user_agent = QLineEdit(s.get("user_agent"))
        self._user_agent.editingFinished.connect(lambda: s.set("user_agent", self._user_agent.text()))
        self._add_row(form, "settings.user_agent", self._user_agent)

        self._template = QLineEdit(s.get("filename_template"))
        self._template.editingFinished.connect(lambda: s.set("filename_template", self._template.text()))
        self._add_row(form, "settings.filename_template", self._template)

        self._template_hint = QLabel()
        self._template_hint.setObjectName("Hint")
        form.addRow("", self._template_hint)

        return widget

    def _about_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        header = QHBoxLayout()
        header.setSpacing(12)
        header.addWidget(ThemedIconLabel("logo", role="ACCENT", size=40))
        name = QLabel("PHDownloader")
        name.setObjectName("PageTitle")
        header.addWidget(name)
        header.addStretch(1)
        layout.addLayout(header)

        self._version_label = QLabel()
        self._version_label.setObjectName("PageSubtitle")
        layout.addWidget(self._version_label)

        self._about_text = QLabel()
        self._about_text.setObjectName("AboutText")
        self._about_text.setWordWrap(True)
        self._about_text.setOpenExternalLinks(True)
        layout.addWidget(self._about_text)
        layout.addStretch(1)
        return widget

    def retranslate_ui(self) -> None:
        self._page_title.setText(tr("settings.title"))
        self._tabs.setTabText(0, tr("settings.tab.general"))
        self._tabs.setTabText(1, tr("settings.tab.network"))
        self._tabs.setTabText(2, tr("settings.tab.advanced"))
        self._tabs.setTabText(3, tr("settings.tab.about"))

        for label, key in self._form_labels:
            label.setText(tr(key))

        for btn in self._browse_buttons:
            if btn is self._ffmpeg_auto_btn:
                btn.setText(tr("settings.ffmpeg_detect"))
            else:
                btn.setText(tr("common.browse"))

        q = self._quality.currentData()
        self._fill_quality_combo(self._quality)
        if q:
            idx = self._quality.findData(q)
            if idx >= 0:
                self._quality.setCurrentIndex(idx)

        f = self._format.currentData()
        self._format.blockSignals(True)
        self._format.clear()
        self._format.addItem(tr("format.mp4"), "mp4")
        self._format.addItem(tr("format.mkv"), "mkv")
        if f:
            idx = self._format.findData(f)
            if idx >= 0:
                self._format.setCurrentIndex(idx)
        self._format.blockSignals(False)

        t = self._theme.currentData()
        self._theme.blockSignals(True)
        self._theme.clear()
        self._theme.addItem(tr("theme.dark"), "dark")
        self._theme.addItem(tr("theme.light"), "light")
        if t:
            idx = self._theme.findData(t)
            if idx >= 0:
                self._theme.setCurrentIndex(idx)
        self._theme.blockSignals(False)

        self._fill_language_combo()

        p = self._proxy_type.currentData()
        self._proxy_type.blockSignals(True)
        self._proxy_type.clear()
        self._proxy_type.addItem(tr("proxy.none"), "None")
        self._proxy_type.addItem("HTTP", "HTTP")
        self._proxy_type.addItem("SOCKS5", "SOCKS5")
        if p:
            idx = self._proxy_type.findData(p)
            if idx >= 0:
                self._proxy_type.setCurrentIndex(idx)
        self._proxy_type.blockSignals(False)

        self._proxy_host.setPlaceholderText(tr("settings.proxy_host_ph"))
        self._proxy_port.setPlaceholderText(tr("settings.proxy_port_ph"))
        self._user_agent.setPlaceholderText(tr("settings.user_agent_ph"))
        self._rate.setSpecialValueText(tr("common.unlimited"))
        self._template_hint.setText(tr("settings.template_hint"))
        self._version_label.setText(tr("settings.version", version=__version__))
        self._about_text.setText(tr("settings.about_body"))
        self._refresh_ffmpeg_status()

    def _save_ffmpeg_path(self, value: str) -> None:
        self.settings.set("ffmpeg_path", value.strip())
        self._refresh_ffmpeg_status()

    def _browse_ffmpeg(self) -> None:
        start = self._ffmpeg_edit.text() or str(Path.home())
        chosen, _ = QFileDialog.getOpenFileName(
            self, tr("settings.locate_ffmpeg"), start, "ffmpeg (ffmpeg.exe ffmpeg)"
        )
        if chosen:
            self._ffmpeg_edit.setText(chosen)
            self._save_ffmpeg_path(chosen)

    def _auto_detect_ffmpeg(self) -> None:
        from utils import prepare_ffmpeg_environment

        custom = self._ffmpeg_edit.text().strip() or None
        pair = prepare_ffmpeg_environment(custom)
        if pair:
            folder = str(Path(pair[0]).parent)
            self._ffmpeg_edit.setText(folder)
            self.settings.set("ffmpeg_path", folder)
        self._refresh_ffmpeg_status()

    def _refresh_ffmpeg_status(self) -> None:
        from utils import resolve_ffmpeg

        custom = self._ffmpeg_edit.text().strip() or None
        pair = resolve_ffmpeg(custom)
        if pair:
            self._ffmpeg_hint.setText(tr("settings.ffmpeg_detected", path=pair[0]))
        else:
            self._ffmpeg_hint.setText(tr("settings.ffmpeg_not_found"))
        self._ffmpeg_edit.setPlaceholderText(tr("settings.ffmpeg_auto_ph"))

    # -- handlers ----------------------------------------------------------

    def _on_theme_data(self, _index: int) -> None:
        name = self._theme.currentData()
        if name:
            self.settings.set("theme", name)
            self.theme_changed.emit(str(name))

    def _on_language(self, _index: int) -> None:
        code = self._language.currentData()
        if not code:
            return
        code = normalize_language(code)
        self.settings.set("language", code)
        i18n.set_language(code)
        self.language_changed.emit(code)
