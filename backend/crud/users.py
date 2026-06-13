from sqlmodel import Session

from backend.models import User

def sync_clerk_user(session: Session, user_id: str, email: str):
    existing_user = session.get(User, user_id)
    if existing_user:
        if existing_user.email != email:
            existing_user.email = email
            session.add(existing_user)
            session.commit()
            session.refresh(existing_user)
            return existing_user, "updated"

        return existing_user, "existing"

    new_user = User(id=user_id, email=email)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user, "created"
