# 01 — Architecture

## Components

Defined in `server/docker-compose.yaml`:

| Service | Build / image | Container port | Host port (compose) |
|---|---|---|---|
| `mem0` (API) | `server/dev.Dockerfile`, context = repo root | 8000 | 8888 |
| `postgres` | `pgvector/pgvector:pg17` | 5432 | 8432 |
| `mem0-dashboard` | `server/dashboard/Dockerfile` | 3000 | 3000 |

`server/Dockerfile` is a second, slimmer API image (the one the fork modified). It does
not run Alembic migrations; the compose command does (see below).

## The API process

`server/main.py` at import time:

1. Fails startup if `JWT_SECRET` is empty and `AUTH_DISABLED` is not set.
2. Builds `DEFAULT_CONFIG` (`server/main.py:119-140`):
   - `vector_store`: `pgvector` on `POSTGRES_*`, table `POSTGRES_COLLECTION_NAME`.
   - `llm`: provider `openai`, model `MEM0_DEFAULT_LLM_MODEL`, temperature 0.2.
   - `embedder`: provider `openai`, model `MEM0_DEFAULT_EMBEDDER_MODEL`.
   - `history_db_path`: `HISTORY_DB_PATH` (SQLite).
3. `server_state.initialize_state` merges any overrides saved in the app database
   (`settings` row `config_overrides`, written by `POST /configure`) over that config, and
   builds one `mem0.Memory`.
4. Mounts the memory routes plus `/auth`, `/api-keys`, `/entities`, `/requests`.
5. CORS allows only `DASHBOARD_URL`.

The compose command for `mem0` is:

```
alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The `mem0` library is this repository's `mem0/`, installed into site-packages by
`server/dev.Dockerfile` when the image is built (outside `/app`, which compose bind-mounts
from `server/`). Nothing is installed at container start, and PyPI's `mem0ai` is never used.

## How model calls reach the gateway

There is no Gooclaim code for this; it is configuration. mem0's OpenAI LLM uses
`config.openai_base_url or OPENAI_BASE_URL or https://api.openai.com/v1`
(`mem0/llms/openai.py:51`); the embedder checks `OPENAI_API_BASE` first, then
`OPENAI_BASE_URL` (`mem0/embeddings/openai.py:22-25`). Gooclaim sets:

- `OPENAI_BASE_URL` = the LiteLLM gateway's `/v1` URL
- `OPENAI_API_KEY` = a gateway virtual key for this service
- `MEM0_DEFAULT_LLM_MODEL` = a gateway alias

Model calls happen on:

- `POST /memories` with `infer` true (fact extraction, LLM) and always for embedding;
- `POST /search` (embedding of the query);
- `PUT /memories/{id}` with new text (embedding);
- `POST /generate-instructions` (LLM).

Precedent writes with `infer=False`, so its traffic is embedding calls only. The server
does not send a `user` (tenant) field, so gateway spend is attributed to the key only.

## Data flow for Precedent

```
activation in connector-hub
  └─ POST memory-mcp /v1/memory/add  (infer=false, metadata = column key, field, tenant ref)
       └─ POST /memories  {messages, user_id, agent_id, metadata, infer:false}
            └─ embed text via gateway ─▶ insert row in pgvector table; history in SQLite

agent drafting a mapping (mapping MCP)
  └─ POST memory-mcp /v1/memory/search  (one search per column)
       └─ POST /search {query, user_id, agent_id, top_k}
            └─ embed query via gateway ─▶ nearest rows
  └─ mapping MCP filters by exact column key in metadata, counts distinct tenant refs
```

## Storage

- Postgres database `POSTGRES_DB`: vector table (HNSW index by default, 1536 dimensions
  by default).
- Postgres database `APP_DB_NAME` (created by `server/init-db.sh`): users, API keys,
  request logs, refresh-token ids, settings.
- SQLite file `HISTORY_DB_PATH`: per-memory change history.
