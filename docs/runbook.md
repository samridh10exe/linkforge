# Runbook

## Fast Checks

```bash
curl -i http://localhost/health
curl -i http://localhost/ready
curl -sS http://localhost/metrics | sed -n '1,40p'
sg docker -c 'docker compose ps'
sg docker -c 'docker compose logs web postgres --since 5m'
```

## Incident Triage

1. Check `GET /health`.
2. If `GET /health` is `200` but user traffic is broken, check `GET /ready`.
3. Inspect `docker compose ps` for restart state.
4. Check recent `web` and `postgres` logs.
5. Re-run `./scripts/smoke.sh http://localhost`.
6. If the web container is gone, re-run `./scripts/chaos_demo.sh` after recovery to verify restart behavior.

## Recovery Steps

### Web Failure

```bash
sg docker -c 'docker compose up -d web nginx'
curl -i http://localhost/health
```

### Database Failure

```bash
sg docker -c 'docker compose start postgres'
sg docker -c 'docker compose exec -T postgres pg_isready -U postgres -d hackathon_app'
curl -i http://localhost/ready
```

### Schema Repair

```bash
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH=.
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=postgres
export DATABASE_NAME=hackathon_app
uv run python scripts/bootstrap_db.py
```
