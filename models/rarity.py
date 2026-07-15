"""Centralized rarity, style, and pack-distribution selector rules.

Every part of the app (UI, services, seed generator, tests) imports these
instead of comparing rarity strings ad hoc.
"""

RARITY_ORDER: dict[str, int] = {
    "common": 0,
    "uncommon": 1,
    "rare": 2,
    "epic": 3,
    "legendary": 4,
}

RARITIES: tuple[str, ...] = tuple(RARITY_ORDER)

RARITY_COLORS: dict[str, str] = {
    "common": "#9e9e9e",
    "uncommon": "#4caf50",
    "rare": "#2196f3",
    "epic": "#9c27b0",
    "legendary": "#f44336",
}

RARITY_LABELS: dict[str, str] = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "epic": "Epic",
    "legendary": "Legendary",
}

# Per-character slot layout: slots 1-3 common, 4-6 uncommon, 7-8 rare,
# 9 epic, 10 legendary (the required 3/3/2/1/1 distribution).
RARITY_PATTERN: tuple[str, ...] = (
    "common", "common", "common",
    "uncommon", "uncommon", "uncommon",
    "rare", "rare",
    "epic",
    "legendary",
)

# Pack distribution selectors -> set of eligible rarities.
SELECTORS: dict[str, set[str]] = {
    "common": {"common"},
    "uncommon": {"uncommon"},
    "rare": {"rare"},
    "epic": {"epic"},
    "legendary": {"legendary"},
    "standard": {"common", "uncommon"},
    "rare+": {"rare", "epic", "legendary"},
    "epic+": {"epic", "legendary"},
    "any": {"common", "uncommon", "rare", "epic", "legendary"},
}

# Sticker copy styles. Foil is a style of the same sticker, not a separate
# album slot: one placement of either style completes the slot.
STYLES: tuple[str, ...] = ("normal", "foil")
