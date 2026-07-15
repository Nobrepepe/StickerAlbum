import pytest

from services.album_service import APPLIED, MISSING, OWNED
from services.errors import ApplyError


def _sticker(repos, sid):
    return repos["stickers"].get(sid)


def test_first_copy_creates_inventory_item(state_repo):
    state_repo.add_copy("TST_001", "normal")
    assert state_repo.get_quantity("TST_001", "normal") == 1


def test_adding_same_style_increments_quantity(state_repo):
    state_repo.add_copy("TST_001", "normal")
    state_repo.add_copy("TST_001", "normal")
    assert state_repo.get_quantity("TST_001", "normal") == 2


def test_normal_and_foil_counts_are_separate(state_repo):
    state_repo.add_copy("TST_001", "normal")
    state_repo.add_copy("TST_001", "foil")
    assert state_repo.get_quantity("TST_001", "normal") == 1
    assert state_repo.get_quantity("TST_001", "foil") == 1
    assert state_repo.total_owned("TST_001") == 2


def test_unowned_sticker_cannot_be_applied(repos, album_service):
    with pytest.raises(ApplyError):
        album_service.apply(_sticker(repos, "TST_001"), "normal")


def test_unowned_style_cannot_be_applied(repos, state_repo, album_service):
    state_repo.add_copy("TST_001", "normal")
    with pytest.raises(ApplyError):
        album_service.apply(_sticker(repos, "TST_001"), "foil")


def test_invalid_style_rejected(repos, state_repo, album_service):
    state_repo.add_copy("TST_001", "normal")
    with pytest.raises(ApplyError):
        album_service.apply(_sticker(repos, "TST_001"), "holographic")


def test_applying_increases_progress_once(repos, state_repo, album_service):
    state_repo.add_copy("TST_001", "normal")
    became_applied = album_service.apply(_sticker(repos, "TST_001"), "normal")
    assert became_applied is True
    assert album_service.character_progress("TST_C01") == (1, 10)


def test_replacing_normal_with_foil_does_not_double_count(repos, state_repo, album_service):
    state_repo.add_copy("TST_001", "normal")
    state_repo.add_copy("TST_001", "foil")
    assert album_service.apply(_sticker(repos, "TST_001"), "normal") is True
    assert album_service.apply(_sticker(repos, "TST_001"), "foil") is False
    assert album_service.character_progress("TST_C01") == (1, 10)
    assert album_service.applied_style("TST_001") == "foil"
    # Only one placement exists for the sticker.
    assert list(state_repo.state.placements) == ["TST_001"]


def test_applying_does_not_reduce_inventory(repos, state_repo, album_service):
    state_repo.add_copy("TST_001", "normal", 3)
    album_service.apply(_sticker(repos, "TST_001"), "normal")
    assert state_repo.get_quantity("TST_001", "normal") == 3
    assert album_service.duplicate_count("TST_001") == 2


def test_slot_states(repos, state_repo, album_service):
    assert album_service.slot_state("TST_001") == MISSING
    state_repo.add_copy("TST_001", "normal")
    assert album_service.slot_state("TST_001") == OWNED
    album_service.apply(_sticker(repos, "TST_001"), "normal")
    assert album_service.slot_state("TST_001") == APPLIED


def test_character_progress_counts_only_that_character(repos, state_repo, album_service):
    for sid in ("TST_001", "TST_002", "TST_011"):
        state_repo.add_copy(sid, "normal")
        album_service.apply(_sticker(repos, sid), "normal")
    assert album_service.character_progress("TST_C01") == (2, 10)
    assert album_service.character_progress("TST_C02") == (1, 10)


def test_collection_progress(repos, state_repo, album_service):
    for sid in ("TST_001", "TST_011", "TST_099"):
        state_repo.add_copy(sid, "normal")
        album_service.apply(_sticker(repos, sid), "normal")
    assert album_service.collection_progress("TST") == (3, 100)


def test_character_complete_only_at_ten(repos, state_repo, album_service):
    for pos in range(1, 10):
        sid = f"TST_{pos:03d}"
        state_repo.add_copy(sid, "normal")
        album_service.apply(_sticker(repos, sid), "normal")
    assert album_service.is_character_complete("TST_C01") is False
    state_repo.add_copy("TST_010", "normal")
    album_service.apply(_sticker(repos, "TST_010"), "normal")
    assert album_service.is_character_complete("TST_C01") is True
    assert album_service.completed_characters("TST") == (1, 10)


def test_collection_complete_only_at_hundred(repos, state_repo, album_service):
    for n in range(1, 100):
        sid = f"TST_{n:03d}"
        state_repo.add_copy(sid, "normal")
        album_service.apply(_sticker(repos, sid), "normal")
    assert album_service.is_collection_complete("TST") is False
    state_repo.add_copy("TST_100", "normal")
    album_service.apply(_sticker(repos, "TST_100"), "normal")
    assert album_service.is_collection_complete("TST") is True
