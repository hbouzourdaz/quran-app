from __future__ import annotations

from pathlib import Path

from kivy.core.text import LabelBase


FONT_NAME = "Rubik"
FONT_PATH = Path(__file__).resolve().parents[1] / "assets" / "fonts" / "Rubik-Regular.ttf"


def register_rubik() -> str:
    if FONT_PATH.exists():
        LabelBase.register(name=FONT_NAME, fn_regular=str(FONT_PATH))
    return FONT_NAME


def apply_rubik_to_theme(theme_cls) -> None:
    register_rubik()
    for style, values in theme_cls.font_styles.items():
        if style == "Icon":
            continue
        values[0] = FONT_NAME
        values[2] = False
        values[3] = 0

