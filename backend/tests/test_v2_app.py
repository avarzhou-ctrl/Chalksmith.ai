import ast
import asyncio
import json
import logging
import os
import signal
import tempfile
import unittest
from pathlib import Path
from time import monotonic
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from jwt import InvalidTokenError
from pydantic import ValidationError
from sqlalchemy import inspect, text
from sqlmodel import create_engine

from backend.app.core.config import LOCAL_CLERK_FILE, LOCAL_ENV_FILE, REPOSITORY_DIR, Settings
from backend.app.core.errors import AppError
from backend.app.core.logging import JsonFormatter
from backend.app.db.session import create_db_and_tables
from backend.app.integrations.auth import _decode_clerk_token, get_current_user
from backend.app.integrations.llm.base import (
    LLMOutputLimitError,
    LLMProviderError,
    LLMResult,
    LLMSource,
)
from backend.app.integrations.llm.deepseek import DeepSeekProvider
from backend.app.integrations.llm.factory import create_llm_provider
from backend.app.integrations.llm.gemini import VertexGeminiProvider
from backend.app.integrations.llm.openai import OpenAIProvider
from backend.app.integrations.storage import create_storage
from backend.app.integrations.storage.gcp import GCSStorage
from backend.app.integrations.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.lessons.formats import FormatRequest, get_lesson_format_strategy
from backend.app.lessons.formats.contracts import ModelOutputError
from backend.app.lessons.formats.code import build_code_generation_prompt, parse_generated_lesson
from backend.app.lessons.formats.slides import compiler as slides_compiler
from backend.app.lessons.formats.slides.presentation.custom import (
    PROMPT_HTML_LENGTH_TARGET,
    sanitize_slide_html,
)
from backend.app.lessons.formats.slides.presentation.layouts import LAYOUTS
from backend.app.lessons.formats.slides.strategy import (
    StructuredSlidesStrategy,
    build_slides_repair_prompt,
)
from backend.app.lessons.formats.slides.spec import (
    SLIDE_CAPACITY,
    SlidesLessonSpec,
)
from backend.app.lessons.formats.video.compiler import (
    VIDEO_COMPILER_VERSION,
    VIDEO_RUNTIME_END,
    VIDEO_RUNTIME_START,
    VIDEO_RUNTIME_VERSION,
    compile_video,
)
from backend.app.lessons.formats.video.prompt import VIDEO_RULES
from backend.app.lessons.formats.video.strategy import VideoStrategy
from backend.app.lessons.generation import (
    GenerationService,
    LLMProgress,
    _public_error,
    _should_attempt_repair,
)
from backend.app.lessons.render.base import (
    GeneratedCodeError,
    PolicyViolationError,
    RenderError,
)
from backend.app.lessons.render.manim import (
    LocalManimRenderer,
    RemoteManimRenderer,
    is_local_renderer_url,
    validate_manim_code,
)
from backend.app.renderer_main import renderer_app


class SettingsTests(unittest.TestCase):
    def test_default_output_budget_allows_lessons_beyond_16k_tokens(self) -> None:
        self.assertEqual(Settings().llm_max_output_tokens, 32_768)

    def test_settings_load_selected_provider_and_origins(self) -> None:
        environment = {
            "APP_ENV": "test",
            "FRONTEND_ORIGINS": "http://localhost:3000,https://app.chalksmith.ai/",
            "LLM_PROVIDER": "openai",
            "LLM_TIMEOUT_SECONDS": "45",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch("backend.app.core.config.load_dotenv") as load_dotenv,
        ):
            settings = Settings.from_env()

        # env.local is read first, so it wins over the Clerk file.
        self.assertEqual(
            [call.args[0] for call in load_dotenv.call_args_list],
            [LOCAL_ENV_FILE, LOCAL_CLERK_FILE],
        )
        self.assertEqual(settings.app_env, "test")
        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.llm_timeout_seconds, 45)
        self.assertEqual(
            settings.frontend_origins,
            ("http://localhost:3000", "https://app.chalksmith.ai"),
        )

    def test_settings_resolve_centralized_service_account_path(self) -> None:
        environment = {
            "APP_ENV": "test",
            "GOOGLE_APPLICATION_CREDENTIALS": ".env/service-account.json",
        }

        with (
            patch.dict(os.environ, environment, clear=True),
            patch("backend.app.core.config.load_dotenv"),
        ):
            Settings.from_env()
            credentials_path = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]

        self.assertEqual(
            credentials_path,
            str((REPOSITORY_DIR / ".env/service-account.json").resolve()),
        )

    def test_settings_reject_relative_frontend_origin(self) -> None:
        with self.assertRaises(ValueError):
            Settings(frontend_origins=("localhost:3000",))

    def test_production_requires_only_the_selected_llm_key(self) -> None:
        settings = Settings(
            app_env="production",
            clerk_issuer="https://clerk.example",
            llm_provider="openai",
            llm_model="gpt-test",
            openai_api_key="secret",
            database_url="postgresql+psycopg://user:pass@localhost/db",
            gcs_bucket="bucket",
            gcs_signer_service_account="api@example.iam.gserviceaccount.com",
            manim_renderer_url="https://renderer.example",
            frontend_origins=("https://chalksmith.example",),
            clerk_authorized_parties=("https://chalksmith.example",),
        )

        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.vertex_ai_location, "global")

    def test_production_vertex_uses_project_identity_without_api_key(self) -> None:
        settings = Settings(
            app_env="production",
            gcp_project_id="project",
            clerk_issuer="https://clerk.example",
            llm_provider="vertex",
            llm_model="gemini-test",
            vertex_ai_location="global",
            database_url="postgresql+psycopg://user:pass@localhost/db",
            gcs_bucket="bucket",
            gcs_signer_service_account="api@example.iam.gserviceaccount.com",
            manim_renderer_url="https://renderer.example",
            frontend_origins=("https://chalksmith.example",),
            clerk_authorized_parties=("https://chalksmith.example",),
        )

        self.assertEqual(settings.llm_provider, "vertex")
        self.assertIsNone(settings.openai_api_key)

    @patch("backend.app.integrations.llm.gemini.genai.Client")
    def test_vertex_provider_uses_adc_project_and_location(self, client: MagicMock) -> None:
        settings = Settings(
            gcp_project_id="project",
            llm_provider="vertex",
            llm_model="gemini-test",
            vertex_ai_location="global",
        )

        create_llm_provider(settings)

        client.assert_called_once_with(vertexai=True, project="project", location="global")

    @patch("backend.app.integrations.llm.deepseek.AsyncOpenAI")
    def test_deepseek_provider_targets_the_deepseek_base_url(self, client: MagicMock) -> None:
        settings = Settings(
            llm_provider="deepseek",
            llm_model="deepseek-v4-flash",
            deepseek_api_key="secret",
        )

        create_llm_provider(settings)

        client.assert_called_once_with(
            api_key="secret", base_url="https://api.deepseek.com", timeout=settings.llm_timeout_seconds
        )

    def test_deepseek_keeps_the_output_budget_for_the_answer(self) -> None:
        provider = DeepSeekProvider(
            api_key="secret",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            timeout_seconds=120,
            max_output_tokens=16_384,
        )
        message = MagicMock(content="summary\n---CODE_START---\ncode")
        completion = MagicMock(choices=[MagicMock(finish_reason="stop", message=message)])
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=completion)

        result = asyncio.run(provider.generate("prompt"))

        request = provider.client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["extra_body"], {"thinking": {"type": "disabled"}})
        self.assertEqual(result.text, "summary\n---CODE_START---\ncode")

    def test_deepseek_reports_a_truncated_answer_as_a_token_limit(self) -> None:
        provider = DeepSeekProvider(
            api_key="secret",
            model="deepseek-v4-flash",
            base_url="https://api.deepseek.com",
            timeout_seconds=120,
            max_output_tokens=16_384,
        )
        completion = MagicMock(choices=[MagicMock(finish_reason="length")])
        provider.client = MagicMock()
        provider.client.chat.completions.create = AsyncMock(return_value=completion)

        # Truncation surfaces downstream as a malformed lesson, which reads as a
        # model formatting failure rather than an exhausted budget.
        with self.assertRaisesRegex(LLMProviderError, "16384-token output limit"):
            asyncio.run(provider.generate("prompt"))

    def test_deepseek_provider_requires_key(self) -> None:
        with self.assertRaisesRegex(AppError, "DEEPSEEK_API_KEY"):
            create_llm_provider(Settings(llm_provider="deepseek", llm_model="deepseek-v4-flash"))

    def test_vertex_provider_requires_project(self) -> None:
        with self.assertRaisesRegex(AppError, "GCP_PROJECT_ID"):
            create_llm_provider(Settings(llm_provider="vertex", llm_model="gemini-test"))

    def test_production_api_rejects_incomplete_configuration(self) -> None:
        with self.assertRaises(ValueError):
            Settings(app_env="production")

    def test_production_rejects_insecure_renderer_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(
                app_env="production",
                gcp_project_id="project",
                clerk_issuer="https://clerk.example",
                llm_model="model",
                database_url="postgresql+psycopg://user:pass@localhost/db",
                gcs_bucket="bucket",
                gcs_signer_service_account="api@example.iam.gserviceaccount.com",
                manim_renderer_url="http://renderer.example",
                frontend_origins=("https://chalksmith.example",),
                clerk_authorized_parties=("https://chalksmith.example",),
            )

    def test_production_rejects_insecure_frontend_origins(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(
                app_env="production",
                gcp_project_id="project",
                clerk_issuer="https://clerk.example",
                llm_model="model",
                database_url="postgresql+psycopg://user:pass@localhost/db",
                gcs_bucket="bucket",
                gcs_signer_service_account="api@example.iam.gserviceaccount.com",
                manim_renderer_url="https://renderer.example",
                frontend_origins=("http://chalksmith.example",),
                clerk_authorized_parties=("https://chalksmith.example",),
            )


class AuthenticationTests(unittest.IsolatedAsyncioTestCase):
    def test_clerk_token_rejects_an_untrusted_authorized_party(self) -> None:
        settings = Settings(
            app_env="test",
            clerk_issuer="https://clerk.example",
            clerk_authorized_parties=("http://localhost:3000",),
        )
        jwks_client = MagicMock()
        jwks_client.get_signing_key_from_jwt.return_value.key = "public-key"

        with (
            patch("backend.app.integrations.auth._jwks_client", return_value=jwks_client),
            patch(
                "backend.app.integrations.auth.jwt.decode",
                return_value={"sub": "user_123", "azp": "https://attacker.example"},
            ),
            self.assertRaises(InvalidTokenError),
        ):
            _decode_clerk_token("session-token", settings)

    async def test_clerk_subject_becomes_the_tenant_owner(self) -> None:
        request = MagicMock()
        request.app.state.settings = Settings(
            app_env="test",
            clerk_issuer="https://clerk.example",
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="session-token")

        with patch(
            "backend.app.integrations.auth._decode_clerk_token",
            return_value={"sub": "user_123", "email": "teacher@example.com"},
        ):
            user = await get_current_user(request, credentials)

        self.assertEqual(user.uid, "user_123")
        self.assertEqual(user.email, "teacher@example.com")

    async def test_invalid_clerk_token_returns_unauthorized(self) -> None:
        request = MagicMock()
        request.app.state.settings = Settings(
            app_env="test",
            clerk_issuer="https://clerk.example",
        )
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")

        with patch(
            "backend.app.integrations.auth._decode_clerk_token",
            side_effect=InvalidTokenError("invalid"),
        ), self.assertRaises(AppError) as raised:
            await get_current_user(request, credentials)

        self.assertEqual(raised.exception.status_code, 401)
        self.assertEqual(raised.exception.code, "invalid_session_token")


class StorageTests(unittest.TestCase):
    @patch("backend.app.integrations.storage.gcp.impersonated_credentials.Credentials")
    @patch("backend.app.integrations.storage.gcp.storage.Client")
    def test_signed_url_reuses_matching_impersonated_adc(
        self,
        storage_client: MagicMock,
        impersonated_credentials: MagicMock,
    ) -> None:
        signer_email = "api@example.iam.gserviceaccount.com"
        client = storage_client.return_value
        client._credentials.signer_email = signer_email
        blob = client.bucket.return_value.blob.return_value
        blob.generate_signed_url.return_value = "https://signed.example"
        storage_backend = GCSStorage(
            Settings(
                gcp_project_id="project",
                gcs_bucket="bucket",
                gcs_signer_service_account=signer_email,
            )
        )

        url = storage_backend.signed_url("lessons/output.html")

        self.assertEqual(url, "https://signed.example")
        impersonated_credentials.assert_not_called()
        self.assertIs(blob.generate_signed_url.call_args.kwargs["credentials"], client._credentials)


class LocalStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings = Settings(
            app_env="local",
            local_storage_dir=self.directory.name,
            local_storage_base_url="http://localhost:8000/",
        )
        self.storage = LocalStorage(self.settings)

    def test_selected_only_when_a_directory_is_configured(self) -> None:
        self.assertIsInstance(create_storage(self.settings), LocalStorage)
        self.assertIsInstance(
            create_storage(Settings(app_env="local", gcs_bucket="bucket")),
            GCSStorage,
        )

    def test_objects_round_trip_and_delete_by_prefix(self) -> None:
        source = Path(self.directory.name) / "render.html"
        source.write_text("<html></html>", encoding="utf-8")

        self.storage.upload_file(source, "lessons/teacher/1/lesson.html", "text/html")
        self.storage.upload_bytes(b"%PDF-", "sources/teacher/1/notes.pdf", "application/pdf")
        stored = Path(self.directory.name) / "lessons/teacher/1/lesson.html"
        self.assertEqual(stored.read_text(encoding="utf-8"), "<html></html>")

        self.storage.delete_prefix("sources/teacher/1/")
        self.assertFalse((Path(self.directory.name) / "sources/teacher/1").exists())
        self.storage.delete("lessons/teacher/1/lesson.html")
        self.assertFalse(stored.exists())
        # GCS deletes are idempotent, and a missing local file must behave the same.
        self.storage.delete("lessons/teacher/1/lesson.html")

    def test_signed_url_points_at_the_serving_route(self) -> None:
        self.assertEqual(
            self.storage.signed_url("lessons/teacher/1/lesson.html"),
            "http://localhost:8000/local-storage/lessons/teacher/1/lesson.html",
        )
        self.assertEqual(
            self.storage.signed_url("lessons/teacher/1/lesson.mp4", download_name="A lesson.mp4"),
            "http://localhost:8000/local-storage/lessons/teacher/1/lesson.mp4?download=A%20lesson.mp4",
        )

    def test_keys_escaping_the_root_are_rejected(self) -> None:
        for object_key in ("../escaped.html", "lessons/../../escaped.html", "/etc/passwd", ""):
            with self.subTest(object_key=object_key), self.assertRaises(AppError) as raised:
                self.storage.object_path(object_key)
            self.assertEqual(raised.exception.status_code, 404)

    def test_deployed_environments_refuse_a_local_directory(self) -> None:
        for app_env in ("staging", "production"):
            with self.subTest(app_env=app_env), self.assertRaises(ValidationError):
                Settings(app_env=app_env, local_storage_dir=self.directory.name)


class LocalStorageRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.app = create_app(
            Settings(app_env="test", database_url="sqlite://", local_storage_dir=self.directory.name)
        )
        self.client = TestClient(self.app)
        lesson = Path(self.directory.name) / "lessons/teacher/1/lesson.html"
        lesson.parent.mkdir(parents=True)
        lesson.write_text("<html></html>", encoding="utf-8")

    def test_object_is_served_inline_or_as_a_download(self) -> None:
        response = self.client.get("/local-storage/lessons/teacher/1/lesson.html")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "<html></html>")
        self.assertTrue(response.headers["content-type"].startswith("text/html"))
        self.assertNotIn("content-disposition", response.headers)

        download = self.client.get(
            "/local-storage/lessons/teacher/1/lesson.html?download=Fractions.html"
        )

        self.assertEqual(download.headers["content-disposition"], 'attachment; filename="Fractions.html"')

    def test_traversal_and_missing_objects_are_not_found(self) -> None:
        # Percent-encoded so the client cannot normalize the escape away first.
        for path in (
            "/local-storage/%2e%2e%2f%2e%2e%2fenv.local",
            "/local-storage/lessons/teacher/2/lesson.html",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_route_is_absent_without_a_local_directory(self) -> None:
        client = TestClient(create_app(Settings(app_env="test", database_url="sqlite://")))

        self.assertEqual(client.get("/local-storage/lessons/teacher/1/lesson.html").status_code, 404)


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        # Without an explicit URL the engine falls back to an on-disk SQLite file,
        # which the lifespan below then creates in the repository's .env directory.
        self.app: FastAPI = create_app(Settings(app_env="test", database_url="sqlite://"))
        self.client = TestClient(self.app)

    def test_healthcheck(self) -> None:
        response = self.client.get("/ready", headers={"X-Request-Id": "test-request"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "environment": "test", "version": "2.0.0"},
        )
        self.assertEqual(response.headers["X-Request-Id"], "test-request")

    def test_app_error_uses_shared_response_shape(self) -> None:
        @self.app.get("/test-error")
        async def raise_test_error() -> None:
            raise AppError(code="TEST_ERROR", message="Expected failure", status_code=409)

        response = self.client.get("/test-error")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json(),
            {"error": {"code": "TEST_ERROR", "message": "Expected failure"}},
        )

    def test_request_validation_uses_shared_response_shape(self) -> None:
        @self.app.get("/validated")
        async def validated(count: int) -> dict[str, int]:
            return {"count": count}

        response = self.client.get("/validated?count=invalid")

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_unhandled_error_uses_shared_response_shape(self) -> None:
        @self.app.get("/unexpected")
        async def raise_unexpected_error() -> None:
            raise RuntimeError("private diagnostic")

        with TestClient(self.app, raise_server_exceptions=False) as client:
            response = client.get(
                "/unexpected",
                headers={"Origin": "http://localhost:3000", "X-Request-Id": "error-request"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "internal_error")
        self.assertNotIn("private diagnostic", response.text)
        self.assertEqual(response.headers["X-Request-Id"], "error-request")
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://localhost:3000")

    def test_json_formatter_includes_generation_retry_error(self) -> None:
        record = logging.LogRecord(
            name="backend.app.lessons.generation",
            level=logging.WARNING,
            pathname=__file__,
            lineno=1,
            msg="lesson_generation_retry",
            args=(),
            exc_info=None,
        )
        record.lesson_id = "c72da3d5-0606-4649-afe1-9308df5b9bcb"
        record.lesson_format = "slides"
        record.stage = "rendering"
        record.error_type = "ModelOutputError"
        record.repair_reason = "slides_custom_html"
        record.repair_outcome = "started"
        record.error = "custom-html exceeds 6000 characters (7124 given)"

        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual(payload["message"], "lesson_generation_retry")
        self.assertEqual(payload["lesson_id"], record.lesson_id)
        self.assertEqual(payload["lesson_format"], "slides")
        self.assertEqual(payload["stage"], "rendering")
        self.assertEqual(payload["error_type"], "ModelOutputError")
        self.assertEqual(payload["repair_reason"], "slides_custom_html")
        self.assertEqual(payload["repair_outcome"], "started")
        self.assertEqual(payload["error"], record.error)

    def test_provider_error_visibility_uses_the_injected_app_environment(self) -> None:
        error = LLMProviderError("private upstream diagnostic")

        production_message = _public_error(error, app_env="production")
        local_message = _public_error(error, app_env="local")

        self.assertNotIn("private upstream diagnostic", production_message)
        self.assertIn("private upstream diagnostic", local_message)


class RendererSecurityTests(unittest.TestCase):
    def test_manim_allows_expected_scene_imports(self) -> None:
        validate_manim_code("from manim import *\nclass GeneratedScene(Scene):\n    def construct(self):\n        self.add(Text('Hi'))")

    def test_manim_blocks_operating_system_imports(self) -> None:
        with self.assertRaises(RenderError):
            validate_manim_code("import os\nfrom manim import *\nclass GeneratedScene(Scene): pass")

    def test_manim_blocks_dynamic_runtime_access(self) -> None:
        bypasses = (
            "from manim import *\nclass GeneratedScene(Scene):\n def construct(self): getattr({}, '__class__')",
            "from manim import *\nclass GeneratedScene(Scene):\n def construct(self): __builtins__['open']('x')",
            "import manim\nclass GeneratedScene(manim.Scene):\n def construct(self): manim.ImageMobject('x')",
        )
        for code in bypasses:
            with self.subTest(code=code), self.assertRaises(RenderError):
                validate_manim_code(code)

    def test_manim_allows_audited_computation_imports_and_declared_helpers(self) -> None:
        validate_manim_code(
            "from manim import *\n"
            "import itertools\n"
            "from fractions import Fraction\n"
            "class GeneratedScene(Scene):\n"
            " def _make_label(self): return Fraction(1, 2)\n"
            " def construct(self): self._make_label()"
        )

    def test_manim_still_blocks_dangerous_imports_from_allowed_modules(self) -> None:
        with self.assertRaises(PolicyViolationError):
            validate_manim_code(
                "from manim import *\n"
                "from numpy import load as read_data\n"
                "class GeneratedScene(Scene): pass"
            )

    def test_local_renderer_urls_are_detected(self) -> None:
        self.assertTrue(is_local_renderer_url("http://localhost:8081"))
        self.assertTrue(is_local_renderer_url("http://[::1]:8081"))
        self.assertFalse(is_local_renderer_url("https://renderer.example"))

    def test_renderer_returns_a_bounded_render_diagnostic(self) -> None:
        with patch(
            "backend.app.renderer_main.LocalManimRenderer.render",
            new=AsyncMock(side_effect=RenderError("bounded diagnostic")),
        ):
            response = TestClient(renderer_app).post(
                "/internal/render/manim",
                json={"code": "from manim import *\nclass GeneratedScene(Scene): pass"},
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.json(),
            {
                "detail": {
                    "error_type": "render_error",
                    "message": "bounded diagnostic",
                }
            },
        )

    def test_remote_renderer_preserves_policy_violation_ownership(self) -> None:
        class FakeResponse:
            status_code = 422
            text = "policy violation"
            content = b""

            @staticmethod
            def json() -> dict[str, object]:
                return {
                    "detail": {
                        "error_type": "policy_violation",
                        "message": "Generated Manim code imports a blocked module.",
                    }
                }

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def post(self, *_args, **_kwargs):
                return FakeResponse()

        renderer = RemoteManimRenderer(
            "https://renderer.example",
            timeout_seconds=60,
            max_render_bytes=1_000_000,
            authenticate=False,
        )
        with tempfile.TemporaryDirectory() as directory, patch(
            "backend.app.lessons.render.manim.httpx.AsyncClient",
            return_value=FakeClient(),
        ), self.assertRaises(PolicyViolationError):
            asyncio.run(renderer.render("blocked", Path(directory)))


class GenerationDeadlineTests(unittest.IsolatedAsyncioTestCase):
    async def test_video_repair_is_skipped_when_deadline_budget_is_too_small(self) -> None:
        class RepairableStrategy:
            def can_repair(self, _error: Exception) -> bool:
                return True

        self.assertFalse(
            _should_attempt_repair(
                strategy=RepairableStrategy(),
                error=GeneratedCodeError("bad code"),
                lesson_format="video",
                deadline=monotonic() + 60,
            )
        )

    async def test_generation_deadline_limits_each_async_operation(self) -> None:
        service = GenerationService(
            session=None,  # type: ignore[arg-type]
            llm=None,  # type: ignore[arg-type]
            storage=None,  # type: ignore[arg-type]
            renderers={},
            deadline=monotonic() + 0.001,
            request_id="deadline-test",
            app_env="test",
        )

        with self.assertRaises(TimeoutError):
            await service._await(asyncio.sleep(1))

    async def test_non_streaming_provider_emits_heartbeats_while_waiting(self) -> None:
        class SlowLLM:
            async def generate(self, _prompt: str) -> LLMResult:
                await asyncio.sleep(0.01)
                return LLMResult(text="done", provider="fake", model="fake-model")

        service = GenerationService(
            session=None,  # type: ignore[arg-type]
            llm=SlowLLM(),
            storage=None,  # type: ignore[arg-type]
            renderers={},
            deadline=monotonic() + 1,
            request_id="heartbeat-test",
            app_env="test",
        )

        with patch("backend.app.lessons.generation.LLM_HEARTBEAT_SECONDS", 0.001):
            events = [
                event
                async for event in service._generate_with_progress(
                    "prompt",
                    lesson_id=uuid4(),
                    owner_hash="owner-hash",
                    stage="generating",
                    message="Creating lesson code…",
                )
            ]

        self.assertTrue(
            any(
                isinstance(event, LLMProgress) and "Waiting for the model" in event.message
                for event in events
            )
        )
        self.assertIsInstance(events[-1], LLMResult)

    async def test_failed_generation_cleanup_removes_output_and_uploaded_sources(self) -> None:
        storage = MagicMock()
        service = GenerationService(
            session=None,  # type: ignore[arg-type]
            llm=None,  # type: ignore[arg-type]
            storage=storage,
            renderers={},
            deadline=monotonic() + 1,
            request_id="cleanup-test",
            app_env="test",
        )
        lesson_id = uuid4()

        await service._cleanup_failed_storage(
            lesson_id=lesson_id,
            owner_hash="owner-hash",
            object_key=f"lessons/teacher/{lesson_id}/lesson.html",
            source_prefix=f"sources/teacher/{lesson_id}/",
        )

        storage.delete.assert_called_once_with(f"lessons/teacher/{lesson_id}/lesson.html")
        storage.delete_prefix.assert_called_once_with(f"sources/teacher/{lesson_id}/")


class GeminiStreamingTests(unittest.IsolatedAsyncioTestCase):
    async def test_stream_yields_deltas_and_final_billed_usage(self) -> None:
        async def responses():
            yield SimpleNamespace(
                text="first ",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=20,
                    candidates_token_count=None,
                    thoughts_token_count=3,
                ),
            )
            yield SimpleNamespace(
                text="second",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=20,
                    candidates_token_count=5,
                    thoughts_token_count=3,
                ),
            )

        provider = VertexGeminiProvider(
            project="test-project",
            location="global",
            model="test-model",
            timeout_seconds=1,
            max_output_tokens=100,
        )
        provider.client = MagicMock()
        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=responses())

        chunks = [chunk async for chunk in provider.stream("prompt")]

        self.assertEqual("".join(chunk.text for chunk in chunks), "first second")
        self.assertEqual(chunks[-1].input_tokens, 20)
        self.assertEqual(chunks[-1].output_tokens, 8)

    async def test_stream_sends_source_files_as_binary_parts(self) -> None:
        async def responses():
            yield SimpleNamespace(
                text="done",
                usage_metadata=SimpleNamespace(
                    prompt_token_count=20,
                    candidates_token_count=5,
                    thoughts_token_count=0,
                ),
            )

        provider = VertexGeminiProvider(
            project="test-project",
            location="global",
            model="test-model",
            timeout_seconds=1,
            max_output_tokens=100,
        )
        provider.client = MagicMock()
        provider.client.aio.models.generate_content_stream = AsyncMock(return_value=responses())
        image = LLMSource("diagram.png", "image/png", b"png-bytes")
        pdf = LLMSource("worksheet.pdf", "application/pdf", b"pdf-bytes")

        chunks = [chunk async for chunk in provider.stream("prompt", sources=(image, pdf))]

        self.assertEqual(chunks[-1].text, "done")
        contents = provider.client.aio.models.generate_content_stream.await_args.kwargs["contents"]
        self.assertEqual(contents[0].text, "prompt")
        self.assertEqual(contents[1].text, "Source image: diagram.png")
        self.assertEqual(contents[2].inline_data.mime_type, "image/png")
        self.assertEqual(contents[2].inline_data.data, b"png-bytes")
        self.assertEqual(contents[3].text, "Source document: worksheet.pdf")
        self.assertEqual(contents[4].inline_data.mime_type, "application/pdf")
        self.assertEqual(contents[4].inline_data.data, b"pdf-bytes")


class OpenAISourceTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_reports_output_budget_truncation(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_output_tokens=100,
        )
        provider.client = MagicMock()
        provider.client.responses.create = AsyncMock(
            return_value=SimpleNamespace(
                status="incomplete",
                incomplete_details=SimpleNamespace(reason="max_output_tokens"),
            )
        )

        with self.assertRaises(LLMOutputLimitError):
            await provider.generate("prompt")

    async def test_generate_sends_images_and_pdfs_as_data_urls(self) -> None:
        provider = OpenAIProvider(
            api_key="test-key",
            model="test-model",
            timeout_seconds=1,
            max_output_tokens=100,
        )
        provider.client = MagicMock()
        provider.client.responses.create = AsyncMock(
            return_value=SimpleNamespace(
                output_text="done",
                usage=SimpleNamespace(input_tokens=20, output_tokens=5),
            )
        )
        image = LLMSource("diagram.jpg", "image/jpeg", b"jpeg-bytes")
        pdf = LLMSource("worksheet.pdf", "application/pdf", b"pdf-bytes")

        result = await provider.generate("prompt", sources=(image, pdf))

        self.assertEqual(result.text, "done")
        request_input = provider.client.responses.create.await_args.kwargs["input"]
        content = request_input[0]["content"]
        self.assertEqual(content[0], {"type": "input_text", "text": "prompt"})
        self.assertEqual(
            content[1],
            {"type": "input_text", "text": "Source image: diagram.jpg"},
        )
        self.assertEqual(content[2]["type"], "input_image")
        self.assertEqual(
            content[2]["image_url"],
            "data:image/jpeg;base64,anBlZy1ieXRlcw==",
        )
        self.assertEqual(
            content[3],
            {"type": "input_text", "text": "Source document: worksheet.pdf"},
        )
        self.assertEqual(content[4]["type"], "input_file")
        self.assertEqual(content[4]["filename"], "worksheet.pdf")
        self.assertEqual(
            content[4]["file_data"],
            "data:application/pdf;base64,cGRmLWJ5dGVz",
        )


class RendererCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_renderer_cancellation_kills_the_process_group(self) -> None:
        class FakeProcess:
            pid = 1234
            returncode = None

            def __init__(self) -> None:
                self.wait_calls = 0

            async def wait(self) -> int:
                self.wait_calls += 1
                if self.wait_calls == 1:
                    await asyncio.Event().wait()
                self.returncode = -9
                return self.returncode

        process = FakeProcess()
        renderer = LocalManimRenderer(timeout_seconds=60, max_render_bytes=1_000_000)
        code = "from manim import *\nclass GeneratedScene(Scene):\n def construct(self): pass"
        with tempfile.TemporaryDirectory() as directory, patch(
            "backend.app.lessons.render.manim.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ), patch("backend.app.lessons.render.manim.os.killpg") as kill_process_group:
            task = asyncio.create_task(renderer.render(code, Path(directory)))
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        kill_process_group.assert_called_once_with(process.pid, signal.SIGKILL)


class ParseGeneratedLessonTests(unittest.TestCase):
    def test_recovers_complete_unmarked_interactive_without_model_repair(self) -> None:
        lesson = parse_generated_lesson(
            "Teacher summary.\n```html\n<!doctype html><html><body>Hi</body></html>\n```",
            "interactive",
        )

        self.assertEqual(lesson.summary, "Teacher summary.")
        self.assertEqual(
            lesson.code,
            "<!doctype html><html><body>Hi</body></html>",
        )

    def test_recovers_complete_unmarked_video_without_model_repair(self) -> None:
        lesson = parse_generated_lesson(
            "Teacher summary.\n```python\nfrom manim import *\n"
            "class GeneratedScene(Scene):\n    def construct(self):\n        self.wait()\n```",
            "video",
        )

        self.assertEqual(lesson.summary, "Teacher summary.")
        self.assertIn("class GeneratedScene(Scene):", lesson.code)
        ast.parse(lesson.code)

    def test_drops_invented_closing_separator(self) -> None:
        lesson = parse_generated_lesson(
            "A summary.\n---CODE_START---\nfrom manim import *\nx = 1\n---CODE_END---\n", "video"
        )
        self.assertEqual(lesson.summary, "A summary.")
        self.assertEqual(lesson.code, "from manim import *\nx = 1")
        ast.parse(lesson.code)

    def test_drops_any_trailing_prose_not_only_a_known_marker(self) -> None:
        for trailer in ("--- END ---", "[END OF CODE]", "Hope this helps!", "```", "*** fin ***"):
            with self.subTest(trailer=trailer):
                lesson = parse_generated_lesson(f"S\n---CODE_START---\nx = 1\n{trailer}\n", "video")
                self.assertEqual(lesson.code, "x = 1")

    def test_keeps_a_trailing_comment_because_it_already_parses(self) -> None:
        lesson = parse_generated_lesson("S\n---CODE_START---\nx = 1\n# Done\n", "video")
        self.assertEqual(lesson.code, "x = 1\n# Done")
        ast.parse(lesson.code)

    def test_keeps_code_whose_last_line_is_valid_python(self) -> None:
        code = "from manim import *\n\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        self.wait(2.5)"
        lesson = parse_generated_lesson(f"S\n---CODE_START---\n{code}\n", "video")
        self.assertEqual(lesson.code, code)

    def test_leaves_badly_malformed_python_for_validation_to_reject(self) -> None:
        broken = "def f(\n" + "\n".join(f"x{index} = {index}" for index in range(20))
        lesson = parse_generated_lesson(f"S\n---CODE_START---\n{broken}\n", "video")
        self.assertEqual(lesson.code, broken)
        with self.assertRaises(SyntaxError):
            ast.parse(lesson.code)

    def test_truncates_html_after_the_document_ends(self) -> None:
        lesson = parse_generated_lesson(
            "S\n---CODE_START---\n<html><body>hi</body></html>\n---CODE_END---\nthanks!", "slides"
        )
        self.assertEqual(lesson.code, "<html><body>hi</body></html>")

    def test_still_strips_markdown_fences(self) -> None:
        lesson = parse_generated_lesson("S\n---CODE_START---\n```python\nx = 1\n```", "video")
        self.assertEqual(lesson.code, "x = 1")


class CodeGenerationPromptTests(unittest.TestCase):
    def test_prompt_organizes_and_preserves_generation_guidance(self) -> None:
        prompt = build_code_generation_prompt(
            topic="Explain vectors",
            rules="Return a complete runnable example.",
            sources="Teacher notes",
            previous_code="print('old')",
            edit_instruction="Add a worked example.",
        )

        for section in (
            "<CONTEXT_RULES>",
            "<OUTPUT_CONTRACT>",
            "<LESSON_REQUIREMENTS>",
            "<FORMAT_RULES>",
        ):
            self.assertIn(section, prompt)
        normalized_prompt = " ".join(prompt.split())
        self.assertIn("advanced or competition topics", normalized_prompt)
        self.assertIn("curriculum-ready sequence", normalized_prompt)
        self.assertIn("verify calculations and units", normalized_prompt)
        self.assertIn("concrete examples before abstraction", normalized_prompt)
        self.assertIn("teacher-provided material as the factual basis", normalized_prompt)
        self.assertIn("irrelevant or sensitive material", normalized_prompt)
        self.assertIn("preserving working behavior", normalized_prompt)
        self.assertIn("<REQUEST>Explain vectors</REQUEST>", prompt)
        self.assertIn("<SOURCES>\nTeacher notes\n</SOURCES>", prompt)
        self.assertIn("<EDIT_INSTRUCTION>Add a worked example.</EDIT_INSTRUCTION>", prompt)
        self.assertIn("<EXISTING_CODE>\nprint('old')\n</EXISTING_CODE>", prompt)
        self.assertIn("Return a complete runnable example.", prompt)
        self.assertIn("---CODE_START--- on its own line", prompt)
        self.assertIn("Never use Markdown fences", prompt)
        self.assertIn("write no closing separator, fence, or commentary", prompt)


class VideoGenerationTests(unittest.TestCase):
    def test_prompt_requires_platform_typography_and_latex_helpers(self) -> None:
        for section in (
            "<DELIVERABLE>",
            "<TEACHING_SEQUENCE>",
            "<PLATFORM_STYLE>",
            "<MATH_RENDERING>",
            "<LAYOUT_AND_SAFETY>",
        ):
            self.assertIn(section, VIDEO_RULES)

        normalized_rules = " ".join(VIDEO_RULES.split())
        self.assertIn("Use `cs_text(value, role, color)`", normalized_rules)
        self.assertIn("Use `cs_math(r\"...\", role, color)`", normalized_rules)
        self.assertIn("The platform selects Inter or Noto Sans CJK SC", normalized_rules)
        self.assertIn("Never call Text, MarkupText, Paragraph, Title", normalized_rules)
        self.assertIn("Never call Tex or MathTex directly", normalized_rules)
        self.assertIn("Never represent a fraction with a slash", normalized_rules)
        self.assertIn("share one base font size", normalized_rules)
        self.assertIn("split a long equality chain", normalized_rules)
        self.assertIn("decimal, fractions, itertools, manim, math, numpy, random, statistics", normalized_rules)
        self.assertIn("Helper methods declared on GeneratedScene are allowed", normalized_rules)
        self.assertNotIn("Use Text and Unicode symbols instead of Tex", normalized_rules)

    def test_strategy_injects_the_platform_runtime_and_metadata(self) -> None:
        response = r'''A concise summary.
---CODE_START---
from manim import *
import numpy as np

class GeneratedScene(Scene):
    def construct(self):
        title = cs_text("Pythagorean theorem", "title", "text")
        formula = cs_math(r"a^2 + b^2 = c^2", "display", "accent")
        self.add(title, formula)
'''

        prepared = VideoStrategy().prepare(response)

        self.assertEqual(prepared.summary, "A concise summary.")
        self.assertEqual(prepared.runtime_version, VIDEO_RUNTIME_VERSION)
        self.assertEqual(prepared.compiler_version, VIDEO_COMPILER_VERSION)
        self.assertIn(VIDEO_RUNTIME_START, prepared.source_code)
        self.assertIn(VIDEO_RUNTIME_END, prepared.source_code)
        self.assertIn('CS_LATIN_FONT = "Inter"', prepared.source_code)
        self.assertIn('CS_CJK_FONT = "Noto Sans CJK SC"', prepared.source_code)
        self.assertIn("def cs_math", prepared.source_code)
        self.assertIn("MathTex(", prepared.source_code)
        self.assertIn('"display": (36, 11.4)', prepared.source_code)
        self.assertIn('"equation": (36, 10.8)', prepared.source_code)
        self.assertIn("CS_MATH_MIN_SCALE = 0.9", prepared.source_code)
        self.assertIn("split it into multiple formulas", prepared.source_code)
        self.assertIn('config.background_color = CS_COLORS["background"]', prepared.source_code)
        self.assertIn("class GeneratedScene(Scene):", prepared.source_code)
        ast.parse(prepared.source_code)
        validate_manim_code(prepared.source_code)

    def test_compiler_preserves_a_module_docstring_before_manim_imports(self) -> None:
        compiled = compile_video(
            '"""Generated teaching scene."""\n'
            "from manim import *\n"
            "class GeneratedScene(Scene):\n"
            "    def construct(self):\n"
            "        self.wait()"
        )

        self.assertTrue(compiled.startswith('"""Generated teaching scene."""'))
        self.assertLess(compiled.index("from manim import *"), compiled.index(VIDEO_RUNTIME_START))

    def test_compiler_rejects_direct_text_and_math_objects(self) -> None:
        direct_calls = (
            'Text("Heading")',
            r'MathTex(r"x^2")',
            r'Tex(r"Area")',
        )
        for direct_call in direct_calls:
            with self.subTest(direct_call=direct_call), self.assertRaisesRegex(
                RenderError, "must use Chalksmith helpers"
            ):
                compile_video(
                    "from manim import *\n"
                    "class GeneratedScene(Scene):\n"
                    "    def construct(self):\n"
                    f"        self.add({direct_call})\n"
                )

    def test_edit_prompt_strips_the_prior_compiler_runtime(self) -> None:
        source = """from manim import *
class GeneratedScene(Scene):
    def construct(self):
        self.add(cs_text("Old", "title", "text"))
"""
        compiled = compile_video(source)
        recompiled = compile_video(compiled)

        prompt = VideoStrategy().build_prompt(
            FormatRequest(
                topic="Revise the title",
                lesson_format="video",
                previous_code=compiled,
                edit_instruction="Use the new title.",
            )
        )

        self.assertNotIn(VIDEO_RUNTIME_START, prompt)
        self.assertNotIn(VIDEO_RUNTIME_END, prompt)
        self.assertIn('self.add(cs_text("Old", "title", "text"))', prompt)
        self.assertEqual(recompiled.count(VIDEO_RUNTIME_START), 1)
        self.assertEqual(recompiled.count(VIDEO_RUNTIME_END), 1)

    def test_compiler_rejects_platform_style_overrides(self) -> None:
        source = """from manim import *
config.background_color = WHITE
class GeneratedScene(Scene):
    def construct(self):
        self.wait()
"""

        with self.assertRaisesRegex(RenderError, "must not override the platform background"):
            compile_video(source)


class StructuredSlidesTests(unittest.TestCase):
    def test_slides_always_use_the_structured_strategy(self) -> None:
        strategy = get_lesson_format_strategy("slides")

        self.assertIsInstance(strategy, StructuredSlidesStrategy)

    def test_prompt_exposes_the_compact_v2_contract_without_runtime_css(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(topic="Equivalent fractions", lesson_format="slides")
        )
        schema = json.loads(
            prompt.split("<JSON_SCHEMA>\n", 1)[1].split("\n</JSON_SCHEMA>", 1)[0]
        )
        schema_nodes: list[tuple[object, bool]] = [(schema, False)]
        while schema_nodes:
            node, is_properties = schema_nodes.pop()
            if isinstance(node, dict):
                if not is_properties:
                    self.assertNotIn("title", node)
                schema_nodes.extend(
                    (child, key == "properties") for key, child in node.items()
                )
            elif isinstance(node, list):
                schema_nodes.extend((child, False) for child in node)

        required_fragments = (
            '"chalksmith.slides.v2"',
            "<BLOCK_CONTRACT>",
            "<MATH_NOTATION>",
            "<LAYOUT_CONTRACT>",
            "<VISUAL_TEACHING_RULES>",
            "<CUSTOM_HTML_RULES>",
            "literal plain text, not Markdown",
            "five structured Blocks before considering custom-html",
            "deck must include at least\none custom-html visual",
            "reconstruct its\nessential teaching relationships",
            "wrap genuine mathematical notation in inline\nKaTeX delimiters",
            "Standard Block typography, spacing, alignment, sizing, and overflow are renderer-owned",
            "steps, phases, and reasoning chains use one numbered list",
            "Never type manual number prefixes or newline-separated pseudo-lists",
            "Write markup inside the fixed layout slot",
            "The outer Block clips overflow",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, prompt)
        for layout in LAYOUTS:
            self.assertIn(f"- {layout}:", prompt)
        for fragment in ('"cell-diagram"', '"force-diagram"', "--cs-bg", "Reveal.initialize({"):
            with self.subTest(forbidden_fragment=fragment):
                self.assertNotIn(fragment, prompt)
        self.assertIn("title", schema["properties"])

    def test_compiler_renders_a_versioned_v2_artifact(self) -> None:
        prepared = StructuredSlidesStrategy().prepare(_slides_fixture())

        self.assertEqual(prepared.spec_version, "chalksmith.slides.v2")
        self.assertEqual(prepared.runtime_version, "slides-runtime.v2.0")
        self.assertEqual(prepared.compiler_version, "slides-compiler.v2.0")
        self.assertIn('data-chalksmith-runtime="slides-runtime.v2.0"', prepared.source_code)
        self.assertIn(slides_compiler.REVEAL_SCRIPT, prepared.source_code)
        self.assertIn(slides_compiler.KATEX_SCRIPT, prepared.source_code)

    def test_every_explicit_layout_renders_without_reordering_blocks(self) -> None:
        for layout, definition in LAYOUTS.items():
            lesson = json.loads(_slides_fixture())
            count = max(definition.slots)
            lesson["payload"]["slides"][0]["layout"] = layout
            lesson["payload"]["slides"][0]["blocks"] = [
                {
                    "type": "key-point",
                    "summary": f"Point {index}",
                    "explanation": f"Explanation {index}",
                    "presentation": "standard",
                    "appearance": "card",
                }
                for index in range(1, count + 1)
            ]

            prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

            self.assertIn(f'data-chalksmith-layout="{layout}"', prepared.source_code)
            positions = [
                prepared.source_code.index(f"Point {index}")
                for index in range(1, count + 1)
            ]
            self.assertEqual(positions, sorted(positions))

    def test_layout_css_preserves_stacked_and_three_column_sizing(self) -> None:
        prepared = StructuredSlidesStrategy().prepare(_slides_fixture())

        self.assertIn(
            ".cs-layout--top-1-bottom-2 {\n"
            "  grid-template-columns: repeat(2, minmax(0, 1fr));\n"
            "  grid-template-rows: auto auto;\n"
            "  align-content: start;\n"
            "}",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-layout--top-2-bottom-1 {\n"
            "  grid-template-columns: repeat(2, minmax(0, 1fr));\n"
            "  grid-template-rows: minmax(0, 1fr) auto;\n"
            "}",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-layout--top-1-bottom-3 {\n"
            "  grid-template-columns: repeat(3, minmax(0, 1fr));\n"
            "  grid-template-rows: auto auto;\n"
            "  align-content: start;\n"
            "}",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-layout--top-3-bottom-1 {\n"
            "  grid-template-columns: repeat(3, minmax(0, 1fr));\n"
            "  grid-template-rows: minmax(0, 1fr) auto;\n"
            "}",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-layout--row-3 {\n"
            "  grid-template-columns: repeat(3, minmax(0, 1fr));\n"
            "}",
            prepared.source_code,
        )
        self.assertNotIn(".cs-layout--row-3 {\n  align-content: start", prepared.source_code)

    def test_incompatible_layout_falls_back_locally_by_block_count(self) -> None:
        lesson = json.loads(_slides_fixture())
        slide = lesson["payload"]["slides"][0]
        slide["layout"] = "top-1-bottom-3"
        slide["blocks"] = [
            {
                "type": "key-point",
                "summary": "Left",
                "explanation": "First",
            },
            {
                "type": "key-point",
                "summary": "Right",
                "explanation": "Second",
            },
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        spec = json.loads(prepared.lesson_spec)

        self.assertEqual(spec["payload"]["slides"][0]["layout"], "row-2")
        self.assertIn('data-chalksmith-layout="row-2"', prepared.source_code)

    def test_unknown_layout_falls_back_locally_by_block_count(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["layout"] = "two-balanced-columns"

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        spec = json.loads(prepared.lesson_spec)

        self.assertEqual(spec["payload"]["slides"][0]["layout"], "single")
        self.assertIn('data-chalksmith-layout="single"', prepared.source_code)

    def test_list_presentations_reuse_existing_visual_patterns(self) -> None:
        lesson = json.loads(_slides_fixture())
        presentations = ("bullets", "numbered", "accent-rows", "timeline", "bands")
        for slide, presentation in zip(lesson["payload"]["slides"], presentations):
            slide["layout"] = "single"
            slide["blocks"] = [
                {
                    "type": "list",
                    "presentation": presentation,
                    "appearance": "card",
                    "items": [
                        {
                            "summary": "First",
                            "explanation": "Explanation",
                            "badge": "1",
                        },
                        {
                            "summary": "Second",
                            "explanation": "Explanation",
                            "badge": "2",
                        },
                    ],
                }
            ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        for presentation in presentations:
            self.assertIn(f"cs-list--{presentation}", prepared.source_code)
        self.assertIn(
            ".cs-list--numbered .cs-item__badge,\n"
            ".cs-list--numbered .cs-item__content {\n"
            "  grid-column: 2;\n"
            "}",
            prepared.source_code,
        )

    def test_key_point_presentations_are_content_agnostic(self) -> None:
        lesson = json.loads(_slides_fixture())
        presentations = ("standard", "accent-bar", "callout", "spotlight", "tagged")
        for slide, presentation in zip(lesson["payload"]["slides"], presentations):
            slide["layout"] = "single"
            slide["blocks"] = [
                {
                    "type": "key-point",
                    "summary": "Summary",
                    "explanation": "Explanation",
                    "badge": "Label",
                    "presentation": presentation,
                    "appearance": "soft",
                }
            ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        for presentation in presentations:
            self.assertIn(f"cs-key-point--{presentation}", prepared.source_code)
        self.assertIn(
            ".cs-item__badge,\n"
            ".cs-key-point__badge {\n"
            "  align-self: start;",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-key-point--tagged {\n"
            "  grid-template-columns: minmax(0, 1fr);\n"
            "}",
            prepared.source_code,
        )
        self.assertIn(
            ".cs-key-point--tagged .cs-key-point__badge {\n"
            "  grid-column: 1;\n"
            "}",
            prepared.source_code,
        )

    def test_compiler_renders_all_six_block_shapes(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0] = {
            "title": "All Blocks",
            "layout": "grid-3-by-2",
            "blocks": [
                {
                    "type": "prose",
                    "paragraphs": ["A paragraph."],
                    "presentation": "body",
                    "appearance": "plain",
                },
                {
                    "type": "list",
                    "items": [{"summary": "A"}, {"summary": "B"}],
                    "presentation": "bullets",
                    "appearance": "card",
                },
                {
                    "type": "key-point",
                    "summary": "Key",
                    "explanation": "Detail",
                    "presentation": "callout",
                    "appearance": "accent",
                },
                {
                    "type": "table",
                    "columns": ["A", "B"],
                    "rows": [["1", "2"]],
                    "appearance": "card",
                },
                {
                    "type": "equation",
                    "items": [{"latex": "a^2+b^2=c^2"}],
                    "appearance": "card",
                },
                {
                    "type": "custom-html",
                    "description": "Triangle model",
                    "html": '<svg viewBox="0 0 100 100"><polygon points="10,90 90,90 10,10"></polygon></svg>',
                },
            ],
        }

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        for class_name in (
            "cs-prose",
            "cs-list",
            "cs-key-point",
            "cs-table",
            "cs-equation",
            "cs-custom",
        ):
            self.assertIn(class_name, prepared.source_code)
        self.assertIn(
            '<div class="cs-table__viewport"><table>',
            prepared.source_code,
        )
        self.assertIn(
            "transform: translate(-50%, -50%) scale(var(--cs-table-scale, 1));",
            prepared.source_code,
        )
        self.assertIn("table-layout: auto;", prepared.source_code)
        self.assertIn(
            ".reveal .cs-table th,\n"
            ".reveal .cs-table td {\n"
            "  padding: 1.15rem 0.8rem;",
            prepared.source_code,
        )
        self.assertIn("overflow-wrap: break-word;", prepared.source_code)
        self.assertIn(
            ".cs-table {\n"
            "  display: grid;\n"
            "  grid-template-rows: minmax(0, 1fr);\n"
            "  padding: 1rem;",
            prepared.source_code,
        )
        self.assertIn(
            'script data-chalksmith-table-fit',
            prepared.source_code,
        )
        self.assertIn(
            "const heightScale = viewport.clientHeight / table.offsetHeight;",
            prepared.source_code,
        )

    def test_list_explanation_does_not_inherit_reveal_small_math_styles(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["blocks"] = [
            {
                "type": "list",
                "items": [
                    {
                        "summary": "First curvature",
                        "explanation": "Use $k_1 = \\frac{1}{2}$.",
                    },
                    {
                        "summary": "Second curvature",
                        "explanation": "Use $k_2 = \\frac{1}{3}$.",
                    },
                ],
                "presentation": "bands",
            }
        ]
        lesson["payload"]["slides"][0]["layout"] = "single"

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(
            '<span class="cs-item__explanation">Use $k_1 = \\frac{1}{2}$.</span>',
            prepared.source_code,
        )
        self.assertNotIn('<small class="cs-item__explanation">', prepared.source_code)
        self.assertIn("data-chalksmith-katex", prepared.source_code)

    def test_equation_block_renders_multiple_ordered_items(self) -> None:
        lesson = json.loads(_slides_fixture())
        equation = lesson["payload"]["slides"][2]["blocks"][1]
        equation["items"] = [
            {"latex": "2x + 3 = 11", "explanation": "Start with the equation."},
            {"latex": "2x = 8", "explanation": "Subtract three from both sides."},
            {"latex": "x = 4", "explanation": "Divide both sides by two."},
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertEqual(prepared.source_code.count('class="cs-equation__item"'), 3)
        positions = [
            prepared.source_code.index(latex)
            for latex in ("2x + 3 = 11", "2x = 8", "x = 4")
        ]
        self.assertEqual(positions, sorted(positions))
        for item in equation["items"]:
            self.assertLess(
                prepared.source_code.index(item["explanation"]),
                prepared.source_code.index(item["latex"]),
            )
        self.assertIn("font-size: 1em", prepared.source_code)
        self.assertIn("font-size: 1.4rem", prepared.source_code)

    def test_single_equation_shape_is_normalized_without_llm_repair(self) -> None:
        lesson = json.loads(_slides_fixture())
        equation = lesson["payload"]["slides"][2]["blocks"][1]
        item = equation.pop("items")[0]
        equation.update(item)

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        persisted = json.loads(prepared.lesson_spec)["payload"]["slides"][2]["blocks"][1]

        self.assertEqual(persisted["items"], [item])
        self.assertNotIn("latex", persisted)
        self.assertNotIn("explanation", persisted)

    def test_custom_html_can_share_layouts_without_a_deck_count_limit(self) -> None:
        lesson = json.loads(_slides_fixture())
        for index, slide in enumerate(lesson["payload"]["slides"]):
            slide["layout"] = "row-2"
            slide["blocks"] = [
                {
                    "type": "key-point",
                    "summary": f"Visual {index}",
                    "explanation": "Read the model.",
                },
                {
                    "type": "custom-html",
                    "description": f"Visual model {index}",
                    "html": f'<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="{20 + index}"></circle></svg>',
                },
            ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertEqual(prepared.source_code.count('aria-label="Visual model'), 5)
        self.assertIn('data-chalksmith-layout="row-2"', prepared.source_code)

    def test_custom_html_scopes_styles_and_ids(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        raw_html = lesson["payload"]["slides"][2]["blocks"][0]["html"]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        persisted = json.loads(prepared.lesson_spec)["payload"]["slides"][2]["blocks"][0]

        self.assertNotEqual(persisted["html"], raw_html)
        self.assertIn("__CS_SCOPE__", persisted["html"])
        self.assertRegex(prepared.source_code, r"\.csx-[0-9a-f]{10} \.csx-[0-9a-f]{10}-base")
        self.assertRegex(prepared.source_code, r'id="csx-[0-9a-f]{10}-bond"')
        self.assertRegex(prepared.source_code, r'url\(#csx-[0-9a-f]{10}-bond\)')

    def test_custom_html_rejects_executable_and_remote_markup(self) -> None:
        for html in (
            "<script>alert(1)</script>",
            '<svg><image href="https://example.com/a.png"></image></svg>',
            '<div onclick="alert(1)">Click</div>',
        ):
            with self.subTest(html=html):
                with self.assertRaises(ValueError):
                    sanitize_slide_html(html)

    def test_parser_recovers_unescaped_quotes_inside_custom_html(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        lesson["payload"]["slides"][2]["blocks"][0]["html"] = (
            '<div class="row"><span class="base a">A</span></div>'
        )
        raw = json.dumps(lesson).replace('\\"', '"')

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        prepared = StructuredSlidesStrategy().prepare(raw)

        self.assertIn("Complementary DNA strands", prepared.source_code)
        self.assertIn("class=", prepared.source_code)

    def test_parser_reports_extra_backslash_from_recovered_custom_html(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        lesson["payload"]["slides"][2]["blocks"][0]["html"] = (
            '<svg><rect fill="var(--cs-surface-raised)"></rect></svg>'
        )
        encoded = json.dumps(lesson)
        raw = encoded.replace(
            r'fill=\"var(--cs-surface-raised)\"',
            r'fill=\"var(--cs-surface-raised)\\"',
        )

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        with self.assertRaisesRegex(ModelOutputError, "invalid backslash escape"):
            StructuredSlidesStrategy().prepare(raw)

    def test_parser_recovers_json_controls_in_equations(self) -> None:
        lesson = json.loads(_slides_fixture())
        encoded = json.dumps(lesson)
        legal = json.dumps(r"\frac{1}{2} \times \frac{2}{2} = \frac{2}{4}")[1:-1]
        raw = encoded.replace(legal, "\\frac{1}{2}\n\\times 2")

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        prepared = StructuredSlidesStrategy().prepare(raw)
        spec = json.loads(prepared.lesson_spec)

        self.assertEqual(
            spec["payload"]["slides"][2]["blocks"][1]["items"][0]["latex"],
            "\\frac{1}{2}\n\\times 2",
        )

    def test_parser_recovers_trailing_commas_and_extra_fields(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["speaker_notes"] = "drop me"
        lesson["payload"]["slides"][0]["blocks"][0]["decorative_color"] = "amber"
        lesson["payload"]["slides"][0]["blocks"] = lesson["payload"]["slides"][0]["blocks"][0]
        raw = json.dumps(lesson).replace("}", ",}", 1)

        prepared = StructuredSlidesStrategy().prepare(raw)
        spec = json.loads(prepared.lesson_spec)

        self.assertNotIn("speaker_notes", spec)
        self.assertNotIn(
            "decorative_color",
            spec["payload"]["slides"][0]["blocks"][0],
        )
        self.assertIsInstance(spec["payload"]["slides"][0]["blocks"], list)

    def test_parser_does_not_repair_truncated_json_locally(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            StructuredSlidesStrategy().prepare(
                '{"schema_version":"chalksmith.slides.v2","format":}'
            )

    def test_repair_prompt_preserves_custom_html_margin(self) -> None:
        prompt = build_slides_repair_prompt(
            "Original instructions",
            '{"payload":{"slides":[]}}',
            ValueError("custom-html.html: String should have at most 6000 characters"),
        )

        self.assertIn(f"below {PROMPT_HTML_LENGTH_TARGET} characters", prompt)
        self.assertIn("shorten it substantially", prompt)
        self.assertNotIn("Original instructions", prompt)
        self.assertIn("Custom HTML rules remain authoritative", prompt)
        self.assertIn("Never use event handlers", prompt)
        self.assertIn("parses\nas strict JSON", prompt)
        self.assertIn("Escape HTML attribute quotes exactly once", prompt)
        self.assertIn("recheck the complete specification", prompt)

    def test_slide_capacity_counts_visible_content(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["blocks"] = [
            {
                "type": "prose",
                "paragraphs": ["x" * 220, "y" * 220, "z" * 220],
            }
        ]

        with self.assertRaisesRegex(ModelOutputError, "slide capacity"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_schema_rejects_removed_subject_specific_blocks(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["blocks"] = [
            {
                "type": "cell-diagram",
                "cell_type": "animal",
                "cell_label": "Animal cell",
                "features": [],
            }
        ]

        with self.assertRaisesRegex(ModelOutputError, "does not match any"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_compiler_escapes_structured_content(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["title"] = "<script>alert(1)</script>"
        lesson["payload"]["slides"][0]["blocks"] = [
            {
                "type": "key-point",
                "summary": "<b>Important</b>",
                "explanation": "Use < and > safely.",
            }
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", prepared.source_code)
        self.assertIn("&lt;b&gt;Important&lt;/b&gt;", prepared.source_code)
        self.assertNotIn("<script>alert(1)</script>", prepared.source_code)

    def test_compiler_omits_katex_when_no_math_is_used(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][2]["blocks"] = [
            {
                "type": "key-point",
                "summary": "Equivalent values",
                "explanation": "The quantities are equal.",
            }
        ]
        lesson["payload"]["slides"][2]["layout"] = "single"

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertNotIn(slides_compiler.KATEX_STYLESHEET, prepared.source_code)
        self.assertNotIn(slides_compiler.KATEX_SCRIPT, prepared.source_code)
        self.assertNotIn("data-chalksmith-katex", prepared.source_code)

    def test_compiler_typesets_inline_math_in_any_structured_text_field(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][2]["blocks"] = [
            {
                "type": "key-point",
                "summary": "Use $x^2$ in the title row.",
                "explanation": "The side satisfies $WX = 4$.",
            }
        ]
        lesson["payload"]["slides"][2]["layout"] = "single"

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(slides_compiler.KATEX_STYLESHEET, prepared.source_code)
        self.assertIn(slides_compiler.KATEX_SCRIPT, prepared.source_code)
        self.assertIn("data-chalksmith-katex", prepared.source_code)
        self.assertIn(
            '{ left: "\\\\(", right: "\\\\)", display: false }',
            prepared.source_code,
        )

    def test_compiler_does_not_treat_currency_as_inline_math(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][2]["blocks"] = [
            {
                "type": "prose",
                "paragraphs": ["Tickets cost $5 to $10."],
            }
        ]
        lesson["payload"]["slides"][2]["layout"] = "single"

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertNotIn(slides_compiler.KATEX_STYLESHEET, prepared.source_code)
        self.assertNotIn("data-chalksmith-katex", prepared.source_code)

    def test_prompt_keeps_dynamic_context_separate(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(
                topic="Fractions",
                lesson_format="slides",
                sources="Teacher source",
                previous_spec='{"schema_version":"chalksmith.slides.v1"}',
                edit_instruction="Add an example.",
            )
        )

        self.assertIn("<SOURCES>Teacher source</SOURCES>", prompt)
        self.assertIn("<EDIT_INSTRUCTION>Add an example.</EDIT_INSTRUCTION>", prompt)
        self.assertIn("<PREVIOUS_SPEC>", prompt)
        self.assertIn("return a complete v2 specification", prompt)

def _custom_html_fixture() -> str:
    """A deck whose worked example contains scoped authored markup."""
    lesson = json.loads(_slides_fixture())
    lesson["payload"]["slides"][2] = {
        "title": "Building strand 2",
        "label": "Visual explanation",
        "layout": "single",
        "blocks": [
            {
                "type": "custom-html",
                "description": "Complementary DNA strands",
                "html": (
                    "<style>.base{padding:.25rem .7rem;border-radius:.4rem}"
                    ".a{background:#ef4444;color:#fff}</style>"
                    '<div><span class="base a">A</span></div>'
                    '<svg viewBox="0 0 40 8"><defs><linearGradient id="bond">'
                    '<stop offset="0%" stop-color="#22c55e"></stop></linearGradient>'
                    '</defs><line x1="0" y1="4" x2="36" y2="4" '
                    'stroke="url(#bond)"></line></svg>'
                ),
            }
        ],
    }
    return json.dumps(lesson)


def _slides_fixture() -> str:
    return (
        Path(__file__).parent / "fixtures" / "lesson_specs" / "slides.json"
    ).read_text(encoding="utf-8")


class LessonSchemaMigrationTests(unittest.TestCase):
    def test_adds_specification_metadata_to_an_existing_lessons_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            engine = create_engine(f"sqlite:///{Path(directory) / 'legacy.db'}")
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "CREATE TABLE lessons ("
                        "id CHAR(32) PRIMARY KEY, "
                        "owner_id VARCHAR(128) NOT NULL"
                        ")"
                    )
                )
                connection.execute(
                    text(
                        "INSERT INTO lessons (id, owner_id) VALUES "
                        "('11111111111111111111111111111111', 'teacher-a')"
                    )
                )

            create_db_and_tables(engine)

            columns = {column["name"] for column in inspect(engine).get_columns("lessons")}
            self.assertTrue(
                {
                    "lesson_spec",
                    "spec_version",
                    "runtime_version",
                    "compiler_version",
                    "first_error",
                    "repair_error",
                    "raw_model_output",
                    "final_lesson_id",
                    "published_at",
                }.issubset(columns)
            )
            self.assertIn("user_profiles", inspect(engine).get_table_names())
            self.assertIn("lesson_tags", inspect(engine).get_table_names())
            self.assertIn("lesson_likes", inspect(engine).get_table_names())
            self.assertIn("lesson_sets", inspect(engine).get_table_names())
            self.assertIn("lesson_set_items", inspect(engine).get_table_names())
            indexes = {index["name"]: index for index in inspect(engine).get_indexes("lessons")}
            self.assertTrue(indexes["uq_lessons_owner_root_version"]["unique"])
            with engine.connect() as connection:
                row = connection.execute(
                    text(
                        "SELECT root_lesson_id, final_lesson_id FROM lessons "
                        "WHERE owner_id = 'teacher-a'"
                    )
                ).one()
            self.assertEqual(row.root_lesson_id, row.final_lesson_id)


if __name__ == "__main__":
    unittest.main()
