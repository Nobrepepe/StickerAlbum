"""Dialog for inspecting a sticker slot and applying owned copies."""

from typing import Callable

import flet as ft

from components.assets import resolve_image, sticker_mask_image
from components.audio_player import play_sound
from components.foil_shimmer import FoilShimmer
from components.placeholders import sticker_art
from components.rarity_chip import rarity_chip
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
            [rarity_chip(sticker.rarity), ft.Text(sticker.id, color=ft.Colors.GREY_500, size=12)],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10,
        ),
        ft.Text(f"Character: {character.name}", size=13, color=ft.Colors.GREY_400),
    ]

    if state == APPLIED:
        body_art: ft.Control = _art_display(sticker, foil=applied_style == "foil")
        info.append(ft.Text(
            f"Applied · {_STYLE_LABELS.get(applied_style, applied_style)}",
            size=13, color="#81c784", weight=ft.FontWeight.BOLD,
        ))
        if sticker.flavor_text:
            info.append(ft.Text(
                f"“{sticker.flavor_text}”", size=13, italic=True,
                color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER,
            ))
        dups = album.duplicate_count(sticker.id)
        if dups:
            info.append(ft.Text(f"Spare copies: {dups}", size=12, color=ft.Colors.GREY_500))
    elif state == OWNED:
        # Preview shimmers if the only owned style is foil.
        body_art = _art_display(sticker, foil="normal" not in owned)
        counts = " · ".join(
            f"{_STYLE_LABELS[s]} ×{q}" for s, q in owned.items()
        )
        info.append(ft.Text(f"Owned, not applied yet — {counts}", size=13, color="#ffb300"))
    else:
        body_art = ft.Container(
            width=_ART_W, height=_ART_H, border_radius=8,
            border=ft.border.all(1, ft.Colors.GREY_800),
            alignment=ft.alignment.center,
            content=ft.Text("Not collected yet", color=ft.Colors.GREY_600),
        )
        info.append(ft.Text("Open packs in the Shop to find this sticker.",
                            size=13, color=ft.Colors.GREY_500))

    right_actions: list[ft.Control] = [ft.TextButton("Close", on_click=close)]

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
                ft.TextButton("Cancel", on_click=lambda ev: page.close(confirm)),
                ft.FilledButton("Convert", on_click=convert),
            ]
            page.open(confirm)

        right_actions.append(ft.OutlinedButton(
            f"Vice Conversion (+{spare_count * each})",
            icon=ft.Icons.RECYCLING,
            on_click=confirm_conversion,
        ))
    for style, qty in owned.items():
        if style == applied_style:
            continue  # already in the slot with this style
        label = (
            f"Apply {_STYLE_LABELS[style]}"
            if applied_style is None
            else f"Switch to {_STYLE_LABELS[style]}"
        )
        right_actions.append(ft.FilledButton(f"{label} (×{qty})", on_click=apply_style(style)))

    dialog.title = ft.Text(sticker.name, text_align=ft.TextAlign.CENTER)
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
            ft.IconButton(
                ft.Icons.VOLUME_UP, icon_size=18, tooltip="Play voice line",
                on_click=lambda e: play_sound(page, sticker.sound),
            ),
            ft.Row(right_actions, spacing=8, tight=True),
        ]
        dialog.actions_alignment = ft.MainAxisAlignment.SPACE_BETWEEN
    else:
        dialog.actions = right_actions
        dialog.actions_alignment = ft.MainAxisAlignment.END
    page.open(dialog)
