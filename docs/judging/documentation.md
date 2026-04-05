# Documentation Submission Pack

## Core Docs

- Evidence link target:
  - `README.md`
  - `docs/architecture.md`
  - `docs/api.md`
  - `docs/env.md`
  - `docs/deploy.md`
  - `docs/runbook.md`
  - `docs/failure-modes.md`
  - `docs/load-testing.md`
  - `docs/judge-demo.md`
- What it proves:
  - setup, operation, rollback, limits, and demo flow are documented
- Screenshot target:
  - file tree showing the `docs/` folder
- Reproduce:

```bash
find docs -maxdepth 2 -type f | sort
```

## Seed And Schema Notes

- Evidence link target:
  - `docs/architecture.md`
  - `scripts/seed.py`
- What it proves:
  - schema matches the seed data
  - `users.username` is intentionally non-unique because the seed disproves uniqueness
- Screenshot target:
  - the architecture note about duplicate usernames
- Reproduce:

```bash
uv run python scripts/seed.py
```
