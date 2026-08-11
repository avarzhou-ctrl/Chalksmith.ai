import asyncio
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from fastapi import UploadFile

from backend.app.core.config import Settings
from backend.app.core.errors import AppError


@dataclass(frozen=True)
class SourceDocument:
    filename: str
    text: str
    data: bytes


async def extract_sources(files: list[UploadFile], settings: Settings) -> list[SourceDocument]:
    if len(files) > settings.max_source_files:
        raise AppError(
            code="too_many_sources",
            message=f"Upload at most {settings.max_source_files} PDF files.",
            status_code=413,
        )
    documents: list[SourceDocument] = []
    total_bytes = 0
    total_characters = 0
    for upload in files:
        filename = Path(upload.filename or "source.pdf").name
        if upload.content_type not in {"application/pdf", "application/octet-stream"}:
            raise AppError(
                code="unsupported_source_type",
                message=f'"{filename}" must be a PDF file.',
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
                message="The combined PDF uploads exceed the request size limit.",
                status_code=413,
            )
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
        documents.append(SourceDocument(filename=filename, text=text, data=data))
    return documents


def _extract_pdf_text(data: bytes) -> str:
    with pymupdf.open(stream=data, filetype="pdf") as pdf:
        return "\n".join(page.get_text("text") for page in pdf).strip()


def source_context(documents: list[SourceDocument]) -> str:
    if not documents:
        return ""
    sections = [f"SOURCE: {document.filename}\n{document.text}" for document in documents]
    return "\n\n---\n\n".join(sections)
