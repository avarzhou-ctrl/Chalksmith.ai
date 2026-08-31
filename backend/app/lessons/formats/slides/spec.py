from typing import Literal

from pydantic import Field, field_validator, model_validator

from backend.app.lessons.formats.contracts import StrictSpecModel
from backend.app.lessons.formats.slides.presentation import SlideBlock, block_visible_length
from backend.app.lessons.formats.slides.presentation.layouts import (
    LAYOUTS,
    LayoutName,
    normalize_layout,
)


SLIDE_CAPACITY = 720


class SlideSpec(StrictSpecModel):
    title: str = Field(min_length=1, max_length=80)
    label: str | None = Field(default=None, min_length=1, max_length=40)
    background: Literal["default", "soft", "accent", "contrast"] = "default"
    layout: LayoutName = "auto"
    blocks: list[SlideBlock] = Field(min_length=1, max_length=6)

    @field_validator("layout", mode="before")
    @classmethod
    def recover_unknown_layout(cls, value: object) -> object:
        if value == "auto" or isinstance(value, str) and value in LAYOUTS:
            return value
        return "auto"

    @model_validator(mode="after")
    def validate_composition(self) -> "SlideSpec":
        self.layout = normalize_layout(self.layout, len(self.blocks))
        if sum(block_visible_length(block) for block in self.blocks) > SLIDE_CAPACITY:
            raise ValueError("slide content exceeds the slide capacity")
        return self


class SlidesPayload(StrictSpecModel):
    slides: list[SlideSpec] = Field(min_length=5, max_length=9)


class SlidesLessonSpec(StrictSpecModel):
    schema_version: Literal["chalksmith.slides.v2"]
    format: Literal["slides"]
    summary: str = Field(min_length=1, max_length=600)
    title: str = Field(min_length=1, max_length=100)
    learning_goal: str = Field(min_length=1, max_length=240)
    grade_band: Literal["elementary", "middle", "advanced"]
    language: str = Field(pattern=r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
    payload: SlidesPayload
