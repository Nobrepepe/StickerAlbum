# Sticker Album

A private desktop app that recreates the joy of filling a World Cup–style
sticker album — with original fictional collections. Opening a pack records a
real deposit into your savings account (the app only records the amount; no
bank connection).

**The loop:** confirm savings deposit → open pack → reveal stickers → collect
new copies and duplicates → manually apply stickers → watch the album fill.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Built with Python + [Flet](https://flet.dev) 0.28 (desktop, Linux-friendly,
packageable for other platforms later).

## Tests

```bash
.venv/bin/python -m pytest tests/
```

## Layout

| Path | Purpose |
|---|---|
| `data/` | Static catalog: `collections.json`, `characters.json`, `stickers.json`, `packs.json`; plus `drafts.json` for Creator drafts |
| `app_data/user_state.json` | Mutable progress: inventory, placements, favorite, total savings (created on first run, saved atomically) |
| `assets/` | Optional artwork (see `assets/README.txt`); anything missing renders as a styled placeholder |
| `models/` | Frozen dataclasses + centralized rarity/selector/money rules |
| `repositories/` | JSON loading and user-state persistence (no UI code) |
| `services/` | Pack opening (injectable RNG), album placement rules, home summaries |
| `views/`, `components/` | Flet screens and reusable controls |
| `seed.py` | Deterministic demo catalog generator (only runs when `data/` is empty; `python seed.py --force` regenerates) |

## Adding a collection

Use the **Creator** screen in the app: pick a unique three-letter code, name
the collection, then fill in its 10 characters and their 10 stickers each
(rarities follow the fixed slot pattern: 3× common, 3× uncommon, 2× rare,
1× epic, 1× legendary). Cover, portrait, and sticker images can be imported
from disk at any point. Incomplete collections stay as drafts, visible only
in the Creator; once every character has a name and 10 named stickers, the
Publish button moves it into the catalog.

Packs are still added by hand: after publishing, add an entry to
`data/packs.json` whose `distribution[].pool` is the collection (or a
character) ID. Prices are integer cents (`2500` → `R$ 25,00`).

Hand-editing the catalog files also still works — follow the existing shape,
and never rename published sticker `id`s like `HGT_042` (saved user state
references them).
