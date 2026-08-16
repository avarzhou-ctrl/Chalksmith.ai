"""Shared renderer contracts and result types."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class RenderedAsset:
    path: Path
    content_type: str
    extension: str


class Renderer(Protocol):
    async def render(self, code: str, workdir: Path) -> RenderedAsset: ...


class RenderError(RuntimeError):
    pass
