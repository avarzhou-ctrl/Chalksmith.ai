from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


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
    async def generate(self, prompt: str) -> LLMResult: ...


@runtime_checkable
class StreamingLLMProvider(Protocol):
    def stream(self, prompt: str) -> AsyncIterator[LLMStreamChunk]: ...


class LLMProviderError(RuntimeError):
    pass
