from html import escape
from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks.base import BlockDefinition, BlockGuide


class ComparisonBlock(StrictSpecModel):
    type: Literal["comparison"]
    left_title: str = Field(min_length=1, max_length=48)
    left_items: list[str] = Field(min_length=1, max_length=4)
    right_title: str = Field(min_length=1, max_length=48)
    right_items: list[str] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def validate_items(self) -> "ComparisonBlock":
        items = [*self.left_items, *self.right_items]
        if any(not item.strip() or len(item) > 100 for item in items):
            raise ValueError("comparison items must contain 1 to 100 characters")
        return self


class ProcessBlock(StrictSpecModel):
    type: Literal["process"]
    steps: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_steps(self) -> "ProcessBlock":
        if any(not step.strip() or len(step) > 80 for step in self.steps):
            raise ValueError("process steps must contain 1 to 80 characters")
        return self


class LabeledDiagramBlock(StrictSpecModel):
    type: Literal["labeled-diagram"]
    subject: str = Field(min_length=1, max_length=40)
    labels: list[str] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def validate_labels(self) -> "LabeledDiagramBlock":
        if any(not label.strip() or len(label) > 40 for label in self.labels):
            raise ValueError("labeled-diagram labels must contain 1 to 40 characters")
        return self


class CycleBlock(StrictSpecModel):
    type: Literal["cycle"]
    steps: list[str] = Field(min_length=3, max_length=6)

    @model_validator(mode="after")
    def validate_steps(self) -> "CycleBlock":
        if any(not step.strip() or len(step) > 48 for step in self.steps):
            raise ValueError("cycle steps must contain 1 to 48 characters")
        return self


def render_comparison(block: ComparisonBlock) -> str:
    left = "".join(f"<li>{escape(item)}</li>" for item in block.left_items)
    right = "".join(f"<li>{escape(item)}</li>" for item in block.right_items)
    return f"""
      <article class="cs-comparison">
        <div class="cs-card">
          <h3>{escape(block.left_title)}</h3>
          <ul>{left}</ul>
        </div>
        <div class="cs-card">
          <h3>{escape(block.right_title)}</h3>
          <ul>{right}</ul>
        </div>
      </article>"""


def render_process(block: ProcessBlock) -> str:
    steps = "".join(
        f"<li><span>{index}</span><p>{escape(step)}</p></li>"
        for index, step in enumerate(block.steps, start=1)
    )
    return f'<article class="cs-card cs-process"><ol>{steps}</ol></article>'


def render_labeled_diagram(block: LabeledDiagramBlock) -> str:
    labels = "".join(f"<li>{escape(label)}</li>" for label in block.labels)
    return f"""
      <figure class="cs-card cs-labeled-diagram">
        <div class="cs-labeled-diagram__subject">{escape(block.subject)}</div>
        <ul>{labels}</ul>
      </figure>"""


def render_cycle(block: CycleBlock) -> str:
    steps = "".join(
        f"<li><span>{index}</span><p>{escape(step)}</p></li>"
        for index, step in enumerate(block.steps, start=1)
    )
    return f"""
      <figure class="cs-card cs-cycle">
        <ol>{steps}</ol>
        <figcaption aria-hidden="true">↺</figcaption>
      </figure>"""


DIAGRAM_BLOCKS = (
    BlockDefinition(
        ComparisonBlock,
        BlockGuide(
            "comparison",
            "structural",
            "two-sided contrast",
            "two matched columns with headings",
            "two concepts need direct similarities or differences; use as the only body block",
            '{"type":"comparison","left_title":"Plant cell","left_items":["Cell wall"],"right_title":"Animal cell","right_items":["No cell wall"]}',
            standalone=True,
        ),
        render_comparison,
    ),
    BlockDefinition(
        ProcessBlock,
        BlockGuide(
            "process",
            "structural",
            "an ordered system or linear process",
            "a horizontal numbered sequence",
            "showing stages that move from a start to an end; use as the only body block",
            '{"type":"process","steps":["Evaporation","Condensation","Precipitation"]}',
            standalone=True,
        ),
        render_process,
    ),
    BlockDefinition(
        LabeledDiagramBlock,
        BlockGuide(
            "labeled-diagram",
            "visual",
            "parts or attributes connected to one central concept",
            "a hub-and-spoke concept diagram with surrounding labels",
            "showing conceptual parts, not precise anatomical positions; use as the only body block",
            '{"type":"labeled-diagram","subject":"Cell","labels":["Membrane","Nucleus","Cytoplasm"]}',
            standalone=True,
        ),
        render_labeled_diagram,
    ),
    BlockDefinition(
        CycleBlock,
        BlockGuide(
            "cycle",
            "visual",
            "a repeating sequence with no final endpoint",
            "a connected loop of three to six stages",
            "the final stage returns to the first; use as the only body block",
            '{"type":"cycle","steps":["Evaporation","Condensation","Precipitation","Collection"]}',
            standalone=True,
        ),
        render_cycle,
    ),
)
