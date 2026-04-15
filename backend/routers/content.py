import uuid
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlmodel import Session, select, desc
from backend.database import get_session
from backend.models import LessonRequest, LessonResponse, Lesson
from backend.services.llm import generate_lesson
from backend.services.render import render_remotion_lesson, render_p5js_lesson, render_revealjs_lesson
from backend.services.export import export_service

router = APIRouter()

@router.post("/lesson", response_model=LessonResponse)
async def create_lesson(request: LessonRequest, req: Request, session: Session = Depends(get_session)):
    base_url = str(req.base_url).rstrip("/")
    
    # Check if this is an edit request
    previous_code = None
    if request.lesson_id:
        statement = select(Lesson).where(Lesson.id == request.lesson_id)
        db_lesson = session.exec(statement).first()
        if db_lesson:
            previous_code = db_lesson.code
            # Ensure we use the correct topic from the original lesson if not provided new prompt
            if not request.topic:
                request.topic = db_lesson.topic

    code = generate_lesson(
        request.topic, 
        request.model, 
        request.format, 
        previous_code=previous_code, 
        edit_prompt=request.prompt
    )
    
    if request.format == "remotion":
        file_url = render_remotion_lesson(request.topic, request.model, code)
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
        id=db_lesson.id,
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

    return LessonResponse(
        id=db_lesson.id,
        url=f"{base_url}{db_lesson.url}",
        code=db_lesson.code
    )

@router.get("/export")
async def export_lesson(id: str, session: Session = Depends(get_session)):
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
