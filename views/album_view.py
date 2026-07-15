import flet as ft

from components.placeholders import character_portrait
from components.sticker_dialog import open_sticker_dialog
from components.sticker_slot import build_sticker_slot


def build_album(page: ft.Page, ctx, nav, collection_id: str) -> ft.Control:
    collection = ctx.collections.get(collection_id)
    characters = ctx.characters.list_by_collection(collection_id)
    theme = collection.theme_color or "#7c4dff"
    spicy_on = ctx.settings.state.spicy_enabled

    selected = {"index": 0}

    # Containers refreshed in place after selection changes or applies.
    char_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
    header = ft.Container()
    grid = ft.Row(wrap=True, spacing=12, run_spacing=12)
    spicy_section = ft.Column(spacing=10, visible=False)
    collection_progress_text = ft.Text(size=13, color=ft.Colors.GREY_300)
    collection_progress_bar = ft.ProgressBar(
        color=theme, bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE), width=220
    )

    def char_tile(i: int, char) -> ft.Control:
        applied, total = ctx.album.character_progress(char.id)
        is_selected = i == selected["index"]
        complete = total > 0 and applied == total
        return ft.Container(
            bgcolor=ft.Colors.with_opacity(0.18, theme) if is_selected else None,
            border_radius=10,
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            on_click=lambda e, i=i: select(i),
            ink=True,
            content=ft.Row(
                [
                    character_portrait(char, 36, theme),
                    ft.Column(
                        [
                            ft.Text(char.name, size=13,
                                    weight=ft.FontWeight.BOLD if is_selected else None,
                                    max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(f"{applied} / {total}", size=11, color=ft.Colors.GREY_400),
                        ],
                        spacing=1,
                        tight=True,
                        expand=True,
                    ),
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="#81c784")
                    if complete else ft.Container(width=16),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    def on_slot_tap(sticker):
        character = ctx.characters.get(sticker.character_id)
        open_sticker_dialog(page, ctx.album, sticker, character, on_change=refresh)

    def refresh():
        char = characters[selected["index"]]
        applied, total = ctx.album.character_progress(char.id)
        header.content = ft.Row(
            [
                character_portrait(char, 72, theme),
                ft.Column(
                    [
                        ft.Text(char.name, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(char.description, size=12, color=ft.Colors.GREY_400,
                                max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Row(
                            [
                                ft.ProgressBar(
                                    value=applied / total if total else 0,
                                    width=180, color=theme,
                                    bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                                ),
                                ft.Text(f"{applied} / {total} applied",
                                        size=12, color=ft.Colors.GREY_300),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                    expand=True,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        grid.controls = [
            build_sticker_slot(ctx.album, s, on_slot_tap)
            for s in ctx.stickers.list_by_character(char.id, spicy=False)
        ]
        spicy_stickers = (
            ctx.stickers.list_by_character(char.id, spicy=True) if spicy_on else []
        )
        spicy_section.visible = bool(spicy_stickers)
        if spicy_stickers:
            s_applied, s_total = ctx.album.spicy_character_progress(char.id)
            spicy_section.controls = [
                ft.Row(
                    [
                        ft.Text("🌶️", size=18),
                        ft.Text("Spicy stickers", size=14, weight=ft.FontWeight.BOLD,
                                color="#ff7043"),
                        ft.Text(f"{s_applied} / {s_total}", size=12,
                                color=ft.Colors.GREY_400),
                        ft.Container(
                            content=ft.Divider(height=1, color="#3a2a26"), expand=True
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [build_sticker_slot(ctx.album, s, on_slot_tap) for s in spicy_stickers],
                    wrap=True, spacing=12, run_spacing=12,
                ),
            ]
        char_list.controls = [char_tile(i, c) for i, c in enumerate(characters)]
        col_applied, col_total = ctx.album.collection_progress(collection_id)
        collection_progress_text.value = f"{col_applied} / {col_total} stickers"
        collection_progress_bar.value = col_applied / col_total if col_total else 0
        page.update()

    def select(i: int):
        selected["index"] = i
        refresh()

    refresh()

    return ft.Column(
        [
            ft.Row(
                [
                    ft.IconButton(ft.Icons.ARROW_BACK, tooltip="Back to collections",
                                  on_click=lambda e: nav.go_collections()),
                    ft.Text(collection.name, size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Column(
                        [collection_progress_text, collection_progress_bar],
                        spacing=4,
                        horizontal_alignment=ft.CrossAxisAlignment.END,
                        tight=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    ft.Container(
                        width=230,
                        bgcolor="#15151d",
                        border_radius=12,
                        padding=8,
                        content=char_list,
                    ),
                    ft.Column(
                        [header,
                         ft.Column([grid, spicy_section],
                                   scroll=ft.ScrollMode.AUTO, expand=True, spacing=16)],
                        spacing=16,
                        expand=True,
                    ),
                ],
                spacing=16,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ],
        spacing=14,
        expand=True,
    )
