import math
import random

from models.catalog import Pack, PackDistribution, PackPool, Sticker
from models.rarity import RARITY_ORDER, SELECTORS
from models.results import OpenedSticker, PackOpenResult
from repositories.pack_repository import PackRepository
from repositories.settings_repository import SettingsRepository
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository
from services.errors import PackConfigError

# Spicy drops chain until a miss; the cap only guards against a
# misconfigured spicy_rate of 1.0 looping forever.
MAX_SPICY_CHAIN = 20


class PackOpeningService:
    """Resolves pack distributions, rolls stickers/styles, updates inventory
    and savings, and commits everything in one save."""

    def __init__(
        self,
        stickers: StickerRepository,
        packs: PackRepository,
        state: UserStateRepository,
        settings: SettingsRepository | None = None,
        rng: random.Random | None = None,
    ):
        self._stickers = stickers
        self._packs = packs
        self._state = state
        self._settings = settings
        self._rng = rng if rng is not None else random.Random()

    @property
    def _spicy_enabled(self) -> bool:
        return bool(self._settings and self._settings.state.spicy_enabled)

    def roll(self, pack: Pack) -> list[tuple[Sticker, str]]:
        """Pure selection: returns (sticker, style) picks without side effects."""
        picks: list[tuple[Sticker, str]] = []
        for dist in pack.distribution:
            for _ in range(dist.quantity):
                sticker = self._roll_distribution(pack, dist)
                style = "foil" if self._rng.random() < pack.foil_rate else "normal"
                picks.append((sticker, style))
        picks.extend(self._roll_spicy(pack))
        return picks

    def _roll_distribution(self, pack: Pack, dist: PackDistribution) -> Sticker:
        if not dist.pools and not dist.rarity_weights:
            allowed = SELECTORS.get(dist.value)
            if allowed is None:
                raise PackConfigError(
                    f"Pack {pack.id!r}: unknown distribution selector {dist.value!r}"
                )
            eligible = self._eligible(dist.pool, allowed, dist.include, dist.exclude)
            if not eligible:
                raise PackConfigError(
                    f"Pack {pack.id!r}: no stickers in pool {dist.pool!r} "
                    f"match selector {dist.value!r}"
                )
            return self._rng.choice(eligible)

        sources = dist.pools or ((PackPool(dist.pool),) if dist.pool else ())
        weights = dict(dist.rarity_weights)
        if not sources or not weights:
            raise PackConfigError(
                f"Pack {pack.id!r}: custom distribution requires pools and rarity_weights"
            )
        self._validate_weights(pack, (s.weight for s in sources), "pool")
        unknown = set(weights) - set(RARITY_ORDER)
        if unknown or "spicy" in weights:
            raise PackConfigError(
                f"Pack {pack.id!r}: invalid regular rarity weights: {sorted(unknown or {'spicy'})}"
            )
        self._validate_weights(pack, weights.values(), "rarity")

        # Only choose source/rarity combinations that can actually produce a
        # sticker, renormalizing their configured weights when some are empty.
        choices: list[list[Sticker]] = []
        choice_weights: list[float] = []
        for source in sources:
            for rarity, rarity_weight in weights.items():
                eligible = self._eligible(
                    source.pool, {rarity}, dist.include, dist.exclude
                )
                if eligible and source.weight > 0 and rarity_weight > 0:
                    choices.append(eligible)
                    choice_weights.append(source.weight * rarity_weight)
        if not choices:
            raise PackConfigError(
                f"Pack {pack.id!r}: custom distribution has no eligible stickers"
            )
        return self._rng.choice(self._rng.choices(choices, weights=choice_weights, k=1)[0])

    def _eligible(
        self,
        pool: str,
        rarities: set[str],
        include: tuple[str, ...],
        exclude: tuple[str, ...],
    ) -> list[Sticker]:
        included = set(include)
        excluded = set(exclude)
        return [
            s for s in self._stickers.resolve_pool(pool)
            if not s.spicy and s.rarity in rarities
            and (not included or s.id in included) and s.id not in excluded
        ]

    @staticmethod
    def _validate_weights(pack: Pack, weights, label: str) -> None:
        values = list(weights)
        if (
            not values
            or any(not math.isfinite(w) or w < 0 for w in values)
            or not any(w > 0 for w in values)
        ):
            raise PackConfigError(f"Pack {pack.id!r}: invalid {label} weights")

    def _roll_spicy(self, pack: Pack) -> list[tuple[Sticker, str]]:
        """Bonus spicy drops: while the spicy_rate roll hits, add one random
        sticker from the configured sources and roll again."""
        if not self._spicy_enabled or pack.spicy_rate <= 0:
            return []
        sources = pack.spicy_pools or (PackPool(pack.collection_id),)
        self._validate_weights(pack, (s.weight for s in sources), "spicy pool")
        available = [
            (self._stickers.resolve_pool(source.pool), source.weight)
            for source in sources
        ]
        available = [
            ([s for s in stickers if s.spicy], weight)
            for stickers, weight in available if weight > 0
        ]
        available = [(stickers, weight) for stickers, weight in available if stickers]
        pool = [stickers for stickers, _ in available]
        if not pool:
            return []  # collection without spicy stickers: nothing to drop
        picks: list[tuple[Sticker, str]] = []
        while len(picks) < MAX_SPICY_CHAIN and self._rng.random() < pack.spicy_rate:
            source = self._rng.choices(
                pool, weights=[weight for _, weight in available], k=1
            )[0]
            sticker = self._rng.choice(source)
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
