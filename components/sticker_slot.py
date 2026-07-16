"""Album sticker slot: renders the missing / owned / applied states."""

from typing import Callable

import flet as ft

from components.placeholders import sticker_art
from components.rarity_chip import rarity_chip
from models.catalog import Sticker
from models.rarity import RARITY_COLORS
from services.album_service import APPLIED, OWNED, AlbumService

SLOT_W = 148.0
SLOT_H = 208.0

_SLOT_BG = "#191922"
_FOIL_GOLD = "#ffd54f"


def _badge(text: str, color: str) -> ft.Control:
    return ft.Container(
        content=ft.Text(text, size=9, weight=ft.FontWeight.BOLD, color="#101014"),
        bgcolor=color,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=6, vertical=2),
    )


def build_sticker_slot(
    album: AlbumService,
    sticker: Sticker,
    on_tap: Callable[[Sticker], None],
    width: float = SLOT_W,
    height: float = SLOT_H,
) -> ft.Container:
    state = album.slot_state(sticker.id)
    rarity_color = RARITY_COLORS.get(sticker.rarity, "#9e9e9e")
    # Scale the typography gently with the slot size so bigger slots read
    # bigger, with the artwork staying the dominant element.
    k = max(1.0, width / SLOT_W)
    art_w, art_h = width - 24, height - 74 * k**0.5
    label_size = round(11 * k**0.5)
    chip_size = round(8 * k**0.5)

    badges: list[ft.Control] = []
    if sticker.spicy:
        badges.append(_badge("🌶️", "#ff7043"))
    if state == APPLIED:
        style = album.applied_style(sticker.id)
        body: ft.Control = ft.Column(
            [
                sticker_art(sticker, art_w, art_h),
                ft.Text(
                    sticker.name, size=label_size, text_align=ft.TextAlign.CENTER,
                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS,
                    color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                ),
                rarity_chip(sticker.rarity, size=chip_size),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )
        border_color = _FOIL_GOLD if style == "foil" else ft.Colors.with_opacity(0.9, rarity_color)
        if style == "foil":
            badges.append(_badge("FOIL ✨", _FOIL_GOLD))
        dups = album.duplicate_count(sticker.id)
        if dups > 0:
            badges.append(_badge(f"+{dups}", "#b0bec5"))
    elif state == OWNED:
        # Owned but not pasted: show a sticker "back", never the artwork
        # as if it were already in the album.
        body = ft.Column(
            [
                ft.Container(
                    width=art_w,
                    height=art_h,
                    border_radius=8,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_center,
                        end=ft.alignment.bottom_center,
                        colors=[ft.Colors.with_opacity(0.35, rarity_color), "#101018"],
                    ),
                    alignment=ft.alignment.center,
                    content=ft.Icon(
                        ft.Icons.STICKY_NOTE_2_OUTLINED,
                        size=40 * k,
                        color=ft.Colors.with_opacity(0.8, rarity_color),
                    ),
                ),
                ft.Text(sticker.id, size=label_size, color=ft.Colors.GREY_400),
                rarity_chip(sticker.rarity, size=chip_size),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )
        border_color = "#ffb300"
        badges.append(_badge("READY TO APPLY", "#ffb300"))
    else:  # missing
        body = ft.Column(
            [
                ft.Container(
                    width=art_w,
                    height=art_h,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.25, rarity_color)),
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        f"#{sticker.number:02d}",
                        size=26 * k,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                    ),
                ),
                ft.Text(sticker.id, size=label_size, color=ft.Colors.GREY_600),
                rarity_chip(sticker.rarity, size=chip_size),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )
        border_color = ft.Colors.with_opacity(0.35, rarity_color)

    return ft.Container(
        width=width,
        height=height,
        bgcolor=_SLOT_BG,
        border=ft.border.all(2, border_color),
        border_radius=12,
        padding=ft.padding.only(left=10, right=10, top=12, bottom=8),
        on_click=lambda e: on_tap(sticker),
        ink=True,
        content=ft.Stack(
            [
                ft.Container(content=body, alignment=ft.alignment.center),
                ft.Row(badges, alignment=ft.MainAxisAlignment.END, spacing=4,
                       top=0, right=0) if badges else ft.Container(),
            ],
            expand=True,
        ),
        tooltip=f"{sticker.name} · {sticker.rarity}",
    )
