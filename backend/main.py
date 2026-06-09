import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
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

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Allowed origins for development (localhost) and production
load_dotenv(os.path.join(current_dir, ".env.local"))

def _parse_origins(value: str) -> list[str]:
    # CORS origin matching is exact, so normalize trailing slashes from env values.
    return [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]

default_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

origins = list(dict.fromkeys([
    *default_origins,
    *_parse_origins(os.getenv("FRONTEND_ORIGINS", "")),
    *_parse_origins(os.getenv("FRONTEND_URL", "")),
]))

origin_regex = os.getenv("FRONTEND_ORIGIN_REGEX") or None

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(content.router, prefix="/content")
