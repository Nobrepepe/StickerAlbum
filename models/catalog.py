"""Immutable catalog entities: authored content the user collects."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Collection:
    id: str
    name: str
    description: str
    cover_image: str | None = None
    theme_color: str | None = None


@dataclass(frozen=True)
class Character:
    id: str
    collection_id: str
    name: str
    description: str = ""
    portrait_image: str | None = None


@dataclass(frozen=True)
class Sticker:
    id: str
    collection_id: str
    character_id: str
    number: int
    name: str
    rarity: str
    image: str | None = None
    flavor_text: str = ""
    spicy: bool = False  # hidden bonus sticker, only visible when enabled
    sound: str | None = None  # optional voice line for the flavor text


@dataclass(frozen=True)
class PackPool:
    pool: str
    weight: float = 1.0


@dataclass(frozen=True)
class PackDistribution:
    # Legacy form: pool + value. Custom distributions use pools and
    # rarity_weights instead; both forms remain supported.
    pool: str
    value: str
    quantity: int
    pools: tuple[PackPool, ...] = ()
    rarity_weights: tuple[tuple[str, float], ...] = ()
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()


@dataclass(frozen=True)
class Pack:
    id: str
    collection_id: str
    name: str
    description: str
    price: int  # minor currency units (cents)
    foil_rate: float
    distribution: tuple[PackDistribution, ...]
    image: str | None = None
    spicy_rate: float = 0.2  # chance of bonus spicy drops (chained until a miss)
    spicy_pools: tuple[PackPool, ...] = ()

    @property
    def sticker_count(self) -> int:
        return sum(d.quantity for d in self.distribution)
