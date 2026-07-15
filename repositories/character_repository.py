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
    def from_file(cls, path: Path) -> "CharacterRepository":
        raw = load_json_file(path)
        if not isinstance(raw, list):
            raise CatalogError(f"{path.name}: expected a list of characters")
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

    def list_all(self) -> list[Character]:
        return list(self._by_id.values())

    def list_by_collection(self, collection_id: str) -> list[Character]:
        return list(self._by_collection.get(collection_id, []))

    def get(self, character_id: str) -> Character:
        try:
            return self._by_id[character_id]
        except KeyError:
            raise UnknownIdError(f"Unknown character: {character_id}") from None
