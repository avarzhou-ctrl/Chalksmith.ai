from openai import AsyncOpenAI

from backend.app.integrations.llm.base import LLMProviderError, LLMResult, LLMSource


class DeepSeekProvider:
    """DeepSeek speaks the OpenAI wire format on /chat/completions only, so this
    provider cannot reuse the Responses API call in openai.py."""

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

    async def generate(self, prompt: str, sources: tuple[LLMSource, ...] = ()) -> LLMResult:
        if sources:
            raise LLMProviderError("The configured DeepSeek model does not support source files.")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
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
            raise LLMProviderError(
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
