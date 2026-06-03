#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost}"
OUT_DIR="${OUT_DIR:-docs/judging/artifacts/evaluator}"
mkdir -p "${OUT_DIR}"
STAMP="$(date +%Y%m%d-%H%M%S)"
RUN_ID="$(date +%Y%m%d%H%M%S)-$$"
LOG_FILE="${OUT_DIR}/evaluator-smoke-${STAMP}.log"

request() {
  local method="$1"
  local path="$2"
  local body="${3:-}"
  local response
  if [ -n "${body}" ]; then
    response="$(curl -sS -X "${method}" "${BASE_URL}${path}" \
      -H 'Content-Type: application/json' \
      -d "${body}" \
      -w $'\nHTTP_STATUS:%{http_code}')"
  else
    response="$(curl -sS -X "${method}" "${BASE_URL}${path}" \
      -w $'\nHTTP_STATUS:%{http_code}')"
  fi
  local status
  status="$(printf '%s' "${response}" | awk -F: '/HTTP_STATUS/ {print $2}')"
  local payload
  payload="$(printf '%s' "${response}" | sed '/HTTP_STATUS:/d')"
  printf '%s %s -> %s\n%s\n\n' "${method}" "${path}" "${status}" "${payload}" | tee -a "${LOG_FILE}" >&2
  if [[ ! "${status}" =~ ^2 ]]; then
    return 1
  fi
  printf '%s' "${payload}"
}

health_body="$(request GET /health)"

bulk_csv="$(mktemp)"
cat > "${bulk_csv}" <<'CSV'
username,email,created_at
CSV
cat >> "${bulk_csv}" <<CSV
bulkproof-${RUN_ID}-1,bulkproof-${RUN_ID}-1@example.com,2026-04-04T12:00:00
bulkproof-${RUN_ID}-2,bulkproof-${RUN_ID}-2@example.com,2026-04-04T12:00:01
CSV
bulk_response="$(curl -sS -X POST "${BASE_URL}/users/bulk" \
  -F "file=@${bulk_csv};type=text/csv" \
  -w $'\nHTTP_STATUS:%{http_code}')"
rm -f "${bulk_csv}"
bulk_status="$(printf '%s' "${bulk_response}" | awk -F: '/HTTP_STATUS/ {print $2}')"
bulk_body="$(printf '%s' "${bulk_response}" | sed '/HTTP_STATUS:/d')"
printf 'POST /users/bulk -> %s\n%s\n\n' "${bulk_status}" "${bulk_body}" | tee -a "${LOG_FILE}" >&2
if [[ ! "${bulk_status}" =~ ^2 ]]; then
  exit 1
fi

request GET '/users?page=1&per_page=3' >/dev/null
user_create="$(request POST /users "{\"username\":\"smoke-user-${RUN_ID}\",\"email\":\"smoke-user-${RUN_ID}@example.com\"}")"
user_id="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${user_create}")"
request GET "/users/${user_id}" >/dev/null
request PUT "/users/${user_id}" "{\"username\":\"smoke-user-${RUN_ID}-updated\"}" >/dev/null

url_create="$(request POST /urls "{\"user_id\":${user_id},\"original_url\":\"https://example.com/evaluator-smoke/${RUN_ID}\",\"title\":\"Evaluator Smoke\"}")"
url_id="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["id"])' <<<"${url_create}")"
short_code="$(python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["short_code"])' <<<"${url_create}")"
request GET '/urls?page=1&per_page=3' >/dev/null
request GET "/urls/${url_id}" >/dev/null
request PUT "/urls/${url_id}" '{"title":"Evaluator Smoke Updated","is_active":false}' >/dev/null
request GET '/events?page=1&per_page=3' >/dev/null

cat <<EOF | tee -a "${LOG_FILE}"
SUMMARY
health=${health_body}
bulk=${bulk_body}
user_id=${user_id}
url_id=${url_id}
short_code=${short_code}
EOF
