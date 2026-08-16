from fastapi import Request

from backend.app.core.config import Settings
from backend.app.lessons.render.base import Renderer
from backend.app.lessons.render.html import HTMLRenderer
from backend.app.lessons.render.manim import (
    RemoteManimRenderer,
    UnavailableManimRenderer,
    is_local_renderer_url,
)


def get_request_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_renderers(request: Request) -> dict[str, Renderer]:
    settings: Settings = request.app.state.settings
    manim: Renderer
    if settings.manim_renderer_url:
        manim = RemoteManimRenderer(
            settings.manim_renderer_url,
            settings.manim_timeout_seconds,
            settings.max_render_bytes,
            authenticate=not is_local_renderer_url(settings.manim_renderer_url),
        )
    else:
        # API processes never execute generated Python; local development also uses renderer_main.
        manim = UnavailableManimRenderer()
    return {
        "interactive": HTMLRenderer(required_marker="p5"),
        "slides": HTMLRenderer(required_marker="reveal"),
        "video": manim,
    }
