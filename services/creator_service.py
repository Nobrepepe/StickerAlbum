"""Rules for creating collections in-app: draft lifecycle, the 10x10
completeness requirements, image imports, and publishing into the catalog."""

import json
import logging
import re
import shutil
from pathlib import Path

from models.draft import DraftCharacter, DraftCollection, DraftSticker, new_draft_skeleton
from models.rarity import SPICY_PER_CHARACTER, slot_rarity
from repositories._files import atomic_write_json
from repositories._json_loading import load_json_file
from repositories.collection_repository import CollectionRepository
from repositories.draft_repository import DraftRepository
from repositories.errors import AppError

log = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")
ALLOWED_SOUND_EXTS = (".mp3", ".wav", ".ogg", ".m4a")

_CODE_RE = re.compile(r"^[A-Z]{3}$")


class CreatorError(AppError):
    """A creator action was rejected (bad code, incomplete draft, ...)."""


def character_id(code: str, index: int) -> str:
    return f"{code}_C{index:02d}"


def sticker_number(char_index: int, position: int) -> int:
    """Regular slots (1-10) number 1-100; spicy slots (11-15) number 101-150."""
    if position <= 10:
        return (char_index - 1) * 10 + position
    return 100 + (char_index - 1) * SPICY_PER_CHARACTER + (position - 10)


def sticker_id(code: str, char_index: int, position: int) -> str:
    return f"{code}_{sticker_number(char_index, position):03d}"


class CreatorService:
    def __init__(
        self,
        drafts: DraftRepository,
        collections: CollectionRepository,
        data_dir: Path,
        assets_dir: Path,
    ):
        self._drafts = drafts
        self._collections = collections
        self._data_dir = data_dir
        self._assets_dir = assets_dir

    # ---- codes -----------------------------------------------------------

    def normalize_code(self, code: str) -> str:
        code = (code or "").strip().upper()
        if not _CODE_RE.match(code):
            raise CreatorError("The code must be exactly three letters (A–Z).")
        return code

    def validate_new_code(self, code: str) -> str:
        code = self.normalize_code(code)
        published = {c.id for c in self._collections.list_all()}
        if code in published or self._drafts.get(code) is not None:
            raise CreatorError(f"The code {code} is already in use. Codes must be unique.")
        return code

    # ---- draft lifecycle ---------------------------------------------------

    def create_collection(
        self, code: str, name: str, description: str = "", theme_color: str | None = None
    ) -> DraftCollection:
        code = self.validate_new_code(code)
        if not name.strip():
            raise CreatorError("The collection needs a name.")
        draft = new_draft_skeleton(code, name.strip(), description.strip(), theme_color)
        self._drafts.upsert(draft)
        return draft

    def save(self, draft: DraftCollection) -> None:
        self._drafts.upsert(draft)

    def delete_draft(self, code: str) -> None:
        self._drafts.delete(code)

    # ---- completeness ------------------------------------------------------

    @staticmethod
    def sticker_complete(sticker: DraftSticker) -> bool:
        return bool(sticker.name.strip())

    @classmethod
    def character_complete(cls, character: DraftCharacter) -> bool:
        return bool(character.name.strip()) and all(
            cls.sticker_complete(s) for s in character.stickers
        )

    @classmethod
    def character_progress(cls, character: DraftCharacter) -> tuple[int, int]:
        return sum(1 for s in character.stickers if cls.sticker_complete(s)), len(
            character.stickers
        )

    @classmethod
    def collection_complete(cls, draft: DraftCollection) -> bool:
        return bool(draft.name.strip()) and len(draft.characters) == 10 and all(
            cls.character_complete(c) for c in draft.characters
        )

    @classmethod
    def collection_progress(cls, draft: DraftCollection) -> tuple[int, int]:
        return sum(1 for c in draft.characters if cls.character_complete(c)), len(
            draft.characters
        )

    # ---- images ------------------------------------------------------------

    def _import_file(self, source: str, rel: str, old: str | None,
                     allowed: tuple[str, ...], what: str) -> str:
        """Copy a media file into assets/ under its canonical name."""
        src = Path(source)
        ext = src.suffix.lower()
        if ext not in allowed:
            raise CreatorError(
                f"Unsupported {what} type {ext or '(none)'}; "
                f"use {', '.join(e.lstrip('.') for e in allowed)}."
            )
        if not src.is_file():
            raise CreatorError(f"File not found: {src.name}")
        dest = self._assets_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(src, dest)
        except OSError as exc:
            raise CreatorError(f"Could not import the {what}: {exc}") from exc
        # Re-uploading with a different extension leaves the old file behind;
        # drop it so the assets folder doesn't accumulate strays.
        if old and old != rel:
            try:
                (self._assets_dir / old).unlink(missing_ok=True)
            except OSError:
                pass
        return rel

    def attach_image(
        self,
        draft: DraftCollection,
        kind: str,  # "cover" | "tile" | "card" | "sticker"
        source: str,
        char_index: int | None = None,
        position: int | None = None,
    ) -> str:
        """Import an image and point the draft at it. Tile and card art are
        convention-named (portraits/<CHAR_ID>_tile / _card) and picked up by
        the UI from disk, so they don't live in a draft field."""
        ext = Path(source).suffix.lower()
        if kind == "cover":
            rel = self._import_file(source, f"covers/{draft.id}{ext}",
                                    draft.cover_image, ALLOWED_IMAGE_EXTS, "image")
            draft.cover_image = rel
        elif kind == "tile":
            cid = character_id(draft.id, char_index)
            rel = self._import_file(source, f"portraits/{cid}_tile{ext}",
                                    None, ALLOWED_IMAGE_EXTS, "image")
        elif kind == "card":
            cid = character_id(draft.id, char_index)
            rel = self._import_file(source, f"portraits/{cid}_card{ext}",
                                    None, ALLOWED_IMAGE_EXTS, "image")
        elif kind == "sticker":
            sticker = draft.characters[char_index - 1].stickers[position - 1]
            rel = self._import_file(
                source, f"stickers/{sticker_id(draft.id, char_index, position)}{ext}",
                sticker.image, ALLOWED_IMAGE_EXTS, "image")
            sticker.image = rel
        else:
            raise ValueError(f"Unknown image kind: {kind}")
        self._drafts.upsert(draft)
        return rel

    def attach_sound(
        self,
        draft: DraftCollection,
        source: str,
        char_index: int,
        position: int,
    ) -> str:
        """Optional voice line for a sticker's flavor text."""
        sticker = draft.characters[char_index - 1].stickers[position - 1]
        ext = Path(source).suffix.lower()
        rel = self._import_file(
            source, f"sounds/{sticker_id(draft.id, char_index, position)}{ext}",
            sticker.sound, ALLOWED_SOUND_EXTS, "sound")
        sticker.sound = rel
        self._drafts.upsert(draft)
        return rel

    # ---- publishing ----------------------------------------------------------

    def publish(self, code: str) -> None:
        """Append a complete draft to the catalog files and remove the draft."""
        draft = self._drafts.get(code)
        if draft is None:
            raise CreatorError(f"No draft with code {code}.")
        if not self.collection_complete(draft):
            done, total = self.collection_progress(draft)
            raise CreatorError(
                f"'{draft.name or code}' is not complete yet "
                f"({done}/{total} characters finished). Every character needs a "
                "name and 15 named stickers (10 regular + 5 spicy)."
            )

        collections_path = self._data_dir / "collections.json"
        characters_path = self._data_dir / "characters.json"
        stickers_path = self._data_dir / "stickers.json"
        collections = load_json_file(collections_path)
        characters = load_json_file(characters_path)
        stickers = load_json_file(stickers_path)

        if any(c.get("id") == draft.id for c in collections):
            raise CreatorError(f"A published collection with code {draft.id} already exists.")

        collections.append({
            "id": draft.id,
            "name": draft.name,
            "description": draft.description,
            "cover_image": draft.cover_image,
            "theme_color": draft.theme_color,
        })
        for c in draft.characters:
            characters.append({
                "id": character_id(draft.id, c.index),
                "collection_id": draft.id,
                "name": c.name.strip(),
                "description": c.description.strip(),
                "portrait_image": c.portrait_image,
            })
            for s in c.stickers:
                stickers.append({
                    "id": sticker_id(draft.id, c.index, s.position),
                    "collection_id": draft.id,
                    "character_id": character_id(draft.id, c.index),
                    "number": sticker_number(c.index, s.position),
                    "name": s.name.strip(),
                    "rarity": slot_rarity(s.position),
                    "image": s.image,
                    "flavor_text": s.flavor_text.strip(),
                    "spicy": s.spicy,
                    "sound": s.sound,
                })

        atomic_write_json(collections_path, collections)
        atomic_write_json(characters_path, characters)
        atomic_write_json(stickers_path, stickers)
        self._drafts.delete(code)
        log.info("Published collection %s (%s)", draft.id, draft.name)
