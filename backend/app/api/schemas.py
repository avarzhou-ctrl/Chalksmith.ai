from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


LessonFormat = Literal["interactive", "slides", "video"]


class LessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    topic: str
    format: LessonFormat
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    source_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class LessonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
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
