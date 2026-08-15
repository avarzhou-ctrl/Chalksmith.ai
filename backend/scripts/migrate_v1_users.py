"""Dry-run-first import of v1 Clerk users, emitting an owner map for migrate_v1.

Clerk cannot move users between instances, so v1's ids cannot be kept; each
import records its old id in `external_id`, which the owner map joins on.
"""

import argparse
import csv
import json
import os
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from backend.scripts.migrate_v1 import psycopg_url


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create the missing users.")
    parser.add_argument("--owner-map", type=Path, default=Path("owner-map.json"))
    parser.add_argument(
        "--users-csv",
        type=Path,
        help="Clerk Dashboard user export. Required to carry passwords over, which the API cannot read.",
    )
    return parser.parse_args()


def call(key: str, path: str, method: str = "GET", body: dict | None = None):
    # Clerk's WAF rejects urllib's default User-Agent with a 403.
    request = urllib.request.Request(
        f"https://api.clerk.com/v1{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {key}",
            "User-Agent": "curl/8.7.1",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def all_users(key: str) -> list[dict]:
    users, offset = [], 0
    while True:
        page = call(key, f"/users?limit=100&offset={offset}")
        users += page
        if len(page) < 100:
            return users
        offset += 100


def primary_email(user: dict) -> str | None:
    addresses = user.get("email_addresses") or []
    for address in addresses:
        if address["id"] == user.get("primary_email_address_id"):
            return address["email_address"].lower()
    return addresses[0]["email_address"].lower() if addresses else None


def record(user_id: str, email: str, first: str, last: str, created: str, digest: str, hasher: str) -> dict:
    return {
        "id": user_id,
        "email": email.lower(),
        "first_name": first or None,
        "last_name": last or None,
        "created_at": created,
        "password_digest": digest or None,
        "password_hasher": hasher or None,
    }


def csv_users(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [
            record(
                row["id"],
                row["primary_email_address"] or row["verified_email_addresses"],
                row["first_name"],
                row["last_name"],
                row["created_at"],
                row["password_digest"],
                row["password_hasher"],
            )
            for row in csv.DictReader(handle)
            if row["primary_email_address"] or row["verified_email_addresses"]
        ]


def api_users(key: str) -> list[dict]:
    # The API never returns password digests, so these users import passwordless.
    return [
        record(
            user["id"],
            primary_email(user),
            user.get("first_name"),
            user.get("last_name"),
            datetime.fromtimestamp(user["created_at"] / 1000, UTC).isoformat().replace("+00:00", "Z"),
            "",
            "",
        )
        for user in all_users(key)
        if primary_email(user)
    ]


def import_body(user: dict) -> dict:
    body = {
        "email_address": [user["email"]],
        "external_id": user["id"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "created_at": user["created_at"],
    }
    # Without a digest the account has no password and signs in by OAuth or email code.
    if user["password_digest"]:
        body |= {"password_digest": user["password_digest"], "password_hasher": user["password_hasher"]}
    else:
        body["skip_password_requirement"] = True
    return body


def main() -> None:
    args = parse_args()
    source_key = os.environ.get("V1_CLERK_SECRET_KEY")
    target_key = os.environ.get("CLERK_SECRET_KEY")
    v1_database_url = os.environ.get("V1_DATABASE_URL")
    if not target_key or not v1_database_url:
        raise SystemExit("CLERK_SECRET_KEY and V1_DATABASE_URL are required.")
    if not args.users_csv and not source_key:
        raise SystemExit("Supply --users-csv or V1_CLERK_SECRET_KEY as the source of users.")

    source_users = csv_users(args.users_csv) if args.users_csv else api_users(source_key)
    target_by_email = {primary_email(u): u for u in all_users(target_key)}
    created = skipped = with_password = 0

    for user in sorted(source_users, key=lambda u: u["created_at"]):
        if user["email"] in target_by_email:
            skipped += 1
            continue
        if args.apply:
            target_by_email[user["email"]] = call(target_key, "/users", "POST", import_body(user))
        created += 1
        with_password += bool(user["password_digest"])

    v1 = create_engine(psycopg_url(v1_database_url))
    with v1.connect() as connection:
        emails = {
            str(row[0]): str(row[1]).lower()
            for row in connection.execute(text('SELECT id, email FROM "user"'))
        }
        owners = [str(row[0]) for row in connection.execute(text("SELECT DISTINCT user_id FROM lesson"))]

    owner_map, unmapped = {}, []
    for owner in owners:
        target = target_by_email.get(emails.get(owner, ""))
        if target:
            owner_map[owner] = target["id"]
        else:
            unmapped.append(owner)

    if args.apply:
        args.owner_map.write_text(json.dumps(owner_map, indent=1), encoding="utf-8")

    mode = "applied" if args.apply else "dry-run"
    print(
        f"Users {mode}: {created} to create ({with_password} with a migrated password), "
        f"{skipped} already present in the target instance."
    )
    print(f"Owner map: {len(owner_map)}/{len(owners)} lesson owners resolved -> {args.owner_map}")
    for owner in unmapped:
        print(f"  unmapped owner {owner} (v1 email {emails.get(owner, 'unknown')})")


if __name__ == "__main__":
    main()
