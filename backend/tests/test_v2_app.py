import asyncio
import os
import signal
import tempfile
import unittest
from pathlib import Path
from time import monotonic
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.main import create_app
from backend.app.renderers.base import RenderError
from backend.app.renderers.manim import LocalManimRenderer, is_local_renderer_url, validate_manim_code
from backend.app.renderer_main import renderer_app
from backend.app.services.generation import GenerationService


class SettingsTests(unittest.TestCase):
    def test_settings_load_selected_provider_and_origins(self) -> None:
        environment = {
            "APP_ENV": "test",
            "FRONTEND_ORIGINS": "http://localhost:3000,https://app.chalksmith.ai/",
            "LLM_PROVIDER": "openai",
            "LLM_TIMEOUT_SECONDS": "45",
        }

        with patch.dict(os.environ, environment, clear=True):
            settings = Settings.from_env()

        self.assertEqual(settings.app_env, "test")
        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.llm_timeout_seconds, 45)
        self.assertEqual(
            settings.frontend_origins,
            ("http://localhost:3000", "https://app.chalksmith.ai"),
        )

    def test_settings_reject_relative_frontend_origin(self) -> None:
        with self.assertRaises(ValueError):
            Settings(frontend_origins=("localhost:3000",))

    def test_production_requires_only_the_selected_llm_key(self) -> None:
        settings = Settings(
            app_env="production",
            identity_platform_project_id="project",
            llm_provider="openai",
            llm_model="gpt-test",
            openai_api_key="secret",
            database_url="postgresql+psycopg://user:pass@localhost/db",
            gcs_bucket="bucket",
            gcs_signer_service_account="api@example.iam.gserviceaccount.com",
            manim_renderer_url="https://renderer.example",
            frontend_origins=("https://chalksmith.example",),
        )

        self.assertEqual(settings.llm_provider, "openai")
        self.assertIsNone(settings.gemini_api_key)

    def test_production_api_rejects_incomplete_configuration(self) -> None:
        with self.assertRaises(ValueError):
            Settings(app_env="production")

    def test_production_rejects_insecure_renderer_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(
                app_env="production",
                identity_platform_project_id="project",
                llm_model="model",
                gemini_api_key="secret",
                database_url="postgresql+psycopg://user:pass@localhost/db",
                gcs_bucket="bucket",
                gcs_signer_service_account="api@example.iam.gserviceaccount.com",
                manim_renderer_url="http://renderer.example",
                frontend_origins=("https://chalksmith.example",),
            )

    def test_production_rejects_insecure_frontend_origins(self) -> None:
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            Settings(
                app_env="production",
                identity_platform_project_id="project",
                llm_model="model",
                gemini_api_key="secret",
                database_url="postgresql+psycopg://user:pass@localhost/db",
                gcs_bucket="bucket",
                gcs_signer_service_account="api@example.iam.gserviceaccount.com",
                manim_renderer_url="https://renderer.example",
                frontend_origins=("http://chalksmith.example",),
            )


class ApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.app: FastAPI = create_app(Settings(app_env="test"))
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
