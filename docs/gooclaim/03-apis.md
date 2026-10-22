# 03 — APIs

Source: `server/main.py` and `server/routers/*.py`. OpenAPI is served at `/docs`,
`/redoc` and `/openapi.json`; `/` redirects to `/docs`.

## Authentication (`server/auth.py`)

Checked in this order by `verify_auth`:

1. `Authorization: Bearer <jwt>` — a dashboard user's access token (HS256, `JWT_SECRET`,
   30-minute access tokens, 30-day single-use refresh tokens).
2. `X-API-Key` — if it equals `ADMIN_API_KEY` the caller is treated as admin; otherwise it
   is looked up among non-revoked keys created in the dashboard (`m0sk_...`, bcrypt-hashed).
3. `AUTH_DISABLED=true` — everything open (local development only).

Otherwise 401. `require_admin` routes additionally need the admin role (or the admin key).

Gooclaim's memory MCP authenticates with `X-API-Key` = `ADMIN_API_KEY`.

## Routes Gooclaim calls

All through `gooclaim-memory-mcp`; no other Gooclaim service calls this API.

| Method | Path | Auth | Request | Response |
|---|---|---|---|---|
| POST | `/memories` | any | `messages[]` (`role`, `content`), at least one of `user_id`/`agent_id`/`run_id`, optional `metadata`, `infer`, `expiration_date`, `memory_type`, `prompt` | `{"results": [...]}` |
| POST | `/search` | any | `query`, `filters`, `top_k`, `threshold`, `explain`, `show_expired`; top-level `user_id`/`agent_id`/`run_id` still accepted but deprecated | `{"results": [...]}` |
| GET | `/memories` | any | query `user_id`, `agent_id`, `run_id`, `top_k` (0-1000), `show_expired` | memories for the namespace |
| DELETE | `/memories/{memory_id}` | any | — | `{"message": ...}` |

Notes:

- The memory MCP still sends `user_id` and `agent_id` at the top level of `/search`, which
  the server accepts and moves into `filters` with a deprecation warning in its log.
- `GET /memories` with no identifier lists every memory and needs admin.
- 4xx means the request was wrong (`not found` → 404, validation → 400); upstream model or
  store failures come back as 5xx via `upstream_error`.

## Other routes (upstream, not used by Gooclaim services)

| Method | Path | Auth |
|---|---|---|
| GET | `/configure` (secrets redacted), `/configure/providers` | any |
| POST | `/configure` — changes and persists the runtime config | admin |
| POST | `/generate-instructions` — LLM call | any |
| GET / PUT | `/memories/{memory_id}` | any |
| GET | `/memories/{memory_id}/history` | any |
| DELETE | `/memories?user_id=&agent_id=&run_id=` — bulk delete | admin |
| POST | `/reset` — deletes all memories | admin |
| GET | `/auth/setup-status`; POST `/auth/register`, `/auth/login`, `/auth/refresh`; GET/PATCH `/auth/me`; POST `/auth/change-password`, `/auth/onboarding-complete` | mixed |
| GET / POST / DELETE | `/api-keys`, `/api-keys/{key_id}` | user |
| GET | `/entities` | any |
| DELETE | `/entities/{entity_type}/{entity_id}` — deletes an entity's memories | admin |
| GET | `/requests` — request log | admin |

The memory MCP deliberately does not expose bulk delete or reset as tools; clearing a
namespace is a human action through this API.

There is no `/api/health` route on the API (it is only in the request-log skip list); the
dashboard serves `/api/health`.
