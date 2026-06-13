import uuid
from typing import Optional

from sqlmodel import Session, desc, select

from backend.models import Lesson, User


def get_lesson_for_user(session: Session, lesson_id: str, user_id: Optional[str]):
    return session.exec(
        select(Lesson).where(Lesson.id == lesson_id, Lesson.user_id == user_id)
    ).first()


def get_lesson_by_details(
    session: Session,
    topic: str,
    model: str,
    format: str,
    user_id: Optional[str],
):
    return session.exec(
        select(Lesson)
        .where(
            Lesson.topic == topic,
            Lesson.model == model,
            Lesson.format == format,
            Lesson.user_id == user_id,
        )
        .order_by(desc(Lesson.created_at))
    ).first()


def get_user_lessons(session: Session, user_id: Optional[str]):
    """Fetches records ensuring strict tenant isolation."""
    return session.exec(
        select(Lesson)
        .where(Lesson.user_id == user_id)
        .order_by(desc(Lesson.created_at))
    ).all()


def ensure_user_exists(session: Session, user_id: Optional[str]):
    if not user_id:
        return None

    user = session.get(User, user_id)
    if user:
        return user

    user = User(id=user_id, email=f"pending_{user_id}@chalksmith.ai")
    session.add(user)
    return user


def create_lesson_record(
    session: Session,
    *,
    user_id: Optional[str],
    topic: str,
    model: str,
    format: str,
    url: str,
    code: str,
    summary: str,
):
    ensure_user_exists(session, user_id)
    db_lesson = Lesson(
        id=str(uuid.uuid4()),
        user_id=user_id,
        topic=topic,
        model=model,
        format=format,
        url=url,
        code=code,
        summary=summary,
    )

    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)
    return db_lesson


def update_lesson_title(
    session: Session,
    lesson_id: str,
    user_id: Optional[str],
    title: str,
):
    db_lesson = get_lesson_for_user(session, lesson_id, user_id)
    if not db_lesson:
        return None

    db_lesson.topic = title
    session.add(db_lesson)
    session.commit()
    session.refresh(db_lesson)
    return db_lesson


def delete_lesson_record(session: Session, db_lesson: Lesson):
    session.delete(db_lesson)
    session.commit()
