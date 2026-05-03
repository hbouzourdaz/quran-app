from __future__ import annotations

import json
import os
import re
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


APP_NAME = "Hakim Downloader"
QUALITY_CHOICES = ("360p", "720p", "1080p", "Audio only")
DEFAULT_QUALITY = "720p"
DEFAULT_LANGUAGE = "ar"


def default_download_dir() -> str:
    """Return a writable default download directory for desktop or Android."""
    try:
        from kivy.utils import platform
    except Exception:
        platform = ""

    if platform == "android":
        try:
            from android.storage import primary_external_storage_path

            return str(Path(primary_external_storage_path()) / "Download" / APP_NAME)
        except Exception:
            pass

    downloads = Path.home() / "Downloads"
    if downloads.exists():
        return str(downloads / APP_NAME)
    return str(Path.home() / APP_NAME)


def ensure_directory(path: str) -> str:
    target = Path(os.path.expanduser(path)).resolve()
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def format_duration(seconds: Optional[float]) -> str:
    if seconds is None:
        return "--:--"
    try:
        total = int(seconds)
    except (TypeError, ValueError):
        return "--:--"
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"


def bytes_to_human(value: Optional[float]) -> str:
    if not value:
        return "0 B"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def speed_to_human(value: Optional[float]) -> str:
    if not value:
        return "0 B/s"
    return f"{bytes_to_human(value)}/s"


def is_probable_url(text: str) -> bool:
    if not text:
        return False
    candidate = text.strip()
    return bool(re.match(r"^https?://[^\s]+$", candidate, re.IGNORECASE))


class JsonStore:
    """Small atomic JSON store used for settings and history."""

    def __init__(self, path: str, default: Any):
        self.path = Path(path)
        self.default = default
        self._lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> Any:
        with self._lock:
            if not self.path.exists():
                return self._copy_default()
            try:
                with self.path.open("r", encoding="utf-8") as handle:
                    return json.load(handle)
            except (json.JSONDecodeError, OSError):
                return self._copy_default()

    def write(self, data: Any) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            temporary.replace(self.path)

    def _copy_default(self) -> Any:
        return json.loads(json.dumps(self.default))


class SettingsStore:
    DEFAULTS: Dict[str, Any] = {
        "download_dir": default_download_dir(),
        "quality": DEFAULT_QUALITY,
        "audio_only": False,
        "theme_style": "Dark",
        "language": DEFAULT_LANGUAGE,
        "clipboard_autofill": True,
        "notifications": True,
        "ffmpeg_location": "",
    }

    def __init__(self, user_data_dir: str):
        self._store = JsonStore(str(Path(user_data_dir) / "settings.json"), self.DEFAULTS)

    def get_all(self) -> Dict[str, Any]:
        data = self.DEFAULTS.copy()
        loaded = self._store.read()
        if isinstance(loaded, dict):
            data.update(loaded)
        return data

    def get(self, key: str, default: Any = None) -> Any:
        return self.get_all().get(key, default)

    def set(self, key: str, value: Any) -> None:
        data = self.get_all()
        data[key] = value
        self._store.write(data)

    def update(self, **values: Any) -> None:
        data = self.get_all()
        data.update(values)
        self._store.write(data)


class HistoryStore:
    def __init__(self, user_data_dir: str):
        self._store = JsonStore(str(Path(user_data_dir) / "history.json"), [])

    def all(self) -> List[Dict[str, Any]]:
        data = self._store.read()
        return data if isinstance(data, list) else []

    def add(self, entry: Dict[str, Any]) -> None:
        data = self.all()
        entry.setdefault("created_at", time.time())
        data.append(entry)
        self._store.write(data[-100:])

    def update(self, item_id: str, **values: Any) -> None:
        data = self.all()
        for item in data:
            if item.get("id") == item_id:
                item.update(values)
                item["updated_at"] = time.time()
                break
        self._store.write(data)

    def clear(self) -> None:
        self._store.write([])
