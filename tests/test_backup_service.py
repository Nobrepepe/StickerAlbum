import json

import pytest

from repositories.draft_repository import DraftRepository
from repositories.user_state_repository import UserStateRepository
from services.backup_service import BackupError, BackupService


@pytest.fixture
def env(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "collections.json").write_text(json.dumps(
        [{"id": "HGT", "name": "Heights", "description": ""}]))
    (data_dir / "characters.json").write_text(json.dumps(
        [{"id": "HGT_C01", "collection_id": "HGT", "name": "Aria"}]))
    (data_dir / "stickers.json").write_text(json.dumps(
        [{"id": "HGT_001", "collection_id": "HGT", "character_id": "HGT_C01",
          "number": 1, "name": "First", "rarity": "common"}]))
    state = UserStateRepository(tmp_path / "user_state.json")
    drafts = DraftRepository(data_dir / "drafts.json")
    return BackupService(state, drafts, data_dir), state, drafts, data_dir, tmp_path


# ---- progress -----------------------------------------------------------------

def test_progress_export_import_round_trip(env):
    service, state, _, _, tmp = env
    state.add_copy("HGT_001", "foil", 2)
    state.set_placement("HGT_001", "foil")
    state.state.favorite_character_id = "HGT_C01"
    state.add_savings(7500)
    state.save()

    backup = tmp / "backup.json"
    service.export_progress(str(backup))

    state.reset()
    assert state.state.total_saved == 0
    assert state.state.inventory == {}

    warnings = service.import_progress(str(backup))
    assert warnings == []
    assert state.get_quantity("HGT_001", "foil") == 2
    assert state.get_placement("HGT_001") == "foil"
    assert state.state.favorite_character_id == "HGT_C01"
    assert state.state.total_saved == 7500
    # and it was persisted, not just held in memory
    reloaded = UserStateRepository(state._path)
    assert reloaded.state.total_saved == 7500


def test_progress_import_rejects_non_progress_file(env):
    service, _, _, _, tmp = env
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"something": "else"}))
    with pytest.raises(BackupError):
        service.import_progress(str(bad))


def test_progress_import_rejects_unreadable_file(env):
    service, _, _, _, tmp = env
    bad = tmp / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(BackupError):
        service.import_progress(str(bad))


def test_reset_progress_clears_everything(env):
    service, state, _, _, _ = env
    state.add_copy("HGT_001", "normal")
    state.add_savings(1000)
    state.save()
    service.reset_progress()
    assert state.state.inventory == {}
    assert state.state.placements == {}
    assert state.state.total_saved == 0
    reloaded = UserStateRepository(state._path)
    assert reloaded.state.total_saved == 0


# ---- catalog ---------------------------------------------------------------------

def test_catalog_export_import_round_trip(env):
    service, _, drafts, data_dir, tmp = env
    backup = tmp / "catalog.json"
    service.export_catalog(str(backup))

    bundle = json.loads(backup.read_text())
    assert bundle["format"] == "sticker-album-catalog"
    assert bundle["collections"][0]["id"] == "HGT"

    service.reset_catalog()
    assert json.loads((data_dir / "collections.json").read_text()) == []

    service.import_catalog(str(backup))
    assert json.loads((data_dir / "collections.json").read_text())[0]["id"] == "HGT"
    assert json.loads((data_dir / "stickers.json").read_text())[0]["id"] == "HGT_001"


def test_catalog_import_rejects_wrong_format(env):
    service, _, _, _, tmp = env
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"format": "something-else", "collections": []}))
    with pytest.raises(BackupError, match="not a catalog backup"):
        service.import_catalog(str(bad))


def test_catalog_import_rejects_malformed_records_before_writing(env):
    service, _, _, data_dir, tmp = env
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({
        "format": "sticker-album-catalog",
        "collections": [{"name": "missing id"}],
        "characters": [],
        "stickers": [],
    }))
    with pytest.raises(BackupError, match="Invalid catalog backup"):
        service.import_catalog(str(bad))
    # original catalog untouched
    assert json.loads((data_dir / "collections.json").read_text())[0]["id"] == "HGT"


def test_reset_catalog_clears_all_catalog_files_and_drafts(env):
    service, _, drafts, data_dir, _ = env
    from models.draft import new_draft_skeleton
    drafts.upsert(new_draft_skeleton("WIP", "Work in progress"))
    service.reset_catalog()
    assert json.loads((data_dir / "collections.json").read_text()) == []
    assert json.loads((data_dir / "characters.json").read_text()) == []
    assert json.loads((data_dir / "stickers.json").read_text()) == []
    assert json.loads((data_dir / "drafts.json").read_text()) == {"collections": []}
