import asyncio
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Awaitable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic
from typing import TypeVar
from uuid import UUID

from sqlmodel import Session

from backend.app.core.config import get_settings
from backend.app.db.lessons import (
    create_lesson,
    get_owned_lesson,
    next_version_number,
    save_lesson,
)
from backend.app.integrations.llm.base import (
    LLMProvider,
    LLMProviderError,
    LLMResult,
    StreamingLLMProvider,
)
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
LLM_HEARTBEAT_SECONDS = 10.0
LLM_PROGRESS_INTERVAL_SECONDS = 0.5
LLM_PROGRESS_CHARACTER_STEP = 500


@dataclass(frozen=True)
class LLMProgress:
    stage: str
    message: str
    generated_characters: int


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

    async def _generate_with_progress(
        self,
        prompt: str,
        *,
        lesson_id: UUID,
        owner_hash: str,
        stage: str,
        message: str,
    ) -> AsyncIterator[LLMProgress | LLMResult]:
        started = monotonic()
        if isinstance(self.llm, StreamingLLMProvider):
            result: LLMResult | None = None
            text_parts: list[str] = []
            input_tokens = None
            output_tokens = None
            provider = "unknown"
            model = "unknown"
            generated_characters = 0
            reported_characters = 0
            last_progress_at = started
            iterator = self.llm.stream(prompt).__aiter__()
            pending_chunk: asyncio.Task | None = None
            try:
                while True:
                    if pending_chunk is None:
                        pending_chunk = asyncio.create_task(anext(iterator))
                    remaining = self.deadline - monotonic()
                    if remaining <= 0:
                        raise TimeoutError
                    done, _ = await asyncio.wait(
                        {pending_chunk},
                        timeout=min(LLM_HEARTBEAT_SECONDS, remaining),
                    )
                    if not done:
                        yield LLMProgress(
                            stage=stage,
                            message=_llm_progress_message(message, generated_characters),
                            generated_characters=generated_characters,
                        )
                        reported_characters = generated_characters
                        last_progress_at = monotonic()
                        continue
                    try:
                        chunk = pending_chunk.result()
                    except StopAsyncIteration:
                        pending_chunk = None
                        break
                    pending_chunk = None
                    text_parts.append(chunk.text)
                    generated_characters += len(chunk.text)
                    provider = chunk.provider
                    model = chunk.model
                    input_tokens = chunk.input_tokens or input_tokens
                    output_tokens = chunk.output_tokens or output_tokens
                    now = monotonic()
                    if (
                        generated_characters - reported_characters >= LLM_PROGRESS_CHARACTER_STEP
                        or now - last_progress_at >= LLM_PROGRESS_INTERVAL_SECONDS
                    ):
                        yield LLMProgress(
                            stage=stage,
                            message=_llm_progress_message(message, generated_characters),
                            generated_characters=generated_characters,
                        )
                        reported_characters = generated_characters
                        last_progress_at = now
            finally:
                if pending_chunk is not None and not pending_chunk.done():
                    pending_chunk.cancel()
                    with suppress(asyncio.CancelledError):
                        await pending_chunk
                close_iterator = getattr(iterator, "aclose", None)
                if close_iterator is not None:
                    with suppress(Exception):
                        await close_iterator()
            generated_text = "".join(text_parts)
            if len(generated_text) != reported_characters:
                yield LLMProgress(
                    stage=stage,
                    message=_llm_progress_message(message, len(generated_text)),
                    generated_characters=len(generated_text),
                )
            result = LLMResult(
                text=generated_text,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            )
        else:
            generation_task = asyncio.create_task(self.llm.generate(prompt))
            try:
                while True:
                    remaining = self.deadline - monotonic()
                    if remaining <= 0:
                        raise TimeoutError
                    done, _ = await asyncio.wait(
                        {generation_task},
                        timeout=min(LLM_HEARTBEAT_SECONDS, remaining),
                    )
                    if done:
                        result = generation_task.result()
                        break
                    yield LLMProgress(
                        stage=stage,
                        message=_llm_progress_message(message, 0),
                        generated_characters=0,
                    )
            finally:
                if not generation_task.done():
                    generation_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await generation_task

        logger.info(
            "lesson_llm_completed",
            extra={
                "lesson_id": str(lesson_id),
                "owner_id_hash": owner_hash,
                "stage": stage,
                "provider": result.provider,
                "model": result.model,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "duration_ms": round((monotonic() - started) * 1000),
                "request_id": self.request_id,
            },
        )
        yield result

    async def _cleanup_failed_storage(
        self,
        *,
        lesson_id: UUID,
        owner_hash: str,
        object_key: str | None,
        source_prefix: str | None,
    ) -> None:
        operations = []
        if object_key:
            operations.append(("output", self.storage.delete, object_key))
        if source_prefix:
            operations.append(("sources", self.storage.delete_prefix, source_prefix))
        for target, operation, key in operations:
            try:
                await asyncio.to_thread(operation, key)
            except Exception:
                logger.warning(
                    "lesson_storage_cleanup_failed",
                    extra={
                        "lesson_id": str(lesson_id),
                        "owner_id_hash": owner_hash,
                        "stage": target,
                        "request_id": self.request_id,
                    },
                )

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
        started = monotonic()
        owner_hash = hashlib.sha256(owner_id.encode()).hexdigest()[:16]
        object_key: str | None = None
        previous_code = None
        root_lesson_id = None
        parent_lesson_id = None
        version_number = 1
        if base_lesson_id:
            base_lesson = get_owned_lesson(self.session, base_lesson_id, owner_id)
            if not base_lesson:
                raise ValueError("The lesson to edit was not found.")
            previous_code = base_lesson.source_code
            root_lesson_id = base_lesson.root_lesson_id
            parent_lesson_id = base_lesson.id
            version_number = next_version_number(self.session, root_lesson_id, owner_id)

        lesson = create_lesson(
            self.session,
            owner_id=owner_id,
            topic=topic,
            lesson_format=lesson_format,
            root_lesson_id=root_lesson_id,
            parent_lesson_id=parent_lesson_id,
            version_number=version_number,
            edit_instruction=edit_instruction,
        )
        source_prefix = f"sources/{owner_id}/{lesson.id}/" if sources else None
        yield _event("started", {"lesson_id": str(lesson.id)})

        try:

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
            result = None
            async for llm_event in self._generate_with_progress(
                prompt,
                lesson_id=lesson.id,
                owner_hash=owner_hash,
                stage="generating",
                message="Creating lesson code…",
            ):
                if isinstance(llm_event, LLMResult):
                    result = llm_event
                else:
                    yield _event("progress", _progress_data(llm_event))
            if result is None:
                raise RuntimeError("The AI provider returned no final result.")
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
                    repair = None
                    async for llm_event in self._generate_with_progress(
                        build_repair_prompt(
                            original_prompt=prompt,
                            code=generated.code,
                            error=str(first_error),
                        ),
                        lesson_id=lesson.id,
                        owner_hash=owner_hash,
                        stage="repairing",
                        message="Repairing the video scene…",
                    ):
                        if isinstance(llm_event, LLMResult):
                            repair = llm_event
                        else:
                            yield _event("progress", _progress_data(llm_event))
                    if repair is None:
                        raise RuntimeError("The AI provider returned no repair result.")
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
            await self._cleanup_failed_storage(
                lesson_id=lesson.id,
                owner_hash=owner_hash,
                object_key=object_key,
                source_prefix=source_prefix,
            )
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
            await self._cleanup_failed_storage(
                lesson_id=lesson.id,
                owner_hash=owner_hash,
                object_key=object_key,
                source_prefix=source_prefix,
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


def _llm_progress_message(message: str, generated_characters: int) -> str:
    if generated_characters:
        return f"{message} {generated_characters:,} characters generated"
    return f"{message} Waiting for the model…"


def _progress_data(progress: LLMProgress) -> dict[str, object]:
    return {
        "stage": progress.stage,
        "message": progress.message,
        "generated_characters": progress.generated_characters,
    }


def _public_error(error: Exception) -> str:
    if isinstance(error, LLMProviderError):
        # The upstream text is what makes this actionable: an exhausted balance, an
        # unknown model id, and a rejected key all arrive as the same generic
        # failure otherwise. Production keeps the generic message so provider
        # internals stay out of browser-visible responses.
        if get_settings().app_env == "production":
            return "The configured AI provider could not complete this request."
        return f"The configured AI provider could not complete this request. Upstream: {error}"
    if isinstance(error, RenderError):
        return "The generated lesson could not be rendered. Please try again."
    if isinstance(error, TimeoutError):
        return "Lesson generation timed out. Please try again."
    if isinstance(error, ValueError):
        return str(error)
    return "Lesson generation failed unexpectedly. Please try again."
