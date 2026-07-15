"""Personal sticker album — desktop app entry point.

Run from the repository root:  python main.py
"""

import logging

import flet as ft

from context import AppContext
from repositories.errors import AppError
from views.album_view import build_album
from views.collections_view import build_collections
from views.errors_ui import show_info
from views.home_view import build_home
from views.pack_result_view import build_pack_result
from views.shop_view import build_shop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("album")


class AppShell:
    """Persistent navigation rail + swappable content area."""

    def __init__(self, page: ft.Page, ctx: AppContext):
        self.page = page
        self.ctx = ctx
        self.content = ft.Container(expand=True, padding=ft.padding.all(24))
        self.rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=84,
            group_alignment=-0.9,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="Home"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.COLLECTIONS_BOOKMARK_OUTLINED,
                    selected_icon=ft.Icons.COLLECTIONS_BOOKMARK,
                    label="Collections",
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icons.STOREFRONT_OUTLINED,
                    selected_icon=ft.Icons.STOREFRONT,
                    label="Shop",
                ),
            ],
            on_change=self._on_rail_change,
        )
        self.root = ft.Row(
            [self.rail, ft.VerticalDivider(width=1), self.content],
            expand=True,
            spacing=0,
        )

    def _on_rail_change(self, e):
        [self.go_home, self.go_collections, self.go_shop][e.control.selected_index]()

    def _set(self, index: int, control: ft.Control):
        self.rail.selected_index = index
        self.content.content = control
        self.page.update()

    def go_home(self):
        self._set(0, build_home(self.page, self.ctx, self))

    def go_collections(self):
        self._set(1, build_collections(self.page, self.ctx, self))

    def go_album(self, collection_id: str):
        self.ctx.state.set_last_collection(collection_id)
        self._set(1, build_album(self.page, self.ctx, self, collection_id))

    def go_shop(self):
        self._set(2, build_shop(self.page, self.ctx, self))

    def go_pack_result(self, result):
        self._set(2, build_pack_result(self.page, self.ctx, self, result))


def main(page: ft.Page):
    page.title = "Sticker Album"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#101018"
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
