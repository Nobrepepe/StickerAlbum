import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.catalog import Character, Collection, Pack, PackDistribution, Sticker
from models.rarity import RARITY_PATTERN
from repositories.character_repository import CharacterRepository
from repositories.collection_repository import CollectionRepository
from repositories.pack_repository import PackRepository
from repositories.settings_repository import SettingsRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from services.album_service import AlbumService
from services.pack_service import PackOpeningService


def make_catalog():
    """Tiny but complete test collection: 10 characters x 10 stickers."""
    collection = Collection(id="TST", name="Testland", description="test")
    characters = []
    stickers = []
    for ci in range(1, 11):
        cid = f"TST_C{ci:02d}"
        characters.append(Character(id=cid, collection_id="TST", name=f"Char {ci}"))
        for pos in range(1, 11):
            number = (ci - 1) * 10 + pos
            stickers.append(Sticker(
                id=f"TST_{number:03d}",
                collection_id="TST",
                character_id=cid,
                number=number,
                name=f"Sticker {number}",
                rarity=RARITY_PATTERN[pos - 1],
            ))
    packs = [
        Pack(
            id="TST_standard",
            collection_id="TST",
            name="Test Pack",
            description="",
            price=2500,
            foil_rate=0.0,
            distribution=(
                PackDistribution(pool="TST", value="standard", quantity=4),
                PackDistribution(pool="TST", value="rare+", quantity=1),
            ),
        ),
    ]
    return collection, characters, stickers, packs


@pytest.fixture
def catalog():
    return make_catalog()


@pytest.fixture
def repos(catalog):
    collection, characters, stickers, packs = catalog
    return {
        "collections": CollectionRepository([collection]),
        "characters": CharacterRepository(characters),
        "stickers": StickerRepository(stickers),
        "packs": PackRepository(packs),
    }


@pytest.fixture
def state_repo(tmp_path, repos):
    return UserStateRepository(
        tmp_path / "user_state.json",
        known_sticker_ids=repos["stickers"].all_ids(),
    )


@pytest.fixture
def album_service(repos, state_repo):
    return AlbumService(repos["stickers"], repos["characters"], state_repo)


@pytest.fixture
def settings_repo(tmp_path):
    return SettingsRepository(tmp_path / "settings.json")


def make_pack_service(repos, state_repo, seed=42, packs=None):
    import random
    return PackOpeningService(
        repos["stickers"],
        packs or repos["packs"],
        state_repo,
        rng=random.Random(seed),
    )
