"""Dry-run-first migration from the v1 lesson table and static files to v2."""

import argparse
import json
import mimetypes
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from google.cloud import storage
from sqlalchemy import create_engine, text

from backend.app.renderers.html import secure_html_document

FORMAT_MAP = {
    "p5.js": "interactive",
    "reveal.js": "slides",
    "manim": "video",
    "remotion": "video",
    "interactive": "interactive",
    "slides": "slides",
    "video": "video",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write rows and upload files.")
    parser.add_argument("--static-root", type=Path, default=Path("backend/static"))
    parser.add_argument("--orphan-owner", help="Owner uid to use only for legacy rows with no user_id.")
    parser.add_argument("--owner-map", type=Path, help="JSON object mapping Clerk uid to Identity Platform uid.")
    parser.add_argument(
        "--preserve-owner-ids",
        action="store_true",
        help="Keep legacy owner ids only when Identity Platform was imported with identical uids.",
    )
    return parser.parse_args()


def stable_uuid(value: str) -> UUID:
    try:
        return UUID(value)
    except ValueError:
        return uuid5(NAMESPACE_URL, f"chalksmith-v1:{value}")


def psycopg_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def find_static_file(root: Path, legacy_url: str | None) -> Path | None:
    if not legacy_url:
        return None
    name = Path(urlparse(legacy_url).path).name
    if not name:
        return None
    direct = root / name
    if direct.is_file():
        return direct
    return next(root.rglob(name), None)


def main() -> None:
    args = parse_args()
    source_url = os.environ.get("V1_DATABASE_URL")
    destination_url = os.environ.get("DATABASE_URL")
    bucket_name = os.environ.get("GCS_BUCKET")
    if not source_url or not destination_url or not bucket_name:
        raise SystemExit("V1_DATABASE_URL, DATABASE_URL, and GCS_BUCKET are required.")
    if args.apply and not args.owner_map and not args.preserve_owner_ids:
        raise SystemExit("--apply requires --owner-map or an explicit --preserve-owner-ids decision.")

    owner_map = json.loads(args.owner_map.read_text(encoding="utf-8")) if args.owner_map else {}

    source = create_engine(psycopg_url(source_url))
    destination = create_engine(psycopg_url(destination_url))
    bucket = storage.Client().bucket(bucket_name) if args.apply else None
    migrated = skipped = files = 0

    with source.connect() as source_connection, destination.begin() as destination_connection:
        rows = source_connection.execute(text("SELECT * FROM lesson ORDER BY created_at")).mappings()
        for row in rows:
            legacy_owner = row.get("user_id") or args.orphan_owner
            owner_id = owner_map.get(str(legacy_owner)) if owner_map else legacy_owner
            lesson_format = FORMAT_MAP.get(str(row.get("format")))
            if not owner_id or not lesson_format:
                skipped += 1
                continue
            lesson_id = stable_uuid(str(row["id"]))
            artifact = find_static_file(args.static_root, row.get("url"))
            object_key = None
            status = "failed"
            error_message = "Legacy output file was not found during migration."
            if artifact:
                object_key = f"lessons/{owner_id}/{lesson_id}/lesson{artifact.suffix.lower()}"
                status = "ready"
                error_message = None
                if bucket:
                    content_type = mimetypes.guess_type(artifact.name)[0] or "application/octet-stream"
                    blob = bucket.blob(object_key)
                    blob.content_disposition = "inline"
                    blob.cache_control = "private, max-age=300"
                    if artifact.suffix.lower() in {".html", ".htm"}:
                        blob.upload_from_string(
                            secure_html_document(artifact.read_text(encoding="utf-8")),
                            content_type=content_type,
                        )
                    else:
                        blob.upload_from_filename(artifact, content_type=content_type)
                    files += 1

            created_at = row.get("created_at") or datetime.now(timezone.utc)
            values = {
                "id": lesson_id,
                "owner_id": owner_id,
                "topic": row.get("topic") or "Untitled lesson",
                "format": lesson_format,
                "status": status,
                "summary": row.get("summary"),
                "source_code": row.get("code"),
                "object_key": object_key,
                "error_message": error_message,
                "created_at": created_at,
                "updated_at": created_at,
            }
            if args.apply:
                destination_connection.execute(
                    text("""
                        INSERT INTO lessons
                            (id, owner_id, topic, format, status, summary, source_code,
                             object_key, error_message, created_at, updated_at)
                        VALUES
                            (:id, :owner_id, :topic, :format, :status, :summary, :source_code,
                             :object_key, :error_message, :created_at, :updated_at)
                        ON CONFLICT (id) DO NOTHING
                    """),
                    values,
                )
            migrated += 1

        if not args.apply:
            destination_connection.rollback()

    mode = "applied" if args.apply else "dry-run"
    print(f"Migration {mode}: {migrated} rows eligible, {skipped} skipped, {files} files uploaded.")


if __name__ == "__main__":
    main()
