# Environment Variables

| Variable | Section | Notes |
|----------|---------|-------|
| `FLASK_ENV` | App | `development` or `production` |
| `SECRET_KEY` | App | |
| `SHORT_CODE_LENGTH` | App | Default 6 |
| `SHORT_CODE_ATTEMPTS` | App | Retry limit for collision avoidance |
| `CLICK_EVENT_WORKERS` | App | Background thread count |
| `DATABASE_NAME` | DB | |
| `DATABASE_HOST` | DB | |
| `DATABASE_PORT` | DB | |
| `DATABASE_USER` | DB | |
| `DATABASE_PASSWORD` | DB | |
| `DATABASE_MAX_CONNECTIONS` | DB | Pool size |
| `DATABASE_STALE_TIMEOUT` | DB | Seconds before stale connection is dropped |
| `DATABASE_POOL_TIMEOUT` | DB | Seconds to wait for a pool slot |
| `TEST_DATABASE_NAME` | DB | Used by pytest |
| `GUNICORN_WORKERS` | Gunicorn | |
| `GUNICORN_THREADS` | Gunicorn | |
| `GUNICORN_TIMEOUT` | Gunicorn | |
| `GUNICORN_GRACEFUL_TIMEOUT` | Gunicorn | |
| `HEALTH_DB_TIMEOUT_MS` | Health | Timeout for `/ready` DB check |
| `REDIS_URL` | Cache | Redis connection string |
| `MONITOR_HEALTH_URL` | Monitor | URL polled by `scripts/monitor.py` |
| `DISCORD_WEBHOOK_URL` | Monitor | Discord webhook for alerts |
| `MONITOR_INTERVAL` | Monitor | Seconds between polls |

See `.env.example` for recommended local values.
