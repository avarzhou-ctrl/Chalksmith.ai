from pydantic import BaseModel

class LessonRequest(BaseModel):
    topic: str
    model: str
    format: str

class LessonResponse(BaseModel):
    url: str
    code: str