from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


LessonFormat = Literal["interactive", "slides", "video"]


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    root_lesson_id: UUID
    parent_lesson_id: UUID | None
    version_number: int
    topic: str
    format: LessonFormat
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    source_code: str | None
    spec_version: str | None
    runtime_version: str | None
    compiler_version: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class LessonVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_lesson_id: UUID | None
    version_number: int
    topic: str
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    edit_instruction: str | None


class LessonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    root_lesson_id: UUID
    version_count: int = 1
    topic: str
    format: LessonFormat
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    created_at: datetime
    updated_at: datetime


class LessonUpdate(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class AccessURLResponse(BaseModel):
    url: str
    expires_in: int
