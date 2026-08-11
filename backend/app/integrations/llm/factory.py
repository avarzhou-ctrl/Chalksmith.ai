from fastapi import Request

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.integrations.llm.base import LLMProvider
from backend.app.integrations.llm.gemini import GeminiProvider
from backend.app.integrations.llm.openai import OpenAIProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if not settings.llm_model:
        raise AppError(code="llm_not_configured", message="LLM_MODEL is not configured.", status_code=503)
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise AppError(code="llm_not_configured", message="GEMINI_API_KEY is not configured.", status_code=503)
        return GeminiProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
        )
    if not settings.openai_api_key:
        raise AppError(code="llm_not_configured", message="OPENAI_API_KEY is not configured.", status_code=503)
    return OpenAIProvider(
        api_key=settings.openai_api_key.get_secret_value(),
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        max_output_tokens=settings.llm_max_output_tokens,
    )


def get_llm_provider(request: Request) -> LLMProvider:
    if not hasattr(request.app.state, "llm_provider"):
        request.app.state.llm_provider = create_llm_provider(request.app.state.settings)
    return request.app.state.llm_provider
