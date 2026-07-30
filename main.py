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
    PAGE_BG,
    TAB_ACTIVE,
    TAB_IDLE,
)
from context import AppContext
from models.money import format_money
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
    """Persistent album masthead, binder tabs, and swappable paper page."""

    def __init__(self, page: ft.Page, ctx: AppContext):
        self.page = page
        self.ctx = ctx
        self.selected_key = "home"
        self._entries: list[tuple] = []
        self._tabs: dict[str, ft.Container] = {}

        self.masthead_stats = ft.Text(
            size=12.5,
            font_family=META_FONT,
            color=INK_SOFT,
        )
        self.savings_amount = ft.Text(
            size=26,
            font_family=META_FONT,
            color=INK,
        )
        savings_card = ft.Container(
            width=212,
            bgcolor=CARD_BG,
            padding=ft.padding.symmetric(horizontal=14, vertical=12),
            rotate=ft.Rotate(0.024),
            shadow=ft.BoxShadow(
                spread_radius=-3,
                blur_radius=8,
                color="#00000033",
                offset=ft.Offset(0, 3),
            ),
            content=ft.Stack(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "DEPOSITED SO FAR",
                                size=8.5,
                                font_family=DISPLAY_FONT,
                                weight=ft.FontWeight.W_700,
                                color=INK_SOFT,
                                style=ft.TextStyle(letter_spacing=1.35),
                            ),
                            self.savings_amount,
                            self._dashed_rule(180),
                        ],
                        spacing=8,
                    ),
                    ft.Container(
                        width=78,
                        height=20,
                        bgcolor="#f0e6cdd9",
                        rotate=ft.Rotate(-0.052),
                        top=-21,
                        left=50,
                    ),
                ],
                clip_behavior=ft.ClipBehavior.NONE,
            ),
        )
        self.masthead = ft.Container(
            padding=ft.padding.only(left=10, top=2, right=6, bottom=20),
            content=ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "MY STICKER ALBUM",
                                size=33,
                                font_family=DISPLAY_FONT,
                                weight=ft.FontWeight.W_900,
                                color=INK,
                            ),
                            self.masthead_stats,
                        ],
                        spacing=9,
                        expand=True,
                    ),
                    savings_card,
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )

        self.tabs_row = ft.Row(
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.END,
        )
        self.tabs_host = ft.Container(
            padding=ft.padding.only(left=24),
            content=self.tabs_row,
        )
        self.content = ft.Container(
            expand=True,
            bgcolor=PAGE_BG,
            padding=ft.padding.only(left=24, top=20, right=24, bottom=28),
            alignment=ft.alignment.top_left,
            shadow=ft.BoxShadow(
                spread_radius=-10,
                blur_radius=26,
                color="#0000006b",
                offset=ft.Offset(0, 12),
            ),
        )
        self.root = ft.Container(
            expand=True,
            padding=24,
            content=ft.Column(
                [self.masthead, self.tabs_host, self.content],
                spacing=0,
                expand=True,
            ),
        )
        self._build_rail()
        self.refresh_masthead(update=False)

    @staticmethod
    def _dashed_rule(width: float) -> ft.Control:
        return ft.Row(
            [
                ft.Container(width=4, height=1, bgcolor="#2f261838")
                for _ in range(max(1, int(width // 8)))
            ],
            spacing=4,
            height=1,
            width=width,
        )

    def _build_rail(self):
        """Rebuild the tab set when optional navigation entries change."""
        entries = [
            ("home", "Home", self.go_home),
            ("collections", "Collections", self.go_collections),
            ("shop", "Shop", self.go_shop),
            ("vice", "Vice Shop", self.go_vice_shop),
        ]
        if self.ctx.settings.state.creator_enabled:
            entries.append(("creator", "Creator", self.go_creator))
        entries.append(("settings", "Settings", self.go_settings))
        self._entries = entries
        if not any(entry[0] == self.selected_key for entry in entries):
            self.selected_key = "home"
        self._tabs = {}
        tabs: list[ft.Control] = []
        for key, label, callback in entries:
            tab = ft.Container(
                border_radius=ft.border_radius.only(top_left=3, top_right=3),
                alignment=ft.alignment.center,
                on_click=lambda e, cb=callback: cb(),
                ink=True,
                animate=ft.Animation(280, ft.AnimationCurve.EASE_OUT_BACK),
                animate_offset=ft.Animation(
                    280, ft.AnimationCurve.EASE_OUT_BACK
                ),
                content=ft.Text(
                    label.upper(),
                    font_family=DISPLAY_FONT,
                    size=9,
                    weight=ft.FontWeight.W_700,
                    style=ft.TextStyle(letter_spacing=0.9),
                    no_wrap=True,
                ),
            )
            self._tabs[key] = tab
            tabs.append(tab)
        self.tabs_row.controls = tabs
        self._style_tabs()

    def _style_tabs(self):
        for key, tab in self._tabs.items():
            selected = key == self.selected_key
            tab.bgcolor = TAB_ACTIVE if selected else TAB_IDLE
            tab.padding = ft.padding.only(
                left=20,
                top=11 if selected else 9,
                right=20,
                bottom=17 if selected else 12,
            )
            tab.offset = ft.Offset(0, 0.03 if selected else 0.11)
            tab.shadow = ft.BoxShadow(
                spread_radius=-4,
                blur_radius=10 if selected else 6,
                color="#00000033" if selected else "#0000002e",
                offset=ft.Offset(0, -4 if selected else -2),
            )
            tab.content.color = INK if selected else "#2f2618a3"

    def rebuild_rail(self):
        """Rebuild optional tabs while preserving a valid selection."""
        self._build_rail()
        self.page.update()

    def refresh_masthead(self, *, update: bool = True):
        summary = self.ctx.summary.home_summary()
        self.masthead_stats.value = (
            f"{summary.unique_owned} owned · {summary.total_applied} pasted · "
            f"{summary.completed_collections} of "
            f"{summary.total_collections} albums finished"
        )
        self.savings_amount.value = format_money(summary.total_saved)
        if update and self.root.page is not None:
            self.masthead.update()

    def _set(self, key: str, control: ft.Control):
        self.selected_key = key
        self._style_tabs()
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
        self.refresh_masthead(update=False)


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
