"""Character tile (16:9 landscape) and card (9:16 portrait) builders.

Both are meant to sit on white boards: the art's vignette edges blend into
the board, and metadata floats on small dark signs so nothing covers the
white-edge effect. Backgrounds come from the convention-named files
portraits/<CHARACTER_ID>_tile.png and portraits/<CHARACTER_ID>_card.png,
falling back to a theme gradient with the character's name.
"""

from typing import Callable

import flet as ft

from components.assets import character_card_image, character_tile_image
from components.theme import SIGN_BG

TILE_W = 252.0
TILE_H = TILE_W * 9 / 16
CARD_W = 252.0
CARD_H = CARD_W * 16 / 9

_SIGN_SHADOW = ft.BoxShadow(
    blur_radius=4, color=ft.Colors.with_opacity(0.35, "#000000"),
    offset=ft.Offset(0, 1),
)


def tile_sign(lines: list[ft.Control]) -> ft.Control:
    """Floating dark chip over tile/card art."""
    return ft.Container(
        content=ft.Column(lines, spacing=1, tight=True,
                          horizontal_alignment=ft.CrossAxisAlignment.START),
        bgcolor=ft.Colors.with_opacity(0.82, SIGN_BG),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        shadow=_SIGN_SHADOW,
    )


def _fallback_gradient(theme: str) -> ft.LinearGradient:
    return ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=[ft.Colors.with_opacity(0.6, theme), "#14141c"],
    )


def character_tile(
    char,
    theme: str,
    sign_lines: list[ft.Control],
    on_click: Callable | None = None,
    width: float = TILE_W,
) -> ft.Control:
    src = character_tile_image(char.id)
    return ft.Container(
        width=width,
        height=width * 9 / 16,
        bgcolor="#ffffff",
        on_click=on_click,
        image=ft.DecorationImage(src=src, fit=ft.ImageFit.COVER) if src else None,
        gradient=None if src else _fallback_gradient(theme),
        content=ft.Stack(
            [ft.Container(content=tile_sign(sign_lines), bottom=6, left=6)],
            expand=True,
        ),
    )


def character_card(
    char,
    theme: str,
    sign_lines: list[ft.Control],
    width: float = CARD_W,
) -> ft.Control:
    src = character_card_image(char.id)
    layers: list[ft.Control] = []
    if not src:
        layers.append(ft.Container(
            alignment=ft.alignment.center,
            content=ft.Text(char.name, size=20, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                            text_align=ft.TextAlign.CENTER),
            padding=16,
        ))
    layers.append(ft.Container(content=tile_sign(sign_lines), bottom=8, left=8))
    return ft.Container(
        width=width,
        height=width * 16 / 9,
        bgcolor="#ffffff",
        border_radius=14,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        image=ft.DecorationImage(src=src, fit=ft.ImageFit.COVER) if src else None,
        gradient=None if src else ft.LinearGradient(
            begin=ft.alignment.top_center,
            end=ft.alignment.bottom_center,
            colors=[ft.Colors.with_opacity(0.55, theme), "#101018"],
        ),
        content=ft.Stack(layers, expand=True),
    )
