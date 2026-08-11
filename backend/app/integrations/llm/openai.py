from openai import AsyncOpenAI

from backend.app.integrations.llm.base import LLMProviderError, LLMResult


class OpenAIProvider:
    def __init__(self, *, api_key: str, model: str, timeout_seconds: int, max_output_tokens: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str) -> LLMResult:
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=prompt,
                max_output_tokens=self.max_output_tokens,
            )
            usage = response.usage
            return LLMResult(
                text=response.output_text,
                provider="openai",
                model=self.model,
                input_tokens=getattr(usage, "input_tokens", None),
                output_tokens=getattr(usage, "output_tokens", None),
            )
        except Exception as error:
            raise LLMProviderError(f"OpenAI request failed: {error}") from error
