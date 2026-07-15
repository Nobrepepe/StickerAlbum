from pathlib import Path

from models.catalog import Pack, PackDistribution
from repositories._json_loading import load_json_file
from repositories.errors import CatalogError, UnknownIdError


class PackRepository:
    def __init__(self, packs: list[Pack]):
        self._by_id = {p.id: p for p in packs}

    @classmethod
    def from_file(cls, path: Path) -> "PackRepository":
        raw = load_json_file(path)
        if not isinstance(raw, dict):
            raise CatalogError(f"{path.name}: expected an object keyed by pack ID")
        packs = []
        for pack_id, r in raw.items():
            try:
                packs.append(Pack(
                    id=str(pack_id),
                    collection_id=str(r["collection_id"]),
                    name=str(r["name"]),
                    description=str(r.get("description", "")),
                    price=int(r["price"]),
                    foil_rate=float(r.get("foil_rate", 0.0)),
                    distribution=tuple(
                        PackDistribution(
                            pool=str(d["pool"]),
                            value=str(d["value"]),
                            quantity=int(d["quantity"]),
                        )
                        for d in r["distribution"]
                    ),
                    image=r.get("image"),
                ))
            except (KeyError, TypeError, ValueError) as exc:
                raise CatalogError(f"{path.name}: pack {pack_id!r} is malformed: {exc}") from exc
        return cls(packs)

    def list_all(self) -> list[Pack]:
        return list(self._by_id.values())

    def get(self, pack_id: str) -> Pack:
        try:
            return self._by_id[pack_id]
        except KeyError:
            raise UnknownIdError(f"Unknown pack: {pack_id}") from None
