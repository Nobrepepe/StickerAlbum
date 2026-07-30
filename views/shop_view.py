import logging

import flet as ft

from components.pack_card import pack_card
from components.paper import ink_button, outline_button, page_caption
from components.theme import BODY_FONT, CARD_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from models.money import format_money
from repositories.errors import AppError
from views.errors_ui import show_error

log = logging.getLogger(__name__)


def build_shop(page: ft.Page, ctx, nav) -> ft.Control:
    def confirm_and_open(pack):
        dialog = ft.AlertDialog(modal=True, bgcolor=CARD_BG)

        def cancel(e):
            page.close(dialog)  # nothing recorded, nothing opened

        def confirm(e):
            page.close(dialog)
            try:
                # Result is generated and committed here, before any reveal
                # animation, so closing the app mid-reveal loses nothing.
                result = ctx.pack_service.open_pack(pack.id)
            except AppError as exc:
                show_error(page, str(exc))
                return
            except Exception:
                log.exception("Unexpected failure opening pack %s", pack.id)
                show_error(page, "Something went wrong opening the pack. See the log for details.")
                return
            nav.refresh_masthead()
            nav.go_pack_result(result)

        dialog.title = ft.Text("CONFIRM YOUR DEPOSIT", font_family=DISPLAY_FONT,
                               weight=ft.FontWeight.W_700, color=INK)
        dialog.content = ft.Text(
            f"Confirm that you deposited {format_money(pack.price)} into your "
            "savings account. The app will record the deposit and open the pack.",
            size=14, font_family=BODY_FONT, color=INK,
        )
        dialog.actions = [
            outline_button("CANCEL", cancel),
            ink_button("CONFIRM DEPOSIT & OPEN", confirm, icon=ft.Icons.SAVINGS),
        ]
        dialog.actions_alignment = ft.MainAxisAlignment.END
        page.open(dialog)

    cards = []
    for pack in ctx.packs.list_all():
        try:
            collection = ctx.collections.get(pack.collection_id)
            name, theme = collection.name, collection.theme_color
        except AppError:
            name, theme = pack.collection_id, None
        cards.append(pack_card(
            pack, name, theme,
            on_open=lambda p=pack: confirm_and_open(p),
            spicy_enabled=ctx.settings.state.spicy_enabled,
        ))

    return ft.Column(
        [
            page_caption("every pack you open records a real deposit"),
            ft.Row(cards, wrap=True, spacing=20, run_spacing=20),
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
