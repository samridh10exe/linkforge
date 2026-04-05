#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost}"
OUT_DIR="${OUT_DIR:-docs/judging/artifacts/evaluator}"
mkdir -p "${OUT_DIR}"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="${OUT_DIR}/evaluator-smoke-${STAMP}.log"

request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local headers=()
  if [ -n "${body}" ]; then
    headers=(-H 'Content-Type: application/json')
  fi
  local response
  response="$(curl -sS -X "${method}" "${BASE_URL}${path}" "${headers[@]}" ${body:+-d "${body}"} \
    -w $'\nHTTP_STATUS:%{http_code}')"
  local status
  status="$(printf '%s' "${response}" | awk -F: '/HTTP_STATUS/ {print $2}')"
  local payload
  payload="$(printf '%s' "${response}" | sed '/HTTP_STATUS:/d')"
  printf '%s %s -> %s\n%s\n\n' "${method}" "${path}" "${status}" "${payload}" | tee -a "${LOG_FILE}" >&2
  printf '%s' "${payload}"
}

health_body="$(request GET /health)"

bulk_csv="$(mktemp)"
cat > "${bulk_csv}" <<'CSV'
id,username,email,created_at
900001,bulkproof1,bulkproof1@example.com,2026-04-04T12:00:00
900002,bulkproof2,bulkproof2@example.com,2026-04-04T12:00:01
CSV
bulk_response="$(curl -sS -X POST "${BASE_URL}/users/bulk" \
  -F "file=@${bulk_csv};type=text/csv" \
  -w $'\nHTTP_STATUS:%{http_code}')"
rm -f "${bulk_csv}"
bulk_status="$(printf '%s' "${bulk_response}" | awk -F: '/HTTP_STATUS/ {print $2}')"
bulk_body="$(printf '%s' "${bulk_response}" | sed '/HTTP_STATUS:/d')"
printf 'POST /users/bulk -> %s\n%s\n\n' "${bulk_status}" "${bulk_body}" | tee -a "${LOG_FILE}" >&2

users_body="$(request GET /users)"
user_create="$(request POST /users '{"username":"smoke-user","email":"smoke-user@example.com"}')"
user_id="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${user_create}")"
user_get="$(request GET "/users/${user_id}")"
user_update="$(request PUT "/users/${user_id}" '{"username":"smoke-user-updated"}')"

url_create="$(request POST /urls "{\"user_id\":${user_id},\"original_url\":\"https://example.com/evaluator-smoke\",\"title\":\"Evaluator Smoke\"}")"
url_id="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${url_create}")"
short_code="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["short_code"])' <<<"${url_create}")"
urls_list="$(request GET /urls)"
url_get="$(request GET "/urls/${url_id}")"
url_update="$(request PUT "/urls/${url_id}" '{"title":"Evaluator Smoke Updated","is_active":false}')"
events_body="$(request GET /events)"

cat <<EOF | tee -a "${LOG_FILE}"
SUMMARY
health=${health_body}
bulk=${bulk_body}
user_id=${user_id}
url_id=${url_id}
short_code=${short_code}
EOF
