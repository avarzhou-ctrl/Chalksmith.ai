import os
from typing import Optional
from fastapi import HTTPException, status
from sqlmodel import Session
from backend.models import User, current_usage_month

FREE_MONTHLY_LIMIT = 20

# Checks backend secret from frontend
def validate_internal_request(secret: Optional[str]) -> None:
    expected_secret = os.environ.get("INTERNAL_BACKEND_SECRET")
    if expected_secret and secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Direct unverified access pathways blocked.",
        )

def get_user_or_404(session: Session, user_id: Optional[str]) -> User:
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Rest user's counter
    month = current_usage_month()
    if user.usage_month != month:
        user.usage_month = month
        user.monthly_used = 0
        session.add(user)
        session.commit()
        session.refresh(user)

    return user

# Finds user, resets usage if new month, blocks free users at 20 lessons
def ensure_can_create_lesson(session: Session, user_id: Optional[str]) -> User:
    user = get_user_or_404(session, user_id)
    if user.subscription == "free" and user.monthly_used >= FREE_MONTHLY_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Generation limit of 20 per month reached. Upgrade to Pro for more generations!",
        )

    return user

# Increments monthly usage
def record_new_lesson_usage(session: Session, user_id: str) -> User:
    user = get_user_or_404(session, user_id)
    user.monthly_used += 1
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
