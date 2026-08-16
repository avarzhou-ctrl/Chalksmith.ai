from typing import Annotated, Literal

from pydantic import Field, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel


SlideKind = Literal[
    "learning-goal",
    "concept",
    "visual-explanation",
    "worked-example",
    "comprehension-check",
    "recap",
]


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


class EquationBlock(StrictSpecModel):
    type: Literal["equation"]
    expression: str = Field(min_length=1, max_length=160)
    explanation: str | None = Field(default=None, min_length=1, max_length=180)

    @model_validator(mode="after")
    def validate_expression(self) -> "EquationBlock":
        if "$" in self.expression:
            raise ValueError("equation expressions must not include dollar delimiters")
        return self


class StepsBlock(StrictSpecModel):
    type: Literal["steps"]
    items: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_items(self) -> "StepsBlock":
        if any(not item.strip() or len(item) > 140 for item in self.items):
            raise ValueError("step items must contain 1 to 140 characters")
        return self


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


class FractionModelBlock(StrictSpecModel):
    type: Literal["fraction-model"]
    numerator: int = Field(ge=0, le=12)
    denominator: int = Field(ge=2, le=12)
    label: str | None = Field(default=None, min_length=1, max_length=48)

    @model_validator(mode="after")
    def validate_fraction(self) -> "FractionModelBlock":
        if self.numerator > self.denominator:
            raise ValueError("fraction numerator cannot exceed its denominator")
        return self


class ProcessBlock(StrictSpecModel):
    type: Literal["process"]
    steps: list[str] = Field(min_length=2, max_length=5)

    @model_validator(mode="after")
    def validate_steps(self) -> "ProcessBlock":
        if any(not step.strip() or len(step) > 80 for step in self.steps):
            raise ValueError("process steps must contain 1 to 80 characters")
        return self


SlideBlock = Annotated[
    StatementBlock
    | BulletsBlock
    | CalloutBlock
    | EquationBlock
    | StepsBlock
    | ComparisonBlock
    | FractionModelBlock
    | ProcessBlock,
    Field(discriminator="type"),
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
                raise ValueError("comprehension-check content exceeds the slide capacity")
        elif not self.body:
            raise ValueError(f"{self.kind} slides require at least one body block")
        elif any(
            value is not None
            for value in (self.question, self.choices, self.answer_index, self.explanation)
        ):
            raise ValueError("question fields are only valid on comprehension-check slides")
        elif sum(_visible_text_length(block.model_dump()) for block in self.body) > 520:
            raise ValueError(f"{self.kind} content exceeds the slide capacity")
        elif len(self.body) > 1 and any(
            isinstance(block, (ComparisonBlock, ProcessBlock)) for block in self.body
        ):
            raise ValueError(
                "comparison and process blocks must occupy a slide body by themselves"
            )
        return self


class SlidesPayload(StrictSpecModel):
    slides: list[SlideSpec] = Field(min_length=5, max_length=9)


class SlidesLessonSpec(StrictSpecModel):
    schema_version: Literal["chalksmith.slides.v1"]
    format: Literal["slides"]
    summary: str = Field(min_length=1, max_length=600)
    title: str = Field(min_length=1, max_length=100)
    learning_goal: str = Field(min_length=1, max_length=240)
    grade_band: Literal["elementary", "middle"]
    language: str = Field(pattern=r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
    payload: SlidesPayload


def _visible_text_length(value: object) -> int:
    if isinstance(value, str):
        return len(value)
    if isinstance(value, dict):
        return sum(_visible_text_length(item) for item in value.values())
    if isinstance(value, list):
        return sum(_visible_text_length(item) for item in value)
    return 0
