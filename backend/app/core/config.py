import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPOSITORY_DIR = BACKEND_DIR.parent
LOCAL_ENV_FILE = REPOSITORY_DIR / ".env" / ".env.backend.local"
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
    clerk_issuer: str | None = None
    clerk_jwks_url: str | None = None
    clerk_audience: str | None = None
    clerk_authorized_parties: tuple[str, ...] = DEFAULT_FRONTEND_ORIGINS

    llm_provider: Literal["vertex", "openai"] = "vertex"
    llm_model: str | None = None
    llm_timeout_seconds: int = Field(default=120, gt=0)
    llm_max_output_tokens: int = Field(default=16_384, gt=0)
    vertex_ai_location: str = "global"
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

    @field_validator("clerk_issuer")
    @classmethod
    def normalize_clerk_issuer(cls, issuer: str | None) -> str | None:
        if not issuer:
            return None
        if not issuer.startswith("https://"):
            raise ValueError("CLERK_ISSUER must use HTTPS")
        return issuer.rstrip("/")

    @field_validator("clerk_authorized_parties")
    @classmethod
    def validate_clerk_authorized_parties(cls, parties: tuple[str, ...]) -> tuple[str, ...]:
        invalid = [party for party in parties if not party.startswith(("http://", "https://"))]
        if invalid:
            raise ValueError("CLERK_AUTHORIZED_PARTIES must contain absolute HTTP(S) origins")
        return tuple(dict.fromkeys(parties))

    @model_validator(mode="after")
    def validate_production_configuration(self) -> "Settings":
        if self.app_env != "production" or self.app_role == "renderer":
            return self
        required = {
            "CLERK_ISSUER": self.clerk_issuer,
            "LLM_MODEL": self.llm_model,
            "GCS_BUCKET": self.gcs_bucket,
            "GCS_SIGNER_SERVICE_ACCOUNT": self.gcs_signer_service_account,
            "MANIM_RENDERER_URL": self.manim_renderer_url,
        }
        if self.llm_provider == "vertex":
            required["GCP_PROJECT_ID"] = self.gcp_project_id
            required["VERTEX_AI_LOCATION"] = self.vertex_ai_location
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
        if any(not party.startswith("https://") for party in self.clerk_authorized_parties):
            raise ValueError("CLERK_AUTHORIZED_PARTIES must use HTTPS in production")
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        # Local services share the ignored root .env directory; deployments inject variables.
        load_dotenv(LOCAL_ENV_FILE)
        _resolve_google_credentials_path()

        origins = _csv_env("FRONTEND_ORIGINS") or DEFAULT_FRONTEND_ORIGINS
        authorized_parties = _csv_env("CLERK_AUTHORIZED_PARTIES") or origins
        return cls(
            app_env=os.getenv("APP_ENV", "local"),
            app_role=os.getenv("APP_ROLE", "api"),
            frontend_origins=origins,
            gcp_project_id=os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
            clerk_issuer=os.getenv("CLERK_ISSUER"),
            clerk_jwks_url=os.getenv("CLERK_JWKS_URL"),
            clerk_audience=os.getenv("CLERK_AUDIENCE"),
            clerk_authorized_parties=authorized_parties,
            llm_provider=os.getenv("LLM_PROVIDER", "vertex"),
            llm_model=os.getenv("LLM_MODEL"),
            llm_timeout_seconds=os.getenv("LLM_TIMEOUT_SECONDS", "120"),
            llm_max_output_tokens=os.getenv("LLM_MAX_OUTPUT_TOKENS", "16384"),
            vertex_ai_location=os.getenv("VERTEX_AI_LOCATION", "global"),
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


def _resolve_google_credentials_path() -> None:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        return
    path = Path(credentials_path).expanduser()
    if not path.is_absolute():
        path = REPOSITORY_DIR / path
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(path.resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
