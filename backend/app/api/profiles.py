from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.api.schemas import ProfileUpdate, PublicProfileResponse
from backend.app.core.errors import AppError
from backend.app.db.profiles import (
    get_profile_by_owner,
    get_public_profile,
    save_user_profile,
)
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user

private_router = APIRouter(prefix="/v2/profile", tags=["profile"])
public_router = APIRouter(prefix="/v2/profiles", tags=["profiles"])


@private_router.get("", response_model=PublicProfileResponse)
def get_my_profile(
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    profile = get_profile_by_owner(session, user.uid)
    if profile is None:
        raise AppError(code="profile_not_found", message="Profile not found.", status_code=404)
    return profile


@private_router.put("", response_model=PublicProfileResponse)
def update_my_profile(
    update: ProfileUpdate,
    user: AuthUser = Depends(get_current_user),
    session: Session = Depends(get_session, scope="function"),
):
    display_name = update.display_name.strip()
    if not display_name:
        raise AppError(
            code="profile_name_required",
            message="A public display name is required.",
            status_code=422,
        )
    return save_user_profile(
        session,
        owner_id=user.uid,
        display_name=display_name,
        bio=update.bio.strip(),
    )


@public_router.get("/{profile_id}", response_model=PublicProfileResponse)
def get_profile(
    profile_id: UUID,
    session: Session = Depends(get_session, scope="function"),
):
    profile = get_public_profile(session, profile_id)
    if profile is None:
        raise AppError(code="profile_not_found", message="Profile not found.", status_code=404)
    return profile
