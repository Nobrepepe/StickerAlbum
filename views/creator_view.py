"""Creator screen: build new collections in-app.

Drafts (stored in data/drafts.json) are only visible here. A draft becomes a
published collection — visible in Collections/Home/Shop pools — only when it
is complete: a name, 10 named characters, 10 named stickers each. Rarities
and sticker numbers follow the fixed 3/3/2/1/1 slot pattern automatically.
"""

import flet as ft

from components.empty_state import empty_state
from components.assets import character_tile_image, resolve_image
from components.placeholders import cover_band, sticker_art
from components.theme import PANEL_BG, PANEL_BORDER
from components.rarity_chip import rarity_chip
from models.catalog import Sticker
from models.draft import SLOTS_PER_CHARACTER, DraftCollection
from models.rarity import RARITY_COLORS, RARITY_LABELS, slot_rarity
from repositories.errors import AppError
from services.creator_service import character_id, sticker_id, sticker_number
from views.errors_ui import show_error, show_info

_TOTAL_STICKERS = 10 * SLOTS_PER_CHARACTER  # 150 per collection
_SPICY_COLOR = "#ff7043"

_THEME_COLORS = {
    "Purple": "#7c4dff",
    "Cyan": "#00bcd4",
    "Green": "#4caf50",
    "Amber": "#ffb300",
    "Red": "#f44336",
    "Pink": "#ec407a",
    "Indigo": "#5c6bc0",
    "Teal": "#26a69a",
}

_CARD_BG = PANEL_BG
_BORDER = ft.border.all(1, PANEL_BORDER)

# Sticker slots share the artwork's 3:4 ratio, so imported art fills the tile
# without being cropped.
_TILE_W, _TILE_H = 147.0, 196.0
_TILE_RADIUS = 12


def _slot_border_color(rarity: str) -> str:
    """A slot's rarity is carried by its border color alone. Spicy keeps the
    warmer orange-red used for spicy chrome elsewhere in the Creator."""
    if rarity == "spicy":
        return _SPICY_COLOR
    return RARITY_COLORS.get(rarity, "#9e9e9e")


def _art_scrim() -> ft.LinearGradient:
    """Darkens the top and bottom of a slot so the number, icons, and name
    stay readable over imported artwork, leaving the middle mostly clear."""
    return ft.LinearGradient(
        begin=ft.alignment.top_center,
        end=ft.alignment.bottom_center,
        colors=[ft.Colors.with_opacity(o, "#0d0d13")
                for o in (0.85, 0.3, 0.55, 0.9)],
        stops=[0.0, 0.32, 0.62, 1.0],
    )


# Keeps a slot's name crisp over the brightest artwork without dimming it.
_NAME_ON_ART = ft.TextStyle(
    shadow=ft.BoxShadow(blur_radius=4, color=ft.Colors.with_opacity(0.9, "#000000")),
)


def _draft_sticker(draft: DraftCollection, char_index: int, position: int) -> Sticker:
    s = draft.characters[char_index - 1].stickers[position - 1]
    return Sticker(
        id=sticker_id(draft.id, char_index, position),
        collection_id=draft.id,
        character_id=character_id(draft.id, char_index),
        number=sticker_number(char_index, position),
        name=s.name or f"Sticker #{position}",
        rarity=slot_rarity(position),
        image=s.image,
        flavor_text=s.flavor_text,
        spicy=s.spicy,
    )


def build_creator(page: ft.Page, ctx, nav,
                  live_collection_id: str | None = None) -> ft.Control:
    """The Creator. With live_collection_id set, the editor opens in
    hot-edit mode: it edits the PUBLISHED collection in place (names,
    images, sounds, flavor) — progress is kept, structure is fixed."""
    creator = ctx.creator
    root = ft.Container(expand=True)
    state: dict = {"draft": None, "char": 1, "live": False}
    pending: dict = {}

    def persist_draft() -> bool:
        """Commit the working object: drafts go to drafts.json, live
        collections go straight back onto the catalog."""
        if state["live"]:
            try:
                creator.apply_live_edits(state["draft"])
            except AppError as exc:
                show_error(page, str(exc))
                return False
        else:
            creator.save(state["draft"])
        return True

    # One picker for every upload; replace any picker left by a previous
    # build so page.overlay doesn't accumulate them.
    def on_pick_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return  # user cancelled the native dialog
        path = e.files[0].path
        if not path:
            show_error(page, "Image import is only available in the desktop app.")
            return
        try:
            if pending["kind"] == "sound":
                rel = creator.attach_sound(
                    state["draft"], path,
                    pending["char_index"], pending["position"],
                    persist=not state["live"],
                )
            else:
                rel = creator.attach_image(
                    state["draft"], pending["kind"], path,
                    pending.get("char_index"), pending.get("position"),
                    persist=not state["live"],
                )
            if state["live"]:
                creator.apply_live_edits(state["draft"])
        except AppError as exc:
            show_error(page, str(exc))
            return
        after = pending.get("after")
        if after:
            after(rel)
        else:
            render()
        show_info(page, "Sound imported." if pending["kind"] == "sound"
                  else "Image imported.")

    picker = ft.FilePicker(on_result=on_pick_result)
    page.overlay[:] = [c for c in page.overlay if not isinstance(c, ft.FilePicker)]
    page.overlay.append(picker)

    def pick_image(kind: str, char_index: int | None = None,
                   position: int | None = None, after=None):
        pending.clear()
        pending.update(kind=kind, char_index=char_index, position=position, after=after)
        if kind == "sound":
            picker.pick_files(
                dialog_title="Choose a sound",
                allow_multiple=False,
                allowed_extensions=["mp3", "wav", "ogg", "m4a"],
            )
        else:
            picker.pick_files(
                dialog_title="Choose an image",
                allow_multiple=False,
                allowed_extensions=["png", "jpg", "jpeg", "webp"],
            )

    # ---- publishing -------------------------------------------------------

    def publish(draft: DraftCollection):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Publish {draft.name}?"),
            content=ft.Text(
                f"'{draft.name}' ({draft.id}) will appear in Collections and its "
                "150 stickers (100 regular + 50 spicy) become collectible. Add "
                "packs for it in data/packs.json to make them obtainable. "
                "Publishing can't be undone from the app.",
                size=14,
            ),
        )

        def do_publish(e):
            page.close(dialog)
            try:
                creator.publish(draft.id)
            except AppError as exc:
                show_error(page, str(exc))
                return
            state["draft"] = None
            nav.reload_catalog()
            show_info(page, f"{draft.name} published! It's now in Collections.")
            nav.go_collections()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Publish", icon=ft.Icons.ROCKET_LAUNCH, on_click=do_publish),
        ]
        page.open(dialog)

    # ---- new collection / edit info dialog ---------------------------------

    def collection_dialog(draft: DraftCollection | None):
        is_new = draft is None
        code_field = ft.TextField(
            label="Three-letter code",
            value="" if is_new else draft.id,
            max_length=3,
            width=180,
            capitalization=ft.TextCapitalization.CHARACTERS,
            input_filter=ft.InputFilter(regex_string=r"[A-Za-z]"),
            disabled=not is_new,
            helper_text="Unique, e.g. HGT" if is_new else "Fixed after creation",
        )
        name_field = ft.TextField(label="Collection name",
                                  value="" if is_new else draft.name)
        desc_field = ft.TextField(label="Description", multiline=True, min_lines=2,
                                  max_lines=3, value="" if is_new else draft.description)
        color_field = ft.Dropdown(
            label="Theme color",
            options=[ft.dropdown.Option(key=hexv, text=name)
                     for name, hexv in _THEME_COLORS.items()],
            value=(None if is_new else draft.theme_color) or _THEME_COLORS["Purple"],
            width=220,
        )
        error_text = ft.Text("", color="#e57373", size=12, visible=False)
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("New collection" if is_new else "Edit collection"),
            content=ft.Column(
                [code_field, name_field, desc_field, color_field, error_text],
                tight=True, spacing=14, width=380,
            ),
        )

        def fail(msg: str):
            error_text.value = msg
            error_text.visible = True
            page.update()

        def save(e):
            name = name_field.value.strip()
            if not name:
                fail("The collection needs a name.")
                return
            if is_new:
                try:
                    new_draft = creator.create_collection(
                        code_field.value, name, desc_field.value, color_field.value
                    )
                except AppError as exc:
                    fail(str(exc))
                    return
                page.close(dialog)
                open_editor(new_draft)
            else:
                draft.name = name
                draft.description = desc_field.value.strip()
                draft.theme_color = color_field.value
                if not persist_draft():
                    return
                page.close(dialog)
                render()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Create draft" if is_new else "Save", on_click=save),
        ]
        page.open(dialog)

    # ---- draft list ---------------------------------------------------------

    def delete_draft(draft: DraftCollection):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Delete draft {draft.name or draft.id}?"),
            content=ft.Text(
                "The draft and its progress are removed. Imported images stay "
                "in the assets folder.", size=14,
            ),
        )

        def do_delete(e):
            creator.delete_draft(draft.id)
            page.close(dialog)
            render()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Delete draft", icon=ft.Icons.DELETE_OUTLINE,
                            on_click=do_delete),
        ]
        page.open(dialog)

    def draft_card(draft: DraftCollection) -> ft.Control:
        chars_done, chars_total = creator.collection_progress(draft)
        stickers_done = sum(creator.character_progress(c)[0] for c in draft.characters)
        complete = creator.collection_complete(draft)
        total = _TOTAL_STICKERS
        return ft.Container(
            width=330, bgcolor=_CARD_BG, border_radius=14, border=_BORDER,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Column([
                cover_band(draft.cover_image, draft.theme_color, height=70),
                ft.Container(padding=16, content=ft.Column([
                    ft.Row([
                        ft.Text(draft.name or "(unnamed)", size=17,
                                weight=ft.FontWeight.BOLD, expand=True,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Container(
                            content=ft.Text(draft.id, size=11, weight=ft.FontWeight.BOLD),
                            border=ft.border.all(1, "#4a4a5a"), border_radius=8,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                        ),
                    ]),
                    ft.Text(
                        f"{chars_done} / {chars_total} characters · "
                        f"{stickers_done} / {total} stickers named",
                        size=12, color=ft.Colors.GREY_400,
                    ),
                    ft.ProgressBar(
                        value=stickers_done / total,
                        color=draft.theme_color or "#7c4dff",
                        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                    ),
                    ft.Row([
                        ft.FilledTonalButton("Continue", icon=ft.Icons.EDIT,
                                             on_click=lambda e, d=draft: open_editor(d)),
                        ft.FilledButton(
                            "Publish", icon=ft.Icons.ROCKET_LAUNCH, disabled=not complete,
                            tooltip=None if complete else
                            "Every character needs a name and 15 named stickers "
                            "(10 regular + 5 spicy)",
                            on_click=lambda e, d=draft: publish(d),
                        ),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, tooltip="Delete draft",
                                      on_click=lambda e, d=draft: delete_draft(d)),
                    ], spacing=8),
                ], spacing=10)),
            ], spacing=0),
        )

    # ---- catalog backup / restore / reset ----------------------------------

    def on_catalog_save_result(e: ft.FilePickerResultEvent):
        if not e.path:
            return
        try:
            ctx.backup.export_catalog(e.path)
        except AppError as exc:
            show_error(page, str(exc))
            return
        show_info(page, f"Catalog backed up to {e.path}")

    def on_catalog_open_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        path = e.files[0].path
        if not path:
            show_error(page, "Restore is only available in the desktop app.")
            return
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Restore catalog from backup?"),
            content=ft.Text(
                "This replaces ALL current collections, characters, stickers, "
                "and drafts with the backup's contents.", size=14,
            ),
        )

        def do_restore(ev):
            page.close(dialog)
            try:
                ctx.backup.import_catalog(path)
            except AppError as exc:
                show_error(page, str(exc))
                return
            nav.reload_catalog()
            show_info(page, "Catalog restored.")
            nav.go_creator()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda ev: page.close(dialog)),
            ft.FilledButton("Restore", icon=ft.Icons.RESTORE, on_click=do_restore),
        ]
        page.open(dialog)

    catalog_save_picker = ft.FilePicker(on_result=on_catalog_save_result)
    catalog_open_picker = ft.FilePicker(on_result=on_catalog_open_result)
    page.overlay.extend([catalog_save_picker, catalog_open_picker])

    def backup_catalog(e):
        catalog_save_picker.save_file(
            dialog_title="Save catalog backup",
            file_name="album-catalog-backup.json",
            allowed_extensions=["json"],
        )

    def restore_catalog(e):
        catalog_open_picker.pick_files(
            dialog_title="Choose a catalog backup",
            allow_multiple=False,
            allowed_extensions=["json"],
        )

    def reset_catalog(e):
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Delete ALL collections?"),
            content=ft.Text(
                "Every collection, character, and sticker is removed — drafts "
                "too. Your playthrough progress file is kept but will point at "
                "stickers that no longer exist. Packs in data/packs.json are "
                "not touched; remove entries for deleted collections by hand. "
                "Consider a catalog backup first.",
                size=14,
            ),
        )

        def do_reset(ev):
            page.close(dialog)
            try:
                ctx.backup.reset_catalog()
            except AppError as exc:
                show_error(page, str(exc))
                return
            nav.reload_catalog()
            show_info(page, "Catalog reset: all collections deleted.")
            nav.go_creator()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda ev: page.close(dialog)),
            ft.FilledButton(
                "Delete everything",
                icon=ft.Icons.DELETE_FOREVER,
                style=ft.ButtonStyle(bgcolor="#b71c1c", color=ft.Colors.WHITE),
                on_click=do_reset,
            ),
        ]
        page.open(dialog)

    def render_list():
        drafts = ctx.drafts.list_all()
        body: ft.Control = (
            ft.Row([draft_card(d) for d in drafts], wrap=True, spacing=16, run_spacing=16)
            if drafts else
            empty_state(ft.Icons.DESIGN_SERVICES,
                        "No drafts yet",
                        "Create a collection and fill in its 10 characters at your pace.")
        )
        root.content = ft.Column([
            ft.Row([
                ft.Text("Creator", size=26, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                ft.FilledButton("New collection", icon=ft.Icons.ADD,
                                on_click=lambda e: collection_dialog(None)),
            ]),
            ft.Text(
                "Drafts live only here until they're complete: 10 characters, "
                "each with 15 named stickers — 10 regular (3 common, "
                "3 uncommon, 2 rare, 1 epic, 1 legendary) plus 5 special "
                "spicy stickers.",
                size=13, color=ft.Colors.GREY_400,
            ),
            body,
            ft.Container(
                padding=ft.padding.only(top=8),
                content=ft.Column([
                    ft.Text("Catalog data", size=14, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_300),
                    ft.Text(
                        "The authored collections, characters, and stickers "
                        "(not your playthrough progress).",
                        size=12, color=ft.Colors.GREY_500,
                    ),
                    ft.Row([
                        ft.FilledTonalButton("Backup catalog…", icon=ft.Icons.UPLOAD,
                                             on_click=backup_catalog),
                        ft.FilledTonalButton("Restore backup…", icon=ft.Icons.DOWNLOAD,
                                             on_click=restore_catalog),
                        ft.OutlinedButton(
                            "Reset catalog…", icon=ft.Icons.DELETE_FOREVER,
                            style=ft.ButtonStyle(color="#e57373"),
                            on_click=reset_catalog,
                        ),
                    ], wrap=True, spacing=12),
                ], spacing=8),
            ),
        ], spacing=18, scroll=ft.ScrollMode.AUTO, expand=True,
           alignment=ft.MainAxisAlignment.START)
        page.update()

    # ---- sticker dialog ------------------------------------------------------

    def sticker_dialog(draft: DraftCollection, char_index: int, position: int):
        s = draft.characters[char_index - 1].stickers[position - 1]
        rarity = slot_rarity(position)
        name_field = ft.TextField(label="Sticker name", value=s.name)
        flavor_field = ft.TextField(label="Flavor text", value=s.flavor_text,
                                    multiline=True, min_lines=2, max_lines=3)
        preview = ft.Container(
            content=sticker_art(_draft_sticker(draft, char_index, position), 200, 200),
            alignment=ft.alignment.center,
        )
        spicy_marker = (
            [ft.Container(
                content=ft.Text("SPICY 🌶️", size=10, weight=ft.FontWeight.BOLD,
                                color="#101014"),
                bgcolor=_SPICY_COLOR, border_radius=8,
                padding=ft.padding.symmetric(horizontal=8, vertical=2),
            )] if s.spicy else []
        )
        sound_label = ft.Text(
            f"🔊 {s.sound.split('/')[-1]}" if s.sound else "",
            size=11, color=ft.Colors.GREY_500, visible=bool(s.sound),
            text_align=ft.TextAlign.CENTER,
        )
        # Imports commit as soon as they're picked, so a cancelled dialog
        # still has to refresh the grid when art or a sound was attached.
        touched = {"assets": False, "saved": False}
        dialog = ft.AlertDialog(
            # Not modal: tapping outside dismisses and drops the text edits,
            # exactly like Cancel.
            modal=False,
            on_dismiss=lambda e: (
                render() if touched["assets"] and not touched["saved"] else None
            ),
            title=ft.Text(f"Sticker #{sticker_number(char_index, position):02d}"
                          + (" 🌶️" if s.spicy else "")),
            content=ft.Column([
                preview,
                ft.Row([*spicy_marker, rarity_chip(rarity),
                        ft.Text(sticker_id(draft.id, char_index, position),
                                size=12, color=ft.Colors.GREY_500)],
                       alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                name_field,
                flavor_field,
                ft.Row([
                    ft.OutlinedButton(
                        "Image…", icon=ft.Icons.IMAGE,
                        on_click=lambda e: pick_image(
                            "sticker", char_index, position, after=refresh_preview),
                    ),
                    ft.OutlinedButton(
                        "Sound…", icon=ft.Icons.MUSIC_NOTE,
                        tooltip="Optional voice line for the flavor text",
                        on_click=lambda e: pick_image(
                            "sound", char_index, position, after=refresh_sound),
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                sound_label,
            ], tight=True, spacing=12, width=340),
        )

        def refresh_preview(rel: str):
            touched["assets"] = True
            preview.content = sticker_art(
                _draft_sticker(draft, char_index, position), 200, 200)
            page.update()

        def refresh_sound(rel: str):
            touched["assets"] = True
            sound_label.value = f"🔊 {rel.split('/')[-1]}"
            sound_label.visible = True
            page.update()

        def save(e):
            s.name = name_field.value.strip()
            s.flavor_text = flavor_field.value.strip()
            if not persist_draft():
                return  # live edit rejected (e.g. blank name); keep the dialog
            touched["saved"] = True  # the render below covers on_dismiss
            page.close(dialog)
            render()

        dialog.actions = [
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.FilledButton("Save", on_click=save),
        ]
        page.open(dialog)

    # ---- editor --------------------------------------------------------------

    def open_editor(draft: DraftCollection, char_index: int = 1):
        state["draft"] = draft
        state["char"] = char_index
        render()

    def render_editor():
        draft: DraftCollection = state["draft"]
        theme = draft.theme_color or "#7c4dff"
        ci = state["char"]
        character = draft.characters[ci - 1]

        sidebar = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True,
        alignment=ft.MainAxisAlignment.START)
        publish_button = ft.FilledButton("Publish", icon=ft.Icons.ROCKET_LAUNCH,
                                         on_click=lambda e: publish(draft))
        progress_text = ft.Text(size=13, color=ft.Colors.GREY_300)

        def sidebar_tile(i: int) -> ft.Control:
            c = draft.characters[i - 1]
            done, total = creator.character_progress(c)
            complete = creator.character_complete(c)
            selected = i == state["char"]
            tile_src = character_tile_image(character_id(draft.id, i))
            thumb = ft.Container(
                width=64, height=36, border_radius=6,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                image=ft.DecorationImage(src=tile_src, fit=ft.ImageFit.COVER)
                if tile_src else None,
                gradient=None if tile_src else ft.LinearGradient(
                    begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                    colors=[ft.Colors.with_opacity(0.6, theme), "#14141c"],
                ),
            )
            return ft.Container(
                bgcolor=ft.Colors.with_opacity(0.18, theme) if selected else None,
                border_radius=10,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                on_click=lambda e, i=i: switch_character(i),
                ink=True,
                content=ft.Row([
                    thumb,
                    ft.Column([
                        ft.Text(c.name or f"Character #{i}", size=13,
                                weight=ft.FontWeight.BOLD if selected else None,
                                color=None if c.name else ft.Colors.GREY_500,
                                max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(f"{done} / {total} stickers", size=11,
                                color=ft.Colors.GREY_400),
                    ], spacing=1, tight=True, expand=True),
                    ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="#81c784")
                    if complete else ft.Container(width=16),
                ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            )

        def refresh_sidebar():
            sidebar.controls = [sidebar_tile(i) for i in range(1, 11)]
            done, total = creator.collection_progress(draft)
            progress_text.value = f"{done} / {total} characters complete"
            complete = creator.collection_complete(draft)
            publish_button.disabled = not complete
            publish_button.tooltip = (
                None if complete
                else "Every character needs a name and 15 named stickers "
                     "(10 regular + 5 spicy)"
            )
            page.update()

        def switch_character(i: int):
            persist_draft()  # commit any pending text edits
            state["char"] = i
            render()

        def back_to_list(e):
            persist_draft()
            if state["live"]:
                # Leaving the hot editor: the rest of the app must see the
                # edited catalog.
                nav.reload_catalog()
                nav.go_collections()
                return
            state["draft"] = None
            render()

        # Text fields write to the draft as you type and persist on blur, so
        # typing doesn't rebuild the view (and steal focus) on every key.
        def bind(setter):
            def on_change(e):
                setter(e.control.value)
            return on_change

        def persist(e):
            persist_draft()
            refresh_sidebar()

        name_field = ft.TextField(
            label="Character name", value=character.name, width=320,
            on_change=bind(lambda v: setattr(character, "name", v)), on_blur=persist,
        )
        desc_field = ft.TextField(
            label="Character description", value=character.description, expand=True,
            on_change=bind(lambda v: setattr(character, "description", v)),
            on_blur=persist,
        )

        def sticker_tile(position: int) -> ft.Control:
            s = character.stickers[position - 1]
            rarity = slot_rarity(position)
            named = creator.sticker_complete(s)
            # Rarity reads from the border; unnamed slots keep the hue but
            # stay visibly unfinished (thinner, faded).
            color = _slot_border_color(rarity)
            art = resolve_image(s.image)

            indicators: list[ft.Control] = []
            if not art:
                # With art in the tile, the image icon is only worth showing
                # while it's still missing.
                indicators.append(ft.Icon(
                    ft.Icons.IMAGE_OUTLINED, size=14, color=ft.Colors.GREY_700,
                    tooltip="No image yet"))
            indicators.append(ft.Icon(
                ft.Icons.VOLUME_UP if s.sound else ft.Icons.VOLUME_OFF_OUTLINED,
                size=14, color="#81c784" if s.sound else ft.Colors.GREY_700,
                tooltip="Has voice line" if s.sound else "No voice line yet"))

            edge = 2 if named else 1
            # Art and scrim live one level in, clipped to the radius *inside*
            # the border: clipping the bordered container itself shaves the
            # border off at the rounded corners.
            face = ft.Container(
                border_radius=_TILE_RADIUS - edge,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                image=ft.DecorationImage(src=art, fit=ft.ImageFit.COVER,
                                         opacity=0.9) if art else None,
                content=ft.Container(
                    padding=10,
                    gradient=_art_scrim() if art else None,
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"#{sticker_number(ci, position):02d}", size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.GREY_300 if art
                                    else ft.Colors.GREY_400),
                            *([ft.Text("🌶️", size=12)] if s.spicy else []),
                            ft.Container(expand=True),
                            *indicators,
                        ], spacing=4),
                        ft.Text(s.name or "Unnamed", size=13,
                                color=None if named else ft.Colors.GREY_500,
                                max_lines=3, overflow=ft.TextOverflow.ELLIPSIS,
                                weight=ft.FontWeight.BOLD if named else None,
                                style=_NAME_ON_ART if art else None,
                                expand=True),
                    ], spacing=6),
                ),
            )
            return ft.Container(
                width=_TILE_W, height=_TILE_H,
                bgcolor=_CARD_BG, border_radius=_TILE_RADIUS,
                border=ft.border.all(edge, color if named
                                     else ft.Colors.with_opacity(0.4, color)),
                ink=True,
                on_click=lambda e, p=position: sticker_dialog(draft, ci, p),
                content=face,
                tooltip=f"{RARITY_LABELS.get(rarity, rarity)} — tap to edit",
            )

        live = state["live"]
        banner = (
            ft.Text("LIVE — edits apply to the published collection "
                    "immediately; your progress is kept",
                    size=11, color="#81c784")
            if live else
            ft.Text("DRAFT — visible only in the Creator until published",
                    size=11, color="#ffb300")
        )
        header_right = (
            ft.FilledTonalButton("Done", icon=ft.Icons.CHECK, on_click=back_to_list)
            if live else
            ft.Column([progress_text, publish_button], spacing=6,
                      horizontal_alignment=ft.CrossAxisAlignment.END, tight=True)
        )
        header = ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK,
                          tooltip="Back to collections" if live else "Back to drafts",
                          on_click=back_to_list),
            ft.Column([
                ft.Row([
                    ft.Text(draft.name, size=22, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Text(draft.id, size=11, weight=ft.FontWeight.BOLD),
                        border=ft.border.all(1, "#4a4a5a"), border_radius=8,
                        padding=ft.padding.symmetric(horizontal=8, vertical=2),
                    ),
                    ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_size=18,
                                  tooltip="Edit name, description, color",
                                  on_click=lambda e: collection_dialog(draft)),
                    ft.OutlinedButton("Cover image…", icon=ft.Icons.IMAGE,
                                      on_click=lambda e: pick_image("cover")),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                banner,
            ], spacing=2, tight=True, expand=True),
            header_right,
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

        panel_tile_src = character_tile_image(character_id(draft.id, ci))
        panel_thumb = ft.Container(
            width=128, height=72, border_radius=8,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            image=ft.DecorationImage(src=panel_tile_src, fit=ft.ImageFit.COVER)
            if panel_tile_src else None,
            gradient=None if panel_tile_src else ft.LinearGradient(
                begin=ft.alignment.top_left, end=ft.alignment.bottom_right,
                colors=[ft.Colors.with_opacity(0.6, theme), "#14141c"],
            ),
            tooltip="16:9 tile art (shown in album sidebars)",
        )
        character_panel = ft.Column([
            ft.Row([
                panel_thumb,
                ft.Column([
                    ft.Row([
                        name_field,
                        ft.OutlinedButton(
                            "Tile…", icon=ft.Icons.PANORAMA_WIDE_ANGLE,
                            tooltip="16:9 landscape banner (e.g. the eyes)",
                            on_click=lambda e: pick_image("tile", ci)),
                        ft.OutlinedButton(
                            "Card…", icon=ft.Icons.PORTRAIT,
                            tooltip="9:16 full-body card",
                            on_click=lambda e: pick_image("card", ci)),
                    ], spacing=10, run_spacing=8, wrap=True),
                    desc_field,
                ], spacing=10, tight=True, expand=True),
            ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
            ft.Text("Sticker slots — tap to name them and add art",
                    size=13, color=ft.Colors.GREY_400),
            ft.Column([
                ft.Row([sticker_tile(p) for p in range(1, 11)],
                       wrap=True, spacing=12, run_spacing=12),
                ft.Row([
                    ft.Text("🌶️", size=16),
                    ft.Text("Spicy stickers — hidden in the album unless "
                            "enabled in Settings" if live else
                            "Spicy stickers — required before publishing, "
                            "hidden in the album unless enabled in Settings",
                            size=12, weight=ft.FontWeight.BOLD, color=_SPICY_COLOR),
                ], spacing=8),
                ft.Row([sticker_tile(p) for p in range(11, SLOTS_PER_CHARACTER + 1)],
                       wrap=True, spacing=12, run_spacing=12),
            ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=14),
        ], spacing=14, expand=True)

        root.content = ft.Column([
            header,
            ft.Row([
                ft.Container(width=230, bgcolor="#2b2735", border_radius=12,
                             padding=8, content=sidebar),
                character_panel,
            ], spacing=16, expand=True, vertical_alignment=ft.CrossAxisAlignment.START),
        ], spacing=14, expand=True)
        refresh_sidebar()

    # ---- entry ---------------------------------------------------------------

    def render():
        if state["draft"] is None:
            render_list()
        else:
            render_editor()

    if live_collection_id is not None:
        try:
            state["draft"] = creator.load_live(live_collection_id)
            state["live"] = True
        except AppError as exc:
            show_error(page, str(exc))
    render()
    return root
