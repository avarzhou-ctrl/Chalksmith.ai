from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: str = Field(index=True, max_length=128)
    # All revisions in a lesson share a root; parent preserves the edit lineage.
    root_lesson_id: UUID = Field(index=True)
    parent_lesson_id: UUID | None = Field(default=None, index=True)
    version_number: int = Field(default=1, ge=1)
    topic: str = Field(max_length=500)
    format: str = Field(index=True, max_length=32)
    status: str = Field(default="generating", index=True, max_length=32)
    summary: str | None = Field(default=None, sa_column=Column(Text))
    source_code: str | None = Field(default=None, sa_column=Column(Text))
    lesson_spec: str | None = Field(default=None, sa_column=Column(Text))
    spec_version: str | None = Field(default=None, max_length=64)
    runtime_version: str | None = Field(default=None, max_length=64)
    compiler_version: str | None = Field(default=None, max_length=64)
    object_key: str | None = Field(default=None, max_length=1024)
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    edit_instruction: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
