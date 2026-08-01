# GOOCLAIM — Fork Notes

`mem0` is a **fork** of the upstream [mem0ai/mem0](https://github.com/mem0ai/mem0),
deployed as **Gooclaim Memory** (long-term semantic memory: `mem0` API + `mem0-dashboard`
+ `mem0-pgvector`). Upstream code + docs are unchanged; this file records the Gooclaim-specific
conventions layered on top.

## Branch strategy (Gooclaim)
- **`main`** — upstream mirror. Sync upstream here; do NOT put Gooclaim changes on main.
- **`develop`** — Gooclaim Memory customizations (deploy config, provider wiring).
- **`release/dev`** (default) — deployable dev branch (= our customizations). Maintainer direct-push; others PR + review.
- **`release/uat` / `release/prd`** — promotion branches (PR + review/approval).

Flow for our changes: `feature/fix/chore/docs/* → release/dev → release/uat → release/prd`.
Pull upstream into `main`, then merge `main → develop → release/dev` to adopt upstream updates.

## Deploy (auralixy)
- Runs on `mem0` namespace: `mem0` (API) · `mem0-dashboard` · `mem0-pgvector`.
- OpenAI-direct (`OPENAI_API_KEY`, `MEM0_DEFAULT_LLM_MODEL=gpt-4.1`, `text-embedding-3-small`).
- Image via `az acr build` → `gcdevacrcinax` ACR; secrets via Azure Key Vault (ESO).

## Push gate
No server CI on the Gooclaim side. Keep changes minimal + rebase-friendly against upstream.

## Do not
- Don't rewrite upstream README/docs — record Gooclaim specifics here.
- Don't commit secrets; `.env` stays local / AKV.

