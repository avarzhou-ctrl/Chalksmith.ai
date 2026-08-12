# Google Cloud deployment assets

`deploy.sh` provisions the production resources, builds three images, and deploys the public Next.js web service, public-network authenticated FastAPI service, and private Manim renderer. Running it changes Google Cloud resources and requires the deployment permissions documented in [GCP.md](../../GCP.md).

Before deployment:

1. Configure the production Clerk application and allowed URLs as described in [CLERK.md](../../CLERK.md).
2. Create Secret Manager secrets for the database password and Clerk server key. Add an OpenAI-key secret only when selecting OpenAI.
3. Export the required values and run the script from the repository root.

```bash
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

For OpenAI, set `LLM_PROVIDER=openai` and export `LLM_SECRET_NAME` with the OpenAI-key secret name. Vertex AI authenticates as the API service account and needs no LLM key.

The API service account can use the selected LLM, Cloud SQL, private lesson objects, required secrets, URL signing, and the private renderer. The web service account can read only the Clerk server secret. The renderer service account intentionally has no project roles and receives no database, storage, secret, or LLM credentials.

The deployment enforces Uniform Bucket-Level Access and Public Access Prevention on the lesson bucket. Public Access Prevention still permits scoped V4 signed URLs, so previews and downloads remain private without public IAM grants. The generated web URL is added to API CORS and JWT authorized-party settings; add the same URL to the Clerk application's allowed URLs after the first deployment.

Initialize or migrate data from a trusted environment with Cloud SQL access:

```bash
uv run --project backend python -m backend.scripts.init_db
uv run --project backend python -m backend.scripts.migrate_v1
uv run --project backend python -m backend.scripts.migrate_v1 \
  --preserve-owner-ids \
  --static-root ../chalksmith-v1/backend/static \
  --apply
```

Preserve owner IDs only when reusing the v1 Clerk application. Otherwise supply an explicit `--owner-map`. The migration is a dry run unless `--apply` is supplied; reconcile lesson counts and ownership and test all preview/download/delete paths before cutover.
