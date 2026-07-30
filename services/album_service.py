from models.catalog import Sticker
from models.rarity import STYLES
from repositories.character_repository import CharacterRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from services.errors import ApplyError

# Slot states used by the UI.
MISSING = "missing"
OWNED = "owned"  # owned but not applied
APPLIED = "applied"


class AlbumService:
    """Placement rules and progress, always derived from actual placements."""

    def __init__(
        self,
        stickers: StickerRepository,
        characters: CharacterRepository,
        state: UserStateRepository,
    ):
        self._stickers = stickers
        self._characters = characters
        self._state = state

    # ---- slot state ------------------------------------------------------

    def slot_state(self, sticker_id: str) -> str:
        if self._state.get_placement(sticker_id) is not None:
            return APPLIED
        if self._state.total_owned(sticker_id) > 0:
            return OWNED
        return MISSING

    def applied_style(self, sticker_id: str) -> str | None:
        return self._state.get_placement(sticker_id)

    def owned_styles(self, sticker_id: str) -> dict[str, int]:
        return self._state.owned_styles(sticker_id)

    def duplicate_count(self, sticker_id: str) -> int:
        """Copies beyond the one conceptually used by the album placement."""
        total = self._state.total_owned(sticker_id)
        return max(0, total - 1) if self._state.get_placement(sticker_id) else total

    def has_foil_spare(self, sticker_id: str) -> bool:
        """Whether an unapplied copy in the spare pile is foil.

        Inventory is not consumed when a sticker is placed, so the foil copy
        on the board must be subtracted from the owned foil quantity.
        """
        foil_owned = self._state.get_quantity(sticker_id, "foil")
        foil_on_board = self._state.get_placement(sticker_id) == "foil"
        return foil_owned - (1 if foil_on_board else 0) > 0

    # ---- applying --------------------------------------------------------

    def apply(self, sticker: Sticker, style: str) -> bool:
        """Apply (or restyle) a sticker. Returns True when an empty slot
        became applied (i.e. progress increased)."""
        if style not in STYLES:
            raise ApplyError(f"Unsupported style: {style}")
        if self._state.get_quantity(sticker.id, style) < 1:
            if self._state.total_owned(sticker.id) < 1:
                raise ApplyError(f"You don't own {sticker.name} yet.")
            raise ApplyError(f"You don't own a {style} copy of {sticker.name}.")
        previous = self._state.get_placement(sticker.id)
        self._state.set_placement(sticker.id, style)
        self._state.save()
        return previous is None

    # ---- progress --------------------------------------------------------
    def character_progress(self, character_id: str) -> tuple[int, int]:
        stickers = self._stickers.list_by_character(character_id)
        applied = sum(1 for s in stickers if self._state.get_placement(s.id))
        return applied, len(stickers)

    def is_character_complete(self, character_id: str) -> bool:
        applied, total = self.character_progress(character_id)
        return total > 0 and applied == total

    def collection_progress(self, collection_id: str) -> tuple[int, int]:
        stickers = self._stickers.list_by_collection(collection_id)
        applied = sum(1 for s in stickers if self._state.get_placement(s.id))
        return applied, len(stickers)

    def is_collection_complete(self, collection_id: str) -> bool:
        applied, total = self.collection_progress(collection_id)
        return total > 0 and applied == total

    def completed_characters(self, collection_id: str) -> tuple[int, int]:
        chars = self._characters.list_by_collection(collection_id)
        done = sum(1 for c in chars if self.is_character_complete(c.id))
        return done, len(chars)
