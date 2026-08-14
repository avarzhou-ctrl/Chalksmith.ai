import asyncio
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

from backend.app.core.config import LOCAL_CLERK_FILE, LOCAL_ENV_FILE, REPOSITORY_DIR, Settings
from backend.app.core.errors import AppError
from backend.app.integrations.auth import _decode_clerk_token, get_current_user
from backend.app.integrations.llm.base import LLMResult
from backend.app.integrations.llm.base import LLMProviderError
from backend.app.integrations.llm.deepseek import DeepSeekProvider
from backend.app.integrations.llm.factory import create_llm_provider
from backend.app.integrations.llm.gemini import VertexGeminiProvider
from backend.app.integrations.storage import GCSStorage
from backend.app.main import create_app
from backend.app.renderers.base import RenderError
from backend.app.renderers.manim import LocalManimRenderer, is_local_renderer_url, validate_manim_code
from backend.app.renderer_main import renderer_app
from backend.app.services.generation import GenerationService, LLMProgress


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
    @patch("backend.app.integrations.storage.impersonated_credentials.Credentials")
    @patch("backend.app.integrations.storage.storage.Client")
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
        )

        with patch("backend.app.services.generation.LLM_HEARTBEAT_SECONDS", 0.001):
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
            "backend.app.renderers.manim.asyncio.create_subprocess_exec",
            new=AsyncMock(return_value=process),
        ), patch("backend.app.renderers.manim.os.killpg") as kill_process_group:
            task = asyncio.create_task(renderer.render(code, Path(directory)))
            await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task

        kill_process_group.assert_called_once_with(process.pid, signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
