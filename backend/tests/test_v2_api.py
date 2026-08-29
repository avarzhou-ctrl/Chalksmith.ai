import asyncio
import json
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
from sqlmodel import Session, select
from starlette.datastructures import Headers

from backend.app.api.dependencies import get_renderers
from backend.app.core.config import Settings
from backend.app.db.lessons import (
    create_lesson,
    get_owned_lesson,
    save_lesson,
    set_lesson_publication,
)
from backend.app.db.profiles import ensure_user_profile
from backend.app.db.models import LessonFolder, LessonLike, LessonTag
from backend.app.db.session import get_session
from backend.app.integrations.auth import AuthUser, get_current_user
from backend.app.integrations.llm.base import LLMResult, LLMSource, LLMStreamChunk
from backend.app.integrations.llm.factory import get_llm_provider
from backend.app.integrations.storage import get_storage
from backend.app.main import create_app
from backend.app.lessons.formats.code import build_code_repair_prompt
from backend.app.lessons.formats.interactive.prompt import INTERACTIVE_RULES
from backend.app.lessons.formats.interactive.strategy import InteractiveStrategy
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


class SourceAwareFakeLLM(FakeLLM):
    supports_sources = True

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.sources: list[tuple[LLMSource, ...]] = []

    async def generate(
        self,
        prompt: str,
        sources: tuple[LLMSource, ...] = (),
    ) -> LLMResult:
        self.prompts.append(prompt)
        self.sources.append(sources)
        return await super().generate(prompt)


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
        self.content_types: dict[str, str] = {}
        self.deletions: list[tuple[str, str]] = []

    def upload_file(self, source: Path, object_key: str, content_type: str) -> None:
        self.objects[object_key] = source.read_bytes()
        self.content_types[object_key] = content_type

    def upload_bytes(self, data: bytes, object_key: str, content_type: str) -> None:
        self.objects[object_key] = data
        self.content_types[object_key] = content_type

    def signed_url(self, object_key: str, *, download_name: str | None = None) -> str:
        suffix = f"?download={download_name}" if download_name else ""
        return f"https://storage.test/{object_key}{suffix}"

    def delete(self, object_key: str) -> None:
        self.deletions.append(("object", object_key))
        self.objects.pop(object_key, None)
        self.content_types.pop(object_key, None)

    def delete_prefix(self, prefix: str) -> None:
        self.deletions.append(("prefix", prefix))
        for key in list(self.objects):
            if key.startswith(prefix):
                self.objects.pop(key)
                self.content_types.pop(key, None)


class ConnectionTracker:
    def __init__(self, engine) -> None:
        self.engine = engine
        self.active = 0

    def __enter__(self) -> "ConnectionTracker":
        event.listen(self.engine, "checkout", self._checkout)
        event.listen(self.engine, "checkin", self._checkin)
        return self

    def __exit__(self, *_args) -> None:
        event.remove(self.engine, "checkout", self._checkout)
        event.remove(self.engine, "checkin", self._checkin)

    def _checkout(self, *_args) -> None:
        self.active += 1

    def _checkin(self, *_args) -> None:
        self.active -= 1


def _completed_lesson_id(stream: str) -> str:
    completed_line = next(
        line for block in stream.split("\n\n")
        if "event: complete" in block
        for line in block.splitlines()
        if line.startswith("data: ")
    )
    return json.loads(completed_line[6:])["lesson_id"]


def _failed_lesson_id(stream: str) -> str:
    error_line = next(
        line for block in stream.split("\n\n")
        if "event: error" in block
        for line in block.splitlines()
        if line.startswith("data: ")
    )
    return json.loads(error_line[6:])["lesson_id"]


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
        lesson_id = _completed_lesson_id(response.text)

        lesson_response = self.client.get(f"/v2/lessons/{lesson_id}")
        self.assertEqual(lesson_response.status_code, 200)
        self.assertEqual(lesson_response.json()["status"], "ready")
        self.assertIn("Content-Security-Policy", next(iter(self.storage.objects.values())).decode())

        access_response = self.client.post(f"/v2/lessons/{lesson_id}/access-url")
        self.assertEqual(access_response.status_code, 200)
        self.assertEqual(access_response.json()["expires_in"], 300)

    def test_image_source_is_stored_and_sent_to_the_model(self) -> None:
        llm = SourceAwareFakeLLM()
        self.app.dependency_overrides[get_llm_provider] = lambda: llm
        image = b"\x89PNG\r\n\x1a\nsource-image-bytes"

        response = self.client.post(
            "/v2/generations",
            data={"topic": "Explain this diagram", "format": "interactive"},
            files={"sources": ("diagram.png", image, "image/png")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: complete", response.text)
        self.assertEqual(len(llm.sources), 1)
        self.assertEqual(llm.sources[0], (LLMSource("diagram.png", "image/png", image),))
        self.assertIn("SOURCE IMAGE: diagram.png", llm.prompts[0])
        source_key = next(key for key in self.storage.objects if key.endswith("/diagram.png"))
        self.assertEqual(self.storage.objects[source_key], image)
        self.assertEqual(self.storage.content_types[source_key], "image/png")

    def test_pdf_source_is_stored_and_sent_directly_to_the_model(self) -> None:
        llm = SourceAwareFakeLLM()
        self.app.dependency_overrides[get_llm_provider] = lambda: llm
        pdf = b"%PDF-1.7\nimage-only-pdf"

        response = self.client.post(
            "/v2/generations",
            data={"topic": "Explain this worksheet", "format": "interactive"},
            files={"sources": ("worksheet.pdf", pdf, "application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("event: complete", response.text)
        self.assertEqual(
            llm.sources[0],
            (LLMSource("worksheet.pdf", "application/pdf", pdf),),
        )
        self.assertIn("SOURCE DOCUMENT: worksheet.pdf", llm.prompts[0])
        self.assertNotIn("image-only-pdf", llm.prompts[0])
        source_key = next(key for key in self.storage.objects if key.endswith("/worksheet.pdf"))
        self.assertEqual(self.storage.objects[source_key], pdf)
        self.assertEqual(self.storage.content_types[source_key], "application/pdf")

    def test_source_file_requires_a_source_capable_model(self) -> None:
        response = self.client.post(
            "/v2/generations",
            data={"topic": "Explain this worksheet", "format": "interactive"},
            files={
                "sources": (
                    "worksheet.pdf",
                    b"%PDF-1.7\nimage-only-pdf",
                    "application/pdf",
                )
            },
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "source_files_not_supported")

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
        for asset_url in (
            REVEAL_CORE_STYLESHEET,
            REVEAL_THEME_STYLESHEET,
            REVEAL_SCRIPT,
            KATEX_STYLESHEET,
            KATEX_SCRIPT,
            KATEX_AUTO_RENDER_SCRIPT,
        ):
            self.assertIn(asset_url, lesson["source_code"])
        self.assertIn("data-chalksmith-reveal-fallback", lesson["source_code"])
        self.assertEqual(len(llm.prompts), 1)
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
        lesson_id = _completed_lesson_id(response.text)
        lesson = self.client.get(f"/v2/lessons/{lesson_id}").json()
        self.assertEqual(lesson["status"], "ready")
        self.assertIsNone(lesson["error_message"])
        self.assertNotIn("first_error", lesson)
        with Session(self.app.state.engine) as session:
            stored = get_owned_lesson(
                session,
                UUID(lesson_id),
                "teacher-a",
            )
            self.assertIn("Invalid Slides specification", stored.first_error)

    def test_unescaped_custom_html_compiles_without_a_model_repair(self) -> None:
        lesson = json.loads(_slides_response())
        lesson["payload"]["slides"][2]["body"] = [
            {
                "type": "custom-html",
                "description": "Igneous to sedimentary",
                "html": '<div class="cycle"><span class="igneous">Igneous</span></div>',
            }
        ]
        raw = json.dumps(lesson).replace('\\"', '"')
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

        selected = self.client.put(f"/v2/lessons/{edited_id}/final")

        self.assertEqual(selected.status_code, 200)
        self.assertEqual(selected.json()["final_lesson_id"], edited_id)
        versions = self.client.get(f"/v2/lessons/{edited_id}/versions").json()
        self.assertEqual([version["is_final"] for version in versions], [False, True])
        dashboard = self.client.get("/v2/lessons").json()
        self.assertEqual(dashboard[0]["id"], edited_id)

    def test_published_final_version_is_publicly_listed_viewable_and_downloadable(self) -> None:
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Public fractions", "format": "interactive"},
        )
        first_id = _completed_lesson_id(first.text)
        edited = self.client.post(
            "/v2/generations",
            data={
                "topic": "Public fractions",
                "format": "interactive",
                "base_lesson_id": first_id,
                "edit_instruction": "Add a visual example.",
            },
        )
        edited_id = _completed_lesson_id(edited.text)

        tags = self.client.put(
            f"/v2/lessons/{edited_id}/tags",
            json={"tags": [" Math ", "math", "Grade 6"]},
        )
        self.assertEqual(tags.status_code, 200)
        self.assertEqual(tags.json()["tags"], ["Math", "Grade 6"])

        publication = self.client.put(
            f"/v2/lessons/{edited_id}/publication",
            json={"published": True, "display_name": "Ada Teacher"},
        )

        self.assertEqual(publication.status_code, 200)
        self.assertTrue(publication.json()["is_published"])
        self.assertEqual(publication.json()["lesson_id"], edited_id)
        self.assertIsNotNone(publication.json()["published_at"])
        profile = self.client.get("/v2/profile")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["display_name"], "Ada Teacher")
        self.assertNotIn("email", profile.json())
        updated_profile = self.client.put(
            "/v2/profile",
            json={
                "display_name": "Ada Teacher",
                "bio": "I create visual math lessons for curious learners.",
            },
        )
        self.assertEqual(updated_profile.status_code, 200)
        profile_id = updated_profile.json()["id"]
        public_profile = self.client.get(f"/v2/profiles/{profile_id}")
        self.assertEqual(public_profile.status_code, 200)
        self.assertEqual(
            public_profile.json()["bio"],
            "I create visual math lessons for curious learners.",
        )
        self.assertNotIn("email", public_profile.json())
        self.assertTrue(self.client.get(f"/v2/lessons/{first_id}").json()["is_published"])
        dashboard = self.client.get("/v2/lessons")
        self.assertEqual(dashboard.status_code, 200)
        self.assertTrue(dashboard.json()[0]["is_published"])
        published = self.client.get("/v2/explore/lessons")
        self.assertEqual(published.status_code, 200)
        self.assertEqual([lesson["id"] for lesson in published.json()], [edited_id])
        self.assertNotIn("source_code", published.json()[0])
        self.assertNotIn("email", published.json()[0])
        self.assertEqual(published.json()[0]["author_profile_id"], profile_id)
        self.assertEqual(published.json()[0]["author_display_name"], "Ada Teacher")
        self.assertEqual(published.json()[0]["tags"], ["Math", "Grade 6"])
        self.assertEqual(published.json()[0]["like_count"], 0)
        detail = self.client.get(f"/v2/explore/lessons/{edited_id}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["tags"], ["Math", "Grade 6"])
        self.assertEqual(detail.json()["like_count"], 0)
        liked = self.client.put(f"/v2/explore/lessons/{edited_id}/like")
        self.assertEqual(liked.status_code, 200)
        self.assertTrue(liked.json()["liked"])
        self.assertEqual(liked.json()["like_count"], 1)
        self.assertEqual(
            self.client.put(f"/v2/explore/lessons/{edited_id}/like").json()["like_count"],
            1,
        )
        self.assertEqual(
            self.client.get(
                f"/v2/explore/lessons/liked?root_id={published.json()[0]['root_lesson_id']}"
            ).json(),
            [published.json()[0]["root_lesson_id"]],
        )
        unliked = self.client.delete(f"/v2/explore/lessons/{edited_id}/like")
        self.assertFalse(unliked.json()["liked"])
        self.assertEqual(unliked.json()["like_count"], 0)
        self.assertEqual(
            [lesson["id"] for lesson in self.client.get("/v2/explore/lessons?q=ada").json()],
            [edited_id],
        )
        self.assertEqual(
            [lesson["id"] for lesson in self.client.get("/v2/explore/lessons?tag=math&tag=grade+6").json()],
            [edited_id],
        )
        self.assertEqual(
            self.client.get("/v2/explore/tags").json(),
            [
                {"label": "Grade 6", "value": "grade 6", "lesson_count": 1},
                {"label": "Math", "value": "math", "lesson_count": 1},
            ],
        )

        old_access = self.client.post(f"/v2/explore/lessons/{first_id}/access-url")
        view_access = self.client.post(f"/v2/explore/lessons/{edited_id}/access-url")
        download_access = self.client.post(
            f"/v2/explore/lessons/{edited_id}/access-url?download=true"
        )

        self.assertEqual(old_access.status_code, 404)
        self.assertEqual(view_access.status_code, 200)
        self.assertNotIn("?download=", view_access.json()["url"])
        self.assertIn("?download=Public fractions.html", download_access.json()["url"])

        previous_published_at = publication.json()["published_at"]
        self.assertEqual(self.client.put(f"/v2/lessons/{first_id}/final").status_code, 200)
        self.assertEqual(self.client.get("/v2/explore/lessons").json()[0]["id"], first_id)
        self.assertNotEqual(
            self.client.get(f"/v2/lessons/{first_id}").json()["published_at"],
            previous_published_at,
        )
        self.assertEqual(self.client.put(f"/v2/lessons/{edited_id}/final").status_code, 200)

        unpublished = self.client.put(
            f"/v2/lessons/{first_id}/publication",
            json={"published": False},
        )

        self.assertEqual(unpublished.status_code, 200)
        self.assertFalse(unpublished.json()["is_published"])
        self.assertFalse(self.client.get("/v2/lessons").json()[0]["is_published"])
        self.assertEqual(self.client.get("/v2/explore/lessons").json(), [])
        self.assertEqual(self.client.get("/v2/explore/tags").json(), [])
        self.assertEqual(
            self.client.post(f"/v2/explore/lessons/{edited_id}/access-url").status_code,
            404,
        )

    def test_only_ready_lessons_can_be_published(self) -> None:
        with Session(self.app.state.engine) as session:
            lesson = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Still generating",
                lesson_format="video",
            )
            lesson_id = lesson.id

        response = self.client.put(
            f"/v2/lessons/{lesson_id}/publication",
            json={"published": True},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["error"]["code"], "lesson_not_ready")

    def test_my_published_lessons_are_owner_scoped(self) -> None:
        with Session(self.app.state.engine) as session:
            for owner_id, topic in (
                ("teacher-a", "My published lesson"),
                ("teacher-b", "Another teacher's lesson"),
            ):
                lesson = create_lesson(
                    session,
                    owner_id=owner_id,
                    topic=topic,
                    lesson_format="interactive",
                )
                lesson.status = "ready"
                lesson.object_key = f"lessons/{owner_id}/{lesson.id}/lesson.html"
                save_lesson(session, lesson)
                ensure_user_profile(
                    session,
                    owner_id=owner_id,
                    display_name=owner_id,
                )
                set_lesson_publication(session, lesson, True)

        mine = self.client.get("/v2/explore/lessons/mine")
        public = self.client.get("/v2/explore/lessons")

        self.assertEqual(mine.status_code, 200)
        self.assertEqual([lesson["topic"] for lesson in mine.json()], ["My published lesson"])
        self.assertCountEqual(
            [lesson["topic"] for lesson in public.json()],
            ["My published lesson", "Another teacher's lesson"],
        )

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
        observed_connections: list[tuple[str, int]] = []
        connections = ConnectionTracker(self.app.state.engine)

        class InspectingLLM(FakeLLM):
            async def generate(self, prompt: str) -> LLMResult:
                observed_connections.append(("llm", connections.active))
                return await super().generate(prompt)

        original_upload_file = self.storage.upload_file

        def upload_file(source: Path, object_key: str, content_type: str) -> None:
            observed_connections.append(("storage", connections.active))
            original_upload_file(source, object_key, content_type)

        self.app.dependency_overrides[get_llm_provider] = lambda: InspectingLLM()
        self.storage.upload_file = upload_file
        try:
            with connections:
                response = self.client.post(
                    "/v2/generations",
                    data={"topic": "Connection lifecycle", "format": "interactive"},
                )
        finally:
            self.storage.upload_file = original_upload_file

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_connections, [("llm", 0), ("storage", 0)])

    def test_access_url_releases_its_connection_before_signing(self) -> None:
        generated = self.client.post(
            "/v2/generations",
            data={"topic": "Signed URL lifecycle", "format": "interactive"},
        )
        lesson_id = _completed_lesson_id(generated.text)
        observed_connections: list[int] = []
        connections = ConnectionTracker(self.app.state.engine)

        def signed_url(object_key: str, *, download_name: str | None = None) -> str:
            observed_connections.append(connections.active)
            return f"https://storage.test/{object_key}"

        original_signed_url = self.storage.signed_url
        self.storage.signed_url = signed_url
        try:
            with connections:
                response = self.client.post(f"/v2/lessons/{lesson_id}/access-url")
        finally:
            self.storage.signed_url = original_signed_url

        self.assertEqual(response.status_code, 200)
        self.assertEqual(observed_connections, [0])

    def test_delete_releases_its_connection_before_storage_calls(self) -> None:
        generated = self.client.post(
            "/v2/generations",
            data={"topic": "Delete lifecycle", "format": "interactive"},
        )
        lesson_id = _completed_lesson_id(generated.text)
        observed_connections: list[int] = []
        connections = ConnectionTracker(self.app.state.engine)

        original_delete_prefix = self.storage.delete_prefix

        def delete_prefix(prefix: str) -> None:
            observed_connections.append(connections.active)
            original_delete_prefix(prefix)

        self.storage.delete_prefix = delete_prefix
        try:
            with connections:
                response = self.client.delete(f"/v2/lessons/{lesson_id}")
        finally:
            self.storage.delete_prefix = original_delete_prefix

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
        self.assertIsNone(history[0]["error_message"])
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
        # Lesson cards, their tags, and version counts each use one bounded query.
        self.assertEqual(len(select_statements), 3)
        self.assertEqual(sum("lesson_tags" in statement for statement in select_statements), 1)
        dashboard_select = select_statements[0]
        for private_or_heavy_field in (
            "source_code",
            "lesson_spec",
            "raw_model_output",
            "first_error",
            "object_key",
        ):
            self.assertNotIn(private_or_heavy_field, dashboard_select)

    def test_lesson_tags_are_root_scoped_searchable_and_validated(self) -> None:
        first = self.client.post(
            "/v2/generations",
            data={"topic": "Fraction models", "format": "interactive"},
        )
        first_id = _completed_lesson_id(first.text)
        edited = self.client.post(
            "/v2/generations",
            data={
                "topic": "Fraction models",
                "format": "interactive",
                "base_lesson_id": first_id,
                "edit_instruction": "Add a number line.",
            },
        )
        edited_id = _completed_lesson_id(edited.text)

        updated = self.client.put(
            f"/v2/lessons/{edited_id}/tags",
            json={"tags": [" Math ", "math", "Number Sense"]},
        )

        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["tags"], ["Math", "Number Sense"])
        self.assertEqual(self.client.get(f"/v2/lessons/{first_id}").json()["tags"], ["Math", "Number Sense"])
        self.assertEqual(self.client.get(f"/v2/lessons/{edited_id}").json()["tags"], ["Math", "Number Sense"])
        self.assertEqual(
            [lesson["id"] for lesson in self.client.get("/v2/lessons?tag=math&tag=number+sense").json()],
            [first_id],
        )
        self.assertEqual(
            [lesson["id"] for lesson in self.client.get("/v2/lessons?q=number+sense").json()],
            [first_id],
        )
        self.assertEqual(
            self.client.get("/v2/lessons/tags").json(),
            [
                {"label": "Math", "value": "math", "lesson_count": 1},
                {"label": "Number Sense", "value": "number sense", "lesson_count": 1},
            ],
        )
        self.assertEqual(
            self.client.put(
                f"/v2/lessons/{first_id}/tags",
                json={"tags": ["1", "2", "3", "4", "5", "6"]},
            ).status_code,
            422,
        )

        self.assertEqual(self.client.delete(f"/v2/lessons/{first_id}").status_code, 204)
        with Session(self.app.state.engine) as session:
            self.assertEqual(session.exec(select(LessonTag)).all(), [])

    def test_lesson_queries_are_tenant_isolated(self) -> None:
        with Session(self.app.state.engine) as session:
            mine = create_lesson(session, owner_id="teacher-a", topic="Mine", lesson_format="slides")
            other = create_lesson(session, owner_id="teacher-b", topic="Other", lesson_format="slides")
            session.add(
                LessonTag(
                    root_lesson_id=other.id,
                    owner_id="teacher-b",
                    normalized_value="private",
                    label="Private",
                )
            )
            session.commit()
            mine_id = str(mine.id)
            other_id = str(other.id)

        response = self.client.get("/v2/lessons")
        ids = {row["id"] for row in response.json()}
        self.assertIn(mine_id, ids)
        self.assertNotIn(other_id, ids)
        self.assertEqual(self.client.get("/v2/lessons/tags").json(), [])
        self.assertEqual(self.client.get(f"/v2/lessons/{other_id}").status_code, 404)
        self.assertEqual(
            self.client.put(
                f"/v2/lessons/{other_id}/publication",
                json={"published": False},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                f"/v2/lessons/{other_id}/tags",
                json={"tags": ["No access"]},
            ).status_code,
            404,
        )

    def test_folder_tree_moves_lessons_and_only_deletes_leaf_folders(self) -> None:
        parent_response = self.client.post(
            "/v2/folders",
            json={"name": "Math", "parent_id": None},
        )
        self.assertEqual(parent_response.status_code, 201)
        parent = parent_response.json()
        child_response = self.client.post(
            "/v2/folders",
            json={"name": "Geometry", "parent_id": parent["id"]},
        )
        self.assertEqual(child_response.status_code, 201)
        child = child_response.json()

        duplicate = self.client.post(
            "/v2/folders",
            json={"name": " Geometry ", "parent_id": parent["id"]},
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.json()["error"]["code"], "folder_name_conflict")

        with Session(self.app.state.engine) as session:
            root = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Triangles",
                lesson_format="slides",
            )
            revision = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Triangles",
                lesson_format="slides",
                root_lesson_id=root.id,
                parent_lesson_id=root.id,
                version_number=2,
            )
            lesson_id = str(revision.id)
            root_id = root.id
            revision_id = revision.id

        moved = self.client.put(
            f"/v2/lessons/{lesson_id}/folder",
            json={"folder_id": child["id"]},
        )
        self.assertEqual(moved.status_code, 200)
        self.assertEqual(moved.json()["folder_id"], child["id"])
        self.assertEqual(self.client.get("/v2/lessons").json()[0]["folder_id"], child["id"])

        blocked = self.client.delete(f"/v2/folders/{parent['id']}")
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.json()["error"]["code"], "folder_has_children")

        renamed = self.client.patch(
            f"/v2/folders/{parent['id']}",
            json={"name": "Mathematics"},
        )
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.json()["name"], "Mathematics")

        self.assertEqual(self.client.delete(f"/v2/folders/{child['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/v2/lessons/{lesson_id}").json()["folder_id"], parent["id"])
        with Session(self.app.state.engine) as session:
            root = get_owned_lesson(session, root_id, "teacher-a")
            revision = get_owned_lesson(session, revision_id, "teacher-a")
            self.assertEqual(str(root.folder_id), parent["id"])
            self.assertIsNone(revision.folder_id)

        self.assertEqual(self.client.delete(f"/v2/folders/{parent['id']}").status_code, 204)
        self.assertIsNone(self.client.get(f"/v2/lessons/{lesson_id}").json()["folder_id"])

    def test_folder_operations_are_tenant_isolated(self) -> None:
        with Session(self.app.state.engine) as session:
            other_folder = LessonFolder(owner_id="teacher-b", name="Private")
            mine = create_lesson(
                session,
                owner_id="teacher-a",
                topic="Mine",
                lesson_format="interactive",
            )
            session.add(other_folder)
            session.commit()
            session.refresh(other_folder)
            other_folder_id = str(other_folder.id)
            lesson_id = str(mine.id)

        self.assertEqual(self.client.get("/v2/folders").json(), [])
        self.assertEqual(
            self.client.post(
                "/v2/folders",
                json={"name": "Child", "parent_id": other_folder_id},
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.put(
                f"/v2/lessons/{lesson_id}/folder",
                json={"folder_id": other_folder_id},
            ).status_code,
            404,
        )
        self.assertEqual(self.client.patch(f"/v2/folders/{other_folder_id}", json={"name": "No"}).status_code, 404)
        self.assertEqual(self.client.delete(f"/v2/folders/{other_folder_id}").status_code, 404)

    def test_missing_identity_token_is_rejected(self) -> None:
        self.app.dependency_overrides.pop(get_current_user)

        response = self.client.get("/v2/lessons")
        public_response = self.client.get("/v2/explore/lessons")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")
        self.assertEqual(public_response.status_code, 200)

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
            object_key = lesson.object_key
            session.add(LessonLike(root_lesson_id=lesson.root_lesson_id, owner_id="teacher-b"))
            session.commit()

        response = self.client.delete(f"/v2/lessons/{lesson_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.storage.deletions[0][0], "prefix")
        self.assertEqual(self.storage.deletions[1], ("object", object_key))
        self.assertEqual(self.client.get(f"/v2/lessons/{lesson_id}").status_code, 404)
        with Session(self.app.state.engine) as session:
            self.assertEqual(
                session.exec(
                    select(LessonLike).where(LessonLike.root_lesson_id == lesson_id)
                ).all(),
                [],
            )

    def test_source_count_and_combined_byte_limits(self) -> None:
        count_settings = Settings(app_env="test", max_source_files=1)
        uploads = [
            UploadFile(filename="one.pdf", file=BytesIO(b"%PDF")),
            UploadFile(filename="two.pdf", file=BytesIO(b"%PDF")),
        ]
        with self.assertRaisesRegex(Exception, "at most 1"):
            asyncio.run(extract_sources(uploads, count_settings))

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
        with self.assertRaisesRegex(Exception, "combined source files"):
            asyncio.run(extract_sources([upload], byte_settings))

    def test_source_images_are_signature_checked(self) -> None:
        settings = Settings(app_env="test")
        valid = UploadFile(
            filename="diagram.webp",
            file=BytesIO(b"RIFF\x04\x00\x00\x00WEBPdata"),
            headers=Headers({"content-type": "image/webp"}),
        )
        documents = asyncio.run(extract_sources([valid], settings))

        self.assertEqual(documents[0].media_type, "image/webp")

        invalid = UploadFile(
            filename="diagram.png",
            file=BytesIO(b"not-an-image"),
            headers=Headers({"content-type": "image/png"}),
        )
        with self.assertRaisesRegex(Exception, "not a valid PNG image"):
            asyncio.run(extract_sources([invalid], settings))

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
            asyncio.run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

    def test_html_renderer_accepts_terminating_counter_loop_and_ignores_lesson_text(self) -> None:
        generated = """<!doctype html><html><body><script>
const p5 = true;
const example = "for (let i = steps; i >= 0; i++)";
for (let i = steps; i >= 0; i--) drawPoint(i);
</script></body></html>"""
        with TemporaryDirectory() as directory:
            asset = asyncio.run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

        self.assertEqual(asset.extension, "html")

    def test_html_renderer_rejects_static_latex_without_global_typesetting(self) -> None:
        generated = r'''<!doctype html><html><head>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
</head><body><div id="legend">$\triangle WXM$</div><script>
const p5 = true;
// renderMathInElement(document.body) is not an actual typesetting call.
renderMathInElement(document.getElementById("content"));
</script></body></html>'''
        with TemporaryDirectory() as directory, self.assertRaisesRegex(
            RenderError, "without global KaTeX typesetting"
        ):
            asyncio.run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

    def test_html_renderer_accepts_static_latex_with_global_typesetting(self) -> None:
        generated = r'''<!doctype html><html><head>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
</head><body><div id="legend">$\triangle WXM$</div><script>
const p5 = true;
window.addEventListener("DOMContentLoaded", () => renderMathInElement(document.body));
</script></body></html>'''
        with TemporaryDirectory() as directory:
            asset = asyncio.run(
                HTMLRenderer(required_marker="p5").render(generated, Path(directory))
            )

        self.assertEqual(asset.extension, "html")

    def test_interactive_prompt_and_repair_prompt_cover_generation_constraints(self) -> None:
        for section in (
            "<DELIVERABLE>",
            "<TEACHING_AND_INTERACTION>",
            "<VISUAL_LAYOUT>",
            "<MATH_RENDERING>",
            "<POINTER_COORDINATES>",
            "<STATE_AND_MODE_CHECKS>",
            "<RUNTIME_SAFETY>",
            "<SECURITY_RULES>",
        ):
            self.assertIn(section, INTERACTIVE_RULES)
        normalized_rules = " ".join(INTERACTIVE_RULES.split())
        self.assertIn("free from unintended overlap", normalized_rules)
        self.assertIn(
            "consistent spacing, alignment, margins, and visual density",
            normalized_rules,
        )
        self.assertIn("do not crowd one area", normalized_rules)
        self.assertIn("Reflow, resize, or simplify content", normalized_rules)
        self.assertIn("KaTeX 0.16.9", normalized_rules)
        self.assertIn("auto-render to recognize `$...$`", normalized_rules)
        self.assertIn("After dynamically inserting or changing a formula", normalized_rules)
        self.assertIn("Never leave raw LaTeX delimiters visible", normalized_rules)
        self.assertIn(
            "Make pointer interactions work after responsive scaling", normalized_rules
        )
        self.assertIn("Every mode switch must update", normalized_rules)
        self.assertIn("Ensure draw() reads the current mode", normalized_rules)
        self.assertIn("trace the initial state and every mode", normalized_rules)
        self.assertIn("each referenced function and DOM id exists", normalized_rules)
        self.assertIn(
            "Do not name variables or function parameters after p5.js functions",
            normalized_rules,
        )
        self.assertIn("cannot throw an exception, freeze draw()", normalized_rules)
        self.assertIn("decrement toward a lower bound", INTERACTIVE_RULES)
        self.assertTrue(
            InteractiveStrategy().can_repair(RenderError("raw LaTeX is visible"))
        )
        repair = build_code_repair_prompt(
            original_prompt="Create an interactive lesson.",
            code="<html><script>const p5 = true;</script></html>",
            error="counter loop whose update moves away",
        )

        self.assertIn("failed validation or rendering", repair)
        self.assertIn("requested format", repair)
        self.assertIn("<REPAIR_TASK>", repair)
        self.assertNotIn("previous Manim code", repair)


if __name__ == "__main__":
    unittest.main()
