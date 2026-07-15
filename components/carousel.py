"""Auto-advancing sticker carousel for the Home screen.

The auto task is started in did_mount and cancelled in will_unmount, so
rebuilding Home never leaves duplicate background tasks running, and updates
after the control leaves the page are swallowed safely.
"""

import asyncio

import flet as ft


class StickerCarousel(ft.Container):
    def __init__(self, slides: list[ft.Control], interval: float = 5.0):
        super().__init__()
        assert slides, "StickerCarousel requires at least one slide"
        self._slides = slides
        self._interval = interval
        self._idx = 0
        self._task: asyncio.Task | None = None

        self._switcher = ft.AnimatedSwitcher(
            content=slides[0],
            transition=ft.AnimatedSwitcherTransition.FADE,
            duration=400,
            reverse_duration=200,
        )
        self._counter = ft.Text(self._label(), size=12, color=ft.Colors.GREY_500)
        self.content = ft.Column(
            [
                self._switcher,
                ft.Row(
                    [
                        ft.IconButton(
                            ft.Icons.CHEVRON_LEFT,
                            on_click=lambda e: self._advance(-1),
                            tooltip="Previous",
                        ),
                        self._counter,
                        ft.IconButton(
                            ft.Icons.CHEVRON_RIGHT,
                            on_click=lambda e: self._advance(1),
                            tooltip="Next",
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=4,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
            tight=True,
        )

    def _label(self) -> str:
        return f"{self._idx + 1} / {len(self._slides)}"

    def did_mount(self):
        if len(self._slides) > 1 and self._task is None:
            self._task = self.page.run_task(self._auto_loop)

    def will_unmount(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def _auto_loop(self):
        try:
            while True:
                await asyncio.sleep(self._interval)
                self._advance(1)
        except asyncio.CancelledError:
            pass

    def _advance(self, step: int):
        if self.page is None:
            return
        self._idx = (self._idx + step) % len(self._slides)
        self._switcher.content = self._slides[self._idx]
        self._counter.value = self._label()
        try:
            self.update()
        except Exception:
            # Page/session closed between the check and the update.
            pass
