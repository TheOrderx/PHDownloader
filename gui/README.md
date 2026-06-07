# PHDownloader — GUI

A modern, dark-themed **PyQt6** desktop front-end for the `phvid` downloader
backend. Frameless window, accent-orange theme, background download threads,
live progress cards, searchable history, and a full settings panel.

> **Legal note:** Only download content you are authorised to download. Respect
> the source site's Terms of Service and your local laws. For lawful personal use.

---

## Screenshots

> _Add screenshots here once you run the app._

| Home | Queue | History | Settings |
| --- | --- | --- | --- |
| `docs/home.png` | `docs/queue.png` | `docs/history.png` | `docs/settings.png` |

---

## Features

- **Frameless custom window** — draggable title bar, min/maximise/close, double-click
  to maximise, edge-resize, soft drop shadow, rounded corners.
- **Dark / light themes** with an animated toggle (accent `#ff9000`, charcoal `#1a1a1a`).
- **Sidebar navigation** with active-item accent border and recolouring SVG icons.
- **Home page** — URL input + paste button, "Add to Queue", drag-&-drop `.txt`
  batch import, quality/format/output controls, thumbnail/metadata toggles, and a
  concurrent-downloads slider.
- **Queue page** — live cards (thumbnail, title, uploader/duration/quality,
  gradient progress bar with `% • speed • ETA`, status badge) and per-item
  Pause/Resume, Cancel, Open-folder actions, plus Pause/Resume/Clear bulk tools.
- **History page** — sortable `QTableWidget` backed by **SQLite** (`history.db`),
  search box, and a right-click menu (Re-download, Open file, Open folder, Copy
  URL, Remove).
- **Settings page** — tabbed (General / Network / Advanced / About), persisted via
  `QSettings`.
- **System tray** icon (Show/Hide, Pause All, Quit) + desktop notifications on
  completion. Minimises to tray on close (configurable).
- **Hotkeys** — `Ctrl+N` new download, `Ctrl+V` paste URL, `Space` pause/resume
  selected card, `Delete` cancel selected, `Ctrl+Q` quit.
- **Never blocks the UI** — each download runs in its own `QThread`; progress,
  metadata and cancellation flow back through Qt signals.

## Requirements

- **Python 3.9+**
- **PyQt6** (see `requirements.txt`)
- The **phvid backend** (the `config.py`, `downloader.py`, `extractor.py`,
  `utils.py` modules in the parent directory — already present in this repo)
- **ffmpeg / ffprobe** on `PATH` for clean `.mp4` / `.mkv` output. If ffmpeg is
  missing the app automatically falls back to a lossless `.ts` byte-merge for
  HLS (plays in VLC/MPV); encrypted HLS then needs ffmpeg.

## Quick start (auto-installs everything)

From the project root just run the launcher — it installs any missing Python
packages on first run, then starts the app. **ffmpeg is downloaded
automatically** in the background on first launch (Windows); until it finishes,
HLS downloads fall back to a lossless `.ts`.

```bash
python launcher.py
```

### Manual install (alternative)

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r gui/requirements.txt
python -m gui.main      # or: python gui/main.py
```

ffmpeg is auto-installed on Windows. To install it yourself instead:

| Platform | Command |
| --- | --- |
| Windows | `winget install Gyan.FFmpeg` (or let the app fetch it) |
| macOS | `brew install ffmpeg` |
| Debian/Ubuntu | `sudo apt install ffmpeg` |

## Build a standalone .exe (Windows)

```bash
python build_exe.py            # -> dist/PHDownloader.exe   (single file, default)
python build_exe.py --onedir   # -> dist/PHDownloader/...   (one folder, faster start)
```

PyInstaller is installed automatically if missing. The built app bundles Python
and all packages; ffmpeg is still fetched on first run (kept out of the bundle to
keep it small). Double-click `PHDownloader.exe` to run — no Python required.

## Usage

1. **Home** → paste a PornHub URL (or click the clipboard button) and press
   **Add to Queue** (or `Enter`). Or drag a `.txt` file of URLs onto the drop zone.
2. Pick **Quality / Format / Output folder** and the **concurrent downloads**
   count before adding.
3. **Queue** → watch progress; pause/resume/cancel individual items or use the
   bulk toolbar. Completed items show an **Open folder** button.
4. **History** → search past downloads; right-click for actions.
5. **Settings** → defaults, proxy (HTTP/SOCKS5), timeouts/retries/rate-limit,
   ffmpeg path, cookies file, custom user-agent, filename template, theme.

## Architecture

```
gui/
├── main.py                 # QApplication setup + entry point
├── main_window.py          # frameless window, nav, tray, hotkeys, resize, theme
├── widgets/
│   ├── title_bar.py        # custom title bar (drag + window controls)
│   ├── sidebar.py          # navigation + theme toggle
│   ├── download_card.py    # one live download card
│   ├── url_input.py        # URL field + paste button
│   └── custom_widgets.py   # themed SVG icons, buttons, toggle, badges, shadow
├── pages/
│   ├── home_page.py        # input + options + batch import
│   ├── queue_page.py       # live cards + bulk actions + empty state
│   ├── history_page.py     # SQLite-backed sortable table + context menu
│   └── settings_page.py    # tabbed settings (General/Network/Advanced/About)
├── core/
│   ├── download_manager.py # queue, concurrency, signal relay, history writes
│   ├── worker.py           # QThread that drives the phvid backend
│   └── database.py         # SQLite history store
├── resources/
│   ├── icons/              # Feather-style SVGs (recoloured per theme)
│   └── styles.qss          # full stylesheet (themed via @token@ substitution)
└── utils/
    ├── settings.py         # typed QSettings wrapper
    ├── theme.py            # palettes, QSS builder, ThemeManager singleton
    └── notifications.py    # tray / plyer desktop notifications
```

### Backend integration

The GUI imports the existing backend `Downloader` and drives it inside a
`DownloadWorker(QThread)`. The backend exposes three optional, fully
backward-compatible hooks (unused by the CLI):

- `progress_hook(dict)` — `{stage, downloaded, total, speed, eta, frac}`, ~10 Hz.
- `info_hook(info, stream, path)` — fired once after extraction (title, uploader,
  thumbnail path, output path).
- `cancel_event` (`threading.Event`) + `show_progress_bar=False` — cooperative
  pause/cancel and silencing the console progress bar.

**Pause** stops the worker but keeps the partial file / HLS segments, so
**Resume** continues via the backend's existing resume logic. **Cancel** removes
the item and deletes partials.

## Notes

- Settings, window geometry and last page are stored via `QSettings`; history in
  `history.db` under the app data directory.
- `embed subtitles` is shown but disabled — the source does not provide subtitles.
