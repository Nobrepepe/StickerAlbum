import flet as ft

from models.rarity import RARITY_COLORS, RARITY_LABELS


def rarity_chip(rarity: str, size: int = 10) -> ft.Control:
    color = RARITY_COLORS.get(rarity, "#9e9e9e")
    return ft.Container(
        content=ft.Text(
            RARITY_LABELS.get(rarity, rarity).upper(),
            size=size,
            weight=ft.FontWeight.BOLD,
            color=color,
        ),
        border=ft.border.all(1, ft.Colors.with_opacity(0.6, color)),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        bgcolor=ft.Colors.with_opacity(0.12, color),
    )
