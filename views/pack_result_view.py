"""Tactile, interruptible pack-opening reveal sequence."""

import asyncio
from contextlib import suppress

import flet as ft

from components.assets import sticker_mask_image
from components.audio_player import (
    TEAR_SOUND,
    play_reveal_then,
    play_sound,
    play_spicy,
    play_stamp,
)
from components.foil_shimmer import FoilShimmer
from components.paper import (
    dashed_rule,
    ink_button,
    outline_button,
    page_caption,
    paper_label,
)
from components.placeholders import cover_band, sticker_art
from components.theme import CARD_BG, DESK_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from models.money import format_money
from models.results import PackOpenResult

STAGE_W, STAGE_H = 600.0, 400.0
CARD_W, CARD_H = 132.0, 176.0
CARD_LEFT, CARD_TOP = 234.0, 205.0
PACK_W, PACK_H = 260.0, 146.25
PACK_LEFT, PACK_TOP = 170.0, 240.0
FOCUS_DY = -145.0
MAX_FAN = 5


class _PackReveal(ft.Column):
    def __init__(self, page: ft.Page, ctx, nav, result: PackOpenResult):
        super().__init__(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.host_page = page
        self.ctx = ctx
        self.nav = nav
        self.result = result
        self.items = result.items
        self.index = -1
        self._task: asyncio.Task | None = None
        self._mounted = False

        self.shadow = ft.Container(
            width=100,
            height=14,
            left=250,
            top=382,
            border_radius=50,
            bgcolor="#2f26184f",
            opacity=0,
            animate_opacity=ft.Animation(460, ft.AnimationCurve.EASE_OUT),
            shadow=ft.BoxShadow(blur_radius=14, color="#2f26183d"),
        )
        self.cards = [self._item_card(i) for i in range(len(self.items))]
        self.pack_body = ft.Container(
            width=PACK_W,
            height=PACK_H,
            left=PACK_LEFT,
            top=PACK_TOP,
            offset=ft.Offset(0, -4.25),
            scale=1.06,
            bgcolor=CARD_BG,
            shadow=ft.BoxShadow(blur_radius=10, color="#00000052",
                                offset=ft.Offset(0, 6)),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=cover_band(
                result.pack.image,
                self._pack_theme(),
                height=PACK_H,
            ),
            animate_offset=ft.Animation(460, ft.AnimationCurve.EASE_OUT_BACK),
            animate_scale=ft.Animation(240, ft.AnimationCurve.EASE_OUT),
        )
        self.crimp = ft.Container(
            width=PACK_W,
            height=18,
            left=PACK_LEFT,
            top=PACK_TOP - 18,
            bgcolor=CARD_BG,
            offset=ft.Offset(0, -34.5),
            # Positioned controls must be direct children of a Stack. Keeping
            # this rule in a bare Container made Flet render its red runtime
            # error placeholder until the tear animation hid the crimp.
            content=ft.Stack(
                [
                    ft.Container(
                        content=dashed_rule(PACK_W - 6),
                        bottom=0,
                        left=3,
                    )
                ],
                expand=True,
            ),
            animate_offset=ft.Animation(300, ft.AnimationCurve.EASE_IN),
            animate_rotation=ft.Animation(300, ft.AnimationCurve.EASE_IN),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_IN),
        )
        self.vignette = ft.Container(
            width=STAGE_W,
            height=STAGE_H,
            bgcolor="#140e0859",
            opacity=0,
            ignore_interactions=True,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_OUT),
        )
        self.album_marker = ft.Container(
            width=92,
            height=66,
            right=24,
            bottom=22,
            border=ft.border.all(1.5, "#2f261859"),
            alignment=ft.alignment.center,
            content=ft.Text(
                "ALBUM",
                size=10,
                font_family=META_FONT,
                color=INK_SOFT,
            ),
        )
        self.stage = ft.Stack(
            [
                self.shadow,
                *self.cards,
                self.pack_body,
                self.crimp,
                self.vignette,
                self.album_marker,
            ],
            width=STAGE_W,
            height=STAGE_H,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        )

        self.beat_name = ft.Text(
            "PACK READY",
            size=11,
            font_family=DISPLAY_FONT,
            weight=ft.FontWeight.W_700,
            color=INK,
            style=ft.TextStyle(letter_spacing=1.1),
        )
        self.beat_note = ft.Text(
            "The deposit and stickers are already safely recorded.",
            size=10.5,
            font_family=META_FONT,
            color=INK_SOFT,
        )
        self.counter = ft.Text(
            f"0 / {len(self.items)}",
            size=11,
            font_family=META_FONT,
            color=INK_SOFT,
        )
        self.reveal_next = ink_button("REVEAL NEXT", self._on_reveal_next)
        self.reveal_next.disabled = True
        self.reveal_next.opacity = 0.45
        self.reveal_all = outline_button("REVEAL ALL", self._on_reveal_all)
        self.reveal_all.disabled = True
        self.continue_shop = ink_button(
            "CONTINUE TO SHOP",
            lambda e: self._start_file(self.nav.go_shop),
        )
        self.continue_shop.visible = False
        self.open_album = outline_button(
            "OPEN ALBUM",
            lambda e: self._start_file(
                lambda: self.nav.go_album(self.result.pack.collection_id)
            ),
        )
        self.open_album.visible = False

        footer = ft.Container(
            width=STAGE_W,
            bgcolor=CARD_BG,
            padding=ft.padding.symmetric(horizontal=16, vertical=14),
            border=ft.border.only(top=ft.BorderSide(1, "#2f261824")),
            content=ft.Row(
                [
                    ft.Column(
                        [self.beat_name, self.beat_note],
                        spacing=6,
                        tight=True,
                        expand=True,
                    ),
                    self.counter,
                    self.reveal_all,
                    self.reveal_next,
                    self.open_album,
                    self.continue_shop,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        new_count = sum(item.is_new for item in self.items)
        self.controls = [
            ft.Row(
                [
                    ft.Text(
                        f"OPENING: {result.pack.name}".upper(),
                        size=22,
                        font_family=DISPLAY_FONT,
                        weight=ft.FontWeight.W_900,
                        color=INK,
                        expand=True,
                    ),
                    ft.Text(
                        f"{format_money(result.deposit)} deposited · "
                        f"{new_count} new · "
                        f"{len(self.items) - new_count} duplicate",
                        size=11,
                        font_family=META_FONT,
                        color=INK_SOFT,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            self.stage,
            footer,
        ]

    def _pack_theme(self):
        with suppress(Exception):
            return self.ctx.collections.get(
                self.result.pack.collection_id
            ).theme_color
        return None

    def _item_card(self, i: int) -> ft.Control:
        item = self.items[i]
        labels = [
            paper_label("NEW" if item.is_new else "DUPLICATE", size=7.5),
            paper_label(item.sticker.rarity.upper(), item.sticker.rarity, size=7.5),
        ]
        if item.style == "foil":
            labels.append(paper_label("FOIL", gold=True, size=7.5))
        if item.sticker.spicy:
            labels.append(paper_label("🌶️", "spicy", size=7.5))
        art_layers: list[ft.Control] = [
            sticker_art(item.sticker, CARD_W - 10, 136),
        ]
        if item.style == "foil":
            mask = sticker_mask_image(item.sticker.id)
            if mask:
                art_layers.append(FoilShimmer(mask, CARD_W - 10, 136))
        return ft.Container(
            width=CARD_W,
            height=CARD_H,
            left=CARD_LEFT,
            top=CARD_TOP,
            bgcolor="#ffffff",
            padding=5,
            opacity=0,
            shadow=ft.BoxShadow(blur_radius=8, color="#0000004d",
                                offset=ft.Offset(0, 4)),
            content=ft.Stack(
                [
                    ft.Stack(art_layers, width=CARD_W - 10, height=136),
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    item.sticker.name,
                                    size=9,
                                    font_family=DISPLAY_FONT,
                                    weight=ft.FontWeight.W_700,
                                    color=INK,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Row(labels, spacing=2, wrap=True),
                            ],
                            spacing=3,
                        ),
                        left=3,
                        right=3,
                        bottom=3,
                    ),
                ],
                expand=True,
            ),
            animate_offset=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
            animate_rotation=ft.Animation(320, ft.AnimationCurve.EASE_OUT),
            animate_scale=ft.Animation(380, ft.AnimationCurve.EASE_OUT_BACK),
            animate_opacity=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

    def did_mount(self):
        self._mounted = True
        self._task = self.host_page.run_task(self._intro)

    def will_unmount(self):
        self._mounted = False
        self._cancel_task()

    def _cancel_task(self):
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None

    async def _wait(self, seconds: float) -> bool:
        await asyncio.sleep(seconds)
        return self._mounted and self.page is not None

    def _safe_update(self):
        if not self._mounted or self.page is None:
            return
        with suppress(Exception):
            self.update()

    async def _intro(self):
        try:
            self.beat_name.value = "THE PACK LANDS"
            self.pack_body.offset = ft.Offset(0, 0)
            self.pack_body.scale = 1
            self.crimp.offset = ft.Offset(0, 0)
            self.shadow.opacity = 1
            play_stamp(self.host_page)
            self._safe_update()
            if not await self._wait(0.48):
                return

            self.beat_name.value = "TEAR THE CRIMP"
            self.crimp.offset = ft.Offset(0, -0.55)
            self.crimp.rotate = ft.Rotate(-0.38)
            self.crimp.opacity = 0
            self.pack_body.scale = 0.975
            play_sound(self.host_page, TEAR_SOUND)
            self._safe_update()
            if not await self._wait(0.16):
                return
            self.pack_body.scale = 1
            self._safe_update()
            if not await self._wait(0.18):
                return

            self.beat_name.value = "THE STICKERS FAN OUT"
            for i in range(min(MAX_FAN, len(self.cards))):
                self._set_fan_pose(i, i)
                self.cards[i].opacity = 1
                self._safe_update()
                if not await self._wait(0.07):
                    return
            self.beat_name.value = "READY TO REVEAL"
            self.beat_note.value = "Reveal one at a time, or file the whole pack."
            self.reveal_next.disabled = False
            self.reveal_next.opacity = 1
            self.reveal_all.disabled = False
            self._safe_update()
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    def _set_fan_pose(self, card_index: int, slot: int):
        card = self.cards[card_index]
        dx = (slot - 2) * 27
        dy = -48 - (4 - slot) * 2
        card.offset = ft.Offset(dx / CARD_W, dy / CARD_H)
        card.rotate = ft.Rotate((slot - 2) * 5 * 3.141592653589793 / 180)
        card.scale = 1

    def _raise_card(self, card_index: int) -> None:
        """Paint the focused card above the fan, but still behind the pack."""
        focused = self.cards[card_index]
        self.stage.controls = [
            self.shadow,
            *(card for card in self.cards if card is not focused),
            focused,
            self.pack_body,
            self.crimp,
            self.vignette,
            self.album_marker,
        ]

    def _on_reveal_next(self, e):
        if self._task is not None or self.index >= len(self.items) - 1:
            return
        self._task = self.host_page.run_task(self._present_next)

    async def _present_next(self):
        try:
            if self.index >= 0:
                previous = self.cards[self.index]
                previous.opacity = 0.4
                previous.scale = 0.92
            self.index += 1
            window_start = max(0, self.index - (MAX_FAN - 1))
            for i, card in enumerate(self.cards):
                if i < window_start:
                    card.opacity = 0
                elif window_start <= i < window_start + MAX_FAN:
                    slot = i - window_start
                    self._set_fan_pose(i, slot)
                    card.opacity = 0.4 if i < self.index else 1
            card = self.cards[self.index]
            card.opacity = 1
            card.offset = ft.Offset(0, FOCUS_DY / CARD_H)
            card.scale = 1.55
            card.rotate = ft.Rotate(-0.07 if self.items[self.index].sticker.spicy else 0)
            self._raise_card(self.index)
            special = (
                self.items[self.index].style == "foil"
                or self.items[self.index].sticker.rarity == "legendary"
            )
            self.vignette.opacity = 1 if special else 0
            self.counter.value = f"{self.index + 1} / {len(self.items)}"
            self.beat_name.value = self.items[self.index].sticker.name.upper()
            self.beat_note.value = (
                f"{self.items[self.index].sticker.rarity} · "
                f"{'foil' if self.items[self.index].style == 'foil' else 'normal'}"
            )
            self.reveal_next.disabled = True
            self.reveal_next.opacity = 0.45
            self._safe_update()
            self.host_page.run_task(
                play_reveal_then,
                self.host_page,
                self.items[self.index].sticker.sound,
                self.items[self.index].sticker.spicy,
                self.items[self.index].is_new,
            )
            hold = 0.38
            if self.items[self.index].sticker.rarity in {"rare", "epic"}:
                hold += 0.08
            if special:
                hold += 0.4
            if not await self._wait(hold):
                return
            if self.items[self.index].sticker.spicy:
                card.rotate = ft.Rotate(0)
            done = self.index >= len(self.items) - 1
            self.reveal_next.visible = not done
            self.reveal_all.visible = not done
            self.continue_shop.visible = done
            self.open_album.visible = done
            self.reveal_next.disabled = False
            self.reveal_next.opacity = 1
            self._safe_update()
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    def _play_if_spicy(self, indices) -> None:
        if any(self.items[i].sticker.spicy for i in indices):
            play_spicy(self.host_page)

    def _on_reveal_all(self, e):
        start = self.index + 1
        self._cancel_task()
        self.index = len(self.items) - 1
        window_start = max(0, len(self.items) - MAX_FAN)
        for i, card in enumerate(self.cards):
            if i < window_start:
                card.opacity = 0
                continue
            self._set_fan_pose(i, i - window_start)
            card.opacity = 0.4
            card.scale = 0.92
        final = self.cards[-1]
        final.opacity = 1
        final.offset = ft.Offset(0, FOCUS_DY / CARD_H)
        final.scale = 1.55
        final.rotate = ft.Rotate(0)
        self._raise_card(self.index)
        self.counter.value = f"{len(self.items)} / {len(self.items)}"
        self.beat_name.value = "PACK REVEALED"
        self.beat_note.value = "Every sticker is already safely in your collection."
        self.reveal_next.visible = False
        self.reveal_all.visible = False
        self.continue_shop.visible = True
        self.open_album.visible = True
        self.vignette.opacity = (
            1 if final and (
                self.items[-1].style == "foil"
                or self.items[-1].sticker.rarity == "legendary"
            ) else 0
        )
        self._safe_update()
        self._play_if_spicy(range(start, len(self.items)))

    def _start_file(self, callback):
        self._cancel_task()
        self._task = self.host_page.run_task(self._file_and_leave, callback)

    async def _file_and_leave(self, callback):
        try:
            visible = [card for card in self.cards if card.opacity]
            for card in visible:
                card.offset = ft.Offset(215 / CARD_W, 255 / CARD_H)
                card.scale = 0.2
                card.opacity = 0
                self._safe_update()
                if not await self._wait(0.06):
                    return
            if not await self._wait(0.4):
                return
            callback()
        except asyncio.CancelledError:
            pass


def build_pack_result(page: ft.Page, ctx, nav, result: PackOpenResult) -> ft.Control:
    """The result is committed before this interruptible view is constructed."""
    return ft.Container(
        expand=True,
        alignment=ft.alignment.top_center,
        content=ft.Column(
            [
                page_caption("every pack you open records a real deposit"),
                _PackReveal(page, ctx, nav, result),
            ],
            spacing=18,
            expand=True,
        ),
    )
