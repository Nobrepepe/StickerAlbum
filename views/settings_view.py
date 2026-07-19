"""Settings screen: progress backup/restore/reset and feature toggles."""

import flet as ft

from components.theme import PANEL_BG, PANEL_BORDER

from repositories.errors import AppError
from views.errors_ui import show_error, show_info

_CARD_BG = PANEL_BG
_BORDER = ft.border.all(1, PANEL_BORDER)


def _section(title: str, subtitle: str, controls: list[ft.Control]) -> ft.Control:
    return ft.Container(
        bgcolor=_CARD_BG,
        border=_BORDER,
        border_radius=14,
        padding=20,
        content=ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD),
                ft.Text(subtitle, size=12, color=ft.Colors.GREY_400),
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
            title=ft.Text("Reset all progress?"),
            content=ft.Text(
                "This permanently deletes your inventory, album placements, "
                "favorite character, and recorded savings. The catalog "
                "(collections and stickers) is not touched. Consider exporting "
                "a backup first.",
                size=14,
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
            ft.TextButton("Cancel", on_click=lambda ev: page.close(dialog)),
            ft.FilledButton(
                "Reset everything",
                icon=ft.Icons.DELETE_FOREVER,
                style=ft.ButtonStyle(bgcolor="#b71c1c", color=ft.Colors.WHITE),
                on_click=do_reset,
            ),
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
        "Your inventory, album placements, favorite character, and savings.",
        [
            ft.Row(
                [
                    ft.FilledTonalButton("Export backup…", icon=ft.Icons.UPLOAD,
                                         on_click=export_progress),
                    ft.FilledTonalButton("Import backup…", icon=ft.Icons.DOWNLOAD,
                                         on_click=import_progress),
                    ft.OutlinedButton(
                        "Reset progress…", icon=ft.Icons.DELETE_FOREVER,
                        style=ft.ButtonStyle(color="#e57373"),
                        on_click=reset_progress,
                    ),
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
            ft.Text("Settings", size=26, weight=ft.FontWeight.BOLD),
            progress_section,
            features_section,
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
