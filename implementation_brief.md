# Sticker Album — “Kraft & Tape” UI implementation brief

You are implementing a visual redesign of an existing **Flet 0.28.3 desktop app** (Python).
Repo: `Nobrepepe/StickerAlbum`, branch `main`. Entry point `python main.py`.

The visual target is a set of approved mockups (`Sticker Album Redesign.dc.html`, turns 2 and 3).
This document is the spec. Follow it literally where it gives values; where it doesn't, follow the
principles in §2.

**This is a re-skin plus one new animation. Do not change data models, services, repositories,
JSON schemas, or any business logic. Do not touch `tests/` expectations about behaviour.**

---

## 1. Non-negotiables

1. **The white boards stay pure white (`#ffffff`).** Sticker art is authored with white vignette
   edges so adjacent stickers blend into one silhouette. Never tint the board, never add opacity or
   transparency handling to sticker art, never put a border or background behind an individual
   applied sticker.
2. **Grid spacing on boards stays `0`** (`spacing=0, run_spacing=0`) — the blending is the product.
3. Sticker slots keep the **3:4** ratio; character tiles **16:9**; character cards **9:16**.
4. The pack result is committed *before* the reveal view opens (`PackOpeningService.open_pack`
   saves inventory + savings in one commit). **Every animation beat must be interruptible and
   skippable with zero consequence.**
5. Keep all existing behaviour: live edit, unpublish, vice shop,
   backups, sounds, favourite character.

---

## 2. The design language

The app is a **scrapbook on a work desk**. Kraft paper surround, cream card stock for panels, pure
white boards for art, ink-black type, gold only for legendary. Nothing glows; everything looks
printed, stamped, taped or typed.

### 2.1 Surfaces — rewrite `components/theme.py`

```python
"""The app's single fixed look: a kraft-paper desk, cream card stock, white boards."""

DESK_BG      = "#c8b9a2"  # app background (was PAGE_BG #282431)
TAB_IDLE     = "#c4b298"  # unselected binder tab (there is no navigation rail any more)
TAB_ACTIVE   = "#fdfaf3"  # selected binder tab — same stock as the page below it
PAGE_BG      = "#fdfaf3"  # the page every screen is printed on
CARD_BG      = "#f4efe6"  # panels, cards, tiles (was PANEL_BG)
CARD_BORDER  = "#ded2bc"  # hairline on cream panels (was PANEL_BORDER)
BOARD_BG     = "#ffffff"  # unchanged — the boards the art blends into
INK          = "#2f2618"  # primary type + filled buttons
INK_SOFT     = "#6b5f4c"  # secondary type on paper
TAPE         = "#f0e6cd"  # washi tape strips (use at ~82% opacity)
GOLD         = "#c9a86a"  # legendary / foil accent only
STAMP_RED    = "#a8563a"  # LIVE EDIT stamp, destructive actions
TRACK_BG     = "#d9cdb8"  # progress-bar troughs on paper
```

Keep the old names as aliases *only* if that saves churn, otherwise update all imports.
`main.py`: `page.bgcolor = DESK_BG`, `page.theme_mode = ft.ThemeMode.LIGHT`, and set a light
`page.theme` so default Material text lands dark on paper. Audit every place that relied on dark
mode (`ft.Colors.GREY_400`, `ft.Colors.WHITE` body text) — those all become `INK` / `INK_SOFT`.

### 2.2 Type

Three faces, registered in `main.py` via `page.fonts` from `assets/fonts/`:

| Role | Font | Usage |
| --- | --- | --- |
| Display | **Archivo** (700/900) | screen titles, card titles, buttons, sticker names. **UPPERCASE** for screen titles and buttons, letter-spacing ~0.12em on small sizes |
| Meta | **Courier Prime** (400) | every count, price, ratio, odds line, description, field value, badge |
| Body | **DM Sans** (400/500) | dialog body copy and long prose only |

Rule of thumb: **numbers and metadata are always typewriter; names and actions are always Archivo.**
Minimum sizes: 11px meta, 12px body. Never centre-align paragraphs.

### 2.3 Rarity is paper stock, not colour — rewrite the presentation half of `models/rarity.py`

`RARITY_COLORS` is currently six saturated hues that fight the art. Replace its *UI use* with a
paper table (keep `RARITY_ORDER`, `RARITY_PATTERN`, `SELECTORS`, `VICE_VALUES` untouched):

```python
# Presentation only. Rarity reads as the stock the label is printed on.
RARITY_PAPER: dict[str, tuple[str, str]] = {   # rarity -> (fill, edge)
    "common":    ("#ffffff", "#c8bda6"),
    "uncommon":  ("#edf0e4", "#b6c2a4"),
    "rare":      ("#e2eaf2", "#a8bdd2"),
    "epic":      ("#ebe2f2", "#bfa9d4"),
    "legendary": ("#f1dfa8", "#b8973f"),   # gold edge; gradient where supported
}
RARITY_INK = "#2f2618"  # label text is always ink, never white-on-colour
```

Where a collection theme colour is used today (`collection.theme_color`), keep it — but demote it to
**cover art and small tints only** (character tile fallbacks, pack art fallbacks). It must never
colour text, buttons or progress bars.

### 2.4 Reusable paper vocabulary — add `components/paper.py`

Build these five helpers first; every screen below is assembled from them.

```python
def ink_button(label, on_click, *, icon=None) -> ft.Control
    # bgcolor=INK, color="#f4efe6", border_radius=0,
    # Archivo 700 10px uppercase letter_spacing 1.2, padding h15 v11,
    # shadow=ft.BoxShadow(0, 0, "#2f261838", ft.Offset(3, 3))  # hard offset, no blur

def tool_button(text, on_click, tooltip) -> ft.Control
    # 32x32 square, 1.5px border INK@35%, Courier 12px, hover fill INK@9%.
    # Replaces every ghost IconButton (edit / unpublish / etc).

def paper_label(text, rarity=None, *, gold=False) -> ft.Control
    # The sticker/rarity/status sign: RARITY_PAPER fill + 1px edge,
    # Courier 400 (8-10px), color RARITY_INK, border_radius=0, tiny drop shadow.
    # Replaces components/rarity_chip.py AND the coloured signs in sticker_slot.

def tape_strip(width=92, angle=-2.5) -> ft.Control
    # 24px tall, bgcolor TAPE @82% opacity, ft.Rotate(radians), dashed side edges
    # faked with 1px borders. Positioned in a Stack, half off the sheet's edge.

def dashed_rule() -> ft.Control
    # 1px dashed ink@22% divider. Replaces every ft.Divider.

def paper_progress(value: float) -> ft.Control
    # 9px tall, trough TRACK_BG with inset shadow, fill = INK.
    # Replaces every ft.ProgressBar (which cannot be styled to match).
```

Card shells: `bgcolor=CARD_BG`, `border_radius=0`, `padding=10`, and
`shadow=ft.BoxShadow(blur_radius=16, spread_radius=-6, color="#00000061", offset=ft.Offset(0, 6))`.
**No rounded corners anywhere except the boards (`border_radius=14`) and pill-free by default** —
paper has square corners.

---

## 3. Screen-by-screen changes

### 3.1 `main.py` — masthead, binder tabs, page (mock <a>5a</a>)

**Delete the `NavigationRail` entirely.** There is no vertical rail in the redesign. The whole
window is one album: a masthead that never changes, a row of binder tabs, and the page under them.
Shell layout, top to bottom, inside a `ft.Column` with `spacing=0`:

**a. Masthead — static, built once, never rebuilt on navigation.**
Padding `26, 30, 30, 34`. A `ft.Row`:
- left, `expand=True`: “MY STICKER ALBUM” Archivo 900 33px uppercase ink; below it, Courier 12.5px
  ink@62% `f"{unique_owned} owned · {total_applied} pasted · {completed} of {total} albums finished"`.
- right, 212px: the taped “DEPOSITED SO FAR” index card from §3.3 (it moves out of `home_view` and
  into the shell — it is global state, not a Home fact).

Expose `refresh_masthead()` on the shell and call it from the two places those numbers change:
after `PackOpeningService.open_pack` commits, and after a vice withdrawal. Navigation must not
call it. **The masthead is the fix for the app re-titling itself on every screen change — no view
may render its own screen title any more.**

**b. Tab row.** `ft.Row(spacing=5)`, `padding.only(left=24)`, `vertical_alignment=END`, one
`ft.Container` per entry — same `_entries` list, keys and `go_*` callbacks as the old rail, and
`rebuild_rail()` keeps its name and its job (re-styling tabs after a selection change).

Per tab: Archivo 700 9px uppercase, `letter_spacing=0.9`, `animate=ft.Animation(280, ft.AnimationCurve.EASE_OUT_BACK)`
plus `animate_offset` and `animate_padding` on the same curve.

| | selected | idle |
| --- | --- | --- |
| `bgcolor` | `TAB_ACTIVE` | `TAB_IDLE` |
| `color` | `INK` | ink@64% |
| `padding` | `11, 20, 17, 20` | `9, 20, 12, 20` |
| `offset` | `ft.Offset(0, 0.03)` | `ft.Offset(0, 0.11)` |
| `shadow` | `BoxShadow(10, ft.Offset(0, -4), "#00000033")` | `BoxShadow(6, ft.Offset(0, -2), "#0000002e")` |

The selected tab is the **same stock as the page**, sits 8px lower than the idle tabs and has no
bottom edge against the page — the seam disappears and the tab reads as part of the sheet. That
single relationship is the whole idea; if you get one thing pixel-right, get this.

*Trapezoid edges:* the mock cuts 9px off each top corner. Flet has no `clip-path`. Ship the tabs as
plain rectangles with `border_radius=ft.border_radius.only(top_left=3, top_right=3)` — do **not**
fake the taper with rotated containers or images.

**c. Page.** `ft.Container(bgcolor=PAGE_BG, expand=True, padding=ft.padding.only(20, 24, 28, 24),`
`shadow=BoxShadow(26, ft.Offset(0, 12), "#0000006b"))`, holding the active view. `border_radius=0`.

**d. Page caption.** Each view's first child is one Courier 11px ink@50% line — not a title:
Home `favourite character · everything you own of them`; Collections `three worlds · pick one to fill`;
Shop `every pack you open records a real deposit`; Vice Shop `spend the savings you earned — with a receipt`;
Creator `live edit · changes publish immediately`; Settings `account, data and sound`.
Album view is the exception: it keeps its collection/character header, since that names *which* album.

Window background stays `DESK_BG`; content padding around the shell 24. The faint desk hatch is
optional (7px diagonal at 2% ink) — skip it if it costs an asset.

### 3.2 `components/sticker_slot.py` — the one functional change

Everything about applied stickers stays exactly as it is. Two changes:

1. **Empty (missing) slots.** Today the mask is tinted `#b0b0b0`, which is the single biggest source
   of “generic” in the current UI — 40% of a fresh album looks broken. Tint it near-white so it
   reads as a pencil ghost on the board:
   ```python
   layers.append(ft.Image(src=mask, width=width, height=height,
                          fit=ft.ImageFit.CONTAIN,
                          color="#e7e3d9", color_blend_mode=ft.BlendMode.SRC_IN))
   ```
   *Optional upgrade (do it if it looks right):* stack two tinted copies — a `#dad4c4` copy scaled
   ~1.02 behind a `#faf8f3` copy — to fake a thin outline around the silhouette. If it produces
   halos on any real mask, drop it and keep the single pale tint.
   The `_EMPTY_BG = "#23232e"` fallback (catalogs with no mask) becomes: white slot, `#d8d2c4`
   1.5px dashed border, `#{number:02d}` in Courier at ink@35%.
2. **Signs become paper.** `_sign()` renders via `paper_label`: `border_radius=0`, Courier not
   Archivo-bold, ink text on rarity paper, 1px edge. The name sign keeps its position
   (`bottom=5, left=6`) and its deliberate overflow onto neighbours. `FOIL ✨` becomes `FOIL` on
   gold paper; `+2` becomes ink-on-white; `READY TO APPLY` becomes ink on `#f1dfa8`.

The owned-but-unpasted “sticker back” keeps its gradient but restyled: `CARD_BG` → `#d9cdb8`
vertical gradient, ink icon at 55%, no rarity tint.

### 3.3 `views/home_view.py`

- Delete `_stat_tile` and the four-tile `ft.Row`. Delete the screen title too — the counts line and
  the savings card both move up into the shell masthead (§3.1a), and Home starts at its page caption.
  Home's own content is now just the polaroid + the owned-stickers board.
- Favourite character becomes a **polaroid**: white container, `padding=9`, the 9:16
  `character_card` art inside, then a caption row *below the art on the white border* — Archivo 14px
  name + Courier 11px `8/10 · Magic Academy`. Rotate `-0.017`. This replaces the floating dark
  `tile_sign` on the card art (keep `tile_sign` for the 16:9 picker tiles, where art bleeds to the
  edge).
- “Change favourite” becomes an underlined Archivo 9.5px uppercase text button, not a `TextButton`
  with an icon.
- The owned-stickers board gets two `tape_strip`s in a `ft.Stack` (top-left −2.5°, bottom-right +2°)
  and `border_radius=0`… **exception**: keep `border_radius=16` on boards if removing it looks
  worse against the desk. Judge it against the mock; the mock uses square boards with tape.
- The two footer `FilledTonalButton`s become `ink_button`s.

### 3.4 `views/collections_view.py` + `components/collection_card.py`

- Card: 328px, `box_sizing` equivalent — set `width=328` on the outer container and put the 10px
  padding *inside* it so three cards fit a 1028px content area with 20px gaps.
- Order: 16:9 cover art (unchanged source), then Archivo 17px name, Courier 11.5px description
  (2 lines, ellipsis, min 32px tall so cards align), then a baseline row of Archivo 900 18px
  `applied` + Courier 11px `of {total} pasted · chars {done}/{total}`, then `paper_progress`,
  then `ink_button("OPEN ALBUM")` + spacer + two `tool_button`s (`ed`, `un` — keep the existing
  tooltips verbatim).
- Delete the percentage figure (the bar says it) and the `ft.ProgressBar`.
- The revert dialog keeps its copy; restyle: `CARD_BG` surface, Archivo title, DM Sans body,
  `ink_button` confirm with `STAMP_RED` background.

### 3.5 `views/shop_view.py` + `components/pack_card.py`

- Pack card = 298px, and it should read as a **pack**: a 16px `CARD_BG` strip on top with
  `border_bottom=2px dashed ink@28%` and three 5px ink@30% squares centred in it (the crimp), then
  the cream body.
- Body: 16:9 pack art → Archivo 16px name → Courier 11px collection name (ink@55%, **not** the theme
  colour) → `dashed_rule` → Courier 11px odds line (`5 stickers · 10% foil · 🌶️ 30%`) → footer row:
  price in a **stamp** (2px ink@55% border, Archivo 900 15px, `ft.Rotate(-0.035)`) + spacer +
  `ink_button("DEPOSIT & OPEN")`.
- Price stops being green. Money is ink; savings is not a reward colour.
- Header: “SHOP” Archivo 900 30px uppercase + the savings line in Courier beside it, same baseline.

### 3.6 `views/album_view.py`

- Header: Archivo 900 collection/character name; description in Courier ink@60%; progress as
  Archivo 900 count + `paper_progress` (220px) — no `ft.ProgressBar`, no `GREY_300`.
- The character sidebar strip keeps its white background, `spacing=0` and blended tiles. Add a
  `tape_strip` at its top edge and drop `border_radius` to 0 to match the boards.
- Everything else in this file (slide animation, stamp settle, dialogs) is untouched.

### 3.7 `views/creator_view.py` — worktable

- “LIVE — edits apply…” green text becomes a **stamp**: 2px `STAMP_RED` border, Archivo 900 10px
  `LIVE EDIT`, `ft.Rotate(-0.05)`, opacity 0.9, next to the title — plus one Courier line
  underneath: `edits apply to the published collection immediately · progress is kept`.
- Character list: cream index cards, 214px, 52×30 tile thumbnail + Archivo 12px name + Courier 10px
  `n/15 slots` + a 14px filled ink square for “complete” (replacing the green check icon).
- Right panel: cream sheet. Text fields become **ruled lines** — `ft.TextField` with
  `border=ft.InputBorder.UNDERLINE`, `border_color=INK@35%`, Courier 15px value, and the label
  above in Archivo 8.5px uppercase ink@50%.
- Slot grid: white 3:4 tiles at `border_radius=0` with a 1px ink@20% shadow, `#01` in Courier
  top-left, Courier name label bottom-centre on rarity paper. Named-but-artless slots show the pale
  pencil ghost from §3.2, not a coloured gradient.
- “Tile…”, “Card…”, “Cover image…” become `tool_button`-style outlined controls; “Done” an
  `ink_button`.

### 3.9 The sticker inspect dialog (mock <a>6a</a>)

The current dialog is a rounded box with centred, stacked metadata and a real layout bug: the
`Spare copies: N` label sits on top of the button row. Rebuild it as a **catalogue slip**:
`ft.AlertDialog` with `shape=ft.RoundedRectangleBorder(radius=0)`, `bgcolor=CARD_BG`,
`content_padding=ft.padding.symmetric(24, 26)`, `barrier_color="#0000009e"`, no `title` and no
`actions` — the slip builds its own footer so nothing can float over it.

772px wide, `ft.Row(spacing=24)`:

**Left, 296px:** white container, `padding=10`, holding the 3:4 art at 276×368. Nothing else — no
border, no radius, no rarity tint on the art.

**Right, expand:** a single left-aligned `ft.Column` — never centred, one fact per line:
1. Row: rarity `paper_label` + Courier 10.5px ink@50% sticker id.
2. Name — Archivo 900 25px uppercase ink, `max_lines=2`.
3. Courier 11.5px ink@60%: `f"{character} · {collection} · {state}"` where state is
   `applied to the board` / `owned, not applied`. This single line replaces the old
   `Character:` and `Applied · Normal` lines — the variant belongs to the switch now, not to prose.
4. `dashed_rule`, then flavour text: Courier 12.5px, `line_height=1.65`, ink@82%. Not italic
   (Courier Prime italic is a separate face — skip it), quoted with real quote marks.
5. `dashed_rule`, then **VARIANT ON THE BOARD** (Archivo 8.5px uppercase ink@50%) and a two-position
   paper switch: `NORMAL` and `FOIL`, 8×16 padding, Archivo 700 9.5px uppercase.
   - selected `NORMAL`: white fill, `rgba(47,38,24,.42)` 1px edge, small shadow.
   - selected `FOIL`: the gold foil gradient, `GOLD` edge.
   - unselected: ink@7% fill, ink@18% edge, ink@45% text, `offset=ft.Offset(0, 0.02)` — it sits
     *pressed down*, which is what makes the pair read as physical.
   - **no foil copy owned:** the `FOIL` position renders in the unselected style with
     `disabled=True` and a `tooltip="no foil copy yet"`. Never hide it — its absence is information.
   - Flipping it calls the existing apply-variant path and swaps the art through an
     `ft.AnimatedSwitcher(duration=300, transition=FADE)`; the foil sheen is the same overlay used
     on foil slots. If the collection has no foil art file, tint-sheen the normal art rather than
     failing.
6. Spacer (`expand=True`), then footer:
   - one Courier 11px ink@60% line: `f"{spares} spare copies · worth {points} vice points"`
     (`0 spare copies` when none — the line stays, the button below it disables);
   - a Row: `ink_button` `CONVERT SPARES → +N VICE` with `expand=True`, and an outlined button
     `▶ VOICE LINE`. Full words on both — the bare `♪` glyph goes away. Disable the voice button
     with a tooltip when the character has no clip.

Close is a Courier `×` at 15px ink@50% pinned top-right of the slip (`ft.Stack`), not a `CLOSE`
button in the footer — the footer is for actions that change something.

### 3.10 Foil spares must be visible on the board

Today the only way to learn that a spare copy is a **foil** is to open the dialog. Fix it in
`components/sticker_slot.py` where the duplicate-count sign is built: the `+N` sign keeps its
position and its Courier type, but takes gold stock when any of those spares is foil.

```python
# spare_is_foil: True if at least one unapplied duplicate of this sticker is a foil copy
if spare_is_foil:
    fill, edge, text = GOLD_PAPER, GOLD, INK      # "#f1dfa8", GOLD
else:
    fill, edge, text = "#ffffff", "#00000038", INK
```

Same rule anywhere else the `+N` chip appears (album boards, Home's owned sheet, the character
picker tiles). It needs one new read from the inventory — a per-sticker `has_foil_spare` flag
alongside the existing spare count. **Read-only: do not change how variants are stored or applied.**
Where a slot already shows the gold `FOIL` sign because the *applied* copy is foil, the `+N` stays
white — gold on the count means "there's a foil in the pile you haven't used".

### 3.8 `views/vice_shop_view.py`, `views/settings_view.py`

Not mocked. Apply §2 mechanically: cream panels, ink type, Courier metadata, `ink_button`,
`paper_progress`, `paper_label`, `dashed_rule`. No new layout ideas — parity only.

---

## 4. The pack-opening animation (`views/pack_result_view.py`)

This is the emotional peak and gets the motion budget. **Rebuild this view**; keep its inputs
(`PackOpenResult`) and its outputs (`nav.go_shop`, `nav.go_album`).

### 4.1 Structure

One `ft.Stack` (600×660 logical, centred, `clip_behavior=ANTI_ALIAS`) containing, in paint order:

1. **Shadow** — 100×14 blurred ink ellipse under the pack, opacity 0 → 1 on land.
2. **The five cards** — 132×176 white containers at `left=234, top=390`, each holding the sticker
   art (`sticker_art`) + `paper_label`s. Painted **behind** the pack.
3. **Pack body** — 150×214 at `left=225, top=370`, pack art or `cover_band` fallback.
4. **Crimp** — 150×18 cream strip at `top=354` with the dashed bottom border.
5. **Vignette** — full-stack radial dim, only for legendary/foil.
6. **Album marker** — 92×66 dashed outline, bottom-right, the flight target for beat 6.

> **The one structural trick:** the cards are always *behind* the pack and each presented card
> travels far enough up to clear the pack's top edge entirely. So a card emerging from the mouth
> needs **no clipping and no masking** — the pack simply covers it until it is out. Do not try to
> mask or clip; Flet will fight you.

Measured geometry from the approved mock (stage-relative, before scaling):
`card rest (234, 390)` · `fan: dx=(i−2)×27, dy=−48−(4−i)×2, rotate=(i−2)×5°` ·
`focus: dy=−270, scale 1.55` · `filed: (+215, +255), scale 0.2, opacity 0`.

### 4.2 Timeline

One `page.run_task` coroutine owns the whole sequence and stagger (Flet has no per-child delay, so
stagger = `await asyncio.sleep(0.07)` between property sets). After **every** sleep, bail out if
`control.page is None` — exactly the guard `album_view._settle_stamp` already uses.

| # | Beat | What animates | Property | Duration / curve |
| --- | --- | --- | --- | --- |
| 0 | Rest | pack sits on the desk, cards hidden (opacity 0), shadow on | — | — |
| 1 | Land | pack `offset (0,−2.9) → 0`, `scale 1.06 → 1.00`, shadow fades in | `animate_offset`, `animate_scale`, `animate_opacity` | 460ms `EASE_OUT_BACK` |
| 2 | Tear | crimp `offset y −0.55` + `rotate −0.38rad` + `opacity → 0`; body dips to `.975` and back | `animate_offset`, `animate_rotation`, `animate_opacity` | 300ms `EASE_IN` |
| 3 | Fan | 5 cards become visible and slide to fan poses, 70ms apart | `animate_offset`, `animate_rotation` | 320ms each, `EASE_OUT` |
| 4 | Present | focus card to `dy −270`, `scale 1.55`; its labels stamp in `scale 1.4 → 1` | `animate_offset`, `animate_scale` | 380ms `EASE_OUT_BACK`; labels 220ms |
| 5 | Recede | previously revealed cards → `opacity .4, scale .92` in the fan | `animate_opacity`, `animate_scale` | 300ms `EASE_OUT` |
| 6 | File | on Continue: all five to the album marker, 60ms apart | `animate_offset`, `animate_scale`, `animate_opacity` | 380ms `EASE_IN` |

Beat 1 fires on view open (the deposit is already committed). Beats 4–5 fire per “Reveal next”.

**The fan is the progress indicator** — delete the five `dots`; keep the `n / 5` counter in Courier.

### 4.3 Rarity payoff, layered onto beat 4 (not separate animations)

- **Common / Uncommon** — nothing extra. Speed is the reward.
- **Rare / Epic** — harder label overshoot; +80ms hold before the button re-enables.
- **Legendary or any foil** — vignette fades in (`radial-gradient` equivalent: a full-stack
  container, `#140e0859`, opacity 0 → 1 over 400ms), the existing `FoilShimmer` `ShaderMask`
  sweeps the silhouette, card holds 400ms longer.
- Sound: `play_stamp` on beat 1, a new paper-tear cue on beat 2 (add
  `TEAR_SOUND = "sounds/tear.wav"` to `audio_player.py`, no-op if the file is absent — the module
  already degrades gracefully), the sticker's own voice line on beat 4 via `play_stamp_then`.

### 4.4 Controls

Footer row: `ink_button("REVEAL NEXT")`, outlined `REVEAL ALL`, Courier `3 / 5`. On the last card
they swap to `ink_button("CONTINUE TO SHOP")` + outlined `OPEN ALBUM`.
**“Reveal all” must skip straight to the final state with no queued animation** — cancel the
coroutine's pending sleeps, snap every property, then render.

---

## 5. Order of work

1. `components/theme.py` + `components/paper.py` + `main.py` light theme, masthead, binder tabs and
   page (§3.1 — the `NavigationRail` dies here). *(App must run and be navigable after this step,
   even if ugly.)*
2. `models/rarity.py` paper table + `paper_label`; delete `components/rarity_chip.py` usages.
3. `components/sticker_slot.py` (empty-slot ghost + paper signs) — verify against a real album with
   ~40% missing stickers.
4. `collection_card.py`, `pack_card.py`, `character_tiles.py`.
5. `home_view.py`, `collections_view.py`, `shop_view.py`, `album_view.py`.
6. `creator_view.py`.
7. `pack_result_view.py` rebuild + animation.
8. The inspect dialog (§3.9) and the gold `+N` foil-spare chip (§3.10).
8. `vice_shop_view.py`, `settings_view.py` parity pass.

Run `pytest` after each step. Existing tests cover services and live edit, not styling — if a test
fails you changed behaviour, so revert that part.

---

## 6. Acceptance criteria

- [ ] No `#282431` / `#332e3e` / `#211d2a` / dark-mode colours remain; `page.theme_mode` is LIGHT.
- [ ] A fresh album (0 stickers applied) reads as a white sheet of pale pencil silhouettes — no
      mid-grey blobs, no dark tiles.
- [ ] Applied stickers still blend edge-to-edge: no borders, no gaps, no tint, `spacing=0`.
- [ ] No saturated rarity fills anywhere; every rarity label is ink on paper stock.
- [ ] Every count, price, ratio and odds string renders in Courier Prime; every title and button in
      uppercase Archivo.
- [ ] `ft.ProgressBar`, `ft.Divider` and ghost `IconButton`s are gone from the redesigned views.
- [ ] Pack opening: land → tear → fan → present plays within ~1.9s to the first card; “Reveal all”
      is instant; navigating away mid-reveal raises nothing in the log.
- [ ] No view renders a screen title, and the masthead numbers change only after a pack open or a
      vice withdrawal — never on navigation.
- [ ] The selected binder tab is exactly `PAGE_BG` and shows no seam against the page below it.
- [ ] Six tabs fit the 1000px minimum width without wrapping (shorten “Vice Shop” before you wrap).
- [ ] Window at the 1000×700 minimum: no clipped cards, no horizontal scroll on Collections or Shop
      (three 328px cards + 20px gaps must fit or wrap cleanly).
- [ ] Inspect dialog: square corners, nothing overlaps at any spare count (test 0, 1, 12), and the
      FOIL position is visible-but-disabled when no foil copy is owned.
- [ ] A sticker with a foil spare shows a gold `+N` on the board without opening the dialog.
- [ ] `python main.py` starts clean; no new warnings in the log.

## 7. Do not

- Do not add gradients as decoration, glows, glass/blur, or rounded “pill” chips.
- Do not introduce a second accent colour; theme colours belong to cover art only.
- Do not add emoji beyond the existing 🌶️.
- Do not hand-draw SVG/vector icons; outlined squares and Material icons at ink colours are fine.
- Do not refactor services, repositories or models while re-skinning.
- Do not touch the white boards.
