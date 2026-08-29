from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Index, Text, UniqueConstraint
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"
    __table_args__ = (
        UniqueConstraint(
            "owner_id",
            "root_lesson_id",
            "version_number",
            name="uq_lessons_owner_root_version",
        ),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: str = Field(index=True, max_length=128)
    # All revisions in a lesson share a root; parent preserves the edit lineage.
    root_lesson_id: UUID = Field(index=True)
    parent_lesson_id: UUID | None = Field(default=None, index=True)
    # Meaningful on the root row: the revision selected for dashboard and sharing.
    final_lesson_id: UUID | None = Field(default=None, index=True)
    # Meaningful on the root row; revisions inherit folder placement from their root.
    folder_id: UUID | None = Field(default=None, index=True)
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
    # Meaningful on the root row; the selected final revision is public while set.
    published_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    # First prepare/render failure that triggered a bounded repair; kept after success.
    first_error: str | None = Field(default=None, sa_column=Column(Text))
    # Private debugging payload; never serialized by an API response model.
    raw_model_output: str | None = Field(default=None, sa_column=Column(Text))
    edit_instruction: str | None = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class LessonFolder(SQLModel, table=True):
    __tablename__ = "lesson_folders"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: str = Field(index=True, max_length=128)
    parent_id: UUID | None = Field(default=None, index=True)
    name: str = Field(max_length=100)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class LessonTag(SQLModel, table=True):
    __tablename__ = "lesson_tags"
    __table_args__ = (
        Index("ix_lesson_tags_owner_normalized", "owner_id", "normalized_value"),
    )

    # Tags classify the whole lesson lineage, so they always point at its root row.
    root_lesson_id: UUID = Field(primary_key=True)
    normalized_value: str = Field(primary_key=True, max_length=32)
    owner_id: str = Field(index=True, max_length=128)
    label: str = Field(max_length=32)
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class UserProfile(SQLModel, table=True):
    __tablename__ = "user_profiles"

    # Public URLs use this opaque id instead of exposing the Clerk subject.
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: str = Field(index=True, unique=True, max_length=128)
    display_name: str = Field(max_length=80)
    bio: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
