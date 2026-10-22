# 06 — Deployment

## Where it runs

Only on **dev**, on AWS: the `server/` stack (API, dashboard, pgvector Postgres) runs as
Docker containers on a dev EC2 instance, managed with Docker Compose. There is no UAT or
production deployment, and nothing runs on Kubernetes, Azure or Azure Key Vault.

Unlike Gooclaim's own services, this stack is **not** deployed through the platform's
per-service deploy script. The platform's direct-AI check (`gooclaim-infra`,
`scripts/no_direct_ai.py`) covers it only in its `audit` mode, which inspects every
running container for provider keys.

## Deploying a change

1. Merge to `release/dev` and run the tests locally (there is no server CI).
2. On the instance, bring the stack's code to the `release/dev` commit (ship only
   git-tracked files, for example from `git archive`; never copy a local `.env`).
3. Keep the instance's own `server/.env` (mode 600). It holds the gateway key, Postgres
   password, `JWT_SECRET` and `ADMIN_API_KEY`, and must not be committed or printed.
4. From `server/`: `docker compose up -d --build`.
   The `mem0` service runs `alembic upgrade head` before uvicorn, so app-database
   migrations apply on start.
5. Verify (see [07-operations](07-operations.md)): API `/docs` answers, `GET /configure`
   shows the gateway base URL and gateway model aliases, the memory MCP's `/ready` is
   healthy.

## Required environment on dev

`OPENAI_API_KEY` (gateway virtual key), `OPENAI_BASE_URL` (gateway `/v1`),
`MEM0_DEFAULT_LLM_MODEL` (gateway alias), `JWT_SECRET`, `ADMIN_API_KEY`,
`POSTGRES_PASSWORD`, `MEM0_TELEMETRY=false`, `DASHBOARD_URL` and
`NEXT_PUBLIC_API_URL` set to the public dashboard and API addresses,
`NEXT_PUBLIC_INSTANCE_NAME=Gooclaim Memory`.

## Rollback

- Code: check out the previous `release/dev` commit on the instance and
  `docker compose up -d --build` again.
- Data: the Postgres volume (`postgres_db`) and the `server/history` directory survive
  `docker compose down`; `docker compose down -v` (`make clean`) deletes the volume and
  every memory. Migrations have no automated down-path in this flow; back up the database
  before applying new ones.

## Notes

- The compose file reinstalls `mem0ai` from PyPI with no version pin every time the API
  container starts, so a restart can change the library version.
- `server/Dockerfile` (the fork-modified image) does not run migrations; if it is used
  instead of compose, run `alembic upgrade head` separately.
