"""Home / download page: URL entry, batch import, and per-download options."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from extractor import Extractor
from gui.core.download_manager import DownloadManager, proxies_from_settings
from gui.utils.i18n import i18n, quality_label, tr
from gui.utils.settings import Settings
from gui.widgets.custom_widgets import TextButton, ThemedIconLabel, repolish
from gui.widgets.url_input import UrlInputBar

QUALITY_VALUES = ["best", "2160", "1440", "1080", "720", "480"]


class DropZone(QFrame):
    """A dashed drop target that accepts ``.txt`` files of URLs."""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(84)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        icon = ThemedIconLabel("upload-cloud", role="TEXT_DIM", size=26)
        self._text = QLabel()
        self._text.setObjectName("DropZoneText")
        layout.addStretch(1)
        layout.addWidget(icon)
        layout.addWidget(self._text)
        layout.addStretch(1)
        i18n.language_changed.connect(lambda _c: self._text.setText(tr("home.dropzone")))
        self._text.setText(tr("home.dropzone"))

    def _set_dragging(self, value: bool) -> None:
        self.setProperty("dragging", value)
        repolish(self)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._set_dragging(True)

    def dragLeaveEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._set_dragging(False)

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt override)
        self._set_dragging(False)
        paths = [
            url.toLocalFile()
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".txt")
        ]
        if paths:
            self.files_dropped.emit(paths)


class HomePage(QWidget):
    """Compose URL input, batch import and download options."""

    queued = pyqtSignal()

    def __init__(
        self, settings: Settings, manager: DownloadManager, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.manager = manager
        self._field_labels: List[tuple[QLabel, str]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(18)

        self._title = QLabel()
        self._title.setObjectName("PageTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("PageSubtitle")
        root.addWidget(self._title)
        root.addWidget(self._subtitle)

        root.addWidget(self._build_url_row())
        root.addWidget(self._build_dropzone())
        root.addWidget(self._build_options_panel())
        root.addStretch(1)

        self.hint = QLabel("")
        self.hint.setObjectName("Hint")
        root.addWidget(self.hint)

        i18n.language_changed.connect(lambda _c: self.retranslate_ui())
        self.retranslate_ui()
        self._load_from_settings()

    # -- builders ----------------------------------------------------------

    def _build_url_row(self) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.url_bar = UrlInputBar()
        self.url_bar.submitted.connect(lambda _t: self._add_current())
        self.add_btn = TextButton(variant="accent", icon_name="plus")
        self.add_btn.clicked.connect(self._add_current)
        layout.addWidget(self.url_bar, 1)
        layout.addWidget(self.add_btn)
        return row

    def _build_dropzone(self) -> QWidget:
        self.dropzone = DropZone()
        self.dropzone.files_dropped.connect(self._import_files)
        return self.dropzone

    def _build_options_panel(self) -> QWidget:
        panel = QFrame()
        panel.setObjectName("Panel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(18, 18, 18, 18)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(14)

        self._options_heading = QLabel()
        self._options_heading.setObjectName("PanelTitle")
        grid.addWidget(self._options_heading, 0, 0, 1, 3)

        lbl_quality = self._field_label("home.quality")
        grid.addWidget(lbl_quality, 1, 0)
        self.quality_combo = QComboBox()
        self._fill_quality_combo()
        self.quality_combo.currentIndexChanged.connect(self._on_quality_changed)
        grid.addWidget(self.quality_combo, 2, 0)

        lbl_format = self._field_label("home.format")
        grid.addWidget(lbl_format, 1, 1)
        self.format_combo = QComboBox()
        self.format_combo.addItem(tr("format.mp4"), "mp4")
        self.format_combo.addItem(tr("format.mkv"), "mkv")
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        grid.addWidget(self.format_combo, 2, 1)

        lbl_conc = self._field_label("home.concurrent")
        grid.addWidget(lbl_conc, 1, 2)
        slider_row = QWidget()
        sl = QHBoxLayout(slider_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(10)
        self.concurrency = QSlider(Qt.Orientation.Horizontal)
        self.concurrency.setRange(1, 10)
        self.concurrency.valueChanged.connect(self._on_concurrency)
        self.conc_value = QLabel("3")
        self.conc_value.setMinimumWidth(18)
        sl.addWidget(self.concurrency, 1)
        sl.addWidget(self.conc_value)
        grid.addWidget(slider_row, 2, 2)

        lbl_out = self._field_label("home.output_folder")
        grid.addWidget(lbl_out, 3, 0)
        out_row = QWidget()
        orl = QHBoxLayout(out_row)
        orl.setContentsMargins(0, 0, 0, 0)
        orl.setSpacing(8)
        self.output_edit = QLineEdit()
        self.output_edit.editingFinished.connect(
            lambda: self.settings.set("output_dir", self.output_edit.text())
        )
        self.browse_btn = TextButton(variant="ghost", icon_name="folder")
        self.browse_btn.clicked.connect(self._browse_output)
        orl.addWidget(self.output_edit, 1)
        orl.addWidget(self.browse_btn)
        grid.addWidget(out_row, 4, 0, 1, 3)

        toggles = QWidget()
        trl = QHBoxLayout(toggles)
        trl.setContentsMargins(0, 0, 0, 0)
        trl.setSpacing(22)
        self.thumb_chk = QCheckBox()
        self.meta_chk = QCheckBox()
        self.subs_chk = QCheckBox()
        self.subs_chk.setEnabled(False)
        self.thumb_chk.toggled.connect(lambda v: self.settings.set("download_thumbnail", v))
        self.meta_chk.toggled.connect(lambda v: self.settings.set("save_metadata", v))
        for chk in (self.thumb_chk, self.meta_chk, self.subs_chk):
            trl.addWidget(chk)
        trl.addStretch(1)
        grid.addWidget(toggles, 5, 0, 1, 3)

        return panel

    def _field_label(self, key: str) -> QLabel:
        label = QLabel()
        label.setObjectName("FieldLabel")
        self._field_labels.append((label, key))
        return label

    def _fill_quality_combo(self) -> None:
        current = self.quality_combo.currentData() if self.quality_combo.count() else None
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        for value in QUALITY_VALUES:
            self.quality_combo.addItem(quality_label(value), value)
        if current:
            idx = self.quality_combo.findData(current)
            if idx >= 0:
                self.quality_combo.setCurrentIndex(idx)
        self.quality_combo.blockSignals(False)

    def retranslate_ui(self) -> None:
        self.url_bar.retranslate_ui()
        self._title.setText(tr("home.title"))
        self._subtitle.setText(tr("home.subtitle"))
        self.add_btn.setText(tr("home.add_queue"))
        self.browse_btn.setText(tr("common.browse"))
        self._options_heading.setText(tr("home.options"))
        for label, key in self._field_labels:
            label.setText(tr(key))
        self.thumb_chk.setText(tr("home.thumbnail"))
        self.meta_chk.setText(tr("home.metadata"))
        self.subs_chk.setText(tr("home.subtitles"))
        self.subs_chk.setToolTip(tr("home.subtitles_tip"))

        q = self.quality_combo.currentData()
        self._fill_quality_combo()
        if q:
            idx = self.quality_combo.findData(q)
            if idx >= 0:
                self.quality_combo.setCurrentIndex(idx)

        f = self.format_combo.currentData()
        self.format_combo.blockSignals(True)
        self.format_combo.clear()
        self.format_combo.addItem(tr("format.mp4"), "mp4")
        self.format_combo.addItem(tr("format.mkv"), "mkv")
        if f:
            idx = self.format_combo.findData(f)
            if idx >= 0:
                self.format_combo.setCurrentIndex(idx)
        self.format_combo.blockSignals(False)

    # -- settings sync -----------------------------------------------------

    def _load_from_settings(self) -> None:
        s = self.settings
        quality = s.get("quality")
        idx = self.quality_combo.findData(quality)
        if idx >= 0:
            self.quality_combo.setCurrentIndex(idx)
        fmt_idx = self.format_combo.findData(s.get("format"))
        if fmt_idx >= 0:
            self.format_combo.setCurrentIndex(fmt_idx)
        self.output_edit.setText(s.get("output_dir"))
        self.concurrency.setValue(s.get("concurrent"))
        self.conc_value.setText(str(s.get("concurrent")))
        self.thumb_chk.setChecked(s.get("download_thumbnail"))
        self.meta_chk.setChecked(s.get("save_metadata"))

    def _on_quality_changed(self, _index: int) -> None:
        value = self.quality_combo.currentData()
        if value:
            self.settings.set("quality", value)

    def _on_format_changed(self, _index: int) -> None:
        value = self.format_combo.currentData()
        if value:
            self.settings.set("format", value)

    def _on_concurrency(self, value: int) -> None:
        self.conc_value.setText(str(value))
        self.settings.set("concurrent", value)
        self.manager.set_max_concurrent(value)

    def _browse_output(self) -> None:
        start = self.output_edit.text() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(self, tr("home.choose_output"), start)
        if chosen:
            self.output_edit.setText(chosen)
            self.settings.set("output_dir", chosen)

    # -- actions -----------------------------------------------------------

    def _build_opts(self) -> dict:
        s = self.settings
        return {
            "output_dir": self.output_edit.text().strip() or s.get("output_dir"),
            "quality": self.quality_combo.currentData() or s.get("quality"),
            "format": self.format_combo.currentData() or s.get("format"),
            "threads": s.get("threads"),
            "proxies": proxies_from_settings(s),
            "cookies_file": s.get("cookies_file"),
            "save_metadata": self.meta_chk.isChecked(),
            "download_thumbnail": self.thumb_chk.isChecked(),
            "rate_limit": s.get("rate_limit"),
            "filename_template": s.get("filename_template"),
            "ffmpeg_path": s.get("ffmpeg_path"),
        }

    def _add_current(self) -> None:
        url = self.url_bar.text()
        if not url:
            self._flash(tr("home.hint_enter_url"))
            return
        if not Extractor.is_supported_url(url):
            self._flash(tr("home.hint_unsupported"))
            return
        self.manager.add(url, self._build_opts())
        self.url_bar.clear()
        self._flash(tr("home.hint_added"))
        self.queued.emit()

    def _import_files(self, paths: List[str]) -> None:
        added = 0
        for path in paths:
            try:
                lines = Path(path).read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for raw in lines:
                url = raw.strip()
                if url and not url.startswith("#") and Extractor.is_supported_url(url):
                    self.manager.add(url, self._build_opts())
                    added += 1
        self._flash(
            tr("home.hint_imported", count=added) if added else tr("home.hint_no_urls")
        )
        if added:
            self.queued.emit()

    def _flash(self, message: str) -> None:
        self.hint.setText(message)
