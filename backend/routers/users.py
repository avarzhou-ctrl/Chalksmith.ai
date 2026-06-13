from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlmodel import Session
from backend.database import get_session
from backend.models import User
from pydantic import BaseModel
import os

router = APIRouter()

class UserRegisterPayload(BaseModel):
    id: str
    email: str

@router.post("/register")
async def register_new_clerk_user(
    payload: UserRegisterPayload,
    x_chalksmith_secret: str = Header(None, alias="X-Chalksmith-Secret"),
    db: Session = Depends(get_session)
):
    # Enforce secure server-to-server connection
    INTERNAL_SECRET = os.environ.get("INTERNAL_BACKEND_SECRET")

    if not INTERNAL_SECRET:
        print("WEBHOOK AUTH CONFIG ERROR: INTERNAL_BACKEND_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Webhook auth is not configured")

    if not x_chalksmith_secret or x_chalksmith_secret != INTERNAL_SECRET:
        print("WEBHOOK AUTH FAILURE: Invalid X-Chalksmith-Secret header.")
        raise HTTPException(status_code=403, detail="Forbidden")

    if not payload.id or not payload.email:
        print(f"WEBHOOK ERROR: Missing id or email in payload: {payload}")
        raise HTTPException(status_code=400, detail="Missing id or email")

    print(f"WEBHOOK RECEIVED: Processing user {payload.id} ({payload.email})")
    # Check if user already exists
    existing_user = db.get(User, payload.id)
    if existing_user:
        # Update email if it changed
        if existing_user.email != payload.email:
            print(f"WEBHOOK UPDATE: Updating email for {payload.id} to {payload.email}")
            existing_user.email = payload.email
            db.add(existing_user)
            db.commit()
            db.refresh(existing_user)
            return {"status": "success", "message": "User email updated.", "user_id": existing_user.id}
        
        print(f"WEBHOOK SKIP: User {payload.id} already synchronized.")
        return {"message": "User already synchronized."}

    # Create the new user record in Neon Postgres
    print(f"WEBHOOK CREATE: Creating new user {payload.id}")
    new_user = User(
        id=payload.id,
        email=payload.email
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"WEBHOOK SUCCESS: User {payload.id} registered.")
    except Exception as e:
        print(f"WEBHOOK ERROR: Failed to commit user {payload.id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database commit failed")
    
    return {"status": "success", "user_id": new_user.id}
