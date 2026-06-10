import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel
from backend.routers import content
from backend.database import create_db_and_tables
from backend.services.fetch_docs import fetch_manim_reference

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

app = FastAPI(lifespan=lifespan)

# Use absolute path for static assets for deployment and runtime stability
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Check if static directory is writable
if not os.access(static_dir, os.W_OK):
    print(f"CRITICAL: Static directory {static_dir} is NOT writable. File generation will fail.")
else:
    print(f"SUCCESS: Static directory {static_dir} is writable.")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Allowed origins for development (localhost) and production.
load_dotenv(os.path.join(current_dir, ".env.local"))

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

app.include_router(content.router, prefix="/content")

INTERNAL_SECRET = os.environ.get("INTERNAL_BACKEND_SECRET")

class GenerationRequest(BaseModel):
    prompt: str

@app.post("/lesson")
async def process_generation(
    payload: GenerationRequest, 
    x_chalksmith_secret: str = Header(None, alias="X-Chalksmith-Secret"),
    x_user_id: str = Header(None, alias="X-User-Id")
):
    # Confirm the request came directly from your secure Vercel server instance
    if not x_chalksmith_secret or x_chalksmith_secret != INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Direct unverified access pathways blocked."
        )
        
    print(True, f"Securely processing request for user: {x_user_id}")
    return {"status": "success", "engine_output": "Vector data compiled successfully."}