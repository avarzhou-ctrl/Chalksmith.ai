"""Dry-run-first idempotent lesson sync between two environments.

Reads SOURCE_DATABASE_URL/SOURCE_GCS_BUCKET/SOURCE_CLERK_SECRET_KEY and writes the
DATABASE_URL/GCS_BUCKET/CLERK_SECRET_KEY target. Re-running a synced pair is a no-op.
"""

import argparse
import hashlib
import os
from pathlib import PurePosixPath

import psycopg
from google.cloud import storage

from backend.scripts.migrate_v1_users import all_users, primary_email

COLUMNS = (
    "id", "owner_id", "root_lesson_id", "parent_lesson_id", "final_lesson_id",
    "version_number", "topic", "published_at",
    "format", "status", "summary", "source_code", "object_key", "error_message",
    "first_error", "raw_model_output", "edit_instruction", "created_at", "updated_at",
)
# owner_id and object_key are rewritten per environment, so they are compared separately.
COMPARED = tuple(name for name in COLUMNS if name not in {"owner_id", "object_key"})
TAG_COLUMNS = ("root_lesson_id", "owner_id", "normalized_value", "label", "created_at")
LIKE_COLUMNS = ("root_lesson_id", "owner_id", "created_at")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Write the planned changes.")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Also delete target lessons the source no longer has, making the sync a mirror.",
    )
    return parser.parse_args()


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def build_owner_map(source_key: str, target_key: str) -> dict[str, str]:
    targets = all_users(target_key)
    by_id = {user["id"]: user for user in targets}
    by_email = {primary_email(user): user for user in targets}
    mapping = {}
    for user in all_users(source_key):
        # external_id records the account a user was imported from, which is an exact
        # link; email carries the match when the sync runs in the other direction.
        target = by_id.get(user.get("external_id") or "") or by_email.get(primary_email(user))
        if target:
            mapping[user["id"]] = target["id"]
    return mapping


def read_lessons(url: str) -> dict[str, dict]:
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(COLUMNS)} FROM lessons")
        return {str(row[0]): dict(zip(COLUMNS, row)) for row in cursor.fetchall()}


def read_tags(url: str) -> dict[tuple[str, str], dict]:
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(TAG_COLUMNS)} FROM lesson_tags")
        return {
            (str(row[0]), row[2]): dict(zip(TAG_COLUMNS, row))
            for row in cursor.fetchall()
        }


def read_likes(url: str) -> dict[tuple[str, str], dict]:
    with psycopg.connect(url) as connection, connection.cursor() as cursor:
        cursor.execute(f"SELECT {', '.join(LIKE_COLUMNS)} FROM lesson_likes")
        return {
            (str(row[0]), row[1]): dict(zip(LIKE_COLUMNS, row))
            for row in cursor.fetchall()
        }


def target_key_for(row: dict, owner_id: str) -> str | None:
    if not row["object_key"]:
        return None
    return f"lessons/{owner_id}/{row['id']}/{PurePosixPath(row['object_key']).name}"


def copy_object(source_bucket, target_bucket, source_key: str, target_key: str) -> bool:
    source_blob = source_bucket.blob(source_key)
    target_blob = target_bucket.blob(target_key)
    if target_blob.exists():
        source_blob.reload()
        target_blob.reload()
        if target_blob.md5_hash == source_blob.md5_hash:
            return False
    source_bucket.copy_blob(source_blob, target_bucket, target_key)
    fresh = target_bucket.blob(target_key)
    fresh.content_disposition = "inline"
    fresh.cache_control = "private, max-age=300"
    fresh.patch()
    return True


def main() -> None:
    args = parse_args()
    source_url = required("SOURCE_DATABASE_URL")
    target_url = required("DATABASE_URL")
    owner_map = build_owner_map(required("SOURCE_CLERK_SECRET_KEY"), required("CLERK_SECRET_KEY"))

    source_rows = read_lessons(source_url)
    target_rows = read_lessons(target_url)
    source_tags = read_tags(source_url)
    target_tags = read_tags(target_url)
    source_likes = read_likes(source_url)
    target_likes = read_likes(target_url)
    client = storage.Client()
    source_bucket = client.bucket(required("SOURCE_GCS_BUCKET"))
    target_bucket = client.bucket(required("GCS_BUCKET"))

    unmapped = sorted({r["owner_id"] for r in source_rows.values() if r["owner_id"] not in owner_map})
    inserts, updates = [], []
    for lesson_id, row in source_rows.items():
        if row["owner_id"] not in owner_map:
            continue
        planned = dict(row)
        planned["owner_id"] = owner_map[row["owner_id"]]
        planned["object_key"] = target_key_for(row, planned["owner_id"])
        current = target_rows.get(lesson_id)
        if current is None:
            inserts.append((row, planned))
        elif (
            current["owner_id"] != planned["owner_id"]
            or current["object_key"] != planned["object_key"]
            or any(current[name] != planned[name] for name in COMPARED)
        ):
            updates.append((row, planned))

    prunable = [row for lesson_id, row in target_rows.items() if lesson_id not in source_rows]
    tag_inserts, tag_updates = [], []
    for key, row in source_tags.items():
        if row["owner_id"] not in owner_map:
            continue
        planned = dict(row)
        planned["owner_id"] = owner_map[row["owner_id"]]
        current = target_tags.get(key)
        if current is None:
            tag_inserts.append(planned)
        elif any(current[name] != planned[name] for name in TAG_COLUMNS):
            tag_updates.append(planned)
    prunable_tags = [row for key, row in target_tags.items() if key not in source_tags]
    like_inserts, like_updates = [], []
    planned_like_keys: set[tuple[str, str]] = set()
    for row in source_likes.values():
        if row["owner_id"] not in owner_map:
            continue
        planned = dict(row)
        planned["owner_id"] = owner_map[row["owner_id"]]
        key = (str(planned["root_lesson_id"]), planned["owner_id"])
        planned_like_keys.add(key)
        current = target_likes.get(key)
        if current is None:
            like_inserts.append(planned)
        elif current["created_at"] != planned["created_at"]:
            like_updates.append(planned)
    prunable_likes = [
        row for key, row in target_likes.items()
        if key not in planned_like_keys
    ]

    print(f"owners: {len(owner_map)} mapped" + (f", {len(unmapped)} unmapped (their lessons are skipped)" if unmapped else ""))
    for owner in unmapped:
        print(f"  unmapped source owner {owner}")
    print(f"lessons: {len(inserts)} to insert, {len(updates)} to update, {len(prunable)} to delete"
          + ("" if args.prune else " (pass --prune to delete)"))
    print(f"tags: {len(tag_inserts)} to insert, {len(tag_updates)} to update, {len(prunable_tags)} to delete"
          + ("" if args.prune else " (pass --prune to delete)"))
    print(f"likes: {len(like_inserts)} to insert, {len(like_updates)} to update, {len(prunable_likes)} to delete"
          + ("" if args.prune else " (pass --prune to delete)"))
    if not args.apply:
        print("\ndry-run: nothing written. Re-run with --apply.")
        return

    copied = 0
    for row, planned in inserts + updates:
        if planned["object_key"]:
            copied += copy_object(source_bucket, target_bucket, row["object_key"], planned["object_key"])

    columns = ", ".join(COLUMNS)
    placeholders = ", ".join(f"%({name})s" for name in COLUMNS)
    assignments = ", ".join(f"{name} = EXCLUDED.{name}" for name in COLUMNS if name != "id")
    with psycopg.connect(target_url) as connection, connection.cursor() as cursor:
        for _, planned in inserts + updates:
            cursor.execute(
                f"INSERT INTO lessons ({columns}) VALUES ({placeholders}) "
                f"ON CONFLICT (id) DO UPDATE SET {assignments}",
                planned,
            )
        tag_columns = ", ".join(TAG_COLUMNS)
        tag_placeholders = ", ".join(f"%({name})s" for name in TAG_COLUMNS)
        tag_assignments = ", ".join(
            f"{name} = EXCLUDED.{name}"
            for name in TAG_COLUMNS
            if name not in {"root_lesson_id", "normalized_value"}
        )
        for planned in tag_inserts + tag_updates:
            cursor.execute(
                f"INSERT INTO lesson_tags ({tag_columns}) VALUES ({tag_placeholders}) "
                f"ON CONFLICT (root_lesson_id, normalized_value) DO UPDATE SET {tag_assignments}",
                planned,
            )
        like_columns = ", ".join(LIKE_COLUMNS)
        like_placeholders = ", ".join(f"%({name})s" for name in LIKE_COLUMNS)
        for planned in like_inserts + like_updates:
            cursor.execute(
                f"INSERT INTO lesson_likes ({like_columns}) VALUES ({like_placeholders}) "
                "ON CONFLICT (root_lesson_id, owner_id) DO UPDATE SET "
                "created_at = EXCLUDED.created_at",
                planned,
            )
        pruned_objects = 0
        if args.prune:
            for row in prunable_likes:
                cursor.execute(
                    "DELETE FROM lesson_likes WHERE root_lesson_id = %s AND owner_id = %s",
                    (row["root_lesson_id"], row["owner_id"]),
                )
            for row in prunable_tags:
                cursor.execute(
                    "DELETE FROM lesson_tags WHERE root_lesson_id = %s AND normalized_value = %s",
                    (row["root_lesson_id"], row["normalized_value"]),
                )
        if args.prune and prunable:
            for row in prunable:
                if row["object_key"]:
                    blob = target_bucket.blob(row["object_key"])
                    if blob.exists():
                        blob.delete()
                        pruned_objects += 1
            cursor.execute(
                "DELETE FROM lessons WHERE id::text = ANY(%s)", ([str(r["id"]) for r in prunable],)
            )
        connection.commit()

    print(f"applied: {len(inserts)} inserted, {len(updates)} updated, "
          f"{len(prunable) if args.prune else 0} deleted, {copied} objects copied"
          + (f", {pruned_objects} objects deleted" if args.prune else "")
          + f"; tags: {len(tag_inserts)} inserted, {len(tag_updates)} updated, "
          f"{len(prunable_tags) if args.prune else 0} deleted"
          + f"; likes: {len(like_inserts)} inserted, {len(like_updates)} updated, "
          f"{len(prunable_likes) if args.prune else 0} deleted")


if __name__ == "__main__":
    main()
