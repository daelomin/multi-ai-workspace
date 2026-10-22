# GROK review — round 2

Reviewed local `spec.md` version 1.2 (22 October 2026) after `reviews/round-1/` and `reviews/round-1/CONSOLIDATION.md`. Accepted merges M1–M11 are left closed except where the merged sentence is still wrong. FB-D1, FB-D2 and FB-D3 are not reopened; GROK-7 is a minor question about the missing spool contract only.

Re-read on 22 October 2026: cloudflared `ingress/origin_proxy.go` on `master` still replaces `Host` and sets `X-Forwarded-Host` only when `hostHeader` is non-empty, so the M2 rule holds and is not filed again. Cloudflare's JWT page (last updated 6 May 2026) still matches the §5.1 six-week rotation and seven-day overlap; GROK-6 is only the acceptance wording.

### GROK-1 · The container-address deny does not match the chain that can see those packets

- **Section:** §4.4
- **Type:** risk
- **Severity:** minor
- **Finding:** §4.4 tells the host runbook to deny inbound traffic to Atlas container addresses, and the same paragraph points at `DOCKER-USER` because it sees post-DNAT container addresses. Docker's current iptables document says remote packets addressed to a container's own IP are dropped in the raw `PREROUTING` chain and never reach `DOCKER-USER`, so a rule there cannot implement that remote deny, and cannot allow it either. `FORWARD` jumps unconditionally to `DOCKER-USER`, and the spec gives no project-bridge exception, so a destination drop for the `atlas-web` address is aimed at forwarded flows, including the connector's path to port 8088.
- **Proposed change:** Replace the Atlas deny sentence in §4.4 with: "Atlas publishes no host ports. Remote hosts already cannot address an unpublished container IP; that drop happens before `DOCKER-USER`. Do not add a `DOCKER-USER` drop whose destination is an Atlas container address: forwarded project-bridge traffic, including `cloudflared` to `atlas-web:8088`, is the traffic that chain can match. Deny a host port that would publish Atlas, including 8088, and after any firewall change repeat A05, including one successful request through the Tunnel."
- **Evidence:** Docker iptables, "Docker with iptables", checked 2026-10-22: https://docs.docker.com/engine/network/firewall-iptables/ . Quoted behavior: direct-routed packets to a container IP are dropped in raw `PREROUTING` before `DOCKER-USER`; `FORWARD` jumps unconditionally to `DOCKER-USER`; packets in `DOCKER-USER` are already DNATed. No live ruleset was installed.
- **Confidence:** medium

### GROK-2 · The publication steps still replace `current` on a path that must not

- **Section:** §8.1 (also §10, A19)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Numbered step 4 renames the staging directory into the release store and then atomically replaces `current`. The following paragraph, §10 and A19 say `release import` writes only `data/releases/<release-id>/` and leaves `current` unchanged. "No partial publication" sits between those two contracts, so one reading treats an inactive imported release as a failed publication and the other forbids moving the pointer.
- **Proposed change:** After the numbered list in §8.1, add: "Steps 1–3 and the rename into `data/releases/<release-id>/` are what `release import` writes. Replacing `current` is `release activate`, or the local publisher's full transaction, under the publisher lock. An inactive complete directory is not a partial publication. `No partial publication` means a served release must not mix a manifest and files from two releases."
- **Evidence:** reasoning only, from §8.1 steps 4–6, the `release import` paragraph, §10 and A19.
- **Confidence:** high

### GROK-3 · The release copy can finish before the snapshot records `current`

- **Section:** §10 (also §11.1, S07)
- **Type:** gap
- **Severity:** minor
- **Finding:** The exporter may copy immutable releases outside the quiesce window, then stop writers and record the active release. `release import` followed by `release activate` can add a release and move `current` after that copy and before the pause. The snapshot can be marked complete with a pointer to bytes the archive does not contain, and no step holds the publisher lock or checks the recorded release's envelope hashes before that mark.
- **Proposed change:** Add to the §10 backup paragraph: "From the immutable-release copy through the complete mark, hold the publisher lock or refuse concurrent `release import` and `release activate`. Before marking a snapshot complete, check that the recorded active release is present in the snapshot and matches its envelope hashes. A failed check marks the snapshot incomplete, reports the missing item, and does not delete retained data." Add that check to S07.
- **Evidence:** reasoning only, from the §10 sentences "Copy immutable releases outside this pause where possible", "Record … snapshot completion" and "Any failed snapshot remains marked incomplete".
- **Confidence:** high

### GROK-4 · Worker mode creates releases without a writer, mount or lock

- **Section:** §3.2, §7.1 (also §6.3, §13 WP6)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 gives `atlas-worker` the job of creating dataset releases. §7.1 says the one-shot publisher is the only writer of `releases/` and `current`, and §6.3's Compose shape lists a read-only release mount. WP6 has no rule for whether the worker writes `data/`, calls the publisher, or takes the publisher lock, so the worker milestone cannot be built without breaking the sole-writer rule or the web mount.
- **Proposed change:** Add to §3.2 and §7.1: "The worker does not write `releases/` or `current`. It stages job output under its state directory and runs the same `release import` then `release activate` sequence under the publisher lock. The writable `data/` mount belongs to that publisher step. `atlas-web` keeps the read-only mount."
- **Evidence:** reasoning only, from §3.2, §6.3, §7.1, §8.1 and §13 WP6.
- **Confidence:** high

### GROK-5 · Restore can stop writers before anyone checks that it fits

- **Section:** §12.2, §10 (also S05)
- **Type:** gap
- **Severity:** minor
- **Finding:** §12.2 estimates space before image pull/load, release import, export, backup or publication. `restore` is absent. §10 stops the target installation's writers before replacing mutable state or the release pointer, and keeps the previous state only if failure happens before activation. A restore that quiesces first and then runs out of space is outside both the admission list and S05.
- **Proposed change:** Add `restore` to the §12.2 admission list: "Estimate extracted snapshot plus retained current state and active release plus staging, and refuse before stopping services when it cannot fit." Add restore to S05.
- **Evidence:** reasoning only, from §10 `atlasctl restore` and the §12.2 admission sentence.
- **Confidence:** high

### GROK-6 · A19 accepts an unknown `kid` after a refresh

- **Section:** §14 A19 (also §5.1)
- **Type:** risk
- **Severity:** minor
- **Finding:** A19 requires that a JWKS rotation whose `kid` is unknown be accepted after one refresh. §5.1 requires a fail-closed result when that refresh still cannot verify the token. Cloudflare's validation page says to match `kid` to an entry in `public_certs` (the set), and a `kid` that is still absent is not a signing key. An acceptance test written from A19 alone can pass a verifier that treats "refresh completed" as success.
- **Proposed change:** Replace the JWKS clause of A19 with: "A token whose `kid` is missing from the cache and present in the refreshed `public_certs` or JWK `keys` set verifies after one refresh. A `kid` still absent after that refresh is rejected and is not refreshed again for that request."
- **Evidence:** Cloudflare "Validate JWTs", last updated 6 May 2026, checked 2026-10-22: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/ . The page says previous keys stay valid for 7 days, which §5.1 already uses; the defect is the acceptance row.
- **Confidence:** high

### GROK-7 · The diagnostic spool has no directory, setting or writable mount

- **Section:** §12.2, §6.2, §7.1, §7.2
- **Type:** question
- **Severity:** minor
- **Finding:** FB-D1 still chooses the collector or spool. Apart from that choice, §6.2 gives the web container a read-only root filesystem and a bounded tmpfs, §7.1's tree has no diagnostics directory, and §7.2 has no path or cap. §4.2 and §12.2 each send the destination to the other section, so preflight's "configured spool" check has no setting to read. This is new evidence about the missing contract, not a request to pick the collector.
- **Proposed change:** Add the contract FB-D1 will parameterize: `state/diagnostics/` in §7.1, owned by the web UID, included in backup and excluded from automatic deletion; `ATLAS_DIAGNOSTIC_SPOOL_DIR` and `ATLAS_DIAGNOSTIC_SPOOL_CAP_BYTES`, or a collector URL plus cap, in §7.2; a writable mount of that directory in §6.3. Keep the existing statement that `cloudflared` does not write to it.
- **Evidence:** reasoning only, from §6.2, §7.1, §7.2, §4.2 and §12.2. Related open decision: FB-D1.
- **Confidence:** high

### GROK-8 · An existing installation can be updated in §4.0 and cannot in §10

- **Section:** §4.0, §10, §11.4
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.0 says a new import creates a new installation identity unless the operator selects an existing installation for an update or restore. §10 says installation `import` refuses an existing installation, including the earlier phrase "by default", and the `atlasctl` list has no update command. §11.4 requires an image update, an explicit migration and smoke checks, and §4.0 requires naming a container before it is replaced, with no command that does those steps.
- **Proposed change:** Add `atlasctl update` to the §10 command list: explicit installation target, pinned image references, preflight, the §11.4 backup-then-migrate order, a dry-run that names every container to be recreated, and no image or data cleanup. Delete "by default" from the installation-import refusal so update is the only write path onto an existing installation.
- **Evidence:** reasoning only, from §4.0, the §10 import refusal and command list, and §11.4.
- **Confidence:** high

### GROK-9 · A second `release import` of the same id has no result

- **Section:** §8.1, §10, A19
- **Type:** gap
- **Severity:** minor
- **Finding:** `release import` writes `data/releases/<release-id>/`. Step 4's rename and §10 never say what happens when that directory is already there. A retry after a lost response, or two producers using one id, has no specified success or refusal, and the deletion rule forbids removing the existing directory to make the retry fit. A19 covers a new release only.
- **Proposed change:** Add to §10 `release import`: "Never overwrite `data/releases/<release-id>/`. If it exists, compare envelope hashes and the validation record: an identical re-import is success with no writes; any difference refuses and leaves both trees unchanged." Add that case to A19.
- **Evidence:** reasoning only, from §8.1 step 4, §10 `release import` and A19.
- **Confidence:** medium

### GROK-10 · Serving mode's writable state tree includes live prices and jobs

- **Section:** §3.1, §7.1 (also §8.2)
- **Type:** gap
- **Severity:** minor
- **Finding:** Serving mode mounts datasets read-only and gives the web process one narrow writable state directory. §7.1 puts audit, jobs, live overlays and curated overrides under the same `state/` tree, and neither §6.3 nor §7.1 splits that mount. A serving `atlas-web` that can write `state/live` can change prices without the worker that §8.2 says owns each feed, and without a mutation route.
- **Proposed change:** Add to §7.1: "In serving mode, `atlas-web` may write only `state/control`. `state/live`, `state/jobs` and `state/overrides` are read-only for `atlas-web`. The worker, or a one-shot tool in an enabled mode, is the writer of those three directories."
- **Evidence:** reasoning only, from §3.1, §6.3, §7.1 and §8.2.
- **Confidence:** medium

**Top 3**

1. GROK-1 — a container-address deny in the chain §4.4 names does not see the remote packets Docker already drops, and can filter the Tunnel's bridge path.
2. GROK-3 — a snapshot can be marked complete while `current` names a release the immutable copy missed.
3. GROK-6 — A19 can accept a JWT whose `kid` never appears in the refreshed key set.

Result: complete
