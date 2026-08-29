#!/usr/bin/env bash
# Deploy or remove one environment's Cloud Run services. Service accounts come from
# prepare.sh; buckets, secrets, and the Cloud SQL instance come from setup.sh, which
# is also the only place that stops the database.
#
# Configuration defaults come from .env/env.deploy; already-exported variables
# take precedence.
#
#   ./bin/deploy.sh stg|prod start|shutdown
set -euo pipefail

# Cloud Build uploads the working directory, so both builds need the repository root.
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_root}"

deploy_env_file="${DEPLOY_ENV_FILE:-${repo_root}/.env/env.deploy}"

# Load a strict dotenv subset without executing shell code. This catches typos,
# keeps values literal, and lets one-off exported values override the file.
load_deploy_env() {
  local file="$1" line name value line_number=0
  while IFS= read -r line || [[ -n "${line}" ]]; do
    line_number=$((line_number + 1))
    line="${line%$'\r'}"
    [[ "${line}" =~ ^[[:space:]]*$ || "${line}" =~ ^[[:space:]]*# ]] && continue
    if [[ ! "${line}" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      echo "Invalid deployment config at ${file}:${line_number}; expected NAME=value." >&2
      exit 1
    fi
    name="${BASH_REMATCH[1]}"
    value="${BASH_REMATCH[2]}"
    case "${name}" in
      PROJECT_ID|REGION|DOMAIN|LLM_PROVIDER|LLM_MODEL|VERTEX_AI_LOCATION|LLM_SECRET_NAME) ;;
      LLM_TIMEOUT_SECONDS|LLM_MAX_OUTPUT_TOKENS|DEEPSEEK_THINKING) ;;
      MAX_SOURCE_CHARACTERS) ;; # Retain old deploy files; direct PDF inputs no longer use this value.
      BUILD_SERVICE_ACCOUNT|CLOUD_SQL_INSTANCE_NAME|API_SERVICE|RENDERER_SERVICE|WEB_SERVICE) ;;
      ARTIFACT_REPOSITORY|GCS_BUCKET|DATABASE_NAME|DATABASE_USER|DB_PASSWORD_SECRET_NAME) ;;
      CLERK_KEY_SECRET_NAME|CLERK_KEY_FILE|REVISION_TAG|STAGING_ORIGINS) ;;
      *)
        echo "Unknown deployment setting ${name} at ${file}:${line_number}." >&2
        exit 1
        ;;
    esac
    if [[ -z "${!name+x}" ]]; then
      printf -v "${name}" '%s' "${value}"
      export "${name}"
    fi
  done < "${file}"
}

if [[ -f "${deploy_env_file}" ]]; then
  load_deploy_env "${deploy_env_file}"
  echo "Loaded deployment config: ${deploy_env_file}"
fi

environment="${1:-}"
action="${2:-start}"
if [[ "${environment}" != "stg" && "${environment}" != "prod" ]] ||
   [[ "${action}" != "start" && "${action}" != "shutdown" ]]; then
  echo "Usage: ./bin/deploy.sh stg|prod start|shutdown" >&2
  exit 1
fi

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "Missing required deployment setting: PROJECT_ID" >&2
  echo "Copy bin/env.deploy.template to .env/env.deploy and replace its placeholders." >&2
  exit 1
fi
REGION="${REGION:-us-central1}"
build_account="${BUILD_SERVICE_ACCOUNT:-chalksmith-deployer@${PROJECT_ID}.iam.gserviceaccount.com}"

# Process-scoped, unlike `gcloud config set`, so an interrupted run leaves no
# impersonation behind in the caller's gcloud configuration.
export CLOUDSDK_AUTH_IMPERSONATE_SERVICE_ACCOUNT="${build_account}"

sql_instance="${CLOUD_SQL_INSTANCE_NAME:-chalksmith-postgres-${environment}}"
api_service="${API_SERVICE:-chalksmith-api-${environment}}"
renderer_service="${RENDERER_SERVICE:-chalksmith-renderer-${environment}}"
web_service="${WEB_SERVICE:-chalksmith-web-${environment}}"
scheduler_job="${api_service}-keep-warm"

if [[ "${action}" == "shutdown" ]]; then
  # Production is a live service; removing its services takes the product offline.
  if [[ "${environment}" == "prod" ]]; then
    read -rp "Delete the PRODUCTION Cloud Run services and take Chalksmith offline? Type 'prod' to confirm: " answer
    [[ "${answer}" == "prod" ]] || { echo "Aborted." >&2; exit 1; }
  fi
  # Web first, so the front door closes before its dependencies disappear.
  if gcloud scheduler jobs describe "${scheduler_job}" --location "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud scheduler jobs delete "${scheduler_job}" --location "${REGION}" --project "${PROJECT_ID}" --quiet
    echo "deleted: ${scheduler_job}"
  fi
  for service in "${web_service}" "${api_service}" "${renderer_service}"; do
    if gcloud run services describe "${service}" --region "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
      gcloud run services delete "${service}" --region "${REGION}" --project "${PROJECT_ID}" --quiet
      echo "deleted: ${service}"
    fi
  done
  echo "Images, secrets, bucket, and data survive. Stop the database with ./bin/setup.sh ${environment} shutdown."
  exit 0
fi

domain=""
if [[ "${environment}" == "prod" ]]; then
  domain="${DOMAIN:-}"
  domain="${domain%.}"
  domain="$(printf '%s' "${domain}" | tr '[:upper:]' '[:lower:]')"
  if [[ -z "${domain}" ]]; then
    echo "Missing required deployment setting for prod: DOMAIN" >&2
    echo "Use a bare domain in .env/env.deploy, for example: DOMAIN=example.com" >&2
    exit 1
  fi
  if [[ ! "${domain}" =~ ^([a-z0-9]([a-z0-9-]*[a-z0-9])?\.)+[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
    echo "DOMAIN must be a bare domain without a scheme, path, port, spaces, or commas." >&2
    exit 1
  fi
fi
site_domain="${domain:-chalksmith.ai}"

# Environment wins; the file setup.sh reads is the fallback. `|| true` keeps a
# missing file or key from aborting under set -e.
clerk_file="${CLERK_KEY_FILE:-${repo_root}/.env/clerk.key.${environment}}"
clerk_value() { grep -m1 "^$1=" "${clerk_file}" 2>/dev/null | cut -d= -f2- | tr -d '\r\n' || true; }
CLERK_ISSUER="${CLERK_ISSUER:-$(clerk_value CLERK_ISSUER)}"
CLERK_PUBLISHABLE_KEY="${CLERK_PUBLISHABLE_KEY:-$(clerk_value NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY)}"

required=(LLM_PROVIDER LLM_MODEL CLERK_PUBLISHABLE_KEY CLERK_ISSUER)
for name in "${required[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required deployment setting: ${name}" >&2
    exit 1
  fi
done
# Vertex authenticates through the API service account; the key-based providers
# each mount LLM_SECRET_NAME under the variable name their client library reads.
case "${LLM_PROVIDER}" in
  vertex) llm_secret_variable="" ;;
  openai) llm_secret_variable="OPENAI_API_KEY" ;;
  deepseek) llm_secret_variable="DEEPSEEK_API_KEY" ;;
  *)
    echo "LLM_PROVIDER must be 'vertex', 'openai', or 'deepseek'." >&2
    exit 1
    ;;
esac
if [[ -n "${llm_secret_variable}" && -z "${LLM_SECRET_NAME:-}" ]]; then
  echo "Missing required environment variable for ${LLM_PROVIDER}: LLM_SECRET_NAME" >&2
  exit 1
fi
# A development key deploys cleanly and then fails sign-in in the browser.
if [[ "${environment}" == "prod" && "${CLERK_PUBLISHABLE_KEY}" != pk_live_* ]]; then
  echo "CLERK_PUBLISHABLE_KEY is a development key; prod needs the production Clerk instance." >&2
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

registry="${REGION}-docker.pkg.dev/${PROJECT_ID}/${repository}"
revision="${REVISION_TAG:-$(git rev-parse --short HEAD)}"
api_image="${registry}/api:${revision}"
renderer_image="${registry}/renderer:${revision}"
web_image="${registry}/web:${revision}"

# Staging runs the same startup validation as production, so both report production.
app_env="${APP_ENV_OVERRIDE:-production}"
vertex_ai_location="${VERTEX_AI_LOCATION:-global}"
llm_timeout_seconds="${LLM_TIMEOUT_SECONDS:-120}"
llm_max_output_tokens="${LLM_MAX_OUTPUT_TOKENS:-32768}"
# DeepSeek bills its chain of thought against LLM_MAX_OUTPUT_TOKENS, so leaving
# thinking off keeps that budget available for the lesson itself.
deepseek_thinking="${DEEPSEEK_THINKING:-false}"

for setting in llm_timeout_seconds llm_max_output_tokens; do
  value="${!setting}"
  if [[ ! "${value}" =~ ^[1-9][0-9]*$ ]]; then
    echo "${setting} must be a positive integer." >&2
    exit 1
  fi
done

if [[ "${environment}" == "prod" ]]; then
  base_origins="https://${domain},https://www.${domain},https://app.${domain}"
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
  --policy "${repo_root}/bin/artifact-cleanup-policy.json" --no-dry-run >/dev/null

# The migration job and API both require a running Cloud SQL instance.
# setup.sh owns its lifecycle; this only checks.
sql_state="$(gcloud sql instances describe "${sql_instance}" --format='value(state)')"
if [[ "${sql_state}" != "RUNNABLE" ]]; then
  echo "${sql_instance} is ${sql_state}. Run ./bin/setup.sh ${environment} start first." >&2
  exit 1
fi

if [[ -n "${llm_secret_variable}" ]]; then
  gcloud secrets add-iam-policy-binding "${LLM_SECRET_NAME}" \
    --member "serviceAccount:${api_account}" --role roles/secretmanager.secretAccessor >/dev/null
fi

# A build must name its service account explicitly: the organization policy
# constraints/cloudbuild.disableCreateDefaultServiceAccount leaves no default one.
gcloud builds submit --config bin/cloudbuild-backend.yaml \
  --service-account "projects/${PROJECT_ID}/serviceAccounts/${build_account}" \
  --substitutions "_API_IMAGE=${api_image},_RENDERER_IMAGE=${renderer_image}" .

# Cloud Build stages one source archive per submission in this shared bucket.
# Expiring completed archives prevents deploy frequency from growing storage forever.
cloud_build_bucket="gs://${PROJECT_ID}_cloudbuild"
if gcloud storage buckets describe "${cloud_build_bucket}" >/dev/null 2>&1; then
  gcloud storage buckets update "${cloud_build_bucket}" \
    --lifecycle-file "${repo_root}/bin/cloudbuild-source-lifecycle.json" >/dev/null
fi

gcloud run deploy "${renderer_service}" --image "${renderer_image}" --region "${REGION}" \
  --service-account "${renderer_account}" --no-allow-unauthenticated --cpu 2 --memory 2Gi \
  --concurrency 1 --timeout 900 --min 0 --max 2 --cpu-throttling \
  --set-env-vars "APP_ENV=${app_env},APP_ROLE=renderer,MANIM_TIMEOUT_SECONDS=600"
renderer_url="$(gcloud run services describe "${renderer_service}" --region "${REGION}" --format 'value(status.url)')"
gcloud run services add-iam-policy-binding "${renderer_service}" --region "${REGION}" \
  --member "serviceAccount:${api_account}" --role roles/run.invoker >/dev/null

secret_bindings="DATABASE_PASSWORD=${db_password_secret}:latest"
if [[ -n "${llm_secret_variable}" ]]; then
  secret_bindings+=",${llm_secret_variable}=${LLM_SECRET_NAME}:latest"
fi
connection_name="${PROJECT_ID}:${REGION}:${sql_instance}"
# Run additive schema changes before exposing the new API revision. The job uses
# APP_ENV=local because it only needs the database settings, not API/LLM config.
migration_job_env="^|^APP_ENV=local|APP_ROLE=api|CLOUD_SQL_INSTANCE=${connection_name}|DATABASE_NAME=${database}|DATABASE_USER=${database_user}|AUTO_CREATE_TABLES=true"
gcloud run jobs deploy "${api_service}-migration" --image "${api_image}" --region "${REGION}" \
  --service-account "${api_account}" --cpu 1 --memory 512Mi --task-timeout 5m --max-retries 0 \
  --set-cloudsql-instances "${connection_name}" --command python \
  --args=-m,backend.scripts.init_db --set-env-vars "${migration_job_env}" \
  --set-secrets "DATABASE_PASSWORD=${db_password_secret}:latest" --execute-now --wait

gcloud run deploy "${api_service}" --image "${api_image}" --region "${REGION}" \
  --service-account "${api_account}" --allow-unauthenticated --cpu 1 --memory 1Gi \
  --concurrency 8 --timeout 900 --min 0 --max 2 --cpu-throttling \
  --add-cloudsql-instances "${connection_name}" \
  --set-env-vars "^|^APP_ENV=${app_env}|APP_ROLE=api|GCP_PROJECT_ID=${PROJECT_ID}|CLERK_ISSUER=${CLERK_ISSUER}|CLERK_AUTHORIZED_PARTIES=${initial_origins}|LLM_PROVIDER=${LLM_PROVIDER}|LLM_MODEL=${LLM_MODEL}|LLM_TIMEOUT_SECONDS=${llm_timeout_seconds}|LLM_MAX_OUTPUT_TOKENS=${llm_max_output_tokens}|DEEPSEEK_THINKING=${deepseek_thinking}|VERTEX_AI_LOCATION=${vertex_ai_location}|CLOUD_SQL_INSTANCE=${connection_name}|DATABASE_NAME=${database}|DATABASE_USER=${database_user}|GCS_BUCKET=${bucket}|GCS_SIGNER_SERVICE_ACCOUNT=${api_account}|MANIM_RENDERER_URL=${renderer_url}|GENERATION_TIMEOUT_SECONDS=840|FRONTEND_ORIGINS=${initial_origins}|AUTO_CREATE_TABLES=false" \
  --set-secrets "${secret_bindings}"
api_url="$(gcloud run services describe "${api_service}" --region "${REGION}" --format 'value(status.url)')"

# Keep one API instance warm enough to hide the usual idle eviction window.
# Use the single /ready route for the keep-warm request.
if gcloud scheduler jobs describe "${scheduler_job}" --location "${REGION}" --project "${PROJECT_ID}" >/dev/null 2>&1; then
  gcloud scheduler jobs update http "${scheduler_job}" --location "${REGION}" \
    --schedule="*/3 * * * *" --uri="${api_url}/ready" --http-method=GET \
    --attempt-deadline=30s --max-retry-attempts=0 --time-zone=Etc/UTC
else
  gcloud scheduler jobs create http "${scheduler_job}" --location "${REGION}" \
    --schedule="*/3 * * * *" --uri="${api_url}/ready" --http-method=GET \
    --attempt-deadline=30s --max-retry-attempts=0 --time-zone=Etc/UTC
fi

gcloud builds submit --config bin/cloudbuild-web.yaml \
  --service-account "projects/${PROJECT_ID}/serviceAccounts/${build_account}" \
  --substitutions "_WEB_IMAGE=${web_image},_API_URL=${api_url},_CLERK_PUBLISHABLE_KEY=${CLERK_PUBLISHABLE_KEY},_SITE_DOMAIN=${site_domain}" .
gcloud run deploy "${web_service}" --image "${web_image}" --region "${REGION}" \
  --service-account "${web_account}" --allow-unauthenticated --cpu 1 --memory 512Mi \
  --concurrency 40 --timeout 60 --min 0 --max 2 --cpu-throttling \
  --set-secrets "CLERK_SECRET_KEY=${clerk_secret}:latest"
web_url="$(gcloud run services describe "${web_service}" --region "${REGION}" --format 'value(status.url)')"

final_origins="${base_origins:+${base_origins},}${web_url}"
gcloud run services update "${api_service}" --region "${REGION}" \
  --update-env-vars "^|^FRONTEND_ORIGINS=${final_origins}|CLERK_AUTHORIZED_PARTIES=${final_origins}"

cat <<EOF

Environment: ${environment}
API: ${api_url}
Web: ${web_url}
${domain:+Domain origins: ${base_origins}}

Configure ${site_domain} as the Clerk production domain and complete Clerk's DNS records before testing sign-in.
The run.app URL is for deployment diagnostics; Clerk production keys only work on the configured custom domain.
Cloud Run also answers on a second hostname that is not in FRONTEND_ORIGINS -- use the URL above for diagnostics.
EOF
