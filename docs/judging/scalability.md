# Scalability Submission Pack

## Baseline vs Hardened

- Evidence link target:
  - `docs/load-testing.md`
  - `docs/judging/artifacts/load/baseline/`
  - `docs/judging/artifacts/load/tuned/`
- What it proves:
  - measured RPS, p50, p95, error rate, CPU, and memory
  - one tuning pass with before/after data
- Screenshot target:
  - the comparison table in `docs/load-testing.md`
- Reproduce:

```bash
./scripts/reset_app_db.sh
SHORT_CODE=$(curl -sS -X POST http://localhost/urls -H 'Content-Type: application/json' -d '{"user_id":1,"original_url":"https://example.com/load","title":"Load"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["short_code"])')
./scripts/run_load_test.sh tuned read-heavy 80 20 20s "$SHORT_CODE"
```

## Droplet Production Results

Load tests from localhost on DigitalOcean Droplet (multi-container: nginx LB, web1, web2, Redis, PostgreSQL):

| VUs | RPS | p50 | p95 | Error Rate | Tier |
|---:|---:|---:|---:|---:|---|
| 200 | 135 | 1300ms | 3000ms | 0.00% | Silver |
| 500 | 130 | 3500ms | 6300ms | 2.52% | Gold |

Redis cache delivers X-Cache HIT on repeat redirects (verified MISS→HIT).

## Bottleneck And Next Step

- Evidence link target:
  - `docs/load-testing.md`
  - `docs/judging/artifacts/load/breakpoint/mixed-evaluator/u100_summary.json`
- What it proves:
  - evaluator-shaped mixed traffic is the first bottleneck
  - degradation begins around `100` VUs by latency, not by errors
- Screenshot target:
  - the breakpoint table in `docs/load-testing.md`
- Reproduce:

```bash
./scripts/reset_app_db.sh
SHORT_CODE=$(curl -sS -X POST http://localhost/urls -H 'Content-Type: application/json' -d '{"user_id":1,"original_url":"https://example.com/breakpoint","title":"Breakpoint"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["short_code"])')
./scripts/run_load_test.sh breakpoint mixed-evaluator 100 20 15s "$SHORT_CODE"
```
