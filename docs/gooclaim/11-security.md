# 11 — Security

## Access

- Auth is on by default. `AUTH_DISABLED=true` opens every route and is for a laptop only.
- Services use `X-API-Key`. Gooclaim's memory MCP sends `ADMIN_API_KEY`, which carries the
  admin role: it can also call `POST /configure`, bulk delete and `/reset`. The memory MCP
  limits what callers can do by exposing only add, search, list and delete-by-id.
- Dashboard users sign in with email and password (bcrypt), get 30-minute JWTs and
  single-use 30-day refresh tokens. Register, login and refresh are rate-limited per IP
  (5, 10 and 20 per minute).
- Dashboard API keys are stored only as bcrypt hashes; the full key is shown once.
- This server does not use `gooclaim-auth` tokens. Gooclaim identity is enforced one hop
  earlier, by the memory MCP's auth middleware.

## Secrets

Secrets reach the containers as environment variables from the instance's `server/.env`:
`OPENAI_API_KEY` (a LiteLLM gateway virtual key, never a provider key), `JWT_SECRET`,
`ADMIN_API_KEY`, `POSTGRES_PASSWORD`. The file is never committed. `GET /configure`
redacts keys named like `api_key`, `password`, `secret`, `token`.

## Model access

All model traffic must go to the LiteLLM gateway (`OPENAI_BASE_URL`). The image also
bundles the Anthropic and Google SDKs, and `POST /configure` would accept those providers;
using them would bypass the gateway. The platform's direct-AI `audit` check flags provider
keys in running containers.

## Data rules

- Precedent stores schema, not member data: column names, canonical fields, a tenant's own
  code values, and a one-way tenant reference. Never a value from a tenant's file.
- The namespace is fixed by the memory MCP. A future consumer whose memories are about
  people must get a separate namespace that never crosses tenants.
- Memory text also lands in the SQLite history file and in Postgres; both must be treated
  as the same sensitivity as the memories.

## Telemetry

Both the server (`server/telemetry.py`) and the mem0 library send anonymous events to
mem0's PostHog project unless `MEM0_TELEMETRY=false`. The server's onboarding events carry
the admin's email domain and the setup wizard's use-case text. Gooclaim environments set
`MEM0_TELEMETRY=false`.

## Supply chain

- `pyproject.toml` caps `litellm` below 1.107.0 (a compromised release). The server image
  does not install the `llms` extra, so this guards development installs of this tree.
- The server runs this repository's own `mem0/`, installed into the image from the checked-out
  commit; `server/requirements.txt` does not name `mem0ai` and the compose start command installs
  nothing (`tests/test_gooclaim_mem0_comes_from_this_repo.py`). Other dependencies are still
  version ranges, resolved at build time.
- A root `.dockerignore` keeps `.env` files, `.git` and `node_modules` out of the images.
