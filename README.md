# Gooclaim Memory

Gooclaim's fork of the open-source [mem0](https://github.com/mem0ai/mem0) project, run as
**Gooclaim Memory**: a self-hosted semantic memory store (REST API + admin dashboard +
Postgres/pgvector) that Gooclaim OS uses to remember approved field mappings across tenants.

## Table of Contents

- [What This Service Does](#what-this-service-does)
- [How This Fork Differs From Upstream](#how-this-fork-differs-from-upstream)
- [Architecture & Position](#architecture--position)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Database / State](#database--state)
- [Observability](#observability)
- [Testing](#testing)
- [Deployment](#deployment)
- [Versioning & Branches](#versioning--branches)
- [Upstream](#upstream)

Detailed docs: [`docs/gooclaim/`](docs/gooclaim/README.md). The `docs/` folder outside
`docs/gooclaim/` is upstream mem0's Mintlify site and is not edited in this fork.

## What This Service Does

Gooclaim runs only the **`server/`** stack from this repository: the mem0 FastAPI REST
server, its Next.js dashboard, and a pgvector Postgres.

Its one consumer today is **Precedent**, the mapping memory:

- When a person activates a tenant's CMS field mapping, connector-hub writes one memory per
  column decision ("tenant column `X` maps to canonical field `Y`") and per code value.
- When an agent drafts a new mapping, the mapping MCP recalls what other tenants did with a
  column of the same name.

Both go through `gooclaim-memory-mcp` (in `gooclaim-mcp-server`), which is the only
Gooclaim service that calls this API directly.

**What it does NOT do:**

- It is **not** conversation memory and does not store member profiles. No channel,
  engine or Orion code calls it. Member profiles live in the member registry, which
  deliberately does not use mem0.
- It does **not** run `openmemory/` (a different mem0 product with a different API).
- It does **not** use the Python SDK, the TypeScript SDK, the CLIs, or anything under
  `integrations/`, `skills/`, `examples/` or `evaluation/`.
- It holds no member data by contract: Precedent stores column names and a tenant's own
  code values, never row values, and refers to a tenant only by a one-way reference.

## How This Fork Differs From Upstream

Base: upstream `main` at `42cf18c` (2026-07-13). Gooclaim's changes are three commits:

| Change | Files |
|---|---|
| API image installs `libpq5` and `psycopg[binary]` (fixes "no pq wrapper available") and drops uvicorn `--reload` | `server/Dockerfile` |
| OpenAPI title and description rebranded to "Gooclaim Memory API" | `server/main.py` |
| Dashboard rebranded (logos, favicons, login page, page titles); the "Cloud features (Pro)" nav removed | `server/dashboard/**` |
| `litellm` optional extra capped `<1.107.0` (1.107.0 was a compromised release) | `pyproject.toml` |
| Fork notes | `GOOCLAIM-FORK.md` (partly stale, see [docs/gooclaim/09-development.md](docs/gooclaim/09-development.md)) |

Everything else is upstream code, unchanged.

## Architecture & Position

```
connector-hub ──(on mapping activation)──▶ gooclaim-memory-mcp ──X-API-Key──▶ Gooclaim Memory API ──▶ LiteLLM gateway
mapping MCP  ──(recall precedent)────────▶   /v1/memory/*                     /memories, /search       (embeddings, LLM)
                                                                                     │
                                                                    Postgres (pgvector) + SQLite history
                                                                                     ▲
                                                               Dashboard (Next.js) ──┘ (admin use)
```

| Component | Source | Container port |
|---|---|---|
| API (FastAPI + uvicorn) | `server/main.py` | 8000 |
| Dashboard (Next.js) | `server/dashboard/` | 3000 |
| Postgres 17 + pgvector | image `pgvector/pgvector:pg17` | 5432 |

The API builds one `mem0.Memory` from `DEFAULT_CONFIG` (`server/main.py:119-140`):
vector store `pgvector`, LLM provider `openai`, embedder provider `openai`. The OpenAI
provider is only a wire format: Gooclaim points it at the **LiteLLM gateway** by setting
`OPENAI_BASE_URL` and giving `OPENAI_API_KEY` a gateway virtual key (see
[Configuration](#configuration)).

**Hard rules**

- Every model call goes through the LiteLLM gateway. Never configure a direct provider
  key, and never switch the provider (via env or `POST /configure`) to `anthropic` or
  `gemini`, which the image also bundles.
- Only Precedent's namespace is used today (`user_id` + `agent_id` fixed by the memory
  MCP's config, never by the caller). A future per-tenant consumer must get its own
  namespace.
- Never store a value out of a tenant's file; column names and codes only.
- Keep fork changes minimal and marked, so upstream merges stay easy.

## Quick Start

Prerequisites: Docker with Compose, and a reachable LiteLLM gateway (or an OpenAI-compatible
endpoint for local testing).

```bash
cd server
cp .env.example .env
# Set at least: POSTGRES_PASSWORD, JWT_SECRET, ADMIN_API_KEY,
# OPENAI_API_KEY (gateway key), OPENAI_BASE_URL (gateway /v1 URL),
# MEM0_DEFAULT_LLM_MODEL (gateway alias), MEM0_TELEMETRY=false
make up          # builds and starts API (host 8888), dashboard (host 3000), Postgres (host 8432)
make health
```

Open the dashboard on port 3000 to create the first admin, or use `make bootstrap` to
create the admin and first API key from the terminal. API docs are at `/docs` on the API.

## API Reference

All routes come from `server/main.py` and `server/routers/`. Auth is a Bearer JWT
(dashboard users) or `X-API-Key` (an API key from the dashboard, or `ADMIN_API_KEY`).

Routes Gooclaim's services call (through the memory MCP):

| Method | Path | Used for |
|---|---|---|
| POST | `/memories` | Add a memory (`messages`, `user_id`, `agent_id`, `metadata`, `infer`) |
| POST | `/search` | Similarity search within a namespace |
| GET | `/memories?user_id=&agent_id=&top_k=` | List a namespace; also the memory MCP's readiness probe |
| DELETE | `/memories/{memory_id}` | Delete one memory |

Other upstream routes exist (`/configure`, `/generate-instructions`, `/memories/{id}`
GET/PUT, `/memories/{id}/history`, bulk `DELETE /memories`, `/reset`, `/auth/*`,
`/api-keys`, `/entities`, `/requests`). See [docs/gooclaim/03-apis.md](docs/gooclaim/03-apis.md).

## Configuration

### Repository structure (the parts Gooclaim uses)

```
server/
  main.py            FastAPI app, DEFAULT_CONFIG, memory routes
  auth.py            JWT / API-key / admin-key auth
  db.py, models.py   SQLAlchemy app database (users, keys, logs, settings)
  server_state.py    builds mem0.Memory; merges config overrides stored in Postgres
  routers/           /auth, /api-keys, /entities, /requests
  alembic/           app-database migrations 001-006
  Dockerfile         API image (fork-modified)
  dev.Dockerfile     image used by docker-compose.yaml
  docker-compose.yaml  API + Postgres + dashboard
  dashboard/         Next.js admin UI (fork-rebranded)
pyproject.toml       mem0ai library (fork: litellm cap)
```

### Environment variables (API)

Read with `os.environ.get` in `server/main.py`, `server/auth.py`, `server/db.py`,
`server/telemetry.py`. There is no settings class.

| Variable | Default | Required | Notes |
|---|---|---|---|
| `OPENAI_API_KEY` | none | yes | LiteLLM gateway virtual key for this service |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` (library default) | yes for Gooclaim | Gateway `/v1` URL. Read by mem0's OpenAI LLM and embedder |
| `MEM0_DEFAULT_LLM_MODEL` | `gpt-4.1-nano-2025-04-14` | set it | Use a gateway alias |
| `MEM0_DEFAULT_EMBEDDER_MODEL` | `text-embedding-3-small` | no | Must exist on the gateway; 1536 dimensions matches the pgvector default |
| `JWT_SECRET` | empty | yes | Startup fails without it unless `AUTH_DISABLED` |
| `ADMIN_API_KEY` | empty | yes for Gooclaim | The key the memory MCP sends as `X-API-Key` |
| `AUTH_DISABLED` | false | no | Local development only |
| `POSTGRES_HOST` / `POSTGRES_PORT` | `postgres` / `5432` | no | |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` | `postgres` / `postgres` | password yes | Compose refuses to start without `POSTGRES_PASSWORD` |
| `POSTGRES_DB` | `postgres` | no | Database holding the vector table |
| `POSTGRES_COLLECTION_NAME` | `memories` | no | Vector table name |
| `APP_DB_NAME` | `mem0_app` | no | Database for users, keys, logs, settings |
| `HISTORY_DB_PATH` | `/app/history/history.db` | no | SQLite memory-change history |
| `DASHBOARD_URL` | `http://localhost:3000` | no | Only CORS origin allowed |
| `MEM0_TELEMETRY` | true | no | Set `false`: otherwise events go to mem0's PostHog |
| `MEM0_TELEMETRY_STATE_PATH` | `/app/history/telemetry.json` | no | |
| `REQUEST_LOG_RETENTION_DAYS` | 30 | no | Used by `make prune-logs` |

Dashboard: `NEXT_PUBLIC_API_URL`, `API_INTERNAL_URL`, `NEXT_PUBLIC_INSTANCE_NAME`.
Full detail: [docs/gooclaim/05-configuration.md](docs/gooclaim/05-configuration.md).

## Database / State

One Postgres instance, two databases:

- `POSTGRES_DB` (default `postgres`): the pgvector table `POSTGRES_COLLECTION_NAME`
  (default `memories`), created by the mem0 library on first start.
- `APP_DB_NAME` (default `mem0_app`, created by `server/init-db.sh`): `users`, `api_keys`,
  `request_logs`, `refresh_token_jtis`, `settings` (Alembic migrations `001`-`006`).

Plus a SQLite history file at `HISTORY_DB_PATH`. Note that `POST /configure` saves
overrides in the `settings` table and they are re-applied over the env defaults at every
start (`server/server_state.py`).

## Observability

Plain Python logging with a request id per request (`X-Request-ID` response header). Each
request is also written to the `request_logs` table and shown in the dashboard. There is
no OpenTelemetry or audit-bus emission in this server; audit events for Precedent tool
calls are emitted by `gooclaim-memory-mcp`.

## Testing

Upstream tests run with Hatch from the repo root: `make test` (`pytest tests/`). The
server's own tests are `tests/test_server_auth.py`, `tests/test_server_params.py` and
`tests/test_api_keys_router.py`. See [docs/gooclaim/08-testing.md](docs/gooclaim/08-testing.md).

## Deployment

Dev only, on AWS: the `server/` stack runs as Docker containers (API, dashboard, Postgres)
on a dev EC2 instance, started with Docker Compose. It is not deployed through the
platform's per-service deploy script. Nothing runs on Kubernetes or Azure. See
[docs/gooclaim/06-deployment.md](docs/gooclaim/06-deployment.md).

## Versioning & Branches

| Branch | Holds |
|---|---|
| `main` | Upstream mirror (currently at the fork base `42cf18c`) |
| `release/dev` | Default branch: upstream + Gooclaim changes; what dev runs |
| `release/uat`, `release/prd` | Promotion branches |
| `develop` | Older integration branch |

Flow: `feature|fix|chore|docs/<x>` → `release/dev` → `release/uat` → `release/prd`.
No server CI on the Gooclaim side: run the checks locally before pushing.

## Upstream

- Source: <https://github.com/mem0ai/mem0>
- Docs: <https://docs.mem0.ai> (self-hosted server: "Open Source → REST API")
- Upstream internals for coding agents: [`AGENTS.md`](AGENTS.md), [`LLM.md`](LLM.md),
  [`server/README.md`](server/README.md)
- License: Apache-2.0 ([`LICENSE`](LICENSE))
