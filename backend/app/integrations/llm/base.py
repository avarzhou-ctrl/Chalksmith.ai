from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMImage:
    filename: str
    media_type: str
    data: bytes


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class LLMStreamChunk:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    supports_images: bool

    async def generate(
        self,
        prompt: str,
        images: tuple[LLMImage, ...] = (),
    ) -> LLMResult: ...


@runtime_checkable
class StreamingLLMProvider(Protocol):
    def stream(
        self,
        prompt: str,
        images: tuple[LLMImage, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]: ...


class LLMProviderError(RuntimeError):
    pass
