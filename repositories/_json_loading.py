"""Shared helper for reading catalog JSON files with clear errors."""

import json
from pathlib import Path

from repositories.errors import CatalogError


def load_json_file(path: Path):
    if not path.exists():
        raise CatalogError(f"Catalog file not found: {path.name}")
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise CatalogError(f"Catalog file {path.name} is unreadable: {exc}") from exc
