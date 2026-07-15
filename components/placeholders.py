"""Styled placeholder art used whenever a catalog image file is absent."""

import flet as ft

from components.assets import resolve_image
from models.catalog import Character, Sticker
from models.rarity import RARITY_COLORS

_DARK = "#14141c"


def sticker_art(sticker: Sticker, width: float, height: float) -> ft.Control:
    """Sticker artwork or a rarity-tinted placeholder, aspect preserved."""
    src = resolve_image(sticker.image)
    if src:
        return ft.Image(
            src=src, width=width, height=height,
            fit=ft.ImageFit.CONTAIN, border_radius=8,
        )
    color = RARITY_COLORS.get(sticker.rarity, "#9e9e9e")
    return ft.Container(
        width=width,
        height=height,
        border_radius=8,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.with_opacity(0.55, color), _DARK],
        ),
        alignment=ft.alignment.center,
        content=ft.Column(
            [
                ft.Text(
                    f"#{sticker.number:02d}",
                    size=min(width, height) * 0.28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                ),
                ft.Text(
                    sticker.name,
                    size=11,
                    text_align=ft.TextAlign.CENTER,
                    color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE),
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


def character_portrait(
    character: Character, size: float = 64, color: str | None = None
) -> ft.Control:
    """Circular portrait or an initials placeholder."""
    src = resolve_image(character.portrait_image)
    if src:
        return ft.Container(
            width=size, height=size, border_radius=size / 2,
            content=ft.Image(src=src, fit=ft.ImageFit.COVER),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )
    initials = "".join(w[0] for w in character.name.split()[:2]).upper()
    tint = color or "#5c6bc0"
    return ft.Container(
        width=size,
        height=size,
        border_radius=size / 2,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[ft.Colors.with_opacity(0.8, tint), _DARK],
        ),
        alignment=ft.alignment.center,
        content=ft.Text(
            initials, size=size * 0.36, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE
        ),
    )


def cover_band(image: str | None, color: str | None, height: float = 90) -> ft.Control:
    """Collection/pack cover image or a theme-colored gradient band."""
    src = resolve_image(image)
    if src:
        return ft.Image(src=src, height=height, fit=ft.ImageFit.COVER, expand=True)
    tint = color or "#455a64"
    return ft.Container(
        height=height,
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.Colors.with_opacity(0.85, tint), _DARK],
        ),
    )
