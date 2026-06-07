"""Video information extraction.

Uses yt-dlp for every site it supports (YouTube, Kick, Twitter/X, etc.). When
yt-dlp fails on a PornHub URL, a best-effort custom extractor parses the
``flashvars`` / ``mediaDefinitions`` JSON embedded in the page HTML.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

import config
from utils import get_logger

logger = get_logger()

_EXTRACTORS: Optional[List[object]] = None


class ExtractionError(Exception):
    """Raised when video information cannot be extracted by any method."""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Stream:
    """A single downloadable media stream for one quality level."""

    height: int
    url: str
    protocol: str  # "hls" or "http"
    ext: str = "mp4"
    format_id: str = ""
    has_video: bool = True
    has_audio: bool = True
    tbr: float = 0.0  # total bitrate (kbps); used to break quality ties
    filesize: Optional[int] = None
    audio_url: Optional[str] = None  # set when audio must be merged separately

    @property
    def is_hls(self) -> bool:
        return self.protocol == "hls"


@dataclass
class VideoInfo:
    """Normalised metadata plus the list of available streams for a video."""

    id: str
    title: str
    uploader: str
    duration: int
    upload_date: str
    tags: List[str]
    view_count: int
    thumbnail: str
    webpage_url: str
    streams: List[Stream]
    raw: Dict[str, object] = field(default_factory=dict)

    def template_data(self, ext: str, quality: int) -> Dict[str, object]:
        """Build the substitution dict used by filename templates."""
        from utils import format_duration  # local import avoids a cycle

        return {
            "id": self.id,
            "title": self.title,
            "uploader": self.uploader or "unknown_uploader",
            "ext": ext,
            "quality": f"{quality}p" if quality else "NA",
            "height": quality,
            "upload_date": self.upload_date or "NA",
            "duration": self.duration,
            "duration_string": format_duration(self.duration),
            "view_count": self.view_count,
        }

    def metadata_dict(self) -> Dict[str, object]:
        """Return the dictionary to serialise into the ``.info.json`` sidecar.

        Prefers the rich yt-dlp payload when present; otherwise emits the
        normalised fields gathered by the custom extractor.
        """
        if self.raw:
            return self.raw
        return {
            "id": self.id,
            "title": self.title,
            "uploader": self.uploader,
            "duration": self.duration,
            "upload_date": self.upload_date,
            "tags": self.tags,
            "view_count": self.view_count,
            "thumbnail": self.thumbnail,
            "webpage_url": self.webpage_url,
            "formats": [
                {
                    "format_id": s.format_id,
                    "height": s.height,
                    "protocol": s.protocol,
                    "ext": s.ext,
                    "tbr": s.tbr,
                    "url": s.url,
                }
                for s in self.streams
            ],
        }


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def _ytdlp_extractors() -> List[object]:
    global _EXTRACTORS
    if _EXTRACTORS is None:
        from yt_dlp.extractor import gen_extractors

        _EXTRACTORS = list(gen_extractors())
    return _EXTRACTORS


def _looks_like_http_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _matching_extractors(url: str) -> List[object]:
    return [ie for ie in _ytdlp_extractors() if ie.suitable(url)]


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class Extractor:
    """Resolves a supported video URL into a :class:`VideoInfo`."""

    _FLASHVARS_RE = re.compile(
        r"var\s+flashvars_\d+\s*=\s*(\{.*?\});", re.DOTALL
    )

    def __init__(
        self,
        *,
        proxy: Optional[str] = None,
        cookiefile: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.proxy = proxy
        self.cookiefile = cookiefile
        self.headers = headers

    # -- public API ---------------------------------------------------------

    @classmethod
    def is_supported_url(cls, url: str) -> bool:
        """Return True when yt-dlp recognises ``url`` as downloadable media."""
        url = url.strip()
        if not _looks_like_http_url(url):
            return False
        extractors = _matching_extractors(url)
        if any(ie.IE_NAME != "generic" for ie in extractors):
            return True
        return any(ie.IE_NAME == "generic" for ie in extractors)

    @classmethod
    def extractor_name(cls, url: str) -> Optional[str]:
        """Return the primary yt-dlp extractor id for ``url``, if any."""
        url = url.strip()
        for ie in _matching_extractors(url):
            if ie.IE_NAME != "generic":
                return str(ie.IE_NAME)
        return None

    @staticmethod
    def _is_audio_only_format(fmt: Dict[str, object]) -> bool:
        """Return True when ``fmt`` is a genuine audio-only stream."""
        url = fmt.get("url") or fmt.get("manifest_url")
        if not url:
            return False
        vcodec = str(fmt.get("vcodec") or "none")
        acodec = str(fmt.get("acodec") or "none")
        format_id = str(fmt.get("format_id") or "").lower()
        if vcodec != "none":
            return False
        if acodec != "none":
            return True
        return "audio" in format_id

    def extract_best_audio(
        self, url: str, *, container: str = "mp4"
    ) -> Optional[Dict[str, object]]:
        """Return a fresh best-audio format dict from yt-dlp (resolved URL included)."""
        import yt_dlp

        # Never append ``/best`` — on Twitter that falls back to a video-only stream.
        if config.is_twitter_url(url):
            selectors = [
                "bestaudio[format_id*=Audio]/bestaudio[format_id*=audio]/bestaudio",
            ]
        elif container == "mp4":
            selectors = ["bestaudio[ext=m4a]/bestaudio"]
        else:
            selectors = ["bestaudio"]
        opts = self._ytdlp_options(url)
        for fmt in selectors:
            opts["format"] = fmt
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except Exception as exc:  # noqa: BLE001 - try the next selector
                logger.debug("Audio format %r failed for %s: %s", fmt, url, exc)
                continue
            if info and self._is_audio_only_format(info):
                return dict(info)
        return None

    def extract_info(self, url: str) -> VideoInfo:
        """Extract video info, trying yt-dlp first then a PornHub HTML fallback.

        Args:
            url: A video page or direct media URL supported by yt-dlp.

        Returns:
            A populated :class:`VideoInfo`.

        Raises:
            ExtractionError: If extraction fails for every strategy.
        """
        url = url.strip()
        if not self.is_supported_url(url):
            raise ExtractionError(f"URL is not supported by yt-dlp: {url}")

        try:
            return self._extract_with_ytdlp(url)
        except Exception as exc:  # noqa: BLE001 - we deliberately fall back
            if not config.is_pornhub_url(url):
                raise ExtractionError(f"yt-dlp extraction failed: {exc}") from exc
            logger.warning("yt-dlp extraction failed (%s); trying PornHub fallback.", exc)
            try:
                return self._extract_custom(url)
            except Exception as fallback_exc:  # noqa: BLE001
                raise ExtractionError(
                    f"Both yt-dlp and PornHub fallback failed: "
                    f"yt-dlp={exc}; fallback={fallback_exc}"
                ) from fallback_exc

    # -- yt-dlp path --------------------------------------------------------

    def _headers_for_url(self, url: str) -> Dict[str, str]:
        if self.headers is not None:
            return dict(self.headers)
        if config.is_pornhub_url(url):
            return config.base_headers()
        return config.default_headers()

    def _ytdlp_options(self, url: str) -> Dict[str, object]:
        opts: Dict[str, object] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "http_headers": self._headers_for_url(url),
        }
        if self.proxy:
            opts["proxy"] = self.proxy
        if self.cookiefile:
            opts["cookiefile"] = self.cookiefile
        return opts

    def _extract_with_ytdlp(self, url: str) -> VideoInfo:
        import yt_dlp  # imported lazily so a missing dep degrades gracefully

        with yt_dlp.YoutubeDL(self._ytdlp_options(url)) as ydl:
            info = ydl.extract_info(url, download=False)

        if info is None:
            raise ExtractionError("yt-dlp returned no information.")
        if info.get("_type") == "playlist":
            entries = [e for e in info.get("entries", []) if e]
            if not entries:
                raise ExtractionError("Playlist contained no entries.")
            info = entries[0]

        streams = self._streams_from_ytdlp(info.get("formats") or [])
        if not streams:
            raise ExtractionError("yt-dlp found no usable video streams.")

        return VideoInfo(
            id=str(info.get("id") or "unknown"),
            title=str(info.get("title") or "untitled"),
            uploader=str(
                info.get("uploader")
                or info.get("channel")
                or info.get("uploader_id")
                or "unknown_uploader"
            ),
            duration=int(info.get("duration") or 0),
            upload_date=str(info.get("upload_date") or ""),
            tags=list(info.get("tags") or info.get("categories") or []),
            view_count=int(info.get("view_count") or 0),
            thumbnail=str(info.get("thumbnail") or ""),
            webpage_url=str(info.get("webpage_url") or url),
            streams=streams,
            raw=info,
        )

    @staticmethod
    def _format_height(fmt: Dict[str, object]) -> int:
        height = int(fmt.get("height") or 0)
        if height > 0:
            return height
        width = int(fmt.get("width") or 0)
        if width > 0:
            return width
        resolution = str(fmt.get("resolution") or "")
        match = re.search(r"(\d+)", resolution)
        if match:
            return int(match.group(1))
        return 480

    @staticmethod
    def _streams_from_ytdlp(formats: List[Dict[str, object]]) -> List[Stream]:
        streams: List[Stream] = []
        for fmt in formats:
            vcodec = str(fmt.get("vcodec") or "none")
            acodec = str(fmt.get("acodec") or "none")
            has_video = vcodec != "none"
            has_audio = acodec != "none"
            if not has_video:
                continue
            height = Extractor._format_height(fmt)
            proto = str(fmt.get("protocol") or "")
            is_hls = "m3u8" in proto or str(fmt.get("ext")) == "m3u8"
            url = str(fmt.get("url") or "")
            if not url:
                continue
            streams.append(
                Stream(
                    height=height,
                    url=url,
                    protocol="hls" if is_hls else "http",
                    ext="mp4" if is_hls else str(fmt.get("ext") or "mp4"),
                    format_id=str(fmt.get("format_id") or ""),
                    has_video=True,
                    has_audio=has_audio,
                    tbr=float(fmt.get("tbr") or 0.0),
                    filesize=fmt.get("filesize") or fmt.get("filesize_approx"),  # type: ignore[arg-type]
                )
            )
        return streams

    # -- PornHub HTML fallback ---------------------------------------------

    def _extract_custom(self, url: str) -> VideoInfo:
        """Parse ``flashvars`` from the page HTML when yt-dlp is unavailable."""
        if not config.is_pornhub_url(url):
            raise ExtractionError(f"PornHub fallback not applicable for: {url}")

        headers = self._headers_for_url(url)
        html = self._fetch_html(url, headers)
        flashvars = self._parse_flashvars(html)

        video_id = self._extract_video_id(url, html)
        title = str(
            flashvars.get("video_title") or self._og(html, "title") or "untitled"
        )
        thumbnail = str(
            flashvars.get("image_url") or self._og(html, "image") or ""
        )
        duration = int(flashvars.get("video_duration") or 0)
        uploader = self._extract_uploader(html)

        streams = self._streams_from_flashvars(flashvars, headers)
        if not streams:
            raise ExtractionError("No media definitions found in page HTML.")

        return VideoInfo(
            id=video_id,
            title=title,
            uploader=uploader,
            duration=duration,
            upload_date="",
            tags=self._extract_tags(html),
            view_count=self._extract_view_count(html),
            thumbnail=thumbnail,
            webpage_url=url,
            streams=streams,
            raw={},
        )

    def _fetch_html(self, url: str, headers: Dict[str, str]) -> str:
        resp = requests.get(
            url,
            headers=headers,
            proxies=self._requests_proxies(),
            timeout=(config.CONNECT_TIMEOUT, config.READ_TIMEOUT),
        )
        resp.raise_for_status()
        return resp.text

    def _requests_proxies(self) -> Optional[Dict[str, str]]:
        if not self.proxy:
            return None
        return {"http": self.proxy, "https": self.proxy}

    def _parse_flashvars(self, html: str) -> Dict[str, object]:
        match = self._FLASHVARS_RE.search(html)
        if not match:
            raise ExtractionError("Could not locate flashvars in page HTML.")
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ExtractionError(f"flashvars JSON was malformed: {exc}") from exc

    def _streams_from_flashvars(
        self,
        flashvars: Dict[str, object],
        headers: Dict[str, str],
    ) -> List[Stream]:
        media_definitions = flashvars.get("mediaDefinitions")
        if not isinstance(media_definitions, list):
            return []

        resolved: List[Dict[str, object]] = []
        for entry in media_definitions:
            if not isinstance(entry, dict):
                continue
            video_url = str(entry.get("videoUrl") or "")
            quality = entry.get("quality")
            if isinstance(quality, list) and video_url and "get_media" in video_url:
                resolved.extend(self._resolve_get_media(video_url, headers))
            elif video_url:
                resolved.append(entry)

        streams: List[Stream] = []
        for entry in resolved:
            video_url = str(entry.get("videoUrl") or "")
            if not video_url:
                continue
            fmt = str(entry.get("format") or "").lower()
            quality = entry.get("quality")
            if isinstance(quality, list):
                height = max((int(q) for q in quality if str(q).isdigit()), default=0)
            else:
                height = int(quality) if str(quality).isdigit() else 0
            is_hls = fmt == "hls" or video_url.endswith(".m3u8")
            streams.append(
                Stream(
                    height=height,
                    url=video_url,
                    protocol="hls" if is_hls else "http",
                    ext="mp4" if is_hls else "mp4",
                    format_id=f"{fmt or 'http'}-{height}",
                    has_video=True,
                    has_audio=True,
                )
            )
        return [s for s in streams if s.height > 0]

    def _resolve_get_media(
        self, url: str, headers: Dict[str, str]
    ) -> List[Dict[str, object]]:
        try:
            resp = requests.get(
                url,
                headers=headers,
                proxies=self._requests_proxies(),
                timeout=(config.CONNECT_TIMEOUT, config.READ_TIMEOUT),
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, json.JSONDecodeError) as exc:
            logger.debug("get_media resolution failed: %s", exc)
            return []
        return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []

    # -- HTML scraping helpers ---------------------------------------------

    @staticmethod
    def _og(html: str, prop: str) -> Optional[str]:
        match = re.search(
            rf'<meta\s+property=["\']og:{prop}["\']\s+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        return match.group(1) if match else None

    @staticmethod
    def _extract_video_id(url: str, html: str) -> str:
        query = urlparse(url).query
        match = re.search(r"viewkey=([0-9a-zA-Z]+)", query)
        if match:
            return match.group(1)
        match = re.search(r'"video_id"\s*:\s*"?(\d+)"?', html)
        return match.group(1) if match else "unknown"

    @staticmethod
    def _extract_uploader(html: str) -> str:
        for pattern in (
            r'<meta\s+property=["\']og:author["\']\s+content=["\']([^"\']+)["\']',
            r'"author"\s*:\s*\{[^}]*"name"\s*:\s*"([^"]+)"',
            r'class="usernameBadgesWrapper"[^>]*>\s*<a[^>]*>([^<]+)</a>',
        ):
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return "unknown_uploader"

    @staticmethod
    def _extract_tags(html: str) -> List[str]:
        tags = re.findall(r'data-label="Tag"[^>]*>\s*([^<]+?)\s*<', html)
        return [t.strip() for t in tags if t.strip()]

    @staticmethod
    def _extract_view_count(html: str) -> int:
        match = re.search(r'"interactionCount"\s*:\s*"?(\d+)"?', html)
        return int(match.group(1)) if match else 0


# ---------------------------------------------------------------------------
# Stream selection
# ---------------------------------------------------------------------------

def select_stream(
    streams: List[Stream],
    quality: str,
    *,
    require_audio: bool = False,
) -> Stream:
    """Choose the stream matching the requested quality.

    Args:
        streams: Candidate streams (one or more per height).
        quality: ``"best"`` or a target height string (e.g. ``"1080"``).
        require_audio: When True, only consider streams with embedded audio
            (used when ffmpeg is unavailable for a separate audio merge).

    Returns:
        The selected :class:`Stream`.

    Raises:
        ExtractionError: If ``streams`` is empty or no suitable stream exists.
    """
    if not streams:
        raise ExtractionError("No streams available to choose from.")

    if require_audio:
        streams = [s for s in streams if s.has_audio]
        if not streams:
            raise ExtractionError(
                "No muxed (video+audio) stream is available. Install ffmpeg "
                "to download high-quality video-only formats with separate audio."
            )

    best_by_height: Dict[int, Stream] = {}
    for stream in streams:
        existing = best_by_height.get(stream.height)
        if existing is None:
            best_by_height[stream.height] = stream
            continue
        if stream.has_audio and not existing.has_audio:
            best_by_height[stream.height] = stream
        elif stream.has_audio == existing.has_audio and stream.tbr > existing.tbr:
            best_by_height[stream.height] = stream

    available_heights = sorted(best_by_height, reverse=True)

    if quality == "best":
        chosen = available_heights[0]
    else:
        target = int(quality)
        if target in best_by_height:
            chosen = target
        else:
            lower = [h for h in available_heights if h <= target]
            chosen = lower[0] if lower else available_heights[-1]
            logger.warning(
                "Requested %sp unavailable; using %sp instead.", target, chosen
            )

    return best_by_height[chosen]
