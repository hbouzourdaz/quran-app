from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def notify_user(title: str, message: str) -> None:
    """Show a native notification when plyer is available."""
    try:
        from plyer import notification

        notification.notify(title=title, message=message, timeout=5)
    except Exception:
        pass


def open_path(path: str) -> None:
    target = Path(path)
    if target.is_file():
        target = target.parent
    if not target.exists():
        return

    if sys.platform.startswith("win"):
        os.startfile(str(target))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])

def play_file(path: str) -> None:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return

    if sys.platform.startswith("win"):
        os.startfile(str(target))
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])
