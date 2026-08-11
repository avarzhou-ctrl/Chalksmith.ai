import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_FRONTEND_ORIGINS = (
    "http://localhost:3000",
    "https://chalksmith.ai",
    "https://www.chalksmith.ai",
    "https://app.chalksmith.ai",
)


class Settings(BaseModel):
    """Single validated configuration boundary for the v2 backend."""

    model_config = ConfigDict(frozen=True)

    app_env: Literal["local", "test", "staging", "production"] = "local"
    app_role: Literal["api", "renderer"] = "api"
    frontend_origins: tuple[str, ...] = DEFAULT_FRONTEND_ORIGINS
    gcp_project_id: str | None = None
    identity_platform_project_id: str | None = None

    llm_provider: Literal["gemini", "openai"] = "gemini"
    llm_model: str | None = None
    llm_timeout_seconds: int = Field(default=120, gt=0)
    llm_max_output_tokens: int = Field(default=16_384, gt=0)
    gemini_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None

    cloud_sql_instance: str | None = None
    database_url: str | None = None
    database_name: str | None = None
    database_user: str | None = None
    database_password: SecretStr | None = None
    gcs_bucket: str | None = None
    gcs_signer_service_account: str | None = None
    signed_url_ttl_seconds: int = Field(default=900, gt=0)

    generation_timeout_seconds: int = Field(default=900, gt=0)
    manim_timeout_seconds: int = Field(default=600, gt=0)
    max_render_bytes: int = Field(default=100_000_000, gt=0)
    manim_renderer_url: str | None = None
    max_source_files: int = Field(default=5, gt=0)
    max_source_bytes: int = Field(default=10_000_000, gt=0)
    max_total_source_bytes: int = Field(default=25_000_000, gt=0)
    max_source_characters: int = Field(default=120_000, gt=0)
    auto_create_tables: bool = True

    @field_validator("frontend_origins")
    @classmethod
    def validate_frontend_origins(cls, origins: tuple[str, ...]) -> tuple[str, ...]:
        invalid = [origin for origin in origins if not origin.startswith(("http://", "https://"))]
        if invalid:
            raise ValueError("FRONTEND_ORIGINS must contain absolute HTTP(S) origins")
        return tuple(dict.fromkeys(origins))

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.app_env != "production" or self.app_role == "renderer":
            return self
        required = {
            "IDENTITY_PLATFORM_PROJECT_ID": self.identity_platform_project_id,
            "LLM_MODEL": self.llm_model,
            "GCS_BUCKET": self.gcs_bucket,
            "GCS_SIGNER_SERVICE_ACCOUNT": self.gcs_signer_service_account,
            "MANIM_RENDERER_URL": self.manim_renderer_url,
        }
        if self.llm_provider == "gemini":
            required["GEMINI_API_KEY"] = self.gemini_api_key
        else:
            required["OPENAI_API_KEY"] = self.openai_api_key
        if not self.database_url:
            required.update(
                {
                    "CLOUD_SQL_INSTANCE": self.cloud_sql_instance,
                    "DATABASE_NAME": self.database_name,
                    "DATABASE_USER": self.database_user,
                    "DATABASE_PASSWORD": self.database_password,
                }
            )
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing production configuration: {', '.join(missing)}")
        if self.manim_renderer_url and not self.manim_renderer_url.startswith("https://"):
            raise ValueError("MANIM_RENDERER_URL must use HTTPS in production")
        if any(not origin.startswith("https://") for origin in self.frontend_origins):
            raise ValueError("FRONTEND_ORIGINS must use HTTPS in production")
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        # Local development reads one file; deployed services receive environment variables.
        load_dotenv(BACKEND_DIR / ".env.local")

        origins = _csv_env("FRONTEND_ORIGINS") or DEFAULT_FRONTEND_ORIGINS
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            app_role=os.getenv("APP_ROLE", "api"),
            frontend_origins=origins,
            gcp_project_id=os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
            identity_platform_project_id=os.getenv("IDENTITY_PLATFORM_PROJECT_ID")
            or os.getenv("GCP_PROJECT_ID")
            or os.getenv("GOOGLE_CLOUD_PROJECT"),
            llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
            llm_model=os.getenv("LLM_MODEL"),
            llm_timeout_seconds=os.getenv("LLM_TIMEOUT_SECONDS", "120"),
            llm_max_output_tokens=os.getenv("LLM_MAX_OUTPUT_TOKENS", "16384"),
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            cloud_sql_instance=os.getenv("CLOUD_SQL_INSTANCE"),
            database_url=os.getenv("DATABASE_URL"),
            database_name=os.getenv("DATABASE_NAME"),
            database_user=os.getenv("DATABASE_USER"),
            database_password=os.getenv("DATABASE_PASSWORD"),
            gcs_bucket=os.getenv("GCS_BUCKET"),
            gcs_signer_service_account=os.getenv("GCS_SIGNER_SERVICE_ACCOUNT"),
            signed_url_ttl_seconds=os.getenv("SIGNED_URL_TTL_SECONDS", "900"),
            generation_timeout_seconds=os.getenv("GENERATION_TIMEOUT_SECONDS", "900"),
            manim_timeout_seconds=os.getenv("MANIM_TIMEOUT_SECONDS", "600"),
            max_render_bytes=os.getenv("MAX_RENDER_BYTES", "100000000"),
            manim_renderer_url=os.getenv("MANIM_RENDERER_URL"),
            max_source_files=os.getenv("MAX_SOURCE_FILES", "5"),
            max_source_bytes=os.getenv("MAX_SOURCE_BYTES", "10000000"),
            max_total_source_bytes=os.getenv("MAX_TOTAL_SOURCE_BYTES", "25000000"),
            max_source_characters=os.getenv("MAX_SOURCE_CHARACTERS", "120000"),
            auto_create_tables=_bool_env("AUTO_CREATE_TABLES", True),
        )


def _csv_env(name: str) -> tuple[str, ...]:
    raw_value = os.getenv(name, "")
    return tuple(value.strip().rstrip("/") for value in raw_value.split(",") if value.strip())


def _bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
