from typing import Callable

import flet as ft

from components.paper import PAPER_SHADOW, dashed_rule, ink_button
from components.placeholders import cover_band
from components.theme import CARD_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from models.catalog import Pack
from models.money import format_money


def _crimp(width: float) -> ft.Control:
    return ft.Container(
        height=18,
        content=ft.Stack(
            [
                ft.Row(
                    [
                        ft.Container(width=5, height=5, bgcolor="#2f26184d")
                        for _ in range(3)
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(content=dashed_rule(width - 20), bottom=0, left=0),
            ],
            expand=True,
            alignment=ft.alignment.center,
        ),
    )


def pack_card(
    pack: Pack,
    collection_name: str,
    theme_color: str | None,
    on_open: Callable[[], None],
    spicy_enabled: bool = False,
) -> ft.Control:
    details = [f"{pack.sticker_count} stickers"]
    if pack.foil_rate > 0:
        details.append(f"{pack.foil_rate:.0%} foil")
    if spicy_enabled and pack.spicy_rate > 0:
        details.append(f"🌶️ {pack.spicy_rate:.0%}")
    width = 298.0
    inner = width - 20
    return ft.Container(
        width=width,
        bgcolor=CARD_BG,
        padding=10,
        shadow=PAPER_SHADOW,
        content=ft.Column(
            [
                _crimp(inner),
                cover_band(pack.image, theme_color, height=inner * 9 / 16),
                ft.Container(
                    padding=ft.padding.only(left=6, right=6, top=12, bottom=5),
                    content=ft.Column(
                        [
                            ft.Text(pack.name, size=16, font_family=DISPLAY_FONT,
                                    weight=ft.FontWeight.W_700, color=INK),
                            ft.Text(collection_name, size=11, font_family=META_FONT,
                                    color=INK_SOFT),
                            ft.Text(pack.description, size=11, font_family=META_FONT,
                                    color=INK_SOFT, max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                            dashed_rule(inner - 12),
                            ft.Text(" · ".join(details), size=11,
                                    font_family=META_FONT, color=INK_SOFT),
                            ft.Row(
                                [
                                    ft.Container(
                                        border=ft.border.all(2, "#2f26188c"),
                                        padding=ft.padding.symmetric(
                                            horizontal=9, vertical=7
                                        ),
                                        rotate=ft.Rotate(-0.035),
                                        content=ft.Text(
                                            format_money(pack.price),
                                            size=15,
                                            font_family=DISPLAY_FONT,
                                            weight=ft.FontWeight.W_900,
                                            color=INK,
                                        ),
                                    ),
                                    ft.Container(expand=True),
                                    ink_button(
                                        "DEPOSIT & OPEN",
                                        lambda e: on_open(),
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=8,
                    ),
                ),
            ],
            spacing=0,
        ),
    )
