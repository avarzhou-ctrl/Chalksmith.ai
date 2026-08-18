from hashlib import sha1
from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide
from backend.app.lessons.formats.slides.sanitizer import (
    MAX_HTML_LENGTH,
    resolve_scope,
    sanitize_slide_html,
    visible_text,
)

_MATH_DELIMITERS = ("$", "\\(", "\\[")


class CustomHtmlBlock(StrictSpecModel):
    type: Literal["custom-html"]
    description: str = Field(min_length=1, max_length=120)
    html: str = Field(min_length=1, max_length=MAX_HTML_LENGTH)

    @model_validator(mode="after")
    def sanitize(self) -> "CustomHtmlBlock":
        self.html = sanitize_slide_html(self.html)
        return self


def custom_html_visible_length(block: CustomHtmlBlock) -> int:
    return len(block.description) + len(visible_text(block.html))


def custom_html_uses_math(block: CustomHtmlBlock) -> bool:
    return any(delimiter in block.html for delimiter in _MATH_DELIMITERS)


def render_custom_html(block: CustomHtmlBlock) -> str:
    # The scope class isolates author CSS and element ids from every other block.
    scope = f"csx-{sha1(block.html.encode('utf-8')).hexdigest()[:10]}"
    markup = resolve_scope(block.html, scope)
    return (
        f'<figure class="cs-card cs-custom {scope}" '
        f'aria-label="{escape(block.description)}">{markup}</figure>'
    )


CUSTOM_BLOCKS = (
    BlockDefinition(
        CustomHtmlBlock,
        BlockGuide(
            "custom-html",
            "visual",
            "a representation that no other Block can express",
            "author-written HTML and inline SVG inside a compiler-sized, style-scoped slot",
            "the teaching representation is not a listed relationship, figure, or dataset; "
            "prefer any semantic Block that fits and use this as the only body block",
            '{"type":"custom-html","description":"Complementary DNA strands","html":'
            '"<style>.row{display:flex;gap:.5rem;align-items:center}'
            '.base{padding:.25rem .75rem;border-radius:.4rem;font-weight:700}'
            '.a{background:#ef4444;color:#fff}.t{background:#22c55e;color:#000}</style>'
            '<div class=\\"row\\"><span class=\\"base a\\">A</span>'
            '<span class=\\"base t\\">T</span></div>"}',
            standalone=True,
        ),
        render_custom_html,
    ),
)
