from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class ModelOutputError(ValueError):
    """The model response violates a repairable format or lesson specification contract."""


class StrictSpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class FormatRequest:
    topic: str
    lesson_format: str
    sources: str = ""
    previous_code: str | None = None
    previous_spec: str | None = None
    edit_instruction: str | None = None


@dataclass(frozen=True)
class PreparedLesson:
    summary: str
    source_code: str
    lesson_spec: str | None = None
    spec_version: str | None = None
    runtime_version: str | None = None
    compiler_version: str | None = None


class LessonFormatStrategy(Protocol):
    lesson_format: str
    repair_message: str

    def build_prompt(self, request: FormatRequest) -> str: ...
    def prepare(self, response: str) -> PreparedLesson: ...
    def can_repair(self, error: Exception) -> bool: ...
    def build_repair_prompt(self, original_prompt: str, response: str, error: Exception) -> str: ...
