# Judge Demo Script

## Setup

```bash
docker compose up -d --build
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/seed.py "Seed Data"
```

## Evaluator contract

```bash
./scripts/evaluator_smoke.sh http://localhost
```

Shows: `GET /health` returns 200, user CRUD, URL CRUD, event listing.

## Load proof

Artifact directories:
- `docs/judging/artifacts/load/baseline/`
- `docs/judging/artifacts/load/tuned/`
- `docs/judging/artifacts/load/breakpoint/`

Key results: mixed-flow p95 improved from 460ms to 400ms after tuning,
write-heavy p95 from 180ms to 120ms, read-heavy stayed error-free.

## Chaos proof

```bash
./scripts/chaos_demo.sh
```

Shows: web process crash under load, health recovers, redirects resume,
DB outage returns 503 on data routes, recovery after DB returns,
no tracebacks in logs.
