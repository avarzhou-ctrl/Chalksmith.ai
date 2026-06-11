import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlmodel import create_engine, Session, SQLModel
# Import models here to register them with SQLModel.metadata
from backend.models import Lesson, User

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
    ensure_lesson_user_id_column()

def ensure_lesson_user_id_column():
    inspector = inspect(engine)
    if "lesson" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("lesson")}
    if "user_id" in columns:
        return

    with engine.begin() as connection:
        # Existing lessons cannot be safely assigned to a user automatically.
        connection.execute(text("ALTER TABLE lesson ADD COLUMN user_id VARCHAR"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_lesson_user_id ON lesson (user_id)"))

# Dependency for managing sessions per API request
def get_session():
    with Session(engine) as session:
        yield session
