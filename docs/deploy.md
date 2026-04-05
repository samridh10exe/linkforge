# Deploy and Rollback

## Deploy

```bash
cp .env.example .env
# edit .env with production values
docker compose up -d --build
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/seed.py "Seed Data"
curl http://localhost/health
```

## Rollback

If a new web image is unhealthy:

```bash
docker compose logs web1 web2 nginx
docker compose up -d --build
curl http://localhost/health
```

If the database is down:

```bash
docker compose ps
docker compose start postgres
docker compose exec -T postgres pg_isready -U postgres -d hackathon_app
```

If the schema is missing:

```bash
docker compose exec web1 env PYTHONPATH=/app uv run python scripts/bootstrap_db.py
```
