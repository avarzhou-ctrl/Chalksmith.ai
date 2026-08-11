# Google Cloud deployment

`deploy.sh` provisions the minimal runtime, builds three images, and deploys Cloud Run web, API, and the isolated Manim renderer. It is dry in the repository: running it changes GCP resources and requires project admin/deployment permissions.

Before running it:

1. Upgrade the project to Identity Platform and enable Google, Microsoft, and Email/Password providers in the Google Cloud console. Microsoft requires its client ID and secret; add `https://<project-id>.firebaseapp.com/__/auth/handler` to the Microsoft app redirect URIs. Add `chalksmith.ai`, `www.chalksmith.ai`, `app.chalksmith.ai`, and the Cloud Run web hostname to Identity Platform authorized domains.
2. Create Secret Manager secrets for the database password and the selected LLM API key. Do not put either value in this repository.
3. Export the required values shown below, then run `bash infra/gcloud/deploy.sh` from the repository root.

```bash
export PROJECT_ID=gemini-code-shark
export REGION=us-central1
export LLM_PROVIDER=gemini
export LLM_MODEL=your-approved-model-id
export LLM_SECRET_NAME=gemini-api-key
export DB_PASSWORD_SECRET_NAME=chalksmith-db-password
export FIREBASE_API_KEY=your-public-browser-api-key
export FIREBASE_AUTH_DOMAIN=gemini-code-shark.firebaseapp.com
export FIREBASE_APP_ID=your-public-browser-app-id
bash infra/gcloud/deploy.sh
```

The API service account can reach Cloud SQL, private lesson objects, required secrets, and IAM signing. The renderer service account intentionally receives no project roles and the renderer receives no database or LLM secrets. Cloud Run IAM permits only the API service account to invoke it.
The deployment script also enforces Uniform Bucket-Level Access and [Public Access Prevention](https://cloud.google.com/storage/docs/public-access-prevention) on the lesson bucket. Public Access Prevention still permits scoped V4 Signed URLs, so previews and downloads remain private without public IAM grants.
The deploy script also adds the deployed web service URL to the API CORS allowlist; Identity Platform still requires that hostname to be added to authorized domains in the console.

After deployment, initialize/migrate data from a Cloud Run job or a trusted workstation with Cloud SQL access:

```bash
uv run --project backend python -m backend.scripts.init_db
uv run --project backend python -m backend.scripts.migrate_v1
uv run --project backend python -m backend.scripts.migrate_v1 --owner-map owner-map.json
uv run --project backend python -m backend.scripts.migrate_v1 --owner-map owner-map.json --static-root ../chalksmith-v1/backend/static --apply
```

The owner map is a JSON object from legacy Clerk uid to the verified Identity Platform uid. If users were imported while preserving every uid, pass `--preserve-owner-ids` instead. Generated v1 files were intentionally removed from `main`; check out `v1.0` into a separate worktree or restore a production backup and pass that directory with `--static-root`. The migration is a dry run unless `--apply` is supplied. Validate lesson counts, ownership, all three previews, downloads, source retention, and delete behavior before directing production traffic to v2.
