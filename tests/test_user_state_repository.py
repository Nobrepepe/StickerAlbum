import json

from repositories.user_state_repository import UserStateRepository


def test_save_and_load_round_trip(tmp_path):
    path = tmp_path / "state.json"
    repo = UserStateRepository(path)
    repo.add_copy("HGT_008", "normal", 2)
    repo.add_copy("HGT_008", "foil")
    repo.set_placement("HGT_008", "normal")
    repo.state.favorite_character_id = "HGT_C01"
    repo.add_savings(2500)
    repo.save()

    reloaded = UserStateRepository(path)
    assert reloaded.get_quantity("HGT_008", "normal") == 2
    assert reloaded.get_quantity("HGT_008", "foil") == 1
    assert reloaded.get_placement("HGT_008") == "normal"
    assert reloaded.state.favorite_character_id == "HGT_C01"
    assert reloaded.state.total_saved == 2500
    assert reloaded.load_warnings == []


def test_missing_optional_fields_get_defaults(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"schema_version": 1}))
    repo = UserStateRepository(path)
    assert repo.state.total_saved == 0
    assert repo.state.favorite_character_id is None
    assert repo.state.inventory == {}
    assert repo.state.placements == {}


def test_negative_quantity_rejected_with_warning(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({
        "inventory": [{"sticker_id": "A", "style": "normal", "quantity": -3}],
    }))
    repo = UserStateRepository(path)
    assert repo.state.inventory == {}
    assert any("quantity" in w for w in repo.load_warnings)


def test_unsupported_style_rejected(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({
        "inventory": [{"sticker_id": "A", "style": "holo", "quantity": 1}],
    }))
    repo = UserStateRepository(path)
    assert repo.state.inventory == {}
    assert repo.load_warnings


def test_unknown_sticker_ignored_when_catalog_known(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({
        "inventory": [
            {"sticker_id": "GOOD", "style": "normal", "quantity": 1},
            {"sticker_id": "BAD", "style": "normal", "quantity": 1},
        ],
    }))
    repo = UserStateRepository(path, known_sticker_ids={"GOOD"})
    assert repo.get_quantity("GOOD", "normal") == 1
    assert repo.get_quantity("BAD", "normal") == 0
    assert any("BAD" in w for w in repo.load_warnings)


def test_placement_of_unowned_style_rejected(tmp_path):
    path = tmp_path / "state.json"
    path.write_text(json.dumps({
        "inventory": [{"sticker_id": "A", "style": "normal", "quantity": 1}],
        "placements": [{"sticker_id": "A", "style": "foil"}],
    }))
    repo = UserStateRepository(path)
    assert repo.state.placements == {}
    assert repo.load_warnings


def test_corrupted_file_backed_up_not_destroyed(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{this is not json")
    repo = UserStateRepository(path)
    assert repo.state.total_saved == 0
    assert repo.load_warnings
    backups = list(tmp_path.glob("state.corrupt-*.json"))
    assert len(backups) == 1
    assert backups[0].read_text() == "{this is not json"
    assert not path.exists()  # replaced by backup, fresh save will recreate


def test_atomic_save_leaves_no_temp_files(tmp_path):
    path = tmp_path / "state.json"
    repo = UserStateRepository(path)
    repo.add_copy("X", "normal")
    repo.save()
    leftovers = [p for p in tmp_path.iterdir() if p.name != "state.json"]
    assert leftovers == []
    assert json.loads(path.read_text())["inventory"] == [
        {"sticker_id": "X", "style": "normal", "quantity": 1}
    ]
