"""Centralized asset path resolution.

Catalog entries reference images relative to the assets/ directory. When a
file is missing (all of the seed catalog, until art is added) we return None
and the UI renders a styled placeholder instead of crashing.
"""

import logging

from paths import ASSETS_DIR

log = logging.getLogger(__name__)
_missing_logged: set[str] = set()


def resolve_image(relative: str | None) -> str | None:
    """Return an Image src (relative to flet's assets_dir) or None."""
    if not relative:
        return None
    if (ASSETS_DIR / relative).is_file():
        return f"/{relative}"
    if relative not in _missing_logged:
        _missing_logged.add(relative)
        log.info("Asset missing, using placeholder: %s", relative)
    return None


_IMAGE_EXTS = ("png", "jpg", "jpeg", "webp")


def _resolve_any_ext(base: str) -> str | None:
    for ext in _IMAGE_EXTS:
        rel = f"{base}.{ext}"
        if (ASSETS_DIR / rel).is_file():
            return f"/{rel}"
    return None


def character_tile_image(character_id: str) -> str | None:
    """16:9 landscape banner for the album sidebar (e.g. the character's
    eyes). Convention: assets/portraits/<CHARACTER_ID>_tile.png"""
    return _resolve_any_ext(f"portraits/{character_id}_tile")


def character_card_image(character_id: str) -> str | None:
    """9:16 portrait full-body card shown when the character is selected.
    Convention: assets/portraits/<CHARACTER_ID>_card.png"""
    return _resolve_any_ext(f"portraits/{character_id}_card")


def sticker_mask_image(sticker_id: str) -> str | None:
    """Alpha mask isolating the sticker's subject from its white vignette
    (transparent background, opaque silhouette). Used to keep the foil
    shimmer inside the artwork. Convention: assets/stickers/<ID>_mask.png"""
    return _resolve_any_ext(f"stickers/{sticker_id}_mask")


def resolve_sound(relative: str | None) -> str | None:
    """Return an Audio src (relative to flet's assets_dir) or None."""
    if not relative:
        return None
    if (ASSETS_DIR / relative).is_file():
        return f"/{relative}"
    if relative not in _missing_logged:
        _missing_logged.add(relative)
        log.info("Asset missing, using placeholder: %s", relative)
    return None
