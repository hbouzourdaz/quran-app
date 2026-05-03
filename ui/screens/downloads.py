from __future__ import annotations

import time

from kivy.metrics import dp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView

from i18n import status_label
from services import open_path


class DownloadsScreen(MDScreen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self._build()

    def _build(self) -> None:
        root = MDBoxLayout(orientation="vertical", padding=(dp(20), dp(24), dp(20), dp(20)), spacing=dp(20))
        controls = MDBoxLayout(adaptive_height=True, spacing=dp(10))
        self.refresh_button = MDFillRoundFlatIconButton(
            text="",
            icon="refresh",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.refresh(),
        )
        self.clear_button = MDFlatButton(text="", size_hint_x=1, on_release=lambda *_: self.clear_history())
        controls.add_widget(self.refresh_button)
        controls.add_widget(self.clear_button)
        root.add_widget(controls)

        self.scroll = MDScrollView()
        self.list_box = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            spacing=dp(16),
            padding=(0, 0, 0, dp(32)),
        )
        self.scroll.add_widget(self.list_box)
        root.add_widget(self.scroll)
        self.add_widget(root)
        self.update_texts()

    def update_texts(self) -> None:
        self.refresh_button.text = self.app.tr("refresh")
        self.clear_button.text = self.app.tr("clear")
        self.refresh()

    def refresh(self) -> None:
        self.list_box.clear_widgets()
        history = list(reversed(self.app.history_store.all()))
        if not history:
            self.list_box.add_widget(
                MDLabel(
                    text=self.app.tr("history_empty"),
                    halign="center",
                    theme_text_color="Secondary",
                    adaptive_height=True,
                )
            )
            return

        for item in history:
            self.list_box.add_widget(self._history_card(item))

    def _history_card(self, item) -> MDCard:
        status = status_label(self.app.language, item.get("status", "unknown"))
        progress = item.get("progress", 0)
        created = time.strftime("%Y-%m-%d %H:%M", time.localtime(item.get("created_at", time.time())))
        path = item.get("path") or item.get("output_dir") or ""
        quality = self.app.quality_label(item.get("quality", ""))

        card = MDCard(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(20),
            spacing=dp(14),
            radius=[dp(16)],
            elevation=1,
            line_color=(0, 0, 0, 0.08),
        )
        card.add_widget(
            MDLabel(
                text=item.get("title") or self.app.tr("untitled"),
                font_style="Subtitle1",
                bold=True,
                theme_text_color="Primary",
                halign=self.app.text_align,
                adaptive_height=True,
            )
        )
        card.add_widget(
            MDLabel(
                text=f"{item.get('platform', 'Unknown')} | {quality} | {created}",
                font_style="Caption",
                theme_text_color="Secondary",
                halign=self.app.text_align,
                adaptive_height=True,
            )
        )
        card.add_widget(
            MDLabel(
                text=f"{status} | {progress}%",
                font_style="Caption",
                theme_text_color="Secondary",
                halign=self.app.text_align,
                adaptive_height=True,
            )
        )
        if item.get("error"):
            card.add_widget(
                MDLabel(
                    text=item["error"],
                    font_style="Caption",
                    theme_text_color="Error",
                    halign=self.app.text_align,
                    adaptive_height=True,
                )
            )

        actions = MDBoxLayout(adaptive_height=True, spacing=dp(8))
        actions.add_widget(MDFlatButton(text=self.app.tr("open_folder"), on_release=lambda *_: self.open_item(path)))
        card.add_widget(actions)
        return card

    def open_item(self, path: str) -> None:
        if not path:
            toast(self.app.tr("no_path"))
            return
        try:
            open_path(path)
        except Exception as exc:
            toast(self.app.tr("open_folder_failed", error=exc))

    def clear_history(self) -> None:
        self.app.history_store.clear()
        self.refresh()

