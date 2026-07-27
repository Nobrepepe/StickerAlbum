import json
from collections import Counter

import pytest

from models.catalog import Collection
from models.rarity import RARITY_PATTERN
from repositories.collection_repository import CollectionRepository
from repositories.draft_repository import DraftRepository
from services.creator_service import CreatorError, CreatorService


@pytest.fixture
def env(tmp_path):
    data_dir = tmp_path / "data"
    assets_dir = tmp_path / "assets"
    data_dir.mkdir()
    (data_dir / "collections.json").write_text(json.dumps(
        [{"id": "HGT", "name": "Heights", "description": ""}]
    ))
    (data_dir / "characters.json").write_text("[]")
    (data_dir / "stickers.json").write_text("[]")
    drafts = DraftRepository(data_dir / "drafts.json")
    collections = CollectionRepository([Collection(id="HGT", name="Heights", description="")])
    service = CreatorService(drafts, collections, data_dir, assets_dir)
    return service, drafts, data_dir, assets_dir


def _complete(draft):
    for c in draft.characters:
        c.name = f"Char {c.index}"
        for s in c.stickers:
            s.name = f"Sticker {c.index}-{s.position}"
    return draft


# ---- codes ---------------------------------------------------------------

def test_code_is_normalized_to_uppercase(env):
    service, *_ = env
    draft = service.create_collection("abc", "Test")
    assert draft.id == "ABC"


@pytest.mark.parametrize("bad", ["", "AB", "ABCD", "A1C", "A C", "ÁBC"])
def test_invalid_codes_rejected(env, bad):
    service, *_ = env
    with pytest.raises(CreatorError):
        service.create_collection(bad, "Test")


def test_code_duplicate_with_published_rejected(env):
    service, *_ = env
    with pytest.raises(CreatorError, match="already in use"):
        service.create_collection("HGT", "Clash")
    with pytest.raises(CreatorError, match="already in use"):
        service.create_collection("hgt", "Clash lowercase")


def test_code_duplicate_with_other_draft_rejected(env):
    service, *_ = env
    service.create_collection("NEW", "First")
    with pytest.raises(CreatorError, match="already in use"):
        service.create_collection("NEW", "Second")


def test_name_required(env):
    service, *_ = env
    with pytest.raises(CreatorError, match="name"):
        service.create_collection("NEW", "   ")


# ---- skeleton & completeness ----------------------------------------------

def test_new_draft_has_full_skeleton(env):
    service, *_ = env
    draft = service.create_collection("NEW", "Test")
    assert len(draft.characters) == 10
    assert all(len(c.stickers) == 15 for c in draft.characters)
    # positions 11-15 are the spicy slots
    assert [s.spicy for s in draft.characters[0].stickers] == [False] * 10 + [True] * 5
    assert not service.collection_complete(draft)
    assert service.collection_progress(draft) == (0, 10)


def test_character_completeness_requires_name_and_all_stickers(env):
    service, *_ = env
    draft = service.create_collection("NEW", "Test")
    char = draft.characters[0]
    for s in char.stickers:
        s.name = "x"
    assert not service.character_complete(char)  # no character name yet
    char.name = "Someone"
    assert service.character_complete(char)
    char.stickers[9].name = "  "
    assert not service.character_complete(char)
    assert service.character_progress(char) == (14, 15)


def test_unnamed_spicy_sticker_blocks_completion(env):
    service, *_ = env
    draft = service.create_collection("NEW", "Test")
    char = draft.characters[0]
    char.name = "Someone"
    for s in char.stickers[:10]:  # only the regular ones
        s.name = "x"
    assert not service.character_complete(char)
    assert service.character_progress(char) == (10, 15)
    for s in char.stickers[10:]:
        s.name = "spicy x"
    assert service.character_complete(char)


def test_collection_complete_only_with_all_ten(env):
    service, *_ = env
    draft = _complete(service.create_collection("NEW", "Test"))
    assert service.collection_complete(draft)
    draft.characters[9].name = ""
    assert not service.collection_complete(draft)
    assert service.collection_progress(draft) == (9, 10)


# ---- persistence -----------------------------------------------------------

def test_draft_round_trip(env):
    service, drafts, data_dir, _ = env
    draft = service.create_collection("NEW", "Test", "desc", "#123456")
    draft.characters[2].name = "Charlie"
    draft.characters[2].stickers[4].name = "Fifth"
    draft.characters[2].stickers[4].flavor_text = "flavor"
    service.save(draft)

    reloaded = DraftRepository(data_dir / "drafts.json").get("NEW")
    assert reloaded.name == "Test"
    assert reloaded.theme_color == "#123456"
    assert reloaded.characters[2].name == "Charlie"
    assert reloaded.characters[2].stickers[4].name == "Fifth"
    assert len(reloaded.characters) == 10


def test_corrupted_drafts_backed_up(tmp_path):
    path = tmp_path / "drafts.json"
    path.write_text("{broken")
    repo = DraftRepository(path)
    assert repo.list_all() == []
    assert repo.load_warnings
    assert list(tmp_path.glob("drafts.corrupt-*.json"))


# ---- images ------------------------------------------------------------------

def test_attach_image_copies_and_names_canonically(env, tmp_path):
    service, _, _, assets_dir = env
    draft = service.create_collection("NEW", "Test")
    src = tmp_path / "photo.png"
    src.write_bytes(b"fake-png")

    assert service.attach_image(draft, "cover", str(src)) == "covers/NEW.png"
    assert service.attach_image(draft, "tile", str(src), 3) == "portraits/NEW_C03_tile.png"
    assert service.attach_image(draft, "card", str(src), 3) == "portraits/NEW_C03_card.png"
    assert service.attach_image(draft, "sticker", str(src), 3, 7) == "stickers/NEW_027.png"
    assert (assets_dir / "stickers/NEW_027.png").read_bytes() == b"fake-png"
    assert (assets_dir / "portraits/NEW_C03_tile.png").exists()
    assert draft.characters[2].stickers[6].image == "stickers/NEW_027.png"


def test_attach_sound(env, tmp_path):
    service, _, data_dir, assets_dir = env
    draft = service.create_collection("NEW", "Test")
    src = tmp_path / "voice.mp3"
    src.write_bytes(b"fake-mp3")

    assert service.attach_sound(draft, str(src), 3, 7) == "sounds/NEW_027.mp3"
    assert (assets_dir / "sounds/NEW_027.mp3").read_bytes() == b"fake-mp3"
    assert draft.characters[2].stickers[6].sound == "sounds/NEW_027.mp3"
    # persisted with the draft
    from repositories.draft_repository import DraftRepository
    reloaded = DraftRepository(data_dir / "drafts.json").get("NEW")
    assert reloaded.characters[2].stickers[6].sound == "sounds/NEW_027.mp3"


def test_attach_sound_rejects_bad_extension(env, tmp_path):
    service, *_ = env
    draft = service.create_collection("NEW", "Test")
    src = tmp_path / "voice.txt"
    src.write_bytes(b"x")
    import pytest as _pytest
    with _pytest.raises(CreatorError, match="Unsupported sound type"):
        service.attach_sound(draft, str(src), 1, 1)


def test_publish_carries_sound_field(env, tmp_path):
    service, _, data_dir, _ = env
    draft = _complete(service.create_collection("NEW", "Test"))
    src = tmp_path / "voice.ogg"
    src.write_bytes(b"s")
    service.attach_sound(draft, str(src), 1, 2)
    service.save(draft)
    service.publish("NEW")
    stickers = json.loads((data_dir / "stickers.json").read_text())
    by_id = {s["id"]: s for s in stickers if s["collection_id"] == "NEW"}
    assert by_id["NEW_002"]["sound"] == "sounds/NEW_002.ogg"
    assert by_id["NEW_001"]["sound"] is None


def test_attach_image_rejects_bad_extension(env, tmp_path):
    service, *_ = env
    draft = service.create_collection("NEW", "Test")
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"x")
    with pytest.raises(CreatorError, match="Unsupported image type"):
        service.attach_image(draft, "cover", str(src))


def test_attach_image_replaces_old_extension_file(env, tmp_path):
    service, _, _, assets_dir = env
    draft = service.create_collection("NEW", "Test")
    png = tmp_path / "a.png"
    png.write_bytes(b"png")
    jpg = tmp_path / "b.jpg"
    jpg.write_bytes(b"jpg")
    service.attach_image(draft, "cover", str(png))
    service.attach_image(draft, "cover", str(jpg))
    assert draft.cover_image == "covers/NEW.jpg"
    assert not (assets_dir / "covers/NEW.png").exists()


# ---- publishing -----------------------------------------------------------------

def test_publish_rejects_incomplete(env):
    service, *_ = env
    service.create_collection("NEW", "Test")
    with pytest.raises(CreatorError, match="not complete"):
        service.publish("NEW")


def test_publish_writes_catalog_and_removes_draft(env):
    service, drafts, data_dir, _ = env
    draft = _complete(service.create_collection("NEW", "Test", "a world", "#123456"))
    service.save(draft)
    service.publish("NEW")

    collections = json.loads((data_dir / "collections.json").read_text())
    characters = json.loads((data_dir / "characters.json").read_text())
    stickers = json.loads((data_dir / "stickers.json").read_text())

    assert [c["id"] for c in collections] == ["HGT", "NEW"]
    new_chars = [c for c in characters if c["collection_id"] == "NEW"]
    new_stickers = [s for s in stickers if s["collection_id"] == "NEW"]
    normal = [s for s in new_stickers if not s["spicy"]]
    spicy = [s for s in new_stickers if s["spicy"]]
    assert len(new_chars) == 10
    assert len(normal) == 100
    assert len(spicy) == 50
    assert new_chars[0]["id"] == "NEW_C01"
    assert normal[0]["id"] == "NEW_001"
    assert normal[99]["id"] == "NEW_100"
    assert sorted(s["number"] for s in normal) == list(range(1, 101))
    # spicy stickers number 101-150
    assert sorted(s["number"] for s in spicy) == list(range(101, 151))
    # 3/3/2/1/1 regular slots plus five special spicy slots per character
    per_char = [s["rarity"] for s in normal if s["character_id"] == "NEW_C04"]
    assert per_char == list(RARITY_PATTERN)
    per_char_spicy = [s["rarity"] for s in spicy if s["character_id"] == "NEW_C04"]
    assert per_char_spicy == ["spicy"] * 5
    assert Counter(s["rarity"] for s in new_stickers) == {
        "common": 30, "uncommon": 30, "rare": 20, "epic": 10,
        "legendary": 10, "spicy": 50,
    }
    assert drafts.get("NEW") is None


def test_published_collection_loads_in_catalog_repos(env):
    service, _, data_dir, _ = env
    draft = _complete(service.create_collection("NEW", "Test"))
    service.save(draft)
    service.publish("NEW")

    from repositories.sticker_repository import StickerRepository
    stickers = StickerRepository.from_file(data_dir / "stickers.json")
    assert len(stickers.list_by_collection("NEW")) == 150
    assert len(stickers.list_by_character("NEW_C05", spicy=False)) == 10
    assert len(stickers.list_by_character("NEW_C05", spicy=True)) == 5
    assert stickers.resolve_pool("NEW")  # usable as a pack pool immediately


def test_spicy_image_path_uses_spicy_number(env, tmp_path):
    service, _, _, assets_dir = env
    draft = service.create_collection("NEW", "Test")
    src = tmp_path / "photo.png"
    src.write_bytes(b"fake-png")
    # char 3, spicy slot 12 -> number 100 + 2*5 + 2 = 112
    assert service.attach_image(draft, "sticker", str(src), 3, 12) == "stickers/NEW_112.png"
