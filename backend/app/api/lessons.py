import asyncio
import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session

from backend.app.api.dependencies import get_request_settings
from backend.app.api.schemas import (
    AccessURLResponse,
    LessonFormat,
    LessonListItem,
    LessonResponse,
    LessonUpdate,
)
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.lessons import (
    delete_lesson,
    get_owned_lesson,
    list_owned_lessons,
    save_lesson,
)
from backend.app.db.session import get_session
from backend.app.integrations.identity import AuthUser, get_current_user
from backend.app.integrations.storage import GCSStorage, get_storage

router = APIRouter(prefix="/v2/lessons", tags=["lessons"])


def _owned_or_404(session: Session, lesson_id: UUID, owner_id: str):
    lesson = get_owned_lesson(session, lesson_id, owner_id)
    if lesson is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    return lesson


@router.get("", response_model=list[LessonListItem])
def list_lessons(
    q: str | None = Query(default=None, max_length=200),
    format: LessonFormat | None = None,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return list_owned_lessons(session, user.uid, query=q, lesson_format=format)


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return _owned_or_404(session, lesson_id, user.uid)


@router.patch("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: UUID,
    update: LessonUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    lesson = _owned_or_404(session, lesson_id, user.uid)
    if lesson.status == "deleting":
        raise AppError(
            code="lesson_deleting",
            message="The lesson is pending deletion and cannot be renamed.",
            status_code=409,
        )
    topic = update.topic.strip()
    if not topic:
        raise AppError(code="topic_required", message="A lesson topic is required.", status_code=422)
    lesson.topic = topic
    return save_lesson(session, lesson)


@router.delete("/{lesson_id}", status_code=204)
async def remove_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
    storage: GCSStorage = Depends(get_storage),
) -> Response:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    # A retryable storage/DB failure must never leave a ready record pointing at a missing file.
    lesson.status = "deleting"
    save_lesson(session, lesson)
    try:
        await asyncio.to_thread(storage.delete_prefix, f"sources/{user.uid}/{lesson.id}/")
    except Exception as error:
        raise AppError(
            code="storage_delete_failed",
            message="The lesson source files could not be deleted.",
            status_code=503,
        ) from error
    if lesson.object_key:
        try:
            await asyncio.to_thread(storage.delete, lesson.object_key)
        except Exception as error:
            raise AppError(
                code="storage_delete_failed",
                message="The lesson file could not be deleted.",
                status_code=503,
            ) from error
    delete_lesson(session, lesson)
    return Response(status_code=204)


@router.post("/{lesson_id}/access-url", response_model=AccessURLResponse)
async def create_access_url(
    lesson_id: UUID,
    download: bool = False,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session),
    storage: GCSStorage = Depends(get_storage),
    settings: Settings = Depends(get_request_settings),
) -> AccessURLResponse:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    if lesson.status != "ready" or not lesson.object_key:
        raise AppError(code="lesson_not_ready", message="Lesson output is not ready.", status_code=409)
    extension = Path(lesson.object_key).suffix
    safe_topic = re.sub(r"[^\w .()-]", "_", lesson.topic, flags=re.UNICODE).strip()[:80]
    download_name = f"{safe_topic or 'chalksmith-lesson'}{extension}" if download else None
    try:
        url = await asyncio.to_thread(
            storage.signed_url,
            lesson.object_key,
            download_name=download_name,
        )
    except Exception as error:
        raise AppError(
            code="signed_url_failed",
            message="A temporary lesson URL could not be created.",
            status_code=503,
        ) from error
    return AccessURLResponse(url=url, expires_in=settings.signed_url_ttl_seconds)
