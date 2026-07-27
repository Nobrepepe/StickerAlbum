"""Album screen.

Opens on a collection overview: every sticker in the collection, with a
sidebar of 16:9 character tiles (background art convention:
assets/portraits/<CHARACTER_ID>_tile.png). Selecting a character slides the
sidebar away and replaces it with the character's tall 9:16 card
(assets/portraits/<CHARACTER_ID>_card.png) while the grid focuses on their
stickers at a much larger size. The header back button returns to the
overview with the reverse slide.
"""

import asyncio

import flet as ft

from components.audio_player import play_stamp_then
from components.character_tiles import character_card, character_tile
from components.paper import (
    PAPER_SHADOW,
    dashed_rule,
    outline_button,
    paper_progress,
    tape_strip,
    tool_button,
)
from components.sticker_dialog import open_sticker_dialog
from components.sticker_slot import build_sticker_slot
from components.theme import (
    BOARD_BG,
    DISPLAY_FONT,
    INK,
    INK_SOFT,
    META_FONT,
    STAMP_RED,
)

SIDEBAR_W = 252

# Slots share the artwork's 3:4 ratio. Focused character view goes big;
# the overview shows the whole collection at a glance.
CHAR_SLOT_W, CHAR_SLOT_H = 225.0, 300.0
OVER_SLOT_W, OVER_SLOT_H = 150.0, 200.0

_SPICY_COLOR = STAMP_RED
_BOARD_BG = BOARD_BG


def build_album(page: ft.Page, ctx, nav, collection_id: str) -> ft.Control:
    collection = ctx.collections.get(collection_id)
    characters = ctx.characters.list_by_collection(collection_id)
    theme = collection.theme_color or "#7c4dff"
    spicy_on = ctx.settings.state.spicy_enabled

    # None -> collection overview; 0-9 -> that character's page.
    state: dict = {
        "char": None, "stamp": None, "stamp_control": None, "sliding": False,
    }

    title_text = ft.Text(size=25, font_family=DISPLAY_FONT,
                         weight=ft.FontWeight.W_900, color=INK)
    subtitle_text = ft.Text(size=12, color=INK_SOFT, font_family=META_FONT,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
    progress_text = ft.Text(size=14, color=INK, font_family=DISPLAY_FONT,
                            weight=ft.FontWeight.W_900)
    progress_bar = ft.Container(content=paper_progress(0, width=220))
    grid = ft.Column(spacing=16, scroll=ft.ScrollMode.AUTO, expand=True)
    sidebar = ft.Container(
        width=SIDEBAR_W,
        animate_offset=ft.Animation(240, ft.AnimationCurve.EASE_IN_OUT),
        offset=ft.Offset(0, 0),
    )

    # ---- sidebar: character tile list --------------------------------------
    # Tiles sit edge-to-edge on a white strip so their vignette edges blend
    # into one another, like the stickers on the board.

    def char_tile(i: int, char) -> ft.Control:
        applied, total = ctx.album.character_progress(char.id)
        complete = total > 0 and applied == total
        name_line = ft.Row(
            [
                ft.Text(char.name, size=12, weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE,
                        max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(f"{applied}/{total}", size=11, color=ft.Colors.GREY_400),
                ft.Icon(ft.Icons.CHECK_CIRCLE, size=12, color="#81c784",
                        visible=complete),
            ],
            spacing=6,
            tight=True,
        )
        return character_tile(
            char, theme, [name_line],
            on_click=lambda e, i=i: select_character(i),
            width=SIDEBAR_W,
        )

    def build_char_list() -> ft.Control:
        strip = ft.Container(
            bgcolor=_BOARD_BG,
            border_radius=0,
            content=ft.Column(
                [char_tile(i, c) for i, c in enumerate(characters)],
                spacing=0,  # edges touch: the whole strip reads as one piece
                tight=True,
            ),
        )
        return ft.Stack(
            [
                ft.Column([strip], scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Container(content=tape_strip(92, -2.5), top=-10, left=65),
            ],
            expand=True,
            clip_behavior=ft.ClipBehavior.NONE,
        )

    # ---- sidebar: selected character card -----------------------------------

    def build_char_card(char) -> ft.Control:
        applied, total = ctx.album.character_progress(char.id)
        lines: list[ft.Control] = [
            ft.Row(
                [
                    ft.Text(char.name, size=15, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text(f"{applied}/{total}", size=12, color=ft.Colors.GREY_400),
                ],
                spacing=8,
                tight=True,
            ),
        ]
        if spicy_on:
            s_applied, s_total = ctx.album.spicy_character_progress(char.id)
            if s_total:
                lines.append(ft.Text(f"🌶️ {s_applied} / {s_total}", size=11,
                                     color=_SPICY_COLOR))
        return ft.Column(
            [
                character_card(char, theme, lines, width=SIDEBAR_W),
                outline_button("ALL CHARACTERS",
                               lambda e: back_to_overview(),
                               icon=ft.Icons.ARROW_BACK),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        )

    # ---- grids ----------------------------------------------------------------

    def on_slot_tap(sticker):
        character = ctx.characters.get(sticker.character_id)
        open_sticker_dialog(
            page, ctx.album, sticker, character, on_change=on_applied, vice=ctx.vice
        )

    def make_slot(s, w: float, h: float) -> ft.Control:
        slot = build_sticker_slot(ctx.album, s, on_slot_tap, width=w, height=h)
        if state["stamp"] == s.id:
            # Freshly applied: start big, tilted, and translucent, then settle
            # into place like a sticker being pressed onto the page.
            slot.scale = 1.35
            slot.opacity = 0.3
            slot.rotate = ft.Rotate(-0.06, alignment=ft.alignment.center)
            slot.animate_scale = ft.Animation(420, ft.AnimationCurve.EASE_OUT_BACK)
            slot.animate_opacity = ft.Animation(300, ft.AnimationCurve.EASE_OUT)
            slot.animate_rotation = ft.Animation(420, ft.AnimationCurve.EASE_OUT_BACK)
            state["stamp_control"] = slot
        return slot

    def spicy_header(applied: int, total: int) -> ft.Control:
        # Rendered on the white board, so text needs dark-on-light colors.
        return ft.Row(
            [
                ft.Text("🌶️", size=18),
                ft.Text("SPICY STICKERS", size=14, font_family=DISPLAY_FONT,
                        weight=ft.FontWeight.W_700, color=_SPICY_COLOR),
                ft.Text(f"{applied} / {total}", size=12,
                        font_family=META_FONT, color=INK_SOFT),
                ft.Container(content=dashed_rule(320), expand=True),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def board(sections: list[ft.Control]) -> ft.Control:
        """The big white board the stickers are placed on. Sticker edges and
        the board share the same white, so vignettes blend together."""
        sheet = ft.Container(
            bgcolor=_BOARD_BG,
            border_radius=0,
            padding=ft.padding.only(left=18, right=18, top=20, bottom=20),
            shadow=PAPER_SHADOW,
            content=ft.Column(sections, spacing=22),
        )
        return ft.Stack(
            [sheet, ft.Container(content=tape_strip(), top=-10, left=44)],
            clip_behavior=ft.ClipBehavior.NONE,
        )

    def build_overview_grid() -> list[ft.Control]:
        stickers = ctx.stickers.list_by_collection(collection_id, spicy=False)
        # spacing 0: white vignette edges touch and blend into one surface
        sections: list[ft.Control] = [
            ft.Row([make_slot(s, OVER_SLOT_W, OVER_SLOT_H) for s in stickers],
                   wrap=True, spacing=0, run_spacing=0),
        ]
        if spicy_on:
            spicy = ctx.stickers.list_by_collection(collection_id, spicy=True)
            if spicy:
                applied = sum(1 for s in spicy if ctx.album.applied_style(s.id))
                sections.append(spicy_header(applied, len(spicy)))
                sections.append(
                    ft.Row([make_slot(s, OVER_SLOT_W, OVER_SLOT_H) for s in spicy],
                           wrap=True, spacing=0, run_spacing=0)
                )
        return [board(sections)]

    def build_character_grid(char) -> list[ft.Control]:
        stickers = ctx.stickers.list_by_character(char.id, spicy=False)
        sections: list[ft.Control] = [
            ft.Row([make_slot(s, CHAR_SLOT_W, CHAR_SLOT_H) for s in stickers],
                   wrap=True, spacing=0, run_spacing=0),
        ]
        if spicy_on:
            spicy = ctx.stickers.list_by_character(char.id, spicy=True)
            if spicy:
                s_applied, s_total = ctx.album.spicy_character_progress(char.id)
                sections.append(spicy_header(s_applied, s_total))
                sections.append(
                    ft.Row([make_slot(s, CHAR_SLOT_W, CHAR_SLOT_H) for s in spicy],
                           wrap=True, spacing=0, run_spacing=0)
                )
        return [board(sections)]

    # ---- refresh / navigation ---------------------------------------------------

    def refresh_content():
        ci = state["char"]
        col_applied, col_total = ctx.album.collection_progress(collection_id)
        if ci is None:
            title_text.value = collection.name
            subtitle_text.value = collection.description
            progress_text.value = f"{col_applied} / {col_total} stickers"
            progress_bar.content = paper_progress(
                col_applied / col_total if col_total else 0, width=220
            )
            grid.controls = build_overview_grid()
            sidebar.content = build_char_list()
        else:
            char = characters[ci]
            applied, total = ctx.album.character_progress(char.id)
            title_text.value = char.name
            subtitle_text.value = char.description
            progress_text.value = f"{applied} / {total} applied"
            progress_bar.content = paper_progress(
                applied / total if total else 0, width=220
            )
            grid.controls = build_character_grid(char)
            sidebar.content = build_char_card(char)
        page.update()
        if state["stamp"] is not None:
            state["stamp"] = None
            page.run_task(_settle_stamp)

    async def _settle_stamp():
        # A beat after the slot is on the page, release it to its resting
        # pose; flet animates the transition.
        await asyncio.sleep(0.06)
        slot = state["stamp_control"]
        state["stamp_control"] = None
        if slot is None or slot.page is None:
            return
        slot.scale = 1.0
        slot.opacity = 1.0
        slot.rotate = ft.Rotate(0, alignment=ft.alignment.center)
        try:
            slot.update()
        except Exception:
            pass  # view was torn down mid-animation
            return

    def on_applied(sticker):
        state["stamp"] = sticker.id
        page.run_task(play_stamp_then, page, sticker.sound)
        refresh_content()

    async def _slide_to(target: int | None):
        if state["sliding"]:
            return
        state["sliding"] = True
        try:
            sidebar.offset = ft.Offset(-1.15, 0)
            sidebar.update()
            await asyncio.sleep(0.26)
            state["char"] = target
            sidebar.offset = ft.Offset(0, 0)
            refresh_content()  # rebuilds sidebar content for the new mode
        finally:
            state["sliding"] = False

    def select_character(i: int):
        if state["char"] != i:
            page.run_task(_slide_to, i)

    def back_to_overview():
        if state["char"] is not None:
            page.run_task(_slide_to, None)

    def on_back(e):
        if state["char"] is not None:
            back_to_overview()
        else:
            nav.go_collections()

    # ---- initial build -------------------------------------------------------------

    refresh_content()

    return ft.Column(
        [
            ft.Row(
                [
                    tool_button("←", on_back, "Back"),
                    ft.Column([title_text, subtitle_text], spacing=2, tight=True,
                              expand=True),
                    ft.Column(
                        [progress_text, progress_bar],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        tight=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [sidebar, grid],
                spacing=18,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=14,
        expand=True,
    )
