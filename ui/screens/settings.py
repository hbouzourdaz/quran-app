from __future__ import annotations

from pathlib import Path

from kivy.metrics import dp
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton, MDFlatButton
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField

from app_config import QUALITY_CHOICES, ensure_directory
from i18n import LANGUAGE_LABELS


class SettingsScreen(MDScreen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.quality_menu = None
        self.language_menu = None
        self.file_manager = None
        self.switch_labels = {}
        self._refreshing = False
        self._build()

    def _build(self) -> None:
        scroll = MDScrollView()
        self.content = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            padding=(dp(20), dp(24), dp(20), dp(32)),
            spacing=dp(20),
        )
        scroll.add_widget(self.content)
        self.add_widget(scroll)

        self.path_input = MDTextField(
            hint_text="",
            mode="round",
            icon_left="folder-download-outline",
            font_name="Rubik",
            halign=self.app.text_align,
            multiline=False,
            size_hint_y=None,
            height=dp(64),
        )
        self.content.add_widget(self.path_input)

        path_row = MDBoxLayout(adaptive_height=True, spacing=dp(10))
        self.browse_button = MDFillRoundFlatIconButton(
            text="",
            icon="folder-open-outline",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.open_file_manager(),
        )
        self.save_path_button = MDFlatButton(text="", size_hint_x=1, on_release=lambda *_: self.save_path())
        path_row.add_widget(self.browse_button)
        path_row.add_widget(self.save_path_button)
        self.content.add_widget(path_row)

        self.quality_button = MDFillRoundFlatIconButton(
            text="",
            icon="tune",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.open_quality_menu(),
        )
        self.content.add_widget(self.quality_button)

        self.language_button = MDFillRoundFlatIconButton(
            text="",
            icon="translate",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.open_language_menu(),
        )
        self.content.add_widget(self.language_button)

        self.audio_switch = self._switch_row("prefer_audio", self.set_audio_default)
        self.clipboard_switch = self._switch_row("clipboard_autofill", self.set_clipboard)
        self.notification_switch = self._switch_row("completion_notifications", self.set_notifications)
        self.theme_switch = self._switch_row("dark_theme", self.set_theme)

        self.ffmpeg_input = MDTextField(
            hint_text="",
            mode="round",
            icon_left="console",
            font_name="Rubik",
            halign=self.app.text_align,
            multiline=False,
            size_hint_y=None,
            height=dp(64),
        )
        self.content.add_widget(self.ffmpeg_input)
        self.save_ffmpeg_button = MDFlatButton(text="", size_hint_x=1, on_release=lambda *_: self.save_ffmpeg())
        self.content.add_widget(self.save_ffmpeg_button)
        self.update_texts()

    def _switch_row(self, label_key: str, callback):
        row = MDBoxLayout(adaptive_height=True, spacing=dp(10), padding=(0, dp(4), 0, dp(4)))
        label = MDLabel(text="", halign=self.app.text_align, adaptive_height=True)
        self.switch_labels[label_key] = label
        switch = MDSwitch()
        switch.bind(active=lambda instance, value: callback(value))
        row.add_widget(label)
        row.add_widget(switch)
        self.content.add_widget(row)
        return switch

    def update_texts(self) -> None:
        self.path_input.hint_text = self.app.tr("download_folder")
        self.path_input.halign = self.app.text_align
        self.browse_button.text = self.app.tr("browse")
        self.save_path_button.text = self.app.tr("save_path")
        self.ffmpeg_input.hint_text = self.app.tr("ffmpeg_hint")
        self.ffmpeg_input.halign = self.app.text_align
        self.save_ffmpeg_button.text = self.app.tr("save_ffmpeg")

        for key, label in self.switch_labels.items():
            label.text = self.app.tr(key)
            label.halign = self.app.text_align
        self.refresh()

    def refresh(self) -> None:
        settings = self.app.settings_store.get_all()
        self._refreshing = True
        self.path_input.text = settings["download_dir"]
        self.quality_button.text = self.app.tr(
            "default_quality",
            quality=self.app.quality_label(settings["quality"]),
        )
        self.language_button.text = self.app.tr(
            "language",
            language=self.app.language_label(settings.get("language", self.app.language)),
        )
        self.ffmpeg_input.text = settings.get("ffmpeg_location", "")
        self.audio_switch.active = bool(settings.get("audio_only", False))
        self.clipboard_switch.active = bool(settings.get("clipboard_autofill", True))
        self.notification_switch.active = bool(settings.get("notifications", True))
        self.theme_switch.active = settings.get("theme_style", "Light") == "Dark"
        self._refreshing = False

    def open_file_manager(self) -> None:
        try:
            if not self.file_manager:
                self.file_manager = MDFileManager(
                    exit_manager=self.close_file_manager,
                    select_path=self.select_path,
                    preview=False,
                )
            start_path = self.path_input.text or str(Path.home())
            self.file_manager.show(start_path if Path(start_path).exists() else str(Path.home()))
        except Exception as exc:
            toast(self.app.tr("file_picker_unavailable", error=exc))

    def select_path(self, path: str) -> None:
        selected = Path(path)
        if selected.is_file():
            selected = selected.parent
        self.path_input.text = str(selected)
        self.save_path()
        self.close_file_manager()

    def close_file_manager(self, *args) -> None:
        if self.file_manager:
            self.file_manager.close()

    def save_path(self) -> None:
        try:
            path = ensure_directory(self.path_input.text)
        except Exception as exc:
            toast(self.app.tr("folder_create_failed", error=exc))
            return
        self.path_input.text = path
        self.app.settings_store.set("download_dir", path)
        toast(self.app.tr("folder_saved"))

    def open_quality_menu(self) -> None:
        items = [
            {
                "viewclass": "OneLineListItem",
                "text": self.app.quality_label(label),
                "height": dp(48),
                "on_release": lambda value=label: self.set_quality(value),
            }
            for label in QUALITY_CHOICES
        ]
        self.quality_menu = MDDropdownMenu(caller=self.quality_button, items=items, width_mult=4)
        self.quality_menu.open()

    def set_quality(self, label: str) -> None:
        self.app.settings_store.set("quality", label)
        self.quality_button.text = self.app.tr(
            "default_quality",
            quality=self.app.quality_label(label),
        )
        if self.quality_menu:
            self.quality_menu.dismiss()

    def open_language_menu(self) -> None:
        items = [
            {
                "viewclass": "OneLineListItem",
                "text": label,
                "height": dp(48),
                "on_release": lambda value=code: self.set_language(value),
            }
            for code, label in LANGUAGE_LABELS.items()
        ]
        self.language_menu = MDDropdownMenu(caller=self.language_button, items=items, width_mult=4)
        self.language_menu.open()

    def set_language(self, language: str) -> None:
        if self.language_menu:
            self.language_menu.dismiss()
        self.app.set_language(language)

    def set_audio_default(self, value: bool) -> None:
        if not self._refreshing:
            self.app.settings_store.set("audio_only", bool(value))

    def set_clipboard(self, value: bool) -> None:
        if not self._refreshing:
            self.app.settings_store.set("clipboard_autofill", bool(value))

    def set_notifications(self, value: bool) -> None:
        if not self._refreshing:
            self.app.settings_store.set("notifications", bool(value))

    def set_theme(self, value: bool) -> None:
        if not self._refreshing:
            self.app.set_theme_style("Dark" if value else "Light")

    def save_ffmpeg(self) -> None:
        value = self.ffmpeg_input.text.strip()
        self.app.settings_store.set("ffmpeg_location", value)
        self.app.downloader.set_ffmpeg_location(value)
        toast(self.app.tr("ffmpeg_saved"))

