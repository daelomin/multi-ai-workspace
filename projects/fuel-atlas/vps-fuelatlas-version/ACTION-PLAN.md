# Fuel Atlas — Implementation Action Plan (spec v1.3)

Derived from `spec.md` v1.3 (22 Oct 2026). Itemized unitary development tasks grouped by work package (WP0–WP6). Each task carries a short executive summary, its spec reference and the acceptance criteria it discharges. Order within a package is the natural build order; packages WP0–WP5 are on the serving-release critical path, WP6 is the optional worker milestone.

## 0. Gating decisions (resolve before the affected task)

Four decisions remain open for HUMAN (from `reviews/round-2/CONSOLIDATION.md`). They gate, but do not block, the tasks they feed.

| ID | Decision | Gates |
|---|---|---|
| FB-D1 | Diagnostics collector: which bounded collector/spool + cap + egress (or "spool + cloudflared metrics/exit-status only") | T1.9, T2.11, T4.13 (S06) |
| FB-D2 | Release trust model for `release import`: authenticated transport only, or signed manifests + configured trust key | T3.1, T4.8 |
| FB-D3 | Leave-stopped flag: may backup/restore ever leave an installation stopped on operator request | T4.9, T4.10 |
| FB-D4 | Serving-mode overlay refresh: keep "no refresh command" (v1.3) or add `atlasctl overlay import` | T3.6 |

---

## WP0 — Shared-host contract

### T0.1 · Host inventory & ownership registry
**Summary:** Produce a host-wide inventory of every co-resident stack (service count, memory/CPU/PID limits, observed peaks, storage allocation, backup schedule, maintenance owner). It is the single source for capacity admission and the sibling-app acceptance tests.
**Spec:** §12.1, §11.2. **Acceptance:** S04. **Depends on:** none.

### T0.2 · Installation identity & collision preflight
**Summary:** Implement immutable `ATLAS_INSTALLATION_ID`, explicit `COMPOSE_PROJECT_NAME` and canonical `ATLAS_INSTALL_ROOT`, with uniqueness validation and preflight checks for project/network/volume/mount/storage-root collisions before any mutation.
**Spec:** §4.0. **Acceptance:** S01. **Depends on:** none (identity model; collision *checks* are implemented in T4.4).

### T0.3 · Host runbook (firewall, SSH, recovery)
**Summary:** Write and exercise the host runbook: inventory existing public listeners, preserve approved neighbor connectivity, deny only host ports that would publish Atlas (not container addresses), restrict SSH, keep provider recovery, and re-run A05 after any change.
**Spec:** §4.4, §11.2. **Acceptance:** A05. **Depends on:** T0.1.

### T0.4 · Sibling test application
**Summary:** Stand up a running neighboring Docker application with known IDs, health, network, data hashes and reachability, to prove Atlas deploy/update/stop/restore never disturbs it.
**Spec:** §12.1, §13 (WP0). **Acceptance:** S02, S03. **Depends on:** T0.1.

### T0.5 · Aggregate capacity admission model
**Summary:** Implement the admission math: sum of concurrent container/helper memory limits + host reserve (≥1 GiB or 20% RAM) must fit physical RAM; account per-service ceilings with `mem_limit`/`cpus`/`pids_limit`/swap, and verify effective settings by Docker inspection.
**Spec:** §12.1. **Acceptance:** S04. **Depends on:** T0.1.

---

## WP1 — Inventory & portable runtime

### T1.1 · Route & server-function inventory
**Summary:** Enumerate every route, TanStack server function, SSR loader, framework transport route, subprocess spawn, filesystem read/write and environment read in the existing app, recording discrepancies against `docs/ATLAS-SPEC.md` before changing behavior.
**Spec:** §5.3, §9. **Acceptance:** A07 (baseline). **Depends on:** none.

### T1.2 · Actual DB-usage inventory
**Summary:** Determine whether production state truly needs SQL; if not, keep the scaffold unused; if yes, use explicit durable storage (or an optional PostgreSQL service with a persistent volume + backup). PGLite in memory is prohibited for persistent state.
**Spec:** §2, §6.2. **Acceptance:** A09. **Depends on:** T1.1.

### T1.3 · Portable build/start entrypoints
**Summary:** Add `build:portable` and `start:portable` using the pinned Nitro version's supported standalone Node preset (verify the actual `.output` layout, not an assumed `node-server`), preserving `serverDir: './server'` and middleware/PWA hooks.
**Spec:** §6.1. **Acceptance:** A01. **Depends on:** T1.1.

### T1.4 · Decouple build from migrations & secrets
**Summary:** Remove `db:migrate` and any runtime-secret access from the build; compilation must not contact or migrate a database, and `.env*`/credentials must be excluded from the image context.
**Spec:** §6.1. **Acceptance:** A03. **Depends on:** T1.2.

### T1.5 · Multi-stage web Dockerfile + `.dockerignore`
**Summary:** Author the multi-stage image: pinned Node release satisfying the app, lockfile `npm ci`, pinned base digest, runtime stage with compiled server + static assets + packaged catalogs + attribution, and a `.dockerignore` excluding secrets, raw PBFs, caches, `.git`, `node_modules`.
**Spec:** §6.1. **Acceptance:** A02, A03. **Depends on:** T1.3, T1.4.

### T1.6 · Runtime hardening
**Summary:** Run as a fixed non-root UID/GID with read-only root filesystem, bounded tmpfs, dropped capabilities, `no-new-privileges`, explicit resource limits, graceful SIGTERM and Compose restart policy; host init sets mount ownership without recursive chmod/chown.
**Spec:** §6.2, §7.1. **Acceptance:** A09. **Depends on:** T1.5.

### T1.7 · Internal health/readiness endpoints
**Summary:** Add `/internal/healthz` (liveness) and `/internal/readyz` (readiness requiring a verified usable release, not every feed/country); minimal, credential-free output; served only to loopback/probe source (§2.7 covers that).
**Spec:** §6.2, §9. **Acceptance:** A16. **Depends on:** T1.6.

### T1.8 · Runtime config module & env translation layer
**Summary:** Centralize validation of all settings; report missing setting names without printing contents; translate legacy env names; reject `/home/remi`, desktop service names, home discovery and dev executables; ensure `VITE_*` never carries secrets and hostnames/auth are runtime-configurable without rebuild.
**Spec:** §7.2. **Acceptance:** A02. **Depends on:** T1.1.

### T1.9 · Serving-mode safe import (disable rebuild-on-read / research / live spawn)
**Summary:** Disable all on-read rebuilds, research-job spawning, Jarvis/systemd service launches and Vite live scheduler in production; serving mode imports safely without the worker checkout; missing release files cause explicit errors and readiness failure, never silent reconstruction.
**Spec:** §2, §3.1, §8.1. **Acceptance:** A02, W04. **Depends on:** T1.1.

### T1.10 · Runtime asset packaging & catalog inventory
**Summary:** Explicitly inventory and package (or mount) every required boundary/place/catalog asset so production never implicitly fetches data as a substitute for missing release data.
**Spec:** §6.1. **Acceptance:** A02. **Depends on:** T1.1.

---

## WP2 — Tunnel & authorization

### T2.1 · Compose network/secret shape
**Summary:** Author `compose.yaml`: pinned `atlas-web` + `cloudflared`, project-scoped bridge, zero `ports:`, no `network_mode: host`/privileged/socket, file-backed tunnel secret, healthcheck, resource/log limits, worker profile, and helper images pinned for offline exports.
**Spec:** §4.2, §6.3. **Acceptance:** A04. **Depends on:** T1.5, T0.2.

### T2.2 · Cloudflare named Tunnel + DNS + hostnames
**Summary:** Create one remotely managed named Tunnel per app/environment with owner-supplied `atlas.<domain>` and `atlas-api.<domain>` hostnames resolving only to the Tunnel; no quick/temporary Tunnel; maintain a non-secret config inventory (tunnel ID/name, mappings, Access app IDs/audiences, policies, DNS).
**Spec:** §4.1, §11.2. **Acceptance:** S03, A05. **Depends on:** T2.1.

### T2.3 · Access applications, policies & machine consumers
**Summary:** Define admin identity allowlist + consumer Service Auth policy with distinct audiences per hostname; issue a distinct service credential per backend/environment; document renewal/rotation/revocation/expiry; test the real FuelBuddy backend.
**Spec:** §5.1, §5.2. **Acceptance:** S08, A06. **Depends on:** T2.2.

### T2.4 · Centralized host/route classification
**Summary:** Implement Host-header normalization (compare against configured hostnames, ignore `X-Forwarded-Host`, fail closed on unknown hosts) and route-class/principal separation so each hostname observes the public hostname and stays on its own route class.
**Spec:** §4.1, §5.3. **Acceptance:** A17. **Depends on:** T1.1.

### T2.5 · Access JWT verification with key rotation
**Summary:** Cryptographically validate `Cf-Access-Jwt-Assertion` via Cloudflare JWKS, `kid` selection, configured issuer/audience, permitted algorithms and time claims; cache with bounded refresh shorter than the rotation overlap; refresh once on unknown `kid`; fail closed (never trust an email header or bare JWT presence).
**Spec:** §5.1. **Acceptance:** A06, A19 (JWKS clause). **Depends on:** T2.4.

### T2.6 · Principal/role mapping & route-matrix enforcement
**Summary:** Map verified principals to admin vs read-only roles and enforce the §5.3 route matrix; read credentials can never reach admin endpoints on either hostname; default-deny unclassified routes.
**Spec:** §5.1, §5.3. **Acceptance:** A06. **Depends on:** T2.5.

### T2.7 · `/internal/` isolation
**Summary:** Serve `/internal/*` only to loopback or the project-network probe source, returning 404 otherwise; block it at ingress so a misconfigured rule cannot expose it.
**Spec:** §4.1, §5.1. **Acceptance:** A16. **Depends on:** T1.7, T2.4.

### T2.8 · State-changing GET conversion + CSRF
**Summary:** Convert all GET-based research controls to read-only status or 405; require authenticated POST + same-origin CSRF protection (exact Origin validation, secure cookies) for mutations; exact consumer-origin allowlist when cross-origin reads are needed, never wildcard credentialed CORS.
**Spec:** §5.3. **Acceptance:** A07. **Depends on:** T1.1, T2.6.

### T2.9 · Capability-disabled behavior + capability-aware UI
**Summary:** When research/edit/live-refresh are disabled, return `409` with stable code `CAPABILITY_DISABLED` after authorization (never silent success or local fallback), and clearly label unavailable actions in the UI.
**Spec:** §3.1, §5.3. **Acceptance:** W04. **Depends on:** T2.6.

### T2.10 · Durable audit logging
**Summary:** Record accepted/denied admin actions (timestamp, verified principal, action, target, request/job ID, result), never JWTs/secrets/full sensitive headers; append-only and backed up; reject new admin mutations if audit persistence fails.
**Spec:** §5.3, §12. **Acceptance:** A06/A07 (supporting), S06. **Depends on:** T2.6.

### T2.11 · Bounded diagnostics path (FB-D1)
**Summary:** Emit structured, redacted diagnostics to the chosen bounded spool/collector (not Docker's retained stdout copy), with the §7.2 cap, stop-at-cap behavior and dropped-event counters; preflight fails when no bounded spool/collector is configured.
**Spec:** §12.2, §7.2. **Acceptance:** S06. **Depends on:** FB-D1, T1.8.

---

## WP3 — Immutable releases

### T3.1 · Release envelope & manifest schema
**Summary:** Define the deployment envelope (release ID, format version, producer commit, creation time, path/size/SHA-256, schema versions, compatibility range) alongside the unchanged consumer manifest, hashing the manifest from the envelope; settle FB-D2 trust model.
**Spec:** §8.1. **Acceptance:** A10. **Depends on:** FB-D2.

### T3.2 · Release validator
**Summary:** Validate archive paths, file inventory, GeoJSON schema, country codes, IDs, bounds, counts, manifest links, hashes, and fuel/charger tile+index consistency and stable-ID behavior before any activation.
**Spec:** §8.1. **Acceptance:** A10, A12. **Depends on:** T3.1.

### T3.3 · Atomic publisher (stage → rename → pointer switch)
**Summary:** Stage on the same filesystem, flush, record validation, rename into `data/releases/<id>/`, then atomically replace the relative `current` symlink under a publisher lock; interruption never serves a mixed manifest/data set; failed activation restores/keeps the prior pointer and retains evidence.
**Spec:** §8.1. **Acceptance:** A10, A18. **Depends on:** T3.2.

### T3.4 · Release-identity cache invalidation & request binding
**Summary:** Serve through immutable release-qualified URLs (or equivalent selector); resolve the active release once per request and retain it; invalidate caches by release identity so a manifest and its dependent tiles/indexes always come from one release.
**Spec:** §8.1, §9. **Acceptance:** A18. **Depends on:** T3.3.

### T3.5 · Remove rebuild-on-read in production
**Summary:** Ensure public reads never run consolidation, tile rebuilds or research; enforce through the safe-import changes and a runtime guard so missing files error rather than reconstruct.
**Spec:** §2, §8.1. **Acceptance:** A02, A10. **Depends on:** T1.9.

### T3.6 · Live overlays separation & quota state
**Summary:** Move mutable live data outside immutable releases with base-release/ID compatibility, timestamps and expiry; apply only compatible unexpired overlays; preserve price-observation precedence; persist feed quota/backoff across restarts; no overlay refresh in serving mode unless FB-D4 adds `overlay import`.
**Spec:** §8.2. **Acceptance:** A13, W03. **Depends on:** T3.3, FB-D4.

### T3.7 · Consumer schema/ID/query compatibility preservation
**Summary:** Preserve existing routes, station IDs, filters, units, price precedence, provenance, curated overrides and error semantics so authenticated consumers see identical representative data.
**Spec:** §9. **Acceptance:** A08. **Depends on:** T1.1.

---

## WP4 — Persistence & portability tools (`atlasctl`)

### T4.1 · Bundle manifest & `deployment.json`
**Summary:** Define the three export modes (application release / serving deployment / full working deployment) and the `deployment.json` record (format version, mode, revision, platform/arch, image refs+digests, data release, checksums, state format versions, importer range); always exclude secrets by default.
**Spec:** §10. **Acceptance:** A11, A12. **Depends on:** T3.1.

### T4.2 · `atlasctl` CLI skeleton
**Summary:** One versioned CLI with subcommands `init`, `preflight`, `verify`, `export`, `import`, `backup`, `restore`, `update`, `release import`, `release activate`; each requires an explicit installation target, help, nonzero exits, dry-run where relevant, redacted logs, an operation report, and zero image/data cleanup.
**Spec:** §10. **Acceptance:** A15. **Depends on:** T0.2.

### T4.3 · `atlasctl init`
**Summary:** Idempotent creation of documented directories and ownership, no recursive chmod/chown, never overwriting existing content; requires explicit authorization for the target.
**Spec:** §10, §6.2. **Acceptance:** A19. **Depends on:** T4.2.

### T4.4 · `atlasctl preflight`
**Summary:** Non-mutating checks of Docker resource labels, project identity, canonical mount paths, overlapping storage roots, prerequisites and configuration gaps; report gaps, never silently reconfigure Docker/firewall.
**Spec:** §10, §4.0. **Acceptance:** S01, S06. **Depends on:** T0.2.

### T4.5 · `atlasctl verify`
**Summary:** Verify a release/snapshot against its manifest, checksums and the recorded active release before anything is marked complete or activated.
**Spec:** §10, §11. **Acceptance:** A10, S07. **Depends on:** T3.2.

### T4.6 · `atlasctl export` (three modes)
**Summary:** Take a coherent snapshot after quiescing all mutable-state writers and recording active release/queue state; copy immutable releases outside the pause where possible; exclude secrets (separate encrypted credential package optional); emit attribution/redistribution inventory.
**Spec:** §10. **Acceptance:** A11, W05. **Depends on:** T4.1, T4.9 (quiesce logic).

### T4.7 · `atlasctl import` (registry + archive)
**Summary:** Verify checksums, size/disk requirements, formats, archive traversal/link attacks and image refs before activation; extract into a new directory; refuse to overwrite an existing installation or silently merge state; support registry-online and `docker save/load` image archives (never `docker export`/`import`).
**Spec:** §10. **Acceptance:** A12, S05. **Depends on:** T4.1, T4.12.

### T4.8 · `atlasctl release import` + `release activate`
**Summary:** `release import` writes only `data/releases/<id>/` (steps 1–3 + rename), never identity/secrets/state/`current`; identical re-import is a no-write success, a differing one is refused; `release activate` is the pointer switch under the publisher lock; trust per FB-D2.
**Spec:** §8.1, §10. **Acceptance:** A19. **Depends on:** T3.3, FB-D2.

### T4.9 · `atlasctl backup` (encrypted, snapshot-complete)
**Summary:** Nightly encrypted off-host backup of mutable state, overrides, current-release metadata and SQL state; hold the publisher lock (or refuse concurrent import/activate) from first copy to complete mark; verify archive + recorded active release + previous-state copy before marking complete; restore the recorded running set on failure; FB-D3 leave-stopped flag.
**Spec:** §11.1, §10. **Acceptance:** S07, A14. **Depends on:** T4.6, FB-D3.

### T4.10 · `atlasctl restore`
**Summary:** Target one explicit installation, accept only complete snapshots, stop only that installation's writers before replacing mutable state/release pointer, restart the recorded set after activation, leave previous state intact on pre-activation failure; FB-D3 leave-stopped flag.
**Spec:** §10, §11.3. **Acceptance:** S07, A11. **Depends on:** T4.9, FB-D3.

### T4.11 · `atlasctl update`
**Summary:** Change only an existing installation's application images: pinned refs, preflight, backup → explicit migration if needed → recreate → smoke check; dry-run names every container to be recreated; obtain explicit authorization before replacing containers; no cleanup.
**Spec:** §10, §11.4. **Acceptance:** A15. **Depends on:** T4.9.

### T4.12 · Storage admission checks
**Summary:** Before every image pull/load, release import, export, backup, restore, update or publication, estimate peak space (archive + extracted + staging + new layers + retained old + concurrent jobs), check free bytes/inodes/quota, and refuse when it cannot fit; no automatic cleanup.
**Spec:** §12.2. **Acceptance:** S05. **Depends on:** T0.5.

### T4.13 · Browser state export/import
**Summary:** Provide a UI export of format version, IndexedDB records, local edits/preferences and counts; validate import at the new HTTPS origin with conflict reporting; preserve the old origin until checked; never silently promote device-local edits to authoritative data.
**Spec:** §9, §8.3. **Acceptance:** A09. **Depends on:** T2.4.

---

## WP5 — Serving acceptance & first deployment

### T5.1 · Acceptance suite (A01–A19, S01–S08)
**Summary:** Implement and run the full acceptance matrix against the production image and a fresh VPS-like environment; Cloudflare auth tests use a real staging Tunnel, not mocks.
**Spec:** §14. **Acceptance:** all A/S criteria. **Depends on:** WP1–WP4.

### T5.2 · Performance & soak benchmark
**Summary:** Measure 10 concurrent typical requests for 15 min (no OOM, <1% server errors, p95 <1 s internal), plus cold start, large downloads, external Tunnel latency and a soak proving bounded cache growth; record dataset, query shapes, image digest, peak RSS.
**Spec:** §12. **Acceptance:** A14. **Depends on:** T5.1.

### T5.3 · First-deployment runbook execution
**Summary:** Execute §11.2 end to end: host runbook, Cloudflare Tunnel/DNS/Access, import verified package, init, preflight, start, internal readiness, Tunnel + authorized consumer calls, external IPv4/IPv6 isolation and forged-header tests, browser export/import, acceptance suite, backup/restore evidence.
**Spec:** §11.2. **Acceptance:** A05, A11. **Depends on:** WP0–WP4.

### T5.4 · Backup/restore drill (RPO/RTO)
**Summary:** Perform and time a measured restore drill to record RPO (≤24 h) and RTO (≤2 h after host + Access available), and verify checksums/auth/functional parity on the clean host.
**Spec:** §11.1. **Acceptance:** A14, A11. **Depends on:** T4.9, T4.10.

### T5.5 · Deployment manifest, SBOM & verification report
**Summary:** Produce the release verification report and deployment manifest (image/source digests, lockfile hash, base/runtime versions, architecture, image digest, SBOM, scan results, measured limits, remaining blockers).
**Spec:** §6.1, §14. **Acceptance:** A01–A03 (evidence). **Depends on:** T1.5, T5.1.

---

## WP6 — Optional online worker

### T6.1 · Durable job queue, leases & recovery
**Summary:** Durable job records (ID, type, country, validated params, principal, state, timestamps, lease, attempts, progress, output release, redacted failure) with queued/running/succeeded/failed/cancelled/interrupted states; lost leases marked interrupted; resumable-only recovery.
**Spec:** §8.4. **Acceptance:** W01, W05. **Depends on:** T1.2.

### T6.2 · Worker image (pinned, no ports, no socket)
**Summary:** Pinned Python/Node job image with required source inputs and state mounts; publishes no ports, never receives the Docker socket; stages output under `state/jobs` and reaches `releases/`/`current` only via `release import` + `release activate` under the publisher lock.
**Spec:** §3.2. **Acceptance:** A04, W01. **Depends on:** T3.3.

### T6.3 · Singleton scheduler & explicit job runner
**Summary:** Allowlisted jobs only; validated argument arrays without shell interpolation; cancellation/graceful shutdown; cross-process publisher locks; one worker owns each feed with persisted quota/backoff; no generic remote shell; no untracked subprocess after shutdown.
**Spec:** §8.4, §8.2. **Acceptance:** W01, W03. **Depends on:** T6.1.

### T6.4 · Edit/rebuild/publish transaction
**Summary:** Persist source-of-truth curated edits (principal, timestamp, reason, target ID, optimistic revision); on accept return `202` + job ID, enqueue rebuild, serialize per country, reject stale revisions with 409, use idempotency keys; edits become visible only after complete validated publication.
**Spec:** §8.3. **Acceptance:** W02. **Depends on:** T3.3, T6.3.

### T6.5 · Feed quota persistence & live refresh
**Summary:** Persist feed attempts, quota timestamps, lock/lease and retry backoff across restarts; a missing optional token disables a feed without breaking readiness.
**Spec:** §8.2. **Acceptance:** W03, A13. **Depends on:** T3.6.

### T6.6 · Capability UI (pending/success/failure)
**Summary:** Update the UI to show pending/success/failure for edits and jobs; never report a pending edit as already published.
**Spec:** §8.3, §3.1. **Acceptance:** W02, W04. **Depends on:** T2.9, T6.4.

### T6.7 · Worker acceptance (W01–W05)
**Summary:** Run worker acceptance on the selected host: restart resumability, edit revision/idempotency, quota persistence, disabled-worker read usability, full-working-export restore; base serving release stays usable without the worker.
**Spec:** §14. **Acceptance:** W01–W05. **Depends on:** T6.1–T6.6.

---

## Cross-cutting rule

Every task that touches Docker lifecycle or data obeys the deletion restriction (§1, §4.0): no automatic image pruning, data cleanup or backup expiration; any remove/replace of a named container/resource requires explicit authorization. This is enforced as a review gate on T4.2 (all CLI subcommands) and observed throughout (A15).
