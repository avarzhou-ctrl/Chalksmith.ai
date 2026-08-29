from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy.pool import StaticPool
from fastapi import Request
from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import AppError


def build_database_url(settings: Settings) -> str:
    if settings.database_url:
        return _psycopg_url(settings.database_url)
    required = (
        settings.cloud_sql_instance,
        settings.database_name,
        settings.database_user,
        settings.database_password,
    )
    if not all(required):
        if settings.app_env in {"local", "test"}:
            return "sqlite:///./.env/chalksmith.local.db"
        raise AppError(
            code="database_not_configured",
            message="Cloud SQL configuration is incomplete.",
            status_code=503,
        )
    password = quote_plus(settings.database_password.get_secret_value())
    return (
        f"postgresql+psycopg://{settings.database_user}:{password}@/"
        f"{settings.database_name}?host=/cloudsql/{settings.cloud_sql_instance}"
    )


def _psycopg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def create_database_engine(settings: Settings):
    url = build_database_url(settings)
    options: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    else:
        # db-f1-micro grants few connections; SQLAlchemy's default 5+10 per process
        # would exhaust them across the deployed instances.
        options |= {"pool_size": 2, "max_overflow": 0}
    return create_engine(url, **options)


@lru_cache
def get_engine():
    return create_database_engine(get_settings())


def create_db_and_tables(engine=None) -> None:
    active_engine = engine or get_engine()
    SQLModel.metadata.create_all(active_engine)
    _migrate_lesson_versions(active_engine)


def _migrate_lesson_versions(engine) -> None:
    """Keep the lightweight local/legacy schema compatible without an ORM migration tool."""
    columns = {column["name"] for column in inspect(engine).get_columns("lessons")}
    dialect = engine.dialect.name
    additions = {
        "root_lesson_id": "UUID" if dialect == "postgresql" else "CHAR(32)",
        "parent_lesson_id": "UUID" if dialect == "postgresql" else "CHAR(32)",
        "final_lesson_id": "UUID" if dialect == "postgresql" else "CHAR(32)",
        "folder_id": "UUID" if dialect == "postgresql" else "CHAR(32)",
        "version_number": "INTEGER NOT NULL DEFAULT 1",
        "edit_instruction": "TEXT",
        "lesson_spec": "TEXT",
        "spec_version": "VARCHAR(64)",
        "runtime_version": "VARCHAR(64)",
        "compiler_version": "VARCHAR(64)",
        "published_at": "TIMESTAMP WITH TIME ZONE" if dialect == "postgresql" else "DATETIME",
        "first_error": "TEXT",
        "repair_error": "TEXT",
        "raw_model_output": "TEXT",
    }
    with engine.begin() as connection:
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(text(f"ALTER TABLE lessons ADD COLUMN {name} {definition}"))
        connection.execute(text("UPDATE lessons SET root_lesson_id = id WHERE root_lesson_id IS NULL"))
        connection.execute(
            text(
                "UPDATE lessons SET final_lesson_id = id "
                "WHERE id = root_lesson_id AND final_lesson_id IS NULL"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lessons_owner_root "
                "ON lessons (owner_id, root_lesson_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lessons_published_at "
                "ON lessons (published_at)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_lessons_folder_id "
                "ON lessons (folder_id)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_lessons_owner_root_version "
                "ON lessons (owner_id, root_lesson_id, version_number)"
            )
        )


def get_session(request: Request):
    # Committed objects stay usable without an implicit refresh that checks a
    # connection back out while an SSE stream waits on external services.
    with Session(request.app.state.engine, expire_on_commit=False) as session:
        yield session
