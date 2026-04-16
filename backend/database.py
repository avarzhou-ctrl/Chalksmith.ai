import os
from sqlmodel import create_engine, Session, SQLModel

# Using SQLite for local development as it is self-contained and zero-config
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(BACKEND_DIR, 'lessons.db')}"

# check_same_thread=False required for FastAPI multi-threaded requests
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    # Initializes database schema on server startup
    SQLModel.metadata.create_all(engine)

def get_session():
    # Provides a clean database session dependency for API routers
    with Session(engine) as session:
        yield session