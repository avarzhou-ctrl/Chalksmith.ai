#!/usr/bin/env bash
# One-time project preparation, run by the human deployment account: enables the
# APIs, creates the shared service accounts, and grants every environment-independent
# role. Per-environment resources belong to setup.sh. Safe to re-run.
#
#   ./bin/prepare.sh --project=PROJECT_ID [--human=EMAIL]
set -euo pipefail

project="${PROJECT_ID:-}"
human=""
for arg in "$@"; do
  case "${arg}" in
    --project=*) project="${arg#*=}" ;;
    --human=*) human="${arg#*=}" ;;
    *) echo "Unknown argument: ${arg}" >&2; exit 1 ;;
  esac
done

if [[ -z "${project}" ]]; then
  echo "Missing --project=PROJECT_ID (or PROJECT_ID in the environment)." >&2
  exit 1
fi
if [[ -z "${human}" ]]; then
  human="$(gcloud config get-value account 2>/dev/null)"
fi
if [[ -z "${human}" || "${human}" == "(unset)" ]]; then
  echo "Cannot determine the human account; pass --human=EMAIL." >&2
  exit 1
fi

deployer="chalksmith-deployer@${project}.iam.gserviceaccount.com"
api_account="chalksmith-api@${project}.iam.gserviceaccount.com"

echo "Project: ${project}"
echo "Human:   ${human}"
echo

gcloud config set project "${project}"

# iamcredentials backs both impersonation and the signBlob call behind signed URLs.
gcloud services enable \
  artifactregistry.googleapis.com cloudbuild.googleapis.com run.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com storage.googleapis.com \
  iamcredentials.googleapis.com aiplatform.googleapis.com \
  --project "${project}"

create_account() {
  local name="$1" display="$2"
  if gcloud iam service-accounts describe "${name}@${project}.iam.gserviceaccount.com" \
    --project "${project}" >/dev/null 2>&1; then
    echo "exists: ${name}"
  else
    gcloud iam service-accounts create "${name}" --project "${project}" --display-name "${display}"
  fi
}

grant_project_role() {
  gcloud projects add-iam-policy-binding "${project}" \
    --member "$1" --role "$2" --condition=None >/dev/null
  echo "granted: $2 -> $1"
}

create_account chalksmith-deployer "Chalksmith deployment and build"
create_account chalksmith-api      "Chalksmith API runtime"
create_account chalksmith-renderer "Chalksmith renderer runtime"
create_account chalksmith-web      "Chalksmith web runtime"

# The deployer is also the Cloud Build build account, which is why it needs
# logging.logWriter: a build naming its own service account writes its own logs.
for role in \
  roles/serviceusage.serviceUsageAdmin \
  roles/resourcemanager.projectIamAdmin \
  roles/iam.serviceAccountAdmin \
  roles/iam.serviceAccountUser \
  roles/artifactregistry.admin \
  roles/storage.admin \
  roles/secretmanager.admin \
  roles/cloudsql.admin \
  roles/cloudbuild.builds.editor \
  roles/run.admin \
  roles/logging.logWriter; do
  grant_project_role "serviceAccount:${deployer}" "${role}"
done

# Bucket and secret bindings differ per environment and are granted by setup.sh.
grant_project_role "serviceAccount:${api_account}" roles/cloudsql.client
grant_project_role "serviceAccount:${api_account}" roles/aiplatform.user

# debug.sh runs as the human account: it connects to the staging instance through
# the proxy and reads its password. Starting and stopping it is setup.sh's job.
grant_project_role "user:${human}" roles/cloudsql.client
grant_project_role "user:${human}" roles/secretmanager.secretAccessor

# Signing a GCS URL means the API account calls signBlob as itself.
gcloud iam service-accounts add-iam-policy-binding "${api_account}" \
  --project "${project}" --member "serviceAccount:${api_account}" \
  --role roles/iam.serviceAccountTokenCreator >/dev/null
echo "granted: roles/iam.serviceAccountTokenCreator -> ${api_account} (on itself)"

# Without this the human account can manage the deployer but cannot run one command as it.
gcloud iam service-accounts add-iam-policy-binding "${deployer}" \
  --project "${project}" --member "user:${human}" \
  --role roles/iam.serviceAccountTokenCreator >/dev/null
echo "granted: roles/iam.serviceAccountTokenCreator -> ${human} (on ${deployer})"

cat <<EOF

Prepared. Next, create one environment's resources:

  ./bin/setup.sh stg
EOF
