import code
import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session, select, desc
from backend.database import get_session
from backend.models import LessonRequest, LessonResponse, Lesson
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_remotion_lesson, render_p5js_lesson, render_revealjs_lesson
from backend.services.export import export_service

router = APIRouter()

@router.post("/lesson", response_model=LessonResponse)
async def create_lesson(request: LessonRequest, req: Request, session: Session = Depends(get_session)):
    # Core entry point for all lesson generation and iterative editing
    base_url = str(req.base_url).rstrip("/")
    
    previous_code = None
    if request.lesson_id:
        # Load previous code to provide the LLM with context for iterative edits
        statement = select(Lesson).where(Lesson.id == request.lesson_id)
        db_lesson = session.exec(statement).first()
        if db_lesson:
            previous_code = db_lesson.code
            if not request.topic:
                request.topic = db_lesson.topic

    # Calls LLM engine to generate or edit raw source code
    lesson = generate_lesson(
        request.topic, 
        request.model, 
        request.format, 
        previous_code=previous_code, 
        edit_prompt=request.prompt
    )
    
    # Route to specific renderer based on target format (Video, Interactive, or Slides)
    try:
        if request.format == "remotion":
            file_url = render_remotion_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "manim":
            file_url = render_manim_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "p5.js":
            file_url = render_p5js_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "reveal.js":
            file_url = render_revealjs_lesson(request.topic, request.model, lesson["code"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        # Return as 422 so frontend can detect it as a render/syntax error
        raise HTTPException(status_code=422, detail=str(e))
    
    db_lesson = Lesson(
        id=str(uuid.uuid4()),
        topic=request.topic,
        model=request.model,
        format=request.format,
        url=file_url,
        code=lesson["code"],
        summary=lesson["summary"]
    )

    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)

    return LessonResponse(
        id=db_lesson.id,
        url=f"{base_url}{db_lesson.url}",
        code=db_lesson.code,
        summary=db_lesson.summary
    )

@router.get("/lesson", response_model=LessonResponse)
async def get_lesson(topic: str, model: str, format: str, req: Request, session: Session = Depends(get_session)):
    # Retrieves the most recent version of a specific lesson
    base_url = str(req.base_url).rstrip("/")

    statement = select(Lesson).where(
        Lesson.topic == topic, 
        Lesson.model == model, 
        Lesson.format == format,
    ).order_by(desc(Lesson.created_at))
    results = session.exec(statement)
    db_lesson = results.first()

    return LessonResponse(
        id=db_lesson.id,
        url=f"{base_url}{db_lesson.url}",
        code=db_lesson.code,
        summary=db_lesson.summary
    )

@router.get("/export")
async def export_lesson(id: str, session: Session = Depends(get_session)):
    # Triggers export service to convert lesson to static formats like PDF/MP4
    statement = select(Lesson).where(Lesson.id == id)
    db_lesson = session.exec(statement).first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    try:
        return export_service.prepare_export(
            file_url=db_lesson.url,
            format_type=db_lesson.format,
            topic=db_lesson.topic
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
