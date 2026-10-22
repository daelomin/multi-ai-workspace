# CHATGPT review — round 1

Reviewed the local `spec.md`, Version 1.1 dated 22 October 2026. The README's current-round version label still says v0.1; this review uses the actual local specification as instructed. No round-0 reviews or consolidation are present. This is an independent first-round review based on internal requirements and failure scenarios; it does not verify the source project's implementation, platform documentation or a running deployment.

### CHATGPT-1 · Firewall instructions need an explicit neighboring-listener exception

- **Section:** §4.4; A05; S02
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The instruction to deny inbound application traffic including ports 80 and 443 can be read as a host-wide port ban, although the same paragraph requires preserving neighboring-service connectivity. A sibling application may legitimately use those ports. Atlas already has the separate requirement of publishing no ports, so its isolation test must distinguish an unrelated listener from an Atlas exposure.
- **Proposed change:** Add: "Apply Atlas isolation without blocking an owner-approved neighboring listener on the same host. Do not install host-wide denies for ports 80/443 merely because Atlas uses Tunnel. Record the owner of each existing public listener; external probes must demonstrate that no listener routes to Atlas, while approved neighboring listeners remain reachable. A05 does not require the entire host to have no public listeners."
- **Evidence:** reasoning only — the generic port-deny wording in §4.4 conflicts with its neighboring-service preservation requirement when an approved sibling uses HTTPS.
- **Confidence:** high

### CHATGPT-2 · Define consistency across manifest and tile requests

- **Section:** §7.1; §8.1; §9; A10
- **Type:** gap
- **Severity:** minor
- **Finding:** Resolving the active release once per request protects individual responses, but a map can fetch its manifest before promotion and its tiles or indexes afterward. The spec mentions versioned tiles but does not explicitly require all dependent URLs to stay bound to the manifest's release, leaving the multi-request consistency contract unclear.
- **Proposed change:** Add: "A manifest and its dependent tiles/indexes SHALL identify a single release through immutable release-qualified URLs or an equivalent explicit release selector. Subsequent requests using that identity resolve the retained release rather than the current pointer; cache keys include that identity. Test promotion between a manifest fetch and its dependent requests and verify that all returned files belong to the selected release. State separately whether independent live API requests may observe a newer release."
- **Evidence:** reasoning only — request A can resolve release R1, activation can select R2, and request B can then resolve R2 without violating the existing per-request rule.
- **Confidence:** high

### CHATGPT-3 · Specify recovery after a failed quiesced backup

- **Section:** §10; §11.1; S07
- **Type:** gap
- **Severity:** minor
- **Finding:** The initial backup method stops the installation's connector and writers and later restarts paused services, but does not explicitly define recovery when copying or verification fails or the backup process is interrupted. A routine failed nightly backup could consequently leave the serving installation stopped, even though the archive is correctly marked incomplete.
- **Proposed change:** Add: "Before quiescing, durably record which services were running and the backup operation phase. On success or failure, attempt to restore only that recorded running set, starting writers/web and verifying readiness before reconnecting ingress; do not start services that were previously stopped. Preserve the incomplete snapshot and failure report. Provide an idempotent recovery command for abrupt process/host interruption, and test copy failure plus interruption after services stop. If readiness cannot be restored, leave ingress stopped and emit an actionable alert."
- **Evidence:** reasoning only — snapshot validity and service recovery are separate obligations; marking a failed archive incomplete does not restart the paused installation.
- **Confidence:** high

**Top 3**

1. Clarify that Atlas firewall isolation preserves approved neighboring public listeners.
2. Bind dependent manifest/tile requests to one retained release.
3. Recover the previously running service set after failed or interrupted backups.

No blocking or major findings.

Result: complete
