from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LLMSource:
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
    supports_sources: bool

    async def generate(
        self,
        prompt: str,
        sources: tuple[LLMSource, ...] = (),
    ) -> LLMResult: ...


@runtime_checkable
class StreamingLLMProvider(LLMProvider, Protocol):
    def stream(
        self,
        prompt: str,
        sources: tuple[LLMSource, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]: ...


class LLMProviderError(RuntimeError):
    pass


class LLMOutputLimitError(LLMProviderError):
    """The provider stopped because the configured model output budget was exhausted."""
