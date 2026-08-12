from functools import lru_cache
from urllib.parse import quote_plus

from sqlalchemy.pool import StaticPool
from fastapi import Request
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
    return create_engine(url, **options)


@lru_cache
def get_engine():
    return create_database_engine(get_settings())


def create_db_and_tables(engine=None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())


def get_session(request: Request):
    with Session(request.app.state.engine) as session:
        yield session
