"""Home screen.

The favorite-character area is a white board. With no favorite chosen (or
while changing it), the board shows every character from every collection as
blended 16:9 tiles; picking one switches to the character's tall card on the
left with a board of their owned stickers on the right, album-style.
"""

import flet as ft

from components.character_tiles import character_card, character_tile
from components.empty_state import empty_state
from components.sticker_dialog import open_sticker_dialog
from components.sticker_slot import build_sticker_slot
from components.theme import BOARD_BG, PANEL_BG, PANEL_BORDER
from models.money import format_money

_GRID_TILE_W = 228.0
_SLOT_W, _SLOT_H = 150.0, 200.0
_SPICY_COLOR = "#ff7043"


def _stat_tile(icon: str, label: str, value: str, color: str) -> ft.Control:
    return ft.Container(
        width=220,
        bgcolor=PANEL_BG,
        border_radius=14,
        border=ft.border.all(1, PANEL_BORDER),
        padding=16,
        content=ft.Row(
            [
                ft.Icon(icon, size=30, color=color),
                ft.Column(
                    [
                        ft.Text(value, size=19, weight=ft.FontWeight.BOLD),
                        ft.Text(label, size=12, color=ft.Colors.GREY_400),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=14,
        ),
    )


def build_home(page: ft.Page, ctx, nav) -> ft.Control:
    s = ctx.summary.home_summary()
    fav_area = ft.Container()
    state = {"choosing": False}

    # ---- character picker board ------------------------------------------

    def pick(character_id: str):
        ctx.state.set_favorite_character(character_id)
        state["choosing"] = False
        render_fav()

    def build_picker_board() -> ft.Control:
        sections: list[ft.Control] = [
            ft.Text("Pick your favorite character", size=15,
                    weight=ft.FontWeight.BOLD, color="#3a3644"),
        ]
        any_chars = False
        for collection in ctx.collections.list_all():
            chars = ctx.characters.list_by_collection(collection.id)
            if not chars:
                continue
            any_chars = True
            theme = collection.theme_color or "#7c4dff"
            sections.append(ft.Text(collection.name, size=12,
                                    color=ft.Colors.GREY_600))
            sections.append(ft.Row(
                [
                    character_tile(
                        c, theme,
                        [ft.Text(c.name, size=12, weight=ft.FontWeight.BOLD,
                                 color=ft.Colors.WHITE, max_lines=1,
                                 overflow=ft.TextOverflow.ELLIPSIS)],
                        on_click=lambda e, cid=c.id: pick(cid),
                        width=_GRID_TILE_W,
                    )
                    for c in chars
                ],
                wrap=True, spacing=0, run_spacing=0,
            ))
        if not any_chars:
            return empty_state(ft.Icons.FAVORITE_BORDER, "No characters yet",
                               "Create or restore a collection first.")
        return ft.Container(
            bgcolor=BOARD_BG,
            border_radius=16,
            padding=ft.padding.all(18),
            content=ft.Column(sections, spacing=12),
        )

    # ---- favorite view: card + owned stickers board ------------------------

    def on_slot_tap(sticker):
        character = ctx.characters.get(sticker.character_id)
        open_sticker_dialog(page, ctx.album, sticker, character,
                            on_change=lambda st: nav.go_home(), vice=ctx.vice)

    def build_fav_view(fav) -> ft.Control:
        theme = fav.collection.theme_color or "#7c4dff"
        lines: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text(fav.character.name, size=15, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE, max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{fav.applied}/{fav.total}", size=12,
                            color=ft.Colors.GREY_400),
                ],
                spacing=8, tight=True,
            ),
            ft.Text(fav.collection.name, size=11, color=ft.Colors.GREY_400),
        ]
        left = ft.Column(
            [
                character_card(fav.character, theme, lines),
                ft.TextButton("Change favorite", icon=ft.Icons.SYNC,
                              on_click=lambda e: start_choosing()),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )
        if fav.owned_stickers:
            board_content: ft.Control = ft.Row(
                [build_sticker_slot(ctx.album, st, on_slot_tap,
                                    width=_SLOT_W, height=_SLOT_H)
                 for st, _styles in fav.owned_stickers],
                wrap=True, spacing=0, run_spacing=0,
            )
        else:
            board_content = ft.Column(
                [
                    ft.Icon(ft.Icons.AUTO_AWESOME, size=40,
                            color=ft.Colors.GREY_500),
                    ft.Text(f"No {fav.character.name} stickers yet", size=14,
                            color="#3a3644", weight=ft.FontWeight.BOLD),
                    ft.Text("Open some packs — their stickers will show up here.",
                            size=12, color=ft.Colors.GREY_600),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            )
        board = ft.Container(
            bgcolor=BOARD_BG,
            border_radius=16,
            padding=ft.padding.all(18),
            alignment=ft.alignment.top_left if fav.owned_stickers
            else ft.alignment.center,
            content=board_content,
            expand=True,
        )
        return ft.Row(
            [left, board],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def start_choosing():
        state["choosing"] = True
        render_fav()

    def render_fav():
        fav = ctx.summary.favorite_info()
        if fav is None or state["choosing"]:
            fav_area.content = build_picker_board()
        else:
            fav_area.content = build_fav_view(fav)
        page.update()

    fav = ctx.summary.favorite_info()
    fav_area.content = build_picker_board() if fav is None else build_fav_view(fav)

    return ft.Column(
        [
            ft.Text("My Sticker Album", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("Every pack is a deposit into your savings. Collect, paste, repeat.",
                    size=13, color=ft.Colors.GREY_400),
            ft.Row(
                [
                    _stat_tile(ft.Icons.STYLE, "Unique stickers owned",
                               str(s.unique_owned), "#64b5f6"),
                    _stat_tile(ft.Icons.MENU_BOOK, "Stickers applied",
                               str(s.total_applied), "#81c784"),
                    _stat_tile(ft.Icons.EMOJI_EVENTS, "Collections completed",
                               f"{s.completed_collections} / {s.total_collections}",
                               "#ffd54f"),
                    _stat_tile(ft.Icons.SAVINGS, "Total saved",
                               format_money(s.total_saved), "#4db6ac"),
                ],
                wrap=True,
                spacing=14,
                run_spacing=14,
            ),
            fav_area,
            ft.Row(
                [
                    ft.FilledTonalButton(
                        "Browse collections", icon=ft.Icons.COLLECTIONS_BOOKMARK,
                        on_click=lambda e: nav.go_collections(),
                    ),
                    ft.FilledTonalButton(
                        "Go to shop", icon=ft.Icons.STOREFRONT,
                        on_click=lambda e: nav.go_shop(),
                    ),
                ],
                spacing=12,
            ),
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
