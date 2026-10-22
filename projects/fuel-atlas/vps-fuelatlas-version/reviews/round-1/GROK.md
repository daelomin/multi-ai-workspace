# GROK review — round 1

Reviewed local `spec.md` version 1.1 (22 October 2026). This project has no round-0 reviews and no `CONSOLIDATION.md`, so nothing already accepted is re-opened and there is no open HUMAN decision list to carry.

### GROK-1 · Host-wide deny of 80 and 443 fights the shared VPS

- **Section:** §4.4
- **Type:** inconsistency
- **Severity:** major
- **Finding:** §4.4 tells the host runbook to preserve neighboring services, then says to deny inbound IPv4 and IPv6 application traffic including ports 80, 443, 8088 and 8099. On this spec’s shared Docker host, 80 and 443 are exactly the ports an approved sibling may publish. A literal deny removes that neighbor. The same sentence is also a poor description of Atlas isolation: Atlas already publishes no ports, and Docker’s firewall path is not a general host INPUT rule. Port 8099 is not defined anywhere in this spec; in the local Atlas contract it is the Python query server on `127.0.0.1`.
- **Proposed change:** Replace the deny sentence in §4.4 with: “Atlas publishes no host ports. Deny inbound traffic to Atlas container addresses and to host ports that would publish Atlas, including 8088. Port 8099 is the optional Python query server from `docs/ATLAS-SPEC.md`, which listens on `127.0.0.1` for local validation and is not a production published service. Keep every inventoried neighbor listener that the host owner has approved, including TCP 80 and 443 when that neighbor publishes them. After any firewall change, repeat A05 against Atlas and repeat each neighbor’s own reachability check. Extra Docker filtering belongs in the host runbook and is tested there: published ports are open to the outside by default, ufw and firewalld can be bypassed by Docker port publishing, and `DOCKER-USER` matches post-DNAT container addresses, so a host-wide dport rule is not the Atlas control.”
- **Evidence:** Docker Engine install notes, “Firewall limitations” (published ports bypass ufw/firewalld), checked 2026-10-22: https://docs.docker.com/engine/install/ubuntu/ . Docker iptables (`DOCKER-USER` is pre-Docker FORWARD; packets there are already DNATed), checked 2026-10-22: https://docs.docker.com/engine/network/firewall-iptables/ . Port publishing, checked 2026-10-22: https://docs.docker.com/engine/network/port-publishing/ . Local `docs/ATLAS-SPEC.md` (gas-stations-world), read 2026-10-22: Python query server `127.0.0.1:8099`.
- **Confidence:** high

### GROK-2 · Serving mode has no way to add a release to a live installation

- **Section:** §8.1, §10
- **Type:** gap
- **Severity:** major
- **Finding:** The first release keeps research on the local machine and publishes validated releases to the VPS. §8.1 then says to stage a new directory into an existing release store and flip `current`. The only CLI is `preflight`, `verify`, `export`, `import`, `backup`, `restore` and `release activate`. `import` extracts into a new directory and refuses an existing installation, so it cannot be the recurring publish path. `release activate` only switches the pointer. Following the command list leaves a running serving installation with no specified operation that admits the next dataset.
- **Proposed change:** Add `atlasctl release import` to the §10 command list and to §8.1. It targets one explicit existing installation, writes only `data/releases/<release-id>/` from an authenticated transport or a signed archive checked with the configured trust key, verifies the envelope hashes, and leaves installation identity, secrets, mutable state and `current` unchanged. `release activate` is the following pointer switch under the publisher lock. Installation `import` still refuses an existing installation.
- **Evidence:** reasoning only, from §3.1, §8.1 and the §10 command list and import rule.
- **Confidence:** high

### GROK-3 · The read-only release mount does not contain `current`

- **Section:** §7.1
- **Type:** error
- **Severity:** major
- **Finding:** The bundle puts `current` beside `releases/`, under `data/`. §7.1 tells the web container to mount “the release parent, not only the current symlink target” so a pointer switch is visible. The parent of `data/releases/<release-id>` is `data/releases`, which does not contain `data/current`. A container that follows that wording never sees the symlink §8.1 flips, so activation is invisible until the mount or the process path is recreated. The web mount is read-only; the spec also never gives the one-shot publisher a writable mount of that same directory.
- **Proposed change:** Replace the mount sentence in §7.1 with: “Mount `data/` into the web container read-only. That directory contains both `releases/` and `current`. `current` is a relative symlink to a target inside the same mount. The one-shot publisher mounts the same `data/` directory writable and is the only writer of `releases/` and `current`. Do not mount only `releases/<release-id>` or only `releases/`.”
- **Evidence:** reasoning only, from the §7.1 tree and the mount sentence, read with §6.3 and §8.1 step 4.
- **Confidence:** high

### GROK-4 · `logging.driver: none` drops the stdout logs §12 requires

- **Section:** §12, §12.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §12 requires structured stdout/stderr logs. §12.2 then sets `logging.driver: none` and sends diagnostics to a collector. Docker’s `none` driver stores nothing and `docker logs` returns no output, so a collector that reads the Docker log API sees an empty stream. The no-automatic-deletion goal is real; the two sections name different pipes for the same records.
- **Proposed change:** In §12 and §12.2, require the application to write redacted diagnostics to a bounded spool or directly attached collector that stops accepting new diagnostic records at its cap and does not delete stored records. Set the Atlas services’ logging driver to `none` so Docker keeps no second copy. Preflight fails when that spool or collector is absent. Keep durable audit records on their own append-only store. State that `docker logs` is empty under this driver and is not the diagnostic path.
- **Evidence:** Docker “Configure logging drivers”, driver table: `none` means no logs are available and `docker logs` returns no output. Checked 2026-10-22: https://docs.docker.com/engine/logging/configure/
- **Confidence:** high

### GROK-5 · Hostname separation depends on the Host cloudflared actually sends

- **Section:** §4.1, §14 A06
- **Type:** gap
- **Severity:** minor
- **Finding:** UI and API separation uses the Host the application sees. Cloudflare’s origin-parameter page defines `httpHostHeader` as empty by default and does not say what Host the origin then receives. Current cloudflared source rewrites `Host` only when `httpHostHeader` is non-empty, and then copies the original to `X-Forwarded-Host`. One shared `httpHostHeader` would make both public names look alike. Trusting a client-supplied `X-Forwarded-Host` would let an API-hostname request present the UI name.
- **Proposed change:** Add to §4.1: “Classify the request by the `Host` header delivered to `atlas-web`. Leave `httpHostHeader` empty unless the pinned connector is shown not to preserve the public Host; a configured value is per public hostname and equal to that hostname. Ignore `X-Forwarded-Host` and any client forwarded-host header for classification.” Extend A06: one request to each public hostname records that the application observed that hostname, and an API-hostname request that also sends `X-Forwarded-Host` set to the UI hostname stays on the API route class.
- **Evidence:** Cloudflare origin parameters, `httpHostHeader` default `""`, “Sets the HTTP Host header on requests sent to the local service”, page last updated 17 April 2026, checked 2026-10-22: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/origin-parameters/ . cloudflared `ingress/origin_proxy.go` `httpService.RoundTrip` on `master`, fetched 2026-10-22: `req.URL.Host` is set to the origin; `req.Host` is replaced and `X-Forwarded-Host` is set only when `o.hostHeader != ""`. https://github.com/cloudflare/cloudflared/blob/master/ingress/origin_proxy.go
- **Confidence:** high

### GROK-6 · Unauthenticated `/internal` routes have no acceptance check

- **Section:** §4.1, §5.1, §5.3, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** §5.1 makes internal health the only authentication exception and tells ingress to block those routes. §5.3 puts health, readiness and metrics on “internal probe only”. §4.1 also allows both public hostnames to target `http://atlas-web:8088` with no path exception. A hostname-wide tunnel route therefore reaches handlers that skip JWT checks. A05 probes the raw VPS address, so a tunnel path to `/internal/healthz`, `/internal/readyz` or metrics can still pass the table.
- **Proposed change:** Add to §4.1: “Each public hostname’s ingress forwards the application routes and does not forward `/internal/` to `atlas-web`. Compose probes call `/internal/healthz` on the project network.” Add acceptance A16: from outside, both public hostnames receive a non-success response for `/internal/healthz`, `/internal/readyz` and the metrics path, and the application handler does not run.
- **Evidence:** reasoning only, from §4.1, §5.1, §5.3, §9 and A05.
- **Confidence:** high

### GROK-7 · A failed backup has no restart step

- **Section:** §10
- **Type:** gap
- **Severity:** minor
- **Finding:** The supported backup stops this installation’s connector and web/worker writers. The restart sentence comes after recording snapshot completion. The failure sentence marks the snapshot incomplete and says nothing about the stopped services. An operator who follows the steps in order can leave this installation’s only ingress stopped after a failed copy.
- **Proposed change:** Add to the §10 backup paragraph: “If services were stopped and the snapshot fails or the operation is interrupted, restart those same services before returning, unless the operator passed an explicit leave-stopped flag. Mark the snapshot incomplete either way. A failed backup does not restore itself over the live data.”
- **Evidence:** reasoning only, from the §10 quiesce, record, restart and failed-snapshot sentences.
- **Confidence:** high

### GROK-8 · Restore can be read as a copy onto live writers

- **Section:** §10, §11.4
- **Type:** gap
- **Severity:** minor
- **Finding:** Backup is careful to quiesce writers. `restore` is named, and §11.4 uses it for an incompatible state snapshot, but neither section says to stop this installation first. Copying mutable state or moving `current` under a live web or worker can mix the snapshot with new audit and job writes.
- **Proposed change:** Add to §10: “`atlasctl restore` targets one explicit installation, accepts only a snapshot marked complete, and stops that installation’s connector and web/worker writers before it replaces mutable state or the release pointer. If activation has not happened and restore fails, leave the previous state in place and start the stopped services again. After a successful activation, start those services. Restore does not write into a running writer and does not stop any other installation.”
- **Evidence:** reasoning only, from §10’s backup quiesce and §11.4’s restore clause.
- **Confidence:** high

### GROK-9 · Access key cache needs the documented rotation overlap

- **Section:** §5.1
- **Type:** gap
- **Severity:** minor
- **Finding:** §5.1 requires a JWKS cache with bounded refresh and a closed failure. Cloudflare rotates the Access signing key about every six weeks and keeps the previous key valid for seven days, and it warns that caching `public_cert` alone serves a stale current key. A cache that stores one certificate, or that waits out a refresh interval longer than the overlap without a fetch on an unknown `kid`, fails closed for every caller after rotation.
- **Proposed change:** Add to §5.1: “Load the JWKS set from `https://<team>.cloudflareaccess.com/cdn-cgi/access/certs` and select the key by the JWT `kid`. Do not pin `public_cert` alone. Refresh on the bounded schedule and refresh once immediately when `kid` is missing from the cache; if that refresh fails, reject the token. The refresh interval must be shorter than Cloudflare’s previous-key overlap.”
- **Evidence:** Cloudflare “Validate JWTs”, last updated 6 May 2026, checked 2026-10-22. Signing keys rotate every 6 weeks by default; previous keys stay valid for 7 days; match `kid` in `public_certs` and do not rely on a cached `public_cert`. https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/
- **Confidence:** high

## Top 3

1. GROK-1 — a host-wide deny of 80/443 contradicts the shared-VPS rule and can drop an approved neighbor.
2. GROK-2 — the default local-to-VPS dataset publish has no command that may touch an existing installation.
3. GROK-3 — mounting the release parent hides `current`, so atomic activation never becomes visible to the web container.

Result: complete
