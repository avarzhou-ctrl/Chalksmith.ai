from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.api.dependencies import get_request_settings
from backend.app.api.lesson_access import sign_lesson_access
from backend.app.api.schemas import AccessURLResponse, PublishedLessonItem
from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.db.lessons import get_published_lesson, list_published_lessons
from backend.app.db.session import get_session
from backend.app.integrations.storage import Storage, get_storage

router = APIRouter(prefix="/v2/explore", tags=["explore"])


@router.get("/lessons", response_model=list[PublishedLessonItem])
def list_public_lessons(
    session: Session = Depends(get_session, scope="function"),
):
    return list_published_lessons(session)


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
