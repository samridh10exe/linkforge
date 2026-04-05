# API Reference

All non-2xx responses use:

```json
{
  "error": {
    "code": "string_machine_readable",
    "message": "human readable",
    "request_id": "..."
  }
}
```

## Evaluator-Compatible Endpoints

- `GET /health`
  - `200 {"status":"ok"}`
- `POST /users/bulk`
  - multipart form with `file`
  - `201 {"count": <imported>}`
- `GET /users`
  - optional `?page=&per_page=`
- `GET /users/<id>`
- `POST /users`
  - body: `{"username": str, "email": str}`
- `PUT /users/<id>`
  - body: at least one of `username`, `email`
- `POST /urls`
  - body: `{"user_id": int, "original_url": str, "title": str, "expires_at": str|null}`
- `GET /urls`
  - optional `?user_id=&page=&per_page=`
- `GET /urls/<id>`
- `PUT /urls/<id>`
  - body: at least one of `title`, `original_url`, `is_active`
- `GET /events`
  - optional `?page=&per_page=`

## Shortener Flow Endpoints

- `POST /shorten`
- `GET /<short_code>`
- `DELETE /<short_code>`
- `GET /ready`
- `GET /metrics`

## Core Behaviors

- `GET /<short_code>` returns `410` when the URL exists but is inactive.
- `GET /<short_code>` returns `410` when the URL exists but is expired.
- `POST /shorten` and `POST /urls` return `409` when the same user submits the same active, unexpired `original_url`.
- `DELETE /<short_code>` requires `user_id` and `reason` and performs a soft delete only.
