import random

from models.catalog import Pack, Sticker
from models.rarity import SELECTORS
from models.results import OpenedSticker, PackOpenResult
from repositories.pack_repository import PackRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from services.errors import PackConfigError


class PackOpeningService:
    """Resolves pack distributions, rolls stickers/styles, updates inventory
    and savings, and commits everything in one save."""

    def __init__(
        self,
        stickers: StickerRepository,
        packs: PackRepository,
        state: UserStateRepository,
        rng: random.Random | None = None,
    ):
        self._stickers = stickers
        self._packs = packs
        self._state = state
        self._rng = rng if rng is not None else random.Random()

    def roll(self, pack: Pack) -> list[tuple[Sticker, str]]:
        """Pure selection: returns (sticker, style) picks without side effects."""
        picks: list[tuple[Sticker, str]] = []
        for dist in pack.distribution:
            allowed = SELECTORS.get(dist.value)
            if allowed is None:
                raise PackConfigError(
                    f"Pack {pack.id!r}: unknown distribution selector {dist.value!r}"
                )
            pool = self._stickers.resolve_pool(dist.pool)
            eligible = [s for s in pool if s.rarity in allowed]
            if not eligible:
                raise PackConfigError(
                    f"Pack {pack.id!r}: no stickers in pool {dist.pool!r} "
                    f"match selector {dist.value!r}"
                )
            for _ in range(dist.quantity):
                sticker = self._rng.choice(eligible)
                style = "foil" if self._rng.random() < pack.foil_rate else "normal"
                picks.append((sticker, style))
        return picks

    def open_pack(self, pack_id: str) -> PackOpenResult:
        pack = self._packs.get(pack_id)
        picks = self.roll(pack)

        # New/Duplicate is judged against inventory immediately before each
        # copy is added, so two identical copies in one pack are New then
        # Duplicate.
        items: list[OpenedSticker] = []
        for sticker, style in picks:
            is_new = self._state.total_owned(sticker.id) == 0
            self._state.add_copy(sticker.id, style)
            items.append(OpenedSticker(sticker=sticker, style=style, is_new=is_new))

        self._state.add_savings(pack.price)
        # Single commit: inventory + savings persist together, before any
        # reveal animation begins.
        self._state.save()
        return PackOpenResult(pack=pack, items=tuple(items), deposit=pack.price)
