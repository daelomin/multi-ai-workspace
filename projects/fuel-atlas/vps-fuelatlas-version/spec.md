# Fuel Atlas — portable Docker deployment specification

Version 1.2 · 22 October 2026 · Status: implementation specification; no deployment performed
author: CHATGPT - Astra medium

### Revision history

Version 1.2 consolidates round-1 review (`reviews/round-1/CONSOLIDATION.md`). It corrects the release mount so the `current` pointer is visible, adds `atlasctl release import` and `atlasctl init`, defines request-to-release binding, restores services after failed or interrupted backups, makes restore stop the target installation's writers, replaces the host-wide 80/443 deny with an Atlas-scoped isolation rule, fixes the Host-header and `/internal` ingress rules, adds JWKS key-rotation handling and resolves the `logging.driver: none` contradiction. No new implementation or deployment evidence is claimed.

Version 1.1 incorporates Astra’s conceptual review for multiple independent Docker applications on the same VPS. It supersedes v1.0 for implementation. The original source inspection and dataset measurements are unchanged; this revision adds requirements rather than claiming new implementation or deployment evidence.

The principal changes are explicit installation identity, per-application named Tunnels, host-wide capacity planning, scoped deployment operations, consistent snapshots, and tests against a running neighboring application. Full worker operation remains a later milestone.

## 1. Status and decisions

The implementation SHALL package Fuel Atlas as a production Node application, published datasets and explicit persistent state, orchestrated by Docker Compose. The package SHALL run on an ordinary Linux KVM/full VM without Vercel, a local development checkout, desktop services or provider-specific storage.

**Cloudflare Tunnel is the only application ingress.** No app, API, database, metrics or worker port may be published on the host. No direct origin DNS record or alternative public listener is permitted. A tunnel hostname can still be publicly reachable: Tunnel provides connectivity, while Access and application authorization determine who may use it.

The default VPS deployment serves the website and existing read API. Large research/import runs remain on the local machine initially and publish validated releases to the VPS. An optional worker deployment supports online research, editing and live-feed refresh with explicit resource limits. Worker mode is a defined follow-on milestone, not a dependency of the first serving deployment.

MUST/SHALL identify acceptance requirements. SHOULD identifies a preferred implementation with a documented reason required for deviations. Proposed environment variables and tools in this document are new contracts unless marked existing.

### Binding decisions

- Ubuntu 24.04, Linux x86-64, Docker Engine and Compose v2 form the initial supported target. Debian 12 support is verified separately. ARM64 is optional until native dependencies and all images pass equivalent checks.
- Run a standalone Nitro Node server; do not use Vite dev or preview as the production service.
- Use one explicit Compose project, named Cloudflare Tunnel, connector, private network and storage root per application/environment. Several such projects SHALL coexist on the VPS.
- Deploy one web replica and one publisher at a time initially. Horizontal scaling requires a separate design for shared state and coordination.
- Keep application images, published data, mutable state and credentials separate.
- Keep existing station IDs, schemas, filtering semantics, price precedence, provenance and curated overrides.
- Use Cloudflare Access for private human administration and approved machine clients. All consumer traffic also uses Tunnel.
- Default-deny unclassified routes and capabilities. Existing unauthenticated mutation endpoints must never become accessible as a side effect of migration.
- Preserve the user's deletion rule: no automatic image cleanup, pruning, data removal or backup expiration. Any deletion requires an explicit instruction naming the items. Export, import and update tools must not contain destructive cleanup steps.

## 2. Current implementation and migration constraints

Source project: `/home/remi/GIT/gas-stations-world`.

| Area | Observed implementation | Required change |
|---|---|---|
| Web app | `claude/grok_workspace`: React, TanStack Start, Vite, Nitro; Node 22+ in README | Produce and test a standalone Node image |
| Production target | `vite.config.ts` explicitly selects Nitro `vercel` | Add a portable Node build target while preserving middleware registration |
| Build side effects | `npm run build` also runs `db:migrate`; a configured database can be changed during a build | Separate compilation from deployment migrations; build without runtime secrets |
| Published data | Repository `dist/`: country and charger GeoJSON, versioned tiles, manifest, live overlays | Make published releases immutable and independently portable |
| Existing path overrides | `FUEL_ATLAS_DIST`, `FUEL_AGENT_DIR`, `FUEL_REFERENCE_DIR`, `FUEL_EV_REFERENCE_DIR`, `FUEL_PYTHON`, `FUEL_ATLAS_ROOT` | Centralize validation; add explicit state/job paths; remove desktop path assumptions |
| Reads and rebuilds | `consolidated.server.ts` can spawn Python when inputs change | Disable all on-read rebuilds in production; publish out of band |
| Research | `research-job.server.ts` launches scripts and starts Jarvis/systemd user services | Serving mode must import safely without them; worker mode uses an explicit job runner |
| Live feeds | `live.server.ts` can spawn `eipa_live.py`; Vite starts its scheduler in development | Move refresh ownership to a worker; persist quota state across restarts |
| Browser storage | IndexedDB and localStorage contain client state and edits | Provide export/import before changing browser origin |
| Mutation exposure | Contract records charger PUT/DELETE without authentication and admin controls on GET as well as POST | Authenticate and authorize all control paths; prohibit state-changing GET |
| Database scaffold | `db.ts` supports PostgreSQL or an in-memory PGLite fallback | Inventory actual usage; no silent ephemeral database for persistent production state |

Measured on 22 October 2026: published `dist/` approximately 674 MB; `REFERENCE` 131 MB; `REFERENCE_EV` 275 MB. Raw US and China PBF files total roughly 13.75 GB. These are snapshot measurements, not future storage guarantees or RAM estimates.

The README includes historical scaffolding notes. Implementers must treat executable code and `docs/ATLAS-SPEC.md` as the basis for a route/dependency inventory, and record discrepancies before changing behavior. This specification does not assume that every route or client state location has already been enumerated.

## 3. Scope and deployment modes

### 3.1 Serving mode — first release

Required services: `atlas-web` and `cloudflared`. Administrative release verification, backup and import tools run as explicit one-shot processes. The web application mounts datasets read-only and has a narrow writable state directory.

Includes the existing map UI, fuel and charger read endpoints, applicable secondary layers, manifests/tiles, translations, live overlay reading, private administration, release management and diagnostics. Research execution, charger editing and scheduled fetches are disabled unless their corresponding worker capability is enabled.

The UI must clearly label unavailable research/edit actions. Disabled mutations return `409` with stable code `CAPABILITY_DISABLED` after authorization; they never silently succeed or fall back to local workstation commands. Existing consumers must remain usable without a worker.

### 3.2 Worker mode — optional second release

Adds `atlas-worker`, a pinned Python/Node job image with required source inputs and state mounts. It executes validated jobs, creates new dataset releases, applies durable curated edits and refreshes enabled live feeds. It publishes no ports and never receives the Docker socket.

Default concurrency is one import/research job. A worker resource limit protects web service memory. Full-country or global import sizing must be benchmarked before enabling it on a small VPS. Jarvis integration may remain available for local development, but is not required for the portable runner.

### 3.3 Non-goals

No Kubernetes, cluster orchestration, mandatory managed database, full OSM planet import on a 4 GB server, new fuel/charger data model, public admin UI, or unrelated monitoring stack. This is packaging and operational portability, not an algorithm rewrite.

## 4. Architecture and ingress

```text
Human administrator                         Approved backend consumer
  | Cloudflare Access login                   | machine authentication
  +-----------------------+--------------------+
                          | HTTPS
                Cloudflare edge + Access
                          |
                 outbound-established Tunnel
                          |
                   cloudflared container
                          | private Docker network, HTTP
                  atlas-web:8088
                    |             |
             releases (RO)    app state / audit (RW)
                    ^
           validated release publisher
                    ^
         local build/import or optional worker
```

There is no Internet-to-VPS app connection. HTTP is acceptable only between containers on the same host's private bridge; any cross-host origin link requires authenticated TLS. Browser-to-Cloudflare and Tunnel transport remain encrypted. Cloudflare terminates public TLS and is part of the trust boundary.

### 4.0 Shared-host ownership and installation identity

The VPS is shared infrastructure. Its owner controls Docker Engine, daemon configuration, host/provider firewalls, host storage allocations, SSH, monitoring and backup scheduling. An application deployment controls only its own project resources and its own Cloudflare resources. Atlas tools SHALL inspect prerequisites and report gaps; they SHALL NOT silently install/reconfigure Docker, restart the daemon, change host firewalls or modify another application.

Every installation SHALL have an immutable `ATLAS_INSTALLATION_ID`, explicit `COMPOSE_PROJECT_NAME` and canonical absolute `ATLAS_INSTALL_ROOT`. Store these in a host-specific installation file outside portable application defaults. Example project names are `fuel-atlas-prod` and `fuel-atlas-staging`; deployment must validate uniqueness rather than assume these names are free. Every CLI operation passes the project name, Compose file, project directory and configuration file explicitly. Do not rely on the current directory or Compose's basename-derived identity.

Networks and volumes are project-scoped. Do not specify global `container_name` values or unscoped resource names. Bind mounts must resolve beneath the installation root except explicitly declared read-only inputs and backup destinations. No app can mount another application's directory, the Docker socket or host root. Preflight checks Docker resource labels, existing project identity, canonical mount paths and overlapping storage roots before any mutation.

A new import creates a new installation identity unless the operator explicitly selects an existing installation for an update/restore. Portable exports record source identity for provenance, but SHALL NOT activate that identity blindly on the destination. A deliberate replacement preserves identity only after ownership and collision checks. Refuse ambiguous targets.

App operations may start/stop or recreate only their own services. No daemon restart, host-wide Compose action, global container stop or orphan cleanup is permitted. Even within an app, tools SHALL honor the user's deletion restriction; if a Docker operation would remove or replace a container/resource, identify the exact items and obtain explicit authorization before that destructive step. Image archives and previous data releases remain available.

### 4.1 Hostnames and routing

Use owner-supplied hostnames such as `atlas.<domain>` for the private UI and `atlas-api.<domain>` for approved read clients. Both resolve to the named Tunnel, never to the VPS IP. The API hostname routes only an explicitly reviewed allowlist of read paths/methods. Other routes return 404/405 before handler execution.

Host classification must use the normalized `Host` header delivered to `atlas-web`, compared with the configured hostnames. Ignore `X-Forwarded-Host` and any client-supplied forwarded-host header for classification. Unknown hosts fail closed. Both hostnames may target `http://atlas-web:8088`; application middleware enforces route and principal separation.

The origin must receive the public hostname. For each public hostname, either show with the pinned connector version that the original `Host` is preserved, or set that ingress rule's `httpHostHeader` to exactly that hostname (never one shared value for both). Record the observed behavior in the deployment report. The edge also uses distinct Access applications/audiences, so hostname separation does not rest on the Host header alone.

Each public hostname's ingress forwards application routes and SHALL NOT forward `/internal/` to `atlas-web`; both hostnames return 404 for `/internal/*`. Compose probes call `/internal/healthz` and `/internal/readyz` over the project network.

No quick/temporary Tunnel in production. Use a remotely managed named Tunnel dedicated to this application and environment. Never share its token with a different application’s connector: connectors using the same Tunnel are replicas, not independent routes. All replicas of one Tunnel would need equivalent reachability and compatible state; cross-host replicas are outside the initial scope. Maintain a non-secret configuration inventory covering tunnel ID/name, published hostname/service mappings, Access application IDs/audiences, policies and DNS records. The Tunnel token alone does not reproduce Cloudflare-side configuration.

### 4.2 Compose network requirements

- No `ports:` mappings in any production service, including localhost mappings.
- No `network_mode: host`, privileged mode or Docker socket mount.
- `atlas-web` and `cloudflared` share a project-specific bridge, not unrelated application networks.
- `cloudflared` needs outbound connectivity. Do not put it exclusively on an `internal: true` network that blocks its egress.
- Web requires outbound access for Access JWKS and explicitly inventoried external service reads, including any diagnostics collector destination (§12.2); workers require approved data-source connectivity. These are connectivity requirements, not a claim that a standard Docker bridge enforces destination allowlists. If restricted egress is required, the host runbook SHALL specify and test its firewall/proxy mechanism, DNS behavior and update procedure.
- App listens on `0.0.0.0:8088` inside its container. This is not a published host listener.
- Tunnel credentials are mounted only into `cloudflared`, with read access verified for its actual runtime UID.
- Connector health/metrics endpoints remain internal.

### 4.3 Optional shared connector — deferred alternative

The first deployment uses a dedicated named Tunnel and connector per app. A shared connector may be considered only as a separately managed infrastructure project. It would join one distinct ingress network per app, use unique origin aliases, and have no access to database/backend networks. Its credentials, routes and lifecycle belong to the host operator. Individual app installers may not stop it or modify unrelated routes. Migration then requires per-hostname route cutover rather than stopping the shared connector. Document the resulting shared failure and credential boundary before adopting it.

Different isolated applications may use the same internal port, including 8088. Introduced databases SHALL use a separate backend network reachable only by their own app/worker, not by the connector.

### 4.4 VPS firewall and remote administration

The host runbook SHALL inventory existing services before changing firewall rules, preserve required neighboring-service connectivity, and test those services afterward. Atlas publishes no host ports. For Atlas, deny inbound traffic on IPv4 and IPv6 to Atlas container addresses and to any host port that would publish Atlas, including 8088. Port 8099 is the optional Python query server from `docs/ATLAS-SPEC.md` (`127.0.0.1`, local validation only); it is not a production published service. Do not install host-wide denies for ports 80/443 merely because Atlas uses Tunnel: record the owner of each existing public listener and keep every owner-approved neighboring listener (including TCP 80/443) reachable. After any firewall change, repeat A05 against Atlas and each neighbor's own reachability check. Docker published ports bypass ufw/firewalld and `DOCKER-USER` sees post-DNAT addresses, so a host-wide destination-port rule is not the Atlas control; any extra Docker filtering belongs in the host runbook and is tested there. Restrict SSH to an owner-approved administrative source or established private management network. Keep provider console recovery available before tightening SSH. Public SSH is not part of the application architecture.

Permit outbound DNS, HTTPS and Tunnel transport. Cloudflare currently requires outbound TCP/UDP 7844 for HTTP/2/QUIC; verify current destination requirements when deploying [R1]. Host and provider firewall rules must allow established return traffic. Docker's packet handling means a host firewall alone is not proof of isolation: independently test the public IP and inspect Compose port mappings.

## 5. Authentication and authorization

### 5.1 Default policy

- Private UI: Cloudflare Access, explicit administrator identity allowlist.
- Consumer hostname: Access service authentication for approved backends, plus verified read-only principal mapping in the application.
- No anonymous API bypass in the first release.
- A browser/mobile app must not embed an Access service token. FuelBuddy's backend holds any machine secret and calls the tunneled API. A later direct mobile API requires short-lived per-user authorization and a separately reviewed edge policy.

Validate `Cf-Access-Jwt-Assertion` cryptographically using Cloudflare's JWKS, configured issuer, correct hostname-specific audience, permitted algorithms and time claims. Load the key set from the team's `/cdn-cgi/access/certs` endpoint and select the key by the JWT `kid`; do not pin a single `public_cert`. Cloudflare rotates signing keys about every six weeks and keeps the previous key valid for seven days, so cache with a bounded refresh interval shorter than that overlap and refresh once immediately when a `kid` is missing from the cache. Fail closed when a token cannot be verified, including when that refresh fails. Never trust an email header or mere presence of a JWT. Machine service identities need a verified claim mapping and a read-only role, not an assumption that they have human email claims. Test actual Cloudflare-issued tokens [R2].

If interactive and service policies require separate Access applications, use distinct audiences. Read credentials must not authorize admin endpoints through either hostname. Internal health checks are the only narrowly defined authentication exception; ingress must block those exact routes, and the application SHALL also serve `/internal/*` only to loopback or the project-network probe source, returning 404 otherwise, so a misconfigured ingress rule does not expose them.

### 5.2 Machine consumer lifecycle

Configure the consumer Access application with an explicit Service Auth policy. Issue a distinct service credential for every backend and environment; record owner, purpose, expiry and permitted application audience. Credentials remain server-side file secrets. The consumer sends the required Access service headers on every request, uses bounded timeouts, and never forwards secrets to another host after a redirect. Treat Access login redirects, HTML errors, 401/403 and invalid JSON as authentication failures rather than data responses. Do not retry them indefinitely.

Document credential renewal, overlap during rotation, revocation and expiry alerts. Test the actual FuelBuddy backend through the configured Tunnel. Account-wide Access settings and identity providers are shared dependencies: inventory them without changing them implicitly. Dataset-source terms must also permit intended downstream API consumption, not only exporting backup archives.

### 5.3 Route matrix

| Route class | Allowed principal | Serving mode | Worker mode |
|---|---|---|---|
| UI, static app assets, private diagnostics | authenticated administrator | available | available |
| Existing reviewed data GET/HEAD routes | administrator or approved read client | available | available |
| Research/night jobs, data publishing, job cancellation | administrator | disabled or explicit release-import tool | validated admin operation |
| Charger PUT/DELETE and other data mutations | administrator | capability disabled | durable edit job |
| Health/readiness/metrics | internal probe only | internal | internal |
| Unknown/control/server-function routes | none until classified | denied | denied |

Enumerate TanStack server functions, framework transport routes, SSR loaders and direct HTTP endpoints, not only `/api/*`. Apply checks before any filesystem write, subprocess spawn, external fetch with credentials or state disclosure. Treat GET-based research controls as migration defects: old GET actions become read-only status or 405; authenticated POST plus CSRF protection initiates work.

Use same-origin CSRF protection for browser mutations, exact Origin validation and secure cookie settings where cookies exist. CORS is not authorization. Allow only configured consumer origins when cross-origin browser reads are required; no wildcard credentialed CORS. Return JSON 401/403 for app-level API authorization failures. Cloudflare's edge may reject unauthenticated requests separately; machine clients must handle non-JSON edge responses.

Audit accepted and denied administrative actions with timestamp, verified principal, action, target, request/job ID and result. Never record JWTs, service-token values or complete sensitive headers.

## 6. Production build and containers

### 6.1 Build contract

Add `build:portable` and `start:portable`, leaving existing development workflows intact. Select the installed Nitro version's supported standalone Node preset and verify its actual output. Current Nitro documentation describes `node` and `.output/server/index.mjs`; the repository pins a beta, so do not assume an older `node-server` name or output layout works without validation [R3]. Preserve `serverDir: './server'` and required middleware/PWA hooks.

Use a multi-stage Dockerfile with a pinned supported Node release satisfying the app's requirements, lockfile-based `npm ci`, and separately pinned base image digest. Compilation must not contact or migrate a production database. Exclude `.env*` except example templates, credentials, browser profiles, local data, raw PBFs, caches, logs, `.git`, `node_modules` and unrelated repository files through `.dockerignore`.

Runtime image includes the compiled server, static assets, any runtime-required scripts/catalogs and attribution. Production web startup must not require the source checkout, npm installation, Vite, Python, Jarvis, systemd or desktop environment variables. Any required boundary/place/catalog assets must be explicitly inventoried and packaged or mounted; they must not be fetched implicitly as a substitute for missing release data.

Images carry OCI source/revision/version labels. Record application source commit, lockfile hash, base/runtime versions, target architecture and image digest in the deployment manifest. Use fixed references; no `latest` in release configuration. Scan images and generate an SBOM as release evidence.

### 6.2 Runtime behavior

Run as a fixed non-root UID/GID with read-only root filesystem, bounded tmpfs, dropped capabilities, `no-new-privileges`, explicit resource limits, graceful SIGTERM and Compose restart policy. Host initialization creates mounts with correct ownership; do not recursively chmod/chown arbitrary supplied directories.

Startup validates configuration, active release and required persistent mounts, then becomes ready. It must not modify published data or create a transient fallback database. Separate liveness (`/internal/healthz`) from readiness (`/internal/readyz`). Readiness requires a verified usable release, not availability of every external feed or country. Missing countries are supported data gaps.

Provide an idempotent `atlasctl init` (creates the documented directories and ownership, §10) and a non-mutating `atlasctl preflight`. If actual production features require SQL state, use explicit durable storage or an optional PostgreSQL service with a persistent volume and backup procedure. Do not replace the current unused scaffold with a mandatory database without evidence. PGLite in memory is prohibited for persistent state. Migrations run as an explicit, serialized deployment step after backup, never in image build or concurrently across services.

### 6.3 Required Compose shape

The final `compose.yaml` includes pinned `atlas-web` and `cloudflared` references, named private network, read-only release mount, narrow state mount, internal app healthcheck, resource/log limits and a file-backed tunnel secret. A profile adds the worker. Any helper image used for verification must also be pinned and included in offline exports.

Run the connector using its pinned version's supported token-file option rather than embedding a token in YAML or command arguments. Verify `--token-file`/`TUNNEL_TOKEN_FILE` support against that version [R4]. Local Compose file secrets are host files mounted into containers; they are not an encrypted secret vault [R5].

## 7. Filesystem and configuration contracts

### 7.1 Host bundle layout

```text
fuel-atlas/
  compose.yaml
  .env.example
  installation.example.env # actual host identity configured separately
  deployment.json
  SHA256SUMS
  docs/INSTALL.md
  docs/OPERATIONS.md
  scripts/                 # preflight, verify, export, import, backup, restore
  images/                  # optional Docker save archives
  data/
    releases/<release-id>/ # published data and release manifest
    current                # atomic relative symlink to active release
  state/
    control/               # audit, capabilities and administrative state
    jobs/                  # durable queue/status/leases when worker enabled
    live/                  # mutable expiring overlays and refresh quota state
    overrides/             # durable hand-curated edits, worker mode
  worker-inputs/           # optional raw/reference/agent inputs
  secrets/                 # supplied separately; never in ordinary export
```

Inside containers, use stable paths under `/opt/fuel-atlas` for code and `/srv/fuel-atlas` for data/state. Mount `data/` into the web container read-only. It contains both `releases/` and `current`, and `current` is a relative symlink to a target inside the same mount, so atomic pointer switches are visible. Do not mount only `releases/<release-id>` or only `releases/`. The one-shot publisher mounts the same `data/` directory writable and is the only writer of `releases/` and `current`. Resolve the active release once per request and retain that version throughout the request. Never follow symlinks outside the validated root.

### 7.2 Configuration

| Setting | Requirement |
|---|---|
| `ATLAS_INSTALLATION_ID`, `COMPOSE_PROJECT_NAME`, `ATLAS_INSTALL_ROOT` | unique host installation identity, explicit project and canonical root |
| `ATLAS_IMAGE`, `CLOUDFLARED_IMAGE` | pinned release references; non-secret Compose substitution |
| `ATLAS_UI_HOST`, `ATLAS_API_HOST` | exact configured hostnames |
| `ATLAS_MODE=serve` | default; `worker` capabilities explicitly configured |
| `FUEL_ATLAS_DIST` | existing setting; points to validated current release |
| `ATLAS_STATE_DIR`, `ATLAS_LIVE_DIR`, `ATLAS_JOBS_DIR` | proposed explicit persistent paths |
| `ATLAS_ACCESS_ISSUER` | expected Cloudflare team issuer |
| `ATLAS_UI_ACCESS_AUD`, `ATLAS_API_ACCESS_AUD` | required, hostname-specific audiences |
| `ATLAS_ADMIN_IDENTITIES`, `ATLAS_READ_IDENTITIES` | explicit principal mapping; no open defaults |
| `ATLAS_ALLOWED_ORIGINS` | exact browser origin allowlist when needed |
| `ATLAS_RESEARCH_ENABLED`, `ATLAS_EDITS_ENABLED`, `ATLAS_LIVE_REFRESH_ENABLED` | false by default; require working worker capability |
| `FUEL_AGENT_DIR`, `FUEL_REFERENCE_DIR`, `FUEL_EV_REFERENCE_DIR`, `FUEL_PYTHON` | existing settings; only required for appropriate worker jobs |
| `DATABASE_URL_FILE` | optional new file-secret reader, only if SQL is actually used |
| Tunnel and source API tokens | file-backed secrets, mounted only into the service that needs them |

Provide a documented translation layer for existing environment names. No `/home/remi`, desktop service name, home-directory discovery or developer-specific executable in a portable production path. Validate configuration at startup and report missing setting names without printing their contents. `VITE_*` values are public build-time data and must never hold secrets. Hostnames and authorization config must be runtime configurable without rebuilding the image.

## 8. Dataset releases, edits and jobs

### 8.1 Publication transaction

A release contains the existing consumer manifest plus a separate deployment envelope. Preserve the existing manifest schema. Add envelope fields for unique release ID, format version, producer commit, creation time, paths/sizes/SHA-256 hashes, schema versions and compatibility range. Hash the manifest itself from the envelope to avoid circular checksums.

1. Stage into a new uniquely named directory on the same filesystem as the release store.
2. Validate archive paths, file inventory, GeoJSON schema, country codes, IDs, bounds, counts, manifest links and hashes. Verify fuel and charger tile/index consistency and stable-ID behavior.
3. Complete atomic writes, flush necessary files, and record validation results before activation.
4. Rename the complete staging directory into the release store, then atomically replace the relative `current` symlink under a publisher lock.
5. Invalidate web caches by release identity. In-flight readers retain their original release; new readers use the new one.
6. Check representative API/UI queries. If validation or activation checks fail, keep or restore the prior pointer and retain evidence. Do not remove either release.

No partial publication and no manifest/data mixture. Test the rename/pointer behavior under interruption. Public reads never run consolidation, rebuild tiles or wait for research. Missing release files cause explicit errors and readiness failure rather than silent reconstruction.

A manifest and its dependent tiles/indexes SHALL identify a single release through immutable release-qualified URLs or an equivalent explicit release selector. Requests carrying that identity resolve the retained release rather than the current pointer, and cache keys include it. Test a promotion between a manifest fetch and its dependent requests and verify that all returned files belong to the selected release. State separately that independent live API requests may observe a newer release.

A new release reaches an existing installation through `atlasctl release import` (§10), which writes only `data/releases/<release-id>/`; `release activate` is the following pointer switch under the publisher lock.

Import accepts only a trusted release source. Checksums detect corruption, not malicious substitution: release authenticity comes from authenticated transport and a verified producer, or signed release manifests with an explicitly configured trust key.

### 8.2 Live overlays

Move mutable live data outside immutable releases. Overlay metadata includes base release or ID-compatibility information, timestamps and expiry. Apply only compatible, unexpired overlays; expired or incompatible data is ignored and freshness reported. Preserve price-observation precedence and never invent zero prices for missing data.

One worker owns each feed, with persisted attempts, quota timestamps, lock/lease and retry backoff across restarts. A missing optional token disables that feed without making the read API unready. Default serving mode consumes exported overlays until expiry; ongoing live refresh requires the worker or a trusted external publisher.

### 8.3 Curated edits

Worker mode stores source-of-truth edits separately from published data, with principal, timestamp, reason, target ID and optimistic revision. Keep the semantics of existing fuel overrides and `REFERENCE_EV/overrides/XX.json`; implement an explicit adapter if their storage path changes.

An accepted mutation persists a durable edit and enqueues a rebuild. Return `202` with job ID and pending status until the validated release is active. Update the UI to show pending/success/failure; never report a pending edit as already published. Serialize changes per country and reject stale revisions with 409. Retries use idempotency keys. A failed rebuild retains the edit for diagnosis and retry.

For serving-only deployment, export browser edits and apply them through the local publishing workflow. Do not claim that published GeoJSON alone backs up hand-curated source overrides.

### 8.4 Research job contract

Durable records include ID, type, country, validated parameters, requesting principal, state, creation/start/finish time, lease, attempt count, progress, output release and redacted failure. States are queued/running/succeeded/failed/cancelled/interrupted. PIDs are process-local diagnostics, never durable identity after migration.

Allowlisted jobs only; pass validated argument arrays without shell interpolation. No generic remote shell endpoint. Use cancellation/graceful shutdown and cross-process publisher locks. Recovery marks lost leases interrupted and resumes only explicitly resumable work. Export pauses scheduling and waits for a safe checkpoint or records interrupted jobs. No subprocess continues untracked after shutdown.

## 9. API and browser compatibility

Preserve the existing routes documented in `docs/ATLAS-SPEC.md`: station subdivision/circle queries; charger filters; GeoJSON; applicable places/feeds/catchment/boundaries; translations; IDs, units and observation precedence. The Python query server is not an additional exposed service. If deployed for internal validation it remains un-published and does not become a second source of truth.

Add internal health endpoints to the Node application; existing Python `/health` is not proof the Node container is healthy. Health output is minimal and credential-free.

Cache policy:

- Mutable manifest pointers, auth/session endpoints, admin state and live charger responses: no-store or explicit safe revalidation; preserve existing charger no-store behavior.
- Immutable versioned assets/tiles: cacheable only under an intentionally authorized data policy. Default private data is not stored in a shared edge cache.
- API responses include release identity; use ETag where safe. Avoid user-dependent responses in shared caches.
- PWA/service worker must not cache admin tokens, mutation responses or private API data under an anonymous cache key. Clear incompatible cached versions and test logout/offline behavior.

Bound query radius, result size, request body and execution time. Stream or bound large downloads. Use viewport/tiles for maps where applicable rather than loading every country into RAM per request. No data parsing task may trigger a simultaneous uncontrolled memory spike across requests.

Before origin migration, provide a browser export with format version, relevant IndexedDB records, local edits/preferences and counts. Validate import at the new HTTPS origin; present conflicts and verify representative IDs. Preserve the old origin until checked. Host backups cannot capture arbitrary clients' browser storage. Device-local contributions remain device-local unless explicitly imported; do not silently turn them into globally authoritative data.

## 10. Export and import package

“Exportable” means a tested package can recreate the application on a clean compatible VPS. A container image alone is insufficient. Provide three export modes:

| Mode | Includes | Purpose |
|---|---|---|
| Application release | images or registry references, Compose, checksums, docs, examples, compatibility manifest | reproducible software deployment |
| Serving deployment | application release + active published release, live overlays, control state and current pointer metadata | move/restore read service |
| Full working deployment | serving deployment + overrides, jobs/checkpoints, references, agent state and required worker inputs | preserve editing/research continuity |

All modes exclude secrets by default. A separate explicitly requested encrypted credential package may be produced with a recipient key; never plaintext credentials in the normal archive. Browser data requires its separate export. Include attribution/source-license inventory and flag data whose redistribution is restricted; permission to run a private service is not automatically permission to redistribute every source dataset.

`deployment.json` records export format version, export mode, creation time, application revision, platform/architecture, image references and digests, data release, file checksums, persistent-state format versions and supported importer range. Include non-secret Cloudflare resource identifiers/configuration separately. Do not include Access service secrets or tunnel token.

Support registry-online import and image-archive import using Docker save/load. Do not use `docker export`/`docker import` as the application backup mechanism: these do not capture the required mounted data and image deployment metadata. Bundled image archives must match the destination architecture. Offline image loading does not mean offline operation: Cloudflare Tunnel and live sources still need connectivity.

Exporter takes a coherent snapshot after quiescing all mutable-state writers and recording active release/queue state. Pausing the publisher alone is insufficient: web audit/control state, worker jobs, overlays and databases can still change. The initial supported backup method stops this installation's connector and web/worker writers during the mutable snapshot, after draining requests/jobs; other installations keep running. Copy immutable releases outside this pause where possible. Before quiescing, durably record which of this installation's services were running and the operation phase. Record backup start/end, active release, state schema and snapshot completion, then restart only the paused services. On failure or interruption, attempt to restore only the recorded running set (writers and web first, verifying readiness before reconnecting ingress), unless the operator passed an explicit leave-stopped flag; never start services that were previously stopped. If readiness cannot be restored, leave ingress stopped and emit an actionable alert. Provide an idempotent recovery command for abrupt process or host interruption, and test copy failure and interruption after services stop. Database state uses its supported consistent backup or a stopped-volume copy. Online filesystem/database snapshots are an optional later method and must prove cross-component consistency. Any failed snapshot remains marked incomplete and cannot be restored as a valid backup. Importer verifies checksums, size/disk requirements, supported formats, archive traversal/link attacks and image references before activation. Extract into a new directory, refuse overwriting an existing installation by default, and never merge silently with existing state. Checksum failure leaves the running installation untouched.

`atlasctl restore` targets one explicit installation and accepts only a snapshot marked complete. It stops that installation's connector and web/worker writers before replacing mutable state or the release pointer, never writes into a running writer and never stops another installation. If restore fails before activation, it leaves the previous state in place and restarts the stopped services; after successful activation it starts them.

`atlasctl release import` targets one explicit existing installation. It accepts a checksummed release package from an authenticated transport or a signed archive checked with the configured trust key, applies the §8.1 validation and the §12.2 storage admission, and writes only `data/releases/<release-id>/`. It leaves installation identity, secrets, mutable state and `current` unchanged. Installation `import` still refuses an existing installation.

`atlasctl init` is idempotent and requires explicit authorization for the installation target. It creates the documented directories and ownership without recursive chmod/chown and never overwrites existing content.

Implement one versioned `atlasctl` CLI with subcommands `init`, `preflight`, `verify`, `export`, `import`, `backup`, `restore`, `release import` and `release activate`. These are one operational interface, not separate products. Each command requires an explicit installation target. Each offers help, meaningful nonzero exits, dry-run where relevant, redacted logs and an operation report. They must not prune Docker images or delete staging/old releases automatically.

## 11. Backup, recovery and migration

### 11.1 Backup policy

Nightly encrypted off-host backup of mutable state, curated overrides, current release metadata and any SQL state. Back up each new published release before or immediately after promotion. Keep immutable application release artifacts available by digest or image archive. Provider snapshots supplement these exports.

Initial objectives: mutable-state RPO at most 24 hours; published data recoverable to the latest backed-up release; serving RTO at most two hours after a replacement host and Cloudflare access are available. These are targets requiring a measured restore drill, not an uptime promise.

Persist a last-success backup timestamp and report failures. Retention is append-only until the owner explicitly authorizes removal of named backup items. Warn on low storage; do not apply an expiration/prune policy automatically. Secret recovery material is encrypted separately and tested without logging it.

### 11.2 First deployment

1. Complete the separate host runbook: inventory neighboring apps, capacity and ingress; establish/retest SSH and recovery access; install Docker/Compose only if needed. Assign the installation identity, storage allocation and resource budgets.
2. Create Cloudflare named Tunnel, DNS and Access applications/policies. Define exact admin/read identities.
3. Import a verified serving package into a new directory; run `atlasctl init` to create state directories/permissions and supply file secrets.
4. Run preflight, verify route policy and inspect the rendered Compose configuration for published ports and secret leakage.
5. Start containers and verify readiness through an internal probe. Test the Tunnel and authorized consumer calls.
6. Check public IPv4 and IPv6 directly from outside: app/API ports must be unreachable. Test forged headers and disallowed methods/paths.
7. Export/import browser state, configure consumers' `FUEL_ATLAS_URL` and machine authentication, then run the acceptance suite.
8. Record backup/restore evidence and deployment report before normal use.

### 11.3 Host migration

Quiesce publishers and edit jobs; create and verify a coherent export. Restore into a new host, load the exact images, supply secrets separately and test internally. For staging, use a separate Tunnel/hostname or keep the new connector offline until cutover.

Do not connect old and new hosts as active replicas of the same Tunnel while they serve divergent state: Cloudflare may send requests to either. Stop only the old Atlas-dedicated connector or otherwise remove that connector from routing before enabling its replacement for normal traffic. Confirm its installation labels and Tunnel ID first; never stop another app’s connector or a shared infrastructure connector. With a stable named Tunnel and hostname, migration normally changes the active connector rather than DNS.

Verify API parity, release checksums, Access authorization, stale-overlay behavior and direct-IP isolation. Keep the old host/data intact for rollback. Never run two independent writers on copied state.

### 11.4 Update and rollback

Back up mutable state, verify new image digests and compatibility, perform explicit migrations when required, update images and run smoke checks. An application-only rollback reselects a previous image; a data rollback switches the release pointer. If state schema changed incompatibly, restore a compatible coherent state snapshot with the old image; do not assume image rollback reverses migrations. Preserve all versions until explicit removal authorization.

## 12. Operations and resource budgets

The earlier 2 vCPU, 4 GB RAM, 40 GB disk estimate is a provisional single-Atlas serving baseline, not a capacity recommendation for the combined VPS. Select the host only after inventorying all intended applications and measuring or conservatively estimating their concurrent peaks. Build on the development/CI machine and transfer images; don't assume compiling and importing fit alongside production on this VM.

Starting limits to tune through measurement: web 2 GB RAM/1.5 CPU, connector 256 MB/0.25 CPU, bounded 128 MB web tmpfs, bounded request concurrency and bounded logging without automatic deletion of stored log files. Leave headroom for the host, Docker and filesystem caching. A worker deployment needs a separately measured budget, typically a larger host; don't enable it merely because Compose starts successfully.

Benchmark representative small/large countries and charger queries. Initial acceptance target after warmup: 10 concurrent typical requests for 15 minutes, no OOM or incorrect responses, under 1% server errors and p95 under 1 second internally for bounded read queries. Report cold start, large downloads and external Tunnel latency separately. Record dataset, query shapes, image digest and peak RSS; revise the VM estimate if this target fails. A soak test must show bounded cache growth.

Emit structured, redacted diagnostics with request/job/release IDs through the bounded spool or collector defined in §12.2 (not through Docker's retained stdout copy). Do not enable automatic rotation that deletes stored log files without explicit owner authorization naming the affected files. Set a disk budget, alert before reaching it, and define a bounded remote log sink or a stop-spooling behavior when the budget is exhausted; record any dropped diagnostic-event counts. Keep administrative audit records durable, append-only and backed up. If audit persistence fails, reject new administrative mutations rather than losing their audit trail. Durable audit retention follows the explicit owner deletion rule.

Expose internal-only metrics or status for readiness, active release, uptime, errors, queue depth, last feed attempt/success, expired overlays, last backup and free disk. Prometheus/Grafana are optional profiles, not base requirements. Stopping Tunnel fails closed; there is no direct-IP fallback.

### 12.1 Aggregate capacity and effective limits

Maintain a host inventory listing each project, service count, memory limit/observed peak, CPU limit/observed load, PID limit, storage allocation, growth estimate, backup schedule and maintenance owner. Include databases, monitoring, all Tunnel connectors and one-shot helpers.

For initial admission, the sum of concurrently runnable container/helper memory limits plus reserved OS/Docker headroom SHALL fit physical RAM. Start with a host reserve of at least 1 GiB or 20% of RAM, whichever is greater, and tune upward from measurement. This is an engineering starting policy, not a guarantee. Swap is not usable application capacity: explicitly choose its size and per-container allowance, and avoid relying on swapping for normal operation. Tmpfs memory is included in its container budget. Record units consistently.

Per-container ceilings do not reserve CPU or memory and do not enforce a project-wide aggregate. Account for every service separately, use `mem_limit`, `cpus`, `pids_limit` and supported swap controls, and verify effective settings with Docker inspection after startup. Limit Node heap below the container ceiling with room for buffers/native allocations, then measure actual RSS. Where limits vary across Compose/Engine versions, fail preflight rather than silently omitting them.

Throttle backup/compression/hash/import jobs with explicit CPU, memory and I/O policies supported on the actual host. Serialize heavy maintenance jobs across apps with a host-owned scheduler or lock; a shared scheduler may invoke scoped app commands but may not receive unrestricted app secrets. If hard disk I/O controls are unavailable, schedule maintenance and run contention tests rather than claim isolation.

Acceptance includes Atlas load while neighboring workloads and a backup run. Check their latency/error budgets too. Increase host capacity or reduce workload when the combined budget fails; do not recommend a fixed larger VM without that inventory.

### 12.2 Storage admission and bounded logging

Before an image pull/load, release import, export, backup or publication, estimate peak additional space: compressed archive + extracted files + staging + new image layers + old retained release/image + concurrent jobs. Check filesystem free bytes, free inodes and each app's allocation. Shared image layers may reduce actual consumption but cannot be assumed for admission. Require configurable reserve headroom and refuse the operation when it cannot fit; no automatic cleanup.

Use per-app filesystem quotas or dedicated storage allocations where available. Bind-directory organization alone is not a disk quota. Docker's shared image/log store also needs host monitoring and admission control. A source archive's size is not a bound on extracted size; importer enforces declared and measured extraction limits.

The release must choose and test an actual logging configuration. For the initial no-automatic-deletion policy, set `logging.driver: none` for every Atlas service (including `cloudflared` and one-shot helpers) so Docker keeps no second copy. The application and helpers SHALL write redacted diagnostics directly to a host-approved bounded collector or an explicitly bounded file spool that stops accepting diagnostics at its cap without deleting stored records; the collector destination and its egress are listed in §4.2. `docker logs` is empty under this driver and is not the diagnostic path. `cloudflared` output that cannot reach the spool is covered by its metrics and exit status, and this limit is documented. Verify the collector's retention policy follows owner authorization. Do not claim that application spool limits bound Docker's separate default logs. Preserve counters for dropped diagnostics and separate durable audit records. If no bounded collector/spool is configured, preflight fails rather than allowing unlimited log growth.

At a soft threshold, alert and suspend new storage-heavy jobs. At the hard allocation threshold, reject new imports/publication/mutations, preserve existing reads where safe, and report the affected installation. Restoring capacity requires added storage or explicit item-specific removal authorization. Backup completeness must never be inferred from an out-of-space partial archive.

## 13. Implementation work packages

### WP0 — shared-host contract

Inventory all intended co-resident stacks and record host/app ownership, explicit installation identity, per-app Tunnel/network/storage boundaries, effective service/helper resource limits, storage admission checks and the host maintenance runbook. Implement collision checks and prepare a running sibling test application. This is a prerequisite to shared-host deployment, not a new orchestration platform.

### WP1 — inventory and portable runtime

Inventory routes, server functions, runtime filesystem reads/writes, environment values, actual DB usage, scheduled work and subprocesses. Add production build/start scripts and Node preset, remove database migration from portable image build, package required assets and make serving imports safe without the worker checkout. Add internal health/readiness.

### WP2 — Tunnel and authorization

Create Compose/network/secret configuration. Implement centralized host/route/principal checks, Access JWT verification and role separation. Convert state-changing GET endpoints; protect framework server functions; add CSRF and clear capability-disabled behavior. Deliver reproducible Cloudflare resource setup instructions and configuration inventory.

### WP3 — immutable releases

Implement release validation/envelope, stable path configuration, current-pointer activation and cache invalidation. Remove rebuild-on-read in production. Separate expiring overlays. Retain consumer schema/ID/query compatibility.

### WP4 — persistence and portability tools

Implement bundle manifests, export/import, encrypted backups, restore/preflight and architecture checks. Inventory/preserve browser data through explicit UI export/import. Document ownership, secrets and nondestructive rollback.

### WP5 — serving acceptance and first deployment

Run tests against the actual production image and a fresh VPS-like environment. Prove Tunnel-only access, identity separation, data parity and clean-host restore. Measure resources. Serving release is complete only when its acceptance evidence is recorded.

### WP6 — optional online worker

Implement durable queue/leases, explicit Python worker image, singleton scheduler, edit/rebuild/publish transactions, feed quota persistence and capability UI. Preserve algorithm behavior and source attribution. Enable features only after worker acceptance tests on the selected host; base serving release remains usable without it.

Do not bundle application deployment or Cloudflare policy changes into merely writing this specification. Implementation should follow applicable project instructions and keep existing local data/workflows intact.

## 14. Acceptance criteria

| ID | Required evidence |
|---|---|
| A01 | `npm ci`, typecheck, relevant existing fuel tests and portable build pass; pre-existing unrelated failures are documented rather than suppressed |
| A02 | Production container starts with no source checkout, Vite, Python, Jarvis or systemd available in serving mode |
| A03 | Image build receives no production secrets and performs no DB migration; image/export secret scan finds no credential material |
| A04 | Rendered production Compose has zero published ports and no host networking, privileged mode or Docker socket |
| A05 | External IPv4/IPv6 probes cannot reach origin app/API/metrics (approved neighboring listeners remain reachable and are not a failure); correct hostname works only through Tunnel; disabling Tunnel removes app access |
| A06 | Invalid/missing/expired/wrong-issuer/wrong-audience JWTs and forged identity headers fail; a read principal cannot use admin routes on either hostname |
| A07 | No state change via GET, alternate host, SSR/server-function transport or unclassified route; CSRF attempt fails |
| A08 | Authenticated existing fuel/charger queries preserve representative IDs, filters, units, counts and error semantics; consumer backend works with machine auth |
| A09 | Restart/recreate retains release/state; serving read filesystem is read-only; browser origin import preserves exported records/counts |
| A10 | Bad/truncated/tampered release fails verification; interrupted promotion never serves mixed manifest/data; rollback restores the old release |
| A11 | Clean-host restore from a serving export passes checksums, auth and functional tests; no dependency on `/home/remi` or original host storage |
| A12 | Image archives load and start on supported architecture; wrong architecture/format and unsafe archives fail before activation |
| A13 | Expired live overlay is ignored; absent optional feed token does not break readiness; private/admin data is not shared-cache served |
| A14 | Load/soak benchmark records memory and latency against §12, and backup restore drill records measured RPO/RTO |
| A15 | All export/import/update/backup scripts contain no image-prune/data-cleanup or automatic backup-expiration action |
| A16 | From outside, both public hostnames return a non-success response for `/internal/healthz`, `/internal/readyz` and the metrics path and the handler does not run; `/internal/*` from a non-probe source on the project network is refused |
| A17 | The application observes the public hostname on each Tunnel hostname; an API-hostname request sending `X-Forwarded-Host` set to the UI hostname stays on the API route class |
| A18 | A promotion between a manifest fetch and its dependent tile/index requests never returns files from two releases |
| A19 | `release import` adds a release to a running installation without changing identity, secrets, state or `current`; `init` is idempotent; JWKS key rotation (unknown `kid`) is accepted after one refresh |
| S01 | Two installations with identical directory basenames get distinct explicit project IDs; project/network/volume/mount collisions fail before mutation |
| S02 | Deploy/update/stop/restore Atlas while a sibling app runs; sibling container IDs, health, network, data hashes and reachability remain unchanged |
| S03 | Each app/environment has its own named Tunnel/token; stopping Atlas ingress leaves the sibling hostname working |
| S04 | Inspect effective memory/CPU/PID/swap controls for all services/helpers; combined load plus backup stays within host budget and sibling service targets |
| S05 | Insufficient bytes/inodes/quota and excessive extraction size reject operations without affecting active releases or deleting data |
| S06 | Logging saturation stops spooling/drops diagnostics as documented, preserves audit behavior, and creates no unlimited Docker stdout copy |
| S07 | Snapshot while audit/control writers are active proves quiescing or a consistent snapshot; restore verifies all mutable state, not just published files; a failed or interrupted backup restores the previously running service set, and restore stops only the target installation's writers |
| S08 | Real FuelBuddy service authentication works; expired credentials, redirects and rotation are handled safely; read credentials cannot mutate |
| W01 | Worker jobs survive restart as resumable/interrupted state without duplicate execution or subprocess orphaning |
| W02 | Simultaneous edits honor revisions/idempotency and persist overrides; accepted edit becomes visible only after complete validated publication |
| W03 | Worker scheduler respects persisted feed quota/backoff across restart and multiple attempted workers |
| W04 | Worker disabled: web remains fully usable for reads, attempts to mutate report explicit disabled status, and no hidden Python/Jarvis execution occurs |
| W05 | Full working export restores overrides, input inventory and queue state; stale PIDs/leases do not mark old processes running |

Evidence belongs in a release verification report: commands, image/source digests, environment, test results, measured limits and any remaining blocker. Cloudflare authentication tests require an actual configured staging Tunnel; local mocks alone are insufficient.

## 15. Deliverables and deployment inputs

### Deliverables

- Multi-stage web Dockerfile, `.dockerignore`, optional worker Dockerfile and pinned production Compose.
- Portable build/start entrypoints, health/readiness and validated runtime path/config module.
- Centralized Access JWT/role/route checks and API consumer integration guidance.
- Release envelope/schema, validator, atomic publisher and compatibility tests.
- Portable deployment tools and formats defined in §10, plus encrypted backup/restore workflow.
- Browser state export/import and capability-aware UI.
- Separate host-administration and app-installation runbooks; Cloudflare setup, operations, migration, rollback and credential-rotation documentation.
- Per-installation configuration template, host capacity inventory, scoped lifecycle checks and sibling-app acceptance report.
- Versioned application image(s), optional offline image archives, SBOM, checksums and verification report.
- Worker queue/scheduler/edit features and full-working-export support when the worker milestone is implemented.

### Inputs required for deployment, not for writing the implementation

Inventory of the other Docker applications and their expected workloads/storage needs; actual VPS hostname/IP and SSH access; domain and selected UI/API hostnames; Cloudflare account/zone, named Tunnel and Access configuration; authorized administrator identities and backend consumer identities; chosen initial dataset release; backup destination/encryption recipient; optional source API tokens; decision to enable online workers and the measured host capacity.

No credential should be pasted into this specification. Supply secrets through the chosen secure file/credential workflow. The default architecture is decided; these values parameterize it.

## 16. References

### Local implementation evidence

- [Fuel Atlas web README](/home/remi/GIT/gas-stations-world/claude/grok_workspace/README.md)
- [Build configuration](/home/remi/GIT/gas-stations-world/claude/grok_workspace/vite.config.ts)
- [Package scripts and dependencies](/home/remi/GIT/gas-stations-world/claude/grok_workspace/package.json)
- [Canonical data/API contract](/home/remi/GIT/gas-stations-world/docs/ATLAS-SPEC.md)
- [Consolidated read/rebuild behavior](/home/remi/GIT/gas-stations-world/claude/grok_workspace/src/lib/fuel/consolidated.server.ts)
- [Research launcher](/home/remi/GIT/gas-stations-world/claude/grok_workspace/src/lib/fuel/research-job.server.ts)
- [Live overlay scheduler](/home/remi/GIT/gas-stations-world/claude/grok_workspace/src/lib/fuel/live.server.ts)
- [Database scaffold](/home/remi/GIT/gas-stations-world/claude/grok_workspace/src/lib/db.ts)
- [Build-time migrator](/home/remi/GIT/gas-stations-world/claude/grok_workspace/scripts/migrate.mjs)
- [Python publication pipeline](/home/remi/GIT/gas-stations-world/claude/fuel_station_agent/README.md)

### Official platform references

- R1: [Cloudflare Tunnel firewall requirements](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-with-firewall/).
- R2: [Cloudflare Access JWT validation](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).
- R3: [Nitro Node runtime](https://nitro.build/deploy/runtimes/node) and [deployment presets](https://nitro.build/deploy).
- R4: [Cloudflare Tunnel configuration](https://developers.cloudflare.com/tunnel/configuration/), [token management](https://developers.cloudflare.com/tunnel/reference/tunnel-tokens/) and [run parameters](https://developers.cloudflare.com/tunnel/advanced/run-parameters/). Validate options against the pinned connector version during implementation.
- R5: [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) and [single-server production deployment](https://docs.docker.com/compose/how-tos/production/).

Additional references from the shared-VPS review:

- [Compose project identity](https://docs.docker.com/compose/how-tos/project-name/).
- [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).
- [Compose networking](https://docs.docker.com/compose/how-tos/networking/).
- [Cloudflare Tunnel replicas](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/tunnel-availability/deploy-replicas/).
- [Cloudflare Access service tokens](https://developers.cloudflare.com/cloudflare-one/access-controls/service-credentials/service-tokens/).
