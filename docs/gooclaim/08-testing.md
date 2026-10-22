# 08 — Testing

Gooclaim has added no tests of its own to this repository. The tests that cover what
Gooclaim runs are upstream's server tests, in the root `tests/` folder:

| File | Covers |
|---|---|
| `tests/test_server_auth.py` | Auth modes through FastAPI's TestClient (admin key, API keys, disabled mode, CRUD through auth) |
| `tests/test_server_params.py` | Request parameters passed through to `mem0.Memory` |
| `tests/test_api_keys_router.py` | `/api-keys` router |

They patch `Memory.from_config`, so they need no Postgres or model access.

## Running

From the repo root, with [Hatch](https://hatch.pypa.io/):

```bash
make test                                   # hatch run test -> pytest tests/ (whole upstream suite)
hatch run dev_py_3_12:pytest tests/test_server_auth.py tests/test_server_params.py tests/test_api_keys_router.py
make lint                                   # ruff check
```

The Hatch dev environments install the `llms` extra, so they resolve `litellm` within the
fork's `<1.107.0` cap.

There is no server CI for Gooclaim branches. Run the server tests locally before pushing to
`release/dev`.

## End-to-end check on dev

The meaningful proof is a round trip through the real stack:

1. Through the memory MCP (or directly with `X-API-Key`), `POST /memories` a synthetic
   memory with `infer=false` into a test namespace (not Precedent's).
2. `POST /search` for it and confirm it comes back with a score.
3. Confirm the gateway logged the embedding call under this service's key.
4. `DELETE /memories/{id}` to remove it.

Never use real tenant data for this.
