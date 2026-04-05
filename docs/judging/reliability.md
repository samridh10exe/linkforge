# Reliability Submission Pack

## Bronze

- Evidence link target:
  - `docs/judging/artifacts/evaluator/evaluator-smoke-20260404-134620.log`
  - `tests/`
  - `.github/workflows/ci.yml`
- What it proves:
  - `/health` returns `200`
  - evaluator-compatible API surface works end to end
  - pytest runs in CI
- Screenshot target:
  - terminal output from `./scripts/evaluator_smoke.sh http://localhost`
- Reproduce:

```bash
./scripts/evaluator_smoke.sh http://localhost
```

## Silver

- Evidence link target:
  - `tests/integration/test_evaluator_contract.py`
  - `docs/failure-modes.md`
  - `.github/workflows/ci.yml`
- What it proves:
  - integration coverage for evaluator-style requests
  - documented 404/410/500/503 behavior
  - CI blocks on failures
- Screenshot target:
  - GitHub Actions green check on `ci`
- Reproduce:

```bash
uv run pytest --cov=app --cov-report=term-missing -v
```

## Gold

- Evidence link target:
  - `docs/judging/artifacts/chaos/chaos-20260404-134432.log`
  - `docs/judging/artifacts/chaos/web-chaos-locust-20260404-134432.log`
  - `docs/judging/artifacts/chaos/db-chaos-locust-20260404-134432.log`
- What it proves:
  - web restart and recovery under active load
  - DB outage during live traffic
  - data routes return `503` under DB outage in the load log
  - no traceback leak
- Screenshot target:
  - web-chaos log lines showing kill, health recovery, redirect recovery
- Reproduce:

```bash
./scripts/chaos_demo.sh
```
