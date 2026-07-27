from typing import Callable

import flet as ft

from components.paper import PAPER_SHADOW, ink_button, paper_progress, tool_button
from components.placeholders import cover_band
from components.theme import CARD_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from models.catalog import Collection


def collection_card(
    collection: Collection,
    applied: int,
    total: int,
    chars_done: int,
    chars_total: int,
    on_open: Callable[[], None],
    on_revert: Callable[[], None] | None = None,
    on_edit: Callable[[], None] | None = None,
) -> ft.Control:
    width = 328.0
    body_width = width - 20
    return ft.Container(
        width=width,
        bgcolor=CARD_BG,
        padding=10,
        shadow=PAPER_SHADOW,
        content=ft.Column(
            [
                cover_band(collection.cover_image, collection.theme_color,
                           height=body_width * 9 / 16),
                ft.Container(
                    padding=ft.padding.only(left=6, right=6, top=12, bottom=4),
                    content=ft.Column(
                        [
                            ft.Text(
                                collection.name,
                                size=17,
                                font_family=DISPLAY_FONT,
                                weight=ft.FontWeight.W_700,
                                color=INK,
                            ),
                            ft.Text(
                                collection.description,
                                size=11.5,
                                font_family=META_FONT,
                                color=INK_SOFT,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                height=34,
                            ),
                            ft.Row(
                                [
                                    ft.Text(
                                        str(applied),
                                        size=18,
                                        font_family=DISPLAY_FONT,
                                        weight=ft.FontWeight.W_900,
                                        color=INK,
                                    ),
                                    ft.Text(
                                        f"of {total} pasted · chars "
                                        f"{chars_done}/{chars_total}",
                                        size=11,
                                        font_family=META_FONT,
                                        color=INK_SOFT,
                                        expand=True,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            paper_progress(applied / total if total else 0,
                                           width=body_width - 12),
                            ft.Row(
                                [
                                    ink_button(
                                        "OPEN ALBUM",
                                        lambda e: on_open(),
                                    ),
                                    ft.Container(expand=True),
                                    tool_button(
                                        "ed",
                                        lambda e: on_edit(),
                                        "Hot-edit live: names, images, "
                                        "sounds — progress is kept",
                                    ) if on_edit else ft.Container(),
                                    tool_button(
                                        "un",
                                        lambda e: on_revert(),
                                        "Revert to draft for editing "
                                        "(erases this collection's progress)",
                                    ) if on_revert else ft.Container(),
                                ],
                                spacing=7,
                            ),
                        ],
                        spacing=9,
                    ),
                ),
            ],
            spacing=0,
        ),
    )
