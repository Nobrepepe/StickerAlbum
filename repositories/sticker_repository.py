import logging
from pathlib import Path

from models.catalog import Sticker
from models.rarity import RARITY_ORDER
from repositories._json_loading import load_json_file
from repositories.errors import CatalogError, UnknownIdError

log = logging.getLogger(__name__)


class StickerRepository:
    def __init__(self, stickers: list[Sticker]):
        valid = []
        for s in stickers:
            if s.rarity not in RARITY_ORDER:
                # Invalid rarity would break pack pools and slot rendering;
                # report and exclude rather than crash later.
                log.warning("Sticker %s has invalid rarity %r; skipped", s.id, s.rarity)
                continue
            valid.append(s)
        self._by_id = {s.id: s for s in valid}
        self._by_collection: dict[str, list[Sticker]] = {}
        self._by_character: dict[str, list[Sticker]] = {}
        for s in valid:
            self._by_collection.setdefault(s.collection_id, []).append(s)
            self._by_character.setdefault(s.character_id, []).append(s)
        for group in (*self._by_collection.values(), *self._by_character.values()):
            group.sort(key=lambda s: s.number)

    @classmethod
    def from_raw(cls, raw, source: str = "stickers.json") -> "StickerRepository":
        if not isinstance(raw, list):
            raise CatalogError(f"{source}: expected a list of stickers")
        try:
            return cls([
                Sticker(
                    id=str(r["id"]),
                    collection_id=str(r["collection_id"]),
                    character_id=str(r["character_id"]),
                    number=int(r["number"]),
                    name=str(r["name"]),
                    rarity=str(r["rarity"]),
                    image=r.get("image"),
                    flavor_text=str(r.get("flavor_text", "")),
                    sound=r.get("sound"),
                )
                for r in raw
            ])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise CatalogError(f"{source}: malformed sticker record: {exc}") from exc

    @classmethod
    def from_file(cls, path: Path) -> "StickerRepository":
        return cls.from_raw(load_json_file(path), path.name)

    def all_ids(self) -> set[str]:
        return set(self._by_id)

    def list_by_collection(self, collection_id: str) -> list[Sticker]:
        return list(self._by_collection.get(collection_id, []))

    def list_by_character(self, character_id: str) -> list[Sticker]:
        return list(self._by_character.get(character_id, []))

    def list_by_rarity(self, collection_id: str, rarity: str) -> list[Sticker]:
        return [s for s in self._by_collection.get(collection_id, []) if s.rarity == rarity]

    def get(self, sticker_id: str) -> Sticker:
        try:
            return self._by_id[sticker_id]
        except KeyError:
            raise UnknownIdError(f"Unknown sticker: {sticker_id}") from None

    def resolve_pool(self, pool: str) -> list[Sticker]:
        """A pack pool is a collection ID or a character ID."""
        if pool in self._by_collection:
            return list(self._by_collection[pool])
        if pool in self._by_character:
            return list(self._by_character[pool])
        return []
