from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, select

from backend.app.db.models import Lesson, LessonSet, LessonSetItem, utc_now


MAX_LESSON_SET_ITEMS = 50


@dataclass(frozen=True)
class LessonSetSummary:
    id: UUID
    title: str
    description: str
    lesson_count: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class LessonSetLessonSummary:
    id: UUID
    root_lesson_id: UUID
    topic: str
    format: str
    status: str
    summary: str | None
    position: int


def get_owned_lesson_set(
    session: Session,
    lesson_set_id: UUID,
    owner_id: str,
) -> LessonSet | None:
    return session.exec(
        select(LessonSet).where(
            LessonSet.id == lesson_set_id,
            LessonSet.owner_id == owner_id,
        )
    ).first()


def get_owned_lesson_set_for_update(
    session: Session,
    lesson_set_id: UUID,
    owner_id: str,
) -> LessonSet | None:
    return session.exec(
        select(LessonSet)
        .where(
            LessonSet.id == lesson_set_id,
            LessonSet.owner_id == owner_id,
        )
        .with_for_update()
    ).first()


def list_owned_lesson_sets(session: Session, owner_id: str) -> list[LessonSetSummary]:
    item_count = (
        select(func.count(LessonSetItem.root_lesson_id))
        .where(LessonSetItem.lesson_set_id == LessonSet.id)
        .correlate(LessonSet)
        .scalar_subquery()
    )
    rows = session.exec(
        select(
            LessonSet.id,
            LessonSet.title,
            LessonSet.description,
            item_count,
            LessonSet.created_at,
            LessonSet.updated_at,
        )
        .where(LessonSet.owner_id == owner_id)
        .order_by(col(LessonSet.updated_at).desc(), col(LessonSet.title))
    ).all()
    return [LessonSetSummary(*row) for row in rows]


def list_lesson_set_lessons(
    session: Session,
    lesson_set: LessonSet,
) -> list[LessonSetLessonSummary]:
    root = aliased(Lesson)
    rows = session.exec(
        select(
            Lesson.id,
            Lesson.root_lesson_id,
            Lesson.topic,
            Lesson.format,
            Lesson.status,
            Lesson.summary,
            LessonSetItem.position,
        )
        .join(root, LessonSetItem.root_lesson_id == root.id)
        .join(Lesson, Lesson.id == root.final_lesson_id)
        .where(
            LessonSetItem.lesson_set_id == lesson_set.id,
            root.owner_id == lesson_set.owner_id,
            root.id == root.root_lesson_id,
            Lesson.owner_id == lesson_set.owner_id,
        )
        .order_by(LessonSetItem.position)
    ).all()
    return [LessonSetLessonSummary(*row) for row in rows]


def list_lesson_set_previews(
    session: Session,
    lesson_set_ids: list[UUID],
    owner_id: str,
    *,
    limit_per_set: int = 3,
) -> dict[UUID, list[LessonSetLessonSummary]]:
    if not lesson_set_ids:
        return {}
    root = aliased(Lesson)
    rows = session.exec(
        select(
            LessonSetItem.lesson_set_id,
            Lesson.id,
            Lesson.root_lesson_id,
            Lesson.topic,
            Lesson.format,
            Lesson.status,
            Lesson.summary,
            LessonSetItem.position,
        )
        .join(root, LessonSetItem.root_lesson_id == root.id)
        .join(Lesson, Lesson.id == root.final_lesson_id)
        .where(
            col(LessonSetItem.lesson_set_id).in_(lesson_set_ids),
            root.owner_id == owner_id,
            root.id == root.root_lesson_id,
            Lesson.owner_id == owner_id,
        )
        .order_by(LessonSetItem.lesson_set_id, LessonSetItem.position)
    ).all()
    previews = {lesson_set_id: [] for lesson_set_id in lesson_set_ids}
    for row in rows:
        lesson_set_id = row[0]
        if len(previews[lesson_set_id]) < limit_per_set:
            previews[lesson_set_id].append(LessonSetLessonSummary(*row[1:]))
    return previews


def add_lesson_to_set(
    session: Session,
    lesson_set: LessonSet,
    root: Lesson,
) -> LessonSetItem:
    existing = session.get(LessonSetItem, (lesson_set.id, root.id))
    if existing is not None:
        raise ValueError("lesson_already_in_set")
    count = session.exec(
        select(func.count(LessonSetItem.root_lesson_id)).where(
            LessonSetItem.lesson_set_id == lesson_set.id
        )
    ).one()
    if count >= MAX_LESSON_SET_ITEMS:
        raise ValueError("lesson_set_full")
    item = LessonSetItem(
        lesson_set_id=lesson_set.id,
        root_lesson_id=root.id,
        position=count,
    )
    lesson_set.updated_at = utc_now()
    session.add(item)
    session.add(lesson_set)
    session.commit()
    session.refresh(item)
    return item


def _resequence_items(session: Session, lesson_set_id: UUID) -> None:
    items = list(
        session.exec(
            select(LessonSetItem)
            .where(LessonSetItem.lesson_set_id == lesson_set_id)
            .order_by(LessonSetItem.position)
        ).all()
    )
    for index, item in enumerate(items):
        item.position = 1_000 + index
    session.add_all(items)
    session.flush()
    for index, item in enumerate(items):
        item.position = index
    session.add_all(items)


def remove_lesson_from_set(
    session: Session,
    lesson_set: LessonSet,
    root_lesson_id: UUID,
) -> bool:
    item = session.get(LessonSetItem, (lesson_set.id, root_lesson_id))
    if item is None:
        return False
    session.delete(item)
    session.flush()
    _resequence_items(session, lesson_set.id)
    lesson_set.updated_at = utc_now()
    session.add(lesson_set)
    session.commit()
    return True


def reorder_lesson_set(
    session: Session,
    lesson_set: LessonSet,
    root_lesson_ids: list[UUID],
) -> None:
    items = list(
        session.exec(
            select(LessonSetItem).where(LessonSetItem.lesson_set_id == lesson_set.id)
        ).all()
    )
    existing = {item.root_lesson_id: item for item in items}
    if len(root_lesson_ids) != len(existing) or set(root_lesson_ids) != set(existing):
        raise ValueError("invalid_lesson_set_order")
    for index, item in enumerate(items):
        item.position = 1_000 + index
    session.add_all(items)
    session.flush()
    for position, root_lesson_id in enumerate(root_lesson_ids):
        existing[root_lesson_id].position = position
    lesson_set.updated_at = utc_now()
    session.add_all([*items, lesson_set])
    session.commit()


def delete_lesson_set(session: Session, lesson_set: LessonSet) -> None:
    items = list(
        session.exec(
            select(LessonSetItem).where(LessonSetItem.lesson_set_id == lesson_set.id)
        ).all()
    )
    for item in items:
        session.delete(item)
    session.delete(lesson_set)
    session.commit()


def remove_lesson_from_all_sets(session: Session, root: Lesson) -> None:
    items = list(
        session.exec(
            select(LessonSetItem).where(LessonSetItem.root_lesson_id == root.id)
        ).all()
    )
    affected_set_ids = {item.lesson_set_id for item in items}
    for item in items:
        session.delete(item)
    session.flush()
    updated_at = utc_now()
    for lesson_set_id in affected_set_ids:
        lesson_set = get_owned_lesson_set(session, lesson_set_id, root.owner_id)
        if lesson_set is None:
            continue
        _resequence_items(session, lesson_set_id)
        lesson_set.updated_at = updated_at
        session.add(lesson_set)
