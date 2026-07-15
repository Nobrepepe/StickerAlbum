import flet as ft


def empty_state(icon: str, title: str, subtitle: str = "") -> ft.Control:
    items: list[ft.Control] = [
        ft.Icon(icon, size=48, color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
        ft.Text(title, size=16, color=ft.Colors.with_opacity(0.8, ft.Colors.WHITE)),
    ]
    if subtitle:
        items.append(
            ft.Text(subtitle, size=13, color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE))
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
