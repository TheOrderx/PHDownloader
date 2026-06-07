<div align="center">

# PHDownloader

**Modern, çoklu site video indirici — PyQt6 masaüstü uygulaması + tam CLI**

[**English**](README.md) · **Türkçe**

**YouTube, Twitter/X, PornHub** ve [yt-dlp](https://github.com/yt-dlp/yt-dlp) tarafından desteklenen tüm sitelerden video indirin.  
Eşzamanlı HLS indirme, otomatik ffmpeg kurulumu, yüksek kalite için ayrı ses birleştirme, koyu/açık tema, Türkçe & İngilizce arayüz.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41cd52)
![Platform](https://img.shields.io/badge/Platform-Windows-0078d6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

[Özellikler](#-özellikler) · [Hızlı Başlangıç](#-hızlı-başlangıç) · [CLI](#-komut-satırı) · [Derleme](#-exe-derleme) · [Sorun Giderme](#-sorun-giderme)

</div>

---

## ⚠️ Yasal uyarı

- **Yalnızca kişisel ve yasal kullanım içindir.** Yazılımı nasıl kullandığınızdan yalnızca siz sorumlusunuz.
- Yalnızca **sahibi olduğunuz veya indirmeye açıkça yetkili olduğunuz** içerikleri indirin. İzinsiz telif hakkı korumalı içerik indirmek ülkenizde yasadışı olabilir.
- Her sitenin **Kullanım Şartlarına** uyun. Otomatik indirme bu şartları ihlal edebilir.
- Yetişkin sitelere erişirken **18+** olmalı ve yerel yasalara uymalısınız.
- Bu proje **YouTube, X/Twitter, PornHub veya başka hiçbir platformla bağlantılı değildir** ve onlar tarafından desteklenmemektedir. Tüm markalar ilgili sahiplerine aittir.
- **"Olduğu gibi"** sunulmaktadır, garanti verilmez. Ayrıntılar için [`LICENSE`](LICENSE) dosyasına bakın.

---

## 📸 Ekran görüntüleri

> `docs/` klasörüne ekran görüntüleri ekleyin.

| Ana Sayfa | Kuyruk | Geçmiş | Ayarlar |
| --- | --- | --- | --- |
| ![Ana Sayfa](docs/home.png) | ![Kuyruk](docs/queue.png) | ![Geçmiş](docs/history.png) | ![Ayarlar](docs/settings.png) |

---

## ✨ Özellikler

### Masaüstü arayüzü (PyQt6)

- **Modern arayüz** — koyu / açık tema, turuncu vurgu, çerçevesiz pencere, özel başlık çubuğu, sistem tepsisi
- **Çoklu site URL'leri** — link yapıştırın veya `.txt` dosyasını sürükleyip bırakın
- **İndirme kuyruğu** — eşzamanlı indirmeler, öğe bazında duraklat / sürdür / iptal
- **Canlı kartlar** — küçük resim, başlık, yükleyen, kalite, hız ve ETA ile ilerleme çubuğu
- **Geçmiş** — SQLite veritabanı, arama, yeniden indir, klasörü aç, URL kopyala
- **Ayarlar** — kalite, format, proxy, hız limiti, çerezler, dosya adı şablonu, ffmpeg yolu
- **Çoklu dil** — Türkçe & İngilizce (`Ayarlar → Dil`)
- **Bildirimler** — indirme bitince masaüstü uyarıları
- **Donmayan arayüz** — tüm indirmeler arka plan iş parçacıklarında çalışır

### İndirme motoru (GUI + CLI)

- **yt-dlp çıkarımı** — 1000+ site (YouTube, Twitter/X, Vimeo, Twitch vb.)
- **PornHub HTML yedeği** — yt-dlp başarısız olursa özel `mediaDefinitions` ayrıştırıcısı
- **Kalite seçimi** — `best` veya sabit çözünürlük (240p → 2160p)
- **HLS (m3u8)** — eşzamanlı segment indirme + ffmpeg birleştirme
- **Doğrudan MP4** — **kaldığı yerden devam** destekli akış indirme
- **Ayrı ses birleştirme** — YouTube/Twitter yüksek kalite (video-only + ses) ffmpeg ile birleştirilir
- **Twitter/X optimizasyonu** — güvenilir ses için yt-dlp yerleşik `video+ses` mux
- **Otomatik ffmpeg** — PATH, Scoop, Chocolatey, Program Files veya ilk çalıştırmada indirme (Windows)
- **Meta veri dosyaları** — `.info.json` + `.jpg` küçük resim
- **Dayanıklılık** — üstel geri çekilme, proxy rotasyonu, ffprobe bütünlük kontrolü
- **ffmpeg olmadan** — şifresiz HLS oynatılabilir `.ts` olarak kaydedilir (VLC / MPV)

---

## 🌐 Desteklenen siteler

**yt-dlp** tarafından desteklenen her site çalışır. Yaygın örnekler:

| Platform | Not |
| --- | --- |
| **YouTube** | Yüksek kalite = ayrı video + ses; ffmpeg ile otomatik birleştirilir |
| **Twitter / X** | HLS video + ses; güvenilir ses için özel mux yolu |
| **PornHub** | yt-dlp + özel `mediaDefinitions` HTML yedeği |
| **Vimeo, Twitch, Reddit, TikTok, …** | yt-dlp çıkarıcıları ile |

Siteler sık değişir — yt-dlp'yi güncel tutun:

```bash
pip install -U yt-dlp
```

---

## 🚀 Hızlı başlangıç

### Seçenek A — Windows exe (Python gerekmez)

1. [Releases](https://github.com/TheOrderx/PHDownloader/releases) sayfasından **`PHDownloader.exe`** indirin.
2. **`PHDownloader.exe`** dosyasını çalıştırın.
3. İlk açılışta ffmpeg otomatik indirilir (alt banner).
4. **Ana Sayfa**'ya URL yapıştırın → **Kuyruğa Ekle**.

### Seçenek B — Kaynaktan çalıştırma

```bash
git clone https://github.com/TheOrderx/PHDownloader.git
cd PHDownloader
python launcher.py
```

`launcher.py` eksik Python paketlerini otomatik kurar, ardından arayüzü açar.

### Seçenek C — Yalnızca CLI (arayüz yok)

```bash
pip install -r requirements.txt
python main.py -u "https://www.youtube.com/watch?v=VIDEO_ID"
```

---

## 🛠️ Exe derleme

```bash
python build_exe.py            # → dist/PHDownloader.exe  (tek dosya)
python build_exe.py --onedir   # → dist/PHDownloader/     (daha hızlı açılış)
```

PyInstaller eksikse otomatik kurulur. Derlemeden önce çalışan `PHDownloader.exe` süreçlerini kapatın.

---

## 💻 Komut satırı

```bash
# Tek URL
python main.py -u "https://www.youtube.com/watch?v=XXXX"

# Toplu dosya (satır başına bir URL)
python main.py -b urls.txt -q 1080 -o ./downloads -t 32

# PornHub örneği
python main.py -u "https://www.pornhub.com/view_video.php?viewkey=XXXX" -q best

# ffmpeg olmadan (HLS → .ts)
python main.py -u "URL" --no-ffmpeg
```

### Sık kullanılan bayraklar

| Bayrak | Açıklama |
| --- | --- |
| `-u, --url` | Tek video URL'si |
| `-b, --batch` | URL listesi (satır başına bir) |
| `-o, --output` | Çıktı klasörü (varsayılan: `./downloads`) |
| `-q, --quality` | `best`, `2160`, `1440`, `1080`, `720`, `480`, `360`, `240` |
| `-f, --format` | Çıktı konteyneri: `mp4` veya `mkv` |
| `-t, --threads` | Eşzamanlı HLS segment iş parçacığı (varsayılan: 16) |
| `-p, --proxy` | Proxy URL veya `proxies.txt` dosyası |
| `-c, --cookies` | `cookies.txt` yolu (Netscape formatı) |
| `-r, --rate-limit` | Maks. hız MB/s (`0` = sınırsız) |
| `--filename-template` | yt-dlp şablonu, örn. `%(uploader)s/%(title)s_%(id)s.%(ext)s` |
| `--no-metadata` | `.info.json` dosyasını atla |
| `--no-thumbnail` | Küçük resmi atla |
| `--no-ffmpeg` | ffmpeg devre dışı (HLS → `.ts`, ses birleştirme yok) |

Tam yardım: `python main.py --help`

---

## ⚙️ Ayarlar (GUI)

| Sekme | Seçenekler |
| --- | --- |
| **Genel** | Çıktı klasörü, kalite, format, tema, dil (TR/EN) |
| **Ağ** | Eşzamanlı indirme, segment iş parçacığı, proxy, zaman aşımı, yeniden deneme, hız limiti |
| **Gelişmiş** | ffmpeg yolu (otomatik bul), çerez dosyası, user-agent, dosya adı şablonu |
| **Hakkında** | Sürüm bilgisi |

**ffmpeg yolu:** Otomatik bulma için boş bırakın. **Otomatik Bul** ile yaygın konumlar taranır. Windows'ta ffmpeg ayrıca `%LOCALAPPDATA%\PHDownloader\bin` klasörüne indirilir.

---

## 📦 Gereksinimler

| Bileşen | Gereksinim |
| --- | --- |
| **Python** | 3.9+ (kaynak / CLI / derleme için) |
| **ffmpeg + ffprobe** | MP4 çıktı ve ses birleştirme için gerekli; Windows'ta otomatik kurulur |
| **İşletim sistemi** | Windows (birincil); Linux/macOS kaynaktan ffmpeg ile çalışabilir |

### Python paketleri

Backend ([`requirements.txt`](requirements.txt)):

```
yt-dlp>=2024.4.9
aiohttp>=3.9.0
requests>=2.31.0
tqdm>=4.66.0
```

GUI için ek olarak PyQt6 gerekir — [`gui/requirements.txt`](gui/requirements.txt) veya `launcher.py` kullanın.

### ffmpeg'i elle kurma (isteğe bağlı)

```bash
# Windows
winget install Gyan.FFmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

---

## 🗂️ Proje yapısı

```
PHDownloader/
├── main.py              # CLI giriş noktası
├── launcher.py          # GUI başlatıcı (paketleri otomatik kurar)
├── build_exe.py         # PyInstaller derleme betiği
├── config.py            # Varsayılanlar, başlıklar, user-agent
├── extractor.py         # yt-dlp çıkarımı + PornHub yedeği
├── downloader.py        # HLS/MP4 indirme, ffmpeg mux, ses birleştirme
├── utils.py             # Yollar, günlük, hız limiti, ffmpeg bulma
├── requirements.txt     # Backend bağımlılıkları
├── LICENSE
├── docs/                # Ekran görüntüleri
└── gui/                 # PyQt6 masaüstü uygulaması
    ├── main.py          # GUI giriş
    ├── main_window.py   # Ana pencere, tepsi, ffmpeg kurulumu
    ├── pages/           # Ana Sayfa, Kuyruk, Geçmiş, Ayarlar
    ├── widgets/         # Kartlar, kenar çubuğu, URL girişi
    ├── core/            # İndirme yöneticisi, iş parçacıkları, SQLite
    ├── utils/           # Ayarlar, i18n, tema, ffmpeg kurulumu
    └── resources/       # İkonlar, stiller
```

GUI, arka plan `QThread` işçileriyle aynı backend'i kullanır. Ayrıntılar için [`gui/README.md`](gui/README.md).

---

## 🔊 Ses ve kalite notları

| Site | Davranış |
| --- | --- |
| **YouTube** | 720p+ genelde yalnızca video; en iyi ses indirilip ffmpeg ile birleştirilir |
| **Twitter / X** | Video ve ses ayrı HLS akışları; özel yt-dlp mux yolu |
| **PornHub** | Genelde birleşik (video + ses tek akışta) |
| **ffmpeg yok** | Düşük birleşik kaliteye veya ses birleştirmesiz `.ts` çıktısına düşer |

İndirme **sessiz** tamamlanırsa:

1. İlk çalıştırmada ffmpeg kurulumunun bitmesini bekleyin
2. **Ayarlar → Gelişmiş** — `Bulundu: …/ffmpeg.exe` yazmalı
3. Sessiz dosyayı silin ve yeniden indirin
4. yt-dlp güncelleyin: `pip install -U yt-dlp`

---

## 🧯 Sorun giderme

| Sorun | Çözüm |
| --- | --- |
| **Ses yok (YouTube / Twitter)** | ffmpeg algılandığından emin olun; eski dosyayı silip yeniden indirin; yt-dlp güncelleyin |
| **Çıktı `.ts`, `.mp4` değil** | ffmpeg eksik — otomatik indirmeyi bekleyin veya elle kurun |
| **`Segment failed (HTTP 403)`** | Ayarlarda segment iş parçacığını düşürün (örn. 4–8); proxy deneyin |
| **Çıkarım başarısız** | `pip install -U yt-dlp`; PH için site değişmiş olabilir |
| **Twitter indirme başarısız** | Bazı tweet'ler çerez gerektirir — tarayıcıdan `cookies.txt` dışa aktarın |
| **Derleme: PermissionError** | `python build_exe.py` öncesi tüm `PHDownloader.exe` süreçlerini kapatın |
| **Günlükler** | Uygulama veri klasöründeki `errors.log` dosyasına bakın |

---

## 🤝 Katkı

Issue ve pull request'ler memnuniyetle karşılanır.

- Değişiklikleri odaklı tutun ve mevcut kod stiline uyun
- Backend'e dokunurken hem GUI (`launcher.py`) hem CLI (`main.py`) test edin
- Backend, özel arayüzler için `progress_hook`, `info_hook` ve `cancel_event` kancaları sunar

---

## 📄 Lisans

[MIT](LICENSE) © CheatGlobal-Hypnass

---

## 🙏 Teşekkürler

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — site çıkarımı
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) — masaüstü arayüzü
- [ffmpeg](https://ffmpeg.org/) — birleştirme, dönüştürme, ses mux
- İkonlar [Feather Icons](https://feathericons.com/) (MIT) esinlenmesiyle

---

<div align="center">

**Bu proje işinize yaradıysa GitHub'da ⭐ vermeyi düşünün.**

[**English documentation →**](README.md)

</div>
