"""App settings, separate from playthrough progress so resetting one never
touches the other."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

from repositories._files import atomic_write_json
from repositories.errors import StateSaveError

log = logging.getLogger(__name__)


@dataclass
class Settings:
    creator_enabled: bool = False


class SettingsRepository:
    def __init__(self, path: Path):
        self._path = path
        self.state = self._load()

    def _load(self) -> Settings:
        if not self._path.exists():
            return Settings()
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("settings root is not an object")
        except (json.JSONDecodeError, ValueError, OSError) as exc:
            # Settings are trivially recreatable; fall back to defaults.
            log.warning("Unreadable settings file (%s); using defaults", exc)
            return Settings()
        return Settings(
            creator_enabled=bool(raw.get("creator_enabled", False)),
        )

    def save(self) -> None:
        try:
            atomic_write_json(self._path, {
                "creator_enabled": self.state.creator_enabled,
            })
        except OSError as exc:
            raise StateSaveError(f"Could not save settings: {exc}") from exc

    def set_creator_enabled(self, value: bool) -> None:
        self.state.creator_enabled = value
        self.save()
