from pathlib import Path

from models.catalog import Pack, PackDistribution, PackPool
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
                def pools(value) -> tuple[PackPool, ...]:
                    if value is None:
                        return ()
                    return tuple(
                        PackPool(str(item), 1.0)
                        if isinstance(item, str)
                        else PackPool(str(item["pool"]), float(item.get("weight", 1.0)))
                        for item in value
                    )

                def distribution(d) -> PackDistribution:
                    custom_pools = pools(d.get("pools"))
                    rarity_weights = tuple(
                        (str(rarity), float(weight))
                        for rarity, weight in d.get("rarity_weights", {}).items()
                    )
                    return PackDistribution(
                        pool=str(d.get("pool", "")),
                        value=str(d.get("value", "")),
                        quantity=int(d["quantity"]),
                        pools=custom_pools,
                        rarity_weights=rarity_weights,
                        include=tuple(str(s) for s in d.get("include", ())),
                        exclude=tuple(str(s) for s in d.get("exclude", ())),
                    )

                packs.append(Pack(
                    id=str(pack_id),
                    collection_id=str(r["collection_id"]),
                    name=str(r["name"]),
                    description=str(r.get("description", "")),
                    price=int(r["price"]),
                    foil_rate=float(r.get("foil_rate", 0.0)),
                    spicy_rate=float(r.get("spicy_rate", 0.2)),
                    distribution=tuple(distribution(d) for d in r["distribution"]),
                    image=r.get("image"),
                    spicy_pools=pools(r.get("spicy_pools")),
                ))
            except (KeyError, TypeError, ValueError, AttributeError) as exc:
                raise CatalogError(f"{path.name}: pack {pack_id!r} is malformed: {exc}") from exc
        return cls(packs)

    def list_all(self) -> list[Pack]:
        return list(self._by_id.values())

    def get(self, pack_id: str) -> Pack:
        try:
            return self._by_id[pack_id]
        except KeyError:
            raise UnknownIdError(f"Unknown pack: {pack_id}") from None
