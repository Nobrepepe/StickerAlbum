"""Mutable user progress. Inventory is keyed by (sticker_id, style);
placements by sticker_id — each sticker has exactly one album slot."""

from dataclasses import dataclass, field

SCHEMA_VERSION = 2


@dataclass
class ViceOffering:
    id: str
    name: str
    description: str
    price: int
    quantity: int


@dataclass
class UserState:
    schema_version: int = SCHEMA_VERSION
    favorite_character_id: str | None = None
    total_saved: int = 0  # minor currency units (cents)
    # (sticker_id, style) -> quantity owned (never destructively reduced by
    # applying; duplicates are derived from quantity and placement).
    inventory: dict[tuple[str, str], int] = field(default_factory=dict)
    # sticker_id -> applied style
    placements: dict[str, str] = field(default_factory=dict)
    last_collection_id: str | None = None
    vice_points: int = 0
    vice_offerings: list[ViceOffering] = field(default_factory=list)
