# Judge Demo Script

## Setup

```bash
sg docker -c 'docker compose up -d --build web nginx postgres'
./scripts/reset_app_db.sh
```

## Evaluator Contract

```bash
./scripts/evaluator_smoke.sh http://localhost
```

Show:
- `GET /health -> 200 {"status":"ok"}`
- user creation and update
- URL creation and update
- event listing

## Load Proof

Show these artifact files:
- `docs/judging/artifacts/load/baseline/`
- `docs/judging/artifacts/load/tuned/`
- `docs/judging/artifacts/load/breakpoint/`

Call out:
- mixed-flow p95 improved from `460ms` to `400ms`
- write-heavy p95 improved from `180ms` to `120ms`
- read-heavy remained error-free

## Chaos Proof

```bash
./scripts/chaos_demo.sh
```

Show:
- healthy service
- redirect working
- web process kill under read load
- `GET /health` recovers
- redirect resumes
- DB outage under mixed load
- recovery once DB returns
- no traceback leak in recent web logs
