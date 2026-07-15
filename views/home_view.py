import flet as ft

from components.carousel import StickerCarousel
from components.empty_state import empty_state
from components.placeholders import character_portrait, sticker_art
from components.rarity_chip import rarity_chip
from models.money import format_money


def _stat_tile(icon: str, label: str, value: str, color: str) -> ft.Control:
    return ft.Container(
        width=220,
        bgcolor="#191922",
        border_radius=14,
        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        padding=16,
        content=ft.Row(
            [
                ft.Icon(icon, size=30, color=color),
                ft.Column(
                    [
                        ft.Text(value, size=19, weight=ft.FontWeight.BOLD),
                        ft.Text(label, size=12, color=ft.Colors.GREY_400),
                    ],
                    spacing=2,
                    tight=True,
                ),
            ],
            spacing=14,
        ),
    )


def _favorite_section(page: ft.Page, ctx, nav) -> ft.Control:
    fav = ctx.summary.favorite_info()

    # Dropdown to pick/change the favorite from every character.
    options = []
    for collection in ctx.collections.list_all():
        for char in ctx.characters.list_by_collection(collection.id):
            options.append(
                ft.dropdown.Option(key=char.id, text=f"{collection.name} — {char.name}")
            )

    def on_pick(e):
        ctx.state.set_favorite_character(e.control.value or None)
        nav.go_home()

    picker = ft.Dropdown(
        label="Favorite character",
        options=options,
        value=fav.character.id if fav else None,
        on_change=on_pick,
        width=320,
        dense=True,
    )

    if fav is None:
        body: ft.Control = empty_state(
            ft.Icons.FAVORITE_BORDER,
            "No favorite character yet",
            "Pick one above to feature them here.",
        )
    else:
        collection = fav.collection
        if fav.owned_stickers:
            slides: list[ft.Control] = []
            for sticker, styles in fav.owned_stickers:
                caption = sticker.name + (" · Foil ✨ owned" if "foil" in styles else "")
                slides.append(
                    ft.Column(
                        [
                            sticker_art(sticker, 240, 240),
                            ft.Row(
                                [rarity_chip(sticker.rarity, size=9),
                                 ft.Text(caption, size=12, color=ft.Colors.GREY_300,
                                         max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=8,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                        tight=True,
                    )
                )
            gallery: ft.Control = StickerCarousel(slides, interval=5.0)
        else:
            gallery = empty_state(
                ft.Icons.AUTO_AWESOME,
                f"No {fav.character.name} stickers yet",
                "Open some packs — their stickers will show up here.",
            )
        body = ft.Row(
            [
                ft.Column(
                    [
                        character_portrait(fav.character, 96, collection.theme_color),
                        ft.Text(fav.character.name, size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(collection.name, size=13,
                                color=collection.theme_color or ft.Colors.GREY_400),
                        ft.Text(f"Applied {fav.applied} / {fav.total}",
                                size=13, color=ft.Colors.GREY_300),
                        ft.ProgressBar(
                            value=fav.applied / fav.total if fav.total else 0,
                            width=160,
                            color=collection.theme_color or "#7c4dff",
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    tight=True,
                ),
                ft.Container(content=gallery, expand=True, alignment=ft.alignment.center),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=24,
        )

    return ft.Container(
        bgcolor="#191922",
        border_radius=14,
        border=ft.border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        padding=20,
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Favorite character", size=16, weight=ft.FontWeight.BOLD),
                        ft.Container(expand=True),
                        picker,
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                body,
            ],
            spacing=16,
        ),
    )


def build_home(page: ft.Page, ctx, nav) -> ft.Control:
    s = ctx.summary.home_summary()
    return ft.Column(
        [
            ft.Text("My Sticker Album", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("Every pack is a deposit into your savings. Collect, paste, repeat.",
                    size=13, color=ft.Colors.GREY_400),
            ft.Row(
                [
                    _stat_tile(ft.Icons.STYLE, "Unique stickers owned",
                               str(s.unique_owned), "#64b5f6"),
                    _stat_tile(ft.Icons.MENU_BOOK, "Stickers applied",
                               str(s.total_applied), "#81c784"),
                    _stat_tile(ft.Icons.EMOJI_EVENTS, "Collections completed",
                               f"{s.completed_collections} / {s.total_collections}", "#ffd54f"),
                    _stat_tile(ft.Icons.SAVINGS, "Total saved",
                               format_money(s.total_saved), "#4db6ac"),
                ],
                wrap=True,
                spacing=14,
                run_spacing=14,
            ),
            _favorite_section(page, ctx, nav),
            ft.Row(
                [
                    ft.FilledTonalButton(
                        "Browse collections", icon=ft.Icons.COLLECTIONS_BOOKMARK,
                        on_click=lambda e: nav.go_collections(),
                    ),
                    ft.FilledTonalButton(
                        "Go to shop", icon=ft.Icons.STOREFRONT,
                        on_click=lambda e: nav.go_shop(),
                    ),
                ],
                spacing=12,
            ),
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
