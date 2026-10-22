# 12 — Integrations

## Inbound: who calls Gooclaim Memory

### gooclaim-memory-mcp (`gooclaim-mcp-server/services/memory`)

The only Gooclaim service that calls this API. It exposes MCP tools on `/mcp/memory/` and
matching REST routes:

| Memory MCP route / tool | Calls on Gooclaim Memory |
|---|---|
| `POST /v1/memory/add` · `add_memories` | `POST /memories` with `messages=[{role:user, content:text}]`, the fixed `user_id` + `agent_id`, `metadata`, `infer` |
| `POST /v1/memory/search` · `search_memory` | `POST /search` with `query`, `user_id`, `agent_id`, `top_k` |
| `GET /v1/memory/list` · `list_memories` | `GET /memories?user_id=&agent_id=&top_k=` |
| `POST /v1/memory/delete` · `delete_memories` | `DELETE /memories/{id}`, one call per id |
| `get_health` / `/ready` | `GET /memories` with `top_k=1` |

It sends `X-API-Key` (its `MEMORY_API_KEY` = this server's `ADMIN_API_KEY`), stores
nothing itself, and wraps every answer as `{"result": <this server's answer>}`. It treats
5xx or no connection as "memory unavailable" and 4xx as "request rejected", and it does
not expose bulk delete.

### connector-hub (writes, via the memory MCP)

On mapping activation, connector-hub posts one memory per column decision and per value
decision to the memory MCP's `/v1/memory/add`, with `infer=False` and metadata carrying the
column key, canonical field and a one-way tenant reference. Failures are logged and never
block the activation.

### mapping MCP (reads, via the memory MCP)

`recall_mapping_precedent` posts one `/v1/memory/search` per column, keeps only results
whose stored column key matches exactly, and counts distinct tenant references. An
unreachable memory or an unrecognised answer shape is reported as "could not ask", never
as "no precedent".

## Outbound: what Gooclaim Memory calls

| Dependency | How |
|---|---|
| LiteLLM gateway | OpenAI-compatible `/v1` API via `OPENAI_BASE_URL` + `OPENAI_API_KEY`; embeddings (`MEM0_DEFAULT_EMBEDDER_MODEL`) and, when `infer` is true or `/generate-instructions` is called, chat completions (`MEM0_DEFAULT_LLM_MODEL`) |
| Postgres + pgvector | Vector table and app database (`POSTGRES_*`, `APP_DB_NAME`) |
| PostHog (mem0's) | Only if `MEM0_TELEMETRY` is not `false` |

No calls to the audit bus, `gooclaim-auth`, Redis or Temporal.
