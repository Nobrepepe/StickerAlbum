# Sticker Album

A private desktop app that recreates the joy of filling a World Cup–style
sticker album — with original fictional collections. Opening a pack records a
real deposit into your savings account (the app only records the amount; no
bank connection).

**The loop:** confirm savings deposit → open pack → reveal stickers → collect
new copies and duplicates → manually apply stickers → watch the album fill.

## Vice Shop

Only spare copies you explicitly choose are converted into vice points, and
one copy is always protected for the album. Open a sticker's inspection
dialog, choose **Vice Conversion**, and enter how many spares to convert.

| Rarity | Points per spare |
|---|---:|
| Common | 1 |
| Uncommon | 1 |
| Rare | 3 |
| Epic | 8 |
| Legendary | 40 |

The Vice Shop stores editable indulgences with a name, description, point
price, and available quantity. Claiming deducts the price and reduces the
quantity by one. Points and offerings are part of progress backups and resets.

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
| `app_data/user_state.json` | Mutable progress: inventory, placements, favorite, savings, vice points and offerings (created on first run, saved atomically) |
| `app_data/settings.json` | App settings: Creator screen toggle (off by default) |
| `assets/` | Optional artwork (see `assets/README.txt`); anything missing renders as a styled placeholder |
| `models/` | Frozen dataclasses + centralized rarity/selector/money rules |
| `repositories/` | JSON loading and user-state persistence (no UI code) |
| `services/` | Pack opening (injectable RNG), album placement rules, home summaries |
| `views/`, `components/` | Flet screens and reusable controls |
| `seed.py` | Deterministic demo catalog generator (only runs when `data/` is empty; `python seed.py --force` regenerates) |

## Settings, backups, and resets

The **Settings** screen exports/imports/resets playthrough progress and holds
the optional Creator screen toggle (off by default). The **Creator** screen has matching backup/restore/reset actions for
the catalog itself (collections, characters, stickers, drafts — progress and
packs are untouched). Both resets ask for confirmation.

## Adding a collection

Use the **Creator** screen (enable it in Settings): pick a unique
three-letter code, name the collection, then fill in its 10 characters and
their 10 stickers each (3× common, 3× uncommon, 2× rare,
1× epic, and 1× legendary by slot). Cover, portrait,
and sticker images can be imported from disk at any point. Incomplete
collections stay as drafts, visible only in the Creator; once every character
has a name and 10 named stickers, the Publish button moves it into the
catalog.

Packs are still added by hand in `data/packs.json`. Legacy distributions use
`pool` (a collection or character ID), `value`, and `quantity`. Custom
distributions use weighted `pools`, `rarity_weights`, and `quantity`; optional
`include` and `exclude` sticker-ID lists provide exact control. See the
example below. Prices are integer cents (`2500` → `R$ 25,00`).

```json
{
  "quantity": 5,
  "pools": [
    {"pool": "MRC", "weight": 0.6},
    {"pool": "MGA", "weight": 0.4}
  ],
  "rarity_weights": {
    "rare": 0.7,
    "epic": 0.25,
    "legendary": 0.05
  },
  "exclude": ["MRC_099"]
}
```

Published collections can be edited again in two ways (both need the
Creator enabled, via icons on the collection card):

- **Hot-edit** (pencil): edits the live collection in place — names,
  descriptions, flavor text, cover/tile/card/sticker images, and sounds.
  Structure and rarities are fixed, every name must stay filled in, and
  your progress is untouched.
- **Revert to draft**: turns it back into a fully pre-filled draft for
  structural rework. The collection leaves play, so its progress (owned
  copies and placements) is erased after a confirmation — savings records
  are kept.

Hand-editing the catalog files also still works — follow the existing shape,
and never rename published sticker `id`s like `HGT_042` (saved user state
references them).
