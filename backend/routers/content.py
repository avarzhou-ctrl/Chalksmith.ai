import uuid
import json
import asyncio
import os
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, desc
from backend.database import get_session
from backend.models import LessonRequest, LessonResponse, Lesson
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_remotion_lesson, render_p5js_lesson, render_revealjs_lesson
from backend.services.export import export_service

router = APIRouter()

@router.delete("/lesson/{lesson_id}")
async def delete_lesson(lesson_id: str, session: Session = Depends(get_session)):
    # Delete the lesson from the database and remove its associated physical file
    statement = select(Lesson).where(Lesson.id == lesson_id)
    db_lesson = session.exec(statement).first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Construct the absolute path to the static file to remove it
    # We use a relative path logic consistent with main.py's static mount
    try:
        if db_lesson.url:
            # db_lesson.url looks like "/static/manim_xxx.mp4"
            # We need to strip the leading /static/ to get the filename
            filename = db_lesson.url.replace("/static/", "")
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(current_dir, "static", filename)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # For Manim/Remotion, we might also have a .py or .json file to clean up
            if db_lesson.format in ["manim", "remotion"]:
                ext = ".py" if db_lesson.format == "manim" else ".json"
                source_file = file_path.rsplit(".", 1)[0] + ext
                if os.path.exists(source_file):
                    os.remove(source_file)
    except Exception as e:
        # We log and continue as the primary goal is database cleanup
        print(f"Failed to delete file for lesson {lesson_id}: {e}")

    session.delete(db_lesson)
    session.commit()

    return {"status": "success", "message": "Lesson deleted successfully"}

@router.get("/lesson/generate")
async def generate_lesson_stream(
    topic: str, 
    model: str, 
    format: str, 
    lesson_id: str = None, 
    prompt: str = None,
    req: Request = None, 
    session: Session = Depends(get_session)
):
    """
    Streaming endpoint for lesson generation.
    Yields JSON objects indicating progress and finally the result.
    """
    base_url = str(req.base_url).rstrip("/")

    async def event_generator():
        # Queue bridges synchronous executor threads with the async SSE generator
        queue = asyncio.Queue()

        def status_callback(msg, prog):
            # Synchronous callback for the executor to push updates thread-safely
            loop.call_soon_threadsafe(queue.put_nowait, (msg, prog))

        try:
            # Stage 1: Initializing
            yield f"data: {json.dumps({'status': 'initializing', 'message': 'Initializing generation...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.1)

            previous_code = None
            active_topic = topic
            if lesson_id:
                yield f"data: {json.dumps({'status': 'loading_context', 'message': 'Loading previous lesson context...', 'progress': 15})}\n\n"
                # Load previous context to enable iterative edits based on the current lesson state
                statement = select(Lesson).where(Lesson.id == lesson_id)
                db_lesson = session.exec(statement).first()
                if db_lesson:
                    previous_code = db_lesson.code
                    if not active_topic:
                        active_topic = db_lesson.topic

            # Stage 2: LLM Thinking/Generating
            yield f"data: {json.dumps({'status': 'generating', 'message': f'Chalksmith is thinking about {active_topic}...', 'progress': 30})}\n\n"
            
            loop = asyncio.get_event_loop()
            # Run LLM generation in an executor to avoid blocking the main async event loop during long API calls
            lesson = await loop.run_in_executor(
                None, 
                lambda: generate_lesson(
                    active_topic, 
                    model, 
                    format, 
                    previous_code=previous_code, 
                    edit_prompt=prompt
                )
            )

            # Stage 3: Rendering
            yield f"data: {json.dumps({'status': 'rendering', 'message': f'Rendering {format} assets...', 'progress': 60})}\n\n"
            
            # Start rendering in a background thread to prevent UI freezing while sub-processes (like npx remotion) run
            render_task = loop.run_in_executor(
                None,
                lambda: (
                    render_remotion_lesson(active_topic, model, lesson["code"], on_progress=status_callback) if format == "remotion" else
                    render_manim_lesson(active_topic, model, lesson["code"], on_progress=status_callback) if format == "manim" else
                    render_p5js_lesson(active_topic, model, lesson["code"], on_progress=status_callback) if format == "p5.js" else
                    render_revealjs_lesson(active_topic, model, lesson["code"], on_progress=status_callback) if format == "reveal.js" else
                    None
                )
            )

            # Continuously poll the queue with a timeout to yield real-time rendering updates while waiting for completion
            while not render_task.done():
                try:
                    # Wait for an update or a timeout to check if the task is done
                    msg, prog = await asyncio.wait_for(queue.get(), timeout=0.1)
                    yield f"data: {json.dumps({'status': 'rendering', 'message': msg, 'progress': prog})}\n\n"
                except asyncio.TimeoutError:
                    continue
            
            # Exhaust the queue of any remaining messages to ensure no final progress updates are missed
            while not queue.empty():
                msg, prog = queue.get_nowait()
                yield f"data: {json.dumps({'status': 'rendering', 'message': msg, 'progress': prog})}\n\n"

            try:
                file_url = await render_task
                if file_url is None:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Unsupported format'})}\n\n"
                    return
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                return

            # Stage 4: Finalizing
            yield f"data: {json.dumps({'status': 'finalizing', 'message': 'Saving lesson to database...', 'progress': 95})}\n\n"
            
            new_id = str(uuid.uuid4())
            db_lesson = Lesson(
                id=new_id,
                topic=active_topic,
                model=model,
                format=format,
                url=file_url,
                code=lesson["code"],
                summary=lesson["summary"]
            )

            session.add(db_lesson)
            session.commit()
            session.refresh(db_lesson)

            result = LessonResponse(
                id=db_lesson.id,
                url=f"{base_url}{db_lesson.url}",
                code=db_lesson.code,
                summary=db_lesson.summary
            )
            
            yield f"data: {json.dumps({'status': 'complete', 'result': result.dict(), 'progress': 100})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

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
        return await export_service.prepare_export(
            file_url=db_lesson.url,
            format_type=db_lesson.format,
            topic=db_lesson.topic
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
