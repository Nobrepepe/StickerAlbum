"""Export, import, and reset for the two kinds of saved data:

- playthrough progress (inventory, placements, favorite, savings)
- the authored catalog (collections, characters, stickers, plus drafts)

Imports are validated before anything on disk is replaced.
"""

import json
import logging
from pathlib import Path

from repositories._files import atomic_write_json
from repositories.character_repository import CharacterRepository
from repositories.collection_repository import CollectionRepository
from repositories.draft_repository import DraftRepository
from repositories.errors import AppError, CatalogError
from repositories.sticker_repository import StickerRepository
from repositories.user_state_repository import UserStateRepository

log = logging.getLogger(__name__)

PROGRESS_FORMAT = "sticker-album-progress"
CATALOG_FORMAT = "sticker-album-catalog"


class BackupError(AppError):
    """A backup/restore operation failed in a user-presentable way."""


def _read_json(path: Path) -> dict:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BackupError(f"Could not read the backup file: {exc}") from exc
    if not isinstance(raw, dict):
        raise BackupError("That file doesn't look like an album backup.")
    return raw


class BackupService:
    def __init__(
        self,
        state: UserStateRepository,
        drafts: DraftRepository,
        data_dir: Path,
    ):
        self._state = state
        self._drafts = drafts
        self._data_dir = data_dir

    # ---- playthrough progress ---------------------------------------------

    def export_progress(self, dest: str) -> None:
        payload = {"format": PROGRESS_FORMAT, **self._state.to_payload()}
        try:
            atomic_write_json(Path(dest), payload)
        except OSError as exc:
            raise BackupError(f"Could not write the backup: {exc}") from exc

    def import_progress(self, source: str) -> list[str]:
        raw = _read_json(Path(source))
        # Accept both exported backups and a raw user_state.json.
        if "inventory" not in raw and "placements" not in raw:
            raise BackupError("That file doesn't contain album progress.")
        return self._state.import_data(raw)

    def reset_progress(self) -> None:
        self._state.reset()

    # ---- authored catalog ---------------------------------------------------

    def export_catalog(self, dest: str) -> None:
        try:
            payload = {
                "format": CATALOG_FORMAT,
                "collections": json.loads(
                    (self._data_dir / "collections.json").read_text(encoding="utf-8")),
                "characters": json.loads(
                    (self._data_dir / "characters.json").read_text(encoding="utf-8")),
                "stickers": json.loads(
                    (self._data_dir / "stickers.json").read_text(encoding="utf-8")),
                "drafts": json.loads(
                    (self._data_dir / "drafts.json").read_text(encoding="utf-8"))
                if (self._data_dir / "drafts.json").exists() else {"collections": []},
            }
            atomic_write_json(Path(dest), payload)
        except (OSError, json.JSONDecodeError) as exc:
            raise BackupError(f"Could not write the catalog backup: {exc}") from exc

    def import_catalog(self, source: str) -> None:
        """Replace the whole catalog with a backup bundle (validated first)."""
        raw = _read_json(Path(source))
        if raw.get("format") != CATALOG_FORMAT or not all(
            k in raw for k in ("collections", "characters", "stickers")
        ):
            raise BackupError("That file is not a catalog backup.")
        try:
            # Parse everything through the normal repository loaders so a bad
            # bundle is rejected before any file is touched.
            CollectionRepository.from_raw(raw["collections"], "backup")
            CharacterRepository.from_raw(raw["characters"], "backup")
            StickerRepository.from_raw(raw["stickers"], "backup")
        except CatalogError as exc:
            raise BackupError(f"Invalid catalog backup: {exc}") from exc

        atomic_write_json(self._data_dir / "collections.json", raw["collections"])
        atomic_write_json(self._data_dir / "characters.json", raw["characters"])
        atomic_write_json(self._data_dir / "stickers.json", raw["stickers"])
        drafts = raw.get("drafts")
        atomic_write_json(
            self._data_dir / "drafts.json",
            drafts if isinstance(drafts, dict) else {"collections": []},
        )
        log.info("Catalog restored from %s", source)

    def reset_catalog(self) -> None:
        """Delete every collection, character, and sticker (drafts included).
        Packs (data/packs.json) are managed by hand and left untouched."""
        atomic_write_json(self._data_dir / "collections.json", [])
        atomic_write_json(self._data_dir / "characters.json", [])
        atomic_write_json(self._data_dir / "stickers.json", [])
        atomic_write_json(self._data_dir / "drafts.json", {"collections": []})
        log.info("Catalog reset: all collections deleted")
