# DB usage inventory (T1.2)

Source inspected: `src/lib/db.ts`, `src/lib/auth/server.ts`, `src/lib/auth/pglite-dialect.ts`, `migrations/`. Generated 23 Oct 2026.

## Verdict

**The database is used only by Better Auth (identity + sessions). The core Fuel Atlas dataset is served from GeoJSON files, not SQL.** There are no application-data tables.

## Backend selection (`src/lib/db.ts`)

- `dbSource = "neon"` when `DATABASE_URL` is set → `pg` (node-postgres) Pool.
- `dbSource = "pglite"` otherwise → **in-memory PGLite** (Postgres-compiled-to-WASM), created with no persistent file (`new PGlite({...})`). **Resets on process restart.**
- Type-normalization layer maps `int8→number`, `date→'YYYY-MM-DD'`, `interval→text` so both backends return identical JSON shapes.

## Who actually uses it

`getSql()` is **defined but has zero callers in app data** — the only consumers are the auth stack:

| Consumer | How | Tables |
|---|---|---|
| `src/lib/auth/server.ts` | Better Auth `database` = `Pool` (Neon) or `pgliteDialect(() => getPglite())` (PGLite) | `user`, `session`, `account`, `verification` |
| `src/lib/auth/pglite-dialect.ts` | Kysely dialect over the shared PGLite instance | same |

No `0002_*.sql` app-data migration exists. The only migration is `migrations/auth/0001_auth.sql` (Better Auth CLI-generated schema, 4 tables + indexes).

## What this means against the spec

| Spec rule | Status |
|---|---|
| §2 "inventory actual usage; no silent ephemeral database" | **Confirmed**: PGLite is in-memory and would silently lose all auth state on restart. It is the default when `DATABASE_URL` is unset. |
| §6.2 "PGLite in memory is prohibited for persistent state" | **Violated by default** for auth state (only). Serving mode must either run Postgres or not run auth. |
| §6.1 "no DB migration in build; build without runtime secrets" | **Violated**: `npm run build` runs `npm run db:migrate` (`scripts/migrate.mjs`), which applies `migrations/auth` to a configured `DATABASE_URL` during build. |
| §6.2 "do not create a transient fallback database" | PGLite `createSql()` is lazy; production startup does not eagerly create it on the Neon path, but the fallback exists. |

## Decision to record (feeds T1.4, T6.1)

Three coherent options:

1. **Drop the DB entirely in serving mode** — if Cloudflare Access (§5) replaces Better Auth, nothing needs SQL; `db.ts` and the PGLite path are stripped from the image. (Lowest scope, matches §5.)
2. **Keep Postgres only for auth** — run Better Auth against a real, persistent PostgreSQL service (persistent volume + backup), and disable the PGLite fallback in production.
3. **Keep the scaffold but unused** — ship `db.ts` without a migration step; no DB at runtime until a future feature actually needs it.

The default serving deployment (§3.1) requires no worker and no editing; combined with §5's Cloudflare Access model, **option 1 is the lean default**, with option 2 as the path if self-hosted accounts are retained. Flag for Joe via `decisions.md`.
