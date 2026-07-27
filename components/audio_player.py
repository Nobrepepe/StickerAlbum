"""Shared sound playback: the stamping SFX and per-sticker voice lines.

Keeps a single Audio control in page.overlay (mirroring the FilePicker-in-
overlay convention used elsewhere). Each request replaces that control with
one whose source is assigned before mounting; autoplay then waits for the
client to finish loading it.
"""

import asyncio

import flet as ft

from components.assets import resolve_sound

STAMP_SOUND = "sounds/stamp.wav"
SPICY_SOUND = "sounds/spicy.wav"  # placeholder — swap in a real cue later
TEAR_SOUND = "sounds/tear.wav"
STAMP_DURATION_SECONDS = 1.0


_MARKER = "_album_audio_player"


def _player(page: ft.Page) -> ft.Audio | None:
    # ft.Audio is deprecated in favor of the flet-audio package: in 0.28.3
    # its class is wrapped by a decorator that turns `ft.Audio` into a
    # plain function, so `isinstance(c, ft.Audio)` raises TypeError. Tag
    # our instance instead of type-checking for it.
    for c in page.overlay:
        if getattr(c, "data", None) == _MARKER:
            return c
    return None


def play_sound(page: ft.Page, relative: str | None) -> None:
    """Play a sound file relative to assets/ (e.g. 'sounds/MRC_001.mp3').
    Silently no-ops if the file is missing, so playback stays optional."""
    src = resolve_sound(relative)
    if not src:
        return
    old_player = _player(page)
    player = ft.Audio(src=src, autoplay=True, data=_MARKER)
    if old_player is None:
        page.overlay.append(player)
    else:
        page.overlay[page.overlay.index(old_player)] = player
    # The source is present on the first client render, avoiding an immediate
    # play() command against an unloaded source.
    page.update()


def play_stamp(page: ft.Page) -> None:
    """The tactile 'thump' when a sticker is pressed onto the board."""
    play_sound(page, STAMP_SOUND)


async def play_stamp_then(page: ft.Page, relative: str | None) -> None:
    """Play the complete stamp cue, followed by an optional voice line."""
    play_stamp(page)
    if not resolve_sound(relative):
        return
    await asyncio.sleep(STAMP_DURATION_SECONDS)
    play_sound(page, relative)


def play_spicy(page: ft.Page) -> None:
    """Cue for revealing a spicy sticker in a pack opening."""
    play_sound(page, SPICY_SOUND)
