from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class BarChartItem(StrictSpecModel):
    label: str = Field(min_length=1, max_length=20)
    value: float = Field(ge=0, le=1000)


class BarChartBlock(StrictSpecModel):
    type: Literal["bar-chart"]
    items: list[BarChartItem] = Field(min_length=2, max_length=6)
    unit: str | None = Field(default=None, min_length=1, max_length=16)

    @model_validator(mode="after")
    def validate_bars(self) -> "BarChartBlock":
        if not any(item.value > 0 for item in self.items):
            raise ValueError("bar-chart requires at least one positive value")
        return self


class TimelineEvent(StrictSpecModel):
    label: str = Field(min_length=1, max_length=24)
    text: str = Field(min_length=1, max_length=72)


class TimelineBlock(StrictSpecModel):
    type: Literal["timeline"]
    events: list[TimelineEvent] = Field(min_length=2, max_length=5)


def render_bar_chart(block: BarChartBlock) -> str:
    maximum = max(item.value for item in block.items)
    bars = "".join(
        '<li><span class="cs-bar-chart__value">'
        f"{_format_number(item.value)}{f' {escape(block.unit)}' if block.unit else ''}</span>"
        '<span class="cs-bar-chart__track"><i '
        f'style="--cs-bar-size: {(item.value / maximum) * 100:.3f}%"></i></span>'
        f"<strong>{escape(item.label)}</strong></li>"
        for item in block.items
    )
    return f'<figure class="cs-card cs-bar-chart"><ol>{bars}</ol></figure>'


def render_timeline(block: TimelineBlock) -> str:
    events = "".join(
        f"<li><time>{escape(event.label)}</time><p>{escape(event.text)}</p></li>"
        for event in block.events
    )
    return f'<figure class="cs-card cs-timeline"><ol>{events}</ol></figure>'


def _format_number(value: float) -> str:
    return (
        str(int(value))
        if value.is_integer()
        else f"{value:.2f}".rstrip("0").rstrip(".")
    )


DATA_BLOCKS = (
    BlockDefinition(
        BarChartBlock,
        BlockGuide(
            "bar-chart",
            "visual",
            "comparison of categorical numerical data",
            "a zero-based vertical bar chart with values and labels",
            "learners need to compare two to six categories; use as the only body block",
            '{"type":"bar-chart","items":[{"label":"Mon","value":3},{"label":"Tue","value":7}],"unit":"cm"}',
            standalone=True,
        ),
        render_bar_chart,
    ),
    BlockDefinition(
        TimelineBlock,
        BlockGuide(
            "timeline",
            "visual",
            "events ordered by time",
            "a horizontal time axis with event cards",
            "chronology is the main relationship; use as the only body block",
            '{"type":"timeline","events":[{"label":"1609","text":"Galileo studies the sky"},{"label":"1969","text":"Humans reach the Moon"}]}',
            standalone=True,
        ),
        render_timeline,
    ),
)
