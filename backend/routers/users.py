from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlmodel import Session
from backend.database import get_session
from backend.models import User
from pydantic import BaseModel
import os

router = APIRouter()
INTERNAL_SECRET = os.environ.get("INTERNAL_BACKEND_SECRET")

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
    if not x_chalksmith_secret or x_chalksmith_secret != INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")

    # Check if user already exists
    existing_user = db.get(User, payload.id)
    if existing_user:
        return {"message": "User already synchronized."}

    # Create the new user record in Neon Postgres
    new_user = User(
        id=payload.id,
        email=payload.email,
        subscription="free",
        monthly_used=0
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"status": "success", "user_id": new_user.id}
