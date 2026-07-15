import flet as ft

from components.placeholders import sticker_art
from components.rarity_chip import rarity_chip
from models.money import format_money
from models.rarity import RARITY_COLORS
from models.results import PackOpenResult

_FOIL_GOLD = "#ffd54f"


def _result_badge(text: str, color: str) -> ft.Control:
    return ft.Container(
        content=ft.Text(text, size=11, weight=ft.FontWeight.BOLD, color="#101014"),
        bgcolor=color,
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )


def build_pack_result(page: ft.Page, ctx, nav, result: PackOpenResult) -> ft.Control:
    """The pack is already opened and saved; this view only reveals it."""
    items = result.items
    state = {"index": 0}

    def item_card(i: int) -> ft.Control:
        item = items[i]
        character = ctx.characters.get(item.sticker.character_id)
        badges = [
            _result_badge("NEW", "#81c784") if item.is_new
            else _result_badge("DUPLICATE", "#b0bec5"),
        ]
        if item.style == "foil":
            badges.append(_result_badge("FOIL ✨", _FOIL_GOLD))
        if item.sticker.spicy:
            badges.append(_result_badge("SPICY 🌶️", "#ff7043"))
        border = _FOIL_GOLD if item.style == "foil" else ft.Colors.with_opacity(
            0.8, RARITY_COLORS.get(item.sticker.rarity, "#9e9e9e"))
        return ft.Container(
            key=str(i),  # forces AnimatedSwitcher to treat each card as new
            width=320,
            bgcolor="#191922",
            border=ft.border.all(2, border),
            border_radius=16,
            padding=18,
            content=ft.Column(
                [
                    ft.Row(badges, alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                    sticker_art(item.sticker, 260, 280),
                    ft.Text(item.sticker.name, size=16, weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER),
                    ft.Text(character.name, size=13, color=ft.Colors.GREY_400),
                    ft.Row(
                        [rarity_chip(item.sticker.rarity),
                         ft.Text("Foil ✨" if item.style == "foil" else "Normal",
                                 size=12, color=ft.Colors.GREY_300)],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                tight=True,
            ),
        )

    switcher = ft.AnimatedSwitcher(
        content=item_card(0),
        transition=ft.AnimatedSwitcherTransition.SCALE,
        duration=350,
        reverse_duration=100,
    )
    position = ft.Text(f"1 / {len(items)}", size=14, color=ft.Colors.GREY_300)

    # Progress dots, colored by rarity once revealed.
    dots = ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=6)

    reveal_next_btn = ft.FilledButton("Reveal next", icon=ft.Icons.NAVIGATE_NEXT)
    reveal_all_btn = ft.OutlinedButton("Reveal all", icon=ft.Icons.UNFOLD_MORE)
    continue_btn = ft.FilledButton("Continue to shop", icon=ft.Icons.STOREFRONT,
                                   visible=False,
                                   on_click=lambda e: nav.go_shop())
    album_btn = ft.FilledTonalButton(
        "Open album", icon=ft.Icons.MENU_BOOK, visible=False,
        on_click=lambda e: nav.go_album(result.pack.collection_id),
    )

    def render():
        i = state["index"]
        switcher.content = item_card(i)
        position.value = f"{i + 1} / {len(items)}"
        dots.controls = [
            ft.Container(
                width=12, height=12, border_radius=6,
                bgcolor=RARITY_COLORS.get(items[j].sticker.rarity, "#9e9e9e")
                if j <= i else ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            )
            for j in range(len(items))
        ]
        done = i >= len(items) - 1
        reveal_next_btn.visible = not done
        reveal_all_btn.visible = not done
        continue_btn.visible = done
        album_btn.visible = done
        page.update()

    def reveal_next(e):
        if state["index"] < len(items) - 1:
            state["index"] += 1
            render()

    def reveal_all(e):
        state["index"] = len(items) - 1
        render()

    reveal_next_btn.on_click = reveal_next
    reveal_all_btn.on_click = reveal_all
    render()

    new_count = sum(1 for it in items if it.is_new)
    return ft.Column(
        [
            ft.Text(f"Opening: {result.pack.name}", size=22, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"{format_money(result.deposit)} added to your savings · "
                f"{new_count} new, {len(items) - new_count} duplicate",
                size=13, color=ft.Colors.GREY_400,
            ),
            ft.Container(content=switcher, alignment=ft.alignment.center),
            position,
            dots,
            ft.Row(
                [reveal_next_btn, reveal_all_btn, continue_btn, album_btn],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=12,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=14,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
