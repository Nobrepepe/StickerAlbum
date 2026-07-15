"""Result models returned by services to the UI."""

from dataclasses import dataclass

from models.catalog import Pack, Sticker


@dataclass(frozen=True)
class OpenedSticker:
    sticker: Sticker
    style: str  # "normal" | "foil"
    is_new: bool  # no copy of this sticker (any style) existed before this one


@dataclass(frozen=True)
class PackOpenResult:
    pack: Pack
    items: tuple[OpenedSticker, ...]
    deposit: int  # cents recorded into savings
