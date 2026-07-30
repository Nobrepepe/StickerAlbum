"""Home screen: scrapbook summary, favorite polaroid, and sticker sheet."""

import flet as ft

from components.character_tiles import character_card, character_tile
from components.empty_state import empty_state
from components.paper import (
    PAPER_SHADOW,
    page_caption,
    tape_strip,
)
from components.sticker_dialog import open_sticker_dialog
from components.sticker_slot import build_sticker_slot
from components.theme import (
    BOARD_BG,
    DISPLAY_FONT,
    INK,
    INK_SOFT,
    META_FONT,
)
_GRID_TILE_W = 228.0
_SLOT_W, _SLOT_H = 150.0, 200.0


def build_home(page: ft.Page, ctx, nav) -> ft.Control:
    fav_area = ft.Container()
    state = {"choosing": False}

    def pick(character_id: str):
        ctx.state.set_favorite_character(character_id)
        state["choosing"] = False
        render_fav()

    def build_picker_board() -> ft.Control:
        sections: list[ft.Control] = [
            ft.Text(
                "PICK YOUR FAVORITE CHARACTER",
                size=15,
                font_family=DISPLAY_FONT,
                weight=ft.FontWeight.W_700,
                color=INK,
            ),
        ]
        any_chars = False
        for collection in ctx.collections.list_all():
            chars = ctx.characters.list_by_collection(collection.id)
            if not chars:
                continue
            any_chars = True
            theme = collection.theme_color or "#7c4dff"
            sections.append(ft.Text(collection.name, size=12,
                                    font_family=META_FONT, color=INK_SOFT))
            sections.append(ft.Row(
                [
                    character_tile(
                        c,
                        theme,
                        [ft.Text(
                            c.name,
                            size=12,
                            font_family=DISPLAY_FONT,
                            weight=ft.FontWeight.W_700,
                            color="#ffffff",
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        )],
                        on_click=lambda e, cid=c.id: pick(cid),
                        width=_GRID_TILE_W,
                    )
                    for c in chars
                ],
                wrap=True,
                spacing=0,
                run_spacing=0,
            ))
        if not any_chars:
            return empty_state(ft.Icons.FAVORITE_BORDER, "No characters yet",
                               "Create or restore a collection first.")
        return ft.Container(
            bgcolor=BOARD_BG,
            padding=18,
            shadow=PAPER_SHADOW,
            content=ft.Column(sections, spacing=12),
        )

    def on_slot_tap(sticker):
        character = ctx.characters.get(sticker.character_id)
        collection = ctx.collections.get(character.collection_id)

        def changed(_sticker):
            nav.refresh_masthead()
            nav.go_home()

        open_sticker_dialog(
            page, ctx.album, sticker, character, collection.name,
            on_change=changed, vice=ctx.vice,
        )

    def build_fav_view(fav) -> ft.Control:
        theme = fav.collection.theme_color or "#7c4dff"
        polaroid_width = 244
        art_width = polaroid_width - 18
        polaroid = ft.Container(
            width=polaroid_width,
            bgcolor="#ffffff",
            padding=ft.padding.only(left=9, right=9, top=9, bottom=12),
            rotate=ft.Rotate(-0.017),
            shadow=PAPER_SHADOW,
            content=ft.Column(
                [
                    character_card(fav.character, theme, [], width=art_width),
                    ft.Row(
                        [
                            ft.Text(
                                fav.character.name,
                                size=14,
                                font_family=DISPLAY_FONT,
                                weight=ft.FontWeight.W_700,
                                color=INK,
                            ),
                            ft.Text(
                                f"{fav.applied}/{fav.total} · {fav.collection.name}",
                                size=11,
                                font_family=META_FONT,
                                color=INK_SOFT,
                                expand=True,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.END,
                    ),
                ],
                spacing=10,
            ),
        )
        change = ft.Container(
            padding=ft.padding.only(bottom=3),
            border=ft.border.only(bottom=ft.BorderSide(1.5, "#2f261866")),
            on_click=lambda e: start_choosing(),
            content=ft.Text(
                "CHANGE FAVORITE",
                size=9.5,
                font_family=DISPLAY_FONT,
                weight=ft.FontWeight.W_700,
                color=INK,
                style=ft.TextStyle(letter_spacing=1.1),
            ),
        )
        left = ft.Column([polaroid, change], spacing=14)

        if fav.owned_stickers:
            board_content: ft.Control = ft.Row(
                [
                    build_sticker_slot(
                        ctx.album, sticker, on_slot_tap,
                        width=_SLOT_W, height=_SLOT_H,
                    )
                    for sticker, _styles in fav.owned_stickers
                ],
                wrap=True,
                spacing=0,
                run_spacing=0,
            )
        else:
            board_content = empty_state(
                ft.Icons.AUTO_AWESOME,
                f"No {fav.character.name} stickers yet",
                "Open some packs — their stickers will show up here.",
            )
        board = ft.Container(
            bgcolor=BOARD_BG,
            padding=18,
            shadow=PAPER_SHADOW,
            alignment=ft.alignment.top_left if fav.owned_stickers
            else ft.alignment.center,
            content=board_content,
            expand=True,
        )
        taped_board = ft.Stack(
            [
                board,
                ft.Container(content=tape_strip(), top=-10, left=44),
                ft.Container(content=tape_strip(84, 2), bottom=-9, right=52),
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE,
        )
        return ft.Row(
            [left, ft.Container(content=taped_board, expand=True)],
            spacing=22,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

    def start_choosing():
        state["choosing"] = True
        render_fav()

    def render_fav():
        fav = ctx.summary.favorite_info()
        fav_area.content = (
            build_picker_board()
            if fav is None or state["choosing"]
            else build_fav_view(fav)
        )
        page.update()

    favorite = ctx.summary.favorite_info()
    fav_area.content = (
        build_picker_board() if favorite is None else build_fav_view(favorite)
    )

    return ft.Column(
        [
            page_caption("favourite character · everything you own of them"),
            fav_area,
        ],
        spacing=20,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
