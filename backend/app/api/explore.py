from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from backend.app.api.dependencies import get_request_settings
from backend.app.api.schemas import (
    AccessURLResponse,
    LessonFormat,
    PublishedLessonItem,
    PublishedTagItem,
)
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.lessons import (
    get_published_lesson,
    list_published_lessons,
    list_published_tag_summaries,
    list_tags_for_roots,
    normalize_lesson_tags,
)
from backend.app.db.session import get_session
from backend.app.integrations.storage import Storage, get_storage
from backend.app.lessons.access import sign_lesson_access

router = APIRouter(prefix="/v2/explore", tags=["explore"])


@router.get("/lessons", response_model=list[PublishedLessonItem])
def list_public_lessons(
    q: str | None = Query(default=None, max_length=200),
    format: LessonFormat | None = None,
    tag: list[str] | None = Query(default=None),
    session: Session = Depends(get_session, scope="function"),
):
    try:
        tags = [label for label, _ in normalize_lesson_tags(tag or [])]
    except ValueError as error:
        raise AppError(code="invalid_tags", message=str(error), status_code=422) from error
    lessons = list_published_lessons(
        session,
        query=q.strip() if q and q.strip() else None,
        lesson_format=format,
        tags=tags,
    )
    tags_by_root = list_tags_for_roots(
        session,
        [lesson.root_lesson_id for lesson in lessons],
    )
    return [
        PublishedLessonItem.model_validate(lesson).model_copy(
            update={"tags": tags_by_root.get(lesson.root_lesson_id, [])}
        )
        for lesson in lessons
    ]


@router.get("/tags", response_model=list[PublishedTagItem])
def list_public_tags(
    session: Session = Depends(get_session, scope="function"),
):
    return list_published_tag_summaries(session)


@router.post("/lessons/{lesson_id}/access-url", response_model=AccessURLResponse)
def create_public_access_url(
    lesson_id: UUID,
    download: bool = False,
    session: Session = Depends(get_session, scope="function"),
    storage: Storage = Depends(get_storage),
    settings: Settings = Depends(get_request_settings),
) -> AccessURLResponse:
    lesson = get_published_lesson(session, lesson_id)
    if lesson is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    # Signing may call IAM; release the DB connection before external work.
    session.close()
    return sign_lesson_access(lesson, download=download, storage=storage, settings=settings)
