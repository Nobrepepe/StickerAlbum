import flet as ft

from components.collection_card import collection_card
from components.paper import destructive_button, outline_button, page_caption
from components.theme import BODY_FONT, CARD_BG, DISPLAY_FONT, INK, INK_SOFT, META_FONT
from repositories.errors import AppError
from views.errors_ui import show_error, show_info


def build_collections(page: ft.Page, ctx, nav) -> ft.Control:
    def revert_to_draft(collection):
        stickers = ctx.stickers.list_by_collection(collection.id)
        copies = sum(
            ctx.state.total_owned(s.id) for s in stickers
        )
        placed = sum(1 for s in stickers if ctx.state.get_placement(s.id))
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=CARD_BG,
            title=ft.Text(f"REVERT {collection.name} TO A DRAFT?",
                          font_family=DISPLAY_FONT, weight=ft.FontWeight.W_700,
                          color=INK),
            content=ft.Text(
                f"'{collection.name}' ({collection.id}) leaves play and goes "
                "back to the Creator with everything still filled in — names, "
                "art, sounds — ready to edit and publish again.\n\n"
                "Because it is no longer in play, your progress for this "
                f"collection is erased: {copies} owned copies and {placed} "
                "applied stickers will be removed. If your favorite character "
                "is from this collection, it is cleared. Recorded savings are "
                "kept. Consider exporting a progress backup first.",
                size=14, font_family=BODY_FONT, color=INK,
            ),
        )

        def do_revert(e):
            page.close(dialog)
            try:
                ctx.creator.unpublish(collection.id)
            except AppError as exc:
                show_error(page, str(exc))
                return
            nav.reload_catalog()
            show_info(page, f"{collection.name} is a draft again — find it in the Creator.")
            nav.go_creator()

        dialog.actions = [
            outline_button("CANCEL", lambda e: page.close(dialog)),
            destructive_button(
                "Revert & erase progress",
                do_revert, icon=ft.Icons.EDIT_NOTE,
            ),
        ]
        page.open(dialog)

    creator_on = ctx.settings.state.creator_enabled
    cards = []
    for collection in ctx.collections.list_all():
        applied, total = ctx.album.collection_progress(collection.id)
        chars_done, chars_total = ctx.album.completed_characters(collection.id)
        cards.append(
            collection_card(
                collection, applied, total, chars_done, chars_total,
                on_open=lambda cid=collection.id: nav.go_album(cid),
                on_revert=(lambda c=collection: revert_to_draft(c)) if creator_on else None,
                on_edit=(lambda cid=collection.id: nav.go_live_edit(cid)) if creator_on else None,
            )
        )
    return ft.Column(
        [
            page_caption("three worlds · pick one to fill"),
            ft.Row(cards, wrap=True, spacing=20, run_spacing=20),
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        alignment=ft.MainAxisAlignment.START,
    )
