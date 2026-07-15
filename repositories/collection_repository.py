from pathlib import Path

from models.catalog import Collection
from repositories._json_loading import load_json_file
from repositories.errors import CatalogError, UnknownIdError


class CollectionRepository:
    def __init__(self, collections: list[Collection]):
        self._by_id = {c.id: c for c in collections}
        self._ordered = list(collections)

    @classmethod
    def from_raw(cls, raw, source: str = "collections.json") -> "CollectionRepository":
        if not isinstance(raw, list):
            raise CatalogError(f"{source}: expected a list of collections")
        try:
            return cls([
                Collection(
                    id=str(r["id"]),
                    name=str(r["name"]),
                    description=str(r.get("description", "")),
                    cover_image=r.get("cover_image"),
                    theme_color=r.get("theme_color"),
                )
                for r in raw
            ])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise CatalogError(f"{source}: malformed collection record: {exc}") from exc

    @classmethod
    def from_file(cls, path: Path) -> "CollectionRepository":
        return cls.from_raw(load_json_file(path), path.name)

    def list_all(self) -> list[Collection]:
        return list(self._ordered)

    def get(self, collection_id: str) -> Collection:
        try:
            return self._by_id[collection_id]
        except KeyError:
            raise UnknownIdError(f"Unknown collection: {collection_id}") from None
