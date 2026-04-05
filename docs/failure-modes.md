# Failure Modes

- Missing short code: `404`
- Inactive short code: `410`
- Expired short code: `410`
- Duplicate `original_url` for the same active user: `409`
- Wrong user deleting a short code: `403`
- Invalid JSON or invalid schema: `400`
- Missing user on create or fetch: `404`
- DB connection failure before route work: structured `503`
- `/health`: always `200 {"status":"ok"}`
- `/ready`: `503` when DB connectivity check degrades

## Observed Under Chaos

- Web process kill under active redirect load:
  - container restarted
  - `/health` recovered
  - redirects resumed
  - no traceback leaked in recent logs
- DB loss under mixed evaluator load:
  - `/health` stayed on the liveness surface
  - data routes emitted `503` during the outage in the load log
  - service recovered when PostgreSQL returned
