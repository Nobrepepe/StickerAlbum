"""Small controls shared by the Kraft & Tape presentation layer."""

from collections.abc import Callable

import flet as ft

from components.theme import (
    CARD_BG,
    DISPLAY_FONT,
    GOLD,
    INK,
    META_FONT,
    STAMP_RED,
    TAPE,
    TRACK_BG,
)
from models.rarity import RARITY_INK, RARITY_PAPER

CREAM_TEXT = CARD_BG
PAPER_SHADOW = ft.BoxShadow(
    spread_radius=-6,
    blur_radius=16,
    color="#00000061",
    offset=ft.Offset(0, 6),
)
HARD_SHADOW = ft.BoxShadow(
    spread_radius=0,
    blur_radius=0,
    color="#2f261838",
    offset=ft.Offset(3, 3),
)


def _button_text(label: str, size: float = 10, color: str = INK) -> ft.Text:
    return ft.Text(
        label.upper(),
        font_family=DISPLAY_FONT,
        size=size,
        weight=ft.FontWeight.W_700,
        style=ft.TextStyle(letter_spacing=1.2),
        no_wrap=True,
        color=color,
    )


def ink_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    bgcolor: str = INK,
    disabled: bool = False,
    tooltip: str | None = None,
) -> ft.Control:
    content: ft.Control = _button_text(label, color=CREAM_TEXT)
    if icon is not None:
        content = ft.Row(
            [ft.Icon(icon, size=14, color=CREAM_TEXT), content],
            spacing=7,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        )
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        border_radius=0,
        padding=ft.padding.symmetric(horizontal=15, vertical=11),
        shadow=HARD_SHADOW,
        on_click=on_click,
        disabled=disabled,
        opacity=0.45 if disabled else 1,
        tooltip=tooltip,
        ink=not disabled,
    )


def outline_button(
    label: str,
    on_click: Callable | None,
    *,
    icon=None,
    color: str = INK,
    tooltip: str | None = None,
) -> ft.Control:
    content: ft.Control = _button_text(label, 9.5, color)
    if icon is not None:
        content = ft.Row(
            [ft.Icon(icon, size=14, color=color), content],
            spacing=7,
            tight=True,
        )
    return ft.Container(
        content=content,
        border=ft.border.all(1.5, f"{color}73"),
        border_radius=0,
        padding=ft.padding.symmetric(horizontal=12, vertical=9),
        on_click=on_click,
        tooltip=tooltip,
        ink=True,
    )


def tool_button(text: str, on_click: Callable | None, tooltip: str) -> ft.Control:
    control = ft.Container(
        width=32,
        height=32,
        alignment=ft.alignment.center,
        border=ft.border.all(1.5, "#2f261859"),
        border_radius=0,
        content=ft.Text(text, font_family=META_FONT, size=12, color=INK),
        on_click=on_click,
        tooltip=tooltip,
        ink=True,
    )

    def hover(e):
        control.bgcolor = "#2f261817" if e.data == "true" else None
        control.update()

    control.on_hover = hover
    return control


def paper_label(
    text: str,
    rarity: str | None = None,
    *,
    gold: bool = False,
    size: float = 9,
    max_width: float | None = None,
    fill: str | None = None,
) -> ft.Control:
    paper, edge = RARITY_PAPER.get(rarity or "common", ("#ffffff", "#c8bda6"))
    if gold:
        paper, edge = "#f1dfa8", GOLD
    if fill:
        paper = fill
    return ft.Container(
        content=ft.Text(
            text,
            font_family=META_FONT,
            size=size,
            color=RARITY_INK,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        ),
        bgcolor=paper,
        border=ft.border.all(1, edge),
        border_radius=0,
        padding=ft.padding.symmetric(horizontal=6, vertical=3),
        shadow=ft.BoxShadow(
            blur_radius=2, color="#0000002b", offset=ft.Offset(1, 1)
        ),
        width=max_width,
    )


def tape_strip(width: float = 92, angle: float = -2.5) -> ft.Control:
    # Flet 0.28 has no dashed BorderSide. Alternating one-pixel marks create
    # the torn/dashed side impression without introducing an image asset.
    marks = []
    for y in range(2, 23, 4):
        marks.extend(
            [
                ft.Container(left=0, top=y, width=1, height=2, bgcolor="#2f26182b"),
                ft.Container(right=0, top=y, width=1, height=2, bgcolor="#2f26182b"),
            ]
        )
    return ft.Container(
        width=width,
        height=24,
        bgcolor="#f0e6cdd1",
        rotate=ft.Rotate(angle * 3.141592653589793 / 180),
        shadow=ft.BoxShadow(blur_radius=3, color="#00000024", offset=ft.Offset(0, 1)),
        content=ft.Stack(marks),
    )


def dashed_rule(width: float = 240) -> ft.Control:
    count = max(1, int(width // 8))
    return ft.Row(
        [ft.Container(width=4, height=1, bgcolor="#2f261838") for _ in range(count)],
        spacing=4,
        height=1,
        width=width,
    )


def paper_progress(value: float, width: float = 220) -> ft.Control:
    value = min(1.0, max(0.0, value))
    return ft.Container(
        width=width,
        height=9,
        bgcolor=TRACK_BG,
        shadow=ft.BoxShadow(
            blur_radius=2,
            color="#2f261838",
            offset=ft.Offset(0, 1),
            blur_style=ft.ShadowBlurStyle.INNER,
        ),
        content=ft.Container(width=width * value, height=9, bgcolor=INK),
        alignment=ft.alignment.center_left,
    )


def destructive_button(label: str, on_click: Callable | None, *, icon=None) -> ft.Control:
    return ink_button(label, on_click, icon=icon, bgcolor=STAMP_RED)


def page_caption(text: str) -> ft.Control:
    """Quiet typewriter caption used beneath the active binder tab."""
    return ft.Text(
        text,
        size=11,
        font_family=META_FONT,
        color="#2f261880",
    )
