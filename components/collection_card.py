from typing import Callable

import flet as ft

from components.theme import PANEL_BG, PANEL_BORDER

from components.placeholders import cover_band
from models.catalog import Collection


def collection_card(
    collection: Collection,
    applied: int,
    total: int,
    chars_done: int,
    chars_total: int,
    on_open: Callable[[], None],
    on_revert: Callable[[], None] | None = None,
) -> ft.Control:
    pct = (applied / total * 100) if total else 0.0
    width = 330.0
    return ft.Container(
        width=width,
        bgcolor=PANEL_BG,
        border_radius=14,
        border=ft.border.all(1, PANEL_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Column(
            [
                # Widescreen 16:9 cover so the collection art is the hero.
                cover_band(collection.cover_image, collection.theme_color,
                           height=width * 9 / 16),
                ft.Container(
                    padding=16,
                    content=ft.Column(
                        [
                            ft.Text(collection.name, size=18, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                collection.description, size=12,
                                color=ft.Colors.GREY_400, max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Row(
                                [
                                    ft.Text(f"{applied} / {total}", size=14,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{pct:.0f}%", size=13, color=ft.Colors.GREY_400),
                                    ft.Container(expand=True),
                                    ft.Text(
                                        f"Characters {chars_done} / {chars_total}",
                                        size=12, color=ft.Colors.GREY_400,
                                    ),
                                ],
                            ),
                            ft.ProgressBar(
                                value=(applied / total) if total else 0,
                                color=collection.theme_color or "#7c4dff",
                                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                            ),
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        "Open album",
                                        icon=ft.Icons.MENU_BOOK,
                                        on_click=lambda e: on_open(),
                                    ),
                                    ft.Container(expand=True),
                                    ft.IconButton(
                                        ft.Icons.EDIT_NOTE,
                                        tooltip="Revert to draft for editing "
                                                "(erases this collection's progress)",
                                        icon_color=ft.Colors.GREY_400,
                                        on_click=lambda e: on_revert(),
                                        visible=on_revert is not None,
                                    ),
                                ],
                            ),
                        ],
                        spacing=10,
                    ),
                ),
            ],
            spacing=0,
        ),
    )
