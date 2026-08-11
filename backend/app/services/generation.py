import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Awaitable
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import TypeVar
from uuid import UUID

from sqlmodel import Session

from backend.app.db.lessons import create_lesson, get_owned_lesson, save_lesson
from backend.app.integrations.llm.base import LLMProvider, LLMProviderError
from backend.app.integrations.storage import GCSStorage
from backend.app.renderers.base import RenderError, Renderer
from backend.app.services.prompts import (
    build_generation_prompt,
    build_repair_prompt,
    parse_generated_lesson,
)
from backend.app.services.sources import SourceDocument, source_context

logger = logging.getLogger(__name__)
T = TypeVar("T")


class GenerationService:
    def __init__(
        self,
        *,
        session: Session,
        llm: LLMProvider,
        storage: GCSStorage,
        renderers: dict[str, Renderer],
        deadline: float,
        request_id: str,
    ) -> None:
        self.session = session
        self.llm = llm
        self.storage = storage
        self.renderers = renderers
        self.deadline = deadline
        self.request_id = request_id

    async def _await(self, operation: Awaitable[T]) -> T:
        remaining = self.deadline - monotonic()
        return await asyncio.wait_for(operation, timeout=max(0, remaining))

    async def stream(
        self,
        *,
        owner_id: str,
        topic: str,
        lesson_format: str,
        sources: list[SourceDocument],
        base_lesson_id: UUID | None,
        edit_instruction: str | None,
    ) -> AsyncIterator[str]:
        lesson = create_lesson(
            self.session,
            owner_id=owner_id,
            topic=topic,
            lesson_format=lesson_format,
        )
        started = monotonic()
        owner_hash = hashlib.sha256(owner_id.encode()).hexdigest()[:16]
        object_key: str | None = None
        yield _event("started", {"lesson_id": str(lesson.id)})

        try:
            previous_code = None
            if base_lesson_id:
                base_lesson = get_owned_lesson(self.session, base_lesson_id, owner_id)
                if not base_lesson:
                    raise ValueError("The lesson to edit was not found.")
                previous_code = base_lesson.source_code

            for source in sources:
                source_key = f"sources/{owner_id}/{lesson.id}/{source.filename}"
                await self._await(
                    asyncio.to_thread(
                        self.storage.upload_bytes,
                        source.data,
                        source_key,
                        "application/pdf",
                    )
                )
            prompt = build_generation_prompt(
                topic=topic,
                lesson_format=lesson_format,
                sources=source_context(sources),
                previous_code=previous_code,
                edit_instruction=edit_instruction,
            )
            yield _event("progress", {"stage": "generating", "message": "Creating lesson code…"})
            llm_started = monotonic()
            result = await self._await(self.llm.generate(prompt))
            logger.info(
                "lesson_llm_completed",
                extra={
                    "lesson_id": str(lesson.id),
                    "owner_id_hash": owner_hash,
                    "stage": "generating",
                    "provider": result.provider,
                    "model": result.model,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "duration_ms": round((monotonic() - llm_started) * 1000),
                    "request_id": self.request_id,
                },
            )
            yield _event("progress", {"stage": "validating", "message": "Checking the generated lesson…"})
            generated = parse_generated_lesson(result.text)
            renderer = self.renderers[lesson_format]

            yield _event("progress", {"stage": "rendering", "message": "Preparing the lesson preview…"})
            with TemporaryDirectory(prefix="chalksmith-") as directory:
                workdir = Path(directory)
                render_started = monotonic()
                render_stage = "rendering"
                try:
                    asset = await self._await(renderer.render(generated.code, workdir))
                except RenderError as first_error:
                    if lesson_format != "video":
                        raise
                    logger.warning(
                        "lesson_render_retry",
                        extra={
                            "lesson_id": str(lesson.id),
                            "owner_id_hash": owner_hash,
                            "stage": "rendering",
                            "duration_ms": round((monotonic() - render_started) * 1000),
                            "request_id": self.request_id,
                        },
                    )
                    yield _event("progress", {"stage": "repairing", "message": "Repairing the video scene…"})
                    llm_started = monotonic()
                    repair = await self._await(
                        self.llm.generate(
                            build_repair_prompt(
                                original_prompt=prompt,
                                code=generated.code,
                                error=str(first_error),
                            )
                        )
                    )
                    logger.info(
                        "lesson_llm_completed",
                        extra={
                            "lesson_id": str(lesson.id),
                            "owner_id_hash": owner_hash,
                            "stage": "repairing",
                            "provider": repair.provider,
                            "model": repair.model,
                            "input_tokens": repair.input_tokens,
                            "output_tokens": repair.output_tokens,
                            "duration_ms": round((monotonic() - llm_started) * 1000),
                            "request_id": self.request_id,
                        },
                    )
                    generated = parse_generated_lesson(repair.text)
                    render_started = monotonic()
                    render_stage = "repairing"
                    asset = await self._await(renderer.render(generated.code, workdir))

                output_bytes = asset.path.stat().st_size
                logger.info(
                    "lesson_render_completed",
                    extra={
                        "lesson_id": str(lesson.id),
                        "owner_id_hash": owner_hash,
                        "stage": render_stage,
                        "duration_ms": round((monotonic() - render_started) * 1000),
                        "output_bytes": output_bytes,
                        "request_id": self.request_id,
                    },
                )
                object_key = f"lessons/{owner_id}/{lesson.id}/lesson.{asset.extension}"
                yield _event("progress", {"stage": "saving", "message": "Saving the finished lesson…"})
                await self._await(
                    asyncio.to_thread(
                        self.storage.upload_file,
                        asset.path,
                        object_key,
                        asset.content_type,
                    )
                )

            lesson.status = "ready"
            lesson.summary = generated.summary
            lesson.source_code = generated.code
            lesson.object_key = object_key
            save_lesson(self.session, lesson)
            logger.info(
                "lesson_generation_completed",
                extra={
                    "lesson_id": str(lesson.id),
                    "owner_id_hash": owner_hash,
                    "stage": "complete",
                    "duration_ms": round((monotonic() - started) * 1000),
                    "request_id": self.request_id,
                },
            )
            yield _event("complete", {"lesson_id": str(lesson.id)})
        except (asyncio.CancelledError, GeneratorExit):
            logger.info(
                "lesson_generation_cancelled",
                extra={
                    "lesson_id": str(lesson.id),
                    "owner_id_hash": owner_hash,
                    "stage": "cancelled",
                    "duration_ms": round((monotonic() - started) * 1000),
                    "request_id": self.request_id,
                },
            )
            lesson.status = "failed"
            lesson.error_message = "Generation was cancelled."
            save_lesson(self.session, lesson)
            raise
        except Exception as error:
            logger.exception(
                "lesson_generation_failed",
                extra={
                    "lesson_id": str(lesson.id),
                    "owner_id_hash": owner_hash,
                    "stage": "error",
                    "duration_ms": round((monotonic() - started) * 1000),
                    "request_id": self.request_id,
                },
            )
            if object_key:
                try:
                    await asyncio.to_thread(self.storage.delete, object_key)
                except Exception:
                    logger.warning(
                        "lesson_output_cleanup_failed",
                        extra={
                            "lesson_id": str(lesson.id),
                            "owner_id_hash": owner_hash,
                            "request_id": self.request_id,
                        },
                    )
            lesson.status = "failed"
            lesson.error_message = _public_error(error)
            save_lesson(self.session, lesson)
            yield _event(
                "error",
                {
                    "code": "generation_failed",
                    "message": lesson.error_message,
                    "lesson_id": str(lesson.id),
                },
            )


def _event(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _public_error(error: Exception) -> str:
    if isinstance(error, LLMProviderError):
        return "The configured AI provider could not complete this request."
    if isinstance(error, RenderError):
        return "The generated lesson could not be rendered. Please try again."
    if isinstance(error, TimeoutError):
        return "Lesson generation timed out. Please try again."
    if isinstance(error, ValueError):
        return str(error)
    return "Lesson generation failed unexpectedly. Please try again."
