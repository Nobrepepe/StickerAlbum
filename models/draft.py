"""Mutable draft entities edited in the Creator screen.

A draft collection always carries the full 10x10 skeleton; completeness is
"every character and sticker has a name". Drafts stay out of the published
catalog until published.
"""

from dataclasses import dataclass, field


@dataclass
class DraftSticker:
    position: int  # 1-10 within the character; fixes number and rarity
    name: str = ""
    flavor_text: str = ""
    image: str | None = None


@dataclass
class DraftCharacter:
    index: int  # 1-10 within the collection
    name: str = ""
    description: str = ""
    portrait_image: str | None = None
    stickers: list[DraftSticker] = field(default_factory=list)


@dataclass
class DraftCollection:
    id: str  # the unique three-letter code
    name: str
    description: str = ""
    theme_color: str | None = None
    cover_image: str | None = None
    characters: list[DraftCharacter] = field(default_factory=list)


def new_draft_skeleton(
    code: str, name: str, description: str = "", theme_color: str | None = None
) -> DraftCollection:
    return DraftCollection(
        id=code,
        name=name,
        description=description,
        theme_color=theme_color,
        characters=[
            DraftCharacter(index=i, stickers=[DraftSticker(position=p) for p in range(1, 11)])
            for i in range(1, 11)
        ],
    )
