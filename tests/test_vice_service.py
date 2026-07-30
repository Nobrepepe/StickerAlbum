import pytest

from models.catalog import Sticker
from models.rarity import VICE_VALUES
from repositories.user_state_repository import UserStateRepository
from services.errors import ViceError
from services.vice_service import ViceService


def sticker(rarity="common"):
    return Sticker(
        id="TST_001", collection_id="TST", character_id="TST_C01",
        number=1, name="Test Sticker", rarity=rarity,
    )


def test_conversion_values_follow_relative_drop_frequency():
    assert VICE_VALUES == {
        "common": 1, "uncommon": 1, "rare": 3,
        "epic": 8, "legendary": 40,
    }


def test_conversion_consumes_only_spares_and_persists(tmp_path):
    path = tmp_path / "state.json"
    state = UserStateRepository(path)
    state.add_copy("TST_001", "normal", 3)
    state.add_copy("TST_001", "foil", 2)
    state.set_placement("TST_001", "normal")
    service = ViceService(state)

    converted, earned = service.convert_spares(sticker("rare"))

    assert (converted, earned) == (4, 12)
    assert state.get_quantity("TST_001", "normal") == 1
    assert state.get_quantity("TST_001", "foil") == 0
    assert state.get_placement("TST_001") == "normal"
    reloaded = UserStateRepository(path)
    assert reloaded.state.vice_points == 12
    assert reloaded.total_owned("TST_001") == 1


def test_unapplied_conversion_retains_one_copy_preferably_foil(tmp_path):
    state = UserStateRepository(tmp_path / "state.json")
    state.add_copy("TST_001", "normal", 2)
    state.add_copy("TST_001", "foil")
    service = ViceService(state)

    service.convert_spares(sticker())

    assert state.get_quantity("TST_001", "normal") == 0
    assert state.get_quantity("TST_001", "foil") == 1


def test_conversion_can_leave_some_spares_for_later(tmp_path):
    state = UserStateRepository(tmp_path / "state.json")
    state.add_copy("TST_001", "normal", 4)
    service = ViceService(state)

    converted, earned = service.convert_spares(sticker("epic"), 2)

    assert (converted, earned) == (2, 16)
    assert state.total_owned("TST_001") == 2
    assert service.spare_count("TST_001") == 1


def test_cannot_convert_last_copy(tmp_path):
    state = UserStateRepository(tmp_path / "state.json")
    state.add_copy("TST_001", "normal")
    with pytest.raises(ViceError, match="no spare"):
        ViceService(state).convert_spares(sticker())


def test_offering_crud_claim_and_persistence(tmp_path):
    path = tmp_path / "state.json"
    state = UserStateRepository(path)
    service = ViceService(state)
    offering = service.add_offering("Fancy coffee", "The unnecessarily nice one", 7, 2)
    service.update_offering(offering.id, "Fancy coffee", "With cake", 6, 2)
    state.state.vice_points = 10
    state.save()

    claimed = service.claim(offering.id)

    assert claimed.quantity == 1
    assert service.points == 4
    reloaded = ViceService(UserStateRepository(path))
    assert reloaded.points == 4
    assert reloaded.list_offerings()[0].quantity == 1
    reloaded.remove_offering(offering.id)
    assert reloaded.list_offerings() == []


def test_claim_rejects_insufficient_points_and_sold_out(tmp_path):
    service = ViceService(UserStateRepository(tmp_path / "state.json"))
    expensive = service.add_offering("Treat", "", 5, 1)
    with pytest.raises(ViceError, match="more vice points"):
        service.claim(expensive.id)

    sold_out = service.add_offering("Gone", "", 1, 0)
    with pytest.raises(ViceError, match="sold out"):
        service.claim(sold_out.id)
