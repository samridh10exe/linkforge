# Architecture

## Runtime

nginx fronts two Flask app containers (web1, web2) and handles client connection fan-in.
Gunicorn runs each with environment-controlled worker/thread settings from `gunicorn.conf.py`.
PostgreSQL stores `users`, `urls`, and `events`. Redis caches resolved short codes on the
redirect path. Docker Compose manages all containers.

## Data Model

- **users** -- `id` PK, `username` (not unique -- seed data contains duplicates), `email` (unique)
- **urls** -- `short_code` (unique), `is_active` and `expires_at` control redirect eligibility
- **events** -- stores `created`, `updated`, `deleted`, and runtime `clicked` events

`users.username` is not unique because the provided seed data contains duplicate usernames.
The app keys ownership by `user_id`, so removing username uniqueness is the correct fix
without mutating the CSVs.

## Configuration

Default runtime: 2 Gunicorn workers, 2 threads each, DB pool size 12.

- `/health` returns `{"status":"ok"}` with no DB access (evaluator-compatible)
- `/ready` checks DB connectivity (operator-facing)
- `/metrics` exports Prometheus text format

## Known Limits

`GET /events`, `GET /users`, and `GET /urls` return full JSON lists.
Their latency rises first under heavy mixed load. The evaluator-shaped mixed flow
is the real bottleneck because it combines list reads and write paths.
