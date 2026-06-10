import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlmodel import create_engine, Session, SQLModel
# Import models here to register them with SQLModel.metadata
from backend.models import Lesson, User, current_usage_month

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env.local")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is required to start the backend.")

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL, echo=True)

# Database tables wrapper
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    ensure_usage_month_column()

def ensure_usage_month_column():
    inspector = inspect(engine)
    if "user" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("user")}
    if "usage_month" in columns:
        return

    month = current_usage_month()
    with engine.begin() as connection:
        # create_all does not alter existing tables, so this keeps early Neon prototypes compatible.
        connection.execute(text(f"ALTER TABLE \"user\" ADD COLUMN usage_month VARCHAR DEFAULT '{month}'"))

# Dependency for managing sessions per API request
def get_session():
    with Session(engine) as session:
        yield session
