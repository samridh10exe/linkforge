# Hamilton Fanbois -- URL Shortener

Flask + Peewee + PostgreSQL URL shortener built for the MLH PE Hackathon 2026.

Deployed on a DigitalOcean Droplet behind nginx with two Gunicorn app containers,
Redis cache on the redirect hot path, and Prometheus metrics.

## Run locally

```bash
cp .env.example .env
docker compose up -d
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/seed.py "Seed Data"
curl http://localhost/health
```

## Run tests

```bash
uv sync --dev
uv run pytest --cov=app --cov-report=term-missing
```

CI runs on every push. Tests require a local PostgreSQL (see `.github/workflows/ci.yml`
for the service container setup).

## API

| Method | Path | Behavior |
|--------|------|----------|
| GET | `/health` | Liveness check, no DB |
| GET | `/ready` | Readiness check, verifies DB |
| POST | `/shorten` | Create short URL |
| GET | `/<short_code>` | 302 redirect (410 if inactive/expired, 404 if missing) |
| POST | `/urls` | Create short URL (evaluator-compatible) |
| GET | `/urls` | List URLs |
| PUT | `/urls/<id>` | Update URL |
| DELETE | `/<short_code>` | Soft delete |
| GET | `/events` | List events |
| GET | `/metrics` | Prometheus text format |

All errors return `{"error": {"code": "...", "message": "...", "request_id": "..."}}`.

Full reference: [docs/api.md](docs/api.md)

## Architecture

nginx load-balances across two Gunicorn workers (web1, web2). Redis caches
resolved short codes with `X-Cache: HIT/MISS` headers. PostgreSQL stores
users, URLs, and events with connection pooling (max 12 connections).

Details: [docs/architecture.md](docs/architecture.md)

## Load test results (droplet)

| VUs | RPS | p50 | p95 | Errors |
|----:|----:|----:|----:|-------:|
| 200 | 135 | 1300ms | 3000ms | 0.00% |
| 500 | 130 | 3500ms | 6300ms | 2.52% |

Full results: [docs/load-testing.md](docs/load-testing.md)

## Further docs

- [docs/deploy.md](docs/deploy.md) -- deploy and rollback
- [docs/env.md](docs/env.md) -- environment variables
- [docs/failure-modes.md](docs/failure-modes.md) -- error scenarios
- [docs/runbook.md](docs/runbook.md) -- incident triage and recovery
- [docs/judge-demo.md](docs/judge-demo.md) -- demo walkthrough
