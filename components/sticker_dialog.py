"""Catalogue-slip dialog for inspecting and applying a sticker."""

from typing import Callable

import flet as ft

from components.assets import resolve_image, sticker_mask_image
from components.audio_player import play_sound
from components.foil_shimmer import FoilShimmer
from components.paper import dashed_rule, ink_button, outline_button, paper_label
from components.placeholders import sticker_art
from components.theme import CARD_BG, DISPLAY_FONT, GOLD, INK, INK_SOFT, META_FONT
from models.catalog import Character, Sticker
from models.rarity import RARITY_LABELS
from services.album_service import APPLIED, OWNED, AlbumService
from services.errors import ApplyError, ViceError

_ART_W, _ART_H = 276, 368


def _art_display(sticker: Sticker, foil: bool) -> ft.Control:
    """Return bare art, adding either its mask or a soft fallback foil sheen."""
    src = resolve_image(sticker.image)
    if not src:
        art: ft.Control = sticker_art(sticker, _ART_W, _ART_H)
    else:
        art = ft.Image(
            src=src, width=_ART_W, height=_ART_H, fit=ft.ImageFit.CONTAIN
        )
    layers = [art]
    if foil:
        mask = sticker_mask_image(sticker.id)
        if mask:
            layers.append(FoilShimmer(mask, _ART_W, _ART_H))
        else:
            # Custom collections may predate foil masks. Keep foil selectable
            # and tint the complete artwork instead of silently showing normal.
            layers.append(
                ft.Container(
                    width=_ART_W,
                    height=_ART_H,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=["#fff5c800", "#fff0a273", "#c9a86a24"],
                    ),
                )
            )
    return ft.Stack(layers, width=_ART_W, height=_ART_H)


def open_sticker_dialog(
    page: ft.Page,
    album: AlbumService,
    sticker: Sticker,
    character: Character,
    collection_name: str,
    on_change: Callable[[Sticker], None],
    vice=None,
) -> None:
    """Open the square-cornered catalogue slip used by every sticker board."""
    state = album.slot_state(sticker.id)
    owned = album.owned_styles(sticker.id)
    current_style = album.applied_style(sticker.id)
    selected = {"style": current_style}

    dialog = ft.AlertDialog(
        # Non-modal dialogs are dismissed by tapping their barrier. The
        # barrier remains dark so the slip still reads as an inspection view.
        modal=False,
        bgcolor=CARD_BG,
        shape=ft.RoundedRectangleBorder(radius=0),
        content_padding=ft.padding.symmetric(horizontal=26, vertical=24),
        barrier_color="#0000009e",
    )

    def close(e=None):
        page.close(dialog)

    art_switcher = ft.AnimatedSwitcher(
        content=_art_display(sticker, current_style == "foil"),
        duration=300,
        transition=ft.AnimatedSwitcherTransition.FADE,
    )
    art_board = ft.Container(
        width=296,
        height=388,
        bgcolor="#ffffff",
        padding=10,
        content=art_switcher,
    )

    state_text = "applied" if state == APPLIED else (
        "owned" if state == OWNED else "not collected"
    )
    state_line = ft.Text(
        f"{character.name} · {collection_name} · {state_text}",
        size=11.5,
        font_family=META_FONT,
        color=INK_SOFT,
        max_lines=1,
        overflow=ft.TextOverflow.ELLIPSIS,
    )

    normal_variant: ft.Container
    foil_variant: ft.Container

    def paint_variants() -> None:
        for style, control in (
            ("normal", normal_variant),
            ("foil", foil_variant),
        ):
            is_selected = selected["style"] == style
            available = owned.get(style, 0) > 0
            control.bgcolor = "#ffffff" if is_selected and style == "normal" else (
                "#2f261812" if not is_selected else None
            )
            control.gradient = (
                ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=["#fff8d7", "#e4c876", "#f7edbe"],
                )
                if is_selected and style == "foil"
                else None
            )
            edge = GOLD if is_selected and style == "foil" else (
                INK if is_selected else "#2f261838"
            )
            control.border = ft.border.all(1.5, edge)
            control.shadow = (
                ft.BoxShadow(
                    blur_radius=0,
                    color="#2f261838",
                    offset=ft.Offset(2, 2),
                )
                if is_selected
                else None
            )
            control.offset = ft.Offset(0, 0.02) if not is_selected else None
            control.disabled = not available
            control.opacity = 1 if available else 0.42
            control.tooltip = (
                "No foil copy yet"
                if style == "foil" and not available
                else ("No normal copy yet" if not available else None)
            )

    def apply_style(style: str):
        def handler(e):
            if selected["style"] == style:
                return
            try:
                album.apply(sticker, style)
            except ApplyError as exc:
                page.open(ft.SnackBar(ft.Text(str(exc)), bgcolor="#b71c1c"))
                return
            selected["style"] = style
            art_switcher.content = _art_display(sticker, style == "foil")
            state_line.value = f"{character.name} · {collection_name} · applied"
            paint_variants()
            dialog.update()
            on_change(sticker)

        return handler

    def variant_button(label: str, style: str) -> ft.Container:
        return ft.Container(
            data=f"variant-{style}",
            width=100,
            height=34,
            alignment=ft.alignment.center,
            content=ft.Text(
                label,
                font_family=DISPLAY_FONT,
                size=10,
                weight=ft.FontWeight.W_700,
                color=INK,
            ),
            on_click=apply_style(style),
            ink=True,
        )

    normal_variant = variant_button("NORMAL", "normal")
    foil_variant = variant_button("FOIL", "foil")
    paint_variants()

    spare_count = (
        vice.spare_count(sticker.id)
        if vice is not None
        else album.duplicate_count(sticker.id)
    )
    each = vice.conversion_value(sticker) if vice is not None else 0
    worth = spare_count * each

    def confirm_conversion(e):
        quantity = ft.TextField(
            label=f"Copies to convert (1–{spare_count})",
            value=str(spare_count),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        confirm = ft.AlertDialog(
            modal=True,
            title=ft.Text("Vice Conversion"),
            content=ft.Column(
                [
                    ft.Text(
                        f"Each spare {sticker.name} is worth {each} vice "
                        "points. One copy will always be kept for your album."
                    ),
                    quantity,
                ],
                width=380,
                tight=True,
                spacing=12,
            ),
        )

        def convert(ev):
            try:
                converted, earned = vice.convert_spares(
                    sticker, int(quantity.value)
                )
            except (ValueError, ViceError) as exc:
                message = (
                    str(exc)
                    if isinstance(exc, ViceError)
                    else "Quantity must be a whole number."
                )
                page.open(ft.SnackBar(ft.Text(message), bgcolor="#b71c1c"))
                return
            page.close(confirm)
            page.close(dialog)
            page.open(
                ft.SnackBar(
                    ft.Text(
                        f"Converted {converted} spare copies into "
                        f"{earned} vice points."
                    )
                )
            )
            on_change(sticker)

        confirm.actions = [
            outline_button("CANCEL", lambda ev: page.close(confirm)),
            ink_button("CONVERT", convert),
        ]
        page.open(confirm)

    convert_button = ink_button(
        f"CONVERT SPARES → +{worth} VICE",
        confirm_conversion if spare_count and vice is not None else None,
        disabled=not spare_count or vice is None,
        tooltip="No spare copies to convert" if not spare_count else None,
    )
    convert_button.data = "convert-spares"
    convert_button.expand = True

    voice_button = outline_button(
        "VOICE LINE",
        (lambda e: play_sound(page, sticker.sound)) if sticker.sound else None,
        icon=ft.Icons.PLAY_ARROW,
        tooltip=None if sticker.sound else "No voice line available",
    )
    voice_button.disabled = not bool(sticker.sound)
    voice_button.opacity = 1 if sticker.sound else 0.42

    flavor = sticker.flavor_text or "No catalogue note."
    right = ft.Container(
        expand=True,
        height=388,
        content=ft.Column(
            [
                ft.Row(
                    [
                        paper_label(
                            RARITY_LABELS.get(
                                sticker.rarity, sticker.rarity
                            ).upper(),
                            sticker.rarity,
                        ),
                        ft.Text(
                            sticker.id,
                            color=INK_SOFT,
                            size=10.5,
                            font_family=META_FONT,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Text(
                    sticker.name.upper(),
                    font_family=DISPLAY_FONT,
                    weight=ft.FontWeight.W_900,
                    size=25,
                    color=INK,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                state_line,
                dashed_rule(400),
                ft.Text(
                    f"“{flavor}”",
                    size=12.5,
                    height=1.65,
                    font_family=META_FONT,
                    color=INK,
                ),
                dashed_rule(400),
                ft.Text(
                    "VARIANT ON THE BOARD",
                    font_family=DISPLAY_FONT,
                    weight=ft.FontWeight.W_700,
                    size=9.5,
                    color=INK_SOFT,
                ),
                ft.Row([normal_variant, foil_variant], spacing=8),
                ft.Container(expand=True),
                ft.Text(
                    f"{spare_count} spare copies · worth {worth} vice points",
                    data="spare-summary",
                    size=10.5,
                    font_family=META_FONT,
                    color=INK_SOFT,
                ),
                ft.Row([convert_button, voice_button], spacing=9),
            ],
            spacing=7,
            horizontal_alignment=ft.CrossAxisAlignment.START,
        ),
    )

    dialog.content = ft.Stack(
        [
            ft.Row(
                [art_board, right],
                width=772,
                spacing=24,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Container(
                right=0,
                top=0,
                width=32,
                height=32,
                alignment=ft.alignment.center,
                on_click=close,
                ink=True,
                tooltip="Close",
                bgcolor=CARD_BG,
                border=ft.border.all(1, "#2f261838"),
                content=ft.Text(
                    "×", font_family=META_FONT, size=22, color=INK
                ),
            ),
        ],
        width=772,
        height=388,
    )
    page.open(dialog)
