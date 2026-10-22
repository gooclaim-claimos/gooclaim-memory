# 05 — Configuration

The server has no settings class; values are read with `os.environ.get` at import time.
Sources are named per variable. `server/.env.example` is upstream's sample.

## API — model access

| Variable | Default | Required | Read in |
|---|---|---|---|
| `OPENAI_API_KEY` | none | yes | `server/main.py:114` — LiteLLM gateway virtual key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | yes for Gooclaim | mem0 library (`mem0/llms/openai.py:51`, `mem0/embeddings/openai.py:22-25`) — gateway `/v1` URL |
| `OPENAI_API_BASE` | unset | leave unset | Embedder reads it before `OPENAI_BASE_URL`; if set, it must point to the gateway too |
| `MEM0_DEFAULT_LLM_MODEL` | `gpt-4.1-nano-2025-04-14` | set it | `server/main.py:116` — use a gateway alias |
| `MEM0_DEFAULT_EMBEDDER_MODEL` | `text-embedding-3-small` | no | `server/main.py:117` — model name the gateway serves |

`ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` appear in the upstream sample for the other
bundled providers. Gooclaim must not set them: they are direct provider keys.

## API — auth

| Variable | Default | Required | Read in |
|---|---|---|---|
| `JWT_SECRET` | empty | yes | `server/auth.py:15`; startup raises without it (`server/main.py:89-93`) |
| `ADMIN_API_KEY` | empty | yes for Gooclaim | `server/auth.py:19`; under 16 characters logs a warning |
| `AUTH_DISABLED` | false | no | `server/auth.py:20`; `1/true/yes/on` opens every route |

## API — storage

| Variable | Default | Required | Read in |
|---|---|---|---|
| `POSTGRES_HOST` | `postgres` | no | `server/main.py:107`, `server/db.py:8` |
| `POSTGRES_PORT` | `5432` | no | `server/main.py:108`, `server/db.py:9` |
| `POSTGRES_USER` | `postgres` | no | `server/main.py:110`, `server/db.py:10` |
| `POSTGRES_PASSWORD` | `postgres` (code); compose requires a value | yes | `server/main.py:111`, `server/db.py:11` |
| `POSTGRES_DB` | `postgres` | no | `server/main.py:109` — vector table's database |
| `POSTGRES_COLLECTION_NAME` | `memories` | no | `server/main.py:112` |
| `APP_DB_NAME` | `mem0_app` | no | `server/db.py:12` |
| `HISTORY_DB_PATH` | `/app/history/history.db` | no | `server/main.py:115` |

## API — other

| Variable | Default | Required | Read in |
|---|---|---|---|
| `DASHBOARD_URL` | `http://localhost:3000` | no | `server/main.py:161` — sole CORS origin |
| `MEM0_TELEMETRY` | `true` | set `false` | `server/telemetry.py:27` and the mem0 library |
| `MEM0_TELEMETRY_STATE_PATH` | `/app/history/telemetry.json` | no | `server/telemetry.py:28` |
| `REQUEST_LOG_RETENTION_DAYS` | `30` | no | `server/scripts/prune_request_logs.py:17` |

## Dashboard

| Variable | Compose value | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8888` | API URL used by the browser; substituted into the build at start by `entrypoint.sh` |
| `API_INTERNAL_URL` | `http://mem0:8000` | API URL used server-side |
| `NEXT_PUBLIC_INSTANCE_NAME` | `Mem0` | Instance label; set it to `Gooclaim Memory` |

## Config that is not in the environment

`POST /configure` (admin) merges a JSON patch into the running config and stores it in the
app database (`settings`, key `config_overrides`). On every start those overrides are
merged over `DEFAULT_CONFIG`, so they win over the environment. After any change to model
or gateway settings, check `GET /configure` (secrets are redacted) to see what is
actually in force. `POST /configure` refuses LLM providers other than `openai`,
`anthropic`, `gemini` and embedders other than `openai`, `gemini`; for Gooclaim, only
`openai` (pointed at the gateway) is acceptable.

## Callers' settings (for reference)

`gooclaim-memory-mcp` reaches this API with `MEMORY_API_URL`, `MEMORY_API_KEY` (sent as
`X-API-Key`), `MEMORY_API_TIMEOUT_SECONDS` (default 30), and fixes the namespace with
`PRECEDENT_USER_ID` (default `gooclaim-precedent`) and `PRECEDENT_APP` (default
`precedent`, sent as `agent_id`).
