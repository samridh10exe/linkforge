# Runbook

## Quick checks

```bash
curl -i http://localhost/health
curl -i http://localhost/ready
curl -s http://localhost/metrics | head -40
docker compose ps
docker compose logs web1 web2 postgres --since 5m
```

## Incident triage

1. Check `GET /health`. If it returns 200, the process is alive.
2. If health is 200 but traffic is broken, check `GET /ready` for DB issues.
3. Run `docker compose ps` and look for restart counts.
4. Check `web1`, `web2`, and `postgres` logs.
5. Run `./scripts/evaluator_smoke.sh http://localhost` to verify API surface.

## Recovery

### Web container failure

```bash
docker compose up -d web1 web2 nginx
curl -i http://localhost/health
```

### Database failure

```bash
docker compose start postgres
docker compose exec -T postgres pg_isready -U postgres -d hackathon_app
curl -i http://localhost/ready
```

### Schema repair

```bash
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
```
