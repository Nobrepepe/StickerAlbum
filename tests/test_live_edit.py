import json

import pytest

from models.catalog import Collection
from repositories.collection_repository import CollectionRepository
from repositories.draft_repository import DraftRepository
from repositories.user_state_repository import UserStateRepository
from services.creator_service import CreatorError, CreatorService


@pytest.fixture
def env(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "collections.json").write_text("[]")
    (data_dir / "characters.json").write_text("[]")
    (data_dir / "stickers.json").write_text("[]")
    drafts = DraftRepository(data_dir / "drafts.json")
    collections = CollectionRepository([])
    state = UserStateRepository(tmp_path / "user_state.json")
    service = CreatorService(drafts, collections, data_dir, tmp_path / "assets", state)

    draft = service.create_collection("LVE", "Liveworld", "desc", "#123456")
    for c in draft.characters:
        c.name = f"Char {c.index}"
        for s in c.stickers:
            s.name = f"Sticker {c.index}-{s.position}"
    service.save(draft)
    service.publish("LVE")

    state.add_copy("LVE_001", "normal")
    state.set_placement("LVE_001", "normal")
    state.add_savings(1000)
    state.save()
    return service, drafts, data_dir, state


def test_load_live_prefills_and_stores_no_draft(env):
    service, drafts, _, _ = env
    live = service.load_live("LVE")
    assert live.name == "Liveworld"
    assert live.characters[0].name == "Char 1"
    assert live.characters[0].stickers[0].name == "Sticker 1-1"
    assert service.collection_complete(live)
    assert drafts.get("LVE") is None  # never becomes a draft


def test_apply_live_edits_updates_catalog_in_place(env, tmp_path):
    service, drafts, data_dir, _ = env
    live = service.load_live("LVE")
    live.name = "Renamed World"
    live.description = "new desc"
    live.theme_color = "#654321"
    live.characters[0].name = "Renamed Char"
    live.characters[0].stickers[1].name = "Renamed Sticker"
    live.characters[0].stickers[1].flavor_text = "new flavor"

    src = tmp_path / "art.png"
    src.write_bytes(b"png")
    service.attach_image(live, "sticker", str(src), 1, 2, persist=False)
    snd = tmp_path / "v.mp3"
    snd.write_bytes(b"mp3")
    service.attach_sound(live, str(snd), 1, 2, persist=False)

    service.apply_live_edits(live)

    cols = json.loads((data_dir / "collections.json").read_text())
    assert cols[0]["name"] == "Renamed World"
    assert cols[0]["theme_color"] == "#654321"
    chars = json.loads((data_dir / "characters.json").read_text())
    assert next(c for c in chars if c["id"] == "LVE_C01")["name"] == "Renamed Char"
    stickers = json.loads((data_dir / "stickers.json").read_text())
    s2 = next(s for s in stickers if s["id"] == "LVE_002")
    assert s2["name"] == "Renamed Sticker"
    assert s2["flavor_text"] == "new flavor"
    assert s2["image"] == "stickers/LVE_002.png"
    assert s2["sound"] == "sounds/LVE_002.mp3"
    # structure untouched
    assert s2["rarity"] == "common"
    assert s2["number"] == 2
    assert s2["spicy"] is False
    assert len(stickers) == 150
    # and no phantom draft appeared
    assert drafts.get("LVE") is None


def test_live_edits_keep_progress_untouched(env):
    service, _, _, state = env
    live = service.load_live("LVE")
    live.characters[0].name = "Renamed"
    service.apply_live_edits(live)

    reloaded = UserStateRepository(state._path)
    assert reloaded.get_quantity("LVE_001", "normal") == 1
    assert reloaded.get_placement("LVE_001") == "normal"
    assert reloaded.state.total_saved == 1000


def test_live_edits_reject_blank_names(env):
    service, _, data_dir, _ = env
    live = service.load_live("LVE")
    live.characters[2].stickers[4].name = "   "
    with pytest.raises(CreatorError, match="stay complete"):
        service.apply_live_edits(live)
    # nothing was written
    stickers = json.loads((data_dir / "stickers.json").read_text())
    assert next(s for s in stickers if s["id"] == "LVE_025")["name"] == "Sticker 3-5"

    live2 = service.load_live("LVE")
    live2.characters[0].name = ""
    with pytest.raises(CreatorError, match="needs a name"):
        service.apply_live_edits(live2)


def test_load_live_unknown_code_rejected(env):
    service, *_ = env
    with pytest.raises(CreatorError, match="No published collection"):
        service.load_live("XXX")
