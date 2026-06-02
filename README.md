# url-shortener

`url-shortener` is a Flask service that stores short links in PostgreSQL, caches redirects in Redis, and exposes Prometheus metrics for load-test and incident drills.

## Install

```bash
cp .env.example .env
docker compose up -d
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/seed.py "Seed Data"
```

## Usage

```bash
$ curl -s http://localhost/health
{"status":"ok"}
```

```bash
$ curl -I http://localhost/tdmg9e
HTTP/1.1 302 FOUND
Location: https://hackstack.io/urban/meadow/1
X-Cache: MISS
```

```bash
uv sync --dev
uv run pytest --cov=app --cov-report=term-missing
```

## How It Works

nginx load-balances across two Gunicorn app containers. PostgreSQL stores users, URLs, and events. Redis caches resolved short codes on the redirect path and marks responses with `X-Cache: HIT` or `X-Cache: MISS`. `docs/runbook.md`, `docs/failure-modes.md`, and `docs/load-testing.md` cover the operational paths.
