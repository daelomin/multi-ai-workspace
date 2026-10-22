# DEEPSEEK review — round 2

Reviewed the local `spec.md` v1.2 (22 October 2026) after reading all round-1 reviews and `reviews/round-1/CONSOLIDATION.md`. This review checks internal consistency, implementability and acceptance coverage; it does not verify the source implementation, external platform documentation or a running deployment. Accepted round-1 findings are not repeated unless the merged text remains wrong. Open HUMAN decisions FB-D1, FB-D2 and FB-D3 are not reopened; DEEPSEEK-4 touches FB-D1 only as a minor question with new evidence about a missing contract, not about the choice itself. Seven minor findings, no blocking or major.

### DEEPSEEK-1 · The worker's release-writing path contradicts the sole-writer and read-only-mount rules

- **Section:** §3.2, §7.1, §6.3 (also §8.1, §13 WP6)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 gives the worker responsibility for "creates new dataset releases", but §7.1 says "the one-shot publisher ... is the only writer of `releases/` and `current`", and §6.3 lists only a "read-only release mount" in the required Compose shape. Nothing states whether the worker writes the release store itself, invokes the one-shot publisher as a subprocess, or gets a writable `data/` mount, and nothing says how it takes the publisher lock. As written, WP6 cannot be implemented without contradicting either the sole-writer rule or the release mount.
- **Proposed change:** Add to §3.2 and §7.1: "In worker mode the worker does not write `releases/` or `current` directly. It stages job output under its own state directory and invokes the validated publisher under the publisher lock (the same import-then-activate sequence). The worker profile mounts `data/` writable only for that publisher step, or the publisher runs as a separate one-shot service; web keeps the read-only mount." Alternatively, declare the worker the publisher and replace "one-shot publisher" with "publisher (one-shot in serving mode, worker-invoked in worker mode)", specifying the mount and lock.
- **Evidence:** reasoning only; cross-references §3.2, §6.3, §7.1, §8.1 and §13 WP6.
- **Confidence:** high.

### DEEPSEEK-2 · Serving mode has no supported way to refresh expiring live overlays

- **Section:** §8.2, §10 (also §3.1)
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.1 includes live overlay reading in serving mode, and §8.2 says serving mode "consumes exported overlays until expiry; ongoing live refresh requires the worker or a trusted external publisher". The only overlay-bearing operation is the initial serving import; `release import` writes only `data/releases/<release-id>/` and installation `import` refuses an existing installation. The "trusted external publisher" has no defined write path, authentication, lock or acceptance test, so a serving-only VPS loses live data as overlays expire with no routine way to replace them.
- **Proposed change:** Either (a) add `atlasctl overlay import` targeting one explicit installation, writing only `state/live/`, validating base-release compatibility, expiry and hashes under the publisher/live lock and refusing incompatible sets; or (b) state in §3.1 and §8.2 that serving mode has no overlay refresh and that refresh requires the worker or a documented re-import of a serving package with services stopped. If the external publisher is kept, define its authentication, write interface and lock, and add an acceptance case.
- **Evidence:** reasoning only; cross-references §3.1, §8.2 and the §10 command list/import rules.
- **Confidence:** high.

### DEEPSEEK-3 · Restore is missing from storage admission

- **Section:** §12.2, S05 (also §10)
- **Type:** gap
- **Severity:** minor
- **Finding:** §12.2 requires an admission estimate "before an image pull/load, release import, export, backup or publication" but not before `restore`. Restore extracts a complete snapshot of releases and mutable state and, per §10, must leave the previous state in place when it fails before activation, so it needs space for both trees. S05 tests insufficient bytes/inodes/quota without naming restore. A restore started on a nearly full filesystem can stop services, then fail for lack of space, which the hard-threshold rule does not cover.
- **Proposed change:** Add `restore` to the §12.2 list and define its estimate as extracted snapshot + retained current state/active release + staging, checked before any quiesce; refuse before stopping services when it cannot fit. Add restore to S05.
- **Evidence:** reasoning only; cross-references §10 restore and §12.2/S05.
- **Confidence:** high.

### DEEPSEEK-4 · The bounded diagnostic spool has no filesystem or configuration contract

- **Section:** §12.2, §7.1, §7.2 (also §6.2)
- **Type:** question
- **Severity:** minor
- **Finding:** FB-D1 asks which collector or spool receives diagnostics; separately from that choice, the spec has no place for either. §12.2 requires the web and helpers to write to a bounded spool or collector and makes preflight fail when none is configured, but §7.1's bundle layout contains no spool directory, §7.2 has no spool path, cap or collector-destination setting, and §6.2 gives web a read-only root filesystem with only a narrow state mount. An implementer cannot satisfy preflight or bound the spool without inventing the contract. This is new evidence about the missing contract, not a request to reopen the FB-D1 choice.
- **Proposed change:** Add the contract that FB-D1 will parameterize: a `state/logs/` (or equivalent) directory in §7.1 with an explicit cap and ownership, `ATLAS_DIAGNOSTIC_SPOOL_DIR` and `ATLAS_DIAGNOSTIC_SPOOL_CAP_BYTES` (or collector destination/cap) in §7.2, and a writable mount for web and helper containers in §6.3. State whether it is part of the narrow state mount or a separate bounded volume, and whether `cloudflared` has any path to it (the current text says it does not).
- **Evidence:** reasoning only; cross-references §6.2, §7.1, §7.2 and §12.2. Related open decision: FB-D1.
- **Confidence:** high.

### DEEPSEEK-5 · Application update has no defined entry point and conflicts with the import refusal

- **Section:** §4.0, §10, §11.4
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.0 says a new import creates a new installation identity "unless the operator explicitly selects an existing installation for an update/restore", but §10 says installation `import` "still refuses an existing installation" and the exhaustive `atlasctl` list contains no update/upgrade command. §11.4 requires an update procedure ("verify new image digests and compatibility ... update images and run smoke checks") without naming the interface, and §4.0 requires explicit authorization before a container is replaced. The supported path is therefore undefined; direct Compose recreation is possible but is not reconciled with the "one operational interface" sentence or the authorization rule.
- **Proposed change:** Define one path. Either add `atlasctl update` (explicit installation target, dry-run, pinned image references, preflight, backup ordering, explicit migration step, smoke check, no image or data cleanup) or state that application update is a documented host-runbook sequence of `atlasctl preflight` plus explicit `docker compose -p ... -f ... up -d` commands that first list the containers to be recreated and obtain authorization. Reconcile §4.0's "update" wording with §10's refusal in either case.
- **Evidence:** reasoning only; cross-references §4.0, §10, §11.4 and §13 WP4.
- **Confidence:** high.

### DEEPSEEK-6 · `release import` has no defined behavior when the release ID already exists

- **Section:** §8.1, §10, A19
- **Type:** gap
- **Severity:** minor
- **Finding:** `release import` writes to `data/releases/<release-id>/`, but neither §8.1's "rename the complete staging directory into the release store" nor §10 defines the outcome when that directory already exists. A retry after a lost response, a re-published release, or two producers using the same ID leaves the operator with an unspecified failure and, because of the no-deletion rule, no automatic way to recover; A19 tests only a new release and `init` idempotence.
- **Proposed change:** State that import never overwrites. If `data/releases/<release-id>/` exists, verify its envelope hashes and validation record: treat an identical re-import as idempotent success (no writes), otherwise refuse and leave both directories untouched. Add the duplicate/retry case to A19.
- **Evidence:** reasoning only; cross-references §8.1 step 4, §10 release import/import rules and A19. The exact rename failure is filesystem-dependent; the missing contract is not.
- **Confidence:** medium.

### DEEPSEEK-7 · A snapshot can be marked complete without verifying its contents

- **Section:** §10, §11.1, S07 (also A14)
- **Type:** gap
- **Severity:** minor
- **Finding:** The backup records "snapshot completion" and says any failed snapshot remains incomplete, but no step verifies the written snapshot before it is marked complete: there is no requirement to check the archive against a manifest/checksums, confirm the recorded active release is present and hash-valid, or name the publisher lock so a concurrent `release activate`/`release import` cannot change `releases/` or `current` during the copy. A silent truncation or a release added mid-copy could yield a complete-marked snapshot that fails the A11 restore; A14's drill is periodic, not per backup.
- **Proposed change:** Add to §10: "Before marking a snapshot complete, verify the written archive against its manifest/checksums, confirm the recorded active release is present and hash-valid, and confirm the previous-state copy is complete. Hold the publisher lock for the snapshot (or refuse concurrent `release import`/`release activate`); a verification failure marks the snapshot incomplete and reports the failed item. Verification does not delete or modify retained data." Add the verification case to S07.
- **Evidence:** reasoning only; cross-references §10 backup/marking text, §11.1, S07 and A14.
- **Confidence:** medium.

**Top 3**

1. DEEPSEEK-1 — the worker's release-writing path is inconsistent with §7.1's sole-writer rule and §6.3's read-only mount.
2. DEEPSEEK-2 — serving mode includes live overlay reading but defines no way to refresh overlays once they expire.
3. DEEPSEEK-3 — restore is the space-heaviest operation yet is omitted from §12.2 storage admission.

Result: complete
