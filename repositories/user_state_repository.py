import json
import logging
import os
import time
from pathlib import Path

from models.rarity import STYLES
from models.user_state import SCHEMA_VERSION, UserState
from repositories._files import atomic_write_json
from repositories.errors import StateSaveError

log = logging.getLogger(__name__)


class UserStateRepository:
    """Owns the mutable user state and its JSON file.

    Mutating methods do NOT save automatically; callers (services) decide the
    commit point and call save(), so a pack opening persists atomically.
    """

    def __init__(self, path: Path, known_sticker_ids: set[str] | None = None):
        self._path = path
        self._known_ids = known_sticker_ids
        self.load_warnings: list[str] = []
        self.state = self._load()

    # ---- loading -------------------------------------------------------

    def _load(self) -> UserState:
        if not self._path.exists():
            return UserState()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("state root is not an object")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            backup = self._path.with_name(
                f"{self._path.stem}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}.json"
            )
            try:
                os.replace(self._path, backup)
                msg = f"Saved data was corrupted; backed it up to {backup.name} and started fresh."
            except OSError:
                msg = "Saved data was corrupted and could not be backed up; started fresh."
            log.warning("Corrupted state file (%s): %s", exc, msg)
            self.load_warnings.append(msg)
            return UserState()
        return self._parse(raw)

    def _parse(self, raw: dict) -> UserState:
        state = UserState(schema_version=int(raw.get("schema_version", SCHEMA_VERSION)))

        fav = raw.get("favorite_character_id")
        state.favorite_character_id = str(fav) if fav else None

        total = raw.get("total_saved", 0)
        state.total_saved = total if isinstance(total, int) and total >= 0 else 0

        last = raw.get("last_collection_id")
        state.last_collection_id = str(last) if last else None

        for item in raw.get("inventory", []) or []:
            sid = item.get("sticker_id")
            style = item.get("style")
            qty = item.get("quantity")
            if not sid or style not in STYLES:
                self._warn(f"Ignored inventory entry with bad style/id: {item!r}")
                continue
            if not isinstance(qty, int) or qty <= 0:
                self._warn(f"Ignored inventory entry with invalid quantity: {item!r}")
                continue
            if self._known_ids is not None and sid not in self._known_ids:
                self._warn(f"Ignored inventory entry for unknown sticker {sid!r}")
                continue
            state.inventory[(str(sid), str(style))] = (
                state.inventory.get((str(sid), str(style)), 0) + qty
            )

        for item in raw.get("placements", []) or []:
            sid = item.get("sticker_id")
            style = item.get("style")
            if not sid or style not in STYLES:
                self._warn(f"Ignored placement with bad style/id: {item!r}")
                continue
            if self._known_ids is not None and sid not in self._known_ids:
                self._warn(f"Ignored placement for unknown sticker {sid!r}")
                continue
            if state.inventory.get((str(sid), str(style)), 0) < 1:
                self._warn(f"Ignored placement of unowned style: {sid} ({style})")
                continue
            state.placements[str(sid)] = str(style)

        return state

    def _warn(self, msg: str) -> None:
        log.warning("%s", msg)
        self.load_warnings.append(msg)

    # ---- backup / restore ------------------------------------------------

    def import_data(self, raw: dict) -> list[str]:
        """Replace the current state with imported data (validated the same
        way as a normal load), persist it, and return any warnings."""
        if not isinstance(raw, dict):
            raise ValueError("progress backup root is not an object")
        before = len(self.load_warnings)
        self.state = self._parse(raw)
        self.save()
        return self.load_warnings[before:]

    def reset(self) -> None:
        self.state = UserState()
        self.save()

    # ---- saving --------------------------------------------------------

    def to_payload(self) -> dict:
        return {
            "schema_version": self.state.schema_version,
            "favorite_character_id": self.state.favorite_character_id,
            "total_saved": self.state.total_saved,
            "last_collection_id": self.state.last_collection_id,
            "inventory": [
                {"sticker_id": sid, "style": style, "quantity": qty}
                for (sid, style), qty in sorted(self.state.inventory.items())
            ],
            "placements": [
                {"sticker_id": sid, "style": style}
                for sid, style in sorted(self.state.placements.items())
            ],
        }

    def save(self) -> None:
        """Atomic write: temp file in the same directory, then os.replace."""
        try:
            atomic_write_json(self._path, self.to_payload())
        except OSError as exc:
            raise StateSaveError(f"Could not save your progress: {exc}") from exc

    # ---- inventory -----------------------------------------------------

    def get_quantity(self, sticker_id: str, style: str) -> int:
        return self.state.inventory.get((sticker_id, style), 0)

    def total_owned(self, sticker_id: str) -> int:
        return sum(self.get_quantity(sticker_id, s) for s in STYLES)

    def owned_styles(self, sticker_id: str) -> dict[str, int]:
        return {
            s: q for s in STYLES if (q := self.get_quantity(sticker_id, s)) > 0
        }

    def add_copy(self, sticker_id: str, style: str, count: int = 1) -> None:
        if style not in STYLES:
            raise ValueError(f"Unsupported style: {style}")
        if count < 1:
            raise ValueError("count must be positive")
        key = (sticker_id, style)
        self.state.inventory[key] = self.state.inventory.get(key, 0) + count

    # ---- placements ----------------------------------------------------

    def get_placement(self, sticker_id: str) -> str | None:
        return self.state.placements.get(sticker_id)

    def set_placement(self, sticker_id: str, style: str) -> None:
        self.state.placements[sticker_id] = style

    # ---- misc state ----------------------------------------------------

    def set_favorite_character(self, character_id: str | None) -> None:
        self.state.favorite_character_id = character_id
        self.save()

    def add_savings(self, cents: int) -> None:
        self.state.total_saved += cents

    def set_last_collection(self, collection_id: str | None) -> None:
        self.state.last_collection_id = collection_id
        self.save()
