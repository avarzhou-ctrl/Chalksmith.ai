from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

class LessonRequest(BaseModel):
    # lesson_id is provided for iterative edits; null for new lessons
    # prompt contains instructions for changes to existing code
    topic: str
    model: str
    format: str
    lesson_id: Optional[str] = None
    prompt: Optional[str] = None

class LessonResponse(BaseModel):
    # Standardized API response containing the public URL and source code
    id: str
    url: str
    code: str
    summary: str

class Lesson(SQLModel, table=True):
    # We store the raw 'code' locally to enable future iterative edits
    id: str = Field(primary_key=True)
    topic: str = Field(index=True)
    model: str = Field(index=True)
    format: str = Field(index=True)
    url: str
    code: str
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)