import json
import logging
import os
import time
from pathlib import Path

from models.draft import DraftCharacter, DraftCollection, DraftSticker, new_draft_skeleton
from repositories._files import atomic_write_json
from repositories.errors import StateSaveError

log = logging.getLogger(__name__)


class DraftRepository:
    """Persists in-progress collections in data/drafts.json."""

    def __init__(self, path: Path):
        self._path = path
        self.load_warnings: list[str] = []
        self._drafts: dict[str, DraftCollection] = {}
        self._load()

    # ---- queries ---------------------------------------------------------

    def list_all(self) -> list[DraftCollection]:
        return list(self._drafts.values())

    def get(self, code: str) -> DraftCollection | None:
        return self._drafts.get(code)

    # ---- mutations (each persists immediately) ---------------------------

    def upsert(self, draft: DraftCollection) -> None:
        self._drafts[draft.id] = draft
        self._save()

    def delete(self, code: str) -> None:
        self._drafts.pop(code, None)
        self._save()

    # ---- persistence -----------------------------------------------------

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("drafts root is not an object")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            backup = self._path.with_name(
                f"{self._path.stem}.corrupt-{time.strftime('%Y%m%d-%H%M%S')}.json"
            )
            try:
                os.replace(self._path, backup)
                msg = f"Draft file was corrupted; backed it up to {backup.name}."
            except OSError:
                msg = "Draft file was corrupted and could not be backed up."
            log.warning("Corrupted drafts file (%s): %s", exc, msg)
            self.load_warnings.append(msg)
            return
        for entry in raw.get("collections", []) or []:
            draft = self._parse_draft(entry)
            if draft:
                self._drafts[draft.id] = draft

    def _parse_draft(self, entry) -> DraftCollection | None:
        code = str(entry.get("id", "")).strip().upper()
        if len(code) != 3 or not code.isalpha():
            self._warn(f"Ignored draft with invalid code: {entry.get('id')!r}")
            return None
        # Rebuild on a fresh skeleton so a hand-edited file with missing
        # characters/stickers still yields the full 10x10 structure.
        draft = new_draft_skeleton(
            code,
            str(entry.get("name", "")),
            str(entry.get("description", "")),
            entry.get("theme_color"),
        )
        draft.cover_image = entry.get("cover_image")
        for c in entry.get("characters", []) or []:
            idx = c.get("index")
            if not isinstance(idx, int) or not 1 <= idx <= 10:
                self._warn(f"Draft {code}: ignored character with bad index {idx!r}")
                continue
            dc = draft.characters[idx - 1]
            dc.name = str(c.get("name", ""))
            dc.description = str(c.get("description", ""))
            dc.portrait_image = c.get("portrait_image")
            for s in c.get("stickers", []) or []:
                pos = s.get("position")
                # Old drafts had 10 slots; the fresh skeleton pads to 15.
                if not isinstance(pos, int) or not 1 <= pos <= 15:
                    self._warn(f"Draft {code}: ignored sticker with bad position {pos!r}")
                    continue
                ds = dc.stickers[pos - 1]
                ds.name = str(s.get("name", ""))
                ds.flavor_text = str(s.get("flavor_text", ""))
                ds.image = s.get("image")
        return draft

    def _warn(self, msg: str) -> None:
        log.warning("%s", msg)
        self.load_warnings.append(msg)

    def _save(self) -> None:
        payload = {
            "collections": [
                {
                    "id": d.id,
                    "name": d.name,
                    "description": d.description,
                    "theme_color": d.theme_color,
                    "cover_image": d.cover_image,
                    "characters": [
                        {
                            "index": c.index,
                            "name": c.name,
                            "description": c.description,
                            "portrait_image": c.portrait_image,
                            "stickers": [
                                {
                                    "position": s.position,
                                    "name": s.name,
                                    "flavor_text": s.flavor_text,
                                    "image": s.image,
                                }
                                for s in c.stickers
                            ],
                        }
                        for c in d.characters
                    ],
                }
                for d in self._drafts.values()
            ],
        }
        try:
            atomic_write_json(self._path, payload)
        except OSError as exc:
            raise StateSaveError(f"Could not save drafts: {exc}") from exc
