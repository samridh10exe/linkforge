# Architecture

## Runtime

- `nginx` fronts the Flask app and handles client connection fan-in.
- `gunicorn` runs the Flask app with environment-controlled worker/thread settings from `gunicorn.conf.py`.
- `postgres` stores `users`, `urls`, and `events`.
- Docker Compose is the only process manager for local and demo environments.

## Data Model

- `users`
  - `id` primary key
  - `username` is intentionally **not unique**
  - `email` is unique
- `urls`
  - `short_code` is unique
  - `is_active` and `expires_at` control redirect eligibility
- `events`
  - stores `created`, `updated`, `deleted`, and runtime `clicked` events

`users.username` is not unique because the provided seed data contains duplicate usernames. The app keys ownership and foreign keys by `user_id`, so removing username uniqueness is the correct schema fix without mutating the CSVs.

## Production Choices

- Default hardened runtime: `2` Gunicorn workers, `2` threads each, DB pool size `12`
- `/health` is evaluator-compatible and always returns `{"status":"ok"}`
- `/ready` is the operator-facing DB-sensitive endpoint
- `/metrics` exports Prometheus text format without adding a heavy monitoring stack to the droplet

## Known Limits

- `GET /events`, `GET /users`, and `GET /urls` are intentionally compatibility-focused list endpoints; their latency rises first under heavy mixed load because they return full JSON lists.
- Redirect throughput is strong, but the evaluator-shaped mixed flow is the real bottleneck because it combines list reads and write paths.
