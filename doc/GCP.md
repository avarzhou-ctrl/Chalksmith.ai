# Google Cloud Platform (GCP) Configuration

This is the setup guide for Chalksmith's Google Cloud resources in project `${your-project-id}`. It records the chosen configuration, not the reasoning behind it: authentication is managed separately by Clerk in [CLERK.md](CLERK.md), and sizing and spend are in [COST.md](COST.md).

Never commit service-account JSON files, database passwords, or provider secrets. Local runtime configuration belongs in the ignored root `.env/` directory. Production uses Cloud Run service identities and Secret Manager.

## Resource overview

| Resource | Purpose | Local development | Staging | Production |
| :--- | :--- | :--- | :--- | :--- | 
| Vertex AI | Gemini lesson generation | Application Default Credentials | Cloud Run API service account | Cloud Run API service account |
| Cloud Storage (GCS) | Private PDFs, HTML, and MP4 artifacts | `chalksmith-gcs-stg` | `chalksmith-gcs-stg` | `chalksmith-gcs-prod` |
| Cloud SQL (PostgreSQL16) | Lesson metadata and source code | `chalksmith-postgres-stg` | `chalksmith-postgres-stg` | `chalksmith-postgres-prod`|
| Cloud Run | Next.js web, FastAPI API, isolated Manim renderer | 3 local processes | Required | Required |
| Secret Manager | Database password, Clerk server key, etc. | `chalksmith-db-password-stg` <br> `chalksmith-clerk-key-stg` | <nobr> `chalksmith-db-password-stg` <br> `chalksmith-clerk-key-stg` | <nobr> `chalksmith-db-password-prod` <br> `chalksmith-clerk-key-prod` |
| Cloud Build | Container image storage and builds | Not used | Required | Required |

Vertex AI uses Google credentials and does not use a Gemini Developer API key in this architecture.

## Current project values

| Setting | Value |
| :--- | :--- |
| Project ID | `your-project-id` |
| Default deployment region | `us-central1` |
| Vertex AI location | `global` |
| Vertex AI model | `gemini-3.6-flash` |
| Signing service account | `chalksmith-api@your-project-id.iam.gserviceaccount.com` |

Model availability can change. If the configured model becomes unavailable, choose a Vertex AI model supported in the selected location and update `LLM_MODEL`.

## 1. Prepare roles, APIs and service accounts

 `bin/prepare.sh` prepares all prerequisites discussed in this section. Run it once per project, as the human deployment account (reruns skip prerequisites that are already satisfied):

```bash
gcloud auth login

./bin/prepare.sh --project=your-project-id ...
```

### 1.1 Assign roles to human account

The project `${your-project-id}` must have billing enabled, and is managed by a **human account**, `teammate@example.com`. This **human account** should be granted following roles within the project-level scope (`${your-project-id}`): `X` marks where each role is required. 

| Required role | Purpose | Local | Staging/Production |
| :--- | :--- | :---: | :---: |
| `roles/serviceusage.serviceUsageAdmin` | Enable the APIs listed below. | X | X |
| `roles/iam.serviceAccountAdmin` | Create the local, deployment, and build service accounts and set IAM policy on them. `roles/iam.serviceAccountCreator` is not enough; it omits `iam.serviceAccounts.setIamPolicy`. | X | X |
| `roles/resourcemanager.projectIamAdmin` | Grant project-level roles to those service accounts. | X | X |
| `roles/storage.admin` | Create and configure the development bucket. | X | X |
| `roles/iam.serviceAccountTokenCreator` | Act as the deployment account. Without it the human account can create that account and grant it roles, but cannot run a single command as it. |  | X |
| `roles/cloudsql.client` | Connect to the shared staging instance through the proxy and read its state ([Section 3.1.1](#311-connect-to-database-and-verify-gcp-access)). Starting and stopping it is `bin/setup.sh`, which impersonates the deployment account. | X |  |
| `roles/secretmanager.secretAccessor` | Read the staging database password when running the proxy or a migration locally. | X |  |

The human account needs no Cloud Run, Artifact Registry, or Cloud Build role. Those belong to the deployment service account in [Section 1.3](#13-prepare-service-accounts).

### 1.2 Enable required APIs for the project

Enable the required APIs for `${your-project-id}`:

| API name | Local | Production |
| :--- | :---: | :---: |
| `aiplatform.googleapis.com` | X | X |
| `storage.googleapis.com` | X | X |
| `iamcredentials.googleapis.com` | X | X |
| `sqladmin.googleapis.com` | X | X |
| `secretmanager.googleapis.com` | X | X |
| `artifactregistry.googleapis.com` |  | X |
| `cloudbuild.googleapis.com` |  | X |
| `run.googleapis.com` |  | X |

```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com iamcredentials.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com --project=your-project-id
```

Organization policies are evaluated above project IAM, so a project owner cannot override one inherited from the organization or folder. If a policy restricts allowed services, an organization-policy administrator must [allow these APIs first](https://console.cloud.google.com/iam-admin/orgpolicies/list).

Enable `orgpolicy.googleapis.com` as well to inspect the two constraints that decide whether a deployment can succeed at all:

| Constraint | Effect when enforced |
| :--- | :--- |
| `constraints/iam.allowedPolicyMemberDomains` | Blocks the public `allUsers` binding that the web and API services are deployed with. |
| `constraints/cloudbuild.disableCreateDefaultServiceAccount` | No default Cloud Build service account exists, so builds must name an explicit build account ([Section 1.3](#13-prepare-service-accounts)). |

```bash
gcloud org-policies describe constraints/iam.allowedPolicyMemberDomains \
  --project=your-project-id --effective
```

### 1.3 Prepare service accounts

Two types of service accounts (SA) serve both local and staging/production environments.
- `chalksmith-deployer`: **Deployment and build identity**. `chalksmith-deployer` holds `roles/serviceusage.serviceUsageAdmin`, `roles/resourcemanager.projectIamAdmin`, `roles/iam.serviceAccountAdmin`, `roles/iam.serviceAccountUser`, `roles/artifactregistry.admin`, `roles/storage.admin`, `roles/secretmanager.admin`, `roles/cloudsql.admin`, `roles/cloudbuild.builds.editor`, `roles/run.admin`, and `roles/logging.logWriter`. It is also the Cloud Build build account, which is where the last of those is spent: a build that names its own service account must write its own logs.
- `chalksmith-web`/`chalksmith-api`/`chalksmith-renderer`: Three **runtime Cloud Run** services accounts. Because the runtime accounts are shared, a binding made for one environment persists alongside the other's, so `chalksmith-api` ends up with object admin on both buckets and accessor on both database secrets. Give each environment its own runtime accounts if that boundary matters more than the shared setup does.

| Service account | Role | Required access |
| :--- | :--- | :--- |
| `chalksmith-web` | public Next.js service; reads only the Clerk server secret | Secret accessor for the environment's Clerk server key |
| `chalksmith-api` | public-network FastAPI service; every application route verifies a Clerk JWT | Vertex AI User, Cloud SQL Client, bucket object admin, URL signing, database password, optional OpenAI key, renderer invoker |
| <nobr>`chalksmith-renderer` | private Manim service; only `chalksmith-api` may invoke it | No project data, model, or secret roles |

Generated Python therefore executes in a container that cannot access the database, bucket, LLM, or secrets.

Deploy through impersonation rather than a downloaded key:

```bash
gcloud config set auth/impersonate_service_account \
  chalksmith-deployer@your-project-id.iam.gserviceaccount.com
./bin/deploy.sh --type=stg start
gcloud config unset auth/impersonate_service_account
```

## 2. Deploy GCS buckets, database and secrets in GCP

Both local and staging/production environments share one set of service accounts described in [Section 1.3](#13-prepare-service-accounts).

Every other resource is suffixed: `-stg` for staging, `-prod` for production. Local debugging shares buckets and database with the staging environment.

| Resource | Local | Staging | Production |
| :--- | :--- | :--- | :--- |
| GCS bucket | `chalksmith-gcs-stg` | `chalksmith-gcs-stg` | `chalksmith-gcs-prod` |
| Cloud SQL instance | `chalksmith-postgres-stg` | `chalksmith-postgres-stg` | `chalksmith-postgres-prod` |
| Secrets | `chalksmith-db-password-stg` <br> `chalksmith-clerk-key-stg` | `chalksmith-db-password-stg` <br> `chalksmith-clerk-key-stg` | `chalksmith-db-password-prod` <br> `chalksmith-clerk-key-prod` |

`bin/setup.sh local|stg|prod start|shutdown` implements all requirements discussed in this section. 
- `start`: skips satisfied requirements and creates only the ones needed, then leaves the database running; `local` is an alias for the staging resources.
- `shutdown`: stops the database instance but keeps secrets, buckets, and data for the next run.

### 2.1 Setup environment secrets

Each environment needs its own database password and Clerk server key, and its own keys for other services such as OpenAI (when `LLM_PROVIDER=openai`). Staging uses the Clerk development instance; production uses the production instance. See [CLERK.md](CLERK.md).

```bash
for secret in chalksmith-db-password-stg chalksmith-clerk-key-stg; do
  gcloud secrets create "${secret}" \
    --project="${your-project-id}" \
    --replication-policy=automatic
  gcloud secrets versions add "${secret}" \
    --project="${your-project-id}" \
    --data-file="${clerk-key-file}"
done
```

### 2.2 Create GCS buckets

One private regional bucket per environment. Local debugging writes into the staging bucket.

| Setting | Value | Reason |
| :--- | :--- | :--- |
| Location | `us-central1` | Same region as Cloud Run; artifact reads stay in-region |
| Uniform bucket-level access | Enabled | Object ACLs are disabled, so IAM is the only access path |
| Public access prevention | Enforced | Rejects an `allUsers` binding even if one is added later |
| Lifecycle | Delete `sources/` after 7 days; abort incomplete multipart uploads after 1 day | Uploads are generation inputs, not durable data |

Object layout:

| Key | Content | Lifetime |
| :--- | :--- | :--- |
| `sources/{owner_id}/{lesson_id}/{filename}` | Uploaded PDFs and images | 7 days, by lifecycle rule |
| `lessons/{owner_id}/{lesson_id}/lesson.{html,mp4,py}` | Generated artifacts | Until the lesson is deleted |

Nothing is served publicly. The API hands the browser V4 signed URLs valid for `SIGNED_URL_TTL_SECONDS` (900 by default), produced by `chalksmith-api` calling `signBlob` on itself through `iamcredentials.googleapis.com`. That is why the API account holds `roles/iam.serviceAccountTokenCreator` on its own account and why no JSON key is needed anywhere.

```bash
gcloud storage buckets create gs://chalksmith-gcs-stg \
  --project=your-project-id --location=us-central1 \
  --uniform-bucket-level-access --public-access-prevention

gcloud storage buckets update gs://chalksmith-gcs-stg \
  --lifecycle-file=bin/storage-lifecycle.json

gcloud storage buckets add-iam-policy-binding gs://chalksmith-gcs-stg \
  --member=serviceAccount:chalksmith-api@your-project-id.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

`bin/storage-lifecycle.json`:

```json
{
  "rule": [
    { "action": { "type": "Delete" },
      "condition": { "age": 7, "matchesPrefix": ["sources/"] } },
    { "action": { "type": "AbortIncompleteMultipartUpload" },
      "condition": { "age": 1 } }
  ]
}
```

`chalksmith-web` and `chalksmith-renderer` get no bucket binding at all: the browser reaches artifacts only through signed URLs issued by the API, and the renderer receives its input and returns its output over HTTP.

### 2.3 Database initialization and v1 migration

Start/stop database instances, if needed, create the instance, database, and user. 

`bin/setup.sh local|stg|prod start` brings up the Cloud SQL database, while `shutdown` turns down the database service. If the database is already running, just skip `start`.

| Setting | Value |
| :--- | :--- |
| Database version | `POSTGRES_16` |
| Edition / tier | `ENTERPRISE` / `db-f1-micro` |
| Storage | 10 GB SSD, auto-increase |
| Availability | `ZONAL` |
| Backups | Staging: off. Production: 7 retained, PITR on |
| Database / user | `chalksmith` / `chalksmith` |

`--edition` must be passed explicitly: `db-f1-micro` exists only in the Enterprise edition, and a project whose default is Enterprise Plus rejects it. Sizing rationale and the monthly cost model are in [COST.md](COST.md).

```bash
# Staging: no backups, stopped when idle.
gcloud sql instances create chalksmith-postgres-stg \
  --project=your-project-id --region=us-central1 \
  --database-version=POSTGRES_16 --edition=ENTERPRISE --tier=db-f1-micro \
  --availability-type=ZONAL \
  --storage-type=SSD --storage-size=10 --storage-auto-increase \
  --no-backup

gcloud sql databases create chalksmith --instance=chalksmith-postgres-stg
gcloud sql users create chalksmith --instance=chalksmith-postgres-stg \
  --password="$(gcloud secrets versions access latest --secret=chalksmith-db-password-stg)"

# Left running so debug.sh and deploy.sh can be repeated; stop it when done.
gcloud sql instances patch chalksmith-postgres-stg --activation-policy=ALWAYS

# Production: same machine, but backed up and never stopped.
gcloud sql instances create chalksmith-postgres-prod \
  --project=your-project-id --region=us-central1 \
  --database-version=POSTGRES_16 --edition=ENTERPRISE --tier=db-f1-micro \
  --availability-type=ZONAL \
  --storage-type=SSD --storage-size=10 --storage-auto-increase \
  --backup-start-time=08:00 --retained-backups-count=7 \
  --enable-point-in-time-recovery
```

Shared-core carries no SLA, and `ZONAL` availability means a zone outage is an outage.

`max_connections` on this tier is derived from 0.6 GB of memory and is small; read it with `SELECT * FROM pg_settings WHERE name = 'max_connections'`. Build the engine with `pool_size=2, max_overflow=0` and cap the API at 2 instances ([Section 3.2](#32-staging-and-production-deployment)) — SQLAlchemy's defaults of 5 pooled plus 10 overflow per process would let an API at `--max 5` demand 75 connections.

The v2 schema is created by `create_db_and_tables()` during API startup unless `AUTO_CREATE_TABLES=false`, so a fresh environment needs no explicit schema step. Run the scripts below only to initialize without starting the API, or to import v1 data. Both resolve the connection the same way the API does, so the instance must be running and reachable — from a workstation that means the proxy in [Section 3.1.1](#311-start-cloud-sql-and-verify-gcp-access).

```bash
# Schema only.
uv run --project backend python -m backend.scripts.init_db

# v1 to v2 import: report first, then apply.
uv run --project backend python -m backend.scripts.migrate_v1 \
  --preserve-owner-ids --static-root ../chalksmith-v1/backend/static
uv run --project backend python -m backend.scripts.migrate_v1 \
  --preserve-owner-ids --static-root ../chalksmith-v1/backend/static --apply
```

`migrate_v1` reads the legacy rows and the v1 `static/` tree, writes v2 rows, and uploads the artifacts it finds to `GCS_BUCKET`. Without `--apply` it writes nothing. `--preserve-owner-ids` keeps the v1 Clerk `sub` values and is correct whenever the same Clerk application is reused; supply `--owner-map` when it is not, and `--orphan-owner` for legacy rows that carry no user id ([CLERK.md](CLERK.md)).

## 3. Start the Chalksmith.AI Services

### 3.1 Local debugging

The content in this section is implemented in `bin/debug.sh`.

```bash
# "start" for the proxy and the three local processes
# "shutdown" for those four only; the database keeps running for the next session
./bin/debug.sh start|shutdown
```

#### 3.1.1 Connect to database and verify GCP access

Local processes have no `/cloudsql` unix socket, so they reach the staging instance through the Cloud SQL Auth Proxy listening on `127.0.0.1:5432`.

ADC is a separate credential from `gcloud auth login`; run `gcloud auth application-default login` once if the Python check prints no project. Stopping the instance is `bin/setup.sh stg shutdown`, not part of `bin/debug.sh shutdown`.

```bash
# Cloud SQL access through the proxy
cloud-sql-proxy your-project-id:us-central1:chalksmith-postgres-stg --port 5432 &
psql "postgresql://chalksmith:$(gcloud secrets versions access latest \
  --secret=chalksmith-db-password-stg)@127.0.0.1:5432/chalksmith" -c '\dt'

# Application Default Credentials (ADC) and bucket access
uv run --project backend python -c \
  "import google.auth; c, p = google.auth.default(); print(p, getattr(c, 'service_account_email', type(c).__name__))"
gcloud storage ls gs://chalksmith-gcs-stg
```

#### 3.1.2 Configure local runtime

Both runtimes read the same two files from the ignored `.env/` directory:
`env.local` for service configuration and `clerk.key.stg` for the Clerk instance (documented in [CLERK.md](CLERK.md)).

Values are literal; neither file is expanded by a shell, so `${...}` placeholders must be substituted before saving. Real environment variables win over both files, which is how a single file serves two processes with different roles.

`.env/env.local`:

```dotenv
APP_ENV=local
APP_ROLE=api
FRONTEND_ORIGINS=http://localhost:3000

GCP_PROJECT_ID=your-project-id

LLM_PROVIDER=vertex
LLM_MODEL=gemini-3.6-flash
VERTEX_AI_LOCATION=global

# Staging Cloud SQL through the local proxy from Section 3.1.1.
# Percent-encode the password; a value holding '/', '+', or '=' silently truncates the URL.
DATABASE_URL=postgresql://chalksmith:<url-encoded-password>@127.0.0.1:5432/chalksmith

GCS_BUCKET=chalksmith-gcs-stg
GCS_SIGNER_SERVICE_ACCOUNT=chalksmith-api@your-project-id.iam.gserviceaccount.com
MANIM_RENDERER_URL=http://localhost:8081

NEXT_PUBLIC_API_URL=http://localhost:8000
```

- Clerk settings (`CLERK_ISSUER`, `CLERK_JWKS_URL`, `CLERK_AUDIENCE`, `CLERK_AUTHORIZED_PARTIES`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`) belong in `.env/clerk.key.stg` only.
- The renderer process reads the same file but must override the role: `APP_ROLE=renderer uv run ...`.
- `CLOUD_SQL_INSTANCE`, `DATABASE_NAME`, `DATABASE_USER`, and `DATABASE_PASSWORD` are the deployed alternative to `DATABASE_URL` and are unused locally.
- `LLM_PROVIDER=openai` replaces the three Vertex settings with `OPENAI_API_KEY`.
- `APP_ENV=local` skips the strict startup validation, so an omitted variable silently takes its default rather than failing. Defaults that matter: `SIGNED_URL_TTL_SECONDS=900`, `GENERATION_TIMEOUT_SECONDS=900`, `MANIM_TIMEOUT_SECONDS=600`, `LLM_TIMEOUT_SECONDS=120`, `LLM_MAX_OUTPUT_TOKENS=16384`, `MAX_SOURCE_FILES=5`, `MAX_SOURCE_BYTES=10000000`, `AUTO_CREATE_TABLES=true`.

#### 3.1.3 Start three local debugging processes

Run every command from the repository root in a separate terminal.

```bash
# Terminal 1 — private renderer equivalent on port 8081:
uv run --project backend uvicorn backend.app.renderer_main:renderer_app --reload --port 8081

# Terminal 2 — public API on port 8000:
uv run --project backend uvicorn backend.app.main:app --reload --port 8000

# Terminal 3 — Next.js on port 3000:
npm --prefix frontend run dev
```

After that, verify and debug using following URLs

| URL | Purpose |
| :--- | :--- |
| `http://localhost:3000` | Web application |
| `http://localhost:8000/docs` | FastAPI OpenAPI explorer |
| `http://localhost:8000/healthz` | API health check |
| `http://localhost:8081/healthz` | Renderer health check |


### 3.2 Staging and production deployment

The content in this section is implemented in `bin/deploy.sh`.

```bash
# "start" builds the images and deploys the three Cloud Run services
# "shutdown" deletes those three services; the database is stopped by setup.sh
./bin/deploy.sh --type=stg|prod start|shutdown
```

`shutdown` is a staging affordance. Production is a live service: it stays up, and `--type=prod shutdown` takes the product offline, so it demands an explicit confirmation unless `--yes` is passed.

| Resource | Staging | Production |
| :--- | :--- | :--- |
| Artifact Registry | `chalksmith-stg` | `chalksmith-prod` |
| Cloud Run services | `chalksmith-{api,web,renderer}-stg` | `chalksmith-{api,web,renderer}-prod` |

Export before `start`; the Clerk values come from [CLERK.md](CLERK.md), and staging uses the development instance while production uses the production one:

```bash
export PROJECT_ID=your-project-id REGION=us-central1
export LLM_PROVIDER=vertex LLM_MODEL=gemini-3.6-flash
export CLERK_PUBLISHABLE_KEY=pk_... CLERK_ISSUER=https://<instance>.clerk.accounts.dev
```

Two dependencies fix the order: the API needs the renderer URL, and the web image needs the API URL.

| Step | Action |
| :--- | :--- |
| 1 | Confirm the runtime service accounts and the Cloud SQL instance exist; create the Artifact Registry repository and attach its cleanup policy. Anything missing aborts the run rather than being created here. |
| 2 | Confirm the Cloud SQL instance is running and abort if it is not; `bin/setup.sh` starts it. Bucket and secret bindings were granted there too, alongside the resources themselves, so only the optional OpenAI secret is bound here. |
| 3 | Build the api and renderer images with Cloud Build. The build names `chalksmith-deployer` as its service account because the organization policy in [Section 1.2](#12-enable-required-apis-for-the-project) leaves no default build account. |
| 4 | Deploy the renderer with `--no-allow-unauthenticated`, then grant `chalksmith-api` `roles/run.invoker` on it. |
| 5 | Deploy the API with `--allow-unauthenticated`, `--add-cloudsql-instances`, the renderer URL from step 4, and Secret Manager mounts for `DATABASE_PASSWORD` (plus `OPENAI_API_KEY` when `LLM_PROVIDER=openai`). |
| 6 | Build the web image with the API URL and the Clerk publishable key compiled in, then deploy it. |
| 7 | Rewrite the API's `FRONTEND_ORIGINS` and `CLERK_AUTHORIZED_PARTIES` with the real web URL. |

Step 5 runs before the web hostname exists, so both origin variables start at a placeholder and step 7 corrects them. The placeholder is an `https://` URL rather than an empty string because startup validation rejects non-HTTPS origins. Staging deploys with `APP_ENV=production` as well, so it exercises the same validation path as production.

| Service | Ingress | CPU / memory | Concurrency | Timeout | Scale |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `chalksmith-web-*` | Public | 1 / 512Mi | 40 | 60s | 0–2 |
| `chalksmith-api-*` | Public | 1 / 1Gi | 8 | 900s | 0–2 |
| `chalksmith-renderer-*` | `chalksmith-api` only | 2 / 2Gi | 1 | 900s | 0–2 |

Renderer concurrency is 1: a Manim render occupies the container's CPU for the whole job. The API is capped at 2 instances to stay within the database connection limit ([Section 2.3](#23-database-initialization-and-v1-migration)).

All three services deploy at `--min 0` on request-based billing, including production. Do not pass `--no-cpu-throttling` or switch a service to instance-based billing; the sizing rationale is in [COST.md](COST.md). One constraint is not about cost: request-based billing throttles CPU once the response is sent, so generation must keep holding the request open for its full duration rather than returning early and continuing in the background.

Attach an Artifact Registry cleanup policy retaining the most recent few tags per repository. Every deploy pushes a git-SHA-tagged image, and the renderer image carries a full LaTeX and ffmpeg toolchain.

After `start`:

1. Add the printed web URL to that Clerk instance's allowed URLs. Sign-in is rejected by Clerk until this is done, and it cannot be scripted from here.
2. Use the URL the script printed. Cloud Run answers each service on two hostnames, the legacy `-<hash>-uc.a.run.app` form and the newer `-<project-number>.<region>.run.app` form; only the first is written into `FRONTEND_ORIGINS` and the Clerk authorized parties, so the other fails CORS and Clerk verification. `gcloud run services list` reports the newer form.
3. Verify the API through `/docs` or any `/v2/...` route, which answers `401` without a token. `/healthz` is answered upstream of the container on `*.run.app` and is not a usable deployment check.

`shutdown` deletes the three Cloud Run services and nothing else; images, buckets, secrets, and data all survive, which makes `start` repeatable. Stopping the database is `bin/setup.sh <env> shutdown`, so a `start` between sessions costs no instance boot. Each `start` prints the web URL again — confirm it still matches the Clerk allowed URLs.

Logs are structured JSON on stdout, collected by Cloud Logging. Every API response carries an `X-Request-Id` header matching `jsonPayload.request_id`, and user identity appears only as `owner_id_hash`.

```bash
gcloud beta run services logs tail chalksmith-api-stg \
  --region=us-central1 --project=your-project-id
```

## References

- [Vertex AI SDK authentication](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Cloud Storage IAM roles](https://cloud.google.com/storage/docs/access-control/iam-roles)
- [Cloud Run service identity](https://cloud.google.com/run/docs/securing/service-identity)
- [Cloud SQL Python connector and Cloud Run](https://cloud.google.com/sql/docs/postgres/connect-run)
- [Cloud SQL editions and machine types](https://cloud.google.com/sql/docs/postgres/editions-intro)
- [Cloud SQL connection limits](https://cloud.google.com/sql/docs/postgres/manage-connections)
- [Secret Manager access control](https://cloud.google.com/secret-manager/docs/access-control)
