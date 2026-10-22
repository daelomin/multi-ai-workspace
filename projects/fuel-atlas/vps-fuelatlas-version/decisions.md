# decisions.md — HUMAN decisions (Fuel Atlas portable deploy)

Records decisions **Joe has settled**. Reviewers treat settled entries as fixed; entries still `PROPOSED` are drafts and are **not** fixed. This file carries forward the four review-loop decisions (FB-D1…D4) and adds two decisions surfaced by the M0 code inventory (INV-D1, INV-D2).

## How to read an entry

- **Question** — the fork being decided.
- **Evidence** — spec ref and/or inventory finding.
- **Options** — with trade-offs.
- **Recommended default** — unblocks planning; Joe confirms or overrides.
- **Status / Decision** — `PROPOSED` until Joe records a call (date + choice).

---

## FB-D1 — Diagnostics collector

- **Question:** Which bounded collector or spool receives Atlas diagnostics, and does it need egress beyond the local spool?
- **Evidence:** v1.3 defines the spool contract (`state/diagnostics/`, `ATLAS_DIAGNOSTIC_SPOOL_DIR`, `ATLAS_DIAGNOSTIC_SPOOL_CAP_BYTES`, N4) but not the destination choice. `cloudflared` output that cannot reach the spool is covered by its metrics and exit status (§12.2).
- **Options:**
  - **(a) File spool only** — diagnostics write to `state/diagnostics/` with a byte cap; no external collector. Rely on cloudflared metrics/exit-status for connector output.
  - **(b) External bounded collector** — add a remote sink (e.g. a self-hosted Loki/vector) and record its destination + egress in §4.2.
- **Recommended default:** **(a)** for the first release. No new egress surface, no new destination to inventory. Revisit (b) only if on-host forensics prove insufficient.
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T2.11**)

---

## FB-D2 — Release trust model for `release import`

- **Question:** How does the installation establish that a release package is authentic?
- **Evidence:** §8.1 allows either authenticated transport **or** a signed release manifest with a configured trust key.
- **Options:**
  - **(a) Authenticated transport + verified producer only** — trust comes from the channel (TLS + authenticated source), no key management.
  - **(b) Signed release manifests + configured trust key** — packages carry a signature checked against a configured key; transport-independent.
- **Recommended default:** **(a)** now; keep (b) as an envelope hook so a trust key can be added later without re-plumbing the import path.
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T3.1, T4.8**)

---

## FB-D3 — Leave-stopped flag

- **Question:** May a backup or restore ever leave the installation stopped on operator request?
- **Evidence:** backup/restore semantics (§10, S07) determine whether "stopped" is a valid end state.
- **Options:**
  - **(a) Never leave stopped** — always restore the recorded running set; no stopped end state.
  - **(b) Allow an explicit leave-stopped flag** — operator may request the install stay down after restore.
- **Recommended default:** **(a)** — a stopped end state after restore is a footgun on a shared host; add (b) only if a concrete workflow demands it.
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T4.9, T4.10**)

---

## FB-D4 — Serving-mode overlay refresh

- **Question:** Does serving mode get an overlay-refresh command, or is refresh always via worker/re-import?
- **Evidence:** v1.3 (N2) states serving mode has no overlay-refresh command. The alternative is `atlasctl overlay import` writing only `state/live`.
- **Options:**
  - **(a) Keep v1.3** — no refresh command; refresh needs the worker or a re-import of a serving package.
  - **(b) Add `atlasctl overlay import`** — serving mode can refresh `state/live` in place.
- **Recommended default:** **(a)**, revisited when the worker (M7) is scoped in detail.
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T3.6** scope)

---

## INV-D1 — Auth model (Better Auth vs Cloudflare Access) *(from M0 inventory)*

- **Question:** The running app uses **self-hosted Better Auth** at `/api/auth/*`, federated through a "Grok auth broker". Spec §5 mandates **Cloudflare Access JWT** at the edge + in-app principal mapping. Which is authoritative for the serving release?
- **Evidence:**
  - `inventory/routes.md` finding #1 — Better Auth is the shipped auth stack.
  - `inventory/routes.md` finding #2 — shipped default `VITE_AUTH_ENABLED=false` + no `DATABASE_URL` makes `requireUserId()` return the shared `dev-user`, so **every mutation is effectively unauthenticated** in the default serving config.
  - `spec.md` §5 — Cloudflare Access JWT + Access apps/audiences is the mandated model (A06/A17/S08).
- **Options:**
  - **(a) Migrate to Cloudflare Access and strip Better Auth from the serving image** — matches §5, removes the broker federation, drops the DB dependency (ties to INV-D2 option 1). Cost: the §5 auth layer (T2.3–T2.8) is already scoped for it, but self-hosted user accounts are **removed**.
  - **(b) Retain Better Auth against a real Postgres** — self-hosted accounts survive; Cloudflare Access becomes an optional wrapper. Contradicts §5 as written and needs a spec change.
  - **(c) Dual** — Cloudflare Access for admin/control routes, Better Auth for end-user self-hosted accounts. Two trust boundaries, most complexity.
- **Recommended default:** **(a)**, consistent with §5 and with the INV-D2 default. **Explicitly confirm** the scope loss: (a) removes the self-hosted account feature (and its `/api/auth/*` surface).
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T2.3–T2.8**; coupled to INV-D2)

---

## INV-D2 — Database in serving mode *(from M0 inventory)*

- **Question:** The DB is used only by Better Auth; core data is served from GeoJSON. The default fallback is in-memory PGLite (resets on restart — §6.2 violation), and `npm run build` runs `db:migrate` (§6.1 violation). What should serving mode ship?
- **Evidence:**
  - `inventory/db-usage.md` — "the database is used only by Better Auth (identity + sessions)"; no application-data tables.
  - `inventory/db-usage.md` — PGLite in-memory is the default when `DATABASE_URL` is unset; `getSql()` has zero callers outside the auth stack.
- **Options:**
  - **(1) Drop the DB entirely in serving mode** — if Cloudflare Access replaces Better Auth (INV-D1 a), nothing needs SQL; strip `db.ts` + the PGLite path from the image. Lowest scope, matches §5.
  - **(2) Keep Postgres only for auth** — run Better Auth against a real, persistent PostgreSQL service (volume + backup); disable the PGLite fallback in production.
  - **(3) Keep the scaffold but unused** — ship `db.ts` without a migration step; no DB at runtime until a feature needs it.
- **Recommended default:** **(1)** for the serving release (pairs with INV-D1 option a). If INV-D1 resolves to (b)/(c) self-hosted auth, then **(2)** becomes the default.
- **Status / Decision:** `PROPOSED` — Joe: ________ (unblocks **T1.4, T6.1**; coupled to INV-D1)

---

## Not decisions (already settled by spec — recorded for transparency)

These inventory findings look decision-like but are already mandated by the spec; no Joe call needed. They map to existing ACTION-PLAN tasks.

| Finding | Spec mandate | Task |
|---|---|---|
| Rebuild-on-read in GET chargers/geojson | §8.1 — serving mode must not rebuild on read | T1.9 / T3.5 |
| State-changing GET (`/api/night-run`) | §5.3 — no state change via GET | T2.8 |
| No `/internal/healthz`/`readyz` | A16 — probes must exist | T1.7 |
| Grok connector bridge (`app-data/`) reachable | §5.3 — unknown/control routes → deny | gate/remove (T2.4) |
| Multiplayer `/api/rtc` dead code | §5.3 — no unclassified routes | drop (lean) or wire |
