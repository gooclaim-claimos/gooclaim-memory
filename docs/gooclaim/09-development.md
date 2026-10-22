# 09 — Development

## Branches

| Branch | State |
|---|---|
| `release/dev` | Default and deployable. Upstream `42cf18c` + the three Gooclaim commits |
| `release/uat` | Lacks the `litellm` cap commit |
| `release/prd` | Lacks the fork-notes and `litellm` cap commits |
| `develop` | Lacks the fork-notes and `litellm` cap commits |
| `main` | Upstream mirror, still at `42cf18c` (not synced since the fork) |

Flow for Gooclaim changes: `feature|fix|chore|docs/<x>` → `release/dev` → `release/uat` →
`release/prd`. No Gooclaim changes on `main`.

## Fork changes

`git log --oneline upstream/main..HEAD`:

| Commit | What |
|---|---|
| Gooclaim Memory customizations (dev deploy) | `server/Dockerfile` (libpq5, `psycopg[binary]`, no `--reload`); `server/main.py` OpenAPI title/description; dashboard branding and removal of the "Cloud features (Pro)" nav |
| docs(gooclaim): fork notes | `GOOCLAIM-FORK.md` |
| fix(deps): cap litellm below 1.107.0 | `pyproject.toml` `llms` extra: `litellm>=1.83.7,<1.107.0`, marked `GOOCLAIM DEVIATION` |

Rules for new changes:

- Change as little upstream code as possible; prefer configuration.
- Mark every deviation in the file (`GOOCLAIM DEVIATION` comment) so a merge does not drop
  it silently.
- Gooclaim documentation goes in `README.md`, `CLAUDE.md` and `docs/gooclaim/` only.

## Merging upstream

```bash
git fetch upstream
git checkout main && git merge --ff-only upstream/main && git push origin main
git checkout release/dev && git merge main      # or a feature branch off release/dev
```

Then check, in order:

1. `pyproject.toml` still carries the `litellm` upper bound.
2. `server/Dockerfile` still installs libpq / `psycopg[binary]`.
3. `server/main.py` still has the Gooclaim title (conflicts here are cosmetic).
4. Dashboard branding files and the removed Pro nav (`main-nav.tsx`) — upstream edits to
   the dashboard will conflict here most often.
5. `README.md` / `CLAUDE.md`: keep Gooclaim's versions; upstream's are in `AGENTS.md` and
   upstream's own history.
6. Any change to `server/main.py` `DEFAULT_CONFIG`, `server/auth.py`, `server/alembic/`,
   or the routes the memory MCP calls (`/memories`, `/search`) — re-run the server tests
   and the end-to-end check in [08-testing](08-testing.md).

## GOOCLAIM-FORK.md

Kept as written. Its branch section matches this page; its **Deploy** section is stale:
it describes an Azure/AKS deployment (namespace, ACR image builds, Key Vault secrets) and
OpenAI-direct model access with `gpt-4.1`. None of that is current: dev runs on AWS with
Docker Compose and model calls go through the LiteLLM gateway.
