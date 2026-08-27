#!/usr/bin/env bash
# Run the full stack locally against the staging Cloud SQL instance and bucket:
# the Cloud SQL Auth Proxy plus the renderer, API, and Next.js processes.
#
# --local swaps both for this machine: artifacts in .env/storage served by the
# API, records in .env SQLite, no proxy. Clerk sign-in and Vertex are untouched.
#
# "shutdown" stops those four only; ./bin/setup.sh stg shutdown stops the instance.
#
#   ./bin/debug.sh start [--local] | shutdown
set -euo pipefail

usage() {
  echo "Usage: ./bin/debug.sh start [--local] | shutdown" >&2
  exit 1
}

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_root}"

action="${1:-}"
shift || true
local_mode=0
for argument in "$@"; do
  case "${argument}" in
    --local) local_mode=1 ;;
    *) usage ;;
  esac
done
if [[ "${action}" != "start" && "${action}" != "shutdown" ]]; then
  usage
fi

project="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
region="${REGION:-us-central1}"
sql_instance="chalksmith-postgres-stg"
bucket="chalksmith-gcs-stg"
run_dir=".env/run"
mode_file="${run_dir}/mode"
storage_dir=".env/storage"
local_database_url="sqlite:///./.env/chalksmith.local.db"

stop_pid() {
  local name="$1" file="${run_dir}/$1.pid"
  [[ -f "${file}" ]] || return 0
  local pid; pid="$(cat "${file}")"
  if kill -0 "${pid}" 2>/dev/null; then
    # uv and npm each wrap the real server, so the child has to go first.
    pkill -P "${pid}" 2>/dev/null || true
    kill "${pid}" 2>/dev/null || true
    echo "stopped: ${name} (${pid})"
  fi
  rm -f "${file}"
}

any_running() {
  local name
  for name in web api renderer proxy; do
    if [[ -f "${run_dir}/${name}.pid" ]] && kill -0 "$(cat "${run_dir}/${name}.pid")" 2>/dev/null; then
      return 0
    fi
  done
  return 1
}

start_pid() {
  local name="$1"; shift
  if [[ -f "${run_dir}/${name}.pid" ]] && kill -0 "$(cat "${run_dir}/${name}.pid")" 2>/dev/null; then
    echo "running: ${name}"
    return 0
  fi
  nohup "$@" >"${run_dir}/${name}.log" 2>&1 &
  echo $! >"${run_dir}/${name}.pid"
  echo "started: ${name} (pid $!, log ${run_dir}/${name}.log)"
}

if [[ "${action}" == "shutdown" ]]; then
  for name in web api renderer proxy; do stop_pid "${name}"; done
  rm -f "${mode_file}"
  exit 0
fi

# Both modes read this file for the LLM, renderer, and origin settings.
if [[ ! -f .env/env.local ]]; then
  echo "Missing .env/env.local. See doc/GCP.md section 3.1.2." >&2
  exit 1
fi
if [[ "${local_mode}" == 0 ]]; then
  # Starting the instance is pointless while the backend still talks to SQLite.
  if ! grep -q '^DATABASE_URL=postgresql' .env/env.local; then
    echo "DATABASE_URL in .env/env.local does not point at the proxy. See doc/GCP.md section 3.1.2." >&2
    exit 1
  fi
  if ! command -v cloud-sql-proxy >/dev/null 2>&1; then
    echo "Missing cloud-sql-proxy: https://cloud.google.com/sql/docs/postgres/sql-proxy" >&2
    exit 1
  fi
fi
mkdir -p "${run_dir}"

# Processes read their mode at startup, so start_pid would otherwise report a
# stack from the other mode as already running.
mode="staging"
if [[ "${local_mode}" == 1 ]]; then
  mode="local"
fi
if [[ -f "${mode_file}" && "$(cat "${mode_file}")" != "${mode}" ]] && any_running; then
  echo "Already running in $(cat "${mode_file}") mode. Run ./bin/debug.sh shutdown first." >&2
  exit 1
fi
echo "${mode}" >"${mode_file}"

if [[ "${local_mode}" == 1 ]]; then
  mkdir -p "${storage_dir}"
  # python-dotenv never overwrites an already-set variable, so env.local stays
  # correct for the staging mode.
  export LOCAL_STORAGE_DIR="${repo_root}/${storage_dir}"
  export DATABASE_URL="${local_database_url}"
fi

# ADC is a separate credential from `gcloud auth login`, and GOOGLE_CLOUD_PROJECT
# overrides the project it reports.
adc_project="$(uv run --project backend python -c \
  "import google.auth; c, p = google.auth.default(); print(p or '')" 2>/dev/null)" || {
  echo "No Application Default Credentials. Run: gcloud auth application-default login" >&2
  exit 1
}
echo "ADC: ${adc_project:-<none>}"
if [[ -n "${adc_project}" && "${adc_project}" != "${project}" ]]; then
  echo "warning: ADC resolves ${adc_project}, not ${project}; unset GOOGLE_CLOUD_PROJECT or set it to ${project}" >&2
fi
if [[ "${local_mode}" == 1 ]]; then
  echo "local: lessons in ${storage_dir}, records in ${local_database_url}"
else
  gcloud storage ls "gs://${bucket}" >/dev/null && echo "bucket: gs://${bucket} reachable"

  # setup.sh owns the instance lifecycle; this only checks.
  sql_state="$(gcloud sql instances describe "${sql_instance}" --project "${project}" --format='value(state)')" || {
    echo "If that was a permission error, $(gcloud config get-value account 2>/dev/null) needs" >&2
    echo "roles/cloudsql.client; run ./bin/prepare.sh to grant it." >&2
    exit 1
  }
  if [[ "${sql_state}" != "RUNNABLE" ]]; then
    echo "${sql_instance} is ${sql_state}. Run ./bin/setup.sh stg start first." >&2
    exit 1
  fi

  start_pid proxy cloud-sql-proxy "${project}:${region}:${sql_instance}" --port 5432
fi
start_pid renderer env APP_ROLE=renderer uv run --project backend \
  uvicorn backend.app.renderer_main:renderer_app --reload --port 8081
start_pid api uv run --project backend uvicorn backend.app.main:app --reload --port 8000
start_pid web npm --prefix frontend run dev

if [[ "${local_mode}" == 1 ]]; then
  lessons="${storage_dir}"
  records="${local_database_url}"
else
  lessons="gs://${bucket}"
  records="${sql_instance} via cloud-sql-proxy"
fi

cat <<EOF

Web      http://localhost:3000
API docs http://localhost:8000/docs
Health   http://localhost:8000/ready, http://localhost:8081/ready
Lessons  ${lessons}
Records  ${records}

Stop everything with ./bin/debug.sh shutdown
EOF
