"""Styled placeholder art used whenever a catalog image file is absent."""

import flet as ft

from components.assets import resolve_image
from models.catalog import Sticker
from components.theme import CARD_BG, INK, INK_SOFT, META_FONT
from models.rarity import RARITY_PAPER

_DARK = "#6b5842"


def sticker_art(sticker: Sticker, width: float, height: float) -> ft.Control:
    """Sticker artwork or a rarity-tinted placeholder, aspect preserved."""
    src = resolve_image(sticker.image)
    if src:
        return ft.Image(
            src=src, width=width, height=height,
            fit=ft.ImageFit.CONTAIN, border_radius=8,
        )
    paper, edge = RARITY_PAPER.get(sticker.rarity, ("#ffffff", "#c8bda6"))
    return ft.Container(
        width=width,
        height=height,
        border_radius=0,
        bgcolor=paper,
        border=ft.border.all(1, edge),
        alignment=ft.alignment.center,
        content=ft.Column(
            [
                ft.Text(
                    f"#{sticker.number:02d}",
                    size=min(width, height) * 0.28,
                    font_family=META_FONT,
                    color=INK,
                ),
                ft.Text(
                    sticker.name,
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                    font_family=META_FONT,
                    color=INK_SOFT,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        ),
        padding=8,
    )


# (Circular profile portraits were retired: characters are represented by
# their 16:9 tile and 9:16 card art everywhere.)


def cover_band(image: str | None, color: str | None, height: float = 90) -> ft.Control:
    """Collection/pack cover image (filling the band, cropped rather than
    squished) or a theme-colored gradient fallback."""
    src = resolve_image(image)
    if src:
        return ft.Container(
            height=height,
            image=ft.DecorationImage(src=src, fit=ft.ImageFit.COVER),
        )
    tint = color or "#455a64"
    return ft.Container(
        height=height,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.with_opacity(0.85, tint), _DARK],
        ),
    )
