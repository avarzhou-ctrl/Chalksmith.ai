import base64

from openai import AsyncOpenAI

from backend.app.integrations.llm.base import (
    LLMOutputLimitError,
    LLMProviderError,
    LLMResult,
    LLMSource,
)


class OpenAIProvider:
    supports_sources = True

    def __init__(self, *, api_key: str, model: str, timeout_seconds: int, max_output_tokens: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str, sources: tuple[LLMSource, ...] = ()) -> LLMResult:
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=_input(prompt, sources),
                max_output_tokens=self.max_output_tokens,
            )
            incomplete = getattr(response, "incomplete_details", None)
            if (
                getattr(response, "status", None) == "incomplete"
                and getattr(incomplete, "reason", None) == "max_output_tokens"
            ):
                raise LLMOutputLimitError(
                    f"OpenAI hit the {self.max_output_tokens}-token output limit before finishing."
                )
            usage = response.usage
            return LLMResult(
                text=response.output_text,
                provider="openai",
                model=self.model,
                input_tokens=getattr(usage, "input_tokens", None),
                output_tokens=getattr(usage, "output_tokens", None),
            )
        except LLMOutputLimitError:
            raise
        except Exception as error:
            raise LLMProviderError(f"OpenAI request failed: {error}") from error


def _input(prompt: str, sources: tuple[LLMSource, ...]):
    if not sources:
        return prompt
    content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
    for source in sources:
        encoded = base64.b64encode(source.data).decode("ascii")
        if source.media_type == "application/pdf":
            content.append({"type": "input_text", "text": f"Source document: {source.filename}"})
            content.append(
                {
                    "type": "input_file",
                    "filename": source.filename,
                    "file_data": f"data:{source.media_type};base64,{encoded}",
                }
            )
        else:
            content.append({"type": "input_text", "text": f"Source image: {source.filename}"})
            content.append(
                {
                    "type": "input_image",
                    "image_url": f"data:{source.media_type};base64,{encoded}",
                    "detail": "auto",
                }
            )
    return [{"role": "user", "content": content}]
