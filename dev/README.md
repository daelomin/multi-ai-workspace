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
| `make -C dev smoke` | Run the end-to-end smoke test (P0-14), then open `web/smoke_map.html` |
| `make -C dev test` | Run the unit tests (no database needed) |

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

## Smoke test (P0-14)

```sh
make -C dev up
make -C dev smoke
```

Then open `web/smoke_map.html` in a browser: three fictional sites appear, coloured by speed, served by Martin from Postgres.

What it does:

1. Parses three **synthetic** DATEX II 2.2 files in `samples/datex/`: a measurement-site table, a measured-data publication, and a correction of one measurement.
2. Creates the Phase 0 measure model (`sql/001_measures.sql`): `measurement_site`, `traffic_measure` keyed on `(site_id, source, source_ts, source_version)` (D8, D11), the `traffic_measure_current` view, and the `site_latest_traffic` map view. `traffic_measure` becomes a hypertable when TimescaleDB is present.
3. Loads the files, re-delivers one of them, and checks: 3 sites; 4 raw rows (the correction is kept as a revision; the re-delivery adds nothing); the current view shows the corrected value; the map view has a speed for every site.

It only touches rows with `source = 'smoke'`, so it can be re-run safely.

Limits:

- **The sample files are synthetic.** Their structure follows DATEX II 2.2 but has not been validated against the official schema. The next step is to run the parser on real files from the open DIR feeds (`docs/data_sources.md`, S-1 and S-2).
- **Checked here:** parser, schema and loader against Postgres 16 + PostGIS, including the `make -C dev smoke` target. **Not checked here:** TimescaleDB (not installable in the build environment), Martin and the map page in a browser.
