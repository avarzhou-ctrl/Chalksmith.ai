import base64

import pymupdf
from openai import AsyncOpenAI

from backend.app.integrations.llm.base import (
    LLMOutputLimitError,
    LLMProviderError,
    LLMResult,
    LLMSource,
)

VISION_MODEL = "deepseek-v4-flash-vision-exp"
MAX_PDF_PAGES = 50
MAX_INLINE_SOURCE_BYTES = 32 * 1024 * 1024


class DeepSeekProvider:
    """DeepSeek's OpenAI-compatible chat endpoint with image/PDF source support."""

    supports_sources = False

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: int,
        max_output_tokens: int,
        thinking: bool = False,
    ) -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=timeout_seconds)
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.thinking = thinking
        self.supports_sources = model == VISION_MODEL

    async def generate(self, prompt: str, sources: tuple[LLMSource, ...] = ()) -> LLMResult:
        if sources and not self.supports_sources:
            raise LLMProviderError(
                "DeepSeek source files require the deepseek-v4-flash-vision-exp model."
            )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": _content(prompt, sources)}],
                max_tokens=self.max_output_tokens,
                # DeepSeek enables thinking at high effort by default and bills the
                # chain of thought against max_tokens while returning it in a
                # separate reasoning_content field. Generation asks for one strictly
                # formatted answer, so that budget belongs to the answer itself.
                extra_body={"thinking": {"type": "enabled" if self.thinking else "disabled"}},
            )
        except Exception as error:
            raise LLMProviderError(f"DeepSeek request failed: {error}") from error

        choice = response.choices[0]
        # A truncated answer parses as a malformed lesson much later, which reads as
        # a model formatting failure rather than an exhausted token budget.
        if choice.finish_reason == "length":
            raise LLMOutputLimitError(
                f"DeepSeek hit the {self.max_output_tokens}-token output limit before finishing. "
                "Raise LLM_MAX_OUTPUT_TOKENS, or lower the requested lesson's scope."
            )
        usage = response.usage
        return LLMResult(
            text=choice.message.content or "",
            provider="deepseek",
            model=self.model,
            input_tokens=getattr(usage, "prompt_tokens", None),
            output_tokens=getattr(usage, "completion_tokens", None),
        )


def _content(prompt: str, sources: tuple[LLMSource, ...]) -> str | list[dict[str, object]]:
    """Build OpenAI-compatible content blocks for DeepSeek Vision."""
    if not sources:
        return prompt

    content: list[dict[str, object]] = [{"type": "text", "text": prompt}]
    inline_source_bytes = 0
    for source in sources:
        if source.media_type == "application/pdf":
            pdf_content, pdf_bytes = _pdf_content(source, MAX_INLINE_SOURCE_BYTES - inline_source_bytes)
            content.extend(pdf_content)
            inline_source_bytes += pdf_bytes
            continue
        if not source.media_type.startswith("image/"):
            raise LLMProviderError(f"Unsupported DeepSeek source type: {source.media_type}")
        inline_source_bytes += len(source.data)
        if inline_source_bytes > MAX_INLINE_SOURCE_BYTES:
            raise LLMProviderError("DeepSeek source images exceed the 32 MiB inline request limit.")
        encoded = base64.b64encode(source.data).decode("ascii")
        content.extend(
            (
                {"type": "text", "text": f"Source image: {source.filename}"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{source.media_type};base64,{encoded}",
                        "detail": "auto",
                    },
                },
            )
        )
    return content


def _pdf_content(source: LLMSource, byte_budget: int) -> tuple[list[dict[str, object]], int]:
    """Render PDF pages as JPEGs so DeepSeek Vision can inspect text and diagrams."""
    try:
        document = pymupdf.open(stream=source.data, filetype="pdf")
    except Exception as error:
        raise LLMProviderError(f"Could not read PDF source {source.filename}: {error}") from error

    content: list[dict[str, object]] = []
    rendered_bytes = 0
    try:
        for page_number, page in enumerate(document, start=1):
            if page_number > MAX_PDF_PAGES:
                raise LLMProviderError(
                    f"PDF source {source.filename} exceeds the {MAX_PDF_PAGES}-page limit."
                )
            text = page.get_text("text").strip()
            page_label = f"Source PDF: {source.filename}, page {page_number}"
            if text:
                content.append({"type": "text", "text": f"{page_label}\n{text}"})

            # Rendering the page also handles scanned PDFs and preserves diagrams.
            image = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).tobytes(
                "jpeg", jpg_quality=85
            )
            rendered_bytes += len(image)
            if rendered_bytes > byte_budget:
                raise LLMProviderError(
                    f"Rendered PDF source {source.filename} exceeds the 32 MiB inline request limit."
                )
            encoded = base64.b64encode(image).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded}",
                        "detail": "auto",
                    },
                }
            )
    finally:
        document.close()
    return content, rendered_bytes
