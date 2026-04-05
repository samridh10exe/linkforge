#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
OUT_DIR="${OUT_DIR:-docs/judging/artifacts/chaos}"
mkdir -p "${OUT_DIR}"
START_TS="$(date +%Y%m%d-%H%M%S)"
LOG_START="$(date -Iseconds)"
LOG_FILE="${OUT_DIR}/chaos-${START_TS}.log"

if docker info >/dev/null 2>&1; then
  run_docker() {
    docker "$@"
  }
  run_compose() {
    docker compose "$@"
  }
elif sg docker -c 'docker info >/dev/null 2>&1'; then
  run_docker() {
    local cmd="docker"
    local arg
    for arg in "$@"; do
      cmd+=" $(printf '%q' "${arg}")"
    done
    sg docker -c "${cmd}"
  }
  run_compose() {
    local cmd="docker compose"
    local arg
    for arg in "$@"; do
      cmd+=" $(printf '%q' "${arg}")"
    done
    sg docker -c "${cmd}"
  }
else
  run_docker() {
    sudo docker "$@"
  }
  run_compose() {
    sudo docker compose "$@"
  }
fi

log() {
  echo "[$(date -Iseconds)] $*" | tee -a "${LOG_FILE}"
}

http_status() {
  curl --max-time 5 -sS -o /tmp/chaos-body.$$ -w "%{http_code}" "$1" || true
}

create_short_code() {
  local payload
  payload="$(curl -sS -X POST "${BASE_URL}/urls" \
    -H 'Content-Type: application/json' \
    -d "{\"user_id\":1,\"original_url\":\"https://example.com/chaos/${START_TS}\",\"title\":\"Chaos ${START_TS}\"}")"
  python3 -c 'import json,sys; print(json.loads(sys.stdin.read())["short_code"])' <<<"${payload}"
}

wait_for_health() {
  local max_attempts="${1:-30}"
  local attempt=1
  while [ "${attempt}" -le "${max_attempts}" ]; do
    code="$(curl --max-time 5 -sS -o /tmp/health.$$ -w "%{http_code}" "${BASE_URL}/health" || true)"
    body="$(cat /tmp/health.$$ 2>/dev/null || true)"
    if [ "${code}" = "200" ] && grep -q '"status":"ok"' <<<"${body}"; then
      log "health recovered: ${body}"
      return 0
    fi
    sleep 1
    attempt=$((attempt + 1))
  done
  return 1
}

SHORT_CODE="$(create_short_code)"
log "created short code ${SHORT_CODE}"

SCENARIO=read-heavy READ_SHORT_CODE="${SHORT_CODE}" uv run locust \
  -f ops/locustfile.py \
  --headless \
  --host "${BASE_URL}" \
  --users 80 \
  --spawn-rate 20 \
  --run-time 45s \
  --only-summary \
  --exit-code-on-error 0 > "${OUT_DIR}/web-chaos-locust-${START_TS}.log" 2>&1 &
READ_LOAD_PID=$!

sleep 8
log "killing web container under read load"
run_docker exec "$(run_compose ps -q web)" sh -lc 'kill -9 1' >> "${LOG_FILE}" 2>&1 || true
wait_for_health 45
REDIRECT_CODE="$(curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}/${SHORT_CODE}" || true)"
log "redirect status after web recovery: ${REDIRECT_CODE}"
wait "${READ_LOAD_PID}"
log "web chaos load run complete"

SCENARIO=mixed-evaluator READ_SHORT_CODE="${SHORT_CODE}" uv run locust \
  -f ops/locustfile.py \
  --headless \
  --host "${BASE_URL}" \
  --users 40 \
  --spawn-rate 10 \
  --run-time 45s \
  --only-summary \
  --exit-code-on-error 0 > "${OUT_DIR}/db-chaos-locust-${START_TS}.log" 2>&1 &
DB_LOAD_PID=$!

sleep 8
log "stopping postgres under mixed evaluator load"
run_compose stop postgres >> "${LOG_FILE}" 2>&1
sleep 2
HEALTH_CODE="$(http_status "${BASE_URL}/health")"
HEALTH_BODY="$(cat /tmp/chaos-body.$$ 2>/dev/null || true)"
log "health during db outage: status=${HEALTH_CODE} body=${HEALTH_BODY}"
sleep 3
run_compose start postgres >> "${LOG_FILE}" 2>&1
run_compose exec -T postgres sh -lc 'until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do sleep 1; done' >> "${LOG_FILE}" 2>&1
wait_for_health 45
READY_RECOVERY_CODE="$(http_status "${BASE_URL}/ready")"
READY_RECOVERY_BODY="$(cat /tmp/chaos-body.$$ 2>/dev/null || true)"
log "ready after db recovery: status=${READY_RECOVERY_CODE} body=${READY_RECOVERY_BODY}"
USERS_RECOVERY_CODE="$(http_status "${BASE_URL}/users")"
log "users after db recovery: status=${USERS_RECOVERY_CODE}"
wait "${DB_LOAD_PID}"
log "db chaos load run complete"

WEB_LOGS="$(run_compose logs web --since "${LOG_START}" 2>&1 || true)"
if grep -q "Traceback" <<<"${WEB_LOGS}"; then
  log "traceback detected in recent web logs"
  exit 1
fi
log "no traceback detected in recent web logs"

log "chaos demo finished"
