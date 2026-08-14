#!/usr/bin/env bash
# Create, inspect, or remove the production front door: Cloud Run domain mappings
# and the DNS records those mappings and Clerk require. deploy.sh owns revisions.
#
# Runs as the caller's own account, not the deployer: domain mapping needs Search
# Console ownership verification, which binds to a user rather than to IAM.
#
#   ./bin/domain.sh prod status|start|shutdown
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "${repo_root}"

deploy_env_file="${DEPLOY_ENV_FILE:-${repo_root}/.env/env.deploy}"

# Strict dotenv subset, no shell execution. Names owned by another script are
# skipped, so this shares .env/env.deploy with deploy.sh without shared code.
load_domain_env() {
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
      PROJECT_ID|REGION|DOMAIN|WEB_SERVICE) ;;
      *) continue ;;
    esac
    if [[ -z "${!name+x}" ]]; then
      printf -v "${name}" '%s' "${value}"
      export "${name}"
    fi
  done < "${file}"
}

if [[ -f "${deploy_env_file}" ]]; then
  load_domain_env "${deploy_env_file}"
  echo "Loaded deployment config: ${deploy_env_file}"
fi

environment="${1:-}"
action="${2:-status}"

# deploy.sh ignores DOMAIN for stg, so a staging mapping would never match the
# host routing compiled into the staging image.
if [[ "${environment}" == "stg" ]]; then
  echo "Staging has no custom domain. deploy.sh ignores DOMAIN for stg and compiles" >&2
  echo "the default site domain into the staging web image, so a staging mapping would" >&2
  echo "not match its host routing. Use the run.app URL deploy.sh prints instead." >&2
  exit 1
fi
if [[ "${environment}" != "prod" ]] ||
   [[ "${action}" != "start" && "${action}" != "status" && "${action}" != "shutdown" ]]; then
  echo "Usage: ./bin/domain.sh prod status|start|shutdown" >&2
  echo "  status    report mapping, certificate, and DNS state; exits non-zero until complete" >&2
  echo "  start     verify ownership, create missing mappings, then report what DNS still needs" >&2
  echo "  shutdown  delete the mappings and leave DNS and Clerk records untouched" >&2
  exit 1
fi

for tool in gcloud dig; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "Missing required command: ${tool}" >&2
    exit 1
  fi
done

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "Missing required deployment setting: PROJECT_ID" >&2
  echo "Copy bin/env.deploy.template to .env/env.deploy and replace its placeholders." >&2
  exit 1
fi

# Rejecting a scheme, path, port, space, or comma makes the value safe to
# interpolate into hostnames, DNS queries, and gcloud flags below.
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

region="${REGION:-us-central1}"
web_service="${WEB_SERVICE:-chalksmith-web-prod}"

hosts=("${domain}" "www.${domain}" "app.${domain}")

gc() { gcloud "$@" --project "${PROJECT_ID}" --verbosity=error; }
dm() { gc beta run domain-mappings "$@" --region "${region}"; }

# Ask the zone's own nameserver: a resolver can serve a stale negative answer
# that reads exactly like a missing record.
ns_server="$(dig +short NS "${domain}" 2>/dev/null | head -1 || true)"
ns_server="${ns_server%.}"

dns_lookup() {
  local fqdn="$1" type="$2"
  if [[ -n "${ns_server}" ]]; then
    dig "@${ns_server}" +short "${fqdn}" "${type}" 2>/dev/null || true
  else
    dig +short "${fqdn}" "${type}" 2>/dev/null || true
  fi
}

# Registrar forms want the host relative to the zone; a full hostname there
# produces accounts.example.com.example.com.
relative_host() {
  local fqdn="$1"
  if [[ "${fqdn}" == "${domain}" ]]; then
    printf '@'
  else
    printf '%s' "${fqdn%".${domain}"}"
  fi
}

# Three targets embed a per-instance id known only to the Clerk dashboard, so
# they are matched as <id> patterns instead of becoming a setting.
clerk_records=(
  "CNAME|accounts.${domain}|accounts.clerk.services"
  "CNAME|clerk.${domain}|frontend-api.clerk.services"
  "CNAME|clk._domainkey.${domain}|dkim1.<id>.clerk.services"
  "CNAME|clk2._domainkey.${domain}|dkim2.<id>.clerk.services"
  "CNAME|clkmail.${domain}|mail.<id>.clerk.services"
)

# gcloud writes component-installer progress to stdout, so every line is
# validated; unvalidated, that noise parses as records and reports as wrong ones.
mapping_records() {
  local host="$1" type name rrdata fqdn
  while IFS='|' read -r type name rrdata; do
    case "${type}" in
      A|AAAA|CNAME) ;;
      *) continue ;;
    esac
    [[ -z "${rrdata}" || "${rrdata}" == *[[:space:]]* ]] && continue
    if [[ -z "${name}" || "${name}" == "@" ]]; then
      fqdn="${domain}"
    else
      fqdn="${name}.${domain}"
    fi
    printf '%s|%s|%s\n' "${type}" "${fqdn}" \
      "$(printf '%s' "${rrdata%.}" | tr '[:upper:]' '[:lower:]')"
  done < <(dm describe --domain "${host}" \
    --flatten='status.resourceRecords[]' \
    --format='value[separator="|"](status.resourceRecords.type,status.resourceRecords.name,status.resourceRecords.rrdata)' \
    2>/dev/null || true)
}

mapping_conditions() {
  local host="$1"
  dm describe --domain "${host}" \
    --flatten='status.conditions[]' \
    --format='value[separator="="](status.conditions.type,status.conditions.status)' \
    2>/dev/null | grep -E '^[A-Za-z]+=[A-Za-z]+$' | tr '\n' ' ' || true
}

mapping_exists() {
  dm describe --domain "$1" >/dev/null 2>&1
}

# prepare.sh grants the role; this only checks it. The permission is absent from
# the predefined role definitions, so ask the IAM API rather than read roles.
require_mapping_permission() {
  local token probe account
  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi
  token="$(gcloud auth print-access-token 2>/dev/null || true)"
  if [[ -z "${token}" ]]; then
    return 0
  fi
  probe="$(curl -s -m 15 -X POST \
    -H "Authorization: Bearer ${token}" -H "Content-Type: application/json" \
    -d '{"permissions":["run.domainmappings.create"]}' \
    "https://cloudresourcemanager.googleapis.com/v1/projects/${PROJECT_ID}:testIamPermissions" \
    2>/dev/null || true)"
  if [[ -z "${probe}" || "${probe}" == *run.domainmappings.create* ]]; then
    return 0
  fi
  account="$(gcloud config get-value account 2>/dev/null || echo 'the active account')"
  echo >&2
  echo "${account} cannot create Cloud Run domain mappings in ${PROJECT_ID}." >&2
  echo "Ownership of ${domain} is verified, so only the IAM grant is missing." >&2
  echo "prepare.sh grants it to the human account. Run it, then re-run this:" >&2
  echo >&2
  echo "  ./bin/prepare.sh --project=${PROJECT_ID} --human=${account}" >&2
  exit 1
}

ok_count=0
missing_count=0
wrong_count=0

# Unquoted right-hand side so <id> turned into * matches as a glob.
value_matches() {
  # shellcheck disable=SC2053
  [[ "$1" == ${2//<id>/*} ]]
}

# One lookup per name and type, comparing whole sets: a root mapping needs four
# A records, and checking them one at a time calls an incomplete set wrong.
check_record_set() {
  local type="$1" fqdn="$2" expected_list="$3"
  local found found_list="" expected value hit state=""
  local add="" remove="" missing=0 extra=0

  found="$(dns_lookup "${fqdn}" "${type}")"
  while IFS= read -r value; do
    [[ -z "${value}" ]] && continue
    found_list="${found_list}$(printf '%s' "${value%.}" | tr '[:upper:]' '[:lower:]')"$'\n'
  done <<< "${found}"

  while IFS= read -r expected; do
    [[ -z "${expected}" ]] && continue
    hit=0
    while IFS= read -r value; do
      if [[ -n "${value}" ]] && value_matches "${value}" "${expected}"; then
        hit=1
        break
      fi
    done <<< "${found_list}"
    if [[ "${hit}" -eq 0 ]]; then
      add="${add}${add:+ }${expected}"
      missing=$((missing + 1))
    fi
  done <<< "${expected_list}"

  while IFS= read -r value; do
    [[ -z "${value}" ]] && continue
    hit=0
    while IFS= read -r expected; do
      if [[ -n "${expected}" ]] && value_matches "${value}" "${expected}"; then
        hit=1
        break
      fi
    done <<< "${expected_list}"
    if [[ "${hit}" -eq 0 ]]; then
      remove="${remove}${remove:+ }${value}"
      extra=$((extra + 1))
    fi
  done <<< "${found_list}"

  if [[ "${missing}" -eq 0 && "${extra}" -eq 0 ]]; then
    printf '  %-34s %-5s ok\n' "${fqdn}" "${type}"
    ok_count=$((ok_count + 1))
    return 0
  fi
  if [[ "${missing}" -gt 0 ]]; then
    state="${missing} missing"
    missing_count=$((missing_count + 1))
  fi
  if [[ "${extra}" -gt 0 ]]; then
    state="${state}${state:+, }${extra} extra"
    wrong_count=$((wrong_count + 1))
  fi
  printf '  %-34s %-5s %s\n' "${fqdn}" "${type}" "${state}"
  if [[ -n "${add}" ]]; then
    printf '      add     %s\n' "${add}"
  fi
  if [[ -n "${remove}" ]]; then
    printf '      remove  %s\n' "${remove}"
  fi
  return 0
}

# Every record both sets require, as type|fqdn|rrdata.
required_records=()
collect_required_records() {
  local host line
  required_records=()
  for host in "${hosts[@]}"; do
    while IFS= read -r line; do
      [[ -n "${line}" ]] && required_records+=("${line}")
    done < <(mapping_records "${host}")
  done
  required_records+=("${clerk_records[@]}")
}

print_manual_instructions() {
  local type fqdn rrdata
  echo
  echo "Add these at the authoritative DNS provider for ${domain}."
  echo "Most registrar forms want the relative host and append the domain themselves."
  echo "Targets must match exactly; a proxying provider must serve them unproxied."
  echo "Replace <id> with the instance id shown in Clerk Dashboard -> Domains -> DNS"
  echo "configuration, where a target reads mail.<id>.clerk.services."
  echo
  printf '  %-5s %-18s %-34s %s\n' "TYPE" "HOST" "FULL HOST" "VALUE"
  while IFS='|' read -r type fqdn rrdata; do
    [[ -z "${type}" ]] && continue
    printf '  %-5s %-18s %-34s %s\n' "${type}" "$(relative_host "${fqdn}")" "${fqdn}" "${rrdata}"
  done < <(printf '%s\n' "${required_records[@]}" | sort -u -t"|" -k2,2 -k1,1 -k3,3)
}

report_dns() {
  local type fqdn rrdata key prev_key="" prev_type="" prev_fqdn="" expected=""
  ok_count=0
  missing_count=0
  wrong_count=0
  echo
  if [[ -n "${ns_server}" ]]; then
    echo "DNS, asked directly of ${ns_server}:"
  else
    echo "DNS, asked of the default resolver (no NS record found for ${domain}):"
  fi
  while IFS='|' read -r type fqdn rrdata; do
    [[ -z "${type}" ]] && continue
    key="${type}|${fqdn}"
    if [[ "${key}" == "${prev_key}" ]]; then
      expected="${expected}"$'\n'"${rrdata}"
      continue
    fi
    if [[ -n "${prev_key}" ]]; then
      check_record_set "${prev_type}" "${prev_fqdn}" "${expected}"
    fi
    prev_key="${key}"
    prev_type="${type}"
    prev_fqdn="${fqdn}"
    expected="${rrdata}"
  done < <(printf '%s\n' "${required_records[@]}" | sort -u -t"|" -k2,2 -k1,1 -k3,3)
  if [[ -n "${prev_key}" ]]; then
    check_record_set "${prev_type}" "${prev_fqdn}" "${expected}"
  fi
}

unmapped_count=0

report_mappings() {
  local host conditions
  unmapped_count=0
  echo
  echo "Cloud Run domain mappings in ${region}:"
  for host in "${hosts[@]}"; do
    if mapping_exists "${host}"; then
      conditions="$(mapping_conditions "${host}")"
      printf '  %-34s %s\n' "${host}" "${conditions:-mapped}"
    else
      printf '  %-34s not mapped\n' "${host}"
      unmapped_count=$((unmapped_count + 1))
    fi
  done
}

# Non-zero until every hostname is mapped and every record resolves; the records
# can all pass while no mapping exists at all.
summarize() {
  local incomplete=0
  echo
  if [[ "${missing_count}" -ne 0 || "${wrong_count}" -ne 0 ]]; then
    echo "${ok_count} ok, ${missing_count} incomplete, ${wrong_count} with extra records."
    echo "Apply the add and remove lines above exactly, then allow DNS to propagate and"
    echo "re-run ./bin/domain.sh prod status."
    incomplete=1
  else
    echo "All ${ok_count} required record sets resolve correctly."
  fi
  if [[ "${unmapped_count}" -ne 0 ]]; then
    echo "${unmapped_count} of ${#hosts[@]} hostnames have no Cloud Run domain mapping, so the"
    echo "custom domain is not serving yet. Run ./bin/domain.sh prod start to create them"
    echo "and print the DNS records they need."
    incomplete=1
  fi
  echo "Re-run verification in the Clerk dashboard; Clerk does not re-check on its own."
  return "${incomplete}"
}

echo "Environment: prod"
echo "Domain:      ${domain}"
echo "Service:     ${web_service} in ${region}"
echo "Acting as:   $(gcloud config get-value account 2>/dev/null || echo 'unknown account')"

if [[ "${action}" == "shutdown" ]]; then
  echo
  read -rp "Delete the Cloud Run domain mappings for ${domain} and take the custom domain offline? Type the domain to confirm: " answer
  [[ "${answer}" == "${domain}" ]] || { echo "Aborted." >&2; exit 1; }
  for host in "${hosts[@]}"; do
    if mapping_exists "${host}"; then
      dm delete --domain "${host}" --quiet
      echo "deleted: ${host}"
    else
      echo "absent:  ${host}"
    fi
  done
  cat <<EOF

DNS records and Clerk records survive; delete them at the DNS provider separately.
The Cloud Run services are untouched. Remove them with ./bin/deploy.sh prod shutdown.
EOF
  exit 0
fi

if [[ "${action}" == "start" ]]; then
  if ! gc run services describe "${web_service}" --region "${region}" >/dev/null 2>&1; then
    echo "Missing Cloud Run service ${web_service}. Run ./bin/deploy.sh prod start first." >&2
    exit 1
  fi

  # Ownership is per Google account through Search Console, so a failure here has
  # no IAM explanation. Checking first turns it into one actionable command.
  if verified="$(gc domains list-user-verified --format='value(id)' 2>/dev/null)"; then
    if ! printf '%s\n' "${verified}" | grep -qxF "${domain}"; then
      echo >&2
      echo "${domain} is not verified for $(gcloud config get-value account 2>/dev/null)." >&2
      echo "Run 'gcloud domains verify ${domain}' and complete the Search Console flow," >&2
      echo "then re-run this command. Verifying the root also covers www and app." >&2
      exit 1
    fi
  else
    echo
    echo "Could not list verified domains; continuing. If mapping creation fails,"
    echo "run 'gcloud domains verify ${domain}' first."
  fi

  require_mapping_permission

  echo
  echo "Cloud Run domain mappings in ${region}:"
  for host in "${hosts[@]}"; do
    if mapping_exists "${host}"; then
      echo "  exists:  ${host}"
    else
      # No --force-override: a hostname mapped to another service is worth a look.
      dm create --service "${web_service}" --domain "${host}" >/dev/null
      echo "  created: ${host}"
    fi
  done
fi

collect_required_records
print_manual_instructions
report_mappings
report_dns
summarize
