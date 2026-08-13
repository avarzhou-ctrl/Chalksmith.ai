#!/usr/bin/env bash
# Create one environment's resources: secrets, GCS bucket, Cloud SQL instance.
# "local" shares the staging resources. Safe to re-run; existing resources are kept.
# "start" leaves the instance running so debug.sh and deploy.sh can be repeated
# without paying its boot time again; "shutdown" stops it and keeps everything else.
#
#   ./bin/setup.sh local|stg|prod start|shutdown
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

environment="${1:-}"
action="${2:-start}"
[[ "${environment}" == "local" ]] && environment="stg"
if [[ "${environment}" != "stg" && "${environment}" != "prod" ]] ||
   [[ "${action}" != "start" && "${action}" != "shutdown" ]]; then
  echo "Usage: ./bin/setup.sh local|stg|prod start|shutdown" >&2
  exit 1
fi

project="${PROJECT_ID:-}"
if [[ -z "${project}" ]]; then
  echo "Missing PROJECT_ID in the environment." >&2
  exit 1
fi
region="${REGION:-us-central1}"

deployer="chalksmith-deployer@${project}.iam.gserviceaccount.com"
api_account="chalksmith-api@${project}.iam.gserviceaccount.com"
bucket="chalksmith-gcs-${environment}"
sql_instance="chalksmith-postgres-${environment}"
database="${DATABASE_NAME:-chalksmith}"
database_user="${DATABASE_USER:-chalksmith}"
db_secret="chalksmith-db-password-${environment}"
clerk_secret="chalksmith-clerk-key-${environment}"

# Creating secrets and instances needs the deployer's roles, not the human account's.
# --verbosity=error drops the impersonation warning gcloud repeats on every call.
gc() { gcloud "$@" --project "${project}" --impersonate-service-account="${deployer}" --verbosity=error; }
sql_state() { gc sql instances describe "$1" --format='value(state)'; }

# Cloud SQL serializes operations per instance and rejects a second one with 409,
# including one an earlier run left behind.
sql_drain() {
  local ops
  ops="$(gc sql operations list --instance "$1" --filter='status!=DONE' --format='value(name)')"
  if [[ -n "${ops}" ]]; then
    echo "waiting for in-flight operations on $1"
    # shellcheck disable=SC2086
    gc sql operations wait ${ops} --timeout=900 >/dev/null
  fi
}

sql_start() {
  sql_drain "$1"
  if [[ "$(sql_state "$1")" != "RUNNABLE" ]]; then
    gc sql instances patch "$1" --activation-policy=ALWAYS --quiet >/dev/null
    until [[ "$(sql_state "$1")" == "RUNNABLE" ]]; do
      echo "waiting for $1 to become RUNNABLE"
      sleep 10
    done
  fi
  echo "running: $1"
}

sql_stop() {
  sql_drain "$1"
  gc sql instances patch "$1" --activation-policy=NEVER --quiet >/dev/null
  echo "stopped: $1"
}

echo "Environment: ${environment}"
echo "Acting as:   ${deployer}"
echo "Bucket:      gs://${bucket}"
echo "SQL:         ${sql_instance}"
echo

if [[ "${action}" == "shutdown" ]]; then
  sql_stop "${sql_instance}"
  exit 0
fi

# --- Secrets -----------------------------------------------------------------
# Returns 0 when the secret exists but still has no version.
needs_value() {
  if gc secrets describe "$1" >/dev/null 2>&1; then
    if gc secrets versions list "$1" --limit=1 --format='value(name)' 2>/dev/null | grep -q .; then
      echo "exists: $1"
      return 1
    fi
  else
    gc secrets create "$1" --replication-policy=automatic >/dev/null
    echo "created: $1"
  fi
  return 0
}

# Accepts a file holding the bare key or one with a CLERK_SECRET_KEY= line.
read_clerk_key() {
  local path="${CLERK_KEY_FILE:-${repo_root}/.env/clerk.key.${environment}}"
  if [[ -f "${path}" ]]; then
    if grep -q '^CLERK_SECRET_KEY=' "${path}"; then
      grep -m1 '^CLERK_SECRET_KEY=' "${path}" | cut -d= -f2- | tr -d '\n'
    else
      tr -d '\n' < "${path}"
    fi
    return
  fi
  if [[ -n "${CLERK_KEY_FILE:-}" ]]; then
    echo "No such Clerk key file: ${CLERK_KEY_FILE}" >&2
    return 1
  fi
  local value
  read -rsp "Clerk server key for ${environment} (sk_...): " value >&2
  echo >&2
  printf '%s' "${value}"
}

if needs_value "${db_secret}"; then
  # Hex, not base64: the value goes into a DATABASE_URL, where '/' and '+' are reserved.
  printf '%s' "$(openssl rand -hex 32)" | gc secrets versions add "${db_secret}" --data-file=- >/dev/null
  echo "  added a generated database password"
fi

if needs_value "${clerk_secret}"; then
  clerk_value="$(read_clerk_key)"
  if [[ -z "${clerk_value}" ]]; then
    echo "No Clerk server key supplied for ${clerk_secret}." >&2
    exit 1
  fi
  printf '%s' "${clerk_value}" | gc secrets versions add "${clerk_secret}" --data-file=- >/dev/null
  echo "  added the Clerk server key"
fi

gc secrets add-iam-policy-binding "${db_secret}" \
  --member "serviceAccount:${api_account}" --role roles/secretmanager.secretAccessor >/dev/null
gc secrets add-iam-policy-binding "${clerk_secret}" \
  --member "serviceAccount:chalksmith-web@${project}.iam.gserviceaccount.com" \
  --role roles/secretmanager.secretAccessor >/dev/null

# --- Bucket ------------------------------------------------------------------
if gc storage buckets describe "gs://${bucket}" >/dev/null 2>&1; then
  echo "exists: gs://${bucket}"
else
  gc storage buckets create "gs://${bucket}" --location "${region}" \
    --uniform-bucket-level-access --public-access-prevention
fi
gc storage buckets update "gs://${bucket}" \
  --uniform-bucket-level-access --public-access-prevention \
  --lifecycle-file "${repo_root}/bin/storage-lifecycle.json" >/dev/null
gc storage buckets add-iam-policy-binding "gs://${bucket}" \
  --member "serviceAccount:${api_account}" --role roles/storage.objectAdmin >/dev/null
echo "configured: gs://${bucket}"

# --- Cloud SQL ---------------------------------------------------------------
if gc sql instances describe "${sql_instance}" >/dev/null 2>&1; then
  echo "exists: ${sql_instance}"
else
  # db-f1-micro is Enterprise-only; a project defaulting to Enterprise Plus rejects it.
  backup_flags=(--no-backup)
  if [[ "${environment}" == "prod" ]]; then
    backup_flags=(--backup-start-time=08:00 --retained-backups-count=7 --enable-point-in-time-recovery)
  fi
  gc sql instances create "${sql_instance}" --region "${region}" \
    --database-version POSTGRES_16 --edition ENTERPRISE --tier "${CLOUD_SQL_TIER:-db-f1-micro}" \
    --availability-type ZONAL --storage-type SSD --storage-size 10 --storage-auto-increase \
    "${backup_flags[@]}"
fi

# Databases and users can only be managed while the instance is running, and a
# re-run finds the instance stopped where the first run found it fresh.
sql_start "${sql_instance}"

if ! gc sql databases describe "${database}" --instance "${sql_instance}" >/dev/null 2>&1; then
  gc sql databases create "${database}" --instance "${sql_instance}"
fi

db_password="$(gc secrets versions access latest --secret "${db_secret}")"
if gc sql users list --instance "${sql_instance}" --filter "name=${database_user}" --format 'value(name)' | grep -q .; then
  gc sql users set-password "${database_user}" --instance "${sql_instance}" --password "${db_password}"
else
  gc sql users create "${database_user}" --instance "${sql_instance}" --password "${db_password}"
fi
unset db_password

cat <<EOF

Ready, with ${sql_instance} left running:

  ./bin/debug.sh start                      # local processes against ${sql_instance}
  ./bin/deploy.sh --type=${environment} start
  ./bin/setup.sh ${environment} shutdown             # stop the instance when done for the day
EOF
