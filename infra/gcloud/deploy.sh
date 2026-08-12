#!/usr/bin/env bash
set -euo pipefail

required=(
  PROJECT_ID REGION LLM_PROVIDER LLM_MODEL DB_PASSWORD_SECRET_NAME
  CLERK_PUBLISHABLE_KEY CLERK_SECRET_KEY_SECRET_NAME CLERK_ISSUER
)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
done

if [[ "${LLM_PROVIDER}" != "vertex" && "${LLM_PROVIDER}" != "openai" ]]; then
  echo "LLM_PROVIDER must be 'vertex' or 'openai'." >&2
  exit 1
fi
if [[ "${LLM_PROVIDER}" == "openai" && -z "${LLM_SECRET_NAME:-}" ]]; then
  echo "Missing required environment variable for OpenAI: LLM_SECRET_NAME" >&2
  exit 1
fi

repository="${ARTIFACT_REPOSITORY:-chalksmith}"
bucket="${GCS_BUCKET:-${PROJECT_ID}-chalksmith-private}"
sql_instance="${CLOUD_SQL_INSTANCE_NAME:-chalksmith-postgres}"
database="${DATABASE_NAME:-chalksmith}"
database_user="${DATABASE_USER:-chalksmith}"
api_service="${API_SERVICE:-chalksmith-api}"
renderer_service="${RENDERER_SERVICE:-chalksmith-renderer}"
web_service="${WEB_SERVICE:-chalksmith-web}"
api_account="chalksmith-api@${PROJECT_ID}.iam.gserviceaccount.com"
renderer_account="chalksmith-renderer@${PROJECT_ID}.iam.gserviceaccount.com"
web_account="chalksmith-web@${PROJECT_ID}.iam.gserviceaccount.com"
registry="${REGION}-docker.pkg.dev/${PROJECT_ID}/${repository}"
revision="${REVISION_TAG:-$(git rev-parse --short HEAD)}"
vertex_ai_location="${VERTEX_AI_LOCATION:-global}"
api_image="${registry}/api:${revision}"
renderer_image="${registry}/renderer:${revision}"
web_image="${registry}/web:${revision}"

gcloud config set project "${PROJECT_ID}"
gcloud services enable \
  artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com storage.googleapis.com \
  iamcredentials.googleapis.com aiplatform.googleapis.com

if ! gcloud artifacts repositories describe "${repository}" --location "${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${repository}" --location "${REGION}" --repository-format docker
fi

if ! gcloud storage buckets describe "gs://${bucket}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${bucket}" --location "${REGION}" --uniform-bucket-level-access
fi
gcloud storage buckets update "gs://${bucket}" \
  --uniform-bucket-level-access \
  --public-access-prevention \
  --lifecycle-file infra/gcloud/storage-lifecycle.json

for account_name in chalksmith-api chalksmith-renderer chalksmith-web; do
  if ! gcloud iam service-accounts describe "${account_name}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${account_name}"
  fi
done
gcloud secrets add-iam-policy-binding "${CLERK_SECRET_KEY_SECRET_NAME}" \
  --member "serviceAccount:${web_account}" --role roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member "serviceAccount:${api_account}" --role roles/cloudsql.client --condition=None
if [[ "${LLM_PROVIDER}" == "vertex" ]]; then
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member "serviceAccount:${api_account}" --role roles/aiplatform.user --condition=None
fi
gcloud storage buckets add-iam-policy-binding "gs://${bucket}" \
  --member "serviceAccount:${api_account}" --role roles/storage.objectAdmin
secret_names=("${DB_PASSWORD_SECRET_NAME}")
if [[ "${LLM_PROVIDER}" == "openai" ]]; then
  secret_names+=("${LLM_SECRET_NAME}")
fi
for secret_name in "${secret_names[@]}"; do
  gcloud secrets add-iam-policy-binding "${secret_name}" \
    --member "serviceAccount:${api_account}" --role roles/secretmanager.secretAccessor
done
gcloud iam service-accounts add-iam-policy-binding "${api_account}" \
  --member "serviceAccount:${api_account}" --role roles/iam.serviceAccountTokenCreator

if ! gcloud sql instances describe "${sql_instance}" >/dev/null 2>&1; then
  gcloud sql instances create "${sql_instance}" \
    --database-version POSTGRES_16 --region "${REGION}" --tier db-f1-micro \
    --storage-type SSD --storage-size 10 --storage-auto-increase
fi
if ! gcloud sql databases describe "${database}" --instance "${sql_instance}" >/dev/null 2>&1; then
  gcloud sql databases create "${database}" --instance "${sql_instance}"
fi
db_password="$(gcloud secrets versions access latest --secret "${DB_PASSWORD_SECRET_NAME}")"
if gcloud sql users list --instance "${sql_instance}" --filter "name=${database_user}" --format 'value(name)' | grep -q .; then
  gcloud sql users set-password "${database_user}" --instance "${sql_instance}" --password "${db_password}"
else
  gcloud sql users create "${database_user}" --instance "${sql_instance}" --password "${db_password}"
fi
unset db_password

gcloud builds submit --config infra/gcloud/cloudbuild-backend.yaml \
  --substitutions "_API_IMAGE=${api_image},_RENDERER_IMAGE=${renderer_image}" .

gcloud run deploy "${renderer_service}" --image "${renderer_image}" --region "${REGION}" \
  --service-account "${renderer_account}" --no-allow-unauthenticated --cpu 2 --memory 2Gi \
  --concurrency 1 --timeout 900 --min 0 --max 2 \
  --set-env-vars "APP_ENV=production,APP_ROLE=renderer,MANIM_TIMEOUT_SECONDS=600"
renderer_url="$(gcloud run services describe "${renderer_service}" --region "${REGION}" --format 'value(status.url)')"
gcloud run services add-iam-policy-binding "${renderer_service}" --region "${REGION}" \
  --member "serviceAccount:${api_account}" --role roles/run.invoker

secret_bindings="DATABASE_PASSWORD=${DB_PASSWORD_SECRET_NAME}:latest"
if [[ "${LLM_PROVIDER}" == "openai" ]]; then
  secret_bindings+=",OPENAI_API_KEY=${LLM_SECRET_NAME}:latest"
fi
connection_name="${PROJECT_ID}:${REGION}:${sql_instance}"
gcloud run deploy "${api_service}" --image "${api_image}" --region "${REGION}" \
  --service-account "${api_account}" --allow-unauthenticated --cpu 1 --memory 1Gi \
  --concurrency 8 --timeout 900 --min 0 --max 5 --add-cloudsql-instances "${connection_name}" \
  --set-env-vars "^|^APP_ENV=production|APP_ROLE=api|GCP_PROJECT_ID=${PROJECT_ID}|CLERK_ISSUER=${CLERK_ISSUER}|CLERK_AUTHORIZED_PARTIES=https://chalksmith.ai,https://www.chalksmith.ai,https://app.chalksmith.ai|LLM_PROVIDER=${LLM_PROVIDER}|LLM_MODEL=${LLM_MODEL}|VERTEX_AI_LOCATION=${vertex_ai_location}|CLOUD_SQL_INSTANCE=${connection_name}|DATABASE_NAME=${database}|DATABASE_USER=${database_user}|GCS_BUCKET=${bucket}|GCS_SIGNER_SERVICE_ACCOUNT=${api_account}|MANIM_RENDERER_URL=${renderer_url}|GENERATION_TIMEOUT_SECONDS=840|FRONTEND_ORIGINS=https://chalksmith.ai,https://www.chalksmith.ai,https://app.chalksmith.ai" \
  --set-secrets "${secret_bindings}"
api_url="$(gcloud run services describe "${api_service}" --region "${REGION}" --format 'value(status.url)')"

gcloud builds submit --config infra/gcloud/cloudbuild-web.yaml \
  --substitutions "_WEB_IMAGE=${web_image},_API_URL=${api_url},_CLERK_PUBLISHABLE_KEY=${CLERK_PUBLISHABLE_KEY}" .
gcloud run deploy "${web_service}" --image "${web_image}" --region "${REGION}" \
  --service-account "${web_account}" --allow-unauthenticated --cpu 1 --memory 512Mi \
  --concurrency 40 --timeout 60 --min 0 --max 3 \
  --set-secrets "CLERK_SECRET_KEY=${CLERK_SECRET_KEY_SECRET_NAME}:latest"
web_url="$(gcloud run services describe "${web_service}" --region "${REGION}" --format 'value(status.url)')"
gcloud run services update "${api_service}" --region "${REGION}" \
  --update-env-vars "^|^FRONTEND_ORIGINS=https://chalksmith.ai,https://www.chalksmith.ai,https://app.chalksmith.ai,${web_url}|CLERK_AUTHORIZED_PARTIES=https://chalksmith.ai,https://www.chalksmith.ai,https://app.chalksmith.ai,${web_url}"

echo "API: ${api_url}"
echo "Web: ${web_url}"
