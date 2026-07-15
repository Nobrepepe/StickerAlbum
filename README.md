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
| `data/` | Static catalog: `collections.json`, `characters.json`, `stickers.json`, `packs.json` |
| `app_data/user_state.json` | Mutable progress: inventory, placements, favorite, total savings (created on first run, saved atomically) |
| `assets/` | Optional artwork (see `assets/README.txt`); anything missing renders as a styled placeholder |
| `models/` | Frozen dataclasses + centralized rarity/selector/money rules |
| `repositories/` | JSON loading and user-state persistence (no UI code) |
| `services/` | Pack opening (injectable RNG), album placement rules, home summaries |
| `views/`, `components/` | Flet screens and reusable controls |
| `seed.py` | Deterministic demo catalog generator (only runs when `data/` is empty; `python seed.py --force` regenerates) |

## Adding a collection

Each collection needs exactly 10 characters and 10 stickers per character with
the rarity pattern 3× common, 3× uncommon, 2× rare, 1× epic, 1× legendary
(slots 1–10 in that order). Add entries to the four files in `data/` following
the existing shape (sticker `id`s like `HGT_042` are stable and referenced by
saved user state — never rename them), then add at least one pack in
`packs.json` whose `distribution[].pool` is the collection (or a character)
ID. Prices are integer cents (`2500` → `R$ 25,00`). Artwork goes under
`assets/` using the paths referenced by the catalog; it is optional.
