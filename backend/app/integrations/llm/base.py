from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    async def generate(self, prompt: str) -> LLMResult: ...


class LLMProviderError(RuntimeError):
    pass
