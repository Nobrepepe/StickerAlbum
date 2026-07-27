import random

from models.catalog import Pack, PackDistribution
from repositories.pack_repository import PackRepository
from repositories.settings_repository import SettingsRepository
from services.pack_service import MAX_SPICY_CHAIN, PackOpeningService
from services.summary_service import SummaryService


def _pack(spicy_rate, foil_rate=0.0):
    return Pack(
        id="P", collection_id="TST", name="P", description="",
        price=1000, foil_rate=foil_rate, spicy_rate=spicy_rate,
        distribution=(PackDistribution(pool="TST", value="standard", quantity=5),),
    )


def _service(repos, state_repo, pack, settings, seed=7):
    return PackOpeningService(
        repos["stickers"], PackRepository([pack]), state_repo,
        settings=settings, rng=random.Random(seed),
    )


# ---- settings repository ---------------------------------------------------

def test_settings_defaults(settings_repo):
    assert settings_repo.state.creator_enabled is False
    assert settings_repo.state.spicy_enabled is False


def test_settings_round_trip(tmp_path):
    repo = SettingsRepository(tmp_path / "settings.json")
    repo.set_creator_enabled(True)
    repo.set_spicy_enabled(True)
    reloaded = SettingsRepository(tmp_path / "settings.json")
    assert reloaded.state.creator_enabled is True
    assert reloaded.state.spicy_enabled is True


def test_corrupt_settings_fall_back_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{nope")
    repo = SettingsRepository(path)
    assert repo.state.creator_enabled is False
    assert repo.state.spicy_enabled is False


# ---- spicy pack drops ---------------------------------------------------------

def test_no_spicy_drops_when_toggle_disabled(repos, state_repo, settings_repo):
    # Even a guaranteed spicy rate drops nothing while the feature is off.
    result = _service(repos, state_repo, _pack(spicy_rate=1.0), settings_repo).open_pack("P")
    assert all(not item.sticker.spicy for item in result.items)
    assert len(result.items) == 5


def test_no_spicy_drops_without_settings_repo(repos, state_repo):
    service = PackOpeningService(
        repos["stickers"], PackRepository([_pack(1.0)]), state_repo,
        rng=random.Random(1),
    )
    assert all(not i.sticker.spicy for i in service.open_pack("P").items)


def test_spicy_rate_zero_drops_nothing(repos, state_repo, settings_repo):
    settings_repo.set_spicy_enabled(True)
    result = _service(repos, state_repo, _pack(spicy_rate=0.0), settings_repo).open_pack("P")
    assert all(not item.sticker.spicy for item in result.items)


def test_spicy_drops_are_additional_and_flagged(repos, state_repo, settings_repo):
    settings_repo.set_spicy_enabled(True)
    result = _service(
        repos, state_repo, _pack(spicy_rate=0.5), settings_repo, seed=3
    ).open_pack("P")
    base = [i for i in result.items if not i.sticker.spicy]
    spicy = [i for i in result.items if i.sticker.spicy]
    assert len(base) == 5  # base distribution untouched
    assert all(s.sticker.id.startswith("TST_1") for s in spicy)  # numbers 101+
    assert all(s.sticker.rarity == "spicy" for s in spicy)


def test_spicy_chain_rolls_until_miss(repos, state_repo, settings_repo):
    settings_repo.set_spicy_enabled(True)
    # rate ~1.0 would loop forever without the safety cap
    result = _service(repos, state_repo, _pack(spicy_rate=1.0), settings_repo).open_pack("P")
    spicy = [i for i in result.items if i.sticker.spicy]
    assert len(spicy) == MAX_SPICY_CHAIN


def test_spicy_chain_is_geometric(repos, state_repo, settings_repo):
    """With rate 0.5, chains of different lengths must occur across packs."""
    settings_repo.set_spicy_enabled(True)
    lengths = set()
    for seed in range(30):
        from repositories.user_state_repository import UserStateRepository
        state = UserStateRepository(state_repo._path.parent / f"s{seed}.json")
        result = _service(repos, state, _pack(spicy_rate=0.5), settings_repo,
                          seed=seed).open_pack("P")
        lengths.add(sum(1 for i in result.items if i.sticker.spicy))
    assert 0 in lengths          # sometimes the first roll misses
    assert any(n >= 2 for n in lengths)  # sometimes it chains


def test_base_distribution_never_contains_spicy(repos, state_repo, settings_repo):
    settings_repo.set_spicy_enabled(True)
    pack = Pack(
        id="P", collection_id="TST", name="P", description="",
        price=1000, foil_rate=0.0, spicy_rate=0.0,
        # 'any' covers every rarity; spicy stickers still must not appear
        distribution=(PackDistribution(pool="TST", value="any", quantity=50),),
    )
    result = _service(repos, state_repo, pack, settings_repo).open_pack("P")
    assert all(not i.sticker.spicy for i in result.items)


def test_collection_without_spicy_stickers_is_safe(repos, state_repo, settings_repo, tmp_path):
    settings_repo.set_spicy_enabled(True)
    from models.catalog import Collection, Sticker
    from repositories.sticker_repository import StickerRepository
    plain = StickerRepository([
        Sticker(id="PLN_001", collection_id="PLN", character_id="PLN_C01",
                number=1, name="Only", rarity="common"),
    ])
    pack = Pack(
        id="P", collection_id="PLN", name="P", description="",
        price=100, foil_rate=0.0, spicy_rate=1.0,
        distribution=(PackDistribution(pool="PLN", value="common", quantity=1),),
    )
    service = PackOpeningService(
        plain, PackRepository([pack]), state_repo, settings=settings_repo,
        rng=random.Random(1),
    )
    result = service.open_pack("P")  # must not raise or loop
    assert len(result.items) == 1


# ---- album progress and hidden stats ------------------------------------------

def test_progress_ignores_spicy_stickers(repos, state_repo, album_service):
    # Apply all 10 regular stickers of character 1 -> complete even though
    # no spicy stickers are owned.
    for pos in range(1, 11):
        sid = f"TST_{pos:03d}"
        state_repo.add_copy(sid, "normal")
        album_service.apply(repos["stickers"].get(sid), "normal")
    assert album_service.character_progress("TST_C01") == (10, 10)
    assert album_service.is_character_complete("TST_C01")
    assert album_service.spicy_character_progress("TST_C01") == (0, 5)


def test_spicy_placement_tracks_separately(repos, state_repo, album_service):
    state_repo.add_copy("TST_101", "normal")
    album_service.apply(repos["stickers"].get("TST_101"), "normal")
    assert album_service.spicy_character_progress("TST_C01") == (1, 5)
    assert album_service.character_progress("TST_C01") == (0, 10)


def test_summary_hides_spicy_when_disabled(repos, state_repo, settings_repo, album_service):
    summary = SummaryService(
        repos["collections"], repos["characters"], repos["stickers"],
        state_repo, album_service, settings_repo,
    )
    state_repo.add_copy("TST_001", "normal")   # regular
    state_repo.add_copy("TST_101", "normal")   # spicy
    album_service.apply(repos["stickers"].get("TST_101"), "normal")

    s = summary.home_summary()
    assert s.unique_owned == 1   # spicy hidden
    assert s.total_applied == 0  # spicy placement hidden

    settings_repo.set_spicy_enabled(True)
    s = summary.home_summary()
    assert s.unique_owned == 2
    assert s.total_applied == 1


def test_favorite_carousel_hides_spicy_when_disabled(repos, state_repo, settings_repo, album_service):
    summary = SummaryService(
        repos["collections"], repos["characters"], repos["stickers"],
        state_repo, album_service, settings_repo,
    )
    state_repo.state.favorite_character_id = "TST_C01"
    state_repo.add_copy("TST_001", "normal")
    state_repo.add_copy("TST_101", "normal")

    fav = summary.favorite_info()
    assert [s.id for s, _ in fav.owned_stickers] == ["TST_001"]

    settings_repo.set_spicy_enabled(True)
    fav = summary.favorite_info()
    assert [s.id for s, _ in fav.owned_stickers] == ["TST_001", "TST_101"]
