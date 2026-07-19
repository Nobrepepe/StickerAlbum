import flet as ft

from components.collection_card import collection_card


def build_collections(page: ft.Page, ctx, nav) -> ft.Control:
    cards = []
    for collection in ctx.collections.list_all():
        applied, total = ctx.album.collection_progress(collection.id)
        chars_done, chars_total = ctx.album.completed_characters(collection.id)
        cards.append(
            collection_card(
                collection, applied, total, chars_done, chars_total,
                on_open=lambda cid=collection.id: nav.go_album(cid),
            )
        )
    return ft.Column(
        [
            ft.Text("Collections", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("Pick a world and start filling its album.",
                    size=13, color=ft.Colors.GREY_400),
            ft.Row(cards, wrap=True, spacing=16, run_spacing=16),
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
