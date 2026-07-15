from dataclasses import dataclass

from models.catalog import Character, Collection, Sticker
from repositories.character_repository import CharacterRepository
from repositories.collection_repository import CollectionRepository
from repositories.settings_repository import SettingsRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from services.album_service import AlbumService


@dataclass(frozen=True)
class HomeSummary:
    unique_owned: int
    total_applied: int
    completed_collections: int
    total_collections: int
    total_saved: int  # cents


@dataclass(frozen=True)
class FavoriteInfo:
    character: Character
    collection: Collection
    applied: int
    total: int
    # Owned stickers of this character, with their owned styles, for the
    # Home carousel.
    owned_stickers: tuple[tuple[Sticker, tuple[str, ...]], ...]


class SummaryService:
    """Aggregated statistics for the Home and Collections screens."""

    def __init__(
        self,
        collections: CollectionRepository,
        characters: CharacterRepository,
        stickers: StickerRepository,
        state: UserStateRepository,
        album: AlbumService,
        settings: SettingsRepository | None = None,
    ):
        self._collections = collections
        self._characters = characters
        self._stickers = stickers
        self._state = state
        self._album = album
        self._settings = settings

    def _is_hidden(self, sticker_id: str) -> bool:
        """Spicy stickers vanish from every stat while the toggle is off."""
        if self._settings and self._settings.state.spicy_enabled:
            return False
        try:
            return self._stickers.get(sticker_id).spicy
        except Exception:
            return False

    def home_summary(self) -> HomeSummary:
        owned_ids = {
            sid for (sid, _style), qty in self._state.state.inventory.items()
            if qty > 0 and not self._is_hidden(sid)
        }
        applied = sum(
            1 for sid in self._state.state.placements if not self._is_hidden(sid)
        )
        all_collections = self._collections.list_all()
        completed = sum(
            1 for c in all_collections if self._album.is_collection_complete(c.id)
        )
        return HomeSummary(
            unique_owned=len(owned_ids),
            total_applied=applied,
            completed_collections=completed,
            total_collections=len(all_collections),
            total_saved=self._state.state.total_saved,
        )

    def favorite_info(self) -> FavoriteInfo | None:
        fav_id = self._state.state.favorite_character_id
        if not fav_id:
            return None
        try:
            character = self._characters.get(fav_id)
        except Exception:
            # Favorite points at a character no longer in the catalog.
            return None
        collection = self._collections.get(character.collection_id)
        applied, total = self._album.character_progress(fav_id)
        spicy_on = bool(self._settings and self._settings.state.spicy_enabled)
        owned = tuple(
            (s, tuple(styles))
            for s in self._stickers.list_by_character(fav_id)
            if (spicy_on or not s.spicy) and (styles := self._state.owned_styles(s.id))
        )
        return FavoriteInfo(
            character=character,
            collection=collection,
            applied=applied,
            total=total,
            owned_stickers=owned,
        )
