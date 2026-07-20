import json

import pytest

from models.catalog import Collection
from repositories.collection_repository import CollectionRepository
from repositories.draft_repository import DraftRepository
from repositories.user_state_repository import UserStateRepository
from services.creator_service import CreatorError, CreatorService, slot_from_number


@pytest.fixture
def env(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # One unrelated published collection to prove it survives untouched.
    (data_dir / "collections.json").write_text(json.dumps(
        [{"id": "HGT", "name": "Heights", "description": ""}]))
    (data_dir / "characters.json").write_text("[]")
    (data_dir / "stickers.json").write_text("[]")
    drafts = DraftRepository(data_dir / "drafts.json")
    collections = CollectionRepository([Collection(id="HGT", name="Heights", description="")])
    state = UserStateRepository(tmp_path / "user_state.json")
    service = CreatorService(drafts, collections, data_dir, tmp_path / "assets", state)
    return service, drafts, data_dir, state


def _published_collection(service, tmp_path, code="NEW"):
    draft = service.create_collection(code, "Testworld", "a world", "#123456")
    for c in draft.characters:
        c.name = f"Char {c.index}"
        c.description = f"About char {c.index}"
        for s in c.stickers:
            s.name = f"Sticker {c.index}-{s.position}"
            s.flavor_text = f"Flavor {c.index}-{s.position}"
    src = tmp_path / "a.png"
    src.write_bytes(b"png")
    service.attach_image(draft, "sticker", str(src), 1, 2)   # NEW_002
    snd = tmp_path / "v.ogg"
    snd.write_bytes(b"ogg")
    service.attach_sound(draft, str(snd), 1, 2)
    service.save(draft)
    service.publish(code)


def test_slot_from_number_mapping():
    assert slot_from_number(1) == (1, 1)
    assert slot_from_number(100) == (10, 10)
    assert slot_from_number(101) == (1, 11)
    assert slot_from_number(105) == (1, 15)
    assert slot_from_number(106) == (2, 11)
    assert slot_from_number(150) == (10, 15)
    with pytest.raises(ValueError):
        slot_from_number(151)


def test_unpublish_restores_a_complete_prefilled_draft(env, tmp_path):
    service, drafts, data_dir, _ = env
    _published_collection(service, tmp_path)

    draft = service.unpublish("NEW")

    assert service.collection_complete(draft)
    assert draft.name == "Testworld"
    assert draft.description == "a world"
    assert draft.theme_color == "#123456"
    c1 = draft.characters[0]
    assert c1.name == "Char 1"
    assert c1.description == "About char 1"
    assert c1.stickers[1].name == "Sticker 1-2"
    assert c1.stickers[1].flavor_text == "Flavor 1-2"
    assert c1.stickers[1].image == "stickers/NEW_002.png"
    assert c1.stickers[1].sound == "sounds/NEW_002.ogg"
    # spicy slots come back to positions 11-15
    assert draft.characters[3].stickers[12].name == "Sticker 4-13"
    # persisted, not just returned
    assert DraftRepository(data_dir / "drafts.json").get("NEW") is not None


def test_unpublish_removes_collection_from_catalog(env, tmp_path):
    service, _, data_dir, _ = env
    _published_collection(service, tmp_path)
    service.unpublish("NEW")

    assert [c["id"] for c in json.loads((data_dir / "collections.json").read_text())] == ["HGT"]
    assert json.loads((data_dir / "characters.json").read_text()) == []
    assert json.loads((data_dir / "stickers.json").read_text()) == []


def test_unpublish_erases_only_that_collections_progress(env, tmp_path):
    service, _, _, state = env
    _published_collection(service, tmp_path)

    state.add_copy("NEW_002", "foil", 2)
    state.set_placement("NEW_002", "foil")
    state.add_copy("HGT_001", "normal")
    state.set_placement("HGT_001", "normal")
    state.state.favorite_character_id = "NEW_C01"
    state.state.last_collection_id = "NEW"
    state.add_savings(5000)
    state.save()

    service.unpublish("NEW")

    assert state.total_owned("NEW_002") == 0
    assert state.get_placement("NEW_002") is None
    assert state.total_owned("HGT_001") == 1          # untouched
    assert state.get_placement("HGT_001") == "normal"
    assert state.state.favorite_character_id is None  # was from NEW
    assert state.state.last_collection_id is None
    assert state.state.total_saved == 5000            # savings kept
    # persisted
    reloaded = UserStateRepository(state._path)
    assert reloaded.total_owned("NEW_002") == 0
    assert reloaded.state.total_saved == 5000


def test_unpublish_keeps_unrelated_favorite(env, tmp_path):
    service, _, _, state = env
    _published_collection(service, tmp_path)
    state.state.favorite_character_id = "HGT_C01"
    state.save()
    service.unpublish("NEW")
    assert state.state.favorite_character_id == "HGT_C01"


def test_unpublish_unknown_or_drafted_code_rejected(env, tmp_path):
    service, *_ = env
    with pytest.raises(CreatorError, match="No published collection"):
        service.unpublish("XXX")
    service.create_collection("WIP", "Draft only")
    with pytest.raises(CreatorError, match="already a draft"):
        service.unpublish("WIP")


def test_unpublish_then_publish_round_trip(env, tmp_path):
    service, _, data_dir, _ = env
    _published_collection(service, tmp_path)
    service.unpublish("NEW")
    service.publish("NEW")

    stickers = [s for s in json.loads((data_dir / "stickers.json").read_text())
                if s["collection_id"] == "NEW"]
    assert len(stickers) == 150
    by_id = {s["id"]: s for s in stickers}
    assert by_id["NEW_002"]["sound"] == "sounds/NEW_002.ogg"
    assert by_id["NEW_002"]["image"] == "stickers/NEW_002.png"
    assert by_id["NEW_101"]["spicy"] is True
