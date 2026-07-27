import flet as ft
from components.theme import DISPLAY_FONT, INK, INK_SOFT


def empty_state(icon: str, title: str, subtitle: str = "") -> ft.Control:
    items: list[ft.Control] = [
        ft.Icon(icon, size=48, color="#2f261866"),
        ft.Text(title.upper(), size=16, color=INK, font_family=DISPLAY_FONT,
                weight=ft.FontWeight.W_700),
    ]
    if subtitle:
        items.append(
            ft.Text(subtitle, size=13, color=INK_SOFT)
        )
    return ft.Container(
        content=ft.Column(
            items,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
            tight=True,
        ),
        alignment=ft.alignment.center,
        padding=32,
    )
