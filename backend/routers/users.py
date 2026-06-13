from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlmodel import Session
from backend.crud.users import sync_clerk_user
from backend.database import get_session
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

    try:
        print(f"WEBHOOK RECEIVED: Processing user {payload.id} ({payload.email})")
        user, sync_status = sync_clerk_user(db, payload.id, payload.email)
    except Exception as e:
        db.rollback()
        print(f"WEBHOOK ERROR: Failed to commit user {payload.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database commit failed")

    if sync_status == "updated":
        print(f"WEBHOOK UPDATE: Updated email for {payload.id} to {payload.email}")
        return {"status": "success", "message": "User email updated.", "user_id": user.id}

    if sync_status == "existing":
        print(f"WEBHOOK SKIP: User {payload.id} already synchronized.")
        return {"message": "User already synchronized."}

    print(f"WEBHOOK SUCCESS: User {payload.id} registered.")
    return {"status": "success", "user_id": user.id}
