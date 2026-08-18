from typing import Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.blocks import CustomHtmlBlock, SlideBlock
from backend.app.lessons.formats.slides.blocks.custom import custom_html_visible_length
from backend.app.lessons.formats.slides.registry import STANDALONE_BLOCK_TYPES


MAX_CUSTOM_HTML_BLOCKS = 5

SlideKind = Literal[
    "learning-goal",
    "concept",
    "visual-explanation",
    "worked-example",
    "comprehension-check",
    "recap",
]


class SlideSpec(StrictSpecModel):
    kind: SlideKind
    title: str = Field(min_length=1, max_length=80)
    body: list[SlideBlock] = Field(default_factory=list, max_length=3)
    question: str | None = Field(default=None, min_length=1, max_length=180)
    choices: list[str] | None = Field(default=None, min_length=2, max_length=4)
    answer_index: int | None = Field(default=None, ge=0, le=3)
    explanation: str | None = Field(default=None, min_length=1, max_length=220)

    @model_validator(mode="after")
    def validate_kind_content(self) -> "SlideSpec":
        if self.kind == "comprehension-check":
            if self.question is None or self.choices is None:
                raise ValueError("comprehension checks require a question and choices")
            if self.answer_index is None or self.answer_index >= len(self.choices):
                raise ValueError("answer_index must point to one of the choices")
            if self.explanation is None:
                raise ValueError("comprehension checks require an answer explanation")
            if any(not choice.strip() or len(choice) > 100 for choice in self.choices):
                raise ValueError("choices must contain 1 to 100 characters")
            visible_characters = sum(
                len(value)
                for value in [self.question, *self.choices, self.explanation]
                if value
            )
            if visible_characters > 520:
                raise ValueError(
                    "comprehension-check content exceeds the slide capacity"
                )
        elif not self.body:
            raise ValueError(f"{self.kind} slides require at least one body block")
        elif any(
            value is not None
            for value in (
                self.question,
                self.choices,
                self.answer_index,
                self.explanation,
            )
        ):
            raise ValueError(
                "question fields are only valid on comprehension-check slides"
            )
        elif sum(_block_text_length(block) for block in self.body) > 520:
            raise ValueError(f"{self.kind} content exceeds the slide capacity")
        elif len(self.body) > 1 and any(
            block.type in STANDALONE_BLOCK_TYPES for block in self.body
        ):
            raise ValueError(
                "spatially dense blocks must occupy a slide body by themselves"
            )
        return self


class SlidesPayload(StrictSpecModel):
    slides: list[SlideSpec] = Field(min_length=5, max_length=9)

    @model_validator(mode="after")
    def validate_custom_html_budget(self) -> "SlidesPayload":
        # Free-form markup is an escape hatch; a deck built from it loses every guarantee.
        authored = sum(
            any(isinstance(block, CustomHtmlBlock) for block in slide.body)
            for slide in self.slides
        )
        if authored > MAX_CUSTOM_HTML_BLOCKS:
            raise ValueError(
                f"at most {MAX_CUSTOM_HTML_BLOCKS} slides may use custom-html; "
                f"{authored} did. Use semantic blocks for the rest."
            )
        return self


class SlidesLessonSpec(StrictSpecModel):
    schema_version: Literal["chalksmith.slides.v1"]
    format: Literal["slides"]
    summary: str = Field(min_length=1, max_length=600)
    title: str = Field(min_length=1, max_length=100)
    learning_goal: str = Field(min_length=1, max_length=240)
    grade_band: Literal["elementary", "middle", "advanced"]
    language: str = Field(pattern=r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
    payload: SlidesPayload


def _block_text_length(block: SlideBlock) -> int:
    # Author markup is not learner-visible, so it must not consume slide capacity.
    if isinstance(block, CustomHtmlBlock):
        return custom_html_visible_length(block)
    return _visible_text_length(block.model_dump())


def _visible_text_length(value: object) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, dict):
        return sum(_visible_text_length(item) for item in value.values())
    if isinstance(value, list):
        return sum(_visible_text_length(item) for item in value)
    return 0
