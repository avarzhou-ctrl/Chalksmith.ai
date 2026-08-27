from fastapi import Request

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.integrations.llm.base import LLMProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    if not settings.llm_model:
        raise AppError(code="llm_not_configured", message="LLM_MODEL is not configured.", status_code=503)
    if settings.llm_provider == "vertex":
        if not settings.gcp_project_id:
            raise AppError(
                code="llm_not_configured",
                message="GCP_PROJECT_ID is not configured for Vertex AI.",
                status_code=503,
            )
        from backend.app.integrations.llm.gemini import VertexGeminiProvider

        return VertexGeminiProvider(
            project=settings.gcp_project_id,
            location=settings.vertex_ai_location,
            model=settings.llm_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
        )
    if settings.llm_provider == "deepseek":
        if not settings.deepseek_api_key:
            raise AppError(code="llm_not_configured", message="DEEPSEEK_API_KEY is not configured.", status_code=503)
        from backend.app.integrations.llm.deepseek import DeepSeekProvider

        return DeepSeekProvider(
            api_key=settings.deepseek_api_key.get_secret_value(),
            model=settings.llm_model,
            base_url=settings.deepseek_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
            max_output_tokens=settings.llm_max_output_tokens,
            thinking=settings.deepseek_thinking,
        )
    if not settings.openai_api_key:
        raise AppError(code="llm_not_configured", message="OPENAI_API_KEY is not configured.", status_code=503)
    from backend.app.integrations.llm.openai import OpenAIProvider

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
