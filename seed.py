"""Development seed catalog generator.

Generates a deterministic demo catalog (collections, characters, stickers,
packs) into data/ when no catalog exists. Never overwrites existing files,
so authored data is safe. Can also be run directly:

    python seed.py          # create missing catalog files
    python seed.py --force  # regenerate everything (development only)
"""

import json
import sys
from pathlib import Path

from models.rarity import RARITY_PATTERN

CATALOG_FILES = ("collections.json", "characters.json", "stickers.json", "packs.json")

_COLLECTIONS = [
    {
        "id": "HGT",
        "name": "Alturas Heights",
        "description": "A wind-swept city of impossible towers, where couriers race across the skyline.",
        "cover_image": "covers/HGT.png",
        "theme_color": "#7c4dff",
    },
    {
        "id": "TDL",
        "name": "Tidelow Reef",
        "description": "A drowned kingdom lit by lantern fish, where every street is a current.",
        "cover_image": "covers/TDL.png",
        "theme_color": "#00bcd4",
    },
]

_CHARACTERS = {
    "HGT": [
        ("Aria Vane", "Skyline courier who never touches the ground."),
        ("Bruno Calder", "Bridge engineer with a fear of stairs."),
        ("Cielo Marsh", "Gardener of the floating cloud terraces."),
        ("Dario Quill", "Cartographer of rooftops nobody else can reach."),
        ("Elba Torres", "Dancer who performs on moving elevators."),
        ("Falk Reyes", "Listens to the antennas and hears the city's mood."),
        ("Gala Prisma", "Paints the glass towers a new color every dawn."),
        ("Hugo Ferro", "Crane operator who builds higher than the clouds."),
        ("Iris Vela", "Kite racer, three-time champion of the Updraft Cup."),
        ("Joto Brass", "Balloon postman who delivers to the highest windows."),
    ],
    "TDL": [
        ("Anga Coral", "Shepherd of the wandering reef flocks."),
        ("Bral Marrow", "Pearl diver who maps the dark trenches."),
        ("Cora Lume", "Keeper of the thousand lantern-fish lamps."),
        ("Drift Okane", "Pilot who reads the currents like roads."),
        ("Eelio Sund", "Fisher who catches songs instead of fish."),
        ("Fana Brine", "Chef whose salt gardens feed the whole reef."),
        ("Gill Harrow", "Archivist of every shipwreck's last story."),
        ("Hydra Mint", "Weaver of kelp banners for the tide festivals."),
        ("Inko Shell", "Teller of tides, never wrong twice in a row."),
        ("Juna Abyss", "Cartographer of the places light forgets."),
    ],
}

# One sticker name/flavor template per slot position (1-10); the rarity of
# each position follows RARITY_PATTERN (3/3/2/1/1).
_STICKER_TEMPLATES = [
    ("First Steps", "Where every story begins."),
    ("Daily Ritual", "The small habit that keeps them going."),
    ("Quiet Moment", "Even heroes need to breathe."),
    ("Tools of the Trade", "Never leaves home without them."),
    ("Among Friends", "Stronger together, always."),
    ("Against the Wind", "The day everything pushed back."),
    ("Signature Move", "You'd know it anywhere."),
    ("Night Shift", "The city looks different after dark."),
    ("Moment of Glory", "The one everybody still talks about."),
    ("Golden Portrait", "A legend, captured in gold."),
]

_PACKS = {
    "HGT_standard": {
        "collection_id": "HGT",
        "name": "Heights Starter Pack",
        "description": "5 random Alturas Heights stickers: 4 standard, 1 guaranteed rare or better.",
        "price": 2500,
        "foil_rate": 0.10,
        "image": "packs/HGT_standard.png",
        "distribution": [
            {"pool": "HGT", "value": "standard", "quantity": 4},
            {"pool": "HGT", "value": "rare+", "quantity": 1},
        ],
    },
    "HGT_premium": {
        "collection_id": "HGT",
        "name": "Heights Collector Pack",
        "description": "5 Alturas Heights stickers with a guaranteed epic or legendary.",
        "price": 5000,
        "foil_rate": 0.25,
        "image": "packs/HGT_premium.png",
        "distribution": [
            {"pool": "HGT", "value": "standard", "quantity": 3},
            {"pool": "HGT", "value": "rare+", "quantity": 1},
            {"pool": "HGT", "value": "epic+", "quantity": 1},
        ],
    },
    "TDL_standard": {
        "collection_id": "TDL",
        "name": "Reef Starter Pack",
        "description": "5 random Tidelow Reef stickers: 4 standard, 1 guaranteed rare or better.",
        "price": 2500,
        "foil_rate": 0.10,
        "image": "packs/TDL_standard.png",
        "distribution": [
            {"pool": "TDL", "value": "standard", "quantity": 4},
            {"pool": "TDL", "value": "rare+", "quantity": 1},
        ],
    },
    "TDL_premium": {
        "collection_id": "TDL",
        "name": "Reef Collector Pack",
        "description": "5 Tidelow Reef stickers with a guaranteed epic or legendary.",
        "price": 5000,
        "foil_rate": 0.25,
        "image": "packs/TDL_premium.png",
        "distribution": [
            {"pool": "TDL", "value": "standard", "quantity": 3},
            {"pool": "TDL", "value": "rare+", "quantity": 1},
            {"pool": "TDL", "value": "epic+", "quantity": 1},
        ],
    },
    "TDL_wave": {
        "collection_id": "TDL",
        "name": "Wave Pack",
        "description": "8 completely random Tidelow Reef stickers of any rarity.",
        "price": 3500,
        "foil_rate": 0.15,
        "image": "packs/TDL_wave.png",
        "distribution": [
            {"pool": "TDL", "value": "any", "quantity": 8},
        ],
    },
}


def _build_characters() -> list[dict]:
    chars = []
    for col in _COLLECTIONS:
        for i, (name, desc) in enumerate(_CHARACTERS[col["id"]], start=1):
            cid = f"{col['id']}_C{i:02d}"
            chars.append({
                "id": cid,
                "collection_id": col["id"],
                "name": name,
                "description": desc,
                "portrait_image": f"portraits/{cid}.png",
            })
    return chars


def _build_stickers(characters: list[dict]) -> list[dict]:
    stickers = []
    for char in characters:
        col_id = char["collection_id"]
        char_index = int(char["id"].rsplit("C", 1)[1])
        first_name = char["name"].split()[0]
        for pos in range(1, 11):
            number = (char_index - 1) * 10 + pos
            sid = f"{col_id}_{number:03d}"
            title, flavor = _STICKER_TEMPLATES[pos - 1]
            stickers.append({
                "id": sid,
                "collection_id": col_id,
                "character_id": char["id"],
                "number": number,
                "name": f"{first_name} — {title}",
                "rarity": RARITY_PATTERN[pos - 1],
                "image": f"stickers/{sid}.png",
                "flavor_text": flavor,
            })
    return stickers


def ensure_seed_catalog(data_dir: Path, force: bool = False) -> bool:
    """Create catalog files if the catalog is absent. Returns True if
    anything was generated. Never overwrites unless force=True."""
    existing = [f for f in CATALOG_FILES if (data_dir / f).exists()]
    if existing and not force:
        if len(existing) < len(CATALOG_FILES):
            missing = set(CATALOG_FILES) - set(existing)
            raise RuntimeError(
                f"Partial catalog in {data_dir}: missing {sorted(missing)}. "
                "Restore the missing files or move the others away to reseed."
            )
        return False

    data_dir.mkdir(parents=True, exist_ok=True)
    characters = _build_characters()
    payloads = {
        "collections.json": _COLLECTIONS,
        "characters.json": characters,
        "stickers.json": _build_stickers(characters),
        "packs.json": _PACKS,
    }
    for fname, payload in payloads.items():
        (data_dir / fname).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return True


if __name__ == "__main__":
    from paths import DATA_DIR

    created = ensure_seed_catalog(DATA_DIR, force="--force" in sys.argv)
    print("Catalog generated." if created else "Catalog already present; nothing done.")
