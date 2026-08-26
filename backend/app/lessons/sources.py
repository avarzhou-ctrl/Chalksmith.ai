import asyncio
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from fastapi import UploadFile

from backend.app.core.config import Settings
from backend.app.core.errors import AppError
from backend.app.integrations.llm.base import LLMImage

IMAGE_MEDIA_TYPES = {
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
SUPPORTED_MEDIA_TYPES = {"application/pdf", *IMAGE_MEDIA_TYPES.values()}


@dataclass(frozen=True)
class SourceDocument:
    filename: str
    media_type: str
    data: bytes
    text: str | None = None


async def extract_sources(files: list[UploadFile], settings: Settings) -> list[SourceDocument]:
    if len(files) > settings.max_source_files:
        raise AppError(
            code="too_many_sources",
            message=f"Upload at most {settings.max_source_files} source files.",
            status_code=413,
        )
    documents: list[SourceDocument] = []
    total_bytes = 0
    total_characters = 0
    for upload in files:
        filename = Path(upload.filename or "source").name
        media_type = _declared_media_type(filename, upload.content_type)
        if media_type is None:
            raise AppError(
                code="unsupported_source_type",
                message=f'"{filename}" must be a PDF, PNG, JPEG, or WebP file.',
                status_code=422,
            )
        data = await upload.read(settings.max_source_bytes + 1)
        if len(data) > settings.max_source_bytes:
            raise AppError(
                code="source_too_large",
                message=f'"{filename}" exceeds the upload size limit.',
                status_code=413,
            )
        total_bytes += len(data)
        if total_bytes > settings.max_total_source_bytes:
            raise AppError(
                code="sources_too_large",
                message="The combined source files exceed the request size limit.",
                status_code=413,
            )
        if media_type == "application/pdf":
            if not data.startswith(b"%PDF"):
                raise AppError(code="invalid_pdf", message=f'"{filename}" is not a valid PDF.', status_code=422)
            try:
                text = await asyncio.to_thread(_extract_pdf_text, data)
            except Exception as error:
                raise AppError(code="pdf_extraction_failed", message=f'Could not read "{filename}".', status_code=422) from error
            if not text:
                raise AppError(
                    code="pdf_has_no_text",
                    message=f'"{filename}" has no readable text layer.',
                    status_code=422,
                )
            total_characters += len(text)
            if total_characters > settings.max_source_characters:
                raise AppError(
                    code="source_text_too_large",
                    message="The combined source text exceeds the generation limit.",
                    status_code=413,
                )
            documents.append(
                SourceDocument(filename=filename, media_type=media_type, data=data, text=text)
            )
            continue

        if _detected_image_media_type(data) != media_type:
            raise AppError(
                code="invalid_image",
                message=f'"{filename}" is not a valid {media_type.removeprefix("image/").upper()} image.',
                status_code=422,
            )
        documents.append(SourceDocument(filename=filename, media_type=media_type, data=data))
    return documents


def _declared_media_type(filename: str, content_type: str | None) -> str | None:
    normalized = (content_type or "").lower().split(";", 1)[0].strip()
    if normalized in SUPPORTED_MEDIA_TYPES:
        return normalized
    if normalized not in {"", "application/octet-stream"}:
        return None
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    return IMAGE_MEDIA_TYPES.get(suffix)


def _detected_image_media_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _extract_pdf_text(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        return "\n".join(page.get_text("text") for page in pdf).strip()


def source_context(documents: list[SourceDocument]) -> str:
    if not documents:
        return ""
    sections = [
        (
            f"SOURCE DOCUMENT: {document.filename}\n{document.text}"
            if document.text is not None
            else f"SOURCE IMAGE: {document.filename}\n[Image content is attached separately.]"
        )
        for document in documents
    ]
    return "\n\n---\n\n".join(sections)


def source_images(documents: list[SourceDocument]) -> tuple[LLMImage, ...]:
    return tuple(
        LLMImage(filename=document.filename, media_type=document.media_type, data=document.data)
        for document in documents
        if document.media_type.startswith("image/")
    )
