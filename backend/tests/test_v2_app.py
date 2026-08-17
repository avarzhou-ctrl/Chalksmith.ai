import ast
import asyncio
import json
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
from sqlalchemy import inspect, text
from sqlmodel import create_engine

from backend.app.core.config import LOCAL_CLERK_FILE, LOCAL_ENV_FILE, REPOSITORY_DIR, Settings
from backend.app.core.errors import AppError
from backend.app.db.session import create_db_and_tables
from backend.app.integrations.auth import _decode_clerk_token, get_current_user
from backend.app.integrations.llm.base import LLMResult
from backend.app.integrations.llm.base import LLMProviderError
from backend.app.integrations.llm.deepseek import DeepSeekProvider
from backend.app.integrations.llm.factory import create_llm_provider
from backend.app.integrations.llm.gemini import VertexGeminiProvider
from backend.app.integrations.storage import GCSStorage
from backend.app.main import create_app
from backend.app.lessons.formats import FormatRequest, get_lesson_format_strategy
from backend.app.lessons.formats.code import parse_generated_lesson
from backend.app.lessons.formats.slides import compiler as slides_compiler
from backend.app.lessons.formats.slides.registry import (
    BLOCK_DEFINITIONS,
    BLOCK_REGISTRY,
    BLOCK_STYLE_GROUP_ORDER,
    BLOCK_STYLE_GROUPS,
    BLOCK_TYPES,
)
from backend.app.lessons.formats.slides.spec import SlidesLessonSpec
from backend.app.lessons.formats.slides.strategy import StructuredSlidesStrategy
from backend.app.lessons.generation import GenerationService, LLMProgress
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


class StructuredSlidesTests(unittest.TestCase):
    def test_slides_always_use_the_structured_strategy(self) -> None:
        strategy = get_lesson_format_strategy("slides")

        self.assertIsInstance(strategy, StructuredSlidesStrategy)

    def test_prompt_exposes_a_schema_but_not_the_runtime_styles(self) -> None:
        prompt = StructuredSlidesStrategy().build_prompt(
            FormatRequest(topic="Equivalent fractions", lesson_format="slides")
        )

        self.assertIn('"chalksmith.slides.v1"', prompt)
        self.assertIn("The platform owns all layout", prompt)
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
        self.assertIn("semantic anchors for diagonals, radii, altitudes", prompt)
        self.assertIn("aim for 2 to 4 slides with visual blocks", prompt)
        self.assertIn("derives the layout and drawing", prompt)
        self.assertNotIn('"template"', prompt)
        self.assertNotIn("--cs-bg", prompt)
        self.assertNotIn("Reveal.initialize({", prompt)

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
        self.assertEqual(prepared.spec_version, "chalksmith.slides.v1")
        self.assertNotIn("data-chalksmith-template", prepared.source_code)

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

            create_db_and_tables(engine)

            columns = {column["name"] for column in inspect(engine).get_columns("lessons")}
            self.assertTrue(
                {
                    "lesson_spec",
                    "spec_version",
                    "runtime_version",
                    "compiler_version",
                }.issubset(columns)
            )


if __name__ == "__main__":
    unittest.main()
