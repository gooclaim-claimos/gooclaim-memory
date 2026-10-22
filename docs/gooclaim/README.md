# Gooclaim Memory — Gooclaim docs

These pages describe how Gooclaim runs this fork of mem0. Everything in `docs/` outside
this folder is upstream mem0's Mintlify site and is not maintained by Gooclaim.

| Page | Covers |
|---|---|
| [00-overview](00-overview.md) | What Gooclaim uses it for, and what it does not |
| [01-architecture](01-architecture.md) | The `server/` stack, data flow, how model calls reach the gateway |
| [03-apis](03-apis.md) | Routes, auth, and the subset Gooclaim calls |
| [05-configuration](05-configuration.md) | Environment variables for the API and dashboard |
| [06-deployment](06-deployment.md) | How the stack runs on dev |
| [07-operations](07-operations.md) | Health checks, admin tasks, state, common failures |
| [08-testing](08-testing.md) | Server tests and how to run them |
| [09-development](09-development.md) | Branches, fork changes, merging upstream |
| [11-security](11-security.md) | Auth, secrets, data rules, telemetry |
| [12-integrations](12-integrations.md) | The memory MCP, connector-hub, mapping MCP, LiteLLM |

Not included because nothing Gooclaim-specific applies: components (upstream code), data
model beyond what 01/07 cover, ADRs (none for this fork).
