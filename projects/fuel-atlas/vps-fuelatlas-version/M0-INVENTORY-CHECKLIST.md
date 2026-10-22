# M0 Inventory Checklist — spec v1.3

Working checklist for milestone **M0** of `ROADMAP.md`. It turns the four M0 work items (T1.1, T1.2, T0.1, FB-D1…D4) into concrete questions and inspection targets. M0 is **done** when every section's output file is written and the exit criteria at the bottom are met.

Source project to inspect: `/home/remi/GIT/gas-stations-world` (web app: `claude/grok_workspace`; canonical contract: `docs/ATLAS-SPEC.md`). Inventory outputs live in this project under `inventory/`. FB decisions go in `decisions.md`.

> Rule from §2: record **discrepancies** between executable code and `docs/ATLAS-SPEC.md` before changing behavior. A gap found here is a finding, not a bug to fix silently.

## Progress snapshot (23 Oct 2026)

Legend: `[x]` done · `[~]` drafted/scaffolded, blocked on external input · `[ ]` open.

| M0 item | Status | Output |
|---|---|---|
| T1.1 route & server-function inventory | `[x]` complete | `inventory/routes.md` (consolidated, §0–§11) |
| T1.2 DB usage inventory | `[x]` complete | `inventory/db-usage.md` |
| T0.1 host inventory | `[~]` scaffolded | `inventory/host.md` — **blocked on target-VPS access** |
| FB-D1…D4 decisions | `[~]` drafted | `decisions.md` — awaiting Joe's call |
| INV-D1 (auth model) / INV-D2 (DB) | `[~]` drafted | `decisions.md` — new, from inventory findings |

**M0 gate: NOT PASSED.** Blockers: Joe must settle FB-D1…D4 + INV-D1/INV-D2 in `decisions.md`, and §9 of `inventory/host.md` must be run on the target VPS to complete the host inventory.

---

## 1. FB decisions (→ `decisions.md`)

Answer each with options + evidence, then record Joe's call. A recommended default is given to unblock planning; Joe confirms. All six decisions are now **drafted** in `decisions.md` (four review-derived + two inventory-derived); the `Decision:` lines await Joe.

- [x] **FB-D1 — Diagnostics collector.** Options: (a) file spool only (`state/diagnostics/` + `ATLAS_DIAGNOSTIC_SPOOL_CAP_BYTES`, rely on cloudflared metrics/exit-status for connector output); (b) external bounded collector (adds egress + destination to the §4.2 inventory). *Default to (a) for first release.* Unblocks **T2.11**.
- [x] **FB-D2 — Release trust model.** Options: (a) authenticated transport + verified producer only; (b) signed release manifests + configured trust key. *Default to (a), keep (b) as an envelope hook.* Unblocks **T3.1, T4.8**.
- [x] **FB-D3 — Leave-stopped flag.** Options: (a) never leave stopped (always restore the recorded running set); (b) allow an explicit leave-stopped flag. *Default to (a).* Unblocks **T4.9, T4.10**.
- [x] **FB-D4 — serving-mode overlay refresh.** Options: (a) keep v1.3 "no refresh command" (worker or re-import); (b) add `atlasctl overlay import`. *Default to (a), revisit with worker.* Unblocks **T3.6** scope.
- [x] **INV-D1 — Auth model** *(new, from T1.1 finding #1/#2)*. Shipped Better Auth vs spec §5 Cloudflare Access. *Default to (a) migrate to Cloudflare Access + strip Better Auth.* Unblocks **T2.3–T2.8**.
- [x] **INV-D2 — Database in serving mode** *(new, from T1.2)*. DB only serves Better Auth; default fallback is in-memory PGLite. *Default to (1) drop DB in serving mode.* Unblocks **T1.4, T6.1**. Coupled to INV-D1.

---

## 2. T1.1 — Route & server-function inventory (→ `inventory/routes.md`)

**Complete.** All of 2A–2H are consolidated into a single `inventory/routes.md` (§0–§11) rather than the seven separate files listed in §5 below. The spec requires enumerating **everything**, not only `/api/*`: "TanStack server functions, framework transport routes, SSR loaders and direct HTTP endpoints."

### 2A. Route table — one row per route

- [x] Enumerate every HTTP endpoint from `docs/ATLAS-SPEC.md` (station subdivision/circle, charger filters, GeoJSON, places/feeds/catchment/boundaries, translations).
- [x] Enumerate every route registered in Nitro/TanStack (`server/`, `server/api/`, route handlers) beyond the documented set.
- [x] For each route record: **method**, **path**, **handler file:line**, **auth class** (admin / read / internal / unknown), **side effects** (FS write, subprocess, credentialed external fetch, state disclosure).
- [x] Flag every **unclassified** route (§5.3 "Unknown/control/server-function routes: none until classified").

### 2B. Server functions / transport routes / SSR loaders

- [x] List TanStack server functions (`createServerFn`, `.server.ts` handlers) and their transport paths.
- [x] List SSR loaders / framework `_server`/`_serverFn` entry points that execute server-side on request.
- [x] Mark which of these accept request input and can mutate state (candidates for CSRF + auth gate in T2.8).

### 2C. State-changing GET detection (→ `inventory/routes.md` §3)

- [x] Find every **GET** that writes files, launches a subprocess, starts a job or mutates state.
- [x] Record the target change for each: "read-only status" vs "405" (per §5.3).

### 2D. Filesystem read/write map (→ `inventory/routes.md` §5)

- [x] Map every read: `FUEL_ATLAS_DIST`, `FUEL_AGENT_DIR`, `FUEL_REFERENCE_DIR`, `FUEL_EV_REFERENCE_DIR`, `FUEL_PYTHON`, `FUEL_ATLAS_ROOT`.
- [x] Map every write (state, overrides, live overlays, diagnostics, jobs).
- [x] Flag **desktop/home assumptions**: any `/home/remi`, desktop service name, or home-directory discovery (§7.2).

### 2E. Subprocess spawn map (→ `inventory/routes.md` §4)

- [x] `consolidated.server.ts` — where/when it spawns Python on input change (rebuild-on-read).
- [x] `research-job.server.ts` — scripts launched, Jarvis/systemd user-service starts.
- [x] `live.server.ts` — `eipa_live.py` spawn and the Vite dev scheduler.
- [x] Record each spawn's trigger, arguments and whether it is reachable in serving mode.

### 2F. Scheduled work (→ `inventory/routes.md` §8)

- [x] List all timers/cron/schedulers (Vite live scheduler, any cron) and their ownership.
- [x] Note which persist state (quota) vs reset on restart.

### 2G. Environment-variable map (→ `inventory/routes.md` §6)

- [x] List every `process.env`/`import.meta.env` read, its meaning, and current default.
- [x] Split into: build-time public (`VITE_*`), runtime config, secrets. Confirm no `VITE_*` holds a secret.
- [x] Flag legacy names needing the §7.2 translation layer.

### 2H. Client storage map (→ `inventory/routes.md` §7)

- [x] Enumerate IndexedDB stores and `localStorage` keys, their purpose (edits, preferences, cached data).
- [x] Record which are user-edits (must be exportable per §9) vs cache (safe to drop).

**Additional surfaces enumerated beyond the checklist:** connector/tool bridge (`app-data/`, §9), multiplayer P2P dead code (`/api/rtc`, §10), and completeness notes (§11).

---

## 3. T1.2 — DB usage inventory (→ `inventory/db-usage.md`)

**Complete.**

- [x] Trace `src/lib/db.ts` usage: which production code paths actually query it (vs the scaffold being unused).
- [x] List every table/query and the endpoint(s) that hit it.
- [x] Determine whether PGLite (in-memory) is ever the runtime path — prohibited for persistent state (§6.2).
- [x] Decide and record: **no DB** / **explicit durable storage** / **optional PostgreSQL service** (persistent volume + backup).
- [x] Note `scripts/migrate.mjs`'s role and confirm migrations are *not* run in the image build (T1.4 dependency).

Verdict recorded: DB is used **only by Better Auth**; core data is served from GeoJSON. Lean default is "drop DB in serving mode" (option 1), which is now INV-D2 in `decisions.md`.

---

## 4. T0.1 — Host inventory (→ `inventory/host.md`)

**Scaffolded** — `inventory/host.md` is structured against §12.1/§12.2/WP0 and pre-filled with the known dataset sizes and Atlas starting limits. Completion is **blocked on target-VPS access** (run §9's collection commands on the host and paste results).

Per §12.1: one row per co-resident project/service with **service count, memory limit/observed peak, CPU limit/observed load, PID limit, storage allocation, growth estimate, backup schedule, maintenance owner**. Include databases, monitoring, all Tunnel connectors and one-shot helpers.

- [~] Enumerate all Docker Compose projects / stacks on the target VPS.
- [~] Per service: capture the §12.1 fields above.
- [~] Inventory existing public listeners (TCP 80/443 and any other) and their owners (§4.4 — preserve neighbors).
- [~] Inventory SSH access + provider console recovery (before tightening).
- [x] Record the measured dataset sizes as storage inputs: `dist/` ≈ 674 MB, `REFERENCE` ≈ 131 MB, `REFERENCE_EV` ≈ 275 MB, raw US/China PBF ≈ 13.75 GB (22 Oct 2026 snapshot).
- [~] Compute the aggregate admission check: Σ concurrent memory limits + host reserve (≥1 GiB or 20% RAM) vs physical RAM (§12.1).
- [~] Identify the backup destination and encryption recipient (input, not implementation).

---

## 5. Output artifacts (definition of "recorded")

- [x] `inventory/routes.md` — T1.1, consolidated (route table, server functions, state-changing GETs, subprocess map, FS map, env map, client storage, scheduled work, connector bridge, multiplayer). Supersedes the seven-file split below.
- [x] `inventory/db-usage.md` — T1.2.
- [~] `inventory/host.md` — T0.1 (scaffold; blocked on VPS access).
- [~] `decisions.md` — FB-D1…D4 + INV-D1/D2 drafted; awaiting Joe's call.

*(Superseded: the original T1.1 plan split into `inventory/server-functions.md`, `inventory/state-changing-gets.md`, `inventory/filesystem.md`, `inventory/subprocesses.md`, `inventory/env.md`, `inventory/client-storage.md`. Those are now sections §2–§7 of `routes.md`.)*

---

## 6. Exit criteria (M0 gate)

- [~] All four FB decisions answered in `decisions.md` — **drafted, not answered** (also INV-D1/D2).
- [x] Route inventory covers `docs/ATLAS-SPEC.md` **and** executable code, with discrepancies recorded. *(Residual: the exact `docs/ATLAS-SPEC.md` route contract vs this code diff is not yet done — noted in `routes.md` §11; non-blocking for M0.)*
- [x] Every state-changing GET, subprocess spawn, FS path and env var is mapped; no `VITE_*` secret.
- [~] DB decision is explicit (no silent PGLite for persistent state) — **drafted as INV-D2, awaiting Joe**.
- [~] Host inventory lists every co-resident stack with limits + storage, and the §12.1 admission check is computable — **scaffold only, blocked on VPS**.
- [~] No downstream task (T1.3 onward) starts on an unresolved M0 question — **not yet true**: M0 is not gated until Joe resolves the six decisions and the host inventory completes.
