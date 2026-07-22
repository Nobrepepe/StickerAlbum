"""Shared sound playback: the stamping SFX and per-sticker voice lines.

Keeps a single Audio control in page.overlay (mirroring the FilePicker-in-
overlay convention used elsewhere), reusing it for every clip so we don't
accumulate one per playback.
"""

import flet as ft

from components.assets import resolve_sound

STAMP_SOUND = "sounds/stamp.wav"
SPICY_SOUND = "sounds/spicy.wav"  # placeholder — swap in a real cue later


_MARKER = "_album_audio_player"


def _player(page: ft.Page) -> ft.Audio:
    # ft.Audio is deprecated in favor of the flet-audio package: in 0.28.3
    # its class is wrapped by a decorator that turns `ft.Audio` into a
    # plain function, so `isinstance(c, ft.Audio)` raises TypeError. Tag
    # our instance instead of type-checking for it.
    for c in page.overlay:
        if getattr(c, "data", None) == _MARKER:
            return c
    player = ft.Audio(autoplay=False, data=_MARKER)
    page.overlay.append(player)
    page.update()
    return player


def play_sound(page: ft.Page, relative: str | None) -> None:
    """Play a sound file relative to assets/ (e.g. 'sounds/MRC_001.mp3').
    Silently no-ops if the file is missing, so playback stays optional."""
    src = resolve_sound(relative)
    if not src:
        return
    player = _player(page)
    player.src = src
    player.update()
    player.play()


def play_stamp(page: ft.Page) -> None:
    """The tactile 'thump' when a sticker is pressed onto the board."""
    play_sound(page, STAMP_SOUND)


def play_spicy(page: ft.Page) -> None:
    """Cue for revealing a spicy sticker in a pack opening."""
    play_sound(page, SPICY_SOUND)
