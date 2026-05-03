from __future__ import annotations

from kivy.config import Config
from kivy.core.window import Window
from kivy.utils import platform
from kivymd.app import MDApp

from app_config import APP_NAME, HistoryStore, SettingsStore
from downloader import YTDLPDownloader
from i18n import LANGUAGE_LABELS, is_rtl, normalize_language, quality_label, tr
from ui.fonts import apply_rubik_to_theme
from ui.root import AppRoot


Config.set("kivy", "exit_on_escape", "0")


class VideoDownloaderApp(MDApp):
    title = APP_NAME

    def build(self):
        if platform not in ("android", "ios"):
            Window.size = (400, 720)
        Window.minimum_width, Window.minimum_height = 320, 500

        self.settings_store = SettingsStore(self.user_data_dir)
        self.history_store = HistoryStore(self.user_data_dir)
        settings = self.settings_store.get_all()
        self.language = normalize_language(settings.get("language", "ar"))
        self.downloader = YTDLPDownloader(settings.get("ffmpeg_location", ""))

        self.theme_cls.primary_palette = "LightBlue"
        self.theme_cls.accent_palette = "LightBlue"
        self.theme_cls.theme_style = settings.get("theme_style", "Light")
        apply_rubik_to_theme(self.theme_cls)
        try:
            self.theme_cls.material_style = "M3"
        except Exception:
            pass

        return AppRoot(app=self)

    def on_start(self) -> None:
        self._request_android_permissions()
        if hasattr(self.root, "home_screen"):
            self.root.home_screen.autofill_from_clipboard()

    def toggle_theme(self) -> None:
        next_style = "Light" if self.theme_cls.theme_style == "Dark" else "Dark"
        self.set_theme_style(next_style)

    def set_theme_style(self, style: str) -> None:
        self.theme_cls.theme_style = style
        self.settings_store.set("theme_style", style)

    @property
    def is_rtl(self) -> bool:
        return is_rtl(self.language)

    @property
    def text_align(self) -> str:
        return "right" if self.is_rtl else "left"

    def tr(self, key: str, **values) -> str:
        return tr(self.language, key, **values)

    def quality_label(self, quality: str) -> str:
        return quality_label(self.language, quality)

    def language_label(self, language: str | None = None) -> str:
        return LANGUAGE_LABELS.get(normalize_language(language or self.language), "العربية")

    def set_language(self, language: str) -> None:
        self.language = normalize_language(language)
        self.settings_store.set("language", self.language)
        if self.root and hasattr(self.root, "update_texts"):
            self.root.update_texts()

    def refresh_history(self) -> None:
        if (
            self.root
            and hasattr(self.root, "downloads_screen")
            and hasattr(self.root, "current_screen_name")
            and self.root.current_screen_name == "downloads"
        ):
            self.root.downloads_screen.refresh()

    def _request_android_permissions(self) -> None:
        if platform != "android":
            return
        try:
            from android.permissions import Permission, request_permissions

            permissions = [
                Permission.INTERNET,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
                getattr(Permission, "READ_MEDIA_VIDEO", "android.permission.READ_MEDIA_VIDEO"),
                getattr(Permission, "READ_MEDIA_AUDIO", "android.permission.READ_MEDIA_AUDIO"),
                getattr(Permission, "POST_NOTIFICATIONS", "android.permission.POST_NOTIFICATIONS"),
            ]
            request_permissions(permissions)
        except Exception:
            pass


if __name__ == "__main__":
    VideoDownloaderApp().run()
