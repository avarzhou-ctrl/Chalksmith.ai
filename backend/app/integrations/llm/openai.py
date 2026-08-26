import base64

from openai import AsyncOpenAI

from backend.app.integrations.llm.base import LLMImage, LLMProviderError, LLMResult


class OpenAIProvider:
    supports_images = True

    def __init__(self, *, api_key: str, model: str, timeout_seconds: int, max_output_tokens: int) -> None:
        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens

    async def generate(self, prompt: str, images: tuple[LLMImage, ...] = ()) -> LLMResult:
        try:
            response = await self.client.responses.create(
                model=self.model,
                input=_input(prompt, images),
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


def _input(prompt: str, images: tuple[LLMImage, ...]):
    if not images:
        return prompt
    content: list[dict[str, str]] = [{"type": "input_text", "text": prompt}]
    for image in images:
        content.append({"type": "input_text", "text": f"Source image: {image.filename}"})
        encoded = base64.b64encode(image.data).decode("ascii")
        content.append(
            {
                "type": "input_image",
                "image_url": f"data:{image.media_type};base64,{encoded}",
                "detail": "auto",
            }
        )
    return [{"role": "user", "content": content}]
