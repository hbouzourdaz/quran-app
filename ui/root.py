from __future__ import annotations

from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar

from ui.screens.downloads import DownloadsScreen
from ui.screens.home import HomeScreen
from ui.screens.settings import SettingsScreen


class AppRoot(MDBoxLayout):
    def __init__(self, app, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.app = app
        self.spacing = 0

        self.toolbar = MDTopAppBar(
            title=self.app.tr("app_title"),
            elevation=0,
        )
        self.app.bind(theme_cls=self._update_toolbar_colors)
        self.app.theme_cls.bind(theme_style=self._update_toolbar_colors)
        self._update_toolbar_colors()
        
        self.toolbar.right_action_items = [
            ["theme-light-dark", lambda *_: self.app.toggle_theme()],
        ]
        self.add_widget(self.toolbar)

        self.bottom_nav = MDBottomNavigation()
        
        self.home_nav_item = MDBottomNavigationItem(
            name="home",
            text=self.app.tr("home_title"),
            icon="home",
        )
        self.home_nav_item.bind(on_tab_press=lambda *_: self.switch_screen("home"))
        self.home_screen = HomeScreen(app=app, name="home_screen")
        self.home_nav_item.add_widget(self.home_screen)
        
        self.downloads_nav_item = MDBottomNavigationItem(
            name="downloads",
            text=self.app.tr("downloads_title"),
            icon="history",
        )
        self.downloads_nav_item.bind(on_tab_press=lambda *_: self.switch_screen("downloads"))
        self.downloads_screen = DownloadsScreen(app=app, name="downloads_screen")
        self.downloads_nav_item.add_widget(self.downloads_screen)
        
        self.settings_nav_item = MDBottomNavigationItem(
            name="settings",
            text=self.app.tr("settings_title"),
            icon="cog",
        )
        self.settings_nav_item.bind(on_tab_press=lambda *_: self.switch_screen("settings"))
        self.settings_screen = SettingsScreen(app=app, name="settings_screen")
        self.settings_nav_item.add_widget(self.settings_screen)
        
        self.bottom_nav.add_widget(self.home_nav_item)
        self.bottom_nav.add_widget(self.downloads_nav_item)
        self.bottom_nav.add_widget(self.settings_nav_item)
        
        self.add_widget(self.bottom_nav)

        self.current_screen_name = "home"

    def switch_screen(self, screen_name: str) -> None:
        self.current_screen_name = screen_name
        self.update_toolbar_title()
        if screen_name == "downloads":
            self.downloads_screen.refresh()
        elif screen_name == "settings":
            self.settings_screen.refresh()

    def update_toolbar_title(self) -> None:
        titles = {
            "home": "home_title",
            "downloads": "downloads_title",
            "settings": "settings_title",
        }
        self.toolbar.title = self.app.tr(titles.get(self.current_screen_name, "app_title"))

    def update_texts(self) -> None:
        self.update_toolbar_title()
        self.home_nav_item.text = self.app.tr("home_title")
        self.downloads_nav_item.text = self.app.tr("downloads_title")
        self.settings_nav_item.text = self.app.tr("settings_title")
        self.home_screen.update_texts()
        self.downloads_screen.update_texts()
        self.settings_screen.update_texts()

    def _update_toolbar_colors(self, *args) -> None:
        if self.app.theme_cls.theme_style == "Dark":
            self.toolbar.md_bg_color = self.app.theme_cls.bg_normal
            self.toolbar.specific_text_color = (1, 1, 1, 1)
            if hasattr(self, "bottom_nav"):
                self.bottom_nav.panel_color = self.app.theme_cls.bg_normal
        else:
            self.toolbar.md_bg_color = self.app.theme_cls.bg_normal
            self.toolbar.specific_text_color = (0, 0, 0, 1)
            if hasattr(self, "bottom_nav"):
                self.bottom_nav.panel_color = self.app.theme_cls.bg_normal
