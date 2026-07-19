Art assets live here. Everything is optional; the app shows styled
placeholders for anything missing. Formats: png, jpg, jpeg, webp.

  stickers/<STICKER_ID>.png        sticker art, e.g. stickers/HGT_008.png
  stickers/<STICKER_ID>_mask.png   foil shimmer mask: TRANSPARENT background
                                   with an opaque silhouette of the subject
                                   (any color; only the alpha matters).
                                   Same aspect ratio/framing as the sticker
                                   art so the shimmer lines up. The shimmer
                                   only plays inside the silhouette, never
                                   on the white vignette edges.
  portraits/<CHARACTER_ID>.png     small square-ish portrait (avatars)
  portraits/<CHARACTER_ID>_tile.png
                                   16:9 LANDSCAPE banner for the album
                                   sidebar (e.g. the character's eyes),
                                   e.g. portraits/CST_C01_tile.png
  portraits/<CHARACTER_ID>_card.png
                                   9:16 PORTRAIT full-body card shown when
                                   the character is selected in the album,
                                   e.g. portraits/CST_C01_card.png
  covers/<COLLECTION_ID>.png       16:9 widescreen collection cover,
                                   e.g. covers/CST.png
  packs/<PACK_ID>.png              16:9 widescreen pack art
  sounds/<STICKER_ID>.mp3          optional voice line for the sticker's
                                   flavor text (mp3/wav/ogg/m4a)

Tile, card, sticker, cover, and sound files can all be imported from the
Creator screen, which copies them here under these names automatically.

Character IDs are <CODE>_C01 .. <CODE>_C10 (so the first character of a
collection with code CST is CST_C01). Sticker IDs are <CODE>_001 .. _100
for the regular stickers and <CODE>_101 .. _150 for the spicy ones.
