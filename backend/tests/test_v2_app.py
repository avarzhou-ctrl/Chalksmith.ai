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
from backend.app.integrations.llm.base import LLMImage, LLMProviderError, LLMResult
from backend.app.integrations.llm.deepseek import DeepSeekProvider
from backend.app.integrations.llm.factory import create_llm_provider
from backend.app.integrations.llm.gemini import VertexGeminiProvider
from backend.app.integrations.llm.openai import OpenAIProvider
from backend.app.integrations.storage import create_storage
from backend.app.integrations.storage.gcp import GCSStorage
from backend.app.integrations.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.lessons.formats import FormatRequest, get_lesson_format_strategy
from backend.app.lessons.formats.code import build_code_generation_prompt, parse_generated_lesson
from backend.app.lessons.formats.slides import compiler as slides_compiler
from backend.app.lessons.formats.slides.registry import (
    BLOCK_DEFINITIONS,
    BLOCK_REGISTRY,
    BLOCK_STYLE_GROUP_ORDER,
    BLOCK_STYLE_GROUPS,
    BLOCK_TYPES,
)
from backend.app.lessons.formats.slides.blocks.custom import (
    PROMPT_HTML_LENGTH_TARGET,
    sanitize_slide_html,
)
from backend.app.lessons.formats.slides.response import build_slides_repair_prompt
from backend.app.lessons.formats.slides.spec import (
    MAX_CUSTOM_HTML_BLOCKS,
    SLIDE_CAPACITY,
    SlidesLessonSpec,
    _block_text_length,
)
from backend.app.lessons.formats.slides.strategy import StructuredSlidesStrategy
from backend.app.lessons.formats.video.compiler import (
    VIDEO_COMPILER_VERSION,
    VIDEO_RUNTIME_END,
    VIDEO_RUNTIME_START,
    VIDEO_RUNTIME_VERSION,
    compile_video,
)
from backend.app.lessons.formats.video.prompt import VIDEO_RULES
from backend.app.lessons.formats.video.strategy import VideoStrategy
from backend.app.lessons.generation import GenerationService, LLMProgress, _public_error
from backend.app.lessons.render.base import RenderError
from backend.app.lessons.render.manim import (
    LocalManimRenderer,
    is_local_renderer_url,
    validate_manim_code,
)
from backend.app.renderer_main import renderer_app


class SettingsTests(unittest.TestCase):
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
        response = self.client.get("/healthz", headers={"X-Request-Id": "test-request"})

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
        record.stage = "rendering"
        record.error = "custom-html exceeds 6000 characters (7124 given)"

        payload = json.loads(JsonFormatter().format(record))

        self.assertEqual(payload["message"], "lesson_generation_retry")
        self.assertEqual(payload["lesson_id"], record.lesson_id)
        self.assertEqual(payload["stage"], "rendering")
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
        self.assertEqual(response.json(), {"detail": "bounded diagnostic"})


class GenerationDeadlineTests(unittest.IsolatedAsyncioTestCase):
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

    async def test_stream_sends_source_images_as_binary_parts(self) -> None:
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
        image = LLMImage("diagram.png", "image/png", b"png-bytes")

        chunks = [chunk async for chunk in provider.stream("prompt", images=(image,))]

        self.assertEqual(chunks[-1].text, "done")
        contents = provider.client.aio.models.generate_content_stream.await_args.kwargs["contents"]
        self.assertEqual(contents[0].text, "prompt")
        self.assertEqual(contents[1].text, "Source image: diagram.png")
        self.assertEqual(contents[2].inline_data.mime_type, "image/png")
        self.assertEqual(contents[2].inline_data.data, b"png-bytes")


class OpenAIImageTests(unittest.IsolatedAsyncioTestCase):
    async def test_generate_sends_source_images_as_data_urls(self) -> None:
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
        image = LLMImage("diagram.jpg", "image/jpeg", b"jpeg-bytes")

        result = await provider.generate("prompt", images=(image,))

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

    def test_prompt_exposes_a_schema_but_not_the_runtime_styles(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(topic="Equivalent fractions", lesson_format="slides")
        )

        self.assertIn('"chalksmith.slides.v1"', prompt)
        self.assertIn("<OUTPUT_CONTRACT>", prompt)
        self.assertIn("<LESSON_REQUIREMENTS>", prompt)
        self.assertIn("<BLOCK_SELECTION>", prompt)
        self.assertIn("<SLIDE_COMPOSITION>", prompt)
        self.assertIn("<LAYOUT_OWNERSHIP>", prompt)
        self.assertEqual(prompt.count("The platform owns all slide composition"), 1)
        self.assertIn("<BLOCK_CATALOG>", prompt)
        self.assertIn("Renders as a horizontal axis", prompt)
        self.assertIn("energy or food pyramids", prompt)
        self.assertIn("branching pathways", prompt)
        self.assertIn("exclusive and shared properties", prompt)
        self.assertIn("many-to-many directed relationships", prompt)
        self.assertIn("ordered categories along a continuous", prompt)
        self.assertIn("nested containment", prompt)
        self.assertIn("forces acting on one object", prompt)
        self.assertIn("particle-level composition", prompt)
        self.assertIn("type-aware plant, animal, or bacterial", prompt)
        self.assertIn("accurate right-angle markings", prompt)
        self.assertIn("Use a semantic Catalog Block whenever one accurately expresses", prompt)
        self.assertIn("avoid more than two", prompt)
        self.assertIn("consecutive text-only slides", prompt)
        self.assertIn("The compiler draws coordinates and mathematical markings", prompt)
        self.assertNotIn('"template"', prompt)
        self.assertNotIn("--cs-bg", prompt)
        self.assertNotIn("Reveal.initialize({", prompt)

    def test_prompt_scopes_authored_markup_to_the_custom_html_block(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(topic="DNA base pairing", lesson_format="slides")
        )

        self.assertIn("Every field is plain text except the html field", prompt)
        self.assertIn("<CUSTOM_HTML_RULES>", prompt)
        self.assertIn("Inline SVG for drawings: circle, clipPath", prompt)
        self.assertIn("Never use: a, animate", prompt)
        self.assertIn(
            f"on no more than\n{MAX_CUSTOM_HTML_BLOCKS} slides", prompt
        )
        # The catalog owns per-Block guidance; the planning notes must not restate it.
        planning_notes = prompt.split("</BLOCK_CATALOG>")[1]
        self.assertNotIn("Use venn-diagram for set overlap", planning_notes)

    def test_parser_recovers_unescaped_quotes_inside_custom_html(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        lesson["payload"]["slides"][2]["body"][0]["html"] = (
            '<div class="row"><span class="base a">A</span></div>'
        )
        raw = json.dumps(lesson).replace('\\"', '"')

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        prepared = StructuredSlidesStrategy().prepare(raw)

        self.assertIn("Complementary DNA strands", prepared.source_code)
        self.assertIn("class=", prepared.source_code)

    def test_parser_escapes_every_illegal_json_string_control(self) -> None:
        lesson = json.loads(_slides_fixture())
        encoded = json.dumps(lesson)
        raw = encoded.replace(
            json.dumps("\\frac{1}{2} \\times \\frac{2}{2} = \\frac{2}{4}")[1:-1],
            '\\frac{1}{2}\n\\times 2',
        )

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        prepared = StructuredSlidesStrategy().prepare(raw)
        spec = json.loads(prepared.lesson_spec)

        self.assertEqual(
            spec["payload"]["slides"][2]["body"][1]["expression"],
            "\\frac{1}{2}\n\\times 2",
        )

    def test_parser_recovers_an_unescaped_quote_before_prose_punctuation(self) -> None:
        lesson = json.loads(_slides_fixture())
        value = 'He said "go", then left'
        lesson["payload"]["slides"][1]["body"][0]["label"] = value
        raw = json.dumps(lesson).replace(json.dumps(value)[1:-1], value)

        with self.assertRaises(json.JSONDecodeError):
            json.loads(raw)
        prepared = StructuredSlidesStrategy().prepare(raw)
        spec = json.loads(prepared.lesson_spec)

        self.assertEqual(spec["payload"]["slides"][1]["body"][0]["label"], value)

    def test_parser_recovers_trailing_commas_and_extra_fields(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["speaker_notes"] = "drop me"
        lesson["payload"]["slides"][0]["layout"] = "title-only"
        lesson["payload"]["slides"][1]["body"][0]["decorative_color"] = "amber"
        lesson["payload"]["slides"][0]["question"] = ""
        lesson["payload"]["slides"][0]["body"] = lesson["payload"]["slides"][0]["body"][0]
        raw = json.dumps(lesson).replace("}", ",}", 1)

        prepared = StructuredSlidesStrategy().prepare(raw)
        spec = json.loads(prepared.lesson_spec)

        self.assertNotIn("speaker_notes", spec)
        self.assertNotIn("layout", spec["payload"]["slides"][0])
        self.assertNotIn("decorative_color", spec["payload"]["slides"][1]["body"][0])
        self.assertIsNone(spec["payload"]["slides"][0]["question"])
        self.assertIsInstance(spec["payload"]["slides"][0]["body"], list)

    def test_parser_does_not_repair_truncated_json_locally(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid JSON"):
            StructuredSlidesStrategy().prepare(
                '{"schema_version":"chalksmith.slides.v1","format":}'
            )

    def test_invalid_json_can_use_the_bounded_model_repair_fallback(self) -> None:
        self.assertTrue(
            StructuredSlidesStrategy().can_repair(
                ValueError("Invalid JSON at line 1, column 12: Expecting ',' delimiter")
            )
        )
        self.assertTrue(
            StructuredSlidesStrategy().can_repair(
                ValueError("The model response did not contain a JSON object.")
            )
        )
        self.assertTrue(
            StructuredSlidesStrategy().can_repair(
                ValueError("Invalid Slides specification: payload.slides: Field required")
            )
        )

    def test_prompt_requires_json_escaping_inside_custom_html(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(topic="The rock cycle", lesson_format="slides")
        )

        self.assertIn("In that JSON string", prompt)
        self.assertIn('escape every double quote as \\"', prompt)
        self.assertIn(str(SLIDE_CAPACITY), prompt)
        self.assertIn(f"under {PROMPT_HTML_LENGTH_TARGET} characters", prompt)

    def test_repair_prompt_leaves_margin_for_overlong_custom_html(self) -> None:
        prompt = build_slides_repair_prompt(
            "Original instructions",
            '{"payload":{"slides":[]}}',
            ValueError("custom-html.html: String should have at most 6000 characters"),
        )

        self.assertIn(
            f"below {PROMPT_HTML_LENGTH_TARGET} characters",
            prompt,
        )
        self.assertIn("shorten it substantially", prompt)

    def test_prompt_keeps_dynamic_context_separate_from_its_instructions(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(
                topic="Fractions",
                lesson_format="slides",
                sources="Teacher source",
                previous_spec='{"title":"Previous"}',
                edit_instruction="Add an example.",
            )
        )

        self.assertEqual(prompt.count("use them as the factual basis"), 1)
        self.assertEqual(prompt.count("preserve working teaching content"), 1)
        self.assertIn("<SOURCES>Teacher source</SOURCES>", prompt)
        self.assertIn("<EDIT_INSTRUCTION>Add an example.</EDIT_INSTRUCTION>", prompt)

    def test_custom_html_scopes_author_styles_and_identifiers(self) -> None:
        prepared = StructuredSlidesStrategy().prepare(_custom_html_fixture())

        self.assertIn(
            'data-style-groups="content,math,custom,comprehension"', prepared.source_code
        )
        self.assertRegex(
            prepared.source_code, r'class="cs-card cs-custom csx-[0-9a-f]{10}"'
        )
        self.assertRegex(
            prepared.source_code,
            r"\.csx-[0-9a-f]{10} \.csx-[0-9a-f]{10}-base\{",
        )
        self.assertNotIn('class="progress"', prepared.source_code)
        self.assertRegex(prepared.source_code, r'id="csx-[0-9a-f]{10}-bond"')
        self.assertRegex(prepared.source_code, r'stroke="url\(#csx-[0-9a-f]{10}-bond\)"')
        self.assertIn('aria-label="Complementary DNA strands"', prepared.source_code)
        persisted = json.loads(prepared.lesson_spec)["payload"]["slides"][2]["body"][0]
        self.assertIn("__CS_SCOPE__", persisted["html"])
        self.assertNotIn("__CS_SCOPE__", prepared.source_code)

    def test_custom_html_rejects_executable_and_remote_markup(self) -> None:
        for markup in (
            "<div><script>alert(1)</script></div>",
            '<div onclick="steal()">x</div>',
            '<a href="https://example.com">x</a>',
            '<img src="https://example.com/x.png">',
            "<iframe></iframe>",
            "<style>@import url(https://example.com/x.css);</style><p>x</p>",
            "<style>body { display: none; }</style><p>x</p>",
            '<div style="background:url(https://example.com/x.png)">x</div>',
        ):
            with self.subTest(markup=markup):
                with self.assertRaises(ValueError):
                    sanitize_slide_html(markup)

    def test_custom_html_strips_unsupported_styling_without_failing(self) -> None:
        self.assertEqual(
            sanitize_slide_html('<div style="position:fixed;top:0;color:red">x</div>'),
            '<div style="color:red">x</div>',
        )
        self.assertEqual(
            sanitize_slide_html('<marquee><p class="cs-card reveal keep">y</p></marquee>'),
            '<p class="__CS_SCOPE__-keep">y</p>',
        )
        self.assertEqual(
            sanitize_slide_html(
                '<svg viewBox="0 0 4 4"><rect x="1" bogus="2"></rect></svg>'
            ),
            '<svg viewBox="0 0 4 4"><rect x="1"></rect></svg>',
        )

    def test_custom_html_capacity_counts_learner_visible_text(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        block = lesson["payload"]["slides"][2]["body"][0]
        block["html"] = f'<div style="{"color:#fff;" * 200}">{"A" * 40}</div>'

        StructuredSlidesStrategy().prepare(json.dumps(lesson))

        block["html"] = f"<p>{'A' * (SLIDE_CAPACITY + 1)}</p>"
        with self.assertRaisesRegex(ValueError, "exceeds the slide capacity"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_slide_capacity_counts_decoded_on_slide_text_only(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][2]["body"] = [
            {
                "type": "custom-html",
                "description": "A" * 120,
                "html": "<p>Heat &amp; Pressure</p>",
            }
        ]
        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        spec = SlidesLessonSpec.model_validate_json(prepared.lesson_spec)
        self.assertEqual(_block_text_length(spec.payload.slides[2].body[0]), 15)

        lesson["payload"]["slides"][2]["body"] = [
            {
                "type": "hierarchy-tree",
                "root": {"label": "Rocks", "detail": "Origin"},
                "branches": [
                    {
                        "label": "Igneous",
                        "children": [{"label": "Granite", "detail": "Slow cooling"}],
                    },
                    {
                        "label": "Sedimentary",
                        "children": [{"label": "Sandstone", "detail": "Cemented grains"}],
                    },
                ],
            }
        ]
        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        spec = SlidesLessonSpec.model_validate_json(prepared.lesson_spec)
        self.assertEqual(_block_text_length(spec.payload.slides[2].body[0]), 72)

    def test_deck_limits_how_many_slides_may_author_markup(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        authored = lesson["payload"]["slides"][2]
        lesson["payload"]["slides"] = [
            dict(authored, title=f"Slide {index}")
            for index in range(MAX_CUSTOM_HTML_BLOCKS + 1)
        ]

        with self.assertRaisesRegex(
            ValueError,
            f"at most {MAX_CUSTOM_HTML_BLOCKS} slides may use custom-html",
        ):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_deck_allows_five_custom_html_slides(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        authored = lesson["payload"]["slides"][2]
        lesson["payload"]["slides"] = [
            dict(authored, title=f"Slide {index}")
            for index in range(MAX_CUSTOM_HTML_BLOCKS)
        ]

        StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_custom_html_namespaces_reveal_classes_and_unwraps_sections(self) -> None:
        sanitized = sanitize_slide_html(
            '<section><div class="progress fragment keep">Visible</div></section>'
            '<style>.progress,.fragment,.keep{color:red}</style>'
        )

        self.assertNotIn("<section", sanitized)
        self.assertIn(
            'class="__CS_SCOPE__-progress __CS_SCOPE__-fragment '
            '__CS_SCOPE__-keep"',
            sanitized,
        )
        self.assertIn(".__CS_SCOPE__-progress", sanitized)
        self.assertIn(".__CS_SCOPE__-fragment", sanitized)
        self.assertNotIn(".progress,", sanitized)

        # Sanitized markup is canonical lesson data and must survive a later edit unchanged.
        self.assertEqual(sanitize_slide_html(sanitized), sanitized)

    def test_custom_html_must_occupy_the_slide_body_alone(self) -> None:
        lesson = json.loads(_custom_html_fixture())
        lesson["payload"]["slides"][2]["body"].append(
            {"type": "statement", "text": "Pairing is always A with T."}
        )

        with self.assertRaisesRegex(ValueError, "must occupy a slide body by themselves"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_block_catalog_covers_every_schema_block(self) -> None:
        schema = SlidesLessonSpec.model_json_schema()
        body_items = schema["$defs"]["SlideSpec"]["properties"]["body"]["items"]

        self.assertEqual(set(body_items["discriminator"]["mapping"]), BLOCK_TYPES)

    def test_block_registry_colocates_model_guide_and_renderer(self) -> None:
        self.assertEqual(set(BLOCK_REGISTRY), BLOCK_TYPES)
        self.assertEqual(set(BLOCK_STYLE_GROUPS), BLOCK_TYPES)
        self.assertEqual(set(BLOCK_STYLE_GROUPS.values()), set(BLOCK_STYLE_GROUP_ORDER))
        for group in BLOCK_STYLE_GROUP_ORDER:
            self.assertTrue(slides_compiler._BLOCK_STYLE_PATHS[group].is_file())
        self.assertEqual(len(BLOCK_DEFINITIONS), len(BLOCK_TYPES))
        for definition in BLOCK_DEFINITIONS:
            block_type = definition.model.model_json_schema()["properties"]["type"][
                "const"
            ]
            self.assertEqual(definition.guide.type, block_type)
            self.assertTrue(callable(definition.renderer))

    def test_compiler_escapes_content_and_owns_the_document(self) -> None:
        response = _slides_fixture().replace(
            "Equivalent Fractions", "Fractions <script>alert(1)</script>"
        )
        prepared = StructuredSlidesStrategy().prepare(response)

        self.assertIn("Fractions &lt;script&gt;alert(1)&lt;/script&gt;", prepared.source_code)
        self.assertNotIn("<script>alert(1)</script>", prepared.source_code)
        self.assertIn('data-chalksmith-runtime="slides-runtime.v1.1"', prepared.source_code)
        self.assertIn('.slides > section.present', prepared.source_code)
        self.assertIn(
            ".reveal .cs-card ul,\n.reveal .cs-card ol {\n  margin: 0;",
            prepared.source_code,
        )
        self.assertIn(".cs-list ul,\n.cs-steps ol {\n  display: grid;", prepared.source_code)
        self.assertEqual(prepared.spec_version, "chalksmith.slides.v1")
        self.assertNotIn("data-chalksmith-template", prepared.source_code)

    def test_comparison_list_rows_align_at_the_start(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"] = [
            {
                "type": "comparison",
                "left_title": "Before",
                "left_items": ["One", "Two"],
                "right_title": "After",
                "right_items": ["Three", "Four"],
            }
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn('class="cs-comparison"', prepared.source_code)
        self.assertIn(
            ".cs-comparison ul {\n  display: grid;\n  align-content: start;",
            prepared.source_code,
        )

    def test_compiler_rereads_runtime_styles_for_each_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            core_path = Path(directory) / "core.css"
            content_path = Path(directory) / "content.css"
            core_path.write_text(":root { color-scheme: dark; }", encoding="utf-8")
            content_path.write_text(
                ".cs-callout { align-content: center; }", encoding="utf-8"
            )

            with (
                patch.object(slides_compiler, "_CORE_STYLE_PATH", core_path),
                patch.dict(
                    slides_compiler._BLOCK_STYLE_PATHS,
                    {"content": content_path},
                ),
            ):
                self.assertIn(
                    "align-content: center",
                    slides_compiler._slides_styles(("content",)),
                )
                content_path.write_text(
                    ".cs-callout { align-content: start; }", encoding="utf-8"
                )
                self.assertIn(
                    "align-content: start",
                    slides_compiler._slides_styles(("content",)),
                )

    def test_compiler_embeds_only_required_style_groups(self) -> None:
        prepared = StructuredSlidesStrategy().prepare(_slides_fixture())

        self.assertIn(
            'data-style-groups="content,math,comprehension"', prepared.source_code
        )
        for group in ("Content", "Math", "Comprehension"):
            self.assertIn(f"/* Slides {group} styles. */", prepared.source_code)
        for group in ("Data", "Diagrams", "Physics", "Chemistry", "Biology"):
            self.assertNotIn(f"/* Slides {group} styles. */", prepared.source_code)

    def test_compiler_omits_katex_when_no_equation_block_is_used(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][2]["body"] = [
            {"type": "statement", "text": "One half and two fourths are equal."}
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertNotIn(slides_compiler.KATEX_STYLESHEET, prepared.source_code)
        self.assertNotIn(slides_compiler.KATEX_SCRIPT, prepared.source_code)
        self.assertNotIn(slides_compiler.KATEX_AUTO_RENDER_SCRIPT, prepared.source_code)
        self.assertNotIn("data-chalksmith-katex", prepared.source_code)

    def test_schema_allows_the_prompt_to_adapt_the_teaching_sequence(self) -> None:
        adapted = _slides_fixture().replace(
            '"kind": "learning-goal"', '"kind": "concept"'
        ).replace(
            '"kind": "worked-example"', '"kind": "concept"'
        ).replace(
            '"kind": "recap"', '"kind": "concept"'
        )

        prepared = StructuredSlidesStrategy().prepare(adapted)

        self.assertEqual(prepared.spec_version, "chalksmith.slides.v1")

    def test_schema_rejects_a_complex_block_in_a_multi_block_body(self) -> None:
        malformed = json.loads(_slides_fixture())
        malformed["payload"]["slides"][0]["body"].append(
            {"type": "process", "steps": ["Observe", "Explain"]}
        )

        with self.assertRaisesRegex(ValueError, "must occupy a slide body by themselves"):
            StructuredSlidesStrategy().prepare(json.dumps(malformed))

    def test_compiler_selects_a_visual_layout_and_places_the_visual_second(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"].append(
            {
                "type": "fraction-model",
                "numerator": 2,
                "denominator": 3,
                "label": "Two thirds",
            }
        )

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))
        body_start = prepared.source_code.index('data-chalksmith-layout="visual-split"')
        statement_start = prepared.source_code.index("cs-statement", body_start)
        fraction_start = prepared.source_code.index("cs-fraction", body_start)

        self.assertLess(statement_start, fraction_start)

    def test_compiler_renders_the_visual_block_vocabulary(self) -> None:
        lesson = json.loads(_slides_fixture())
        blocks = [
            {
                "type": "number-line",
                "min_value": -5,
                "max_value": 5,
                "markers": [{"value": -2, "label": "negative two"}, {"value": 3}],
            },
            {
                "type": "bar-model",
                "parts": [
                    {"label": "Read", "value": 30},
                    {"label": "Remaining", "value": 10},
                ],
                "total_label": "40 pages",
            },
            {
                "type": "bar-chart",
                "items": [
                    {"label": "Monday", "value": 3},
                    {"label": "Tuesday", "value": 7},
                ],
                "unit": "cm",
            },
            {
                "type": "coordinate-plot",
                "x_min": -5,
                "x_max": 5,
                "y_min": -5,
                "y_max": 5,
                "points": [{"x": 2, "y": 3, "label": "A"}],
            },
            {
                "type": "geometry-model",
                "shape": "triangle",
                "labels": [
                    {"position": "bottom", "text": "base = 8 cm"},
                    {"position": "right", "text": "height = 5 cm"},
                ],
            },
            {
                "type": "labeled-diagram",
                "subject": "Cell <core>",
                "labels": ["Membrane", "Nucleus", "Cytoplasm"],
            },
            {
                "type": "cycle",
                "steps": ["Evaporation", "Condensation", "Precipitation"],
            },
            {
                "type": "timeline",
                "events": [
                    {"label": "1609", "text": "Galileo studies the sky"},
                    {"label": "1969", "text": "Humans reach the Moon"},
                ],
            },
        ]
        lesson["payload"]["slides"] = [
            {"kind": "visual-explanation", "title": f"Visual {index}", "body": [block]}
            for index, block in enumerate(blocks, start=1)
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(
            'data-style-groups="data,diagrams,math"', prepared.source_code
        )
        for class_name in (
            "cs-number-line",
            "cs-bar-model",
            "cs-bar-chart",
            "cs-coordinate-plot",
            "cs-geometry",
            "cs-labeled-diagram",
            "cs-cycle",
            "cs-timeline",
        ):
            self.assertIn(class_name, prepared.source_code)
        self.assertIn("Cell &lt;core&gt;", prepared.source_code)

    def test_geometry_model_renders_a_semantic_right_triangle(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][1] = {
            "kind": "visual-explanation",
            "title": "A labeled right triangle",
            "body": [
                {
                    "type": "geometry-model",
                    "shape": "triangle",
                    "triangle_type": "right",
                    "labels": [
                        {"position": "left", "text": "leg b"},
                        {"position": "bottom", "text": "leg a"},
                        {"position": "right", "text": "hypotenuse c"},
                    ],
                    "points": [
                        {"position": "top", "label": "B"},
                        {"position": "bottom-left", "label": "C"},
                        {"position": "bottom-right", "label": "A"},
                    ],
                }
            ],
        }

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(
            '<polygon points="135.0,45.0 135.0,285.0 540.0,285.0"',
            prepared.source_code,
        )
        self.assertIn('class="cs-geometry__right-angle"', prepared.source_code)
        self.assertIn(">hypotenuse c</text>", prepared.source_code)
        self.assertIn(">C</text></g>", prepared.source_code)

    def test_geometry_model_renders_concurrent_cevians(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][1] = {
            "kind": "visual-explanation",
            "title": "Cevians meet at P",
            "body": [
                {
                    "type": "geometry-model",
                    "shape": "triangle",
                    "triangle_type": "scalene",
                    "points": [
                        {"position": "top", "label": "A"},
                        {"position": "bottom-left", "label": "B"},
                        {"position": "bottom-right", "label": "C"},
                        {"position": "bottom", "label": "D"},
                        {"position": "right", "label": "E"},
                        {"position": "left", "label": "F"},
                        {"position": "center", "label": "P"},
                    ],
                    "segments": [
                        {"start": "top", "end": "bottom"},
                        {"start": "bottom-left", "end": "right"},
                        {"start": "bottom-right", "end": "left"},
                    ],
                }
            ],
        }

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertEqual(
            prepared.source_code.count('<g class="cs-geometry__segment '), 3
        )
        self.assertEqual(
            prepared.source_code.count('<g class="cs-geometry__point">'), 7
        )
        self.assertIn('cx="306.7" cy="205.0"', prepared.source_code)

    def test_geometry_model_marks_congruent_triangle_sides(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][1]["body"] = [
            {
                "type": "geometry-model",
                "shape": "triangle",
                "triangle_type": "isosceles",
            }
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(
            '<polygon points="320.0,45.0 115.0,285.0 525.0,285.0"',
            prepared.source_code,
        )
        self.assertEqual(
            prepared.source_code.count('class="cs-geometry__congruence"'), 2
        )

    def test_geometry_model_rejects_an_anchor_outside_the_shape(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][1]["body"] = [
            {
                "type": "geometry-model",
                "shape": "circle",
                "points": [{"position": "bottom-left", "label": "A"}],
            }
        ]

        with self.assertRaisesRegex(ValueError, "valid anchors for a circle"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_compiler_renders_the_relationship_diagram_library(self) -> None:
        lesson = json.loads(_slides_fixture())
        blocks = [
            {
                "type": "pyramid-diagram",
                "levels": [
                    {
                        "label": "Tertiary consumers",
                        "detail": "Apex predators",
                        "value": "10 kcal",
                    },
                    {
                        "label": "Primary consumers",
                        "detail": "Herbivores",
                        "value": "1,000 kcal",
                    },
                    {
                        "label": "Producers <base>",
                        "detail": "Plants",
                        "value": "10,000 kcal",
                    },
                ],
                "trend_label": "Available energy decreases upward",
            },
            {
                "type": "hierarchy-tree",
                "root": {"label": "Matter"},
                "branches": [
                    {
                        "label": "Pure substances",
                        "children": [{"label": "Elements"}, {"label": "Compounds"}],
                    },
                    {
                        "label": "Mixtures",
                        "children": [
                            {"label": "Homogeneous"},
                            {"label": "Heterogeneous"},
                        ],
                    },
                ],
            },
            {
                "type": "flow-diagram",
                "stages": [
                    {
                        "label": "Input",
                        "nodes": [{"label": "Sunlight"}, {"label": "Water"}],
                    },
                    {
                        "label": "Process",
                        "nodes": [
                            {
                                "label": "Photosynthesis",
                                "detail": "In chloroplasts",
                            }
                        ],
                    },
                    {
                        "label": "Output",
                        "nodes": [{"label": "Glucose"}, {"label": "Oxygen"}],
                    },
                ],
            },
        ]
        for slide, block in zip(lesson["payload"]["slides"], blocks):
            slide["kind"] = "visual-explanation"
            slide["body"] = [block]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        for class_name in ("cs-pyramid", "cs-hierarchy", "cs-flow-diagram"):
            self.assertIn(class_name, prepared.source_code)
        self.assertIn("Producers &lt;base&gt;", prepared.source_code)
        self.assertIn("--cs-pyramid-width: 100.0%", prepared.source_code)
        self.assertIn("--cs-hierarchy-columns: 2", prepared.source_code)
        self.assertIn("--cs-flow-columns: 3", prepared.source_code)
        self.assertIn(".cs-hierarchy .cs-hierarchy__branches", prepared.source_code)

    def test_schema_rejects_duplicate_pyramid_levels(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"] = [
            {
                "type": "pyramid-diagram",
                "levels": [
                    {"label": "Consumers"},
                    {"label": "consumers"},
                    {"label": "Producers"},
                ],
            }
        ]

        with self.assertRaisesRegex(ValueError, "level labels must be unique"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_compiler_renders_the_extended_relationship_diagram_library(self) -> None:
        lesson = json.loads(_slides_fixture())
        blocks = [
            {
                "type": "venn-diagram",
                "left_title": "Plant cells",
                "left_items": ["Cell wall", "Chloroplasts"],
                "right_title": "Animal cells",
                "right_items": ["Centrioles", "Flexible shape"],
                "overlap_title": "Both",
                "overlap_items": ["Nucleus", "Cell membrane"],
            },
            {
                "type": "cause-effect-diagram",
                "effect_label": "Effect",
                "effect": "Algal bloom",
                "effect_detail": "Rapid algae growth",
                "groups": [
                    {
                        "label": "Nutrients",
                        "causes": ["Fertilizer runoff", "Sewage"],
                    },
                    {
                        "label": "Conditions",
                        "causes": ["Warm water", "Strong sunlight"],
                    },
                ],
            },
            {
                "type": "layer-diagram",
                "layers": [
                    {
                        "label": "Crust",
                        "detail": "Thin solid surface",
                        "property": "5–70 km",
                    },
                    {
                        "label": "Mantle",
                        "detail": "Slow-flowing rock",
                        "property": "2,900 km",
                    },
                    {
                        "label": "Outer core",
                        "detail": "Liquid iron and nickel",
                        "property": "Liquid",
                    },
                    {
                        "label": "Inner core",
                        "detail": "Solid metal center",
                        "property": "Hottest",
                    },
                ],
                "order_label": "Surface to center",
            },
            {
                "type": "network-diagram",
                "description": "Energy links in a grassland food web",
                "layers": [
                    {
                        "label": "Producers",
                        "nodes": [
                            {"id": "grass", "label": "Grass"},
                            {"id": "seeds", "label": "Seeds"},
                        ],
                    },
                    {
                        "label": "Consumers",
                        "nodes": [
                            {"id": "rabbit", "label": "Rabbit"},
                            {"id": "mouse", "label": "Mouse"},
                        ],
                    },
                    {
                        "label": "Predators",
                        "nodes": [{"id": "hawk", "label": "Hawk"}],
                    },
                ],
                "edges": [
                    {"from_id": "grass", "to_id": "rabbit"},
                    {"from_id": "seeds", "to_id": "mouse"},
                    {"from_id": "rabbit", "to_id": "hawk"},
                    {"from_id": "mouse", "to_id": "hawk"},
                ],
            },
            {
                "type": "quadrant-diagram",
                "x_low_label": "Low conductivity",
                "x_high_label": "High conductivity",
                "y_low_label": "Weak magnetism",
                "y_high_label": "Strong magnetism",
                "top_left": {
                    "label": "Magnetic insulators",
                    "items": ["Ferrite"],
                },
                "top_right": {
                    "label": "Magnetic conductors",
                    "items": ["Iron", "Steel"],
                },
                "bottom_left": {
                    "label": "Insulators",
                    "items": ["Rubber", "Glass"],
                },
                "bottom_right": {
                    "label": "Conductors",
                    "items": ["Copper", "Aluminum"],
                },
            },
            {
                "type": "spectrum-diagram",
                "bands": [
                    {"label": "Radio", "detail": "Longest wavelength"},
                    {"label": "Microwave"},
                    {"label": "Infrared"},
                    {"label": "Visible"},
                    {"label": "Ultraviolet"},
                    {"label": "X-ray"},
                    {"label": "Gamma", "detail": "Shortest wavelength"},
                ],
                "low_label": "Low frequency",
                "high_label": "High frequency",
                "trend_label": "Frequency increases",
            },
            {
                "type": "concentric-diagram",
                "rings": [
                    {"label": "Organism", "detail": "One living individual"},
                    {"label": "Organ system"},
                    {"label": "Organ"},
                    {"label": "Tissue"},
                    {"label": "Cell", "detail": "Smallest living unit"},
                ],
                "direction_label": "Outer organization to inner structure",
            },
            {
                "type": "matrix-diagram",
                "row_axis_label": "Parent 1",
                "column_axis_label": "Parent 2",
                "row_headers": ["B", "b"],
                "column_headers": ["B", "b"],
                "cells": [["BB", "Bb"], ["Bb", "bb"]],
            },
        ]
        lesson["payload"]["slides"] = [
            {
                "kind": "visual-explanation",
                "title": f"Relationship {index}",
                "body": [block],
            }
            for index, block in enumerate(blocks, start=1)
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        for class_name in (
            "cs-venn",
            "cs-cause-effect",
            "cs-layers",
            "cs-network",
            "cs-quadrant",
            "cs-spectrum",
            "cs-concentric",
            "cs-matrix",
        ):
            self.assertIn(class_name, prepared.source_code)
        self.assertIn("<svg viewBox=\"0 0 1000 420\"", prepared.source_code)
        self.assertIn("Plant cells", prepared.source_code)
        self.assertNotIn("<section class=\"cs-quadrant__region", prepared.source_code)
        self.assertIn("<div class=\"cs-quadrant__region", prepared.source_code)

    def test_schema_rejects_a_backward_network_edge(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"] = [
            {
                "type": "network-diagram",
                "description": "An invalid backward dependency",
                "layers": [
                    {
                        "label": "Inputs",
                        "nodes": [
                            {"id": "a", "label": "A"},
                            {"id": "b", "label": "B"},
                        ],
                    },
                    {
                        "label": "Outputs",
                        "nodes": [{"id": "c", "label": "C"}],
                    },
                ],
                "edges": [
                    {"from_id": "a", "to_id": "c"},
                    {"from_id": "c", "to_id": "b"},
                ],
            }
        ]

        with self.assertRaisesRegex(ValueError, "earlier to a later layer"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_compiler_renders_subject_specific_diagram_blocks(self) -> None:
        lesson = json.loads(_slides_fixture())
        blocks = [
            {
                "type": "function-graph",
                "x_min": -2,
                "x_max": 2,
                "y_min": -1,
                "y_max": 4,
                "series": [
                    {
                        "label": "y = x²",
                        "points": [
                            {"x": -2, "y": 4},
                            {"x": -1, "y": 1},
                            {"x": 0, "y": 0},
                            {"x": 1, "y": 1},
                            {"x": 2, "y": 4},
                        ],
                    }
                ],
            },
            {
                "type": "force-diagram",
                "object_label": "Book",
                "description": "Forces on a book resting on a table",
                "forces": [
                    {
                        "direction": "up",
                        "label": "Normal force",
                        "magnitude": "10 N",
                    },
                    {
                        "direction": "down",
                        "label": "Weight",
                        "magnitude": "10 N",
                    },
                ],
            },
            {
                "type": "wave-diagram",
                "description": "Parts of a transverse wave",
                "equilibrium_label": "Rest position",
                "amplitude_label": "Amplitude",
                "wavelength_label": "One wavelength",
                "crest_label": "Crest",
                "trough_label": "Trough",
            },
            {
                "type": "particle-diagram",
                "samples": [
                    {
                        "label": "Element",
                        "species": [
                            {"formula": "O₂", "atoms": ["O", "O"], "count": 4}
                        ],
                    },
                    {
                        "label": "Compound",
                        "species": [
                            {
                                "formula": "H₂O",
                                "atoms": ["H", "O", "H"],
                                "count": 4,
                            }
                        ],
                    },
                    {
                        "label": "Mixture",
                        "species": [
                            {"formula": "N₂", "atoms": ["N", "N"], "count": 3},
                            {"formula": "O₂", "atoms": ["O", "O"], "count": 2},
                        ],
                    },
                ],
            },
            {
                "type": "reaction-diagram",
                "reactants": [
                    {"coefficient": 2, "formula": "H₂", "name": "Hydrogen"},
                    {"formula": "O₂", "name": "Oxygen"},
                ],
                "products": [
                    {"coefficient": 2, "formula": "H₂O", "name": "Water"}
                ],
                "condition": "spark",
                "caption": "Atoms are rearranged, not created or destroyed.",
            },
            {
                "type": "cell-diagram",
                "cell_type": "plant",
                "cell_label": "Plant cell",
                "features": [
                    {
                        "feature": "cell-wall",
                        "label": "Cell wall",
                        "function": "Rigid support",
                    },
                    {
                        "feature": "cell-membrane",
                        "label": "Cell membrane",
                        "function": "Controls entry and exit",
                    },
                    {
                        "feature": "nucleus",
                        "label": "Nucleus",
                        "function": "Stores genetic information",
                    },
                    {
                        "feature": "chloroplast",
                        "label": "Chloroplast",
                        "function": "Captures light energy",
                    },
                    {
                        "feature": "vacuole",
                        "label": "Central vacuole",
                        "function": "Stores water",
                    },
                ],
            },
        ]
        lesson["payload"]["slides"] = [
            {
                "kind": "visual-explanation",
                "title": f"Subject visual {index}",
                "body": [block],
            }
            for index, block in enumerate(blocks, start=1)
        ]

        prepared = StructuredSlidesStrategy().prepare(json.dumps(lesson))

        self.assertIn(
            'data-style-groups="math,physics,chemistry,biology"',
            prepared.source_code,
        )
        for class_name in (
            "cs-function-graph",
            "cs-force-diagram",
            "cs-wave-diagram",
            "cs-particle-diagram",
            "cs-reaction-diagram",
            "cs-cell-diagram",
        ):
            self.assertIn(class_name, prepared.source_code)
        self.assertIn("cs-particle-diagram__atom--color-1\">O", prepared.source_code)
        self.assertNotIn("cs-particle-diagram__atom--2", prepared.source_code)

    def test_schema_rejects_an_organelle_incompatible_with_the_cell_type(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"] = [
            {
                "type": "cell-diagram",
                "cell_type": "animal",
                "cell_label": "Animal cell",
                "features": [
                    {"feature": "nucleus", "label": "Nucleus"},
                    {"feature": "cell-membrane", "label": "Cell membrane"},
                    {"feature": "chloroplast", "label": "Chloroplast"},
                ],
            }
        ]

        with self.assertRaisesRegex(ValueError, "animal cell does not support"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))

    def test_schema_rejects_visual_coordinates_outside_the_declared_range(self) -> None:
        lesson = json.loads(_slides_fixture())
        lesson["payload"]["slides"][0]["body"] = [
            {
                "type": "coordinate-plot",
                "x_min": -5,
                "x_max": 5,
                "y_min": -5,
                "y_max": 5,
                "points": [{"x": 8, "y": 1}],
            }
        ]

        with self.assertRaisesRegex(ValueError, "points must stay inside its axes"):
            StructuredSlidesStrategy().prepare(json.dumps(lesson))


def _custom_html_fixture() -> str:
    """A deck whose worked example is author-written markup instead of a Block."""
    lesson = json.loads(_slides_fixture())
    lesson["payload"]["slides"][2] = {
        "kind": "worked-example",
        "title": "Building strand 2",
        "body": [
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
                    "raw_model_output",
                    "final_lesson_id",
                    "published_at",
                }.issubset(columns)
            )
            self.assertIn("user_profiles", inspect(engine).get_table_names())
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
