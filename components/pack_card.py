from typing import Callable

import flet as ft

from components.theme import PANEL_BG, PANEL_BORDER

from components.placeholders import cover_band
from models.catalog import Pack
from models.money import format_money


def pack_card(
    pack: Pack,
    collection_name: str,
    theme_color: str | None,
    on_open: Callable[[], None],
    spicy_enabled: bool = False,
) -> ft.Control:
    details = [f"{pack.sticker_count} stickers"]
    if pack.foil_rate > 0:
        details.append(f"{pack.foil_rate:.0%} foil chance")
    if spicy_enabled and pack.spicy_rate > 0:
        details.append(f"🌶️ {pack.spicy_rate:.0%}")
    width = 300.0
    return ft.Container(
        width=width,
        bgcolor=PANEL_BG,
        border_radius=14,
        border=ft.border.all(1, PANEL_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            [
                # Widescreen 16:9 pack art, matching the collection covers.
                cover_band(pack.image, theme_color, height=width * 9 / 16),
                ft.Container(
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(pack.name, size=17, weight=ft.FontWeight.BOLD),
                            ft.Text(collection_name, size=12, color=theme_color or ft.Colors.GREY_400),
                            ft.Text(
                                pack.description, size=12, color=ft.Colors.GREY_400,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(" · ".join(details), size=12, color=ft.Colors.GREY_500),
                            ft.Row(
                                [
                                    ft.Text(
                                        format_money(pack.price), size=18,
                                        weight=ft.FontWeight.BOLD, color="#81c784",
                                    ),
                                    ft.Container(expand=True),
                                    ft.FilledButton(
                                        "Deposit & open",
                                        icon=ft.Icons.SAVINGS,
                                        on_click=lambda e: on_open(),
                                    ),
                                ],
                            ),
                        ],
                        spacing=8,
                    ),
                ),
            ],
            spacing=0,
        ),
    )
