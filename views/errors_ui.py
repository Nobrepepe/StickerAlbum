"""Concise user-facing error reporting (no tracebacks in the UI)."""

import flet as ft


def show_error(page: ft.Page, message: str) -> None:
    page.open(ft.SnackBar(ft.Text(message), bgcolor="#b71c1c"))


def show_info(page: ft.Page, message: str) -> None:
    page.open(ft.SnackBar(ft.Text(message)))
