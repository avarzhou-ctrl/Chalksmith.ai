from openai import AsyncOpenAI

from backend.app.integrations.llm.base import LLMProviderError, LLMResult


class DeepSeekProvider:
    """DeepSeek speaks the OpenAI wire format on /chat/completions only, so this
    provider cannot reuse the Responses API call in openai.py."""

    def __init__(
        self, *, api_key: str, model: str, base_url: str, timeout_seconds: int, max_output_tokens: int
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str) -> LLMResult:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_output_tokens,
            )
            usage = response.usage
            return LLMResult(
                text=response.choices[0].message.content or "",
                provider="deepseek",
                model=self.model,
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            )
        except Exception as error:
            raise LLMProviderError(f"DeepSeek request failed: {error}") from error
