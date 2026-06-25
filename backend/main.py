import os
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from sqlmodel import Session
from backend.routers import lesson, users, sources
from backend.database import create_db_and_tables, get_session
from backend.services.fetch_docs import fetch_manim_reference

current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env.local"))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized before handling requests
    print("--- CREATING DATABASE AND TABLES ---")
    create_db_and_tables()
    print("--- DATABASE CREATION COMPLETE ---")
    
    # Sync Manim docs to provide LLM with latest API reference to reduce hallucinations
    print("--- SYNCING MANIM DOCS ---")
    fetch_manim_reference()
    
    yield

async def verify_internal_secret(x_chalksmith_secret: str = Header(None, alias="X-Chalksmith-Secret")):
    INTERNAL_SECRET = os.environ.get("INTERNAL_BACKEND_SECRET")
    if not INTERNAL_SECRET:
        print("WEBHOOK AUTH CONFIG ERROR: INTERNAL_BACKEND_SECRET is not configured.")
        raise HTTPException(status_code=500, detail="Webhook auth is not configured")

    if not x_chalksmith_secret or x_chalksmith_secret != INTERNAL_SECRET:
        print("WEBHOOK AUTH FAILURE: Invalid X-Chalksmith-Secret header.")
        raise HTTPException(status_code=403, detail="Forbidden")

app = FastAPI(lifespan=lifespan, dependencies=[Depends(verify_internal_secret)])

# Static files setup for LLM-generated content
static_dir = os.path.join(current_dir, "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

if not os.access(static_dir, os.W_OK):
    print(f"CRITICAL: Static directory {static_dir} is NOT writable. File generation will fail.")
else:
    print(f"SUCCESS: Static directory {static_dir} is writable.")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# CORS setup
default_origins = [
    "http://localhost:3000",
    "https://chalksmith.ai",
    "https://www.chalksmith.ai",
    "https://app.chalksmith.ai",
]
origins = list(dict.fromkeys(default_origins))
origin_regex = r"^https://chalksmith-ai-[a-z0-9-]+\.vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(lesson.router, prefix="/content")
app.include_router(users.router, prefix="/users")
app.include_router(sources.router, prefix="/sources")

class GenerationRequest(BaseModel):
    prompt: str

@app.post("/lesson")
async def process_generation(
    payload: GenerationRequest, 
    x_user_id: str = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_session)
):
    return {"status": "success", "engine_output": "Vector data compiled successfully."}