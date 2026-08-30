from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from backend.app.api.schemas import (
    LessonSetAddLesson,
    LessonSetCreate,
    LessonSetDetail,
    LessonSetListItem,
    LessonSetOrderUpdate,
    LessonSetUpdate,
)
from backend.app.core.errors import AppError
from backend.app.db.lesson_sets import (
    add_lesson_to_set,
    delete_lesson_set,
    get_owned_lesson_set,
    get_owned_lesson_set_for_update,
    list_lesson_set_lessons,
    list_lesson_set_previews,
    list_owned_lesson_sets,
    remove_lesson_from_set,
    reorder_lesson_set,
)
from backend.app.db.lessons import get_lesson_root, get_owned_lesson
from backend.app.db.models import LessonSet, utc_now
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user


router = APIRouter(prefix="/v2/lesson-sets", tags=["lesson-sets"])


def _owned_or_404(
    session: Session,
    lesson_set_id: UUID,
    owner_id: str,
    *,
    for_update: bool = False,
) -> LessonSet:
    lesson_set = (
        get_owned_lesson_set_for_update(session, lesson_set_id, owner_id)
        if for_update
        else get_owned_lesson_set(session, lesson_set_id, owner_id)
    )
    if lesson_set is None:
        raise AppError(
            code="lesson_set_not_found",
            message="Lesson set not found.",
            status_code=404,
        )
    return lesson_set


def _clean_title(title: str) -> str:
    cleaned = title.strip()
    if not cleaned:
        raise AppError(
            code="lesson_set_title_required",
            message="A lesson set title is required.",
            status_code=422,
        )
    return cleaned


def _detail(session: Session, lesson_set: LessonSet) -> LessonSetDetail:
    return LessonSetDetail.model_validate(lesson_set).model_copy(
        update={"lessons": list_lesson_set_lessons(session, lesson_set)}
    )


@router.get("", response_model=list[LessonSetListItem])
def list_lesson_sets(
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_sets = list_owned_lesson_sets(session, user.uid)
    previews = list_lesson_set_previews(
        session,
        [lesson_set.id for lesson_set in lesson_sets],
        user.uid,
    )
    return [
        LessonSetListItem.model_validate(lesson_set).model_copy(
            update={"preview_lessons": previews.get(lesson_set.id, [])}
        )
        for lesson_set in lesson_sets
    ]


@router.post("", response_model=LessonSetDetail, status_code=201)
def create_lesson_set(
    create: LessonSetCreate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_set = LessonSet(
        owner_id=user.uid,
        title=_clean_title(create.title),
        description=create.description.strip(),
    )
    session.add(lesson_set)
    session.commit()
    session.refresh(lesson_set)
    return _detail(session, lesson_set)


@router.get("/{lesson_set_id}", response_model=LessonSetDetail)
def get_lesson_set(
    lesson_set_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    return _detail(session, _owned_or_404(session, lesson_set_id, user.uid))


@router.patch("/{lesson_set_id}", response_model=LessonSetDetail)
def update_lesson_set(
    lesson_set_id: UUID,
    update: LessonSetUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_set = _owned_or_404(session, lesson_set_id, user.uid, for_update=True)
    if update.title is None and update.description is None:
        raise AppError(
            code="lesson_set_update_required",
            message="Provide a title or description to update.",
            status_code=422,
        )
    if update.title is not None:
        lesson_set.title = _clean_title(update.title)
    if update.description is not None:
        lesson_set.description = update.description.strip()
    lesson_set.updated_at = utc_now()
    session.add(lesson_set)
    session.commit()
    session.refresh(lesson_set)
    return _detail(session, lesson_set)


@router.delete("/{lesson_set_id}", status_code=204)
def remove_lesson_set(
    lesson_set_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
) -> Response:
    delete_lesson_set(
        session,
        _owned_or_404(session, lesson_set_id, user.uid, for_update=True),
    )
    return Response(status_code=204)


@router.post("/{lesson_set_id}/lessons", response_model=LessonSetDetail, status_code=201)
def add_lesson(
    lesson_set_id: UUID,
    add: LessonSetAddLesson,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_set = _owned_or_404(session, lesson_set_id, user.uid, for_update=True)
    lesson = get_owned_lesson(session, add.lesson_id, user.uid)
    if lesson is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    root = get_lesson_root(session, lesson)
    if root is None or root.final_lesson_id is None:
        raise AppError(code="lesson_not_found", message="Lesson not found.", status_code=404)
    final = get_owned_lesson(session, root.final_lesson_id, user.uid)
    if final is None or final.status != "ready":
        raise AppError(
            code="lesson_not_ready",
            message="Only a ready lesson can be added to a lesson set.",
            status_code=409,
        )
    try:
        add_lesson_to_set(session, lesson_set, root)
    except ValueError as error:
        if str(error) == "lesson_already_in_set":
            raise AppError(
                code="lesson_already_in_set",
                message="This lesson is already in the lesson set.",
                status_code=409,
            ) from error
        raise AppError(
            code="lesson_set_full",
            message="Lesson sets can contain at most 50 lessons.",
            status_code=409,
        ) from error
    return _detail(session, lesson_set)


@router.delete("/{lesson_set_id}/lessons/{root_lesson_id}", response_model=LessonSetDetail)
def remove_lesson(
    lesson_set_id: UUID,
    root_lesson_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_set = _owned_or_404(session, lesson_set_id, user.uid, for_update=True)
    if not remove_lesson_from_set(session, lesson_set, root_lesson_id):
        raise AppError(
            code="lesson_set_item_not_found",
            message="Lesson not found in this set.",
            status_code=404,
        )
    return _detail(session, lesson_set)


@router.put("/{lesson_set_id}/order", response_model=LessonSetDetail)
def reorder_lessons(
    lesson_set_id: UUID,
    update: LessonSetOrderUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    lesson_set = _owned_or_404(session, lesson_set_id, user.uid, for_update=True)
    if len(update.root_lesson_ids) != len(set(update.root_lesson_ids)):
        raise AppError(
            code="invalid_lesson_set_order",
            message="Lesson order contains duplicate lessons.",
            status_code=422,
        )
    try:
        reorder_lesson_set(session, lesson_set, update.root_lesson_ids)
    except ValueError as error:
        raise AppError(
            code="invalid_lesson_set_order",
            message="Lesson order must contain every lesson in the set exactly once.",
            status_code=422,
        ) from error
    return _detail(session, lesson_set)
