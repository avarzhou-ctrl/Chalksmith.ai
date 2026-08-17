import asyncio
from time import monotonic
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.app.api.dependencies import get_renderers, get_request_settings
from backend.app.api.schemas import LessonFormat
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.lessons import get_owned_lesson
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.llm import get_llm_provider
from backend.app.integrations.llm.base import LLMProvider
from backend.app.integrations.storage import Storage, get_storage
from backend.app.lessons.generation import GenerationService
from backend.app.lessons.render.base import Renderer
from backend.app.lessons.sources import extract_sources

router = APIRouter(prefix="/v2/generations", tags=["generations"])


@router.post("")
async def generate_lesson(
    request: Request,
    topic: Annotated[str, Form(min_length=1, max_length=500)],
    format: Annotated[LessonFormat, Form()],
    base_lesson_id: Annotated[UUID | None, Form()] = None,
    edit_instruction: Annotated[str | None, Form(max_length=500)] = None,
    sources: Annotated[list[UploadFile] | None, File()] = None,
    user: AuthUser = Depends(get_current_user),
    # The service uses this session after the endpoint returns, inside the SSE stream.
    session: Session = Depends(get_session, scope="request"),
    settings: Settings = Depends(get_request_settings),
    llm: LLMProvider = Depends(get_llm_provider),
    storage: Storage = Depends(get_storage),
    renderers: dict[str, Renderer] = Depends(get_renderers),
) -> StreamingResponse:
    if base_lesson_id and not edit_instruction:
        raise AppError(
            code="edit_instruction_required",
            message="An edit instruction is required when editing a lesson.",
            status_code=422,
        )
    if not topic.strip():
        raise AppError(code="topic_required", message="A lesson topic is required.", status_code=422)
    if base_lesson_id:
        base_lesson = get_owned_lesson(session, base_lesson_id, user.uid)
        if (
            base_lesson
            and base_lesson.format == "slides"
            and base_lesson.lesson_spec is None
        ):
            raise AppError(
                code="legacy_lesson_read_only",
                message="Legacy Slides lessons are read-only. Create a new Slides lesson instead.",
                status_code=409,
            )
    deadline = monotonic() + settings.generation_timeout_seconds
    try:
        documents = await asyncio.wait_for(
            extract_sources(sources or [], settings),
            timeout=max(0, deadline - monotonic()),
        )
    except TimeoutError as error:
        raise AppError(
            code="generation_timeout",
            message="Lesson generation timed out. Please try again.",
            status_code=504,
        ) from error
    service = GenerationService(
        session=session,
        llm=llm,
        storage=storage,
        renderers=renderers,
        deadline=deadline,
        request_id=request.state.request_id,
    )
    return StreamingResponse(
        service.stream(
            owner_id=user.uid,
            topic=topic.strip(),
            lesson_format=format,
            sources=documents,
            base_lesson_id=base_lesson_id,
            edit_instruction=edit_instruction,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
