"""Settings screen: progress backup/restore/reset and feature toggles."""

import flet as ft

from components.paper import PAPER_SHADOW, destructive_button, ink_button, outline_button
from components.theme import (
    BODY_FONT, CARD_BG, CARD_BORDER, DISPLAY_FONT, INK, INK_SOFT, META_FONT,
)

from repositories.errors import AppError
from views.errors_ui import show_error, show_info

_CARD_BG = CARD_BG
_BORDER = ft.border.all(1, CARD_BORDER)


def _section(title: str, subtitle: str, controls: list[ft.Control]) -> ft.Control:
    return ft.Container(
        bgcolor=_CARD_BG,
        border=_BORDER,
        border_radius=0,
        padding=20,
        shadow=PAPER_SHADOW,
        content=ft.Column(
            [
                ft.Text(title.upper(), size=16, font_family=DISPLAY_FONT,
                        weight=ft.FontWeight.W_700, color=INK),
                ft.Text(subtitle, size=12, font_family=META_FONT, color=INK_SOFT),
                *controls,
            ],
            spacing=12,
        ),
    )


def build_settings(page: ft.Page, ctx, nav) -> ft.Control:
    # ---- file pickers (export needs save_file, import needs pick_files) ----
    pending: dict = {}

    def on_save_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return  # cancelled
        try:
            ctx.backup.export_progress(e.path)
        except AppError as exc:
            show_error(page, str(exc))
            return
        show_info(page, f"Progress backed up to {e.path}")

    def on_pick_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        path = e.files[0].path
        if not path:
            show_error(page, "Import is only available in the desktop app.")
            return
        try:
            warnings = ctx.backup.import_progress(path)
        except (AppError, ValueError) as exc:
            show_error(page, str(exc))
            return
        for w in warnings[:3]:
            show_info(page, w)
        show_info(page, "Progress imported.")
        nav.go_settings()

    save_picker = ft.FilePicker(on_result=on_save_result)
    open_picker = ft.FilePicker(on_result=on_pick_result)
    page.overlay[:] = [c for c in page.overlay if not isinstance(c, ft.FilePicker)]
    page.overlay.extend([save_picker, open_picker])

    def export_progress(e):
        save_picker.save_file(
            dialog_title="Save progress backup",
            file_name="album-progress-backup.json",
            allowed_extensions=["json"],
        )

    def import_progress(e):
        open_picker.pick_files(
            dialog_title="Choose a progress backup",
            allow_multiple=False,
            allowed_extensions=["json"],
        )

    def reset_progress(e):
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=CARD_BG,
            title=ft.Text("RESET ALL PROGRESS?", font_family=DISPLAY_FONT,
                          weight=ft.FontWeight.W_700, color=INK),
            content=ft.Text(
                "This permanently deletes your inventory, album placements, "
                "favorite character, recorded savings, vice points, and vice "
                "offerings. The catalog "
                "(collections and stickers) is not touched. Consider exporting "
                "a backup first.",
                size=14, font_family=BODY_FONT, color=INK,
            ),
        )

        def do_reset(ev):
            page.close(dialog)
            try:
                ctx.backup.reset_progress()
            except AppError as exc:
                show_error(page, str(exc))
                return
            show_info(page, "Progress reset. Fresh album, fresh start!")
            nav.go_settings()

        dialog.actions = [
            outline_button("CANCEL", lambda ev: page.close(dialog)),
            destructive_button("RESET EVERYTHING", do_reset,
                               icon=ft.Icons.DELETE_FOREVER),
        ]
        page.open(dialog)

    # ---- feature toggles -----------------------------------------------------

    def toggle_creator(e):
        ctx.settings.set_creator_enabled(e.control.value)
        nav.rebuild_rail()

    def toggle_spicy(e):
        ctx.settings.set_spicy_enabled(e.control.value)

    progress_section = _section(
        "Playthrough progress",
        "Your inventory, album placements, favorite, savings, and Vice Shop.",
        [
            ft.Row(
                [
                    ink_button("EXPORT BACKUP…", export_progress,
                               icon=ft.Icons.UPLOAD),
                    outline_button("IMPORT BACKUP…", import_progress,
                                   icon=ft.Icons.DOWNLOAD),
                    outline_button("RESET PROGRESS…", reset_progress,
                                   icon=ft.Icons.DELETE_FOREVER,
                                   color="#a8563a"),
                ],
                wrap=True,
                spacing=12,
            ),
        ],
    )

    features_section = _section(
        "Features",
        "Optional parts of the app.",
        [
            ft.Switch(
                label="Creator screen",
                value=ctx.settings.state.creator_enabled,
                on_change=toggle_creator,
                tooltip="Show the collection-building screen in the navigation",
            ),
            ft.Switch(
                label="🌶️",
                value=ctx.settings.state.spicy_enabled,
                on_change=toggle_spicy,
            ),
        ],
    )

    return ft.Column(
        [
            ft.Text("SETTINGS", size=30, font_family=DISPLAY_FONT,
                    weight=ft.FontWeight.W_900, color=INK),
            progress_section,
            features_section,
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
