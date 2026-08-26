from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session

from backend.app.api.schemas import FolderCreate, FolderResponse, FolderUpdate
from backend.app.core.errors import AppError
from backend.app.db.folders import (
    delete_leaf_folder,
    get_owned_folder,
    has_child_folders,
    list_owned_folders,
    sibling_name_exists,
)
from backend.app.db.models import LessonFolder, utc_now
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user

router = APIRouter(prefix="/v2/folders", tags=["folders"])


def _owned_or_404(session: Session, folder_id: UUID, owner_id: str) -> LessonFolder:
    folder = get_owned_folder(session, folder_id, owner_id)
    if folder is None:
        raise AppError(code="folder_not_found", message="Folder not found.", status_code=404)
    return folder


def _clean_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise AppError(code="folder_name_required", message="A folder name is required.", status_code=422)
    return cleaned


def _ensure_unique_name(
    session: Session,
    owner_id: str,
    parent_id: UUID | None,
    name: str,
    *,
    excluding_id: UUID | None = None,
) -> None:
    if sibling_name_exists(
        session,
        owner_id,
        parent_id,
        name,
        excluding_id=excluding_id,
    ):
        raise AppError(
            code="folder_name_conflict",
            message="A folder with this name already exists here.",
            status_code=409,
        )


@router.get("", response_model=list[FolderResponse])
def list_folders(
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    return list_owned_folders(session, user.uid)


@router.post("", response_model=FolderResponse, status_code=201)
def create_folder(
    create: FolderCreate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    if create.parent_id is not None:
        _owned_or_404(session, create.parent_id, user.uid)
    name = _clean_name(create.name)
    _ensure_unique_name(session, user.uid, create.parent_id, name)
    folder = LessonFolder(owner_id=user.uid, parent_id=create.parent_id, name=name)
    session.add(folder)
    session.commit()
    session.refresh(folder)
    return folder


@router.patch("/{folder_id}", response_model=FolderResponse)
def rename_folder(
    folder_id: UUID,
    update: FolderUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    folder = _owned_or_404(session, folder_id, user.uid)
    name = _clean_name(update.name)
    _ensure_unique_name(
        session,
        user.uid,
        folder.parent_id,
        name,
        excluding_id=folder.id,
    )
    folder.name = name
    folder.updated_at = utc_now()
    session.add(folder)
    session.commit()
    session.refresh(folder)
    return folder


@router.delete("/{folder_id}", status_code=204)
def remove_folder(
    folder_id: UUID,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
) -> Response:
    folder = _owned_or_404(session, folder_id, user.uid)
    if has_child_folders(session, folder):
        raise AppError(
            code="folder_has_children",
            message="Delete or move this folder's subfolders first.",
            status_code=409,
        )
    delete_leaf_folder(session, folder)
    return Response(status_code=204)
