from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlmodel import Session, col, select

from backend.app.db.models import Lesson, utc_now


@dataclass(frozen=True)
class LessonVersionSummary:
    id: UUID
    parent_lesson_id: UUID | None
    version_number: int
    topic: str
    status: str
    summary: str | None
    edit_instruction: str | None
    is_final: bool


def create_lesson(
    session: Session,
    *,
    owner_id: str,
    topic: str,
    lesson_format: str,
    root_lesson_id: UUID | None = None,
    parent_lesson_id: UUID | None = None,
    version_number: int = 1,
    edit_instruction: str | None = None,
) -> Lesson:
    lesson_id = uuid4()
    lesson = Lesson(
        id=lesson_id,
        owner_id=owner_id,
        root_lesson_id=root_lesson_id or lesson_id,
        parent_lesson_id=parent_lesson_id,
        final_lesson_id=lesson_id if root_lesson_id is None else None,
        version_number=version_number,
        topic=topic,
        format=lesson_format,
        edit_instruction=edit_instruction,
    )
    session.add(lesson)
    session.commit()
    if session.expire_on_commit:
        # Direct maintenance/test sessions keep the historical detached-object contract.
        session.refresh(lesson)
    return lesson


def get_owned_lesson(session: Session, lesson_id: UUID, owner_id: str) -> Lesson | None:
    return session.exec(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.owner_id == owner_id)
    ).first()


def list_owned_lessons(
    session: Session,
    owner_id: str,
    *,
    query: str | None = None,
    lesson_format: str | None = None,
) -> list[Lesson]:
    root = aliased(Lesson)
    statement = select(Lesson).join(root, Lesson.id == root.final_lesson_id).where(
        root.owner_id == owner_id,
        root.id == root.root_lesson_id,
        Lesson.owner_id == owner_id,
    )
    if query:
        statement = statement.where(col(Lesson.topic).ilike(f"%{query.strip()}%"))
    if lesson_format:
        statement = statement.where(Lesson.format == lesson_format)
    statement = statement.order_by(col(Lesson.updated_at).desc())
    return list(session.exec(statement).all())


def get_lesson_root(session: Session, lesson: Lesson) -> Lesson | None:
    return get_owned_lesson(session, lesson.root_lesson_id, lesson.owner_id)


def list_lesson_versions(session: Session, lesson: Lesson) -> list[Lesson]:
    return list(
        session.exec(
            select(Lesson)
            .where(Lesson.owner_id == lesson.owner_id, Lesson.root_lesson_id == lesson.root_lesson_id)
            .order_by(col(Lesson.version_number))
        ).all()
    )


def list_lesson_version_summaries(
    session: Session,
    lesson: Lesson,
) -> list[LessonVersionSummary]:
    root = get_lesson_root(session, lesson)
    final_lesson_id = root.final_lesson_id if root else lesson.root_lesson_id
    rows = session.exec(
        select(
            Lesson.id,
            Lesson.parent_lesson_id,
            Lesson.version_number,
            Lesson.topic,
            Lesson.status,
            Lesson.summary,
            Lesson.edit_instruction,
        )
        .where(Lesson.owner_id == lesson.owner_id, Lesson.root_lesson_id == lesson.root_lesson_id)
        .order_by(col(Lesson.version_number))
    ).all()
    return [
        LessonVersionSummary(*row, is_final=row.id == final_lesson_id)
        for row in rows
    ]


def count_lesson_versions(
    session: Session,
    owner_id: str,
    root_lesson_ids: list[UUID],
) -> dict[UUID, int]:
    if not root_lesson_ids:
        return {}
    rows = session.exec(
        select(Lesson.root_lesson_id, func.count(Lesson.id))
        .where(
            Lesson.owner_id == owner_id,
            col(Lesson.root_lesson_id).in_(root_lesson_ids),
        )
        .group_by(Lesson.root_lesson_id)
    ).all()
    return {root_lesson_id: count for root_lesson_id, count in rows}


def next_version_number(session: Session, root_lesson_id: UUID, owner_id: str) -> int:
    # PostgreSQL holds this row lock through create_lesson()'s commit, making
    # MAX+1 allocation serial per lineage. The unique index remains the backstop.
    session.exec(
        select(Lesson.id)
        .where(
            Lesson.id == root_lesson_id,
            Lesson.owner_id == owner_id,
        )
        .with_for_update()
    ).one()
    latest_version = session.exec(
        select(func.max(Lesson.version_number)).where(
            Lesson.owner_id == owner_id,
            Lesson.root_lesson_id == root_lesson_id,
        )
    ).one()
    return (latest_version or 0) + 1


def set_final_lesson(session: Session, lesson: Lesson) -> Lesson:
    root = get_lesson_root(session, lesson)
    if root is None:
        raise ValueError("Lesson root was not found.")
    root.final_lesson_id = lesson.id
    return save_lesson(session, root)


def save_lesson(session: Session, lesson: Lesson) -> Lesson:
    lesson.updated_at = utc_now()
    session.add(lesson)
    session.commit()
    if session.expire_on_commit:
        session.refresh(lesson)
    return lesson


def save_lessons(session: Session, lessons: list[Lesson]) -> list[Lesson]:
    updated_at = utc_now()
    for lesson in lessons:
        lesson.updated_at = updated_at
    session.add_all(lessons)
    session.commit()
    if session.expire_on_commit:
        for lesson in lessons:
            session.refresh(lesson)
    return lessons
