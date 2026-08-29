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


class GeneratedCodeError(RenderError):
    """The model-authored lesson is invalid but can be repaired and validated again."""


class PolicyViolationError(RenderError):
    """The model-authored lesson violates a security policy and must be rejected."""


class ArtifactLimitError(RenderError):
    """The lesson exceeded a platform render time or artifact-size limit."""


class InfrastructureRenderError(RenderError):
    """The rendering service failed independently of the generated lesson code."""
