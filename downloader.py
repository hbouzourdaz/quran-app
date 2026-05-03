from __future__ import annotations

import os
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError as YTDLPDownloadError

from app_config import QUALITY_CHOICES, ensure_directory


ProgressCallback = Callable[[Dict[str, Any]], None]


class DownloadError(RuntimeError):
    """User-facing download error with noisy yt-dlp details removed."""


class SilentLogger:
    """Redirects yt-dlp logs to nowhere to avoid console/write errors."""

    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


@dataclass
class FormatOption:
    label: str
    selector: str
    height: Optional[int] = None
    ext: str = "mp4"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VideoMetadata:
    url: str
    webpage_url: str
    title: str
    duration: Optional[float]
    thumbnail: str
    platform: str
    uploader: str
    formats: List[FormatOption]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["formats"] = [item.to_dict() for item in self.formats]
        return data


@dataclass
class DownloadRequest:
    url: str
    output_dir: str
    quality: str = "720p"
    audio_only: bool = False


class PlatformDetector:
    PATTERNS = {
        "YouTube": r"(youtube\.com|youtu\.be|music\.youtube\.com)",
        "Facebook": r"(facebook\.com|fb\.watch)",
        "Instagram": r"(instagram\.com)",
        "Twitter/X": r"(twitter\.com|x\.com)",
        "TikTok": r"(tiktok\.com|vm\.tiktok\.com)",
    }

    @classmethod
    def detect(cls, url: str, extractor_key: str = "") -> str:
        haystack = f"{url} {extractor_key}".lower()
        for name, pattern in cls.PATTERNS.items():
            if re.search(pattern, haystack):
                return name
        return extractor_key or "Unknown"


class YTDLPDownloader:
    """Thin, testable wrapper around yt-dlp for metadata and downloads."""

    QUALITY_SELECTORS = {
        "360p": "best[height<=360]/bestvideo[height<=360]+bestaudio/best",
        "720p": "best[height<=720]/bestvideo[height<=720]+bestaudio/best",
        "1080p": "best[height<=1080]/bestvideo[height<=1080]+bestaudio/best",
        "Audio only": "bestaudio/best",
    }

    def __init__(self, ffmpeg_location: str = ""):
        self.ffmpeg_location = ffmpeg_location.strip()

    def set_ffmpeg_location(self, ffmpeg_location: str) -> None:
        self.ffmpeg_location = ffmpeg_location.strip()

    def fetch_metadata(self, url: str) -> VideoMetadata:
        if not self._valid_url(url):
            raise DownloadError("Enter a valid http or https video URL.")

        options = self._base_options()
        options.update(
            {
                "extract_flat": False,
                "noplaylist": True,
                "skip_download": True,
                "socket_timeout": 20,
            }
        )

        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=False)
        except YTDLPDownloadError as exc:
            raise DownloadError(self._clean_error(str(exc))) from exc
        except Exception as exc:
            raise DownloadError(f"Could not fetch metadata: {exc}") from exc

        info = self._first_entry(info)
        title = info.get("title") or "Untitled video"
        webpage_url = info.get("webpage_url") or url
        extractor_key = info.get("extractor_key") or info.get("extractor") or ""

        return VideoMetadata(
            url=url,
            webpage_url=webpage_url,
            title=title,
            duration=info.get("duration"),
            thumbnail=self._best_thumbnail(info),
            platform=PlatformDetector.detect(webpage_url, extractor_key),
            uploader=info.get("uploader") or info.get("channel") or "",
            formats=self._extract_format_options(info),
        )

    def download(
        self,
        request: DownloadRequest,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> str:
        if not self._valid_url(request.url):
            raise DownloadError("Enter a valid http or https video URL.")

        output_dir = ensure_directory(request.output_dir)
        audio_only = request.audio_only or request.quality == "Audio only"
        selector = self.QUALITY_SELECTORS.get(request.quality, self.QUALITY_SELECTORS["720p"])
        if audio_only:
            selector = self.QUALITY_SELECTORS["Audio only"]

        options = self._base_options()
        options.update(
            {
                "format": selector,
                "outtmpl": os.path.join(output_dir, "%(title).180B [%(id)s].%(ext)s"),
                "continuedl": True,
                "retries": 10,
                "fragment_retries": 10,
                "concurrent_fragment_downloads": 4,
                "merge_output_format": "mp4",
                "noplaylist": True,
                "windowsfilenames": True,
                "trim_file_name": 180,
                "progress_hooks": [self._progress_hook(progress_callback)],
                "postprocessor_hooks": [self._postprocessor_hook(progress_callback)],
            }
        )

        if audio_only:
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(request.url, download=True)
                final_path = self._resolve_final_path(ydl, info, output_dir, audio_only)
        except YTDLPDownloadError as exc:
            raise DownloadError(self._clean_error(str(exc))) from exc
        except Exception as exc:
            raise DownloadError(f"Download failed: {exc}") from exc

        if progress_callback:
            progress_callback(
                {
                    "status": "complete",
                    "percent": 100.0,
                    "downloaded_bytes": None,
                    "total_bytes": None,
                    "speed": None,
                    "eta": None,
                    "message": "Complete",
                    "filename": final_path,
                }
            )
        return final_path

    def _base_options(self) -> Dict[str, Any]:
        options: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "restrictfilenames": False,
            "cachedir": False,
            "logger": SilentLogger(),
            "encoding": "utf-8",
        }
        if self.ffmpeg_location:
            options["ffmpeg_location"] = self.ffmpeg_location
        else:
            # Auto-detect if ffmpeg.exe is in the current directory or bin/
            for path in [Path("ffmpeg.exe"), Path("bin/ffmpeg.exe")]:
                if path.exists():
                    options["ffmpeg_location"] = str(path.resolve())
                    break
        return options

    def _extract_format_options(self, info: Dict[str, Any]) -> List[FormatOption]:
        options: List[FormatOption] = []
        for label, height in (("360p", 360), ("720p", 720), ("1080p", 1080)):
            options.append(
                FormatOption(
                    label=label,
                    height=height,
                    selector=self.QUALITY_SELECTORS[label],
                    note="Best available up to this quality",
                )
            )

        options.append(
            FormatOption(
                label="Audio only",
                selector=self.QUALITY_SELECTORS["Audio only"],
                ext="mp3",
                note="Extract MP3 with ffmpeg",
            )
        )
        return options

    def _progress_hook(self, callback: Optional[ProgressCallback]) -> Callable[[Dict[str, Any]], None]:
        def hook(data: Dict[str, Any]) -> None:
            if not callback:
                return
            status = data.get("status", "")
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            downloaded = data.get("downloaded_bytes") or 0
            percent = (downloaded / total * 100.0) if total else 0.0
            if status == "finished":
                percent = 100.0

            callback(
                {
                    "status": status,
                    "percent": max(0.0, min(100.0, percent)),
                    "downloaded_bytes": downloaded,
                    "total_bytes": total,
                    "speed": data.get("speed"),
                    "eta": data.get("eta"),
                    "message": "Processing media" if status == "finished" else "Downloading",
                    "filename": data.get("filename"),
                }
            )

        return hook

    def _postprocessor_hook(self, callback: Optional[ProgressCallback]) -> Callable[[Dict[str, Any]], None]:
        def hook(data: Dict[str, Any]) -> None:
            if not callback:
                return
            status = data.get("status", "")
            callback(
                {
                    "status": f"postprocess:{status}",
                    "percent": 100.0,
                    "downloaded_bytes": None,
                    "total_bytes": None,
                    "speed": None,
                    "eta": None,
                    "message": "Finalizing file" if status != "finished" else "Finalized",
                    "filename": data.get("info_dict", {}).get("filepath"),
                }
            )

        return hook

    def _resolve_final_path(
        self,
        ydl: YoutubeDL,
        info: Dict[str, Any],
        output_dir: str,
        audio_only: bool,
    ) -> str:
        info = self._first_entry(info)
        candidates: List[str] = []

        for item in info.get("requested_downloads") or []:
            for key in ("filepath", "_filename", "filename"):
                if item.get(key):
                    candidates.append(item[key])

        for key in ("filepath", "_filename", "filename"):
            if info.get(key):
                candidates.append(info[key])

        try:
            prepared = ydl.prepare_filename(info)
            candidates.append(prepared)
            if audio_only:
                candidates.append(str(Path(prepared).with_suffix(".mp3")))
            else:
                candidates.append(str(Path(prepared).with_suffix(".mp4")))
        except Exception:
            pass

        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return str(Path(candidate).resolve())

        files = sorted(Path(output_dir).glob("*"), key=lambda item: item.stat().st_mtime, reverse=True)
        for file_path in files:
            if file_path.is_file() and not file_path.name.endswith((".part", ".ytdl")):
                return str(file_path.resolve())
        return str(Path(output_dir).resolve())

    @staticmethod
    def _valid_url(url: str) -> bool:
        return bool(re.match(r"^https?://[^\s]+$", (url or "").strip(), re.IGNORECASE))

    @staticmethod
    def _first_entry(info: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(info, dict) and info.get("_type") == "playlist" and info.get("entries"):
            for entry in info["entries"]:
                if entry:
                    return entry
        return info or {}

    @staticmethod
    def _best_thumbnail(info: Dict[str, Any]) -> str:
        thumbnails = info.get("thumbnails") or []
        if thumbnails:
            best = sorted(thumbnails, key=lambda item: item.get("height") or 0)[-1]
            return best.get("url") or ""
        return info.get("thumbnail") or ""

    @staticmethod
    def _clean_error(message: str) -> str:
        cleaned = re.sub(r"\x1b\[[0-9;]*m", "", message)
        cleaned = cleaned.replace("ERROR:", "").strip()
        if "Unsupported URL" in cleaned:
            return "This URL is not supported by yt-dlp."
        if "Private video" in cleaned or "login" in cleaned.lower():
            return "This video is private, restricted, or requires login."
        if "ffmpeg" in cleaned.lower() and "not found" in cleaned.lower():
            return "FFmpeg is required but not found. Please install it or set the path in Settings."
        if "HTTP Error" in cleaned or "timed out" in cleaned.lower():
            return "Network error while contacting the platform. Try again later."
        return cleaned or "The platform rejected the request."
