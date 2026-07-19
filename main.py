"""Personal sticker album — desktop app entry point.

Run from the repository root:  python main.py
"""

import logging

import flet as ft

from components.theme import PAGE_BG, RAIL_BG
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
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=84,
            group_alignment=-0.9,
            bgcolor=RAIL_BG,
            on_change=self._on_rail_change,
        )
        self._entries: list[tuple] = []
        self._build_rail()
        self.root = ft.Row(
            [self.rail, ft.VerticalDivider(width=1), self.content],
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
        ]
        if self.ctx.settings.state.creator_enabled:
            entries.append(("creator", ft.Icons.DESIGN_SERVICES_OUTLINED,
                            ft.Icons.DESIGN_SERVICES, "Creator", self.go_creator))
        entries.append(("settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS,
                        "Settings", self.go_settings))
        self._entries = entries
        self.rail.destinations = [
            ft.NavigationRailDestination(icon=icon, selected_icon=sel, label=label)
            for _, icon, sel, label, _ in entries
        ]

    def rebuild_rail(self):
        """Called after a settings change; keeps the current selection valid."""
        current = self._entries[self.rail.selected_index][0] if self._entries else "home"
        self._build_rail()
        self.rail.selected_index = self._index_of(current)
        self.page.update()

    def _index_of(self, key: str) -> int:
        for i, entry in enumerate(self._entries):
            if entry[0] == key:
                return i
        return 0

    def _on_rail_change(self, e):
        self._entries[e.control.selected_index][4]()

    def _set(self, key: str, control: ft.Control):
        self.rail.selected_index = self._index_of(key)
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

    def go_creator(self):
        self._set("creator", build_creator(self.page, self.ctx, self))

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
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = PAGE_BG
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
                        ft.Icon(ft.Icons.ERROR_OUTLINE, size=56, color="#e57373"),
                        ft.Text("Couldn't load the sticker catalog", size=20,
                                weight=ft.FontWeight.BOLD),
                        ft.Text(str(exc), size=13, color=ft.Colors.GREY_400,
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
