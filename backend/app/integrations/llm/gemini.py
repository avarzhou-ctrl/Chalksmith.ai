import asyncio

from google import genai
from google.genai import types

from backend.app.integrations.llm.base import LLMProviderError, LLMResult


class GeminiProvider:
    def __init__(self, *, api_key: str, model: str, timeout_seconds: int, max_output_tokens: int) -> None:
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str) -> LLMResult:
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=self.max_output_tokens,
                    ),
                ),
                timeout=self.timeout_seconds,
            )
            usage = response.usage_metadata
            return LLMResult(
                text=response.text or "",
                provider="gemini",
                model=self.model,
                input_tokens=getattr(usage, "prompt_token_count", None),
                output_tokens=getattr(usage, "candidates_token_count", None),
            )
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error
