# DEEPSEEK review — round 1

Reviewed `spec.md` v1.1 (local file, dated 22 October 2026) independently. The project README still says round 1 reviews v0.1, and there are no round-0 reviews or `CONSOLIDATION.md`; I used the local v1.1 as instructed. Findings are ordered by severity.

### DEEPSEEK-1 · The origin cannot see the public hostname unless the Tunnel sets it

- **Section:** §4.1 (also §5.1, §7.2, §14 A06/A07)
- **Type:** error
- **Severity:** major
- **Finding:** §4.1 requires hostname classification from "normalized, configured hostnames" and says both public hostnames may target `http://atlas-web:8088`, but it never requires the Tunnel ingress to forward the public hostname to the origin. cloudflared's `httpHostHeader` defaults to empty and the origin receives the service URL's host (`atlas-web:8088`) for both hostnames, so the application cannot distinguish the private UI from the API; the API path allowlist and the A06/A07 "read principal cannot use admin routes on either hostname" separation then rest on edge configuration alone. Proposed change: require every ingress rule to set `httpHostHeader` to its exact public hostname (or to pass one explicitly configured, edge-controlled header) and validate it against `ATLAS_UI_HOST`/`ATLAS_API_HOST` before routing; require distinct Access applications/audiences if one audience would otherwise be accepted on both hostnames; add an acceptance test that the origin itself rejects a request carrying the wrong public hostname.
- **Evidence:** Cloudflare Tunnel "Origin parameters": `httpHostHeader` default `""`, "Sets the HTTP `Host` header on requests sent to the local service" (https://developers.cloudflare.com/tunnel/reference/origin-parameters/, checked 2026-10-22); cloudflared issue #1036 is the request to forward the original Host, confirming the default does not (https://github.com/cloudflare/cloudflared/issues/1036, checked 2026-10-22). No live Tunnel was configured.
- **Confidence:** medium

### DEEPSEEK-2 · No defined tool or transport for publishing a release from the local machine

- **Section:** §1, §8.1, §8.3, §10, §15
- **Type:** gap
- **Severity:** major
- **Finding:** The default serving deployment is defined as receiving "validated releases" built on the local machine (§1), and §8.3 sends browser edits through "the local publishing workflow", but no command or package format carries a release to an existing VPS installation. §10's `atlasctl` exposes `release activate` only, and `import` "refuse[s] overwriting an existing installation by default", so the only defined path cannot add a release to a running service; §15 nevertheless requires an "atomic publisher". Proposed change: add a `release publish` (or `release import`) subcommand to §10 that accepts a checksummed release package, validates it, stages it on the release filesystem, takes a named publisher lock under `state/control/`, switches the `current` pointer and records evidence, with an acceptance test; or declare local publication out of scope and remove it from §1, §8.3 and §15.
- **Evidence:** reasoning only (cross-references within the specification).
- **Confidence:** high

### DEEPSEEK-3 · Host-wide 80/443 deny conflicts with approved sibling listeners

- **Section:** §4.4 (also §4.0, §14 S02)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.4 says "For Atlas, deny inbound application traffic on IPv4 and IPv6, including ports 80, 443, 8088 and 8099", but a host firewall rule on a shared IP cannot be scoped to Atlas. If a sibling app has an approved public listener on 443 (the shared-host premise), a literal implementation breaks it, contradicting §4.0's host-owner firewall boundary and S02's "sibling reachability unchanged". Proposed change: limit the Atlas-specific deny to ports Atlas could publish (8088 and any future metrics port); state that 80/443 inbound policy is host-owner territory derived from the host inventory and may not be denied when a sibling has an approved listener; test both the Atlas deny and sibling reachability.
- **Evidence:** reasoning only.
- **Confidence:** high

### DEEPSEEK-4 · Port 8099 is undefined

- **Section:** §4.4
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Port 8099 appears only in the firewall deny list; no service, probe or configuration in the specification uses or defines it. An implementer cannot tell whether it is a stale reference, the Python query server, a metrics port or merely a precautionary block. Proposed change: remove 8099, or define the service that would listen on it and add it to §4.2/§6.3 and the acceptance checks; if it is block-only, say so.
- **Evidence:** reasoning only (full-text check of the local spec).
- **Confidence:** high

### DEEPSEEK-5 · `logging.driver: none` contradicts stdout/stderr diagnostics

- **Section:** §12 (also §12.2, §4.2)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §12 requires "stdout/stderr structured logs", but §12.2 proposes `logging.driver: none` and, in the same sentence, sending diagnostics to a bounded collector. With the `none` driver Docker discards the container's stdout/stderr, so a collector cannot read them, and no application-level shipping path, collector destination or collector egress is specified; §4.2 inventories only JWKS and data-source egress. Proposed change: choose one model—retain stdout with a bounded `json-file`/spool configuration, or define an application-level shipper and the collector destination, credentials and egress in §4.2—and state how `cloudflared` and one-shot helper logs are bounded.
- **Evidence:** reasoning only; the specification's own §12/§12.2 text.
- **Confidence:** high

### DEEPSEEK-6 · Internal health routes are protected only by an edge rule

- **Section:** §5.1 (also §6.2, §14 A05/A06)
- **Type:** risk
- **Severity:** minor
- **Finding:** §5.1 makes internal health checks the only authentication exception and says "ingress must block those exact routes", but the application exemption is by path and has no source or network restriction. If a Tunnel ingress rule is missing or misconfigured on either hostname, `/internal/healthz` and `/internal/readyz` are reachable unauthenticated, and no acceptance criterion checks this. Proposed change: require the health endpoints to accept only loopback or a dedicated internal probe source, and require both public hostnames to return 404 for `/internal/*`; add that check to A05/A06 and the S-series ingress tests.
- **Evidence:** reasoning only.
- **Confidence:** high

### DEEPSEEK-7 · The CLI list omits the required init/ownership step

- **Section:** §10 (also §6.2, §11.2 step 3, §13 WP4)
- **Type:** gap
- **Severity:** minor
- **Finding:** §6.2 requires "one init/preflight command" and §11.2 step 3 creates state directories and permissions before preflight, but §10's `atlasctl` subcommands contain no `init`; preflight is non-mutating by §4.0's "before any mutation". The ownership/mount setup therefore has no defined interface or owner. Proposed change: add an idempotent `init` subcommand that creates the documented directories and ownership without recursive chown, requires explicit authorization, and is covered by an acceptance check; or explicitly fold initialization into preflight and change §6.2/§11.2 to match.
- **Evidence:** reasoning only.
- **Confidence:** high

**Top 3**

1. DEEPSEEK-1 — host classification cannot work at the origin unless the public hostname is forwarded.
2. DEEPSEEK-2 — the default local-to-VPS release path has no tool or transport.
3. DEEPSEEK-3 — the host-wide 80/443 deny conflicts with the shared-host premise (DEEPSEEK-5 is next in operational impact).

Result: complete
