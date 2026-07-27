from types import SimpleNamespace

from components.paper import paper_progress
from components.theme import BOARD_BG, DESK_BG
from models.rarity import RARITY_INK, RARITY_PAPER
from models.results import OpenedSticker, PackOpenResult
from views.pack_result_view import MAX_FAN, _PackReveal


def test_paper_palette_preserves_white_board_and_dark_ink():
    assert DESK_BG == "#c8b9a2"
    assert BOARD_BG == "#ffffff"
    assert RARITY_INK == "#2f2618"
    assert set(RARITY_PAPER) == {
        "common", "uncommon", "rare", "epic", "legendary", "spicy"
    }


def test_paper_progress_clamps_value():
    assert paper_progress(-1, width=100).content.width == 0
    assert paper_progress(2, width=100).content.width == 100


def test_pack_reveal_supports_bonus_items_with_bounded_fan(catalog):
    collection, _characters, stickers, packs = catalog
    items = tuple(
        OpenedSticker(sticker=stickers[i], style="normal", is_new=True)
        for i in range(7)
    )
    result = PackOpenResult(pack=packs[0], items=items, deposit=packs[0].price)
    page = SimpleNamespace(run_task=lambda *args: None)
    ctx = SimpleNamespace(
        collections=SimpleNamespace(get=lambda _id: collection)
    )
    nav = SimpleNamespace(go_shop=lambda: None, go_album=lambda _id: None)

    reveal = _PackReveal(page, ctx, nav, result)
    reveal._on_reveal_all(None)

    assert len(reveal.cards) == 7
    assert reveal.counter.value == "7 / 7"
    assert sum(bool(card.opacity) for card in reveal.cards) == MAX_FAN
