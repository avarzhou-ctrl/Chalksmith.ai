import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session, select, desc
from backend.database import get_session
from backend.models import LessonRequest, LessonResponse, Lesson
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_p5js_lesson, render_revealjs_lesson

router = APIRouter()

@router.post("/lesson", response_model=LessonResponse)
async def create_lesson(request: LessonRequest, req: Request, session: Session = Depends(get_session)):
    base_url = str(req.base_url).rstrip("/")
    
    code = generate_lesson(request.topic, request.model, request.format)
    
    if request.format == "manim":
        file_url = render_manim_lesson(request.topic, request.model, code)
    elif request.format == "p5.js":
        file_url = render_p5js_lesson(request.topic, request.model, code)
    elif request.format == "reveal.js":
        file_url = render_revealjs_lesson(request.topic, request.model, code)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")
    
    db_lesson = Lesson(
        id=str(uuid.uuid4()),
        topic=request.topic,
        model=request.model,
        format=request.format,
        url=file_url,
        code=code
    )

    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)

    return LessonResponse(
        url=f"{base_url}{db_lesson.url}",
        code=db_lesson.code
    )

@router.get("/lesson", response_model=LessonResponse)
async def get_lesson(topic: str, model: str, format: str, req: Request, session: Session = Depends(get_session)):
    base_url = str(req.base_url).rstrip("/")

    statement = select(Lesson).where(
        Lesson.topic == topic, 
        Lesson.model == model, 
        Lesson.format == format
    ).order_by(desc(Lesson.created_at))
    results = session.exec(statement)
    db_lesson = results.first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found. Please use POST to generate it first.")
    
    return LessonResponse(
        url=f"{base_url}{db_lesson.url}",
        code=db_lesson.code
    )
