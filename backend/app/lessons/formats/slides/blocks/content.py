from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class StatementBlock(StrictSpecModel):
    type: Literal["statement"]
    text: str = Field(min_length=1, max_length=320)


class BulletsBlock(StrictSpecModel):
    type: Literal["bullets"]
    items: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_items(self) -> "BulletsBlock":
        if any(not item.strip() or len(item) > 120 for item in self.items):
            raise ValueError("bullet items must contain 1 to 120 characters")
        return self


class CalloutBlock(StrictSpecModel):
    type: Literal["callout"]
    label: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=240)


class StepsBlock(StrictSpecModel):
    type: Literal["steps"]
    items: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_items(self) -> "StepsBlock":
        if any(not item.strip() or len(item) > 140 for item in self.items):
            raise ValueError("step items must contain 1 to 140 characters")
        return self


def render_statement(block: StatementBlock) -> str:
    return (
        f'<article class="cs-card cs-statement"><p>{escape(block.text)}</p></article>'
    )


def render_bullets(block: BulletsBlock) -> str:
    items = "".join(f"<li>{escape(item)}</li>" for item in block.items)
    return f'<article class="cs-card cs-list"><ul>{items}</ul></article>'


def render_callout(block: CalloutBlock) -> str:
    return (
        '<aside class="cs-card cs-callout">'
        f'<p class="cs-card__label">{escape(block.label)}</p>'
        f"<p>{escape(block.text)}</p></aside>"
    )


def render_steps(block: StepsBlock) -> str:
    # Keep KaTeX-generated spans inside one grid cell instead of beside the step counter.
    items = "".join(
        f'<li><span class="cs-steps__content">{escape(item)}</span></li>'
        for item in block.items
    )
    return f'<article class="cs-card cs-steps"><ol>{items}</ol></article>'


CONTENT_BLOCKS = (
    BlockDefinition(
        StatementBlock,
        BlockGuide(
            "statement",
            "text",
            "one central idea",
            "a large, quiet statement card",
            "one sentence deserves the learner's full attention",
            '{"type":"statement","text":"Mass is conserved in a closed system."}',
        ),
        render_statement,
    ),
    BlockDefinition(
        BulletsBlock,
        BlockGuide(
            "bullets",
            "text",
            "a short set of related facts",
            "a conventional bulleted list card",
            "the items are parallel facts rather than a sequence",
            '{"type":"bullets","items":["Solid","Liquid","Gas"]}',
        ),
        render_bullets,
    ),
    BlockDefinition(
        CalloutBlock,
        BlockGuide(
            "callout",
            "text",
            "a definition, warning, or key takeaway",
            "an amber-accented card with a short label",
            "a concise idea needs emphasis",
            '{"type":"callout","label":"Remember","text":"Like charges repel."}',
        ),
        render_callout,
    ),
    BlockDefinition(
        StepsBlock,
        BlockGuide(
            "steps",
            "text",
            "a staged solution or procedure",
            "a vertical numbered list",
            "showing vertical reasoning, calculations, progressive algebra, or formula states; "
            "choose this instead of process when each item needs horizontal writing room",
            '{"type":"steps","items":["Substitute the values.","Multiply.","Add the unit."]}',
            orientation="vertical",
        ),
        render_steps,
    ),
)
