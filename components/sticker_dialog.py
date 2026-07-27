"""Dialog for inspecting a sticker slot and applying owned copies."""

from typing import Callable

import flet as ft

from components.assets import resolve_image, sticker_mask_image
from components.audio_player import play_sound
from components.foil_shimmer import FoilShimmer
from components.paper import ink_button, outline_button, paper_label, tool_button
from components.placeholders import sticker_art
from components.theme import BODY_FONT, CARD_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from models.rarity import RARITY_LABELS
from models.catalog import Character, Sticker
from services.album_service import APPLIED, OWNED, AlbumService
from services.errors import ApplyError
from services.errors import ViceError

_STYLE_LABELS = {"normal": "Normal", "foil": "Foil ✨"}

_ART_W, _ART_H = 300, 400  # 3:4, matching the sticker artwork


def _art_display(sticker: Sticker, foil: bool) -> ft.Control:
    """Sticker art on a white backing plate (so the vignette reads as it
    does on the board), with the masked shimmer when inspecting a foil."""
    src = resolve_image(sticker.image)
    if not src:
        return sticker_art(sticker, _ART_W, _ART_H)
    layers: list[ft.Control] = [
        ft.Image(src=src, width=_ART_W, height=_ART_H, fit=ft.ImageFit.CONTAIN),
    ]
    if foil:
        mask = sticker_mask_image(sticker.id)
        if mask:
            layers.append(FoilShimmer(mask, _ART_W, _ART_H))
    return ft.Container(
        bgcolor="#ffffff",
        border_radius=12,
        padding=6,
        content=ft.Stack(layers, width=_ART_W, height=_ART_H),
    )


def open_sticker_dialog(
    page: ft.Page,
    album: AlbumService,
    sticker: Sticker,
    character: Character,
    on_change: Callable[[Sticker], None],
    vice=None,
) -> None:
    """One dialog for all three slot states. `on_change` runs after a
    successful apply/restyle, receiving the sticker that changed so the
    view can refresh (and animate the slot)."""
    state = album.slot_state(sticker.id)
    owned = album.owned_styles(sticker.id)
    applied_style = album.applied_style(sticker.id)

    dialog = ft.AlertDialog(modal=False)

    def close(e=None):
        page.close(dialog)

    def apply_style(style: str):
        def handler(e):
            try:
                album.apply(sticker, style)
            except ApplyError as exc:
                page.open(ft.SnackBar(ft.Text(str(exc)), bgcolor="#b71c1c"))
                return
            page.close(dialog)
            on_change(sticker)
        return handler

    info: list[ft.Control] = [
        ft.Row(
            [paper_label(RARITY_LABELS.get(sticker.rarity, sticker.rarity).upper(),
                         sticker.rarity),
             ft.Text(sticker.id, color=INK_SOFT, size=12, font_family=META_FONT)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        ft.Text(f"Character: {character.name}", size=13, color=INK_SOFT,
                font_family=META_FONT),
    ]

    if state == APPLIED:
        body_art: ft.Control = _art_display(sticker, foil=applied_style == "foil")
        info.append(ft.Text(
            f"Applied · {_STYLE_LABELS.get(applied_style, applied_style)}",
            size=13, color=INK, font_family=META_FONT,
        ))
        if sticker.flavor_text:
            info.append(ft.Text(
                f"“{sticker.flavor_text}”", size=13, italic=True,
                color=INK_SOFT, font_family=BODY_FONT,
                text_align=ft.TextAlign.LEFT,
            ))
        dups = album.duplicate_count(sticker.id)
        if dups:
            info.append(ft.Text(f"Spare copies: {dups}", size=12,
                                font_family=META_FONT, color=INK_SOFT))
    elif state == OWNED:
        # Preview shimmers if the only owned style is foil.
        body_art = _art_display(sticker, foil="normal" not in owned)
        counts = " · ".join(
            f"{_STYLE_LABELS[s]} ×{q}" for s, q in owned.items()
        )
        info.append(ft.Text(f"Owned, not applied yet — {counts}", size=13,
                            font_family=META_FONT, color=INK))
    else:
        body_art = ft.Container(
            width=_ART_W, height=_ART_H, border_radius=8,
            border=ft.border.all(1, "#d8d2c4"),
            alignment=ft.alignment.center,
            content=ft.Text("Not collected yet", color=INK_SOFT,
                            font_family=META_FONT),
        )
        info.append(ft.Text("Open packs in the Shop to find this sticker.",
                            size=13, color=INK_SOFT, font_family=META_FONT))

    right_actions: list[ft.Control] = [outline_button("CLOSE", close)]

    if vice is not None and vice.spare_count(sticker.id):
        spare_count = vice.spare_count(sticker.id)
        each = vice.conversion_value(sticker)

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
                    width=380, tight=True, spacing=12,
                ),
            )

            def convert(ev):
                try:
                    converted, earned = vice.convert_spares(
                        sticker, int(quantity.value)
                    )
                except (ValueError, ViceError) as exc:
                    message = (
                        str(exc) if isinstance(exc, ViceError)
                        else "Quantity must be a whole number."
                    )
                    page.open(ft.SnackBar(ft.Text(message), bgcolor="#b71c1c"))
                    return
                page.close(confirm)
                page.close(dialog)
                page.open(ft.SnackBar(ft.Text(
                    f"Converted {converted} spare copies into {earned} vice points."
                )))
                on_change(sticker)

            confirm.actions = [
                outline_button("CANCEL", lambda ev: page.close(confirm)),
                ink_button("CONVERT", convert),
            ]
            page.open(confirm)

        right_actions.append(outline_button(
            f"VICE CONVERSION (+{spare_count * each})",
            confirm_conversion, icon=ft.Icons.RECYCLING,
        ))
    for style, qty in owned.items():
        if style == applied_style:
            continue  # already in the slot with this style
        label = (
            f"Apply {_STYLE_LABELS[style]}"
            if applied_style is None
            else f"Switch to {_STYLE_LABELS[style]}"
        )
        right_actions.append(ink_button(f"{label} (×{qty})", apply_style(style)))

    dialog.bgcolor = CARD_BG
    dialog.title = ft.Text(sticker.name.upper(), font_family=DISPLAY_FONT,
                           weight=ft.FontWeight.W_700, color=INK,
                           text_align=ft.TextAlign.CENTER)
    dialog.content = ft.Column(
        [body_art, *info],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        tight=True,
        spacing=10,
        width=360,
    )
    if state == APPLIED and sticker.sound:
        # Pinned on the opposite side from Close/Apply so it never shifts
        # around with the flavor text's line count.
        dialog.actions = [
            tool_button("♪", lambda e: play_sound(page, sticker.sound),
                        "Play voice line"),
            ft.Row(right_actions, spacing=8, tight=True),
        ]
        dialog.actions_alignment = ft.MainAxisAlignment.SPACE_BETWEEN
    else:
        dialog.actions = right_actions
        dialog.actions_alignment = ft.MainAxisAlignment.END
    page.open(dialog)
