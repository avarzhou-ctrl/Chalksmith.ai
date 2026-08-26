import asyncio
from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from backend.app.integrations.llm.base import LLMImage, LLMProviderError, LLMResult, LLMStreamChunk


class VertexGeminiProvider:
    supports_images = True

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        timeout_seconds: int,
        max_output_tokens: int,
    ) -> None:
        self.client = genai.Client(vertexai=True, project=project, location=location)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str, images: tuple[LLMImage, ...] = ()) -> LLMResult:
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=_contents(prompt, images),
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
                provider="vertex",
                model=self.model,
                input_tokens=getattr(usage, "prompt_token_count", None),
                output_tokens=_billed_output_tokens(usage),
            )
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error

    async def stream(
        self,
        prompt: str,
        images: tuple[LLMImage, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                responses = await self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=_contents(prompt, images),
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=self.max_output_tokens,
                    ),
                )
                async for response in responses:
                    usage = response.usage_metadata
                    yield LLMStreamChunk(
                        text=response.text or "",
                        provider="vertex",
                        model=self.model,
                        input_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=_billed_output_tokens(usage),
                    )
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error


def _contents(prompt: str, images: tuple[LLMImage, ...]):
    if not images:
        return prompt
    parts = [types.Part.from_text(text=prompt)]
    for image in images:
        parts.append(types.Part.from_text(text=f"Source image: {image.filename}"))
        parts.append(types.Part.from_bytes(data=image.data, mime_type=image.media_type))
    return parts


def _billed_output_tokens(usage: object) -> int | None:
    candidates = getattr(usage, "candidates_token_count", None)
    thoughts = getattr(usage, "thoughts_token_count", None)
    if candidates is None and thoughts is None:
        return None
    return (candidates or 0) + (thoughts or 0)
