# MLH PE Hackathon URL Shortener

Flask + Peewee + PostgreSQL URL shortener with:
- evaluator-compatible `GET /health`, `/users`, `/urls`, and `/events` endpoints
- short-code redirect flow with `410` handling for inactive and expired URLs
- Docker + nginx deployment path
- seeded database support from `../Seed Data/`
- load, chaos, and judging evidence under `docs/judging/`

## Quick Start

```bash
cp .env.example .env
docker compose up -d postgres
docker compose exec -T postgres createdb -U postgres hackathon_test
export PATH="$HOME/.local/bin:$PATH"
uv sync --dev
export PYTHONPATH=.
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=postgres
export DATABASE_NAME=hackathon_app
uv run python scripts/bootstrap_db.py
uv run python scripts/seed.py
export DATABASE_NAME=hackathon_test
uv run python scripts/bootstrap_db.py
docker compose up -d --build web nginx
```

## Test

```bash
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH=.
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=postgres
export DATABASE_NAME=hackathon_app
export TEST_DATABASE_NAME=hackathon_test
uv run pytest --cov=app --cov-report=term-missing -v
```

## Proof Scripts

- `./scripts/evaluator_smoke.sh http://localhost`
- `./scripts/run_load_test.sh <profile> <scenario> <users> <spawn_rate> <duration> <short_code>`
- `./scripts/chaos_demo.sh`

## Docs

- `docs/architecture.md`
- `docs/api.md`
- `docs/env.md`
- `docs/deploy.md`
- `docs/load-testing.md`
- `docs/runbook.md`
- `docs/judge-demo.md`
- `docs/judging/`
