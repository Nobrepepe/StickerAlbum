import asyncio

from components import audio_player


class FakeAudio:
    def __init__(self, **kwargs):
        self.src = kwargs.get("src")
        self.autoplay = kwargs.get("autoplay")
        self.data = kwargs.get("data")
        self.updated = 0
        self.played = 0
        self.seeked = []

    def update(self):
        self.updated += 1

    def play(self):
        self.played += 1

    def seek(self, position):
        self.seeked.append(position)


class FakePage:
    def __init__(self):
        self.overlay = []
        self.updated = 0

    def update(self):
        self.updated += 1


def test_first_sound_mounts_with_source_and_autoplay(monkeypatch):
    page = FakePage()
    monkeypatch.setattr(audio_player.ft, "Audio", FakeAudio)
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: f"/{rel}")

    audio_player.play_sound(page, "sounds/voice.mp3")

    assert len(page.overlay) == 1
    assert page.overlay[0].src == "/sounds/voice.mp3"
    assert page.overlay[0].autoplay is True
    assert page.overlay[0].played == 0
    assert page.updated == 1


def test_each_sound_replaces_player_without_accumulating(monkeypatch):
    page = FakePage()
    old_player = FakeAudio(src="/sounds/old.mp3", autoplay=True,
                           data=audio_player._MARKER)
    page.overlay.append(old_player)
    monkeypatch.setattr(audio_player.ft, "Audio", FakeAudio)
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: f"/{rel}")

    audio_player.play_sound(page, "sounds/new.mp3")
    assert len(page.overlay) == 1
    assert page.overlay[0] is not old_player
    assert page.overlay[0].src == "/sounds/new.mp3"
    assert page.overlay[0].autoplay is True
    assert page.updated == 1


def test_stamp_then_voice_waits_for_stamp(monkeypatch):
    calls = []

    monkeypatch.setattr(audio_player, "play_stamp",
                        lambda page: calls.append("stamp"))
    monkeypatch.setattr(audio_player, "play_sound",
                        lambda page, rel: calls.append(rel))
    monkeypatch.setattr(audio_player, "resolve_sound",
                        lambda rel: "/voice.mp3" if rel else None)

    async def no_wait(delay):
        calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", no_wait)
    asyncio.run(audio_player.play_stamp_then(object(), "sounds/voice.mp3"))

    assert calls == ["stamp", audio_player.STAMP_DURATION_SECONDS,
                     "sounds/voice.mp3"]


def test_normal_reveal_uses_reveal_sound_then_voice(monkeypatch):
    calls = []
    page = object()
    monkeypatch.setattr(
        audio_player, "play_sound", lambda p, rel: calls.append((p, rel))
    )
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: f"/{rel}")

    async def no_wait(delay):
        calls.append(delay)

    monkeypatch.setattr(asyncio, "sleep", no_wait)
    asyncio.run(audio_player.play_reveal_then(page, "sounds/voice.mp3"))

    assert calls == [
        (page, audio_player.REVEAL_SOUND),
        audio_player.REVEAL_DURATION_SECONDS,
        (page, "sounds/voice.mp3"),
    ]


def test_spicy_reveal_replaces_normal_reveal_cue(monkeypatch):
    calls = []
    monkeypatch.setattr(
        audio_player, "play_sound", lambda page, rel: calls.append(rel)
    )
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: None)

    asyncio.run(audio_player.play_reveal_then(object(), None, True))

    assert calls == [audio_player.SPICY_SOUND]


def test_new_sticker_uses_new_reveal_cue(monkeypatch):
    calls = []
    monkeypatch.setattr(
        audio_player, "play_sound", lambda page, rel: calls.append(rel)
    )
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: None)

    asyncio.run(audio_player.play_reveal_then(object(), None, False, True))

    assert calls == [audio_player.NEW_SOUND]


def test_spicy_takes_priority_over_new_reveal_cue(monkeypatch):
    calls = []
    monkeypatch.setattr(
        audio_player, "play_sound", lambda page, rel: calls.append(rel)
    )
    monkeypatch.setattr(audio_player, "resolve_sound", lambda rel: None)

    asyncio.run(audio_player.play_reveal_then(object(), None, True, True))

    assert calls == [audio_player.SPICY_SOUND]
