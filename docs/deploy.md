# Deploy And Rollback

## Deploy

```bash
cp .env.example .env
docker compose up -d postgres
docker compose exec -T postgres createdb -U postgres hackathon_test
export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH=.
export DATABASE_HOST=localhost
export DATABASE_PORT=5432
export DATABASE_USER=postgres
export DATABASE_PASSWORD=postgres
export DATABASE_NAME=hackathon_app
uv sync --dev
uv run python scripts/bootstrap_db.py
uv run python scripts/seed.py
docker compose up -d --build web nginx
./scripts/smoke.sh http://localhost
```

## Rollback

If a new web image is unhealthy:

```bash
docker compose logs web nginx
docker compose up -d --build web nginx
./scripts/smoke.sh http://localhost
```

If the database is the problem:

```bash
docker compose ps
docker compose start postgres
docker compose exec -T postgres pg_isready -U postgres -d hackathon_app
```

If the app schema is missing:

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
