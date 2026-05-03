from __future__ import annotations

import threading
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.metrics import dp
from kivy.uix.image import AsyncImage
from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.textfield import MDTextField

from app_config import bytes_to_human, format_duration, is_probable_url, speed_to_human
from downloader import DownloadError, DownloadRequest, VideoMetadata
from services import notify_user, play_file


class HomeScreen(MDScreen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.current_metadata: Optional[VideoMetadata] = None
        self.quality_menu: Optional[MDDropdownMenu] = None
        self.current_mode = "audio" if self.app.settings_store.get("audio_only", False) else "video"
        if self.current_mode == "audio":
            self.selected_quality = "Audio only"
        else:
            self.selected_quality = self.app.settings_store.get("quality", "720p")
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

        self.hero_card = MDCard(
            orientation="vertical",
            adaptive_height=True,
            radius=[dp(16)],
            elevation=2,
            line_color=(0, 0, 0, 0.08),
            padding=dp(12),
        )
        self.hero_title = MDLabel(
            text="",
            font_style="H6",
            bold=True,
            theme_text_color="Primary",
            halign=self.app.text_align,
            adaptive_height=True,
        )
        self.hero_subtitle = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Secondary",
            halign=self.app.text_align,
            adaptive_height=True,
        )
        self.hero_card.add_widget(self.hero_title)
        self.hero_card.add_widget(self.hero_subtitle)
        self.content.add_widget(self.hero_card)

        self.url_input = MDTextField(
            hint_text="",
            helper_text="",
            helper_text_mode="on_focus",
            icon_left="link-variant",
            font_name="Rubik",
            halign=self.app.text_align,
            mode="round",
            multiline=False,
            size_hint_y=None,
            height=dp(64),
        )
        self.url_input.bind(on_text_validate=lambda *_: self.fetch_metadata())
        self.content.add_widget(self.url_input)

        action_row = MDBoxLayout(adaptive_height=True, spacing=dp(10))
        self.fetch_button = MDFillRoundFlatIconButton(
            text="",
            icon="cloud-search-outline",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.fetch_metadata(),
        )
        self.paste_button = MDFlatButton(text="", size_hint_x=1, on_release=lambda *_: self.paste_url())
        action_row.add_widget(self.fetch_button)
        action_row.add_widget(self.paste_button)
        self.content.add_widget(action_row)

        self.preview_card = MDCard(
            orientation="vertical",
            adaptive_height=True,
            padding=dp(24),
            spacing=dp(16),
            radius=[dp(16)],
            elevation=1,
            line_color=(0, 0, 0, 0.08),
        )
        self.thumbnail = AsyncImage(
            source="",
            allow_stretch=True,
            keep_ratio=True,
            size_hint_y=None,
            height=dp(180),
        )
        self.title_label = MDLabel(
            text="",
            font_style="H6",
            bold=True,
            theme_text_color="Primary",
            halign=self.app.text_align,
            adaptive_height=True,
        )
        self.meta_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Secondary",
            halign=self.app.text_align,
            adaptive_height=True,
        )
        self.preview_card.add_widget(self.thumbnail)
        self.preview_card.add_widget(self.title_label)
        self.preview_card.add_widget(self.meta_label)
        self.content.add_widget(self.preview_card)

        self.segment_container = MDCard(
            size_hint_y=None,
            height=dp(52),
            elevation=1,
            radius=[dp(28)],
            padding=dp(4),
            spacing=dp(4),
            line_color=(0, 0, 0, 0.08),
        )

        self.video_segment = MDCard(
            radius=[dp(24)],
            md_bg_color=self.app.theme_cls.primary_color,
            elevation=0,
            on_release=lambda *_: self.set_download_mode("video"),
        )
        self.video_label = MDLabel(text=self.app.tr("video_mode", default="Video"), halign="center", theme_text_color="Custom", text_color=(1,1,1,1), bold=True)
        self.video_segment.add_widget(self.video_label)
        
        self.audio_segment = MDCard(
            radius=[dp(24)],
            elevation=0,
            on_release=lambda *_: self.set_download_mode("audio"),
        )
        self.audio_label = MDLabel(text=self.app.tr("audio_mode", default="Audio"), halign="center", theme_text_color="Secondary", bold=True)
        self.audio_segment.add_widget(self.audio_label)

        self.segment_container.add_widget(self.video_segment)
        self.segment_container.add_widget(self.audio_segment)
        self.content.add_widget(self.segment_container)

        selector_row = MDBoxLayout(adaptive_height=True, spacing=dp(10))
        self.quality_button = MDFillRoundFlatIconButton(
            text="",
            icon="tune-variant",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            on_release=lambda *_: self.open_quality_menu(),
        )
        self.download_button = MDFillRoundFlatIconButton(
            text="",
            icon="download",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
            theme_icon_color="Custom",
            icon_color=(1, 1, 1, 1),
            size_hint_x=1,
            disabled=True,
            on_release=lambda *_: self.start_download(),
        )
        selector_row.add_widget(self.quality_button)
        selector_row.add_widget(self.download_button)
        self.content.add_widget(selector_row)

        self.progress_bar = MDProgressBar(
            value=0,
            max=100,
            size_hint_y=None,
            height=dp(14),
            color=self.app.theme_cls.primary_color,
        )
        self.content.add_widget(self.progress_bar)

        self.progress_label = MDLabel(
            text="",
            theme_text_color="Secondary",
            font_style="Caption",
            halign=self.app.text_align,
            adaptive_height=True,
        )
        self.content.add_widget(self.progress_label)

        # ── Footer: branding & copyright ──
        self.footer_label = MDLabel(
            text="",
            font_style="Caption",
            theme_text_color="Hint",
            halign="center",
            adaptive_height=True,
            padding=(0, dp(16), 0, 0),
        )
        self.content.add_widget(self.footer_label)

        self.update_texts()

    def on_pre_enter(self, *args) -> None:
        if self.app.settings_store.get("clipboard_autofill", True):
            self.autofill_from_clipboard()

    def update_texts(self) -> None:
        self.hero_title.text = self.app.tr("home_headline")
        self.hero_subtitle.text = self.app.tr("home_subtitle")
        self.url_input.hint_text = self.app.tr("url_hint")
        self.url_input.helper_text = self.app.tr("url_helper")
        self.url_input.halign = self.app.text_align
        self.fetch_button.text = self.app.tr("fetch")
        self.paste_button.text = self.app.tr("paste")
        self.download_button.text = self.app.tr("download")
        self.footer_label.text = self.app.tr("footer_text")
        self._set_quality_button_text()

        for label in (
            self.hero_title,
            self.hero_subtitle,
            self.title_label,
            self.meta_label,
            self.progress_label,
        ):
            label.halign = self.app.text_align

        if not self.current_metadata:
            self.title_label.text = self.app.tr("preview_empty_title")
            self.meta_label.text = self.app.tr("preview_empty_meta")
            self.progress_label.text = self.app.tr("idle")

        self.set_download_mode(self.current_mode)

    def set_download_mode(self, mode: str) -> None:
        self.current_mode = mode
        if mode == "video":
            self.video_segment.md_bg_color = self.app.theme_cls.primary_color
            self.video_label.text_color = (1, 1, 1, 1)
            self.video_label.theme_text_color = "Custom"
            
            self.audio_segment.md_bg_color = (0, 0, 0, 0)
            self.audio_label.theme_text_color = "Secondary"
            
            self.selected_quality = self.app.settings_store.get("quality", "720p")
        else:
            self.audio_segment.md_bg_color = self.app.theme_cls.primary_color
            self.audio_label.text_color = (1, 1, 1, 1)
            self.audio_label.theme_text_color = "Custom"
            
            self.video_segment.md_bg_color = (0, 0, 0, 0)
            self.video_label.theme_text_color = "Secondary"
            
            self.selected_quality = "Audio only"
            
        self._set_quality_button_text()

    def autofill_from_clipboard(self) -> None:
        try:
            text = Clipboard.paste().strip()
        except Exception:
            return
        if is_probable_url(text) and not self.url_input.text.strip():
            self.url_input.text = text
            toast(self.app.tr("clipboard_detected"))

    def paste_url(self) -> None:
        try:
            text = Clipboard.paste().strip()
        except Exception:
            text = ""
        if text:
            self.url_input.text = text

    def fetch_metadata(self) -> None:
        url = self.url_input.text.strip()
        if not is_probable_url(url):
            self.show_status(self.app.tr("invalid_url"), error=True)
            return

        self.fetch_button.disabled = True
        self.download_button.disabled = True
        self.show_status(self.app.tr("fetching_metadata"))

        thread = threading.Thread(target=self._fetch_worker, args=(url,), daemon=True)
        thread.start()

    def _fetch_worker(self, url: str) -> None:
        try:
            metadata = self.app.downloader.fetch_metadata(url)
            Clock.schedule_once(lambda *_: self._metadata_ready(metadata))
        except DownloadError as exc:
            err = str(exc)
            Clock.schedule_once(lambda *_: self._metadata_failed(err))
        except Exception as exc:
            err = f"Unexpected error: {exc}"
            Clock.schedule_once(lambda *_: self._metadata_failed(err))

    def _metadata_ready(self, metadata: VideoMetadata) -> None:
        self.fetch_button.disabled = False
        self.current_metadata = metadata
        self.thumbnail.source = metadata.thumbnail
        self.title_label.text = metadata.title
        uploader = f" | {metadata.uploader}" if metadata.uploader else ""
        self.meta_label.text = f"{metadata.platform}{uploader} | {format_duration(metadata.duration)}"
        self._configure_quality_menu(metadata.formats)
        self.download_button.disabled = False
        self.show_status(self.app.tr("ready_download"))

    def _metadata_failed(self, message: str) -> None:
        self.fetch_button.disabled = False
        self.download_button.disabled = True
        self.current_metadata = None
        self.show_status(message, error=True)

    def _configure_quality_menu(self, formats) -> None:
        labels = [item.label for item in formats]
        preferred = self.app.settings_store.get("quality", "720p")
        if self.app.settings_store.get("audio_only", False):
            preferred = "Audio only"
        self.selected_quality = preferred if preferred in labels else labels[0]
        self._set_quality_button_text()
        self.quality_items = labels

    def open_quality_menu(self) -> None:
        labels: List[str] = getattr(self, "quality_items", ["360p", "720p", "1080p", "Audio only"])
        items = [
            {
                "viewclass": "OneLineListItem",
                "text": self.app.quality_label(label),
                "height": dp(48),
                "on_release": lambda value=label: self.set_quality(value),
            }
            for label in labels
        ]
        self.quality_menu = MDDropdownMenu(caller=self.quality_button, items=items, width_mult=4)
        self.quality_menu.open()

    def set_quality(self, label: str) -> None:
        self.selected_quality = label
        self._set_quality_button_text()
        if self.quality_menu:
            self.quality_menu.dismiss()

    def _set_quality_button_text(self) -> None:
        self.quality_button.text = self.app.tr(
            "quality",
            quality=self.app.quality_label(self.selected_quality),
        )

    def start_download(self) -> None:
        if not self.current_metadata:
            self.show_status(self.app.tr("fetch_before_download"), error=True)
            return

        settings = self.app.settings_store.get_all()
        output_dir = settings["download_dir"]
        request = DownloadRequest(
            url=self.current_metadata.webpage_url or self.current_metadata.url,
            output_dir=output_dir,
            quality=self.selected_quality,
            audio_only=self.selected_quality == "Audio only",
        )

        item_id = uuid.uuid4().hex
        self.app.history_store.add(
            {
                "id": item_id,
                "title": self.current_metadata.title,
                "url": self.current_metadata.webpage_url,
                "platform": self.current_metadata.platform,
                "quality": self.selected_quality,
                "status": "downloading",
                "progress": 0,
                "output_dir": output_dir,
                "path": "",
            }
        )
        self.app.refresh_history()
        self.progress_bar.value = 0
        self.download_button.disabled = True
        self.fetch_button.disabled = True
        self.show_status(self.app.tr("starting_download"))

        thread = threading.Thread(target=self._download_worker, args=(request, item_id), daemon=True)
        thread.start()

    def _download_worker(self, request: DownloadRequest, item_id: str) -> None:
        last_emit = 0.0

        def progress(data: Dict) -> None:
            nonlocal last_emit
            now = time.monotonic()
            if data.get("status") == "downloading" and now - last_emit < 0.2:
                return
            last_emit = now
            Clock.schedule_once(lambda *_: self._apply_progress(item_id, data))

        try:
            final_path = self.app.downloader.download(request, progress_callback=progress)
            Clock.schedule_once(lambda *_: self._download_complete(item_id, final_path))
        except DownloadError as exc:
            err = str(exc)
            Clock.schedule_once(lambda *_: self._download_failed(item_id, err))
        except Exception as exc:
            err = f"Unexpected error: {exc}"
            Clock.schedule_once(lambda *_: self._download_failed(item_id, err))

    def _apply_progress(self, item_id: str, data: Dict) -> None:
        percent = float(data.get("percent") or 0)
        self.progress_bar.value = percent
        speed = speed_to_human(data.get("speed"))
        downloaded = bytes_to_human(data.get("downloaded_bytes"))
        total = bytes_to_human(data.get("total_bytes"))
        message = self._localized_progress_message(data.get("message"))
        if data.get("total_bytes"):
            text = f"{message}: {percent:.1f}% | {downloaded} / {total} | {speed}"
        else:
            text = f"{message}: {percent:.1f}% | {speed}"
        self.progress_label.text = text
        self.app.history_store.update(item_id, progress=round(percent, 1), status="downloading")
        self.app.refresh_history()

    def _localized_progress_message(self, message: Optional[str]) -> str:
        if message == "Processing media":
            return self.app.tr("processing")
        if message == "Finalizing file":
            return self.app.tr("finalizing")
        return self.app.tr("downloading")

    def _download_complete(self, item_id: str, final_path: str) -> None:
        self.download_button.disabled = False
        self.fetch_button.disabled = False
        self.progress_bar.value = 100
        self.progress_label.text = self.app.tr("complete", name=Path(final_path).name)
        self.app.history_store.update(
            item_id,
            progress=100,
            status="complete",
            path=final_path,
        )
        self.app.refresh_history()
        if self.app.settings_store.get("notifications", True):
            notify_user(self.app.tr("notification_complete_title"), Path(final_path).name)
        toast(self.app.tr("notification_complete_title"))
        
        self.show_success_dialog(final_path)

    def show_success_dialog(self, file_path: str) -> None:
        self.dialog = MDDialog(
            title=self.app.tr("success_title"),
            text=self.app.tr("success_message"),
            buttons=[
                MDFlatButton(
                    text=self.app.tr("close"),
                    on_release=lambda *x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text=self.app.tr("view_video"),
                    theme_text_color="Custom",
                    text_color=self.app.theme_cls.primary_color,
                    on_release=lambda *x: [play_file(file_path), self.dialog.dismiss()]
                ),
            ],
        )
        self.dialog.open()

    def _download_failed(self, item_id: str, message: str) -> None:
        self.download_button.disabled = False
        self.fetch_button.disabled = False
        self.app.history_store.update(item_id, status="failed", error=message)
        self.app.refresh_history()
        self.show_status(message, error=True)

    def show_status(self, message: str, error: bool = False) -> None:
        self.progress_label.text = message
        if error:
            toast(message[:120])

