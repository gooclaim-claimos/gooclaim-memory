# 07 — Operations

## Health

| Check | How |
|---|---|
| API answering | `GET /docs` returns 200 (`make health` does this) |
| API answering and key accepted | `GET /memories?user_id=<ns>&agent_id=<ns>&top_k=1` with `X-API-Key` — the same probe the memory MCP's `/ready` uses |
| Dashboard | `GET /api/health` on the dashboard |
| Postgres | `docker compose exec -T postgres pg_isready` |
| Effective config | `GET /configure` (admin or key; secrets redacted) |

The API has no `/health` route of its own.

## Admin tasks (from `server/`)

| Task | Command |
|---|---|
| Logs | `make logs` |
| First admin + API key without the wizard | `make bootstrap` |
| Reset an admin password | `make reset-admin-password EMAIL=... PASSWORD=...` |
| Trim request logs | `make prune-logs` (keeps `REQUEST_LOG_RETENTION_DAYS`, default 30); not scheduled by default |
| Stop | `make down` |
| Delete all data | `make clean` — removes the Postgres volume |

## State to know about

- **Memories**: Postgres `POSTGRES_DB`, table `POSTGRES_COLLECTION_NAME`.
- **Runtime config overrides**: app database, `settings.config_overrides`. These beat the
  environment at every start. If a model or URL change in `.env` seems to have no effect,
  look here first (`GET /configure`).
- **History**: SQLite at `HISTORY_DB_PATH` inside the `server/history` bind mount.
- **Request log**: `request_logs` grows with every request (health and docs paths are
  skipped) until pruned.

## Common failures

| Symptom | Likely cause |
|---|---|
| API exits at start with "JWT_SECRET is required" | `JWT_SECRET` empty and auth enabled |
| Every route 401 | No `ADMIN_API_KEY` and no admin user; or the caller's key is wrong |
| `POST /memories` or `/search` returns 5xx | Gateway unreachable, gateway key invalid, or the model alias missing on the gateway. Check the API log (request id in `X-Request-ID`) and the gateway's logs |
| LLM calls rejected for an unsupported parameter | mem0 sends `temperature`/`top_p`; some models reject them. The gateway must drop unsupported params for the alias used |
| "no pq wrapper available" | Image without libpq; the fork's `server/Dockerfile` installs it |
| Memory MCP `/ready` fails, API fine | Wrong `MEMORY_API_URL` or `MEMORY_API_KEY` in the memory MCP |
