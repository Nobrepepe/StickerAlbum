"""Album sticker slot, styled for the white sticker board.

Applied stickers render as bare artwork — the art's white vignette edges
blend into the board and into neighbouring stickers (grid spacing is 0).
Floating "signs" carry the metadata: status signs (foil / duplicates /
ready) overflow past the top edge, and a rarity-colored name sign
overflows past the bottom-left, slightly invading the adjacent stickers by
design.
"""

from typing import Callable

import flet as ft

from components.assets import resolve_image, sticker_mask_image
from components.foil_shimmer import FoilShimmer
from components.paper import paper_label
from components.placeholders import sticker_art
from components.theme import CARD_BG, INK, META_FONT, TRACK_BG
from models.catalog import Sticker
from services.album_service import APPLIED, OWNED, AlbumService

# Slots share the 3:4 ratio of the sticker artwork.
SLOT_W = 150.0
SLOT_H = 200.0

def _sign(text: str, rarity: str | None = None, *, gold: bool = False,
          size: int = 9, max_width: float | None = None,
          fill: str | None = None) -> ft.Control:
    # Shrink-to-fit, but cap long names so the sign stays on its sticker.
    # (Flet has no max-width constraint, so estimate the rendered width.)
    width = None
    if max_width is not None and len(text) * size * 0.62 > max_width:
        width = max_width
    return paper_label(
        text, rarity, gold=gold, size=size, max_width=width, fill=fill
    )


def build_sticker_slot(
    album: AlbumService,
    sticker: Sticker,
    on_tap: Callable[[Sticker], None],
    width: float = SLOT_W,
    height: float = SLOT_H,
) -> ft.Container:
    state = album.slot_state(sticker.id)
    k = max(1.0, width / SLOT_W)
    sign_size = round(9 * k**0.5)

    status_signs: list[ft.Control] = []

    layers: list[ft.Control] = []
    if state == APPLIED:
        style = album.applied_style(sticker.id)
        src = resolve_image(sticker.image)
        if src:
            # Bare art on the board; its white edges do the framing.
            layers.append(ft.Image(src=src, width=width, height=height,
                                   fit=ft.ImageFit.CONTAIN))
            if style == "foil":
                mask = sticker_mask_image(sticker.id)
                if mask:
                    layers.append(FoilShimmer(mask, width, height))
        else:
            layers.append(ft.Container(
                content=sticker_art(sticker, width - 12, height - 12),
                alignment=ft.alignment.center,
                margin=6,
            ))
        if style == "foil":
            status_signs.append(_sign("FOIL", gold=True, size=sign_size))
        dups = album.duplicate_count(sticker.id)
        if dups > 0:
            status_signs.append(_sign(
                f"+{dups}",
                gold=album.has_foil_spare(sticker.id),
                size=sign_size,
            ))
    elif state == OWNED:
        # Owned but not pasted: a dark sticker "back", never the artwork.
        layers.append(ft.Container(
            margin=6,
            border_radius=0,
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[CARD_BG, TRACK_BG],
            ),
            alignment=ft.alignment.center,
            content=ft.Icon(
                ft.Icons.STICKY_NOTE_2_OUTLINED,
                size=36 * k,
                color="#2f26188c",
            ),
        ))
        status_signs.append(_sign("READY TO APPLY", gold=True, size=sign_size))
    else:  # missing: preview the sticker's silhouette on the white board
        mask = sticker_mask_image(sticker.id)
        if mask:
            layers.append(ft.Image(
                src=mask,
                width=width,
                height=height,
                fit=ft.ImageFit.CONTAIN,
                color="#e7e3d9",
                color_blend_mode=ft.BlendMode.SRC_IN,
            ))
        else:
            # Older/custom catalogs may not have foil masks yet.
            layers.append(ft.Container(
                margin=6,
                border_radius=0,
                bgcolor="#ffffff",
                border=ft.border.all(1.5, "#d8d2c4"),
                alignment=ft.alignment.center,
                content=ft.Column(
                    [
                        ft.Text(
                            f"#{sticker.number:02d}",
                            size=26 * k,
                            font_family=META_FONT,
                            color="#2f261859",
                        ),
                        ft.Text(sticker.id, size=round(10 * k),
                                font_family=META_FONT, color="#2f261859"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    tight=True,
                ),
            ))

    if status_signs:
        layers.append(ft.Row(status_signs, alignment=ft.MainAxisAlignment.END,
                             spacing=4, top=-7, right=6))
    # Name sign doubles as the rarity marker (background = rarity color).
    # Kept just inside the bottom edge: rows below paint over anything that
    # overflows downward, so only the top signs invade their neighbour.
    layers.append(ft.Container(
        content=_sign(sticker.name, sticker.rarity,
                      size=sign_size, max_width=width - 20),
        bottom=5, left=6,
    ))

    return ft.Container(
        width=width,
        height=height,
        # Same white as the board: invisible, but keeps the whole slot
        # clickable (fully transparent containers don't hit-test).
        bgcolor="#ffffff",
        on_click=lambda e: on_tap(sticker),
        content=ft.Stack(layers, expand=True, clip_behavior=ft.ClipBehavior.NONE),
    )
