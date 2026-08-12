# Google Cloud Platform Configuration

This is the single setup guide for Chalksmith's Google Cloud resources in project `gemini-code-shark`. Authentication is managed separately by Clerk; see [CLERK.md](CLERK.md).

Never commit service-account JSON files, database passwords, or provider secrets. Local runtime configuration belongs in the ignored root `.env/` directory. Production uses Cloud Run service identities and Secret Manager.

## Resource overview

| Resource | Purpose | Local development | Production |
| :--- | :--- | :--- | :--- |
| Vertex AI | Gemini lesson generation | Service-account JSON through Application Default Credentials (ADC) | Cloud Run API service account |
| Cloud Storage (GCS) | Private PDFs, HTML, and MP4 artifacts | `gemini-code-shark-chalksmith-dev` | `gemini-code-shark-chalksmith-private` by default |
| SQLite / Cloud SQL | Lesson metadata and source code | `.env/chalksmith.local.db` | PostgreSQL 16 in Cloud SQL |
| Cloud Run | Next.js web, FastAPI API, isolated Manim renderer | Three local processes replace it | Required |
| Secret Manager | Database password, Clerk server key, optional OpenAI key | Not used | Required |
| Artifact Registry / Cloud Build | Container image storage and builds | Not used | Required |

Vertex AI uses Google credentials and does not use a Gemini Developer API key in this architecture.

## Current project values

| Setting | Value |
| :--- | :--- |
| Project ID | `gemini-code-shark` |
| Default deployment region | `us-central1` |
| Vertex AI location | `global` |
| Vertex AI model | `gemini-3.1-pro-preview` |
| Local service account | `gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com` |
| Local credential file | `.env/gemini-code-shark-2bc98c50a55d.json` |
| Local GCS bucket | `gemini-code-shark-chalksmith-dev` |

Preview model availability can change. If the configured model becomes unavailable, choose a Vertex AI model supported in the selected location and update `LLM_MODEL`.

## 1. Administrator prerequisites

The project must have billing enabled. The human deployment account needs project-level permissions for the operations it performs; granting permissions to a runtime service account does not grant them to the human account.

| Principal | Recommended project role | Purpose |
| :--- | :--- | :--- |
| Deployment account | `roles/serviceusage.serviceUsageAdmin` | Enable required APIs |
| Deployment account | `roles/storage.admin` | Create and administer buckets |
| Deployment account | `roles/iam.serviceAccountCreator` | Create runtime service accounts |
| Deployment account | `roles/resourcemanager.projectIamAdmin` | Grant project IAM roles |
| Deployment account | `roles/run.admin` | Deploy Cloud Run services |
| Deployment account | `roles/cloudbuild.builds.editor` | Submit Cloud Build jobs |
| Deployment account | `roles/artifactregistry.admin` | Create and manage the image repository |
| Deployment account | `roles/cloudsql.admin` | Create and configure Cloud SQL |
| Deployment account | `roles/secretmanager.admin` | Create secrets and IAM bindings |
| Deployment account | `roles/iam.serviceAccountUser` | Deploy services as runtime identities |

An administrator can use narrower custom roles if every command in `infra/gcloud/deploy.sh` remains permitted.

Enable the APIs needed for local authenticated generation:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  iamcredentials.googleapis.com \
  --project=gemini-code-shark
```

Production additionally needs:

```bash
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  --project=gemini-code-shark
```

If an organization policy restricts allowed services, an organization-policy administrator must allow these APIs first. A project owner cannot override an inherited deny policy.

## 2. Local service account and IAM

Create the local development service account if it does not already exist:

```bash
gcloud iam service-accounts create gemini-code-shark-chalksmith \
  --project=gemini-code-shark \
  --display-name="Chalksmith local development"
```

Grant Vertex AI access:

```bash
gcloud projects add-iam-policy-binding gemini-code-shark \
  --member="serviceAccount:gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"
```

The local JSON key is already expected at `.env/gemini-code-shark-2bc98c50a55d.json`. If it must be replaced, create a key only on a trusted workstation and keep the result under `.env/`:

```bash
gcloud iam service-accounts keys create \
  .env/gemini-code-shark-local.json \
  --iam-account=gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com \
  --project=gemini-code-shark
```

Prefer service-account impersonation or workload federation when the environment supports them. Delete unused JSON keys from IAM and remove their local files.

## 3. Create the local GCS bucket

Bucket names are globally unique. Create the private development bucket:

```bash
gcloud storage buckets create \
  gs://gemini-code-shark-chalksmith-dev \
  --project=gemini-code-shark \
  --location=us-central1 \
  --default-storage-class=STANDARD \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --lifecycle-file=infra/gcloud/storage-lifecycle.json
```

Grant the local runtime account object access inside this bucket:

```bash
gcloud storage buckets add-iam-policy-binding \
  gs://gemini-code-shark-chalksmith-dev \
  --member="serviceAccount:gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

Grant the service account permission to sign short-lived URLs as itself:

```bash
gcloud iam service-accounts add-iam-policy-binding \
  gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com \
  --member="serviceAccount:gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project=gemini-code-shark
```

`roles/storage.objectAdmin` manages objects but cannot create buckets. Bucket creation requires `storage.buckets.create`, normally supplied to the human deployment account through project-level `roles/storage.admin`.

The bucket can be deleted later after its objects are no longer needed:

```bash
gcloud storage rm --recursive gs://gemini-code-shark-chalksmith-dev
```

This permanently removes the objects and bucket; inspect it first with `gcloud storage ls --recursive`.

## 4. Configure local runtime

The backend reads `.env/.env.backend.local`:

```dotenv
APP_ENV=local
APP_ROLE=api
FRONTEND_ORIGINS=http://localhost:3000

GCP_PROJECT_ID=gemini-code-shark
GOOGLE_APPLICATION_CREDENTIALS=.env/gemini-code-shark-2bc98c50a55d.json

LLM_PROVIDER=vertex
LLM_MODEL=gemini-3.1-pro-preview
VERTEX_AI_LOCATION=global

DATABASE_URL=sqlite:///./.env/chalksmith.local.db
GCS_BUCKET=gemini-code-shark-chalksmith-dev
GCS_SIGNER_SERVICE_ACCOUNT=gemini-code-shark-chalksmith@gemini-code-shark.iam.gserviceaccount.com
MANIM_RENDERER_URL=http://localhost:8081
```

Keep the Clerk variables documented in [CLERK.md](CLERK.md) in the same backend file. The frontend reads `.env/.env.frontend.local`.

Verify ADC and bucket access:

```bash
uv run --project backend python -c \
  "import google.auth; c, p = google.auth.default(); print(p, getattr(c, 'service_account_email', type(c).__name__))"
gcloud storage ls gs://gemini-code-shark-chalksmith-dev
```

## 5. Local readiness checklist

Before starting the three processes in [README.md](README.md), confirm:

- the backend virtual environment is synced with `--extra video`;
- Cairo, Pango, FFmpeg, `pkg-config`, and CMake are installed for local Manim rendering;
- the service-account JSON path resolves and the key is active;
- Vertex AI accepts the configured model and location;
- the private GCS bucket exists and the local service account can upload/delete objects and sign URLs;
- `.env/chalksmith.local.db` is writable;
- the Clerk application and both local auth environment files are configured.

## 6. Production architecture and service accounts

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

## 7. Production secrets

Create a database-password secret and the Clerk secret described in [CLERK.md](CLERK.md). Add an OpenAI secret only when `LLM_PROVIDER=openai`.

```bash
gcloud secrets create chalksmith-db-password \
  --project=gemini-code-shark \
  --replication-policy=automatic
gcloud secrets versions add chalksmith-db-password \
  --project=gemini-code-shark \
  --data-file=-
```

Enter the secret value on standard input and press Control-D. The deploy script grants each runtime account access only to the secrets it consumes.

## 8. Deploy

Authenticate as the deployment account, then export the required values:

```bash
gcloud auth login
gcloud config set project gemini-code-shark

export PROJECT_ID=gemini-code-shark
export REGION=us-central1
export LLM_PROVIDER=vertex
export LLM_MODEL=gemini-3.1-pro-preview
export VERTEX_AI_LOCATION=global
export DB_PASSWORD_SECRET_NAME=chalksmith-db-password
export CLERK_PUBLISHABLE_KEY=pk_live_...
export CLERK_SECRET_KEY_SECRET_NAME=chalksmith-clerk-secret-key
export CLERK_ISSUER=https://<production-instance>.clerk.accounts.dev

bash infra/gcloud/deploy.sh
```

The script:

1. enables APIs and creates Artifact Registry, private GCS, and Cloud SQL resources when absent;
2. creates least-privilege web, API, and renderer service accounts;
3. builds API, renderer, and web images with Cloud Build;
4. deploys the private renderer and grants only the API service account invocation access;
5. deploys the API with Cloud SQL, storage, signing, LLM, and JWT verification configuration;
6. builds the public web configuration into the frontend and injects the Clerk secret at runtime;
7. adds the generated web hostname to API CORS and Clerk authorized-party allowlists.

After the first deployment, add the printed web hostname to the allowed URLs in the Clerk dashboard. Rebuild the web image when `NEXT_PUBLIC_API_URL` or `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` changes.

For OpenAI, set `LLM_PROVIDER=openai` and export `LLM_SECRET_NAME` with the OpenAI-key secret name.

## 9. Database initialization and v1 migration

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

## 10. Troubleshooting

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
