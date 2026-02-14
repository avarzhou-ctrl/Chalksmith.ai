from fastapi import APIRouter, Request
from backend.models import LessonRequest, LessonResponse
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_p5js_lesson, render_revealjs_lesson

router = APIRouter()

@router.post("/lesson", response_model=LessonResponse)
async def create_lesson(request: LessonRequest, req: Request):
    base_url = str(req.base_url).rstrip("/")
    if request.format == "manim":
        file_url = render_manim_lesson(request.topic, request.model)
    elif request.format == "p5.js":
        file_url = render_p5js_lesson(request.topic, request.model)
    elif request.format == "reveal.js":
        file_url = render_revealjs_lesson(request.topic, request.model)
    else:
        return {"error": "Unsupported format"}
    
    return LessonResponse(
        url=f"{base_url}{file_url}",
        code=generate_lesson(request.topic, request.model, request.format)
    )

@router.get("/lesson", response_model=LessonResponse)
async def get_existinglesson(topic: str, model: str, format: str, req: Request):
    base_url = str(req.base_url).rstrip("/")

    file_url = check_if_lesson_exists(topic, model, format)

    if not file_url:
        return {"error": "Lesson not foudn. Please use POST to generate it first."}
    
    return LessonResponse(
        url=f"{base_url}{file_url}",
        code=generate_lesson(topic, model, format)
    )