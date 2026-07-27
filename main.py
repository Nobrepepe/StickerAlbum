"""Personal sticker album — desktop app entry point.

Run from the repository root:  python main.py
"""

import logging

import flet as ft

from components.theme import (
    BODY_FONT,
    CARD_BG,
    DESK_BG,
    DISPLAY_FONT,
    INK,
    INK_SOFT,
    META_FONT,
    SPINE_BG,
)
from context import AppContext
from repositories.errors import AppError
from views.album_view import build_album
from views.collections_view import build_collections
from views.creator_view import build_creator
from views.errors_ui import show_info
from views.home_view import build_home
from views.pack_result_view import build_pack_result
from views.settings_view import build_settings
from views.shop_view import build_shop
from views.vice_shop_view import build_vice_shop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("album")


class AppShell:
    """Persistent navigation rail + swappable content area. The rail is
    rebuilt when settings change (the Creator tab is optional)."""

    def __init__(self, page: ft.Page, ctx: AppContext):
        self.page = page
        self.ctx = ctx
        # top_left keeps short screens (Settings, Collections, ...) anchored
        # to the top instead of floating in the middle.
        self.content = ft.Container(
            expand=True,
            padding=ft.padding.all(24),
            alignment=ft.alignment.top_left,
        )
        self.selected_key = "home"
        self.rail_column = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=3,
            scroll=ft.ScrollMode.AUTO,
        )
        self.rail = ft.Container(
            width=92,
            bgcolor=SPINE_BG,
            padding=ft.padding.only(top=18, bottom=18),
            content=self.rail_column,
        )
        self._entries: list[tuple] = []
        self._build_rail()
        self.root = ft.Row(
            [self.rail, self.content],
            expand=True,
            spacing=0,
        )

    def _build_rail(self):
        entries = [
            ("home", ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Home", self.go_home),
            ("collections", ft.Icons.COLLECTIONS_BOOKMARK_OUTLINED,
             ft.Icons.COLLECTIONS_BOOKMARK, "Collections", self.go_collections),
            ("shop", ft.Icons.STOREFRONT_OUTLINED, ft.Icons.STOREFRONT, "Shop",
             self.go_shop),
            ("vice", ft.Icons.LOCAL_BAR_OUTLINED, ft.Icons.LOCAL_BAR, "Vice Shop",
             self.go_vice_shop),
        ]
        if self.ctx.settings.state.creator_enabled:
            entries.append(("creator", ft.Icons.DESIGN_SERVICES_OUTLINED,
                            ft.Icons.DESIGN_SERVICES, "Creator", self.go_creator))
        entries.append(("settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS,
                        "Settings", self.go_settings))
        self._entries = entries
        controls: list[ft.Control] = [
            ft.Container(
                width=38,
                height=38,
                border_radius=19,
                bgcolor=CARD_BG,
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=14),
                content=ft.Text(
                    "SA",
                    font_family=DISPLAY_FONT,
                    weight=ft.FontWeight.W_900,
                    size=14,
                    color=SPINE_BG,
                ),
            )
        ]
        for key, icon, selected_icon, label, callback in entries:
            selected = key == self.selected_key
            item_color = "#ffffff" if selected else "#ffffffb3"
            controls.append(
                ft.Container(
                    width=78,
                    padding=ft.padding.symmetric(vertical=8),
                    alignment=ft.alignment.center,
                    bgcolor="#ffffff21" if selected else None,
                    on_click=lambda e, cb=callback: cb(),
                    ink=True,
                    content=ft.Column(
                        [
                            ft.Icon(selected_icon if selected else icon, size=17,
                                    color=item_color),
                            ft.Text(
                                label.upper(),
                                font_family=DISPLAY_FONT,
                                size=8.5,
                                weight=ft.FontWeight.W_700,
                                style=ft.TextStyle(letter_spacing=0.7),
                                text_align=ft.TextAlign.CENTER,
                                color=item_color,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        tight=True,
                    ),
                )
            )
        self.rail_column.controls = controls

    def rebuild_rail(self):
        """Called after a settings change; keeps the current selection valid."""
        current = self.selected_key
        self._build_rail()
        if not any(entry[0] == current for entry in self._entries):
            self.selected_key = "home"
            self._build_rail()
        self.page.update()

    def _index_of(self, key: str) -> int:
        for i, entry in enumerate(self._entries):
            if entry[0] == key:
                return i
        return 0

    def _set(self, key: str, control: ft.Control):
        self.selected_key = key
        self._build_rail()
        self.content.content = control
        self.page.update()

    def go_home(self):
        self._set("home", build_home(self.page, self.ctx, self))

    def go_collections(self):
        self._set("collections", build_collections(self.page, self.ctx, self))

    def go_album(self, collection_id: str):
        self.ctx.state.set_last_collection(collection_id)
        self._set("collections", build_album(self.page, self.ctx, self, collection_id))

    def go_shop(self):
        self._set("shop", build_shop(self.page, self.ctx, self))

    def go_pack_result(self, result):
        self._set("shop", build_pack_result(self.page, self.ctx, self, result))

    def go_vice_shop(self):
        self._set("vice", build_vice_shop(self.page, self.ctx, self))

    def go_creator(self):
        self._set("creator", build_creator(self.page, self.ctx, self))

    def go_live_edit(self, collection_id: str):
        """Hot-edit a published collection (names/images/sounds; progress kept)."""
        self._set("creator", build_creator(self.page, self.ctx, self,
                                           live_collection_id=collection_id))

    def go_settings(self):
        self._set("settings", build_settings(self.page, self.ctx, self))

    def reload_catalog(self):
        """Rebuild repositories/services after the catalog changed (publish,
        restore, reset) so the rest of the app sees it without a restart."""
        self.ctx = AppContext.build()


def main(page: ft.Page):
    page.title = "Sticker Album"
    # Single fixed look — no dark/light modes; the art is authored against
    # the white boards, and the chrome stays a soft warm graphite.
    page.fonts = {
        DISPLAY_FONT: "fonts/Archivo-Variable.ttf",
        META_FONT: "fonts/CourierPrime-Regular.ttf",
        BODY_FONT: "fonts/DMSans-Variable.ttf",
    }
    page.theme_mode = ft.ThemeMode.LIGHT
    page.theme = ft.Theme(
        font_family=BODY_FONT,
        color_scheme=ft.ColorScheme(
            primary=INK,
            on_primary=CARD_BG,
            surface=CARD_BG,
            on_surface=INK,
        ),
        scaffold_bgcolor=DESK_BG,
        dialog_theme=ft.DialogTheme(bgcolor=CARD_BG),
        primary_text_theme=ft.TextTheme(
            body_medium=ft.TextStyle(color=INK),
            body_small=ft.TextStyle(color=INK_SOFT),
        ),
    )
    page.bgcolor = DESK_BG
    page.window.width = 1280
    page.window.height = 860
    page.window.min_width = 1000
    page.window.min_height = 700
    page.padding = 0

    try:
        ctx = AppContext.build()
    except (AppError, RuntimeError) as exc:
        log.error("Failed to load catalog: %s", exc)
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=56, color="#a8563a"),
                        ft.Text("COULDN'T LOAD THE STICKER CATALOG", size=20,
                                font_family=DISPLAY_FONT,
                                weight=ft.FontWeight.W_900, color=INK),
                        ft.Text(str(exc), size=13, color=INK_SOFT,
                                font_family=BODY_FONT,
                                text_align=ft.TextAlign.CENTER),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=12,
                    tight=True,
                ),
            )
        )
        return

    shell = AppShell(page, ctx)
    page.add(shell.root)
    shell.go_home()

    for warning in ctx.state.load_warnings:
        show_info(page, warning)


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
