from pathlib import Path

from models.catalog import Character
from repositories._json_loading import load_json_file
from repositories.errors import CatalogError, UnknownIdError


class CharacterRepository:
    def __init__(self, characters: list[Character]):
        self._by_id = {c.id: c for c in characters}
        self._by_collection: dict[str, list[Character]] = {}
        for c in characters:
            self._by_collection.setdefault(c.collection_id, []).append(c)

    @classmethod
    def from_raw(cls, raw, source: str = "characters.json") -> "CharacterRepository":
        if not isinstance(raw, list):
            raise CatalogError(f"{source}: expected a list of characters")
        try:
            return cls([
                Character(
                    id=str(r["id"]),
                    collection_id=str(r["collection_id"]),
                    name=str(r["name"]),
                    description=str(r.get("description", "")),
                    portrait_image=r.get("portrait_image"),
                )
                for r in raw
            ])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise CatalogError(f"{source}: malformed character record: {exc}") from exc

    @classmethod
    def from_file(cls, path: Path) -> "CharacterRepository":
        return cls.from_raw(load_json_file(path), path.name)

    def list_all(self) -> list[Character]:
        return list(self._by_id.values())

    def list_by_collection(self, collection_id: str) -> list[Character]:
        return list(self._by_collection.get(collection_id, []))

    def get(self, character_id: str) -> Character:
        try:
            return self._by_id[character_id]
        except KeyError:
            raise UnknownIdError(f"Unknown character: {character_id}") from None
