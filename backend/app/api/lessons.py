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
    LessonVersionResponse,
)
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.lessons import (
    count_lesson_versions,
    get_owned_lesson,
    get_lesson_root,
    list_lesson_version_summaries,
    list_lesson_versions,
    list_owned_lessons,
    save_lessons,
)
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.storage import Storage, get_storage

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
    session: Session = Depends(get_session, scope="function"),
):
    lessons = list_owned_lessons(session, user.uid, query=q, lesson_format=format)
    version_counts = count_lesson_versions(
        session,
        user.uid,
        [lesson.root_lesson_id for lesson in lessons],
    )
    return [
        LessonListItem.model_validate(lesson).model_copy(
            update={"version_count": version_counts.get(lesson.root_lesson_id, 0)}
        )
        for lesson in lessons
    ]


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    return _owned_or_404(session, lesson_id, user.uid)


@router.get("/{lesson_id}/versions", response_model=list[LessonVersionResponse])
def get_lesson_versions(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson = _owned_or_404(session, lesson_id, user.uid)
    return list_lesson_version_summaries(session, lesson)


@router.patch("/{lesson_id}", response_model=LessonResponse)
def update_lesson(
    lesson_id: UUID,
    update: LessonUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
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
    root = get_lesson_root(session, lesson)
    if root is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    versions = list_lesson_versions(session, root)
    for version in versions:
        version.topic = topic
    save_lessons(session, versions)
    return lesson


@router.delete("/{lesson_id}", status_code=204)
def remove_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
    storage: Storage = Depends(get_storage),
) -> Response:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    root = get_lesson_root(session, lesson)
    if root is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    versions = list_lesson_versions(session, root)
    # A retryable storage/DB failure must never leave a ready record pointing at a missing file.
    for version in versions:
        version.status = "deleting"
    save_lessons(session, versions)
    for version in versions:
        try:
            storage.delete_prefix(f"sources/{user.uid}/{version.id}/")
        except Exception as error:
            raise AppError(
                code="storage_delete_failed",
                message="The lesson source files could not be deleted.",
                status_code=503,
            ) from error
        if version.object_key:
            try:
                storage.delete(version.object_key)
            except Exception as error:
                raise AppError(
                    code="storage_delete_failed",
                    message="The lesson file could not be deleted.",
                    status_code=503,
                ) from error
    for version in versions:
        session.delete(version)
    session.commit()
    return Response(status_code=204)


@router.post("/{lesson_id}/access-url", response_model=AccessURLResponse)
def create_access_url(
    lesson_id: UUID,
    download: bool = False,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
    storage: Storage = Depends(get_storage),
    settings: Settings = Depends(get_request_settings),
) -> AccessURLResponse:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    if lesson.status != "ready" or not lesson.object_key:
        raise AppError(code="lesson_not_ready", message="Lesson output is not ready.", status_code=409)
    extension = Path(lesson.object_key).suffix
    safe_topic = re.sub(r"[^\w .()-]", "_", lesson.topic, flags=re.UNICODE).strip()[:80]
    download_name = f"{safe_topic or 'chalksmith-lesson'}{extension}" if download else None
    object_key = lesson.object_key
    # Signing can call IAM over the network; do not reserve a scarce DB
    # connection while that independent operation is in flight.
    session.close()
    try:
        url = storage.signed_url(object_key, download_name=download_name)
    except Exception as error:
        raise AppError(
            code="signed_url_failed",
            message="A temporary lesson URL could not be created.",
            status_code=503,
        ) from error
    return AccessURLResponse(url=url, expires_in=settings.signed_url_ttl_seconds)
