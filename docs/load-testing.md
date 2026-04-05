# Load Testing Results

All reported runs used a freshly reset and reseeded `hackathon_app` database before each scenario.

Profiles:
- Baseline: `2 workers x 4 threads`, DB pool `12`
- Hardened: `2 workers x 2 threads`, DB pool `12`

Duration:
- Main comparison runs: `20s`
- Breakpoint runs: `15s`

## Main Comparison

| Scenario | Profile | VUs | RPS | p50 | p95 | Error rate | Web CPU peak | Web mem peak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Read-heavy `GET /<short_code>` | Baseline | 80 | 523.90 | 140ms | 250ms | 0.00% | 291.58% | 130.1 MiB |
| Read-heavy `GET /<short_code>` | Hardened | 80 | 450.97 | 160ms | 250ms | 0.00% | 296.07% | 389.5 MiB |
| Mixed evaluator flow | Baseline | 40 | 171.15 | 190ms | 460ms | 0.00% | 251.65% | 339.1 MiB |
| Mixed evaluator flow | Hardened | 40 | 180.64 | 190ms | 400ms | 0.00% | 267.86% | 637.5 MiB |
| Write-heavy `POST /users` + `POST /urls` | Baseline | 30 | 295.27 | 81ms | 180ms | 0.00% | 254.60% | 284.2 MiB |
| Write-heavy `POST /users` + `POST /urls` | Hardened | 30 | 339.06 | 80ms | 120ms | 0.00% | 296.23% | 663.4 MiB |

Raw artifacts:
- `docs/judging/artifacts/load/baseline/`
- `docs/judging/artifacts/load/tuned/`

## Bottleneck

First bottleneck: evaluator-shaped mixed load, not redirect-only traffic.

Why it bends first:
- `GET /users`, `GET /urls`, and `GET /events` return full JSON lists
- `POST /users` and `POST /urls` both write rows and events
- `POST /urls` also uses advisory locking for duplicate protection

What tuning helped:
- Reducing Gunicorn threads from `4` to `2` while keeping pool size `12`
- This improved mixed-flow p95 from `460ms` to `400ms`
- It improved write-heavy p95 from `180ms` to `120ms`
- It traded away some peak redirect throughput, which is acceptable because the published evaluator is API-mix heavy rather than redirect-only

## Breakpoint Exploration

| Scenario | VUs | RPS | p95 | Error rate | Interpretation |
|---|---:|---:|---:|---:|---|
| Read-heavy | 200 | 541.42 | 490ms | 0.00% | No failure observed at highest tested load |
| Mixed evaluator flow | 100 | 172.09 | 1000ms | 0.00% | First degradation point by latency threshold |
| Write-heavy | 80 | 367.10 | 340ms | 0.00% | No failure observed at highest tested load |

Raw artifacts:
- `docs/judging/artifacts/load/breakpoint/read-heavy/u200_summary.json`
- `docs/judging/artifacts/load/breakpoint/mixed-evaluator/u100_summary.json`
- `docs/judging/artifacts/load/breakpoint/write-heavy/u80_summary.json`

## Reproduce

```bash
./scripts/reset_app_db.sh
SHORT_CODE=$(curl -sS -X POST http://localhost/urls -H 'Content-Type: application/json' -d '{"user_id":1,"original_url":"https://example.com/load","title":"Load"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["short_code"])')
./scripts/run_load_test.sh tuned mixed-evaluator 40 10 20s "$SHORT_CODE"
```
