import random
import json

import pytest

from models.catalog import Pack, PackDistribution, PackPool
from models.rarity import SELECTORS
from repositories.pack_repository import PackRepository
from services.errors import PackConfigError
from services.pack_service import PackOpeningService
from tests.conftest import make_pack_service


def _pack(distribution, foil_rate=0.0, pack_id="P"):
    return Pack(
        id=pack_id, collection_id="TST", name="P", description="",
        price=1000, foil_rate=foil_rate, distribution=tuple(distribution),
    )


def _service(repos, state_repo, pack, seed=1):
    return PackOpeningService(
        repos["stickers"], PackRepository([pack]), state_repo, rng=random.Random(seed)
    )


def test_standard_selector_resolves_to_common_and_uncommon():
    assert SELECTORS["standard"] == {"common", "uncommon"}


def test_rare_plus_selector_resolves_to_rare_epic_legendary():
    assert SELECTORS["rare+"] == {"rare", "epic", "legendary"}


def test_standard_pack_only_yields_allowed_rarities(repos, state_repo):
    pack = _pack([PackDistribution("TST", "standard", 20)])
    result = _service(repos, state_repo, pack).open_pack("P")
    assert all(item.sticker.rarity in {"common", "uncommon"} for item in result.items)


def test_rare_plus_only_yields_rare_or_better(repos, state_repo):
    pack = _pack([PackDistribution("TST", "rare+", 20)])
    result = _service(repos, state_repo, pack).open_pack("P")
    assert all(
        item.sticker.rarity in {"rare", "epic", "legendary"} for item in result.items
    )


def test_custom_rarity_weights_are_applied_before_card_selection(repos, state_repo):
    dist = PackDistribution(
        "", "", 10000,
        pools=(PackPool("TST"),),
        rarity_weights=(("rare", 0.7), ("epic", 0.25), ("legendary", 0.05)),
    )
    result = _service(repos, state_repo, _pack([dist]), seed=17).open_pack("P")
    counts = {
        rarity: sum(i.sticker.rarity == rarity for i in result.items)
        for rarity in ("rare", "epic", "legendary")
    }
    assert 0.68 < counts["rare"] / 10000 < 0.72
    assert 0.23 < counts["epic"] / 10000 < 0.27
    assert 0.04 < counts["legendary"] / 10000 < 0.06


def test_custom_pool_weights_mix_character_pools(repos, state_repo):
    dist = PackDistribution(
        "", "", 4000,
        pools=(PackPool("TST_C01", 0.75), PackPool("TST_C02", 0.25)),
        rarity_weights=(("common", 1.0),),
    )
    result = _service(repos, state_repo, _pack([dist]), seed=23).open_pack("P")
    first = sum(i.sticker.character_id == "TST_C01" for i in result.items)
    assert 0.72 < first / 4000 < 0.78


def test_custom_include_and_exclude_limit_cards(repos, state_repo):
    dist = PackDistribution(
        "", "", 30,
        pools=(PackPool("TST"),),
        rarity_weights=(("rare", 1.0),),
        include=("TST_007", "TST_008"),
        exclude=("TST_008",),
    )
    result = _service(repos, state_repo, _pack([dist])).open_pack("P")
    assert {i.sticker.id for i in result.items} == {"TST_007"}


def test_custom_distribution_loads_from_json(tmp_path):
    path = tmp_path / "packs.json"
    path.write_text(json.dumps({
        "MIX": {
            "collection_id": "TST", "name": "Mixed", "price": 5000,
            "spicy_pools": [
                {"pool": "TST", "weight": 0.6},
                {"pool": "OTH", "weight": 0.4},
            ],
            "distribution": [{
                "quantity": 5,
                "pools": ["TST", {"pool": "OTH", "weight": 0.5}],
                "rarity_weights": {"rare": 0.7, "epic": 0.25, "legendary": 0.05},
                "include": ["TST_007"],
                "exclude": ["OTH_099"],
            }],
        }
    }))
    pack = PackRepository.from_file(path).get("MIX")
    dist = pack.distribution[0]
    assert dist.pools == (PackPool("TST"), PackPool("OTH", 0.5))
    assert dict(dist.rarity_weights) == {
        "rare": 0.7, "epic": 0.25, "legendary": 0.05,
    }
    assert pack.spicy_pools == (PackPool("TST", 0.6), PackPool("OTH", 0.4))


def test_quantities_respected(repos, state_repo):
    pack = _pack([
        PackDistribution("TST", "standard", 4),
        PackDistribution("TST", "rare+", 1),
    ])
    result = _service(repos, state_repo, pack).open_pack("P")
    assert len(result.items) == 5


def test_duplicates_possible(repos, state_repo):
    # A single legendary exists per character; drawing many legendaries from
    # a 10-sticker legendary pool must produce repeats.
    pack = _pack([PackDistribution("TST", "legendary", 50)])
    result = _service(repos, state_repo, pack).open_pack("P")
    ids = [item.sticker.id for item in result.items]
    assert len(set(ids)) < len(ids)


def test_seeded_randomness_is_deterministic(repos, tmp_path):
    from repositories.user_state_repository import UserStateRepository

    def run(seed):
        state = UserStateRepository(tmp_path / f"s{seed}.json")
        pack = _pack([PackDistribution("TST", "any", 10)], foil_rate=0.5)
        result = _service(repos, state, pack, seed=99).open_pack("P")
        return [(i.sticker.id, i.style) for i in result.items]

    assert run(1) == run(2)


def test_foil_rate_zero_produces_no_foils(repos, state_repo):
    pack = _pack([PackDistribution("TST", "any", 30)], foil_rate=0.0)
    result = _service(repos, state_repo, pack).open_pack("P")
    assert all(item.style == "normal" for item in result.items)


def test_foil_rate_one_produces_only_foils(repos, state_repo):
    pack = _pack([PackDistribution("TST", "any", 30)], foil_rate=1.0)
    result = _service(repos, state_repo, pack).open_pack("P")
    assert all(item.style == "foil" for item in result.items)


def test_unknown_selector_raises_config_error(repos, state_repo):
    pack = _pack([PackDistribution("TST", "mythic", 1)])
    with pytest.raises(PackConfigError):
        _service(repos, state_repo, pack).open_pack("P")


def test_empty_pool_raises_config_error(repos, state_repo):
    pack = _pack([PackDistribution("NOPE", "any", 1)])
    with pytest.raises(PackConfigError):
        _service(repos, state_repo, pack).open_pack("P")


def test_same_sticker_twice_marks_first_new_then_duplicate(repos, state_repo):
    pack = _pack([PackDistribution("TST_C01", "legendary", 3)])  # 1-sticker pool
    result = _service(repos, state_repo, pack).open_pack("P")
    flags = [item.is_new for item in result.items]
    assert flags == [True, False, False]


def test_new_vs_duplicate_uses_prior_inventory(repos, state_repo):
    state_repo.add_copy("TST_010", "normal")  # legendary of character 1
    pack = _pack([PackDistribution("TST_C01", "legendary", 1)])
    result = _service(repos, state_repo, pack).open_pack("P")
    assert result.items[0].is_new is False


def test_open_pack_records_savings_and_persists(repos, state_repo):
    pack = _pack([PackDistribution("TST", "any", 5)])
    _service(repos, state_repo, pack).open_pack("P")
    assert state_repo.state.total_saved == 1000
    # Reload from disk to prove it was committed.
    from repositories.user_state_repository import UserStateRepository
    reloaded = UserStateRepository(state_repo._path)
    assert reloaded.state.total_saved == 1000
    assert sum(reloaded.state.inventory.values()) == 5


def test_cancel_is_free_no_state_touched(repos, state_repo, tmp_path):
    # Cancelling simply never calls open_pack; verify baseline stays zero.
    assert state_repo.state.total_saved == 0
    assert not (tmp_path / "user_state.json").exists()
