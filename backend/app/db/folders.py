from uuid import UUID

from sqlmodel import Session, col, select

from backend.app.db.models import Lesson, LessonFolder, utc_now


def get_owned_folder(session: Session, folder_id: UUID, owner_id: str) -> LessonFolder | None:
    return session.exec(
        select(LessonFolder).where(
            LessonFolder.id == folder_id,
            LessonFolder.owner_id == owner_id,
        )
    ).first()


def list_owned_folders(session: Session, owner_id: str) -> list[LessonFolder]:
    return list(
        session.exec(
            select(LessonFolder)
            .where(LessonFolder.owner_id == owner_id)
            .order_by(col(LessonFolder.name))
        ).all()
    )


def sibling_name_exists(
    session: Session,
    owner_id: str,
    parent_id: UUID | None,
    name: str,
    *,
    excluding_id: UUID | None = None,
) -> bool:
    statement = select(LessonFolder.id).where(
        LessonFolder.owner_id == owner_id,
        LessonFolder.name == name,
    )
    if parent_id is None:
        statement = statement.where(LessonFolder.parent_id.is_(None))
    else:
        statement = statement.where(LessonFolder.parent_id == parent_id)
    if excluding_id is not None:
        statement = statement.where(LessonFolder.id != excluding_id)
    return session.exec(statement).first() is not None


def has_child_folders(session: Session, folder: LessonFolder) -> bool:
    return session.exec(
        select(LessonFolder.id).where(
            LessonFolder.owner_id == folder.owner_id,
            LessonFolder.parent_id == folder.id,
        )
    ).first() is not None


def delete_leaf_folder(session: Session, folder: LessonFolder) -> None:
    roots = list(
        session.exec(
            select(Lesson).where(
                Lesson.owner_id == folder.owner_id,
                Lesson.id == Lesson.root_lesson_id,
                Lesson.folder_id == folder.id,
            )
        ).all()
    )
    updated_at = utc_now()
    for root in roots:
        root.folder_id = folder.parent_id
        root.updated_at = updated_at
    session.add_all(roots)
    session.delete(folder)
    session.commit()
