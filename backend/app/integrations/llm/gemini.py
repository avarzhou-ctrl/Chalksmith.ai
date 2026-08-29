import asyncio
from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from backend.app.integrations.llm.base import (
    LLMProviderError,
    LLMResult,
    LLMSource,
    LLMStreamChunk,
    ProviderTruncationError,
)


class VertexGeminiProvider:
    supports_sources = True

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

    async def generate(self, prompt: str, sources: tuple[LLMSource, ...] = ()) -> LLMResult:
        try:
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model,
                    contents=_contents(prompt, sources),
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=self.max_output_tokens,
                    ),
                ),
                timeout=self.timeout_seconds,
            )
            _raise_if_truncated(response, self.max_output_tokens)
            usage = response.usage_metadata
            return LLMResult(
                text=response.text or "",
                provider="vertex",
                model=self.model,
                input_tokens=getattr(usage, "prompt_token_count", None),
                output_tokens=_billed_output_tokens(usage),
            )
        except ProviderTruncationError:
            raise
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error

    async def stream(
        self,
        prompt: str,
        sources: tuple[LLMSource, ...] = (),
    ) -> AsyncIterator[LLMStreamChunk]:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                responses = await self.client.aio.models.generate_content_stream(
                    model=self.model,
                    contents=_contents(prompt, sources),
                    config=types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=self.max_output_tokens,
                    ),
                )
                async for response in responses:
                    _raise_if_truncated(response, self.max_output_tokens)
                    usage = response.usage_metadata
                    yield LLMStreamChunk(
                        text=response.text or "",
                        provider="vertex",
                        model=self.model,
                        input_tokens=getattr(usage, "prompt_token_count", None),
                        output_tokens=_billed_output_tokens(usage),
                    )
        except ProviderTruncationError:
            raise
        except Exception as error:
            raise LLMProviderError(f"Gemini request failed: {error}") from error


def _contents(prompt: str, sources: tuple[LLMSource, ...]):
    if not sources:
        return prompt
    parts = [types.Part.from_text(text=prompt)]
    for source in sources:
        source_kind = "document" if source.media_type == "application/pdf" else "image"
        parts.append(types.Part.from_text(text=f"Source {source_kind}: {source.filename}"))
        parts.append(types.Part.from_bytes(data=source.data, mime_type=source.media_type))
    return parts


def _billed_output_tokens(usage: object) -> int | None:
    candidates = getattr(usage, "candidates_token_count", None)
    thoughts = getattr(usage, "thoughts_token_count", None)
    if candidates is None and thoughts is None:
        return None
    return (candidates or 0) + (thoughts or 0)


def _raise_if_truncated(response: object, max_output_tokens: int) -> None:
    # Surface provider truncation before partial text can be mistaken for repairable formatting.
    candidates = getattr(response, "candidates", None) or ()
    finish_reason = getattr(candidates[0], "finish_reason", None) if candidates else None
    if str(finish_reason).upper().endswith("MAX_TOKENS"):
        raise ProviderTruncationError(
            f"Gemini hit the {max_output_tokens}-token output limit before finishing."
        )
