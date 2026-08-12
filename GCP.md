# Google Cloud Platform Configuration

This is the single setup guide for Chalksmith's Google Cloud resources in project `your-project-id`. Authentication is managed separately by Clerk; see [CLERK.md](CLERK.md).

Never commit service-account JSON files, database passwords, or provider secrets. Local runtime configuration belongs in the ignored root `.env/` directory. Production uses Cloud Run service identities and Secret Manager.

## Resource overview

| Resource | Purpose | Local development | Production |
| :--- | :--- | :--- | :--- |
| Vertex AI | Gemini lesson generation | Service-account JSON through Application Default Credentials (ADC) | Cloud Run API service account |
| Cloud Storage (GCS) | Private PDFs, HTML, and MP4 artifacts | <nobr>`your-project-id-chalksmith-dev` | <nobr>`your-project-id-chalksmith-prod` |
| SQLite / Cloud SQL | Lesson metadata and source code | `.env/chalksmith.local.db` | PostgreSQL 16 in Cloud SQL |
| Cloud Run | Next.js web, FastAPI API, isolated Manim renderer | Three local processes replace it | Required |
| Secret Manager | Database password, Clerk server key, optional OpenAI key | Not used | Required |
| Artifact Registry / Cloud Build | Container image storage and builds | Not used | Required |

Vertex AI uses Google credentials and does not use a Gemini Developer API key in this architecture.

## Current project values

| Setting | Value |
| :--- | :--- |
| Project ID | `your-project-id` |
| Default deployment region | `us-central1` |
| Vertex AI location | `global` |
| Vertex AI model | `gemini-3.6-flash` |
| GCP service account | `your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com` |
| Local credential (devlopment ONLY) | `.env/your-project-id-local.json` |
| GCS bucket (devlopment ONLY) | `your-project-id-chalksmith-dev` |

Model availability can change. If the configured model becomes unavailable, choose a Vertex AI model supported in the selected location and update `LLM_MODEL`.

## Project prerequisites

The project must have billing enabled. The following project-level IAM roles are for the **human account** or **CI/CD deployment identity** that performs setup; they are separate from the application runtime service accounts in [Section 2.1](#21-production-architecture-and-service-accounts). `X` marks where each role is required, scope is within `your-project-id`.

| Required role | Purpose | API | Local | Production |
| :--- | :--- | :--- | :---: | :---: |
| `roles/serviceusage.serviceUsageAdmin` | Enable required Google Cloud APIs. | Service Usage | X | X |
| `roles/iam.serviceAccountCreator` | Create local or Cloud Run service accounts. | IAM | X | X |
| `roles/resourcemanager.projectIamAdmin` | Grant project-level roles to service accounts. | Cloud Resource Manager | X | X |
| `roles/storage.admin` | Create and configure development or production GCS buckets. | Cloud Storage | X | X |
| `roles/run.admin` | Deploy and configure Cloud Run services. | Cloud Run |  | X |
| `roles/cloudbuild.builds.editor` | Submit container-image builds. | Cloud Build |  | X |
| `roles/artifactregistry.admin` | Create and manage the container registry. | Artifact Registry |  | X |
| `roles/cloudsql.admin` | Create and configure Cloud SQL. | Cloud SQL Admin |  | X |
| `roles/secretmanager.admin` | Create secrets and grant runtime access. | Secret Manager |  | X |
| `roles/iam.serviceAccountUser` | Deploy Cloud Run services with their runtime identities. | IAM |  | X |

An administrator can replace these broad predefined roles with narrower custom roles, provided every required command remains allowed.

Enable the required APIs for `your-project-id`:

| API name | Local | Production |
| :--- | :---: | :---: |
| `aiplatform.googleapis.com` | X | X |
| `storage.googleapis.com` | X | X |
| `iamcredentials.googleapis.com` | X | X |
| `artifactregistry.googleapis.com` |  | X |
| `cloudbuild.googleapis.com` |  | X |
| `run.googleapis.com` |  | X |
| `sqladmin.googleapis.com` |  | X |
| `secretmanager.googleapis.com` |  | X |

```bash
gcloud services enable aiplatform.googleapis.com storage.googleapis.com iamcredentials.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com --project=your-project-id
```

If an organization policy restricts allowed services, an organization-policy administrator must [allow these APIs first](https://console.cloud.google.com/iam-admin/orgpolicies/list). A project owner cannot override an inherited deny policy from organization.

## 1. Local Debug

### 1.1 Local development service account and IAM

This service account is only for local development. Production uses the dedicated Cloud Run identities in [Section 2.1](#21-production-architecture-and-service-accounts), without a JSON key.

Create the local development service account if it does not already exist:

```bash
gcloud iam service-accounts create your-project-id-chalksmith \
  --project=your-project-id \
  --display-name="Chalksmith local development"
```

Grant Vertex AI access:

```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

Grant the service account permission to sign short-lived URLs as itself:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com \
  --member="serviceAccount:your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=your-project-id
```

The local JSON key is expected at `.env/your-project-id-local.json`. If it doesn't exist or must be replaced, create a key only on a trusted workstation and keep the result under `.env/`:

```bash
gcloud iam service-accounts keys create \
  .env/your-project-id-local.json \
  --iam-account=your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com \
  --project=your-project-id
```

Prefer service-account impersonation or workload federation when the environment supports them. Delete unused JSON keys from IAM and remove their local files.

### 1.2 Create the (dev) GCS bucket

Bucket names are globally unique. Create the private development bucket:

```bash
gcloud storage buckets create \
  gs://your-project-id-chalksmith-dev \
  --project=your-project-id \
  --location=us-central1 \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --lifecycle-file=infra/gcloud/storage-lifecycle.json
```

Grant the local runtime account object access inside this bucket:

```bash
gcloud storage buckets add-iam-policy-binding \
  gs://your-project-id-chalksmith-dev \
  --member="serviceAccount:your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

`roles/storage.objectAdmin` manages objects but cannot create buckets. Bucket creation requires `storage.buckets.create`, normally supplied to the human deployment account through project-level `roles/storage.admin`.

The bucket can be deleted later after its objects are no longer needed:

```bash
gcloud storage rm --recursive gs://your-project-id-chalksmith-dev
```

This permanently removes the objects and bucket; inspect it first with `gcloud storage ls --recursive`.

### 1.3 Configure local runtime

The backend reads `.env/.env.backend.local`:

```dotenv
APP_ENV=local
APP_ROLE=api
FRONTEND_ORIGINS=http://localhost:3000

GCP_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=.env/your-project-id-local.json

LLM_PROVIDER=vertex
LLM_MODEL=gemini-3.6-flash
VERTEX_AI_LOCATION=global

DATABASE_URL=sqlite:///./.env/chalksmith.local.db
GCS_BUCKET=your-project-id-chalksmith-dev
GCS_SIGNER_SERVICE_ACCOUNT=your-project-id-chalksmith@your-project-id.iam.gserviceaccount.com
MANIM_RENDERER_URL=http://localhost:8081
```

Keep the Clerk variables documented in [CLERK.md](CLERK.md) in the same backend file. The frontend reads `.env/.env.frontend.local`.

Verify ADC and bucket access:

```bash
uv run --project backend python -c \
  "import google.auth; c, p = google.auth.default(); print(p, getattr(c, 'service_account_email', type(c).__name__))"
gcloud storage ls gs://your-project-id-chalksmith-dev
```

### 1.4 Local readiness checklist

Before starting the three processes in [README.md](README.md), confirm:

- the backend virtual environment is synced with `--extra video`;
- Cairo, Pango, FFmpeg, `pkg-config`, and CMake are installed for local Manim rendering;
- the service-account JSON path resolves and the key is active;
- Vertex AI accepts the configured model and location;
- the private GCS bucket exists and the local service account can upload/delete objects and sign URLs;
- `.env/chalksmith.local.db` is writable;
- the Clerk application and both local auth environment files are configured.

## 2. Production deployment

### 2.1 Production architecture and service accounts

Production uses three Cloud Run services:

- `chalksmith-web`: public Next.js service; reads only the Clerk server secret;
- `chalksmith-api`: public-network FastAPI service; every application route verifies a Clerk JWT;
- `chalksmith-renderer`: private Manim service; only `chalksmith-api` may invoke it.

The deploy script creates dedicated service accounts:

| Service account | Required access |
| :--- | :--- |
| `chalksmith-web` | Secret accessor for the Clerk server key only |
| `chalksmith-api` | Vertex AI User, Cloud SQL Client, bucket object admin, URL signing, database password, optional OpenAI key, renderer invoker |
| `chalksmith-renderer` | No project data, model, or secret roles |

Generated Python therefore executes in a container that cannot access the database, bucket, LLM, or secrets.

### 2.2 Production secrets

Create a database-password secret and the Clerk secret described in [CLERK.md](CLERK.md). Add an OpenAI secret only when `LLM_PROVIDER=openai`.

```bash
gcloud secrets create chalksmith-db-password \
  --project=your-project-id \
  --replication-policy=automatic
gcloud secrets versions add chalksmith-db-password \
  --project=your-project-id \
  --data-file=-
```

Enter the secret value on standard input and press Control-D. The deploy script grants each runtime account access only to the secrets it consumes.

For deployment commands, see [README.md](README.md#production-deployment).

### 2.3 Database initialization and v1 migration

Run initialization or migration from a trusted environment that can reach Cloud SQL:

```bash
uv run --project backend python -m backend.scripts.init_db
uv run --project backend python -m backend.scripts.migrate_v1
uv run --project backend python -m backend.scripts.migrate_v1 \
  --preserve-owner-ids \
  --static-root ../chalksmith-v1/backend/static \
  --apply
```

Use `--preserve-owner-ids` only when production reuses the v1 Clerk application. If the Clerk application changed, supply an explicit `--owner-map` instead. The migration is a dry run unless `--apply` is supplied. Validate row counts, ownership isolation, previews, downloads, source retention, and deletion before directing production traffic to v2.

### 2.4 Production troubleshooting

| Symptom | Likely fix |
| :--- | :--- |
| `serviceusage.services.enable` denied | Grant the human deployment account Service Usage Admin or ask an administrator to enable the APIs. |
| `storage.buckets.create` denied | Grant the human deployment account project-level Storage Admin. Object Admin on a service account is insufficient. |
| Resource Usage Restriction | Ask the organization-policy administrator to allow the required service APIs. |
| Vertex AI `403` | Grant the active runtime service account `roles/aiplatform.user` and verify model/location availability. |
| Bucket not found | Create the exact bucket or correct `GCS_BUCKET`; names are globally unique. |
| Signed URL failure | Verify `GCS_SIGNER_SERVICE_ACCOUNT` and self-grant Service Account Token Creator. |
| Manim dependency build failure | Install Cairo, Pango, FFmpeg, `pkg-config`, and CMake before `uv sync --extra video`. |
| API returns `401` | Follow [CLERK.md](CLERK.md) and compare issuer, publishable key application, and authorized origin. |
| API returns `503` during token verification | Confirm the API can reach the configured Clerk JWKS URL. |

## References

- [Vertex AI SDK authentication](https://cloud.google.com/vertex-ai/generative-ai/docs/sdks/overview)
- [Application Default Credentials](https://cloud.google.com/docs/authentication/application-default-credentials)
- [Cloud Storage IAM roles](https://cloud.google.com/storage/docs/access-control/iam-roles)
- [Cloud Run service identity](https://cloud.google.com/run/docs/securing/service-identity)
- [Cloud SQL Python connector and Cloud Run](https://cloud.google.com/sql/docs/postgres/connect-run)
- [Secret Manager access control](https://cloud.google.com/secret-manager/docs/access-control)
