# Development stack (Phase 0)

Postgres 16 with PostGIS and TimescaleDB, Redis, and the Martin vector-tile server, run with Docker Compose. This is the P0-13 scaffold; the stack itself is frozen by D1 (`DECISIONS.md`).

## Start

From the repository root:

```sh
make -C dev up
```

This creates `.env` from `.env.example` if it is missing (dummy development values only), starts the three services and waits until they are healthy.

**Proposed canonical bootstrap command:** `make -C dev up`. It becomes canonical only once HUMAN approves it; it is then recorded in `CONTRIBUTING.md` (P0-8 requires a reproducible bootstrap command, and `make` is not adopted without that approval).

Without `make`, the equivalent is:

```sh
cp -n .env.example .env
docker compose --env-file .env -f dev/docker-compose.yml up -d --wait
```

## Other commands

| Command | What it does |
|---|---|
| `make -C dev down` | Stop the stack, keep the data |
| `make -C dev reset` | Stop the stack and delete the database volume |
| `make -C dev logs` | Follow the logs |
| `make -C dev ps` | Show service status |
| `make -C dev psql` | Open a `psql` shell in the database |

## Services

| Service | Image | Port (host) | Notes |
|---|---|---|---|
| `db` | `timescale/timescaledb-ha:pg16` | `POSTGRES_PORT` (5432) | Extensions created by `db/init/001_extensions.sql` on first start |
| `redis` | `redis:7-alpine` | `REDIS_PORT` (6379) | Cache and streams (Phase 1+) |
| `martin` | `ghcr.io/maplibre/martin:latest` | `MARTIN_PORT` (3000) | Publishes every table and view with a geometry column; catalogue at `http://localhost:3000/catalog` |

## Python

Python tooling uses `uv` (D2):

```sh
uv sync
uv run pytest
```

Host-side tools read `DATABASE_URL` and `REDIS_URL` from `.env`.

## Known limits of this scaffold

- **Not yet started for real.** The compose file passes `docker compose config`, but the images could not be pulled in the environment where it was written (registry access blocked). The first `make -C dev up` on a real machine is the actual test.
- **Image tags are not pinned yet.** Pin exact `timescaledb-ha` and `martin` tags once the first start succeeds.
- **Not production settings.** Passwords in `.env.example` are dummy development values; see the credential policy in `CONTRIBUTING.md`.
