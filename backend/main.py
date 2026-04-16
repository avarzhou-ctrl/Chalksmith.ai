import os
from contextlib import asynccontextmanager
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
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(content.router, prefix="/content")