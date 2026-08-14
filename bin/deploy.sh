#!/usr/bin/env bash
# Deploy or remove one environment's Cloud Run services. Service accounts come from
# prepare.sh; buckets, secrets, and the Cloud SQL instance come from setup.sh, which
# is also the only place that stops the database.
#
#   ./bin/deploy.sh stg|prod start|shutdown
set -euo pipefail

# Cloud Build uploads the working directory, so both builds need the repository root.
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_root}"

environment="${1:-}"
action="${2:-start}"
if [[ "${environment}" != "stg" && "${environment}" != "prod" ]] ||
   [[ "${action}" != "start" && "${action}" != "shutdown" ]]; then
  echo "Usage: ./bin/deploy.sh stg|prod start|shutdown" >&2
  exit 1
fi

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "Missing required environment variable: PROJECT_ID" >&2
  exit 1
fi
REGION="${REGION:-us-central1}"

sql_instance="${CLOUD_SQL_INSTANCE_NAME:-chalksmith-postgres-${environment}}"
api_service="${API_SERVICE:-chalksmith-api-${environment}}"
renderer_service="${RENDERER_SERVICE:-chalksmith-renderer-${environment}}"
web_service="${WEB_SERVICE:-chalksmith-web-${environment}}"

if [[ "${action}" == "shutdown" ]]; then
  # Production is a live service; removing its services takes the product offline.
  if [[ "${environment}" == "prod" ]]; then
    read -rp "Delete the PRODUCTION Cloud Run services and take Chalksmith offline? Type 'prod' to confirm: " answer
    [[ "${answer}" == "prod" ]] || { echo "Aborted." >&2; exit 1; }
  fi
  # Web first, so the front door closes before its dependencies disappear.
  for service in "${web_service}" "${api_service}" "${renderer_service}"; do
    if gcloud run services describe "${service}" --region "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
      gcloud run services delete "${service}" --region "${REGION}" --project "${PROJECT_ID}" --quiet
      echo "deleted: ${service}"
    fi
  done
  echo "Images, secrets, bucket, and data survive. Stop the database with ./bin/setup.sh ${environment} shutdown."
  exit 0
fi

required=(LLM_PROVIDER LLM_MODEL CLERK_PUBLISHABLE_KEY CLERK_ISSUER)
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

repository="${ARTIFACT_REPOSITORY:-chalksmith-${environment}}"
bucket="${GCS_BUCKET:-chalksmith-gcs-${environment}}"
database="${DATABASE_NAME:-chalksmith}"
database_user="${DATABASE_USER:-chalksmith}"
db_password_secret="${DB_PASSWORD_SECRET_NAME:-chalksmith-db-password-${environment}}"
clerk_secret="${CLERK_KEY_SECRET_NAME:-chalksmith-clerk-key-${environment}}"

api_account="chalksmith-api@${PROJECT_ID}.iam.gserviceaccount.com"
renderer_account="chalksmith-renderer@${PROJECT_ID}.iam.gserviceaccount.com"
web_account="chalksmith-web@${PROJECT_ID}.iam.gserviceaccount.com"
build_account="${BUILD_SERVICE_ACCOUNT:-chalksmith-deployer@${PROJECT_ID}.iam.gserviceaccount.com}"

registry="${REGION}-docker.pkg.dev/${PROJECT_ID}/${repository}"
revision="${REVISION_TAG:-$(git rev-parse --short HEAD)}"
api_image="${registry}/api:${revision}"
renderer_image="${registry}/renderer:${revision}"
web_image="${registry}/web:${revision}"

# Staging runs the same startup validation as production, so both report production.
app_env="${APP_ENV_OVERRIDE:-production}"
vertex_ai_location="${VERTEX_AI_LOCATION:-global}"

if [[ "${environment}" == "prod" ]]; then
  base_origins="${PRODUCTION_ORIGINS:-https://chalksmith.ai,https://www.chalksmith.ai,https://app.chalksmith.ai}"
else
  base_origins="${STAGING_ORIGINS:-}"
fi
# The API deploys before the web hostname exists and validation rejects non-HTTPS
# origins, so start from a placeholder and correct it at the end.
initial_origins="${base_origins:-https://placeholder.invalid}"

echo "Environment: ${environment}"
echo "Services:    ${api_service}, ${renderer_service}, ${web_service}"
echo

gcloud config set project "${PROJECT_ID}"

for account in "${api_account}" "${renderer_account}" "${web_account}"; do
  if ! gcloud iam service-accounts describe "${account}" >/dev/null 2>&1; then
    echo "Missing service account ${account}. Run ./bin/prepare.sh first." >&2
    exit 1
  fi
done
# Checked here rather than at --set-secrets, which would fail after the builds.
for secret in "${db_password_secret}" "${clerk_secret}"; do
  if ! gcloud secrets describe "${secret}" >/dev/null 2>&1; then
    echo "Missing secret ${secret}. Run ./bin/setup.sh ${environment} start first." >&2
    exit 1
  fi
done

if ! gcloud artifacts repositories describe "${repository}" --location "${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${repository}" --location "${REGION}" --repository-format docker
fi
# Every deploy pushes a new git-SHA tag; without this the registry grows without bound.
gcloud artifacts repositories set-cleanup-policies "${repository}" --location "${REGION}" \
  --policy-file "${repo_root}/bin/artifact-cleanup-policy.json" --no-dry-run >/dev/null

# The API creates its tables at startup, so the instance must already be up.
# setup.sh owns its lifecycle; this only checks.
sql_state="$(gcloud sql instances describe "${sql_instance}" --format='value(state)')"
if [[ "${sql_state}" != "RUNNABLE" ]]; then
  echo "${sql_instance} is ${sql_state}. Run ./bin/setup.sh ${environment} start first." >&2
  exit 1
fi

if [[ "${LLM_PROVIDER}" == "openai" ]]; then
  gcloud secrets add-iam-policy-binding "${LLM_SECRET_NAME}" \
    --member "serviceAccount:${api_account}" --role roles/secretmanager.secretAccessor >/dev/null
fi

# A build must name its service account explicitly: the organization policy
# constraints/cloudbuild.disableCreateDefaultServiceAccount leaves no default one.
gcloud builds submit --config bin/cloudbuild-backend.yaml \
  --service-account "projects/${PROJECT_ID}/serviceAccounts/${build_account}" \
  --substitutions "_API_IMAGE=${api_image},_RENDERER_IMAGE=${renderer_image}" .

gcloud run deploy "${renderer_service}" --image "${renderer_image}" --region "${REGION}" \
  --service-account "${renderer_account}" --no-allow-unauthenticated --cpu 2 --memory 2Gi \
  --concurrency 1 --timeout 900 --min 0 --max 2 \
  --set-env-vars "APP_ENV=${app_env},APP_ROLE=renderer,MANIM_TIMEOUT_SECONDS=600"
renderer_url="$(gcloud run services describe "${renderer_service}" --region "${REGION}" --format 'value(status.url)')"
gcloud run services add-iam-policy-binding "${renderer_service}" --region "${REGION}" \
  --member "serviceAccount:${api_account}" --role roles/run.invoker >/dev/null

secret_bindings="DATABASE_PASSWORD=${db_password_secret}:latest"
if [[ "${LLM_PROVIDER}" == "openai" ]]; then
  secret_bindings+=",OPENAI_API_KEY=${LLM_SECRET_NAME}:latest"
fi
connection_name="${PROJECT_ID}:${REGION}:${sql_instance}"
gcloud run deploy "${api_service}" --image "${api_image}" --region "${REGION}" \
  --service-account "${api_account}" --allow-unauthenticated --cpu 1 --memory 1Gi \
  --concurrency 8 --timeout 900 --min 0 --max 2 --add-cloudsql-instances "${connection_name}" \
  --set-env-vars "^|^APP_ENV=${app_env}|APP_ROLE=api|GCP_PROJECT_ID=${PROJECT_ID}|CLERK_ISSUER=${CLERK_ISSUER}|CLERK_AUTHORIZED_PARTIES=${initial_origins}|LLM_PROVIDER=${LLM_PROVIDER}|LLM_MODEL=${LLM_MODEL}|VERTEX_AI_LOCATION=${vertex_ai_location}|CLOUD_SQL_INSTANCE=${connection_name}|DATABASE_NAME=${database}|DATABASE_USER=${database_user}|GCS_BUCKET=${bucket}|GCS_SIGNER_SERVICE_ACCOUNT=${api_account}|MANIM_RENDERER_URL=${renderer_url}|GENERATION_TIMEOUT_SECONDS=840|FRONTEND_ORIGINS=${initial_origins}" \
  --set-secrets "${secret_bindings}"
api_url="$(gcloud run services describe "${api_service}" --region "${REGION}" --format 'value(status.url)')"

gcloud builds submit --config bin/cloudbuild-web.yaml \
  --service-account "projects/${PROJECT_ID}/serviceAccounts/${build_account}" \
  --substitutions "_WEB_IMAGE=${web_image},_API_URL=${api_url},_CLERK_PUBLISHABLE_KEY=${CLERK_PUBLISHABLE_KEY}" .
gcloud run deploy "${web_service}" --image "${web_image}" --region "${REGION}" \
  --service-account "${web_account}" --allow-unauthenticated --cpu 1 --memory 512Mi \
  --concurrency 40 --timeout 60 --min 0 --max 2 \
  --set-secrets "CLERK_SECRET_KEY=${clerk_secret}:latest"
web_url="$(gcloud run services describe "${web_service}" --region "${REGION}" --format 'value(status.url)')"

final_origins="${base_origins:+${base_origins},}${web_url}"
gcloud run services update "${api_service}" --region "${REGION}" \
  --update-env-vars "^|^FRONTEND_ORIGINS=${final_origins}|CLERK_AUTHORIZED_PARTIES=${final_origins}"

cat <<EOF

Environment: ${environment}
API: ${api_url}
Web: ${web_url}

Add ${web_url} to the Clerk allowed URLs for this instance; sign-in fails until you do.
Cloud Run also answers on a second hostname that is not in FRONTEND_ORIGINS -- use the URL above.
EOF
