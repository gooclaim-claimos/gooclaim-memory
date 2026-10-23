# CLAUDE.md — gooclaim-memory

Gooclaim's fork of upstream mem0 (`upstream` = mem0ai/mem0), run as **Gooclaim Memory**
on dev. Gooclaim runs only the `server/` stack (FastAPI API + Next.js dashboard +
pgvector Postgres). For upstream internals (SDK, providers, CLIs, plugins, upstream CI)
read `AGENTS.md` and `LLM.md` — they describe upstream, not Gooclaim's use.

Gooclaim docs: `README.md` and `docs/gooclaim/`. Everything else under `docs/` is
upstream's Mintlify site — do not edit it.

## What Gooclaim uses it for

- One consumer: **Precedent**, the cross-tenant mapping memory. connector-hub writes
  approved column mappings (`infer=False`); the mapping MCP recalls them.
- The only direct caller is `gooclaim-memory-mcp` (`gooclaim-mcp-server/services/memory`),
  using `POST /memories`, `POST /search`, `GET /memories`, `DELETE /memories/{id}` with
  `X-API-Key` = `ADMIN_API_KEY`.
- NOT conversation memory, NOT member profiles, NOT `openmemory/`.

## Fork changes (keep them small and marked)

`git log --oneline upstream/main..HEAD` — the commits on top of upstream `42cf18c`:

- `server/Dockerfile`: `libpq5` + `psycopg[binary]`, no `--reload`.
- `server/main.py`: OpenAPI title/description "Gooclaim Memory API".
- `server/dashboard/**`: Gooclaim branding; "Cloud features (Pro)" nav removed.
- `pyproject.toml`: `litellm>=1.83.7,<1.107.0` — a marked GOOCLAIM DEVIATION; a merge
  from upstream must not drop it.
- `server/requirements.txt`, both Dockerfiles, `docker-compose.yaml`, root `.dockerignore`:
  the server runs THIS repo's `mem0/` (installed at image build), never PyPI's `mem0ai`;
  no install at container start; `.env` never enters an image. Guarded by
  `tests/test_gooclaim_mem0_comes_from_this_repo.py` — an upstream merge must keep it green.
- `GOOCLAIM-FORK.md`: fork notes (its Deploy section is stale: Azure/ACR/AKV/OpenAI-direct).

## Layout that matters

```
server/main.py          app, DEFAULT_CONFIG (pgvector + openai LLM/embedder), memory routes
server/auth.py          Bearer JWT | X-API-Key (dashboard key or ADMIN_API_KEY) | AUTH_DISABLED
server/server_state.py  builds mem0.Memory; merges `settings.config_overrides` from Postgres
server/db.py models.py  app DB (APP_DB_NAME): users, api_keys, request_logs, refresh_token_jtis, settings
server/alembic/         migrations 001-006 for the app DB
server/docker-compose.yaml  mem0 (dev.Dockerfile) + postgres (pgvector:pg17) + mem0-dashboard
server/dashboard/       Next.js UI
```

## Model calls

`DEFAULT_CONFIG` uses provider `openai` for both LLM and embedder. mem0's OpenAI LLM reads
`OPENAI_BASE_URL`; its embedder reads `OPENAI_API_BASE` then `OPENAI_BASE_URL`. Gooclaim
sets `OPENAI_BASE_URL` to the LiteLLM gateway and `OPENAI_API_KEY` to a gateway virtual key;
`MEM0_DEFAULT_LLM_MODEL` should be a gateway alias. Nothing in this repo enforces that —
it is pure configuration. The server sends no `user` (tenant) field on model calls.

## Commands

```bash
# server stack (from server/)
make up | make down | make health | make logs
make bootstrap                      # first admin + API key from the terminal
make prune-logs                     # trims request_logs (REQUEST_LOG_RETENTION_DAYS)
make reset-admin-password EMAIL=... PASSWORD=...

# upstream tests (repo root, Hatch)
make test                           # hatch run test -> pytest tests/
hatch run dev_py_3_12:pytest tests/test_server_auth.py tests/test_server_params.py tests/test_api_keys_router.py
make lint                           # ruff
```

## Non-negotiable rules

- Every model call through the LiteLLM gateway. Never put a provider key in the env and
  never switch the provider to `anthropic`/`gemini` (env or `POST /configure`).
- Precedent namespace (`user_id` + `agent_id`) is fixed by the memory MCP, never by a caller.
  A per-tenant consumer gets its own namespace.
- Never store tenant row values or member data; column names and codes only.
- `MEM0_TELEMETRY=false` in any Gooclaim environment.
- Never `AUTH_DISABLED=true` outside a laptop.
- Docs: English only; no secrets, IPs, hostnames, account ids or task ids in README/docs.
- Never commit changes you did not write; never commit `.env`.

## Do not touch without discussion

- Upstream code outside `server/` and the marked deviations — keep the diff rebase-friendly.
- `server/alembic/` migrations (upstream-owned chain).
- The `litellm` upper bound in `pyproject.toml`.
- `docs/` outside `docs/gooclaim/`; `AGENTS.md`, `LLM.md` (upstream files).

## Branches and merging upstream

`release/dev` is the default and deployable branch. `main` mirrors upstream (still at the
fork base). Flow: `feature|fix|chore|docs/<x>` → `release/dev` → `release/uat` →
`release/prd`. To adopt upstream: fetch `upstream`, update `main`, merge into
`release/dev`, re-check every fork change above survived. No server CI — run tests locally.

## Deployment (dev)

The `server/` stack runs as Docker Compose containers on a dev EC2 instance (AWS). It is
not deployed through the platform's per-service deploy script; the platform's direct-AI
`audit` check covers its containers. Its `.env` lives on the instance. No Kubernetes, no
Azure, no Key Vault.
