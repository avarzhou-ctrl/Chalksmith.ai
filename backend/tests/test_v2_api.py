import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import UploadFile
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session
from starlette.datastructures import Headers

from backend.app.api.dependencies import get_renderers
from backend.app.core.config import Settings
from backend.app.db.lessons import create_lesson, save_lesson
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.llm.base import LLMResult
from backend.app.integrations.llm.factory import get_llm_provider
from backend.app.integrations.storage import get_storage
from backend.app.main import create_app
from backend.app.renderers.html import (
    HTMLRenderer,
    REVEAL_CORE_STYLESHEET,
    REVEAL_FALLBACK_SCRIPT,
    REVEAL_FALLBACK_STYLE,
    REVEAL_SCRIPT,
    REVEAL_THEME_STYLESHEET,
)
from backend.app.services.prompts import FORMAT_RULES
from backend.app.services.sources import extract_sources


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
        response = self.client.post(
            "/v2/generations",
            data={"topic": "Fractions", "format": "interactive"},
            headers={"Accept": "text/event-stream"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: started", response.text)
        self.assertIn('"stage": "validating"', response.text)
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

    def test_slide_renderer_pins_verified_reveal_assets(self) -> None:
        generated = """<!doctype html><html><head>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/reveal.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/reveal.js/4.3.1/theme/dracula.min.css">
</head><body><div class="reveal"><div class="slides"><section>Test</section></div></div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@4.3.1/dist/reveal.js"></script>
<script>Reveal.initialize({embedded: true})</script></body></html>"""
        with TemporaryDirectory() as directory:
            asset = __import__("asyncio").run(
                HTMLRenderer(required_marker="reveal").render(generated, Path(directory))
            )
            rendered = asset.path.read_text()

        self.assertIn(REVEAL_CORE_STYLESHEET, rendered)
        self.assertIn(REVEAL_THEME_STYLESHEET, rendered)
        self.assertIn(REVEAL_SCRIPT, rendered)
        self.assertIn(REVEAL_FALLBACK_STYLE, rendered)
        self.assertIn(REVEAL_FALLBACK_SCRIPT, rendered)
        self.assertNotIn("4.3.1", rendered)
        self.assertNotIn("dracula.min.css", rendered)

    def test_slide_renderer_injects_missing_reveal_assets(self) -> None:
        generated = """<!doctype html><html><head></head><body>
<div class="reveal"><div class="slides"><section>Test</section></div></div>
<script>Reveal.initialize({embedded: true})</script></body></html>"""
        with TemporaryDirectory() as directory:
            asset = __import__("asyncio").run(
                HTMLRenderer(required_marker="reveal").render(generated, Path(directory))
            )
            rendered = asset.path.read_text()

        self.assertIn(REVEAL_CORE_STYLESHEET, rendered)
        self.assertIn(REVEAL_THEME_STYLESHEET, rendered)
        self.assertIn(REVEAL_SCRIPT, rendered)
        self.assertIn(REVEAL_FALLBACK_STYLE, rendered)
        self.assertIn(REVEAL_FALLBACK_SCRIPT, rendered)

    def test_slide_renderer_fallback_keeps_the_first_slide_visible(self) -> None:
        generated = """<!doctype html><html><head></head><body>
<div class="reveal"><div class="slides"><section>Visible lesson</section></div></div>
<script>Reveal.initialize({embedded: true})</script></body></html>"""
        with TemporaryDirectory() as directory:
            asset = __import__("asyncio").run(
                HTMLRenderer(required_marker="reveal").render(generated, Path(directory))
            )
            rendered = asset.path.read_text()

        self.assertIn("background: #191919", rendered)
        self.assertIn(".slides > section:first-child", rendered)
        self.assertIn('deck.classList.add("chalksmith-reveal-fallback")', rendered)
        self.assertLess(rendered.index(REVEAL_FALLBACK_STYLE), rendered.index("</head>"))
        self.assertLess(rendered.index(REVEAL_FALLBACK_SCRIPT), rendered.index("</body>"))

    def test_interactive_prompt_prevents_double_scaled_pointer_coordinates(self) -> None:
        rules = FORMAT_RULES["interactive"]

        self.assertIn("use `mouseX` and", rules)
        self.assertIn("do not divide them", rules)
        self.assertIn("p5.js `scale()`", rules)


if __name__ == "__main__":
    unittest.main()
