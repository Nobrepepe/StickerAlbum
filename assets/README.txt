Sticker Album asset guide
=========================

All paths below are relative to this assets/ directory. Catalog artwork and
voice lines are optional: when they are absent the app renders a placeholder
or silently skips playback. The bundled fonts are required for the intended
Kraft & Tape UI.


APP FONTS (required and committed)
----------------------------------

  fonts/Archivo-Variable.ttf       display titles, names, and buttons
  fonts/CourierPrime-Regular.ttf   counts, prices, ratios, and metadata
  fonts/DMSans-Variable.ttf        body copy and longer prose

The corresponding *-OFL.txt license files must remain beside the fonts.


APP SOUND CUES
--------------

These exact WAV paths are used by the app:

  sounds/stamp.wav                 pack landing and sticker application
  sounds/tear.wav                  pack crimp tearing
  sounds/reveal.wav                normal sticker reveal in an opened pack
  sounds/new.wav                   newly acquired sticker reveal
  sounds/spicy.wav                 spicy sticker reveal (replaces reveal.wav
                                   and new.wav for that card so the spicy cue
                                   is audible)

Reveal priority is spicy.wav, then new.wav, then reveal.wav. Missing cues
safely no-op, but all five are needed for the complete sound
design.


COLLECTION AND PACK ART
-----------------------

Supported image formats: png, jpg, jpeg, and webp.

  covers/<COLLECTION_ID>.png       16:9 landscape collection cover
                                   Example: covers/CST.png

  packs/<PACK_ID>.png              16:9 landscape pack image
                                   Example: packs/CST_standard.png

The collection and pack JSON records may point to another relative filename,
but the paths above are the standard convention. Pack images are configured
in data/packs.json; they are not imported by the Creator.


CHARACTER ART
-------------

  portraits/<CHARACTER_ID>_tile.png
                                   16:9 landscape sidebar/picker banner
                                   Example: portraits/CST_C01_tile.png

  portraits/<CHARACTER_ID>_card.png
                                   9:16 portrait full-body character card
                                   Example: portraits/CST_C01_card.png

Character IDs use <COLLECTION_ID>_C01 through <COLLECTION_ID>_C10.


STICKER ART AND FOIL MASKS
--------------------------

  stickers/<STICKER_ID>.png        3:4 sticker artwork
                                   Example: stickers/CST_008.png

  stickers/<STICKER_ID>_mask.png   3:4 foil shimmer alpha mask

Sticker artwork should retain the white vignette/edge used to blend adjacent
stickers into the app's pure-white, zero-gap boards.

A foil mask must have a transparent background and an opaque subject
silhouette. Its color is ignored; only alpha is used. It must have exactly
the same canvas, crop, and framing as the corresponding sticker artwork so
the shimmer aligns and never reaches the white vignette.

Regular sticker IDs are <COLLECTION_ID>_001 through _100. Spicy sticker IDs
are <COLLECTION_ID>_101 through _150.


STICKER VOICE LINES
-------------------

  sounds/<STICKER_ID>.<ext>        optional per-sticker voice/flavor line
                                   Example: sounds/CST_008.mp3

Supported voice formats: mp3, wav, ogg, and m4a. The Creator preserves the
chosen extension and writes the exact relative path into the sticker catalog.


CREATOR IMPORTS
---------------

The Creator copies collection covers, character tile/card art, sticker art,
and sticker voice lines into the convention-named locations above. Foil masks,
pack images, and the five app sound cues are supplied manually.
