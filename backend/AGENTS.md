# AGENTS.md — Backend

Context for agents working inside `backend/`. The repository-wide rules (commit format,
boundaries) live in the root [AGENTS.md](../AGENTS.md) and the project history in
[CHANGELOG.md](../CHANGELOG.md); this file only covers
the Python service. Deployment details are in [GCP.md](../doc/GCP.md) and [README.md](../README.md);
the API contract and refactor rationale are in [REFACTOR.md](../doc/REFACTOR.md).

All paths below are written from the repository root, because every command and every Python
import (`backend.app.*`) resolves from there — never from inside `backend/`.

## Two runtimes, one package

| Runtime | Entry point | Deployed as | Executes generated code? |
| :--- | :--- | :--- | :--- |
| **API** | `backend/app/main.py` → `app` | public Cloud Run service | No |
| **Renderer** | `backend/app/renderer_main.py` → `renderer_app` | private Cloud Run service, callable only by the API service account | Yes — Manim only |

They share this package but not their images. `infra/docker/api.Dockerfile` installs
`--no-extra video`, so **Manim is not even importable in the API container**; the renderer image
installs `--extra video` plus Cairo/Pango/FFmpeg and sets `APP_ROLE=renderer`. This split is the
central security property of the backend: keep generated Python execution confined to
`renderer_main.py`.

## Directory map

```text
backend/
├── .python-version              # Local uv/pyenv default: Python 3.12
├── pyproject.toml               # Runtime dependencies and video extra
├── uv.lock                      # Locked Python dependency graph
├── app/
│   ├── main.py                  # Public API application factory
│   ├── renderer_main.py         # Private POST /internal/render/manim app
│   ├── api/                     # HTTP validation, delegation, serialization
│   │   ├── dependencies.py      # Request settings and renderer wiring
│   │   ├── generations.py       # POST /v2/generations SSE endpoint
│   │   ├── health.py            # Health check
│   │   ├── lessons.py           # Lesson CRUD, versions, and access URLs
│   │   └── schemas.py           # API Pydantic models, not ORM models
│   ├── core/
│   │   ├── config.py            # Frozen Settings, env loading, validation
│   │   ├── errors.py            # AppError and JSON exception handlers
│   │   └── logging.py           # JSON logs and request-id middleware
│   ├── db/
│   │   ├── lessons.py           # Owner-scoped lesson queries and mutations
│   │   ├── models.py            # Lesson SQLModel table
│   │   └── session.py           # Engine, sessions, schema creation, additive migration
│   ├── integrations/
│   │   ├── auth.py              # Clerk JWT verification and AuthUser
│   │   ├── storage.py           # GCS upload, delete, and signed URLs
│   │   └── llm/
│   │       ├── base.py          # Provider protocol, result, stream chunk, errors
│   │       ├── factory.py       # Provider selection
│   │       ├── gemini.py        # Vertex Gemini provider
│   │       ├── openai.py        # OpenAI Responses provider
│   │       └── deepseek.py      # DeepSeek chat-completions provider
│   └── lessons/                 # Lesson-generation domain
│       ├── generation.py        # GenerationService orchestration and SSE events
│       ├── sources.py           # PDF validation, extraction, prompt context
│       ├── formats/
│       │   ├── contracts.py     # Format requests, prepared results, strategy protocol
│       │   ├── code.py          # Code response parsing, prompts, shared code strategy
│       │   ├── registry.py      # Format-to-strategy selection
│       │   ├── slides/
│       │   │   ├── strategy.py  # Validated Spec → compiled Slides result
│       │   │   ├── prompt.py    # Kind-and-Block JSON generation prompt
│       │   │   ├── catalog.py   # LLM-facing Block capabilities and categories
│       │   │   ├── spec.py      # chalksmith.slides.v1 kinds, blocks, validators
│       │   │   ├── compiler.py  # Block composition → Reveal HTML
│       │   │   └── assets/v1/
│       │   ├── interactive/
│       │   │   ├── strategy.py  # Interactive code strategy
│       │   │   └── prompt.py    # p5.js code-generation rules
│       │   └── video/
│       │       ├── strategy.py  # Video code and repair strategy
│       │       └── prompt.py    # Manim code-generation rules
│       └── render/
│           ├── base.py          # Renderer protocol, asset, and RenderError
│           ├── html.py          # HTML validation, CSP, Reveal/KaTeX pinning
│           └── manim.py         # Local, remote, unavailable renderers and AST guard
├── scripts/
│   ├── init_db.py               # Create the current schema
│   ├── migrate_v1.py            # Dry-run-first v1 lesson migration
│   ├── migrate_v1_users.py      # Clerk v1 user mapping/import support
│   └── sync_lessons.py          # Idempotent cross-environment lesson sync
└── tests/
    ├── fixtures/
    │   └── lesson_specs/
    │       └── slides.json      # Representative valid Slides v1 Spec
    ├── test_v2_api.py           # HTTP, generation, storage, ownership tests
    └── test_v2_app.py           # Settings, providers, renderers, Specs, deadlines
```

Routine `__init__.py` files and generated `__pycache__/` directories are omitted from the map.

## Request flow: generation

`POST /v2/generations` (multipart form: `topic`, `format`, optional `base_lesson_id`,
`edit_instruction`, `sources[]`) is the only long-running endpoint.

1. `generations.py` authenticates, validates the form, sets
   `deadline = monotonic() + generation_timeout_seconds`, and extracts PDF text **before**
   opening the stream so upload errors are still ordinary HTTP errors.
2. `GenerationService.stream()` writes the `Lesson` row immediately with `status="generating"`,
   then yields Server-Sent Events:
   `started` → `progress` (`generating` → `validating` → `rendering` → [`repairing`] → `saving`)
   → `complete`, or `error`.
   Vertex Gemini is consumed as a model stream; progress events expose only the accumulated
   character count, while the service buffers the complete response before parsing or rendering.
   Providers without model streaming send a progress heartbeat every 10 seconds instead.
3. Every external await observes the shared deadline. One-shot stages use `self._await(...)`;
   model streaming re-derives the remaining time before each chunk/heartbeat wait. Add new
   awaits the same way, or a slow stage can outlive the request budget.
4. A format strategy parses the model output. Slides always use the strict `chalksmith.slides.v1`
   Kind-and-Block JSON specification and deterministic block-composition compiler; Interactive and
   Video still use `formats/code.py` parsing and the `---CODE_START---` contract. Historical Slides
   without a specification remain readable from their stored artifact but are intentionally
   read-only.
5. The renderer for the format runs in a `TemporaryDirectory`. Structured Slides get one bounded
   specification-repair attempt for JSON/schema/capacity errors. Video gets one code-repair
   attempt after `RenderError`; platform compiler/renderer defects are not sent to the model.
6. The output uploads to `lessons/{owner_id}/{lesson_id}/lesson.{ext}`; uploaded sources live at
   `sources/{owner_id}/{lesson_id}/{filename}`.

Failure handling worth preserving: once the stream has started the HTTP status is already 200, so
errors arrive **in-band** as an `error` event, the lesson row is flipped to `failed` with a
sanitized `_public_error()` message, and a partially written object is deleted. Client
disconnects (`CancelledError`/`GeneratedExit`) are recorded as `failed` too, not silently dropped.

## Data model and versioning

One table, `lessons`. An edit is a **new row**, not an update. Structured lessons store canonical
`lesson_spec` JSON plus `spec_version`, `runtime_version`, and `compiler_version`;
`source_code` is compiler output for those rows and remains the canonical legacy input otherwise.

- `root_lesson_id` — shared by every revision; a first-generation row points at itself.
- `parent_lesson_id` — the row that was edited.
- `version_number` — from `next_version_number()`, per root.

Consequences to respect:

- The dashboard list (`list_owned_lessons`) returns only rows where `id == root_lesson_id`.
  Version counts come from the single grouped query in `count_lesson_versions()` — do not
  reintroduce a per-lesson count loop.
- Rename (`PATCH`) rewrites `topic` on **all** versions of the root.
- Delete marks every version `deleting`, removes the source prefix and object from GCS, and only
  then deletes the rows — a ready row must never point at a missing file.

## Non-negotiable invariants

**Tenant isolation.** `owner_id` is the Clerk `sub` claim. Every read and write goes through the
owner-scoped helpers in `backend/app/db/lessons.py`; there is no unscoped lesson query anywhere,
and new ones must not appear. Missing-or-not-yours is always a 404 via `_owned_or_404()`.

**Generated code is never trusted.**
- `interactive`/`slides`: `HTMLRenderer` requires the marker (`p5` / `reveal`), rejects
  `eval(`/`document.write(`/`new Function(`, injects the CSP `<meta>` from
  `backend/app/lessons/render/html.py`, and pins Reveal.js to the three verified CDN URLs.
- Structured Slides contain no model-authored HTML, CSS, JavaScript, or SVG. The model returns
  validated semantic data and the platform compiler owns the complete document and embedded CSS.
- `video`: `validate_manim_code()` AST-walks the source against an import allowlist
  (`manim`, `math`, `numpy`, `random`), blocked builtins, dunder names, and blocked attributes,
  and requires a `GeneratedScene` class. The API only ever *sends* the code onward.
- `RemoteManimRenderer` attaches a Google OIDC ID token unless the target is localhost.
  With `MANIM_RENDERER_URL` unset the map gets `UnavailableManimRenderer`, which fails cleanly.

**Prompt injection.** `build_code_generation_prompt()` and structured format prompts fence
`REQUEST`, `SOURCES`, `EDIT_INSTRUCTION`, and prior code/specification as untrusted data with an
explicit instruction to ignore embedded rule changes. Keep that framing when editing prompts; also
keep repair diagnostics bounded to the last 4,000 characters.

**Error and log shape.** Client-facing failures raise `AppError(code=…, message=…, status_code=…)`
and always serialize as `{"error": {"code", "message", "details"?}}`. Messages are user-facing:
no stack traces, provider text, or SQL. Logs are JSON on stdout, and `JsonFormatter` copies only
the fields in its allow-list tuple — **a new `extra={...}` key is silently dropped unless you add
it there**. Owner identity is logged as `owner_id_hash` (`sha256(owner_id)[:16]`), never raw.

**Blocking work moves off the loop.** GCS calls, PyMuPDF extraction, and JWT/JWKS verification all
run under `asyncio.to_thread`, or inside a synchronous FastAPI route that FastAPI runs in its
threadpool. The Google Cloud, database, and PyJWT clients are synchronous. Non-streaming database
dependencies use `scope="function"`; generation alone keeps request scope because its SSE iterator
uses the session after the endpoint returns. Never hold a checked-out database connection across
an external-service await.

## Configuration

`Settings` in `backend/app/core/config.py` is a frozen `pydantic.BaseModel` (not `BaseSettings`)
built by `Settings.from_env()`, cached by `get_settings()`, and attached to `app.state.settings`.
Read it inside a request via `Depends(get_request_settings)` — not by calling `get_settings()`
again, which would ignore per-app overrides used by tests.

- Locally, values come from `.env/env.local` plus `.env/clerk.key.stg` at the repository root
  (gitignored and shared with other services). `bin/env.local.template` is the tracked runtime
  template; update it whenever you add a key.
- `validate_production_configuration()` fails startup when `APP_ENV=production` and a required key
  is missing, when origins/renderer URL are not HTTPS, or when Cloud SQL settings are incomplete.
  The renderer role is exempt. New required production settings belong in that validator.
- Adding a setting means touching the field, `from_env()`, `bin/env.local.template`, and, when
  deployed, `bin/env.deploy.template`/`bin/deploy.sh`; production-required values also belong in
  the validator.

Database URL resolution: explicit `DATABASE_URL` → Cloud SQL unix socket
(`postgresql+psycopg://…?host=/cloudsql/…`) → `sqlite:///./.env/chalksmith.local.db` for
`local`/`test` → `AppError` otherwise.

**There is no Alembic.** `create_db_and_tables()` runs `SQLModel.metadata.create_all()` plus the
hand-written additive step `_migrate_lesson_versions()`. A new column on `Lesson` also needs an
entry there, or existing local and deployed databases will not gain it.

## Commands

```bash
# Install (video extra = Manim, needed only for the renderer process)
uv sync --project backend --extra video

# Renderer, terminal 1
uv run --project backend uvicorn backend.app.renderer_main:renderer_app --reload --port 8081

# API, terminal 2
uv run --project backend uvicorn backend.app.main:app --reload --port 8000

# Tests (stdlib unittest — pytest is not a dependency)
uv run --project backend python -m unittest discover -s backend/tests

# Lockfile check, run before opening a PR
uv lock --project backend --check
```

`http://localhost:8000/docs` for the OpenAPI explorer; `/healthz` on both ports. Every API
response carries `X-Request-Id`, which matches the `request_id` field in the structured logs.

## Testing conventions

- `unittest` only, in two files: `test_v2_api.py` (HTTP behavior through `TestClient`) and
  `test_v2_app.py` (settings, auth, storage, renderer sandboxing, deadlines).
- Build an isolated app with `create_app(Settings(app_env="test", database_url="sqlite://", …))`
  and replace collaborators through `app.dependency_overrides` for `get_current_user`,
  `get_llm_provider`, `get_storage`, and `get_renderers`. `FakeLLM`/`FakeStorage` in
  `test_v2_api.py` are the reference doubles.
- `sqlite://` is in-memory and pinned to `StaticPool` by `create_database_engine`, so the whole
  test app shares one connection.
- No network, no real GCP calls, no Manim subprocess in the suite.
- Security-relevant behavior gets a test: sandbox rejections, tenant isolation, upload limits,
  and asset pinning all already have one — follow that precedent for new rules.

## Editing notes

- Layering: routers validate and serialize, `lessons/` owns the workflow and format behavior,
  `db/` owns queries, and `integrations/` owns vendor boundaries. Do not query the database from a
  router body or call GCS from `db/`.
- `integrations/llm/base.py` and `lessons/render/base.py` are `Protocol`s. A new provider or renderer
  implements the protocol and is wired in `llm/factory.py` or `api/dependencies.py`; nothing else
  should need to change.
- Adding a lesson format means: add the `LessonFormat` literal in `api/schemas.py`, colocate its
  strategy and prompt under `lessons/formats/<format>/`, register it in `formats/registry.py`, and
  wire its renderer in `api/dependencies.py`. Declarative formats also colocate their Spec, compiler,
  and versioned assets there. Code formats reuse the envelope and parser in `formats/code.py`;
  shared renderer implementations stay under `lessons/render/`.
- Comments explain *why*, not *what*, and stay sparse — match the existing density.
- Do not add dependencies without approval; `pyproject.toml` pins the API surface deliberately and
  `uv.lock` is checked in CI.
- Never commit credentials. Secrets live in `.env/` locally and Secret Manager in deployment.
