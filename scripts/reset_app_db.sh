#!/usr/bin/env bash
set -euo pipefail

if docker info >/dev/null 2>&1; then
  run_compose() {
    docker compose "$@"
  }
elif sg docker -c 'docker info >/dev/null 2>&1'; then
  run_compose() {
    local cmd="docker compose"
    local arg
    for arg in "$@"; do
      cmd+=" $(printf '%q' "${arg}")"
    done
    sg docker -c "${cmd}"
  }
else
  run_compose() {
    sudo docker compose "$@"
  }
fi

export PATH="${HOME}/.local/bin:${PATH}"
export PYTHONPATH=.
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=postgres
export DATABASE_NAME=hackathon_app

run_compose stop web nginx >/dev/null 2>&1 || true
run_compose exec -T postgres dropdb -U postgres --if-exists hackathon_app
run_compose exec -T postgres createdb -U postgres hackathon_app
uv run python scripts/bootstrap_db.py >/dev/null
uv run python scripts/seed.py >/dev/null
run_compose up -d web nginx >/dev/null

until curl -fsS http://localhost/health >/dev/null; do
  sleep 1
done

echo "app database reset and reseeded"
