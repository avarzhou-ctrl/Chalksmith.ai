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
    folder_id: UUID | None = None
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
    is_published: bool = False
    published_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)
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
    error_message: str | None
    edit_instruction: str | None
    is_final: bool


class LessonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    root_lesson_id: UUID
    folder_id: UUID | None = None
    version_count: int = 1
    topic: str
    format: LessonFormat
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    is_published: bool = False
    lesson_set_count: int = 0
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LessonUpdate(BaseModel):
    topic: str = Field(min_length=1, max_length=500)


class LessonFolderUpdate(BaseModel):
    folder_id: UUID | None = None


class LessonTagsUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list, max_length=5)


class LessonTagsResponse(BaseModel):
    root_lesson_id: UUID
    tags: list[str]


class LessonTagItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    value: str
    lesson_count: int


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: UUID | None = None


class FolderUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class FolderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    parent_id: UUID | None
    name: str
    created_at: datetime
    updated_at: datetime


class LessonSetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)


class LessonSetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2000)


class LessonSetAddLesson(BaseModel):
    lesson_id: UUID


class LessonSetOrderUpdate(BaseModel):
    root_lesson_ids: list[UUID] = Field(max_length=50)


class LessonSetLessonItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    root_lesson_id: UUID
    topic: str
    format: LessonFormat
    status: Literal["generating", "ready", "failed", "deleting"]
    summary: str | None
    position: int


class LessonSetListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    lesson_count: int
    preview_lessons: list[LessonSetLessonItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LessonSetDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    lessons: list[LessonSetLessonItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class AccessURLResponse(BaseModel):
    url: str
    expires_in: int


class FinalLessonResponse(BaseModel):
    root_lesson_id: UUID
    final_lesson_id: UUID


class LessonPublicationUpdate(BaseModel):
    published: bool
    display_name: str | None = Field(default=None, min_length=1, max_length=80)


class LessonPublicationResponse(BaseModel):
    root_lesson_id: UUID
    lesson_id: UUID
    is_published: bool
    published_at: datetime | None


class PublishedLessonItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    root_lesson_id: UUID
    topic: str
    format: LessonFormat
    summary: str | None
    published_at: datetime
    updated_at: datetime
    author_profile_id: UUID
    author_display_name: str
    like_count: int = 0
    tags: list[str] = Field(default_factory=list)


class PublishedLessonLikeResponse(BaseModel):
    root_lesson_id: UUID
    liked: bool
    like_count: int


class PublishedTagItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    label: str
    value: str
    lesson_count: int


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=1, max_length=80)
    bio: str = Field(default="", max_length=500)


class PublicProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    bio: str
    updated_at: datetime
