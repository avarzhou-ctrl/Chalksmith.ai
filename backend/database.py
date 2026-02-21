import os
from sqlmodel import create_engine, Session, SQLModel

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sqlite_url = f"sqlite:///{os.path.join(BACKEND_DIR, 'lessons.db')}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session