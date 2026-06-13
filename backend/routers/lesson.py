import uuid
import json
import asyncio
import os
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, desc
from backend.database import get_session
from backend.models import LessonRequest, LessonRenameRequest, LessonResponse, LessonListResponse, Lesson, User
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_remotion_lesson, render_p5js_lesson, render_revealjs_lesson
from backend.services.export import export_service

router = APIRouter()

@router.delete("/lesson/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Delete the lesson from the database and remove its associated physical file
    statement = select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == x_user_id)
    db_lesson = session.exec(statement).first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Construct the absolute path 
    try:
        if db_lesson.url:
            # Strip the leading /static/ to get the filename
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

@router.patch("/lesson/{lesson_id}")
async def edit_lesson_title(
    lesson_id: str,
    request: LessonRenameRequest,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Simple endpoint to update the lesson's topic/title for better organization
    new_title = request.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Lesson title cannot be empty")

    statement = select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == x_user_id)
    db_lesson = session.exec(statement).first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    db_lesson.topic = new_title
    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)

    return {"status": "success", "message": "Lesson title updated successfully", "new_title": db_lesson.topic}

@router.get("/lesson/generate")
async def generate_lesson_stream(
    topic: str, 
    model: str, 
    format: str, 
    lesson_id: Optional[str] = None, 
    prompt: Optional[str] = None,
    req: Request = None, 
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
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
                statement = select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == x_user_id)
                db_lesson = session.exec(statement).first()
                if not db_lesson:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Lesson not found'})}\n\n"
                    return

                previous_code = db_lesson.code
                if not active_topic:
                    active_topic = db_lesson.topic

            # Stage 2: LLM Thinking/Generating
            yield f"data: {json.dumps({'status': 'generating', 'message': f'Chalksmith is thinking about {active_topic}...', 'progress': 30})}\n\n"
            
            loop = asyncio.get_event_loop()
            # Run LLM generation in an executor to avoid blocking the main async event loop during long API calls
            # LLM API calls are currently synchronous, but we check for disconnection before moving to rendering
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

            if await req.is_disconnected():
                print("Client disconnected after LLM generation. Aborting.")
                return

            # Stage 3: Rendering
            yield f"data: {json.dumps({'status': 'rendering', 'message': f'Rendering {format} assets...', 'progress': 60})}\n\n"
            
            # Start rendering as an async task to allow for clean cancellation if the client disconnects
            if format == "remotion":
                render_task = asyncio.create_task(render_remotion_lesson(active_topic, model, lesson["code"], on_progress=status_callback))
            elif format == "manim":
                render_task = asyncio.create_task(render_manim_lesson(active_topic, model, lesson["code"], on_progress=status_callback))
            elif format == "p5.js":
                render_task = asyncio.create_task(render_p5js_lesson(active_topic, model, lesson["code"], on_progress=status_callback))
            elif format == "reveal.js":
                render_task = asyncio.create_task(render_revealjs_lesson(active_topic, model, lesson["code"], on_progress=status_callback))
            else:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Unsupported format'})}\n\n"
                return

            # Continuously poll for progress updates while monitoring the connection state
            try:
                while not render_task.done():
                    if await req.is_disconnected():
                        print(f"Client disconnected during {format} rendering. Cancelling task.")
                        render_task.cancel()
                        # Wait a moment for the task to receive the cancellation and clean up its subprocesses
                        try:
                            await asyncio.wait_for(render_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass
                        return
                    
                    try:
                        # Non-blocking check of the progress queue
                        msg, prog = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield f"data: {json.dumps({'status': 'rendering', 'message': msg, 'progress': prog})}\n\n"
                    except asyncio.TimeoutError:
                        continue
                
                # Exhaust the queue of any remaining messages to ensure no final progress updates are missed
                while not queue.empty():
                    msg, prog = queue.get_nowait()
                    yield f"data: {json.dumps({'status': 'rendering', 'message': msg, 'progress': prog})}\n\n"

                file_url = await render_task
                if file_url is None:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Rendering failed'})}\n\n"
                    return
            except asyncio.CancelledError:
                render_task.cancel()
                raise
            except Exception as e:
                yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
                return

            # Stage 4: Finalizing
            yield f"data: {json.dumps({'status': 'finalizing', 'message': 'Saving lesson to database...', 'progress': 95})}\n\n"
            
            # Ensure user exists to satisfy foreign key constraint (race condition fallback)
            if x_user_id:
                user = session.get(User, x_user_id)
                if not user:
                    print(f"LAZY USER CREATION: User {x_user_id} missing during stream finalization. Creating placeholder.")
                    user = User(id=x_user_id, email=f"pending_{x_user_id}@chalksmith.ai")
                    session.add(user)

            new_id = str(uuid.uuid4())
            db_lesson = Lesson(
                id=new_id,
                user_id=x_user_id,
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
                url=db_lesson.url,
                code=db_lesson.code,
                summary=db_lesson.summary
            )
            
            yield f"data: {json.dumps({'status': 'complete', 'result': result.dict(), 'progress': 100})}\n\n"

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"CRITICAL ERROR IN SSE STREAM: {error_detail}")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e), 'detail': error_detail})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/lesson/{lesson_id}")
async def get_lesson_by_id(
    lesson_id: str,
    req: Request,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Retrieve a specific lesson by its unique ID, used for loading lessons from dashboard links
    statement = select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == x_user_id)
    db_lesson = session.exec(statement).first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    return LessonListResponse(
        id=db_lesson.id,
        topic=db_lesson.topic,
        model=db_lesson.model,
        format=db_lesson.format,
        url=db_lesson.url,
        code=db_lesson.code,
        summary=db_lesson.summary,
        created_at=db_lesson.created_at
    )

@router.post("/lesson", response_model=LessonResponse)
async def create_lesson(
    request: LessonRequest,
    req: Request,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    previous_code = None
    if request.lesson_id:
        # Load previous code to provide the LLM with context for iterative edits
        statement = select(Lesson).where(Lesson.id == request.lesson_id, Lesson.user_id == x_user_id)
        db_lesson = session.exec(statement).first()
        if not db_lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        previous_code = db_lesson.code
        if not request.topic:
            request.topic = db_lesson.topic

    # Calls LLM engine to generate or edit raw source code
    loop = asyncio.get_event_loop()
    lesson = await loop.run_in_executor(
        None,
        lambda: generate_lesson(
            request.topic, 
            request.model, 
            request.format, 
            previous_code=previous_code, 
            edit_prompt=request.prompt
        )
    )
    
    # Route to specific renderer based on target format (Video, Interactive, or Slides)
    try:
        if request.format == "remotion":
            file_url = await render_remotion_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "manim":
            file_url = await render_manim_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "p5.js":
            file_url = await render_p5js_lesson(request.topic, request.model, lesson["code"])
        elif request.format == "reveal.js":
            file_url = await render_revealjs_lesson(request.topic, request.model, lesson["code"])
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except Exception as e:
        # Return as 422 so frontend can detect it as a render/syntax error
        raise HTTPException(status_code=422, detail=str(e))
    
    # Ensure user exists to satisfy foreign key constraint (race condition fallback)
    if x_user_id:
        user = session.get(User, x_user_id)
        if not user:
            print(f"LAZY USER CREATION: User {x_user_id} missing during create_lesson. Creating placeholder.")
            user = User(id=x_user_id, email=f"pending_{x_user_id}@chalksmith.ai")
            session.add(user)

    db_lesson = Lesson(
        id=str(uuid.uuid4()),
        user_id=x_user_id,
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
        url=db_lesson.url,
        code=db_lesson.code,
        summary=db_lesson.summary
    )

@router.get("/lesson", response_model=LessonResponse)
async def get_lesson(
    topic: str,
    model: str,
    format: str,
    req: Request,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Retrieves the most recent version of a specific lesson
    statement = select(Lesson).where(
        Lesson.topic == topic, 
        Lesson.model == model, 
        Lesson.format == format,
        Lesson.user_id == x_user_id,
    ).order_by(desc(Lesson.created_at))
    results = session.exec(statement)
    db_lesson = results.first()

    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return LessonResponse(
        id=db_lesson.id,
        url=db_lesson.url,
        code=db_lesson.code,
        summary=db_lesson.summary
    )

@router.get("/lessons", response_model=list[LessonListResponse])
async def list_lessons(
    req: Request,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Lists all existing lessons, sorted by creation date (newest first) for the dashboard
    db_lessons = session.exec(select(Lesson).where(Lesson.user_id == x_user_id).order_by(desc(Lesson.created_at))).all()

    return [
        LessonListResponse(
            id=lesson.id,
            topic=lesson.topic,
            model=lesson.model,
            format=lesson.format,
            url=lesson.url,
            code=lesson.code,
            summary=lesson.summary,
            created_at=lesson.created_at
        ) for lesson in db_lessons
    ]

@router.get("/export")
async def export_lesson(
    id: str,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Triggers export service to convert lesson to static formats like PDF/MP4
    statement = select(Lesson).where(Lesson.id == id, Lesson.user_id == x_user_id)
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
