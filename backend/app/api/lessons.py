from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlmodel import Session

from backend.app.api.dependencies import get_request_settings
from backend.app.api.schemas import (
    AccessURLResponse,
    FinalLessonResponse,
    LessonFormat,
    LessonFolderUpdate,
    LessonListItem,
    LessonPublicationResponse,
    LessonPublicationUpdate,
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
    set_final_lesson,
    set_lesson_publication,
)
from backend.app.db.folders import get_owned_folder
from backend.app.db.session import get_session
from backend.app.db.profiles import ensure_user_profile
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.storage import Storage, get_storage
from backend.app.lessons.access import sign_lesson_access

router = APIRouter(prefix="/v2/lessons", tags=["lessons"])


def _owned_or_404(session: Session, lesson_id: UUID, owner_id: str):
    lesson = get_owned_lesson(session, lesson_id, owner_id)
    if lesson is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    return lesson


def _lesson_response(session: Session, lesson) -> LessonResponse:
    root = get_lesson_root(session, lesson)
    if root is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    return LessonResponse.model_validate(lesson).model_copy(
        update={
            "is_published": root.published_at is not None,
            "published_at": root.published_at,
            "folder_id": root.folder_id,
        }
    )


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
            update={
                "version_count": version_counts.get(lesson.root_lesson_id, 0),
                "is_published": lesson.is_published,
            }
        )
        for lesson in lessons
    ]


@router.get("/{lesson_id}", response_model=LessonResponse)
def get_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    return _lesson_response(session, _owned_or_404(session, lesson_id, user.uid))


@router.get("/{lesson_id}/versions", response_model=list[LessonVersionResponse])
def get_lesson_versions(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson = _owned_or_404(session, lesson_id, user.uid)
    return list_lesson_version_summaries(session, lesson)


@router.put("/{lesson_id}/final", response_model=FinalLessonResponse)
def select_final_lesson(
    lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
) -> FinalLessonResponse:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    if lesson.status != "ready":
        raise AppError(
            code="lesson_not_ready",
            message="Only a ready lesson version can be selected as final.",
            status_code=409,
        )
    root = set_final_lesson(session, lesson)
    return FinalLessonResponse(
        root_lesson_id=root.id,
        final_lesson_id=lesson.id,
    )


@router.put("/{lesson_id}/publication", response_model=LessonPublicationResponse)
def update_lesson_publication(
    lesson_id: UUID,
    update: LessonPublicationUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
) -> LessonPublicationResponse:
    lesson = _owned_or_404(session, lesson_id, user.uid)
    if update.published and (lesson.status != "ready" or not lesson.object_key):
        raise AppError(
            code="lesson_not_ready",
            message="Only a ready lesson version can be published.",
            status_code=409,
        )
    if update.published:
        display_name = (update.display_name or "Chalksmith creator").strip()
        ensure_user_profile(
            session,
            owner_id=user.uid,
            display_name=display_name or "Chalksmith creator",
        )
    root = set_lesson_publication(session, lesson, update.published)
    return LessonPublicationResponse(
        root_lesson_id=root.id,
        lesson_id=lesson.id,
        is_published=root.published_at is not None,
        published_at=root.published_at,
    )


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
    return _lesson_response(session, lesson)


@router.put("/{lesson_id}/folder", response_model=LessonResponse)
def move_lesson_to_folder(
    lesson_id: UUID,
    update: LessonFolderUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson = _owned_or_404(session, lesson_id, user.uid)
    root = get_lesson_root(session, lesson)
    if root is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    if update.folder_id is not None:
        if get_owned_folder(session, update.folder_id, user.uid) is None:
            raise AppError(code="folder_not_found", message="Folder not found.", status_code=404)
    root.folder_id = update.folder_id
    save_lessons(session, [root])
    return _lesson_response(session, lesson)


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
    # Signing can call IAM over the network; do not reserve a scarce DB
    # connection while that independent operation is in flight.
    session.close()
    return sign_lesson_access(lesson, download=download, storage=storage, settings=settings)
