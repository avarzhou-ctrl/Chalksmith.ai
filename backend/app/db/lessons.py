from uuid import UUID

from sqlmodel import Session, col, select

from backend.app.db.models import Lesson, utc_now


def create_lesson(session: Session, *, owner_id: str, topic: str, lesson_format: str) -> Lesson:
    lesson = Lesson(owner_id=owner_id, topic=topic, format=lesson_format)
    session.add(lesson)
    session.commit()
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
    statement = select(Lesson).where(Lesson.owner_id == owner_id)
    if query:
        statement = statement.where(col(Lesson.topic).ilike(f"%{query.strip()}%"))
    if lesson_format:
        statement = statement.where(Lesson.format == lesson_format)
    statement = statement.order_by(col(Lesson.updated_at).desc())
    return list(session.exec(statement).all())


def save_lesson(session: Session, lesson: Lesson) -> Lesson:
    lesson.updated_at = utc_now()
    session.add(lesson)
    session.commit()
    session.refresh(lesson)
    return lesson


def delete_lesson(session: Session, lesson: Lesson) -> None:
    session.delete(lesson)
    session.commit()
