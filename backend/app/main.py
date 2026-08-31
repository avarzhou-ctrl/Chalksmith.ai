from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.explore import router as explore_router
from backend.app.api.folders import router as folders_router
from backend.app.api.generations import router as generations_router
from backend.app.api.health import router as health_router
from backend.app.api.lessons import router as lessons_router
from backend.app.api.lesson_sets import router as lesson_sets_router
from backend.app.api.local_storage import router as local_storage_router
from backend.app.api.profiles import private_router as private_profile_router
from backend.app.api.profiles import public_router as public_profiles_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import (
    AppError,
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
)
from backend.app.core.logging import RequestLoggingMiddleware, configure_logging
from backend.app.db.session import create_database_engine, create_db_and_tables


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging()
    engine = create_database_engine(active_settings)

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        if active_settings.auto_create_tables:
            create_db_and_tables(engine)
        yield

    application = FastAPI(
        title="Chalksmith API",
        version="2.0.0",
        description="Generate code-driven teaching materials.",
        lifespan=lifespan,
    )
    application.state.settings = active_settings
    application.state.engine = engine
    application.add_exception_handler(AppError, app_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.add_exception_handler(Exception, unhandled_error_handler)
    application.add_middleware(RequestLoggingMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(active_settings.frontend_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(health_router)
    application.include_router(generations_router)
    application.include_router(lessons_router)
    application.include_router(lesson_sets_router)
    application.include_router(folders_router)
    application.include_router(explore_router)
    application.include_router(private_profile_router)
    application.include_router(public_profiles_router)
    if active_settings.local_storage_dir:
        application.include_router(local_storage_router)
    return application


app = create_app()
