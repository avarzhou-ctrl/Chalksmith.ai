from uuid import UUID

from sqlmodel import Session, select

from backend.app.db.models import UserProfile, utc_now


def get_profile_by_owner(session: Session, owner_id: str) -> UserProfile | None:
    return session.exec(
        select(UserProfile).where(UserProfile.owner_id == owner_id)
    ).first()


def get_public_profile(session: Session, profile_id: UUID) -> UserProfile | None:
    return session.get(UserProfile, profile_id)


def ensure_user_profile(
    session: Session,
    *,
    owner_id: str,
    display_name: str,
) -> UserProfile:
    profile = get_profile_by_owner(session, owner_id)
    if profile is None:
        profile = UserProfile(owner_id=owner_id, display_name=display_name)
        session.add(profile)
    return profile


def save_user_profile(
    session: Session,
    *,
    owner_id: str,
    display_name: str,
    bio: str,
) -> UserProfile:
    profile = get_profile_by_owner(session, owner_id)
    if profile is None:
        profile = UserProfile(
            owner_id=owner_id,
            display_name=display_name,
            bio=bio,
        )
    else:
        profile.display_name = display_name
        profile.bio = bio
        profile.updated_at = utc_now()
    session.add(profile)
    session.commit()
    if session.expire_on_commit:
        session.refresh(profile)
    return profile
