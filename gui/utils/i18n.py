"""Lightweight UI translations (English / Turkish)."""

from __future__ import annotations

from typing import Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal

LANG_EN = "en"
LANG_TR = "tr"

LANGUAGE_CHOICES: Dict[str, str] = {
    LANG_EN: "English",
    LANG_TR: "Türkçe",
}

_STRINGS: Dict[str, Dict[str, str]] = {
    LANG_EN: {
        # Navigation
        "nav.section": "NAVIGATION",
        "nav.home": "Home",
        "nav.queue": "Queue",
        "nav.history": "History",
        "nav.settings": "Settings",
        "nav.about": "About",
        # Home
        "home.title": "Download",
        "home.subtitle": "Paste a link or import a list to start downloading.",
        "home.url_placeholder": "Paste video URL here (YouTube, Kick, X, …)…",
        "home.paste_tooltip": "Paste from clipboard",
        "home.add_queue": "Add to Queue",
        "home.dropzone": "Drag & drop a .txt file of URLs here to batch import",
        "home.options": "Options",
        "home.quality": "Quality",
        "home.format": "Format",
        "home.concurrent": "Concurrent downloads",
        "home.output_folder": "Output folder",
        "home.thumbnail": "Download thumbnail",
        "home.metadata": "Save metadata",
        "home.subtitles": "Embed subtitles",
        "home.subtitles_tip": "Subtitles are not provided by the source.",
        "home.hint_enter_url": "Enter a URL first.",
        "home.hint_unsupported": "That URL isn't supported by yt-dlp.",
        "home.hint_added": "Added to queue.",
        "home.hint_imported": "Imported {count} URL(s).",
        "home.hint_no_urls": "No valid URLs found.",
        "home.choose_output": "Choose output folder",
        # Quality presets
        "quality.best": "Best",
        # Queue
        "queue.title": "Queue",
        "queue.count": "{total} item(s) · {active} active",
        "queue.pause_all": "Pause All",
        "queue.resume_all": "Resume All",
        "queue.clear_done": "Clear Completed",
        "queue.clear_failed": "Clear Failed",
        "queue.empty_title": "No downloads yet",
        "queue.empty_text": "Add a URL from the Home page to get started.",
        # History
        "history.title": "History",
        "history.search": "Search by title, uploader or URL…",
        "history.clear_tooltip": "Clear all history",
        "history.col.preview": "Preview",
        "history.col.title": "Title",
        "history.col.uploader": "Uploader",
        "history.col.quality": "Quality",
        "history.col.size": "Size",
        "history.col.date": "Date",
        "history.col.status": "Status",
        "history.menu.redownload": "Re-download",
        "history.menu.open_file": "Open file",
        "history.menu.open_folder": "Open folder",
        "history.menu.copy_url": "Copy URL",
        "history.menu.remove": "Remove from history",
        # Settings tabs
        "settings.title": "Settings",
        "settings.tab.general": "General",
        "settings.tab.network": "Network",
        "settings.tab.advanced": "Advanced",
        "settings.tab.about": "About",
        "settings.output_folder": "Default output folder",
        "settings.default_quality": "Default quality",
        "settings.default_format": "Default format",
        "settings.theme": "Theme",
        "settings.language": "Language",
        "settings.proxy_type": "Proxy type",
        "settings.proxy_host": "Proxy host",
        "settings.proxy_port": "Proxy port",
        "settings.timeout": "Connection timeout",
        "settings.retries": "Retry count",
        "settings.rate_limit": "Rate limit",
        "settings.threads": "Segment threads (per download)",
        "settings.ffmpeg_path": "ffmpeg path",
        "settings.cookies_file": "Cookies file",
        "settings.user_agent": "Custom user-agent",
        "settings.filename_template": "Filename template",
        "settings.template_hint": "Template keys: %(uploader)s %(title)s %(id)s %(quality)s %(ext)s",
        "settings.proxy_host_ph": "e.g. 127.0.0.1",
        "settings.proxy_port_ph": "e.g. 1080",
        "settings.user_agent_ph": "Leave blank to rotate built-in agents",
        "settings.choose_output": "Choose output folder",
        "settings.locate_ffmpeg": "Locate ffmpeg",
        "settings.ffmpeg_auto_ph": "Leave empty for automatic detection",
        "settings.ffmpeg_detect": "Auto-detect",
        "settings.ffmpeg_detected": "Detected: {path}",
        "settings.ffmpeg_not_found": "ffmpeg not found yet — it will be downloaded on first run (Windows) or must be installed manually.",
        "settings.choose_cookies": "Choose cookies.txt",
        "settings.about_body": (
            "A modern desktop front-end for the <b>phvid</b> downloader.<br><br>"
            "Built with PyQt6. Downloads run in background threads via the phvid "
            "backend (yt-dlp extraction, concurrent HLS segments, ffmpeg muxing).<br><br>"
            "Use responsibly and only for content you are authorised to download. "
            "Respect the source site's Terms of Service and your local laws."
        ),
        "settings.version": "Version {version}",
        # Theme / format
        "theme.dark": "Dark",
        "theme.light": "Light",
        "format.mp4": "MP4",
        "format.mkv": "MKV",
        "proxy.none": "None",
        "common.browse": "Browse",
        "common.unlimited": "Unlimited",
        # Download status badges
        "status.queued": "QUEUED",
        "status.downloading": "DOWNLOADING",
        "status.paused": "PAUSED",
        "status.complete": "COMPLETE",
        "status.failed": "FAILED",
        "status.processing": "PROCESSING",
        # Download card
        "card.resolving": "Resolving…",
        "card.waiting": "Waiting in queue…",
        "card.merging": "Merging / finalising…",
        "card.paused_at": "Paused at {percent:.0f}%",
        "card.complete": "Complete",
        "card.complete_size": "Complete  •  {size}",
        "card.failed": "Failed",
        "card.failed_detail": "Failed  •  {error}",
        "card.progress": "{percent:.0f}%  •  {speed}  •  {eta}",
        "card.eta": "ETA {value}",
        "card.eta_unknown": "ETA —",
        "card.tooltip.pause": "Pause",
        "card.tooltip.resume": "Resume",
        "card.tooltip.retry": "Retry",
        "card.tooltip.open_folder": "Open folder",
        "card.tooltip.cancel": "Cancel",
        # Tray & window
        "tray.tooltip": "PHDownloader",
        "tray.show_hide": "Show / Hide",
        "tray.pause_all": "Pause All",
        "tray.quit": "Quit",
        "tray.download_complete": "Download complete",
        "tray.still_running": "Still running",
        "tray.minimized": "PHDownloader is minimised to the tray.",
        "tray.setup_complete": "Setup complete",
        "tray.ffmpeg_ready": "ffmpeg installed — full MP4/MKV output enabled.",
        "tray.ffmpeg_missing": "ffmpeg unavailable",
        "tray.ffmpeg_ts_fallback": "Downloads will be saved as .ts (plays in VLC). Install ffmpeg for MP4.",
        "setup.working": "Setting up…",
        "setup.ffmpeg_first": "First-time setup: getting ffmpeg ready…",
        "setup.ffmpeg_done": "ffmpeg ready — full MP4/MKV output enabled.",
        "setup.ffmpeg_ts": "ffmpeg unavailable — downloads will be saved as .ts.",
        # ffmpeg bootstrap (message ids from ffmpeg_setup)
        "ffmpeg.preparing": "Preparing ffmpeg download…",
        "ffmpeg.downloading": "Downloading ffmpeg…",
        "ffmpeg.extracting": "Extracting ffmpeg…",
        "ffmpeg.ready": "ffmpeg ready.",
        "ffmpeg.incomplete": "ffmpeg install incomplete.",
        "ffmpeg.not_found_unix": (
            "ffmpeg not found. Install it via your package manager "
            "(e.g. 'brew install ffmpeg' or 'apt install ffmpeg')."
        ),
        "ffmpeg.install_failed": "Could not auto-install ffmpeg: {error}",
    },
    LANG_TR: {
        "nav.section": "MENÜ",
        "nav.home": "Ana Sayfa",
        "nav.queue": "Kuyruk",
        "nav.history": "Geçmiş",
        "nav.settings": "Ayarlar",
        "nav.about": "Hakkında",
        "home.title": "İndir",
        "home.subtitle": "İndirmeye başlamak için bir bağlantı yapıştırın veya liste içe aktarın.",
        "home.url_placeholder": "Video bağlantısını yapıştırın (YouTube, Kick, X, …)",
        "home.paste_tooltip": "Panodan yapıştır",
        "home.add_queue": "Kuyruğa Ekle",
        "home.dropzone": "Toplu içe aktarmak için URL listesi (.txt) dosyasını sürükleyip bırakın",
        "home.options": "Seçenekler",
        "home.quality": "Kalite",
        "home.format": "Biçim",
        "home.concurrent": "Eşzamanlı indirme",
        "home.output_folder": "Çıktı klasörü",
        "home.thumbnail": "Küçük resmi indir",
        "home.metadata": "Meta veriyi kaydet",
        "home.subtitles": "Altyazıları göm",
        "home.subtitles_tip": "Kaynak altyazı sağlamıyor.",
        "home.hint_enter_url": "Önce bir URL girin.",
        "home.hint_unsupported": "Bu URL yt-dlp tarafından desteklenmiyor.",
        "home.hint_added": "Kuyruğa eklendi.",
        "home.hint_imported": "{count} URL içe aktarıldı.",
        "home.hint_no_urls": "Geçerli URL bulunamadı.",
        "home.choose_output": "Çıktı klasörünü seçin",
        "quality.best": "En İyi",
        "queue.title": "Kuyruk",
        "queue.count": "{total} öğe · {active} aktif",
        "queue.pause_all": "Tümünü Duraklat",
        "queue.resume_all": "Tümünü Sürdür",
        "queue.clear_done": "Tamamlananları Temizle",
        "queue.clear_failed": "Başarısızları Temizle",
        "queue.empty_title": "Henüz indirme yok",
        "queue.empty_text": "Başlamak için Ana Sayfa'dan bir URL ekleyin.",
        "history.title": "Geçmiş",
        "history.search": "Başlık, yükleyen veya URL ile ara…",
        "history.clear_tooltip": "Tüm geçmişi temizle",
        "history.col.preview": "Önizleme",
        "history.col.title": "Başlık",
        "history.col.uploader": "Yükleyen",
        "history.col.quality": "Kalite",
        "history.col.size": "Boyut",
        "history.col.date": "Tarih",
        "history.col.status": "Durum",
        "history.menu.redownload": "Yeniden indir",
        "history.menu.open_file": "Dosyayı aç",
        "history.menu.open_folder": "Klasörü aç",
        "history.menu.copy_url": "URL'yi kopyala",
        "history.menu.remove": "Geçmişten kaldır",
        "settings.title": "Ayarlar",
        "settings.tab.general": "Genel",
        "settings.tab.network": "Ağ",
        "settings.tab.advanced": "Gelişmiş",
        "settings.tab.about": "Hakkında",
        "settings.output_folder": "Varsayılan çıktı klasörü",
        "settings.default_quality": "Varsayılan kalite",
        "settings.default_format": "Varsayılan biçim",
        "settings.theme": "Tema",
        "settings.language": "Dil",
        "settings.proxy_type": "Proxy türü",
        "settings.proxy_host": "Proxy sunucusu",
        "settings.proxy_port": "Proxy portu",
        "settings.timeout": "Bağlantı zaman aşımı",
        "settings.retries": "Yeniden deneme",
        "settings.rate_limit": "Hız sınırı",
        "settings.threads": "Segment iş parçacığı (indirme başına)",
        "settings.ffmpeg_path": "ffmpeg yolu",
        "settings.cookies_file": "Çerez dosyası",
        "settings.user_agent": "Özel user-agent",
        "settings.filename_template": "Dosya adı şablonu",
        "settings.template_hint": "Şablon anahtarları: %(uploader)s %(title)s %(id)s %(quality)s %(ext)s",
        "settings.proxy_host_ph": "ör. 127.0.0.1",
        "settings.proxy_port_ph": "ör. 1080",
        "settings.user_agent_ph": "Boş bırakılırsa yerleşik listeler kullanılır",
        "settings.choose_output": "Çıktı klasörünü seçin",
        "settings.locate_ffmpeg": "ffmpeg konumunu seç",
        "settings.ffmpeg_auto_ph": "Otomatik bulma için boş bırakın",
        "settings.ffmpeg_detect": "Otomatik Bul",
        "settings.ffmpeg_detected": "Bulundu: {path}",
        "settings.ffmpeg_not_found": "ffmpeg henüz bulunamadı — ilk çalıştırmada indirilecek (Windows) veya elle kurulmalı.",
        "settings.choose_cookies": "cookies.txt seçin",
        "settings.about_body": (
            "<b>phvid</b> indirici için modern bir masaüstü arayüzü.<br><br>"
            "PyQt6 ile geliştirildi. İndirmeler phvid arka ucu üzerinden arka plan "
            "iş parçacıklarında çalışır (yt-dlp çıkarma, eşzamanlı HLS segmentleri, "
            "ffmpeg birleştirme).<br><br>"
            "Yalnızca indirmeye yetkili olduğunuz içerikler için sorumlu kullanın. "
            "Kaynak sitenin kullanım şartlarına ve yerel yasalara uyun."
        ),
        "settings.version": "Sürüm {version}",
        "theme.dark": "Koyu",
        "theme.light": "Açık",
        "format.mp4": "MP4",
        "format.mkv": "MKV",
        "proxy.none": "Yok",
        "common.browse": "Gözat",
        "common.unlimited": "Sınırsız",
        "status.queued": "KUYRUKTA",
        "status.downloading": "İNDİRİLİYOR",
        "status.paused": "DURAKLATILDI",
        "status.complete": "TAMAMLANDI",
        "status.failed": "BAŞARISIZ",
        "status.processing": "İŞLENİYOR",
        "card.resolving": "Çözümleniyor…",
        "card.waiting": "Kuyrukta bekleniyor…",
        "card.merging": "Birleştiriliyor / tamamlanıyor…",
        "card.paused_at": "{percent:.0f}% konumunda duraklatıldı",
        "card.complete": "Tamamlandı",
        "card.complete_size": "Tamamlandı  •  {size}",
        "card.failed": "Başarısız",
        "card.failed_detail": "Başarısız  •  {error}",
        "card.progress": "{percent:.0f}%  •  {speed}  •  {eta}",
        "card.eta": "Kalan {value}",
        "card.eta_unknown": "Kalan —",
        "card.tooltip.pause": "Duraklat",
        "card.tooltip.resume": "Sürdür",
        "card.tooltip.retry": "Yeniden dene",
        "card.tooltip.open_folder": "Klasörü aç",
        "card.tooltip.cancel": "İptal",
        "tray.tooltip": "PHDownloader",
        "tray.show_hide": "Göster / Gizle",
        "tray.pause_all": "Tümünü Duraklat",
        "tray.quit": "Çık",
        "tray.download_complete": "İndirme tamamlandı",
        "tray.still_running": "Hâlâ çalışıyor",
        "tray.minimized": "PHDownloader sistem tepsisine küçültüldü.",
        "tray.setup_complete": "Kurulum tamamlandı",
        "tray.ffmpeg_ready": "ffmpeg kuruldu — tam MP4/MKV çıktısı etkin.",
        "tray.ffmpeg_missing": "ffmpeg kullanılamıyor",
        "tray.ffmpeg_ts_fallback": "İndirmeler .ts olarak kaydedilir (VLC'de oynatılır). MP4 için ffmpeg kurun.",
        "setup.working": "Hazırlanıyor…",
        "setup.ffmpeg_first": "İlk kurulum: ffmpeg hazırlanıyor…",
        "setup.ffmpeg_done": "ffmpeg hazır — tam MP4/MKV çıktısı etkin.",
        "setup.ffmpeg_ts": "ffmpeg yok — indirmeler .ts olarak kaydedilecek.",
        "ffmpeg.preparing": "ffmpeg indirmesi hazırlanıyor…",
        "ffmpeg.downloading": "ffmpeg indiriliyor…",
        "ffmpeg.extracting": "ffmpeg çıkarılıyor…",
        "ffmpeg.ready": "ffmpeg hazır.",
        "ffmpeg.incomplete": "ffmpeg kurulumu tamamlanamadı.",
        "ffmpeg.not_found_unix": (
            "ffmpeg bulunamadı. Paket yöneticinizle kurun "
            "(ör. 'brew install ffmpeg' veya 'apt install ffmpeg')."
        ),
        "ffmpeg.install_failed": "ffmpeg otomatik kurulamadı: {error}",
    },
}


class I18n(QObject):
    """Global translator with a change notification signal."""

    language_changed = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._lang = LANG_EN

    @property
    def language(self) -> str:
        return self._lang

    def set_language(self, code: str) -> None:
        code = normalize_language(code)
        if code == self._lang:
            return
        self._lang = code
        self.language_changed.emit(code)

    def tr(self, key: str, **kwargs: object) -> str:
        text = _STRINGS.get(self._lang, {}).get(key)
        if text is None:
            text = _STRINGS[LANG_EN].get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError):
                return text
        return text


i18n = I18n()


def normalize_language(value: object) -> str:
    """Map persisted settings values to a language code."""
    raw = str(value or LANG_EN).strip()
    lowered = raw.lower()
    if lowered in (LANG_EN, "english", "en-us", "en_gb"):
        return LANG_EN
    if lowered in (LANG_TR, "türkçe", "turkce", "turkish", "tr-tr"):
        return LANG_TR
    return LANG_EN


def tr(key: str, **kwargs: object) -> str:
    """Translate ``key`` in the active language."""
    return i18n.tr(key, **kwargs)


def quality_label(internal: str) -> str:
    """Map stored quality value to a localized combo label."""
    if internal == "best":
        return tr("quality.best")
    return f"{internal}p"


def quality_value(label: str) -> str:
    """Map a localized combo label back to the stored quality value."""
    if label == tr("quality.best"):
        return "best"
    return label.rstrip("p")
