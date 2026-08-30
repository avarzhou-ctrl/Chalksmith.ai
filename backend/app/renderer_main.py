from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.app.core.config import get_settings
from backend.app.lessons.render.base import (
    ArtifactLimitError,
    GeneratedCodeError,
    InfrastructureRenderError,
    PolicyViolationError,
    RenderError,
)
from backend.app.lessons.render.manim import LocalManimRenderer


class RenderRequest(BaseModel):
    code: str = Field(min_length=1, max_length=250_000)


renderer_app = FastAPI(title="Chalksmith Manim Renderer", version="2.0.0")


@renderer_app.get("/ready")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@renderer_app.post("/internal/render/manim")
async def render_manim(payload: RenderRequest):
    settings = get_settings()
    # The response background closes only after FileResponse completes.
    temporary = TemporaryDirectory(prefix="chalksmith-render-")
    renderer = LocalManimRenderer(settings.manim_timeout_seconds, settings.max_render_bytes)
    try:
        asset = await renderer.render(payload.code, Path(temporary.name))
    except RenderError as error:
        temporary.cleanup()
        if isinstance(error, ArtifactLimitError):
            status_code = 504 if "timed out" in str(error).lower() else 413
        elif isinstance(error, InfrastructureRenderError):
            status_code = 503
        else:
            status_code = 422
        error_type = (
            "policy_violation"
            if isinstance(error, PolicyViolationError)
            else "generated_code"
            if isinstance(error, GeneratedCodeError)
            else "render_error"
        )
        raise HTTPException(
            status_code=status_code,
            detail={"error_type": error_type, "message": str(error)},
        ) from error
    response = FileResponse(asset.path, media_type=asset.content_type, filename="lesson.mp4")
    response.background = _CleanupTask(temporary)
    return response


class _CleanupTask:
    def __init__(self, temporary: TemporaryDirectory[str]) -> None:
        self.temporary = temporary

    async def __call__(self) -> None:
        self.temporary.cleanup()
