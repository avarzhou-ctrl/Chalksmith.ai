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
    gc sql operations wait ${ops} --timeout=unlimited >/dev/null
  fi
}

# Submit patches asynchronously so gcloud's shorter synchronous wait cannot
# report failure while Cloud SQL is still completing a valid operation.
sql_set_activation_policy() {
  local operation
  operation="$(gc sql instances patch "$1" --activation-policy="$2" --async \
    --quiet --format='value(name)')"
  if [[ -z "${operation}" ]]; then
    echo "Cloud SQL returned no operation for $1 activation policy $2." >&2
    return 1
  fi
  echo "waiting for $1 activation policy to become $2"
  gc sql operations wait "${operation}" --timeout=unlimited >/dev/null
}

sql_start() {
  sql_drain "$1"
  if [[ "$(sql_state "$1")" != "RUNNABLE" ]]; then
    sql_set_activation_policy "$1" ALWAYS
    until [[ "$(sql_state "$1")" == "RUNNABLE" ]]; do
      echo "waiting for $1 to become RUNNABLE"
      sleep 10
    done
  fi
  echo "running: $1"
}

sql_stop() {
  sql_drain "$1"
  sql_set_activation_policy "$1" NEVER
  echo "stopped: $1"
}

echo "Environment: ${environment}"
echo "Acting as:   ${deployer}"
echo "Bucket:      gs://${bucket}"
echo "SQL:         ${sql_instance}"
echo

# gcloud asks for periodic reauth on its first call. Force it here, where the
# prompt is visible, instead of inside a probe whose output is captured.
gcloud auth print-access-token >/dev/null

# Probes once ran with their output discarded, which swallowed that reauth prompt:
# the failed read looked like "the resource is absent" and the run minted a second
# database password over the working one. Only a real not-found counts as absent.
probe_output=""
gc_probe() {
  if probe_output="$(gc "$@" 2>&1)"; then
    return 0
  fi
  case "${probe_output}" in
    *NOT_FOUND*|*"HTTPError 404"*|*"not found: 404"*) probe_output=""; return 1 ;;
  esac
  echo "${probe_output}" >&2
  echo "Cannot read the current state of ${project}; refusing to guess at it." >&2
  exit 1
}

if [[ "${action}" == "shutdown" ]]; then
  sql_stop "${sql_instance}"
  exit 0
fi

# --- Secrets -----------------------------------------------------------------
ensure_secret() {
  if gc_probe secrets describe "$1"; then
    return 0
  fi
  gc secrets create "$1" --replication-policy=automatic >/dev/null
  echo "created: $1"
}

# True when the secret exists and already holds at least one version.
secret_has_value() {
  gc_probe secrets describe "$1" || return 1
  gc_probe secrets versions list "$1" --limit=1 --format='value(name)' &&
    [[ -n "${probe_output}" ]]
}

# Adds a version only when the local value differs. Not used for the database
# password: it is generated once and the Cloud SQL user is created from it.
sync_secret_value() {
  local name="$1" value="$2"
  ensure_secret "${name}"
  if gc_probe secrets versions access latest --secret "${name}" &&
     [[ "${probe_output}" == "${value}" ]]; then
    echo "current: ${name}"
    return 0
  fi
  printf '%s' "${value}" | gc secrets versions add "${name}" --data-file=- >/dev/null
  echo "  added a new version of ${name}"
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

ensure_secret "${db_secret}"
if secret_has_value "${db_secret}"; then
  echo "exists: ${db_secret}"
else
  # Hex, not base64: the value goes into a DATABASE_URL, where '/' and '+' are reserved.
  printf '%s' "$(openssl rand -hex 32)" | gc secrets versions add "${db_secret}" --data-file=- >/dev/null
  echo "  added a generated database password"
fi

# With a key file present the local value is authoritative; without one, an
# already-populated secret is left alone rather than prompted for.
clerk_key_file="${CLERK_KEY_FILE:-${repo_root}/.env/clerk.key.${environment}}"
if [[ -f "${clerk_key_file}" ]] || ! secret_has_value "${clerk_secret}"; then
  clerk_value="$(read_clerk_key)"
  if [[ -z "${clerk_value}" ]]; then
    echo "No Clerk server key supplied for ${clerk_secret}." >&2
    exit 1
  fi
  sync_secret_value "${clerk_secret}" "${clerk_value}"
else
  echo "exists: ${clerk_secret}"
fi

gc secrets add-iam-policy-binding "${db_secret}" \
  --member "serviceAccount:${api_account}" --role roles/secretmanager.secretAccessor >/dev/null
gc secrets add-iam-policy-binding "${clerk_secret}" \
  --member "serviceAccount:chalksmith-web@${project}.iam.gserviceaccount.com" \
  --role roles/secretmanager.secretAccessor >/dev/null

# --- Bucket ------------------------------------------------------------------
if gc_probe storage buckets describe "gs://${bucket}"; then
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
if gc_probe sql instances describe "${sql_instance}"; then
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

if ! gc_probe sql databases describe "${database}" --instance "${sql_instance}"; then
  gc sql databases create "${database}" --instance "${sql_instance}"
fi

db_password="$(gc secrets versions access latest --secret "${db_secret}")"
if gc_probe sql users list --instance "${sql_instance}" --filter "name=${database_user}" --format 'value(name)' &&
   [[ -n "${probe_output}" ]]; then
  gc sql users set-password "${database_user}" --instance "${sql_instance}" --password "${db_password}"
else
  gc sql users create "${database_user}" --instance "${sql_instance}" --password "${db_password}"
fi
unset db_password

cat <<EOF

Ready, with ${sql_instance} left running:

  ./bin/debug.sh start              # local processes against ${sql_instance}
  ./bin/deploy.sh ${environment} start
  ./bin/setup.sh ${environment} shutdown    # stop the instance when done for the day
EOF
