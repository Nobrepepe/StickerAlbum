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
| `app_data/settings.json` | App settings: Creator screen toggle, spicy toggle (both off by default) |
| `assets/` | Optional artwork (see `assets/README.txt`); anything missing renders as a styled placeholder |
| `models/` | Frozen dataclasses + centralized rarity/selector/money rules |
| `repositories/` | JSON loading and user-state persistence (no UI code) |
| `services/` | Pack opening (injectable RNG), album placement rules, home summaries |
| `views/`, `components/` | Flet screens and reusable controls |
| `seed.py` | Deterministic demo catalog generator (only runs when `data/` is empty; `python seed.py --force` regenerates) |

## Settings, backups, and resets

The **Settings** screen exports/imports/resets playthrough progress and holds
two feature toggles (both off by default): the Creator screen, and the 🌶️
toggle. The **Creator** screen has matching backup/restore/reset actions for
the catalog itself (collections, characters, stickers, drafts — progress and
packs are untouched). Both resets ask for confirmation.

## Spicy stickers 🌶️

Each character has 5 hidden bonus stickers (numbers 101–150, one per rarity).
While the 🌶️ toggle is off they are invisible everywhere — album, stats,
carousel, and pack drops. When on, packs roll bonus spicy drops using the
pack's `spicy_rate` (default `0.2`): each hit adds one random spicy sticker
from the pack's collection and rolls again until a miss. Spicy stickers never
count toward the 10/100 album completion.

## Adding a collection

Use the **Creator** screen (enable it in Settings): pick a unique
three-letter code, name the collection, then fill in its 10 characters and
their 15 stickers each — 10 regular (3× common, 3× uncommon, 2× rare,
1× epic, 1× legendary by slot) plus 5 spicy, one per rarity. Cover, portrait,
and sticker images can be imported from disk at any point. Incomplete
collections stay as drafts, visible only in the Creator; once every character
has a name and 15 named stickers, the Publish button moves it into the
catalog.

Packs are still added by hand: after publishing, add an entry to
`data/packs.json` whose `distribution[].pool` is the collection (or a
character) ID. Prices are integer cents (`2500` → `R$ 25,00`).

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
