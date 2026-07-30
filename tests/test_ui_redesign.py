import flet as ft

from types import SimpleNamespace

from main import AppShell
from components.paper import paper_progress
from components.sticker_dialog import open_sticker_dialog
from components.sticker_slot import build_sticker_slot
from components.theme import (
    BOARD_BG, CARD_BG, DESK_BG, PAGE_BG, TAB_ACTIVE, TAB_IDLE
)
from models.rarity import RARITY_INK, RARITY_PAPER
from models.results import OpenedSticker, PackOpenResult
from views.pack_result_view import (
    MAX_FAN,
    PACK_H,
    PACK_W,
    STAGE_H,
    _PackReveal,
    build_pack_result,
)


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
    assert isinstance(reveal.crimp.content, ft.Stack)
    reveal._raise_card(0)
    assert reveal.stage.controls.index(reveal.cards[0]) > max(
        reveal.stage.controls.index(card) for card in reveal.cards[1:]
    )
    assert reveal.stage.controls.index(reveal.cards[0]) < reveal.stage.controls.index(
        reveal.pack_body
    )
    reveal._on_reveal_all(None)

    assert len(reveal.cards) == 7
    assert reveal.counter.value == "7 / 7"
    assert sum(bool(card.opacity) for card in reveal.cards) == MAX_FAN

    wrapper = build_pack_result(page, ctx, nav, result)
    assert wrapper.expand is True
    assert wrapper.content.controls[1].stage.height == STAGE_H == 400


def test_opening_pack_uses_landscape_pack_art_ratio():
    assert PACK_W / PACK_H == 16 / 9


def test_shell_uses_persistent_masthead_tabs_and_page():
    calls = {"summary": 0, "updates": 0}

    def summary():
        calls["summary"] += 1
        return SimpleNamespace(
            unique_owned=12,
            total_applied=7,
            completed_collections=1,
            total_collections=3,
            total_saved=2500,
        )

    ctx = SimpleNamespace(
        summary=SimpleNamespace(home_summary=summary),
        settings=SimpleNamespace(
            state=SimpleNamespace(creator_enabled=True)
        ),
    )
    page = SimpleNamespace(update=lambda: calls.__setitem__(
        "updates", calls["updates"] + 1
    ))
    shell = AppShell(page, ctx)
    masthead = shell.masthead

    assert isinstance(shell.root, ft.Container)
    assert shell.content.bgcolor == PAGE_BG
    assert len(shell.tabs_row.controls) == 6
    assert shell.tabs_row.wrap is not True
    assert shell._tabs["home"].bgcolor == TAB_ACTIVE
    assert shell._tabs["shop"].bgcolor == TAB_IDLE

    shell._set("shop", ft.Container())

    assert shell.masthead is masthead
    assert calls["summary"] == 1
    assert shell._tabs["shop"].bgcolor == TAB_ACTIVE
    assert shell.content.content is not None


def _walk(control):
    yield control
    for child in control._get_children():
        yield from _walk(child)


def test_sticker_inspection_is_a_catalogue_slip(
    repos, state_repo, album_service
):
    sticker = repos["stickers"].get("TST_001")
    character = repos["characters"].get(sticker.character_id)

    class Page:
        opened = None

        def open(self, control):
            self.opened = control

        def close(self, control):
            pass

    page = Page()
    open_sticker_dialog(
        page,
        album_service,
        sticker,
        character,
        "Testland",
        on_change=lambda _sticker: None,
    )

    dialog = page.opened
    controls = list(_walk(dialog))
    variants = {c.data: c for c in controls if c.data in {
        "variant-normal", "variant-foil"
    }}

    assert dialog.bgcolor == CARD_BG
    assert dialog.modal is False
    assert dialog.shape.radius == 0
    assert dialog.actions == []
    assert dialog.content.width == 772
    assert variants["variant-normal"].disabled is True
    assert variants["variant-foil"].disabled is True
    assert variants["variant-foil"].tooltip == "No foil copy yet"


def test_duplicate_sign_is_gold_only_when_a_foil_spare_exists(
    repos, state_repo, album_service
):
    sticker = repos["stickers"].get("TST_001")
    state_repo.add_copy(sticker.id, "normal")
    state_repo.add_copy(sticker.id, "foil")
    album_service.apply(sticker, "normal")

    slot = build_sticker_slot(album_service, sticker, lambda _sticker: None)
    signs = [
        control for control in _walk(slot)
        if isinstance(control, ft.Container)
        and isinstance(control.content, ft.Text)
        and control.content.value == "+1"
    ]
    assert len(signs) == 1
    assert signs[0].bgcolor == "#f1dfa8"
