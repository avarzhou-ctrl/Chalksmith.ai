import json
import asyncio
import os
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Header, Request, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from backend.crud.lessons import (
    create_lesson_record,
    delete_lesson_record,
    get_lesson_by_details,
    get_lesson_for_user,
    search_user_lessons,
    update_lesson_title,
)
from backend.database import get_session
from backend.models import LessonRequest, LessonRenameRequest, LessonResponse, LessonListResponse
from backend.services.llm import generate_lesson
from backend.services.render import render_manim_lesson, render_remotion_lesson, render_p5js_lesson, render_revealjs_lesson
from backend.services.export import export_service
from backend.services.sources import extract_source_context

router = APIRouter()


async def extract_combined_source_context(files: Optional[list[UploadFile]]) -> tuple[Optional[str], list[str]]:
    if not files:
        return None, []

    source_blocks = []
    empty_source_files = []
    for file in files:
        source_text = await extract_source_context(file)
        if source_text and source_text.strip():
            source_blocks.append(f"Source file: {file.filename}\n{source_text}")
        else:
            empty_source_files.append(file.filename or "Uploaded file")

    source_context = "\n\n---\n\n".join(source_blocks) if source_blocks else None
    return source_context, empty_source_files


def source_text_layer_error_message(file_names: list[str]) -> str:
    return " ".join(f'"{file_name}" has no encrypted text layer.' for file_name in file_names)


def source_text_layer_error_events(message: str):
    async def event_generator():
        yield f"data: {json.dumps({'status': 'error', 'message': message, 'progress': 0})}\n\n"

    return event_generator()


def log_extracted_source_context(files: Optional[list[UploadFile]], source_context: Optional[str]) -> None:
    if not files:
        return

    file_names = ", ".join(file.filename or "unnamed file" for file in files)
    extracted_text = source_context or "[No text extracted from uploaded source files.]"

    print("\n========== CHALKSMITH SOURCE UPLOAD DEBUG ==========", flush=True)
    print(f"Files: {file_names}", flush=True)
    print(f"Extracted characters: {len(source_context or '')}", flush=True)
    print("---------- Extracted source text begins ----------", flush=True)
    print(extracted_text, flush=True)
    print("---------- Extracted source text ends ------------", flush=True)
    print("====================================================\n", flush=True)


def lesson_generation_events(
    *,
    topic: str,
    model: str,
    format: str,
    req: Request,
    session: Session,
    x_user_id: Optional[str],
    lesson_id: Optional[str] = None,
    prompt: Optional[str] = None,
    source_context: Optional[str] = None,
):
    async def event_generator():
        # Queue bridges synchronous executor threads with the async SSE generator
        queue = asyncio.Queue()

        def status_callback(msg, prog):
            # Synchronous callback for the executor to push updates thread-safely
            loop.call_soon_threadsafe(queue.put_nowait, (msg, prog))

        try:
            yield f"data: {json.dumps({'status': 'initializing', 'message': 'Initializing generation...', 'progress': 10})}\n\n"
            await asyncio.sleep(0.1)

            previous_code = None
            active_topic = topic
            if lesson_id:
                yield f"data: {json.dumps({'status': 'loading_context', 'message': 'Loading previous lesson context...', 'progress': 15})}\n\n"
                db_lesson = get_lesson_for_user(session, lesson_id, x_user_id)
                if not db_lesson:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Lesson not found'})}\n\n"
                    return

                previous_code = db_lesson.code
                if not active_topic:
                    active_topic = db_lesson.topic

            if source_context:
                yield f"data: {json.dumps({'status': 'loading_context', 'message': 'Using uploaded source context...', 'progress': 20})}\n\n"

            yield f"data: {json.dumps({'status': 'generating', 'message': f'Chalksmith is thinking about {active_topic}...', 'progress': 30})}\n\n"

            loop = asyncio.get_event_loop()
            lesson = await loop.run_in_executor(
                None,
                lambda: generate_lesson(
                    active_topic,
                    model,
                    format,
                    previous_code=previous_code,
                    edit_prompt=prompt,
                    source_context=source_context,
                )
            )

            if await req.is_disconnected():
                print("Client disconnected after LLM generation. Aborting.")
                return

            yield f"data: {json.dumps({'status': 'rendering', 'message': f'Rendering {format} assets...', 'progress': 60})}\n\n"

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

            try:
                while not render_task.done():
                    if await req.is_disconnected():
                        print(f"Client disconnected during {format} rendering. Cancelling task.")
                        render_task.cancel()
                        try:
                            await asyncio.wait_for(render_task, timeout=2.0)
                        except (asyncio.CancelledError, asyncio.TimeoutError):
                            pass
                        return

                    try:
                        msg, prog = await asyncio.wait_for(queue.get(), timeout=0.1)
                        yield f"data: {json.dumps({'status': 'rendering', 'message': msg, 'progress': prog})}\n\n"
                    except asyncio.TimeoutError:
                        continue

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

            yield f"data: {json.dumps({'status': 'finalizing', 'message': 'Saving lesson to database...', 'progress': 95})}\n\n"

            db_lesson = create_lesson_record(
                session,
                user_id=x_user_id,
                topic=active_topic,
                model=model,
                format=format,
                url=file_url,
                code=lesson["code"],
                summary=lesson["summary"]
            )

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

    return event_generator()

@router.delete("/lesson/{lesson_id}")
async def delete_lesson(
    lesson_id: str,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Delete the lesson from the database and remove its associated physical file
    db_lesson = get_lesson_for_user(session, lesson_id, x_user_id)

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

    delete_lesson_record(session, db_lesson)

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

    db_lesson = update_lesson_title(session, lesson_id, x_user_id, new_title)
    if not db_lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

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
    return StreamingResponse(
        lesson_generation_events(
            topic=topic,
            model=model,
            format=format,
            lesson_id=lesson_id,
            prompt=prompt,
            req=req,
            session=session,
            x_user_id=x_user_id,
        ),
        media_type="text/event-stream",
    )


@router.post("/lesson/generate")
async def generate_lesson_stream_with_source(
    req: Request,
    topic: str = Form(...),
    model: str = Form(...),
    format: str = Form(...),
    lesson_id: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    source: Optional[list[UploadFile]] = File(None),
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    source_context, empty_source_files = await extract_combined_source_context(source)
    log_extracted_source_context(source, source_context)

    if empty_source_files:
        return StreamingResponse(
            source_text_layer_error_events(source_text_layer_error_message(empty_source_files)),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        lesson_generation_events(
            topic=topic,
            model=model,
            format=format,
            lesson_id=lesson_id,
            prompt=prompt,
            req=req,
            session=session,
            x_user_id=x_user_id,
            source_context=source_context,
        ),
        media_type="text/event-stream",
    )

@router.get("/lesson/{lesson_id}")
async def get_lesson_by_id(
    lesson_id: str,
    req: Request,
    session: Session = Depends(get_session),
    x_chalksmith_secret: Optional[str] = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    # Retrieve a specific lesson by its unique ID, used for loading lessons from dashboard links
    db_lesson = get_lesson_for_user(session, lesson_id, x_user_id)

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
        db_lesson = get_lesson_for_user(session, request.lesson_id, x_user_id)
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

    db_lesson = create_lesson_record(
        session,
        user_id=x_user_id,
        topic=request.topic,
        model=request.model,
        format=request.format,
        url=file_url,
        code=lesson["code"],
        summary=lesson["summary"]
    )

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
    db_lesson = get_lesson_by_details(session, topic, model, format, x_user_id)

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
    session: Session = Depends(get_session),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    q: Optional[str] = None,
    format: Optional[str] = None,
):
    db_lessons = search_user_lessons(session, x_user_id, q, format)

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
    db_lesson = get_lesson_for_user(session, id, x_user_id)

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
