# Incident Response Submission Pack

## Chaos Evidence

- Evidence link target:
  - `docs/judging/artifacts/chaos/chaos-20260404-134432.log`
  - `docs/judging/artifacts/chaos/web-chaos-locust-20260404-134432.log`
  - `docs/judging/artifacts/chaos/db-chaos-locust-20260404-134432.log`
- What it proves:
  - web restart under live read load
  - DB outage under live mixed load
  - redirect recovery
  - DB-backed route `503`s during dependency loss
- Screenshot target:
  - the `chaos-20260404-134432.log` lines for kill, recovery, and restart
- Reproduce:

```bash
./scripts/chaos_demo.sh
```

## Discord Alerting

- **Monitor:** `scripts/monitor.py` polls `/health` every 30s
- **Webhook:** Discord `#alerts` channel
- **Evidence:** monitor log at `/var/log/monitor.log` on droplet

Alert cycle captured on 2026-04-05:
```
[monitor] starting. polling http://localhost/health every 30s
🚨 [2026-04-05T05:32:31.495194] Service DOWN — http://localhost/health is not responding
✅ [2026-04-05T05:33:01.628745] Service RECOVERED — http://localhost/health is back up
```

Both messages posted to Discord `#alerts` channel successfully (HTTP 204).

## Runbook Linkage

- Evidence link target:
  - `docs/runbook.md`
  - `docs/judge-demo.md`
- What it proves:
  - operators have exact commands for detection, restart, schema repair, and verification
- Screenshot target:
  - the recovery command block in `docs/runbook.md`
- Reproduce:

```bash
sed -n '1,220p' docs/runbook.md
```
