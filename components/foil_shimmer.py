"""Foil shimmer: a pulsing sheen constrained to the sticker's silhouette.

The mask (assets/stickers/<ID>_mask.png) must have a transparent background
with an opaque silhouette; ShaderMask with SRC_IN paints the sheen gradient
only where the mask has alpha, so the white vignette edges never shimmer.

The pulse task starts in did_mount and stops in will_unmount, mirroring the
carousel's lifecycle handling, with a small random phase offset so several
foils on screen don't blink in unison.
"""

import asyncio
import random

import flet as ft


class FoilShimmer(ft.Container):
    def __init__(self, mask_src: str, width: float, height: float):
        super().__init__(width=width, height=height)
        self.opacity = 0.0
        self.animate_opacity = ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
        self.content = ft.ShaderMask(
            content=ft.Image(
                src=mask_src, width=width, height=height, fit=ft.ImageFit.CONTAIN
            ),
            blend_mode=ft.BlendMode.SRC_IN,
            shader=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[
                    ft.Colors.with_opacity(0.0, "#ffd54f"),
                    ft.Colors.with_opacity(0.85, "#fffbe6"),
                    ft.Colors.with_opacity(0.25, "#ffd54f"),
                ],
                stops=[0.15, 0.5, 0.85],
            ),
        )
        self._task: asyncio.Task | None = None

    def did_mount(self):
        if self._task is None:
            self._task = self.page.run_task(self._pulse)

    def will_unmount(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _pulse(self):
        try:
            await asyncio.sleep(random.uniform(0.0, 1.2))
            while True:
                self.opacity = 0.8
                self._safe_update()
                await asyncio.sleep(1.1)
                self.opacity = 0.0
                self._safe_update()
                await asyncio.sleep(1.1)
        except asyncio.CancelledError:
            pass

    def _safe_update(self):
        if self.page is None:
            return
        try:
            self.update()
        except Exception:
            pass
