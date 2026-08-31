from html import unescape
from typing import Annotated

from pydantic import Field

from backend.app.lessons.formats.slides.presentation.content import (
    EquationBlock,
    EquationItem,
    KeyPointBlock,
    ListBlock,
    ListItem,
    ProseBlock,
    TableBlock,
    render_equation,
    render_key_point,
    render_list,
    render_prose,
    render_table,
)
from backend.app.lessons.formats.slides.presentation.custom import (
    CustomHtmlBlock,
    custom_html_visible_length,
    render_custom_html,
)


SlideBlock = Annotated[
    ProseBlock
    | ListBlock
    | KeyPointBlock
    | TableBlock
    | EquationBlock
    | CustomHtmlBlock,
    Field(discriminator="type"),
]

_INVISIBLE_KEYS = frozenset({"type", "appearance", "presentation", "description"})


def render_block(block: SlideBlock) -> str:
    if isinstance(block, ProseBlock):
        return render_prose(block)
    if isinstance(block, ListBlock):
        return render_list(block)
    if isinstance(block, KeyPointBlock):
        return render_key_point(block)
    if isinstance(block, TableBlock):
        return render_table(block)
    if isinstance(block, EquationBlock):
        return render_equation(block)
    if isinstance(block, CustomHtmlBlock):
        return render_custom_html(block)
    raise TypeError(f"Unsupported slide block: {type(block).__name__}")


def block_visible_length(block: SlideBlock) -> int:
    if isinstance(block, CustomHtmlBlock):
        return custom_html_visible_length(block)
    return _visible_length(block.model_dump())


def _visible_length(value: object) -> int:
    if isinstance(value, str):
        return len(unescape(value))
    if isinstance(value, dict):
        return sum(
            _visible_length(item)
            for key, item in value.items()
            if key not in _INVISIBLE_KEYS
        )
    if isinstance(value, list):
        return sum(_visible_length(item) for item in value)
    return 0


__all__ = [
    "CustomHtmlBlock",
    "EquationBlock",
    "EquationItem",
    "KeyPointBlock",
    "ListBlock",
    "ListItem",
    "ProseBlock",
    "SlideBlock",
    "TableBlock",
    "block_visible_length",
    "render_block",
]
