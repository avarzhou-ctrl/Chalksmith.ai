from fastapi import APIRouter, Request
from pydantic import BaseModel

from backend.app.core.config import Settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str


@router.get("/healthz", response_model=HealthResponse)
async def healthcheck(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        environment=settings.app_env,
        version=request.app.version,
    )
