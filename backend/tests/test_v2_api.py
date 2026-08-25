import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from fastapi import UploadFile
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from starlette.datastructures import Headers

from backend.app.api.dependencies import get_renderers
from backend.app.core.config import Settings
from backend.app.db.lessons import create_lesson, get_owned_lesson, save_lesson
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.llm.base import LLMResult, LLMStreamChunk
from backend.app.integrations.llm.factory import get_llm_provider
from backend.app.integrations.storage import get_storage
from backend.app.main import create_app
from backend.app.lessons.formats.interactive.prompt import INTERACTIVE_RULES
from backend.app.lessons.formats.code import build_code_repair_prompt
from backend.app.lessons.formats.slides.compiler import (
    KATEX_AUTO_RENDER_SCRIPT,
    KATEX_SCRIPT,
    KATEX_STYLESHEET,
    REVEAL_CORE_STYLESHEET,
    REVEAL_SCRIPT,
    REVEAL_THEME_STYLESHEET,
)
from backend.app.lessons.render.base import RenderError
from backend.app.lessons.render.html import HTMLRenderer
from backend.app.lessons.sources import extract_sources


class FakeLLM:
    async def generate(self, _prompt: str) -> LLMResult:
        return LLMResult(
            text=(
                "A short interactive lesson.\n---CODE_START---\n"
                "<!doctype html><html><head></head><body>"
                "<script src=\"https://cdn.jsdelivr.net/npm/p5@1.11.0/lib/p5.min.js\"></script>"
                "<script>function setup(){createCanvas(320,180)}</script></body></html>"
            ),
            provider="fake",
            model="fake-model",
        )


class StreamingFakeLLM(FakeLLM):
    async def stream(self, prompt: str):
        result = await self.generate(prompt)
        midpoint = len(result.text) // 2
        yield LLMStreamChunk(
            text=result.text[:midpoint],
            provider=result.provider,
            model=result.model,
            input_tokens=120,
        )
        yield LLMStreamChunk(
            text=result.text[midpoint:],
            provider=result.provider,
            model=result.model,
            output_tokens=80,
        )


def _slides_response() -> str:
    return (
        Path(__file__).parent / "fixtures" / "lesson_specs" / "slides.json"
    ).read_text(encoding="utf-8")


class FakeSlidesLLM:
    def __init__(self, *responses: str) -> None:
        self.responses = list(responses or (_slides_response(),))
        self.prompts: list[str] = []

    async def generate(self, prompt: str) -> LLMResult:
        self.prompts.append(prompt)
        return LLMResult(
            text=self.responses.pop(0),
            provider="fake",
            model="fake-slides-model",
        )


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.deletions: list[tuple[str, str]] = []

    def upload_file(self, source: Path, object_key: str, _content_type: str) -> None:
        self.objects[object_key] = source.read_bytes()

    def upload_bytes(self, data: bytes, object_key: str, _content_type: str) -> None:
        self.objects[object_key] = data

    def signed_url(self, object_key: str, *, download_name: str | None = None) -> str:
        suffix = f"?download={download_name}" if download_name else ""
        return f"https://storage.test/{object_key}{suffix}"

    def delete(self, object_key: str) -> None:
        self.deletions.append(("object", object_key))
        self.objects.pop(object_key, None)

    def delete_prefix(self, prefix: str) -> None:
        self.deletions.append(("prefix", prefix))
        for key in list(self.objects):
            if key.startswith(prefix):
                self.objects.pop(key)


def _completed_lesson_id(stream: str) -> str:
    completed_line = next(
        line for block in stream.split("\n\n")
        if "event: complete" in block
        for line in block.splitlines()
        if line.startswith("data: ")
    )
    return __import__("json").loads(completed_line[6:])["lesson_id"]


def _failed_lesson_id(stream: str) -> str:
    error_line = next(
        line for block in stream.split("\n\n")
        if "event: error" in block
        for line in block.splitlines()
        if line.startswith("data: ")
    )
    return __import__("json").loads(error_line[6:])["lesson_id"]


class V2ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        settings = Settings(
            app_env="test",
            database_url="sqlite://",
            signed_url_ttl_seconds=300,
        )
        self.app = create_app(settings)
        self.storage = FakeStorage()

        async def current_user() -> AuthUser:
            return AuthUser(uid="teacher-a", email="teacher@example.com")

        self.app.dependency_overrides[get_current_user] = current_user
        self.app.dependency_overrides[get_llm_provider] = lambda: FakeLLM()
        self.app.dependency_overrides[get_storage] = lambda: self.storage
        self.app.dependency_overrides[get_renderers] = lambda: {
            "interactive": HTMLRenderer(required_marker="p5"),
            "slides": HTMLRenderer(required_marker="reveal"),
            "video": HTMLRenderer(required_marker="never-used"),
        }
        self.client_context = TestClient(self.app)
        self.client = self.client_context.__enter__()

    def tearDown(self) -> None:
        self.client_context.__exit__(None, None, None)

    def test_generation_stream_and_lesson_access(self) -> None:
        self.app.dependency_overrides[get_llm_provider] = lambda: StreamingFakeLLM()
        response = self.client.post(
            "/v2/generations",
            data={"topic": "Fractions", "format": "interactive"},
            headers={"Accept": "text/event-stream"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: started", response.text)
        self.assertIn('"stage": "validating"', response.text)
        self.assertIn('"generated_characters":', response.text)
        self.assertIn('"stage": "saving"', response.text)
        self.assertIn("event: complete", response.text)
        completed_line = next(
            line for block in response.text.split("\n\n")
            if "event: complete" in block
            for line in block.splitlines()
            if line.startswith("data: ")
        )
        lesson_id = __import__("json").loads(completed_line[6:])["lesson_id"]

        lesson_response = self.client.get(f"/v2/lessons/{lesson_id}")
        self.assertEqual(lesson_response.status_code, 200)
        self.assertEqual(lesson_response.json()["status"], "ready")
        self.assertIn("Content-Security-Policy", next(iter(self.storage.objects.values())).decode())

        access_response = self.client.post(f"/v2/lessons/{lesson_id}/access-url")
        self.assertEqual(access_response.status_code, 200)
        self.assertEqual(access_response.json()["expires_in"], 300)

    def test_slides_generation_compiles_a_versioned_specification(self) -> None:
        llm = FakeSlidesLLM()
        self.app.dependency_overrides[get_llm_provider] = lambda: llm

        response = self.client.post(
            "/v2/generations",
            data={"topic": "Equivalent fractions", "format": "slides"},
        )

        self.assertIn("event: complete", response.text)
        self.assertNotIn('"stage": "repairing"', response.text)
        lesson_id = _completed_lesson_id(response.text)
        lesson = self.client.get(f"/v2/lessons/{lesson_id}").json()
        self.assertEqual(lesson["spec_version"], "chalksmith.slides.v1")
        self.assertNotIn("template_id", lesson)
        self.assertEqual(lesson["runtime_version"], "slides-runtime.v1.1")
        self.assertEqual(lesson["compiler_version"], "slides-compiler.v1.1")
        self.assertIn('data-chalksmith-runtime="slides-runtime.v1.1"', lesson["source_code"])
        self.assertNotIn("data-chalksmith-template", lesson["source_code"])
        self.assertIn('data-chalksmith-layout="split"', lesson["source_code"])
        self.assertIn('data-chalksmith-layout="solution-split"', lesson["source_code"])
        self.assertIn('<div class="slides">', lesson["source_code"])
        self.assertIn('<div class="cs-slide__body ', lesson["source_code"])
        self.assertNotIn('<section class="cs-slide__body ', lesson["source_code"])
        self.assertEqual(
            lesson["source_code"].count("<section"),
            lesson["source_code"].count('<section class="cs-slide '),
        )
        self.assertIn(
            ".reveal .slides > section.cs-slide {\n  display: none !important;",
            lesson["source_code"],
        )
        self.assertIn(
            ".reveal .slides > section.cs-slide.present {\n  display: grid !important;",
            lesson["source_code"],
        )
        for asset_url in (
            REVEAL_CORE_STYLESHEET,
            REVEAL_THEME_STYLESHEET,
            REVEAL_SCRIPT,
            KATEX_STYLESHEET,
            KATEX_SCRIPT,
            KATEX_AUTO_RENDER_SCRIPT,
        ):
            self.assertIn(asset_url, lesson["source_code"])
        self.assertIn("data-chalksmith-katex", lesson["source_code"])
        self.assertIn("data-chalksmith-reveal-fallback", lesson["source_code"])
        self.assertIn(
            ".reveal.chalksmith-reveal-fallback .slides > section:first-child",
            lesson["source_code"],
        )
        self.assertEqual(len(llm.prompts), 1)
        self.assertIn("The platform owns all slide composition", llm.prompts[0])
        self.assertNotIn('"template"', llm.prompts[0])
        artifact = next(iter(self.storage.objects.values())).decode()
        self.assertIn("Content-Security-Policy", artifact)
        self.assertIn("Equivalent Fractions", artifact)

    def test_invalid_slides_specification_gets_one_bounded_repair(self) -> None:
        llm = FakeSlidesLLM("{}", _slides_response())
        self.app.dependency_overrides[get_llm_provider] = lambda: llm

        response = self.client.post(
            "/v2/generations",
            data={"topic": "Equivalent fractions", "format": "slides"},
        )

        self.assertIn('"stage": "repairing"', response.text)
        self.assertIn("event: complete", response.text)
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn("Repair the specification, not the layout system", llm.prompts[1])
        lesson = self.client.get(f"/v2/lessons/{_completed_lesson_id(response.text)}").json()
        self.assertEqual(lesson["status"], "ready")
        self.assertIsNone(lesson["error_message"])
        self.assertNotIn("first_error", lesson)
        with Session(self.app.state.engine) as session:
            stored = get_owned_lesson(
                session,
                UUID(_completed_lesson_id(response.text)),
                "teacher-a",
            )
            self.assertIn("Invalid Slides specification", stored.first_error)

    def test_unescaped_custom_html_compiles_without_a_model_repair(self) -> None:
        lesson = __import__("json").loads(_slides_response())
        lesson["payload"]["slides"][2]["body"] = [
            {
                "type": "custom-html",
                "description": "Igneous to sedimentary",
                "html": '<div class="cycle"><span class="igneous">Igneous</span></div>',
            }
        ]
        raw = __import__("json").dumps(lesson).replace('\\"', '"')
        llm = FakeSlidesLLM(raw)
        self.app.dependency_overrides[get_llm_provider] = lambda: llm

        response = self.client.post(
            "/v2/generations",
            data={"topic": "The rock cycle", "format": "slides"},
        )

        self.assertIn("event: complete", response.text)
        self.assertNotIn('"stage": "repairing"', response.text)
        self.assertEqual(len(llm.prompts), 1)
        compiled = self.client.get(f"/v2/lessons/{_completed_lesson_id(response.text)}").json()
        self.assertEqual(compiled["status"], "ready")
        self.assertIn("Igneous", compiled["source_code"])

    def test_unrecoverable_slides_json_uses_one_repair_and_keeps_private_output(self) -> None:
        broken = '{"schema_version":"chalksmith.slides.v1","format":}'
        llm = FakeSlidesLLM(broken, broken)
        self.app.dependency_overrides[get_llm_provider] = lambda: llm

        response = self.client.post(
            "/v2/generations",
            data={"topic": "The rock cycle", "format": "slides"},
        )

        self.assertIn("event: error", response.text)
        self.assertIn('"stage": "repairing"', response.text)
        self.assertEqual(len(llm.prompts), 2)
        lesson_id = _failed_lesson_id(response.text)
        lesson = self.client.get(f"/v2/lessons/{lesson_id}").json()
        self.assertEqual(lesson["status"], "failed")
        self.assertIsNone(lesson["source_code"])
        self.assertNotIn("raw_model_output", lesson)
        self.assertNotIn("first_error", lesson)
        self.assertIn("Invalid JSON", lesson["error_message"])
        with Session(self.app.state.engine) as session:
            stored = get_owned_lesson(session, UUID(lesson_id), "teacher-a")
            self.assertEqual(stored.raw_model_output, broken)
            self.assertIn("Invalid JSON", stored.first_error)

    def test_structured_slides_edit_uses_the_previous_specification(self) -> None:
        llm = FakeSlidesLLM(_slides_response(), _slides_response())
        self.app.dependency_overrides[get_llm_provider] = lambda: llm
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Equivalent fractions", "format": "slides"},
        )
        first_id = _completed_lesson_id(first.text)

        edited = self.client.post(
            "/v2/generations",
            data={
                "topic": "Equivalent fractions",
                "format": "slides",
                "base_lesson_id": first_id,
                "edit_instruction": "Use a pizza example.",
            },
        )

        self.assertIn("event: complete", edited.text)
        self.assertEqual(len(llm.prompts), 2)
        self.assertIn("<PREVIOUS_SPEC>", llm.prompts[1])
        self.assertIn('"schema_version":"chalksmith.slides.v1"', llm.prompts[1])
        self.assertNotIn("<!doctype html>", llm.prompts[1])

    def test_legacy_slides_remain_viewable_but_cannot_be_edited(self) -> None:
        with Session(self.app.state.engine) as session:
            lesson = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Legacy Slides",
                lesson_format="slides",
            )
            lesson.status = "ready"
            lesson.summary = "A historical presentation."
            lesson.source_code = "<!doctype html><html><body>Legacy Slides</body></html>"
            lesson.object_key = f"lessons/teacher-a/{lesson.id}/lesson.html"
            lesson_id = lesson.id
            save_lesson(session, lesson)

        view_response = self.client.get(f"/v2/lessons/{lesson_id}")
        edit_response = self.client.post(
            "/v2/generations",
            data={
                "topic": "Legacy Slides",
                "format": "slides",
                "base_lesson_id": str(lesson_id),
                "edit_instruction": "Add one example.",
            },
        )

        self.assertEqual(view_response.status_code, 200)
        self.assertEqual(view_response.json()["source_code"], lesson.source_code)
        self.assertEqual(edit_response.status_code, 409)
        self.assertEqual(edit_response.json()["error"]["code"], "legacy_lesson_read_only")

        format_change_response = self.client.post(
            "/v2/generations",
            data={
                "topic": "Legacy Slides",
                "format": "interactive",
                "base_lesson_id": str(lesson_id),
                "edit_instruction": "Convert this lesson.",
            },
        )
        self.assertEqual(format_change_response.status_code, 409)
        self.assertEqual(format_change_response.json()["error"]["code"], "lesson_format_mismatch")

    def test_revision_format_must_match_its_parent(self) -> None:
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Fractions", "format": "interactive"},
        )
        first_id = _completed_lesson_id(first.text)

        response = self.client.post(
            "/v2/generations",
            data={
                "topic": "Fractions",
                "format": "slides",
                "base_lesson_id": first_id,
                "edit_instruction": "Convert it.",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "lesson_format_mismatch")

    def test_ready_version_can_be_selected_as_the_dashboard_final(self) -> None:
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Fractions", "format": "interactive"},
        )
        first_id = _completed_lesson_id(first.text)
        edited = self.client.post(
            "/v2/generations",
            data={
                "topic": "Fractions",
                "format": "interactive",
                "base_lesson_id": first_id,
                "edit_instruction": "Add a visual example.",
            },
        )
        edited_id = _completed_lesson_id(edited.text)

        versions = self.client.get(f"/v2/lessons/{first_id}/versions").json()
        self.assertEqual([version["is_final"] for version in versions], [True, False])
        self.assertEqual(self.client.get("/v2/lessons").json()[0]["id"], first_id)

        selected = self.client.put(f"/v2/lessons/{edited_id}/final")

        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()["final_lesson_id"], edited_id)
        versions = self.client.get(f"/v2/lessons/{edited_id}/versions").json()
        self.assertEqual([version["is_final"] for version in versions], [False, True])
        dashboard = self.client.get("/v2/lessons").json()
        self.assertEqual(dashboard[0]["id"], edited_id)
        self.assertEqual(dashboard[0]["version_count"], 2)

    def test_version_numbers_are_unique_within_a_lesson(self) -> None:
        with Session(self.app.state.engine) as session:
            root = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Fractions",
                lesson_format="interactive",
            )
            create_lesson(
                session,
                owner_id="teacher-a",
                topic="Fractions",
                lesson_format="interactive",
                root_lesson_id=root.id,
                parent_lesson_id=root.id,
                version_number=2,
            )
            with self.assertRaises(IntegrityError):
                create_lesson(
                    session,
                    owner_id="teacher-a",
                    topic="Fractions",
                    lesson_format="interactive",
                    root_lesson_id=root.id,
                    parent_lesson_id=root.id,
                    version_number=2,
                )

    def test_database_sessions_match_response_lifetimes(self) -> None:
        routes = [route for route in self.app.routes if isinstance(route, APIRoute)]
        lesson_routes = [route for route in routes if route.path.startswith("/v2/lessons")]
        for route in lesson_routes:
            session_dependencies = [
                dependency
                for dependency in route.dependant.dependencies
                if dependency.call is get_session
            ]
            self.assertEqual(len(session_dependencies), 1, route.path)
            self.assertEqual(session_dependencies[0].scope, "function", route.path)

        generation_route = next(route for route in routes if route.path == "/v2/generations")
        generation_session = next(
            dependency
            for dependency in generation_route.dependant.dependencies
            if dependency.call is get_session
        )
        self.assertEqual(generation_session.scope, "request")

    def test_generation_does_not_hold_a_connection_while_waiting_for_llm(self) -> None:
        active_connections = 0
        observed_connections: list[tuple[str, int]] = []

        def checkout(*_args) -> None:
            nonlocal active_connections
            active_connections += 1

        def checkin(*_args) -> None:
            nonlocal active_connections
            active_connections -= 1

        class InspectingLLM(FakeLLM):
            async def generate(self, prompt: str) -> LLMResult:
                observed_connections.append(("llm", active_connections))
                return await super().generate(prompt)

        original_upload_file = self.storage.upload_file

        def upload_file(source: Path, object_key: str, content_type: str) -> None:
            observed_connections.append(("storage", active_connections))
            original_upload_file(source, object_key, content_type)

        event.listen(self.app.state.engine, "checkout", checkout)
        event.listen(self.app.state.engine, "checkin", checkin)
        self.app.dependency_overrides[get_llm_provider] = lambda: InspectingLLM()
        self.storage.upload_file = upload_file
        try:
            response = self.client.post(
                "/v2/generations",
                data={"topic": "Connection lifecycle", "format": "interactive"},
            )
        finally:
            self.storage.upload_file = original_upload_file
            event.remove(self.app.state.engine, "checkout", checkout)
            event.remove(self.app.state.engine, "checkin", checkin)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_connections, [("llm", 0), ("storage", 0)])

    def test_access_url_releases_its_connection_before_signing(self) -> None:
        generated = self.client.post(
            "/v2/generations",
            data={"topic": "Signed URL lifecycle", "format": "interactive"},
        )
        lesson_id = _completed_lesson_id(generated.text)
        active_connections = 0
        observed_connections: list[int] = []

        def checkout(*_args) -> None:
            nonlocal active_connections
            active_connections += 1

        def checkin(*_args) -> None:
            nonlocal active_connections
            active_connections -= 1

        def signed_url(object_key: str, *, download_name: str | None = None) -> str:
            observed_connections.append(active_connections)
            return f"https://storage.test/{object_key}"

        event.listen(self.app.state.engine, "checkout", checkout)
        event.listen(self.app.state.engine, "checkin", checkin)
        original_signed_url = self.storage.signed_url
        self.storage.signed_url = signed_url
        try:
            response = self.client.post(f"/v2/lessons/{lesson_id}/access-url")
        finally:
            self.storage.signed_url = original_signed_url
            event.remove(self.app.state.engine, "checkout", checkout)
            event.remove(self.app.state.engine, "checkin", checkin)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_connections, [0])

    def test_delete_releases_its_connection_before_storage_calls(self) -> None:
        generated = self.client.post(
            "/v2/generations",
            data={"topic": "Delete lifecycle", "format": "interactive"},
        )
        lesson_id = _completed_lesson_id(generated.text)
        active_connections = 0
        observed_connections: list[int] = []

        def checkout(*_args) -> None:
            nonlocal active_connections
            active_connections += 1

        def checkin(*_args) -> None:
            nonlocal active_connections
            active_connections -= 1

        original_delete_prefix = self.storage.delete_prefix

        def delete_prefix(prefix: str) -> None:
            observed_connections.append(active_connections)
            original_delete_prefix(prefix)

        event.listen(self.app.state.engine, "checkout", checkout)
        event.listen(self.app.state.engine, "checkin", checkin)
        self.storage.delete_prefix = delete_prefix
        try:
            response = self.client.delete(f"/v2/lessons/{lesson_id}")
        finally:
            self.storage.delete_prefix = original_delete_prefix
            event.remove(self.app.state.engine, "checkout", checkout)
            event.remove(self.app.state.engine, "checkin", checkin)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(observed_connections, [0])

    def test_edits_are_versions_of_one_dashboard_lesson(self) -> None:
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Pythagorean theorem", "format": "interactive"},
        )
        first_id = _completed_lesson_id(first.text)

        edited = self.client.post(
            "/v2/generations",
            data={
                "topic": "Pythagorean theorem",
                "format": "interactive",
                "base_lesson_id": first_id,
                "edit_instruction": "Add a worked example.",
            },
        )
        edited_id = _completed_lesson_id(edited.text)

        dashboard = self.client.get("/v2/lessons")
        self.assertEqual(dashboard.status_code, 200)
        rows = dashboard.json()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], first_id)
        self.assertEqual(rows[0]["version_count"], 2)

        versions = self.client.get(f"/v2/lessons/{edited_id}/versions")
        self.assertEqual(versions.status_code, 200)
        history = versions.json()
        self.assertEqual([version["id"] for version in history], [first_id, edited_id])
        self.assertEqual([version["version_number"] for version in history], [1, 2])
        self.assertEqual(history[1]["parent_lesson_id"], first_id)
        self.assertEqual(history[1]["edit_instruction"], "Add a worked example.")
        self.assertNotIn("source_code", history[0])

        commits = 0

        def count_commit(_session) -> None:
            nonlocal commits
            commits += 1

        event.listen(Session, "after_commit", count_commit)
        try:
            renamed = self.client.patch(
                f"/v2/lessons/{edited_id}",
                json={"topic": "Right triangles"},
            )
        finally:
            event.remove(Session, "after_commit", count_commit)

        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(commits, 1)
        renamed_versions = self.client.get(f"/v2/lessons/{first_id}/versions").json()
        self.assertEqual([version["topic"] for version in renamed_versions], ["Right triangles"] * 2)

    def test_lesson_list_counts_versions_with_one_grouped_query(self) -> None:
        with Session(self.app.state.engine) as session:
            for index in range(3):
                root = create_lesson(
                    session,
                    owner_id="teacher-a",
                    topic=f"Lesson {index}",
                    lesson_format="interactive",
                )
                create_lesson(
                    session,
                    owner_id="teacher-a",
                    topic=f"Lesson {index}",
                    lesson_format="interactive",
                    root_lesson_id=root.id,
                    parent_lesson_id=root.id,
                    version_number=2,
                )

        select_statements: list[str] = []

        def record_select(_connection, _cursor, statement, _parameters, _context, _executemany):
            if statement.lstrip().upper().startswith("SELECT"):
                select_statements.append(statement)

        event.listen(self.app.state.engine, "before_cursor_execute", record_select)
        try:
            response = self.client.get("/v2/lessons")
        finally:
            event.remove(self.app.state.engine, "before_cursor_execute", record_select)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row["version_count"] for row in response.json()], [2, 2, 2])
        self.assertEqual(len(select_statements), 2)
        dashboard_select = select_statements[0]
        for private_or_heavy_field in (
            "source_code",
            "lesson_spec",
            "raw_model_output",
            "first_error",
            "object_key",
        ):
            self.assertNotIn(private_or_heavy_field, dashboard_select)

    def test_lesson_queries_are_tenant_isolated(self) -> None:
        with Session(self.app.state.engine) as session:
            mine = create_lesson(session, owner_id="teacher-a", topic="Mine", lesson_format="slides")
            other = create_lesson(session, owner_id="teacher-b", topic="Other", lesson_format="slides")
            mine_id = str(mine.id)
            other_id = str(other.id)

        response = self.client.get("/v2/lessons")
        ids = {row["id"] for row in response.json()}
        self.assertIn(mine_id, ids)
        self.assertNotIn(other_id, ids)
        self.assertEqual(self.client.get(f"/v2/lessons/{other_id}").status_code, 404)

    def test_missing_identity_token_is_rejected(self) -> None:
        self.app.dependency_overrides.pop(get_current_user)

        response = self.client.get("/v2/lessons")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_delete_removes_sources_before_ready_output(self) -> None:
        with Session(self.app.state.engine) as session:
            lesson = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Delete me",
                lesson_format="interactive",
            )
            lesson.status = "ready"
            lesson.object_key = f"lessons/teacher-a/{lesson.id}/lesson.html"
            lesson_id = lesson.id
            save_lesson(session, lesson)

        response = self.client.delete(f"/v2/lessons/{lesson_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.storage.deletions[0][0], "prefix")
        self.assertEqual(self.storage.deletions[1], ("object", lesson.object_key))
        self.assertEqual(self.client.get(f"/v2/lessons/{lesson_id}").status_code, 404)

    def test_source_count_and_combined_byte_limits(self) -> None:
        count_settings = Settings(app_env="test", max_source_files=1)
        uploads = [
            UploadFile(filename="one.pdf", file=BytesIO(b"%PDF")),
            UploadFile(filename="two.pdf", file=BytesIO(b"%PDF")),
        ]
        with self.assertRaisesRegex(Exception, "at most 1"):
            __import__("asyncio").run(extract_sources(uploads, count_settings))

        byte_settings = Settings(
            app_env="test",
            max_source_bytes=100,
            max_total_source_bytes=5,
        )
        upload = UploadFile(
            filename="large.pdf",
            file=BytesIO(b"%PDF12"),
            headers=Headers({"content-type": "application/pdf"}),
        )
        with self.assertRaisesRegex(Exception, "combined PDF uploads"):
            __import__("asyncio").run(extract_sources([upload], byte_settings))

    def test_interactive_prompt_prevents_double_scaled_pointer_coordinates(self) -> None:
        rules = INTERACTIVE_RULES

        self.assertIn("use `mouseX` and", rules)
        self.assertIn("do not divide them", rules)
        self.assertIn("p5.js `scale()`", rules)

    def test_html_renderer_rejects_counter_loop_moving_away_from_bound(self) -> None:
        generated = """<!doctype html><html><body><script>
const p5 = true;
for (let i = steps; i >= 0; i++) drawPoint(i);
</script></body></html>"""
        with TemporaryDirectory() as directory, self.assertRaisesRegex(
            RenderError, "counter loop whose update moves away"
        ):
            __import__("asyncio").run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

    def test_html_renderer_accepts_terminating_counter_loop_and_ignores_lesson_text(self) -> None:
        generated = """<!doctype html><html><body><script>
const p5 = true;
const example = "for (let i = steps; i >= 0; i++)";
for (let i = steps; i >= 0; i--) drawPoint(i);
</script></body></html>"""
        with TemporaryDirectory() as directory:
            asset = __import__("asyncio").run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

        self.assertEqual(asset.extension, "html")

    def test_interactive_prompt_and_repair_prompt_address_runtime_validation(self) -> None:
        self.assertIn("decrement toward a lower bound", INTERACTIVE_RULES)
        repair = build_code_repair_prompt(
            original_prompt="Create an interactive lesson.",
            code="<html><script>const p5 = true;</script></html>",
            error="counter loop whose update moves away",
        )

        self.assertIn("failed validation or rendering", repair)
        self.assertIn("requested format", repair)
        self.assertNotIn("previous Manim code", repair)


if __name__ == "__main__":
    unittest.main()
