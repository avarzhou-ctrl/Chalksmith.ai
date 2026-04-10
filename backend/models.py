from datetime import datetime
from pydantic import BaseModel
from sqlmodel import SQLModel, Field

class LessonRequest(BaseModel):
    topic: str
    model: str
    format: str
    lesson_id: str | None = None
    prompt: str | None = None

class LessonResponse(BaseModel):
    id: str
    url: str
    code: str

class Lesson(SQLModel, table=True):
    id: str = Field(primary_key=True)
    topic: str = Field(index=True)
    model: str = Field(index=True)
    format: str = Field(index=True)
    url: str
    code: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)