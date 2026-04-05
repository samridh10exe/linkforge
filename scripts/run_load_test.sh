#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 6 ]; then
  echo "usage: $0 <profile> <scenario> <users> <spawn_rate> <duration> <short_code>" >&2
  exit 1
fi

PROFILE="$1"
SCENARIO="$2"
USERS="$3"
SPAWN_RATE="$4"
DURATION="$5"
SHORT_CODE="$6"
BASE_URL="${BASE_URL:-http://localhost}"
OUT_DIR="docs/judging/artifacts/load/${PROFILE}/${SCENARIO}"
PREFIX="${OUT_DIR}/u${USERS}"

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

mkdir -p "${OUT_DIR}"

sample_stats() {
  while true; do
    run_docker stats --no-stream --format '{{json .}}' \
      "$(run_compose ps -q web)" \
      "$(run_compose ps -q nginx)" \
      "$(run_compose ps -q postgres)" >> "${PREFIX}_docker_stats.jsonl"
    sleep 1
  done
}

sample_stats &
STATS_PID=$!
cleanup() {
  kill "${STATS_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

SCENARIO="${SCENARIO}" \
READ_SHORT_CODE="${SHORT_CODE}" \
LOAD_USER_ID="${LOAD_USER_ID:-1}" \
uv run locust \
  -f ops/locustfile.py \
  --headless \
  --host "${BASE_URL}" \
  --users "${USERS}" \
  --spawn-rate "${SPAWN_RATE}" \
  --run-time "${DURATION}" \
  --csv "${PREFIX}" \
  --only-summary \
  --exit-code-on-error 0 \
  2>&1 | tee "${PREFIX}_locust.log"

cleanup
trap - EXIT

uv run python scripts/summarize_locust.py "${PREFIX}" | tee "${PREFIX}_summary.pretty.json"
