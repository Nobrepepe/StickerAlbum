import flet as ft

from components.theme import PANEL_BG, PANEL_BORDER
from services.errors import ViceError
from views.errors_ui import show_error, show_info


def build_vice_shop(page: ft.Page, ctx, nav) -> ft.Control:
    def offering_dialog(offering=None):
        name = ft.TextField(label="Name", value=offering.name if offering else "")
        description = ft.TextField(
            label="Description", multiline=True, min_lines=2,
            value=offering.description if offering else "",
        )
        price = ft.TextField(
            label="Price (vice points)", keyboard_type=ft.KeyboardType.NUMBER,
            value=str(offering.price) if offering else "",
        )
        quantity = ft.TextField(
            label="Quantity offered", keyboard_type=ft.KeyboardType.NUMBER,
            value=str(offering.quantity) if offering else "1",
        )
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Edit vice" if offering else "Add a vice"),
            content=ft.Column(
                [name, description, price, quantity],
                width=420, tight=True, spacing=12,
            ),
        )

        def save(e):
            try:
                parsed_price = int(price.value)
                parsed_quantity = int(quantity.value)
                if offering:
                    ctx.vice.update_offering(
                        offering.id, name.value, description.value,
                        parsed_price, parsed_quantity,
                    )
                else:
                    ctx.vice.add_offering(
                        name.value, description.value, parsed_price, parsed_quantity
                    )
            except (ValueError, ViceError) as exc:
                show_error(page, str(exc) if isinstance(exc, ViceError)
                           else "Price and quantity must be whole numbers.")
                return
            page.close(dialog)
            nav.go_vice_shop()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Save", on_click=save),
        ]
        page.open(dialog)

    def remove(offering):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Remove this vice?"),
            content=ft.Text(
                f"{offering.name} will be removed from the shop. "
                "Previously claimed quantities are not restored."
            ),
        )

        def confirm(e):
            try:
                ctx.vice.remove_offering(offering.id)
            except ViceError as exc:
                show_error(page, str(exc))
                return
            page.close(dialog)
            nav.go_vice_shop()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton(
                "Remove", icon=ft.Icons.DELETE,
                style=ft.ButtonStyle(bgcolor="#b71c1c", color=ft.Colors.WHITE),
                on_click=confirm,
            ),
        ]
        page.open(dialog)

    def claim(offering):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Claim {offering.name}?"),
            content=ft.Text(
                f"This costs {offering.price} vice points. Treat yourself, "
                "then mark one quantity as claimed."
            ),
        )

        def confirm(e):
            try:
                ctx.vice.claim(offering.id)
            except ViceError as exc:
                page.close(dialog)
                show_error(page, str(exc))
                return
            page.close(dialog)
            show_info(page, f"{offering.name} claimed. Enjoy it guilt-free.")
            nav.go_vice_shop()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Claim", icon=ft.Icons.CHECK, on_click=confirm),
        ]
        page.open(dialog)

    cards: list[ft.Control] = []
    for offering in ctx.vice.list_offerings():
        sold_out = offering.quantity < 1
        cards.append(ft.Container(
            width=340,
            bgcolor=PANEL_BG,
            border=ft.border.all(1, PANEL_BORDER),
            border_radius=14,
            padding=18,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(offering.name, size=17, weight=ft.FontWeight.BOLD,
                                    expand=True),
                            ft.IconButton(ft.Icons.EDIT, tooltip="Edit",
                                          on_click=lambda e, o=offering: offering_dialog(o)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Remove",
                                          on_click=lambda e, o=offering: remove(o)),
                        ],
                        spacing=4,
                    ),
                    ft.Text(offering.description or "A well-earned indulgence.",
                            size=12, color=ft.Colors.GREY_400),
                    ft.Row(
                        [
                            ft.Text(f"{offering.price} points", size=16,
                                    weight=ft.FontWeight.BOLD, color="#ef5350"),
                            ft.Text(f"{offering.quantity} available", size=12,
                                    color=ft.Colors.GREY_400),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.FilledButton(
                        "Sold out" if sold_out else "Claim",
                        icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                        disabled=sold_out or ctx.vice.points < offering.price,
                        on_click=lambda e, o=offering: claim(o),
                    ),
                ],
                spacing=12,
            ),
        ))

    content: ft.Control
    if cards:
        content = ft.Row(cards, wrap=True, spacing=14, run_spacing=14)
    else:
        content = ft.Container(
            padding=40,
            alignment=ft.alignment.center,
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.LOCAL_BAR_OUTLINED, size=48,
                            color=ft.Colors.GREY_600),
                    ft.Text("No vices on offer yet", size=17,
                            weight=ft.FontWeight.BOLD),
                    ft.Text("Add an indulgence worth working toward.",
                            color=ft.Colors.GREY_400),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
        )

    return ft.Column(
        [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text("Vice Shop", size=26, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "Turn chosen spare stickers into permission to indulge.",
                                size=13, color=ft.Colors.GREY_400,
                            ),
                        ],
                        expand=True, spacing=3,
                    ),
                    ft.Container(
                        bgcolor="#49272d", border_radius=12, padding=14,
                        content=ft.Text(
                            f"{ctx.vice.points} vice points",
                            size=18, weight=ft.FontWeight.BOLD, color="#ef9a9a",
                        ),
                    ),
                    ft.FilledButton(
                        "Add vice", icon=ft.Icons.ADD,
                        on_click=lambda e: offering_dialog(),
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            content,
        ],
        spacing=18,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
