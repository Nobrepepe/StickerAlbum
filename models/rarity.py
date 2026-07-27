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
    "spicy": 5,
}

RARITIES: tuple[str, ...] = tuple(RARITY_ORDER)

RARITY_COLORS: dict[str, str] = {
    "common": "#c8bda6",
    "uncommon": "#b6c2a4",
    "rare": "#a8bdd2",
    "epic": "#bfa9d4",
    "legendary": "#b8973f",
    "spicy": "#c9856d",
}

# Presentation only: rarity reads as the paper stock a label is printed on.
RARITY_PAPER: dict[str, tuple[str, str]] = {
    "common": ("#ffffff", "#c8bda6"),
    "uncommon": ("#edf0e4", "#b6c2a4"),
    "rare": ("#e2eaf2", "#a8bdd2"),
    "epic": ("#ebe2f2", "#bfa9d4"),
    "legendary": ("#f1dfa8", "#b8973f"),
    "spicy": ("#f6ddd4", "#c9856d"),
}
RARITY_INK = "#2f2618"

RARITY_LABELS: dict[str, str] = {
    "common": "Common",
    "uncommon": "Uncommon",
    "rare": "Rare",
    "epic": "Epic",
    "legendary": "Legendary",
    "spicy": "Spicy",
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

# Spicy stickers: 5 hidden bonus stickers per character, all with the special
# presentation-only spicy rarity.
# They never count toward the 10/100 album completion.
SPICY_PER_CHARACTER = 5
SPICY_RARITY_PATTERN: tuple[str, ...] = ("spicy",) * SPICY_PER_CHARACTER


def slot_rarity(position: int) -> str:
    """Rarity for a character slot: 1-10 are regular, 11-15 are spicy."""
    if 1 <= position <= 10:
        return RARITY_PATTERN[position - 1]
    if 11 <= position <= 15:
        return SPICY_RARITY_PATTERN[position - 11]
    raise ValueError(f"Invalid slot position: {position}")

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

# Vice conversion values are inverse to expected rarity frequency in the
# starter pack: 2 common, 2 uncommon, .7 rare, .25 epic, .05 legendary.
# Spicy uses its default 20% first-hit chance: 2 common / .2 spicy = 10.
VICE_VALUES: dict[str, int] = {
    "common": 1,
    "uncommon": 1,
    "rare": 3,
    "epic": 8,
    "legendary": 40,
    "spicy": 10,
}
