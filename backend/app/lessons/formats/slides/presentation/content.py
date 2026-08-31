from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel


Appearance = Literal["plain", "card", "soft", "accent"]


class ProseBlock(StrictSpecModel):
    type: Literal["prose"]
    paragraphs: list[str] = Field(min_length=1, max_length=4)
    presentation: Literal["body", "lead"] = "body"
    appearance: Appearance = "plain"

    @model_validator(mode="after")
    def validate_paragraphs(self) -> "ProseBlock":
        if any(not paragraph.strip() or len(paragraph) > 260 for paragraph in self.paragraphs):
            raise ValueError("prose paragraphs must contain 1 to 260 characters")
        return self


class ListItem(StrictSpecModel):
    summary: str = Field(min_length=1, max_length=100)
    explanation: str | None = Field(default=None, min_length=1, max_length=160)
    badge: str | None = Field(default=None, min_length=1, max_length=24)


class ListBlock(StrictSpecModel):
    type: Literal["list"]
    items: list[ListItem] = Field(min_length=2, max_length=6)
    presentation: Literal[
        "bullets",
        "numbered",
        "accent-rows",
        "timeline",
        "bands",
    ] = "bullets"
    appearance: Appearance = "card"


class KeyPointBlock(StrictSpecModel):
    type: Literal["key-point"]
    summary: str = Field(min_length=1, max_length=80)
    explanation: str = Field(min_length=1, max_length=240)
    badge: str | None = Field(default=None, min_length=1, max_length=24)
    presentation: Literal[
        "standard",
        "accent-bar",
        "callout",
        "spotlight",
        "tagged",
    ] = "standard"
    appearance: Appearance = "card"


class TableBlock(StrictSpecModel):
    type: Literal["table"]
    columns: list[str] = Field(min_length=2, max_length=4)
    rows: list[list[str]] = Field(min_length=1, max_length=5)
    appearance: Appearance = "card"

    @model_validator(mode="after")
    def validate_cells(self) -> "TableBlock":
        if any(not column.strip() or len(column) > 48 for column in self.columns):
            raise ValueError("table column headings must contain 1 to 48 characters")
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("every table row must match the number of columns")
        if any(not cell.strip() or len(cell) > 80 for row in self.rows for cell in row):
            raise ValueError("table cells must contain 1 to 80 characters")
        return self


class EquationItem(StrictSpecModel):
    latex: str = Field(min_length=1, max_length=180)
    explanation: str | None = Field(default=None, min_length=1, max_length=140)


class EquationBlock(StrictSpecModel):
    type: Literal["equation"]
    items: list[EquationItem] = Field(min_length=1, max_length=5)
    appearance: Appearance = "card"


def render_prose(block: ProseBlock) -> str:
    paragraphs = "".join(f"<p>{escape(paragraph)}</p>" for paragraph in block.paragraphs)
    return (
        f'<article class="cs-block cs-surface--{block.appearance} '
        f'cs-prose cs-prose--{block.presentation}">{paragraphs}</article>'
    )


def render_list(block: ListBlock) -> str:
    items = "".join(_render_list_item(item) for item in block.items)
    tag = "ul" if block.presentation == "bullets" else "ol"
    return (
        f'<article class="cs-block cs-surface--{block.appearance} '
        f'cs-list cs-list--{block.presentation}"><{tag}>{items}</{tag}></article>'
    )


def _render_list_item(item: ListItem) -> str:
    badge = f'<span class="cs-item__badge">{escape(item.badge)}</span>' if item.badge else ""
    explanation = (
        f'<span class="cs-item__explanation">{escape(item.explanation)}</span>'
        if item.explanation
        else ""
    )
    return (
        f"<li>{badge}<span class=\"cs-item__content\">"
        f'<strong class="cs-item__summary">{escape(item.summary)}</strong>'
        f"{explanation}</span></li>"
    )


def render_key_point(block: KeyPointBlock) -> str:
    badge = f'<span class="cs-key-point__badge">{escape(block.badge)}</span>' if block.badge else ""
    return (
        f'<article class="cs-block cs-surface--{block.appearance} '
        f'cs-key-point cs-key-point--{block.presentation}">{badge}'
        f"<strong>{escape(block.summary)}</strong>"
        f"<p>{escape(block.explanation)}</p></article>"
    )


def render_table(block: TableBlock) -> str:
    headings = "".join(f'<th scope="col">{escape(column)}</th>' for column in block.columns)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>"
        for row in block.rows
    )
    return (
        f'<figure class="cs-block cs-surface--{block.appearance} cs-table">'
        '<div class="cs-table__viewport">'
        f"<table><thead><tr>{headings}</tr></thead><tbody>{rows}</tbody></table>"
        "</div></figure>"
    )


def render_equation(block: EquationBlock) -> str:
    items = "".join(_render_equation_item(item) for item in block.items)
    return (
        f'<figure class="cs-block cs-surface--{block.appearance} cs-equation">'
        f'<ol class="cs-equation__items">{items}</ol></figure>'
    )


def _render_equation_item(item: EquationItem) -> str:
    explanation = f"<p>{escape(item.explanation)}</p>" if item.explanation else ""
    return (
        '<li class="cs-equation__item">'
        f'{explanation}<div class="cs-equation__formula">$${escape(item.latex)}$$</div>'
        "</li>"
    )
