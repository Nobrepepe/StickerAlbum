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
