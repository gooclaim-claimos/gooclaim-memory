# 00 — Overview

## What it is

Gooclaim Memory is the mem0 self-hosted server (`server/` in this repository) with light
Gooclaim branding. It stores short text memories with metadata, embeds them, and answers
similarity searches. Storage is Postgres with pgvector.

## What Gooclaim uses it for

**Precedent — the mapping memory.** When a tenant's CMS field mapping is activated by a
person, connector-hub records each decision: the tenant's column name, the canonical field
it maps to, and the tenant's own code values. When an agent later drafts a mapping for
another tenant, the mapping MCP recalls how other tenants mapped a column with the same
name and counts distinct tenants from the stored metadata.

Properties of that use:

- **Cross-tenant on purpose.** One fixed namespace (`user_id` + `agent_id`) for the whole
  platform, set in the memory MCP's configuration. The value is the aggregate ("most
  tenants mapped this column the same way").
- **Schema only.** Column names and code values, never row values from a tenant's file.
  The tenant is stored only as a one-way reference, enough to count distinct tenants.
- **Stored verbatim.** connector-hub writes with `infer=False`, so no LLM rewrites a
  decision; only the embedding model is called on write and on search.
- **Best effort.** A failed write never blocks a mapping activation; a failed recall is
  reported as "could not ask", never as "nothing remembered".

## What it does NOT do

- Not conversation memory: no channel, engine or Orion code calls it.
- Not member profiles: those live in the member registry, which deliberately does not use
  mem0.
- Not OpenMemory (`openmemory/`), a different mem0 product with a different API.
- Not the mem0 hosted platform, SDK clients, CLIs or editor plugins.

## Where it sits

```
connector-hub ─▶ gooclaim-memory-mcp ─▶ Gooclaim Memory API ─▶ LiteLLM gateway
mapping MCP   ─▶        (MCP + /v1)       (this repo, server/)     (embeddings, LLM)
```
