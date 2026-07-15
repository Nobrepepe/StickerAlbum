"""Composition root: builds the shared repositories and services once and
hands them to the views. No mutable globals — everything hangs off this."""

from dataclasses import dataclass

from paths import DATA_DIR, USER_STATE_FILE
from repositories.character_repository import CharacterRepository
from repositories.collection_repository import CollectionRepository
from repositories.pack_repository import PackRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from seed import ensure_seed_catalog
from services.album_service import AlbumService
from services.pack_service import PackOpeningService
from services.summary_service import SummaryService


@dataclass
class AppContext:
    collections: CollectionRepository
    characters: CharacterRepository
    stickers: StickerRepository
    packs: PackRepository
    state: UserStateRepository
    album: AlbumService
    pack_service: PackOpeningService
    summary: SummaryService

    @classmethod
    def build(cls) -> "AppContext":
        # Development fixture: only generated when no catalog exists at all;
        # authored data files are never overwritten.
        ensure_seed_catalog(DATA_DIR)

        collections = CollectionRepository.from_file(DATA_DIR / "collections.json")
        characters = CharacterRepository.from_file(DATA_DIR / "characters.json")
        stickers = StickerRepository.from_file(DATA_DIR / "stickers.json")
        packs = PackRepository.from_file(DATA_DIR / "packs.json")
        state = UserStateRepository(USER_STATE_FILE, known_sticker_ids=stickers.all_ids())
        album = AlbumService(stickers, characters, state)
        pack_service = PackOpeningService(stickers, packs, state)
        summary = SummaryService(collections, characters, stickers, state, album)
        return cls(
            collections=collections,
            characters=characters,
            stickers=stickers,
            packs=packs,
            state=state,
            album=album,
            pack_service=pack_service,
            summary=summary,
        )
