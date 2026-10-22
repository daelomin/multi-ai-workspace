# Route & server-function inventory (T1.1)

Source inspected: `/home/remi/GIT/gas-stations-world/claude/grok_workspace` (TanStack Start + Nitro `vercel` preset). Generated 23 Oct 2026 from executable code, not from `docs/ATLAS-SPEC.md`. Discrepancies are flagged inline.

## 0. Key findings (read first)

1. **Auth model mismatch.** The app runs **self-hosted Better Auth** at `/api/auth/*`, federated through a "Grok auth broker" (`GROK_AUTH_ISSUER`). The spec (§5) mandates **Cloudflare Access JWT** at the edge + in-app principal mapping. These are different systems — the whole §5 auth layer is a migration, not a wiring tweak.
2. **Shipped default is auth-off.** `VITE_AUTH_ENABLED=false` (default) + no `DATABASE_URL` → `requireUserId()` returns the shared dev user `dev-user`. In that default serving config every mutation below is effectively **unauthenticated**.
3. **No `/internal/*` endpoints exist.** No `/internal/healthz` / `/internal/readyz` / metrics. Compose probes (spec A16) have nothing to hit yet.
4. **Rebuild-on-read is live.** Two GET routes spawn Python on a stale input (see §4) — exactly what §8.1 / T1.9 must remove.
5. **State-changing GETs exist** (see §3): `/api/night-run` GET persists the ledger file; the charger/mutation routes are the only PUT/DELETE.
6. **The night-run *orchestrator* (`pumpNightRun`) has no caller in `src/`** — the web app only *views* ledgers; the actual pump is driven elsewhere (external script/agent) or is vestigial. Record before relying on it.
7. **Multiplayer P2P is dead code** — `multiplayer/p2p.ts` implements a WebRTC mesh that fetches `/api/rtc`, but no `signaling.server.ts` exists, no route registers `/api/rtc`, and `P2PRoom` has no caller. Either drop it or wire it; it must not ship half-implemented.
8. **Client edits are duplicated across three stores** — station edits/tombstones live in IndexedDB `fuel-atlas` and are mirrored into localStorage `fuel-atlas-meta-v2`; crowd contributions live in IndexedDB `fuel-atlas-crowd`. The §9 browser export must capture all three (and their `deletedIds`), or user edits are lost on origin migration.

---

## 1. Route table

### 1.1 API routes (`src/routes/api/*.ts`)

| Method | Path | Handler (file) | Auth today | Side effects |
|---|---|---|---|---|
| GET | `/api/countries/{iso2}/stations` | `handleStationsRequest` (subdivisions.server) | none | read |
| GET | `/api/countries/{iso2}/chargers` | `handleChargersRequest` (chargers.server) | none | **spawns Python rebuild if stale**; starts live scheduler; reads live overlay |
| PUT | `/api/countries/{iso2}/chargers/{id}` | `saveChargerEdit` (chargers.server) | **none** | writes `REFERENCE_EV/overrides/XX.json` + `dist/chargers/XX.geojson` |
| DELETE | `/api/countries/{iso2}/chargers/{id}` | `deleteCharger` (chargers.server) | **none** | writes overrides + built file |
| GET | `/api/countries/{iso2}/geojson` | `agentGeojsonResponse` (research-job.server) | none | **spawns Python consolidate if stale** |
| GET | `/api/countries/{iso2}/feeds` | `countryFeedStatus` (night-api-run.server) | none | read |
| GET | `/api/countries/{iso2}/places` | `handlePlacesRequest` (places.server) | none | read |
| GET | `/api/countries/{iso2}/subdivisions` | `handleSubdivisionsRequest` (subdivisions.server) | none | read |
| GET | `/api/catchment` | `handleCatchmentRequest` (catchment.server) | none | read |
| GET | `/api/admin/published-counts` | `publishedCountAdminPayload` | **none** | read |
| POST | `/api/admin/published-counts` | `importPublishedCsv` | **none** | writes published-count store (FS) |
| GET | `/api/i18n` | `bundle` (i18n/service) | none | read |
| GET | `/api/i18n/{locale}?speak=` | `bundle` / `speak` | none | read (TTS, no write) |
| GET | `/api/map-boundaries` | `mapBoundariesResponse` | none | read |
| GET | `/api/night-api-run` | `loadNightApiLedger` | none | read |
| GET | `/api/night-run` | `loadNightLedger` + `refreshNightLedger` | **none** | **writes ledger file** (state-changing GET) |

### 1.2 Auth surface (Better Auth, self-hosted)

| Method | Path | Notes |
|---|---|---|
| GET/POST | `/api/auth/*` | sign-in/sign-out/session, OAuth authorize + callback, bearer, cookie. Wired via `better-auth/tanstack-start` + `src/lib/auth/server.ts`. |

### 1.3 Middleware / PWA routes (`server/middleware/grok-pwa.ts`, Nitro `serverDir:"./server"`)

| Method | Path | Notes |
|---|---|---|
| GET | `/__grok/manifest.webmanifest`, `/__grok/manifest.json` | dynamic PWA manifest |
| GET | `?install=1` on any document path | Home Screen install tutorial |
| GET | all HTML documents | stream-inject PWA + OG head tags |

### 1.4 Dev-only (Vite `apply:"serve"`)

| Method | Path | Notes |
|---|---|---|
| GET | `/auth/popup` | OAuth popup completion (preview only) |
| GET | `/__app-env` | `appEnvPlugin`, dev only |

### 1.5 Page routes (SSR)

| Path | File | Loader |
|---|---|---|
| `/` | `index.tsx` | — |
| `/country/$iso2` | `country.$iso2.tsx` | `getCountry(params.iso2)` (read) |
| `/night-run` | `night-run.tsx` | — (polls `GET /api/night-run`) |
| `/night-api-run` | `night-api-run.tsx` | — (polls `GET /api/night-api-run`) |
| `/admin/published-counts` | `admin.published-counts.tsx` | — |

---

## 2. Server functions (`createServerFn`, POST transport)

| Export | File | Method | Effect |
|---|---|---|---|
| `runResearchStep` | fuel/actions.ts | POST | spawns Overpass/OpenData/Nominatim/brand locators (network + research) |
| `listReferenceExtracts` | fuel/actions.ts | POST | reads REFERENCE catalog |
| `importReferenceCountry` | fuel/actions.ts | POST | reads REFERENCE extracts |
| `dispatchResearchJob` | fuel/actions.ts | POST | **spawns research follower subprocess + starts systemd tracker units** |
| `pollResearchJob` | fuel/actions.ts | POST | reads job state |
| `listResearchJobs` | fuel/actions.ts | POST | lists jobs |
| `fetchForecourtHighways` | fuel/actions.ts | POST | fetches highways near points (network) |
| `getConnectorReadiness` | app-data/readiness.ts | POST | reads connector-token readiness |
| `importPublishedCsv` | (via POST /api/admin/published-counts) | POST | writes published-count store |

Note: `getConnectorReadiness` and the `app-data/client.server.ts` `callTool`/connector bridge are the **Grok app-builder "connector"** surface (a local multi-agent/tool bridge), not part of the Fuel Atlas data API. They must be inventoried separately and gated by §5.3 "unknown routes → deny".

---

## 3. State-changing GETs (to convert per §5.3)

| Path | GET side effect | Target treatment |
|---|---|---|
| `/api/night-run` | `refreshNightLedger` → `saveNightLedger` writes `night-run.json` | read-only status, or 405 (mutations move to authenticated POST) |
| `/api/countries/{iso2}/chargers` | triggers Python rebuild + starts scheduler (lazy work) | keep GET read-only; remove rebuild-on-read (T1.9) |
| `/api/countries/{iso2}/geojson` | triggers Python consolidate | keep GET read-only; remove rebuild-on-read (T1.9) |

---

## 4. Subprocess spawn map

| Trigger | Spawn | In serving mode? |
|---|---|---|
| `consolidated.server.ts` `rebuildConsolidated` (via GET geojson) | `python3 consolidate.py --countries XX --no-tiles --out dist/` | yes (rebuild-on-read) — must be removed |
| `chargers.server.ts` `rebuildChargers` (via GET chargers) | `python3 consolidate_chargers.py …` | yes (rebuild-on-read) — must be removed |
| `live.server.ts` `runLiveJob` (scheduler / charger GET) | `python3 eipa_live.py --out dist/` | yes — move to worker (T3.6) |
| `research-job.server.ts` `ensureTrackerUnits` | `systemctl --user start terrascope-tracker.service jarvis-tracker.service` | yes (Jarvis/systemd) — must be disabled |
| `research-job.server.ts` `spawnFollower` | `node scripts/research-job.mjs` (detached) | yes — worker only |
| `research-job.server.ts` `publishJobToTracker` | `node scripts/research-track.mjs --publish XX` (sync) | yes — Jarvis tracker |

---

## 5. Filesystem read/write map

| Path (env override) | Access | Notes |
|---|---|---|
| `dist/` (`FUEL_ATLAS_DIST`) | R/W | `countries/XX.geojson`, `chargers/XX.geojson`, `live/PL.json`. Writes on rebuild + charger edit. |
| `REFERENCE/` (`FUEL_REFERENCE_DIR`) | R | fuel station inputs |
| `REFERENCE_EV/` (`FUEL_EV_REFERENCE_DIR`) | R/W | charger inputs + `overrides/XX.json` (edit target) |
| `fuel_station_agent/` (`FUEL_AGENT_DIR`) | R + spawn cwd | `consolidate.py`, `eipa_live.py`, `data/XX/` |
| `research-jobs/` (workspace) | R/W | job JSON + logs |
| workspace root | R/W | `night-run.json`, `night-api-run.json`, `.lock` files |
| `.jarvis/tracker/memory/` | R | Jarvis tracker graphs |

Desktop/home assumption: `consolidated.server.ts`/`chargers.server.ts` fall back to paths **relative to the repo** (`../fuel_station_agent`, `../REFERENCE_EV`, `REPO_ROOT/dist`) when env vars are unset — no hardcoded `/home/remi`, but the fallbacks assume a source checkout. §7.2 requires explicit paths, no checkout.

---

## 6. Environment variable map

| Var | Kind | Use |
|---|---|---|
| `FUEL_ATLAS_DIST`, `FUEL_AGENT_DIR`, `FUEL_REFERENCE_DIR`, `FUEL_EV_REFERENCE_DIR`, `FUEL_PYTHON`, `FUEL_ATLAS_ROOT` | runtime config | data/agent paths, Python binary |
| `DATABASE_URL` | secret | Postgres/Neon connection (auth) |
| `VITE_AUTH_ENABLED` | build-time public | auth on/off switch |
| `BETTER_AUTH_URL`, `BETTER_AUTH_SECRET`, `GROK_AUTH_ISSUER`, `GROK_AUTH_CLIENT_ID`, `GROK_AUTH_CLIENT_SECRET`, `GROK_PROJECT_ID` | secret / config | Better Auth + broker federation |
| `EIPA_TOKEN` | secret | Poland live feed |
| `OVERPASS_MIRROR_INDEX`, `FUEL_FORCE_ALL_SECTIONS`, `HOME` | config | research spawn env |

---

## 7. Client storage map

### 7.1 IndexedDB

| DB (version) | Store(s) | Contents | User edits? |
|---|---|---|---|
| `fuel-atlas` (v2) | `countries`, `summaries` | persisted country data: stations, report, `deletedIds` (tombstones), research-imported stations | **yes** — authoritative |
| `fuel-atlas-crowd` (v1) | `profile`, `reports` | crowd profile + field reports/validation | **yes** — crowd contributions |

### 7.2 localStorage

| Key | Contents |
|---|---|
| `fuel-atlas-meta-v2` (Zustand `persist`) | country status summaries + `deletedStationIds` (mirrors IDB tombstones) |
| `fuel-atlas.map-basemap` | map basemap preference |

### 7.3 sessionStorage

| Key | Contents |
|---|---|
| `grok-auth.bearer-token` | preview iframe bearer token (partitioned-cookie workaround, preview only) |

Migration note (§9): `deletedStationIds` is stored in **both** `fuel-atlas` (IDB) and `fuel-atlas-meta-v2` (localStorage). The browser export must capture both; IDB is authoritative for station data, localStorage holds the quick-hydrate summaries.

---

## 8. Scheduled work

| Timer | Location | Notes |
|---|---|---|
| hourly live overlay refresh (poll 5 min, refresh 1 h) | `live.server.ts` (server) | moves to worker (T3.6) |
| Better Auth session refresh/expiry | `auth/client.ts` (client) | standard auth |
| WebRTC ping + poll | `multiplayer/p2p.ts` (client) | **dead code (no caller)** |
| job/ledger polling | `country.$iso2.tsx`, `night-run.tsx`, `night-api-run.tsx`, `research-job.ts` | UI polling |
| night-run pump (`pumpNightRun` / `pumpNightApiRun`) | `night-run.server.ts` / `night-api-run.server.ts` | **no caller in `src/`** — external/vestigial |

---

## 9. Grok "connector" tool bridge (`app-data/`)

Not part of the Fuel Atlas data API — it is the Grok app-builder preview's local tool-calling bridge:

- `callTool()` (`app-data/client.server.ts`) proxies tool calls to the Grok connectors gate (`connectors.grok.me` / `connectors.app-builder-testing.com`), resolved only when the request host is `*.grok.me`/`*.app-builder-testing.com` or `GROK_CONNECTORS_URL` is set.
- `getConnectorAccessToken` / `isConnectorTokenReady` / `getConnectorReadiness` / `useRefetchWhenConnectorReady` manage the connector token lifecycle.
- Predicate `isWorkspacePreview()` = `!GROK_PROJECT_ID`.

On a standalone VPS this bridge is **inactive** (no Grok host, `GROK_PROJECT_ID` unset). Per §5.3 "unknown/control routes → deny", it must be explicitly gated or removed so no future request can reach it — it is a **control path**, not a data read.

---

## 10. Multiplayer P2P (dead code)

`src/lib/multiplayer/p2p.ts` implements a full-mesh WebRTC room signaling over `/api/rtc`, but no `signaling.server.ts` exists and no route registers `/api/rtc`. `P2PRoom` has no caller anywhere in `src/`. Verdict: **vestigial client code with an unimplemented server half** — drop it or wire it deliberately; it must not ship as a half-working network surface.

---

## 11. Completeness notes (first-pass open items resolved)

- Read handlers confirmed pure: `subdivisions.server.ts`, `catchment.server.ts`, `places.server.ts`, `map-boundaries.server.ts`, `reference.server.ts` have no `spawn`/`fetch` (file reads only).
- Client storage, scheduled work, connector bridge and the `/api/rtc` multiplayer gap are now enumerated.

T1.1 is now complete for the serving-relevant surface. Still unverified (separate investigation, not blocking M0): the exact `docs/ATLAS-SPEC.md` route contract vs this code (diff not yet done), and the Android/Capacitor build (`android/`, `build:android`) which is out of scope for the VPS serving target.
