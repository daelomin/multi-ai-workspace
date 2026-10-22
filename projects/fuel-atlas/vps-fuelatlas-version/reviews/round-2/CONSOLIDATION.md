# Round 2 consolidation — vps-fuelatlas-version

Consolidated by CLAUDE on 22 October 2026. Reviewed: `spec.md` v1.2. Result: `spec.md` **v1.3**. This is the last round: no blocking or major finding was raised, so the stop rule is met and the review converged at round 2.

Totals: 17 findings (CHATGPT 0, DEEPSEEK 7, GROK 10), 0 blocking, 0 major, 17 minor. All 17 are accepted; duplicates merge into 11 changes (N1–N11).

## Reviewer provenance

Requested vs served model:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | unverified (provider reported no served model) | **unverified** |

GROK is the only unverified reviewer. Its findings were used. GROK-1 and GROK-6 rest on external documentation (Docker iptables, Cloudflare JWT page); CLAUDE did not re-check either. GROK-1 is applied with a pointer to the source (R6) and a note to confirm it on the host's Docker version.

## Accepted and merged

| # | Change in spec v1.3 | Findings | Where |
|---|---|---|---|
| N1 | Worker does not write `releases/`/`current`; it stages output and runs `release import` then `release activate` under the publisher lock; writable `data/` belongs to the publisher step; web stays read-only | DEEPSEEK-1, GROK-4 | §3.2, §7.1 |
| N2 | Serving mode has no overlay refresh command; refresh needs the worker or re-import of a serving package; `atlasctl overlay import` left as FB-D4 | DEEPSEEK-2 | §8.2 |
| N3 | `restore` (and `update`) added to storage admission; restore estimate checked before any service stops; added to S05 | DEEPSEEK-3, GROK-5 | §12.2, S05 |
| N4 | Diagnostic spool contract: `state/diagnostics/`, `ATLAS_DIAGNOSTIC_SPOOL_DIR`, `ATLAS_DIAGNOSTIC_SPOOL_CAP_BYTES`, writable mount for web/helpers, never `cloudflared`. The collector choice stays FB-D1 | DEEPSEEK-4, GROK-7 | §6.3, §7.1, §7.2, §12.2 |
| N5 | Added `atlasctl update` (explicit target, pinned images, preflight, backup-then-migrate, dry-run naming containers, no cleanup); removed "by default" from the import refusal; §11.4 points to it | DEEPSEEK-5, GROK-8 | §10, §11.4 |
| N6 | `release import` never overwrites an existing release ID: identical re-import is a no-write success, a difference is refused; added to A19 | DEEPSEEK-6, GROK-9 | §10, A19 |
| N7 | Hold the publisher lock (or refuse concurrent `release import`/`activate`) from the first release copy to the complete mark; verify archive, recorded active release and previous-state copy before marking complete; added to S07 | DEEPSEEK-7, GROK-3 | §10, S07 |
| N8 | Remove the container-address deny; keep the deny on host ports that would publish Atlas; explain Docker's raw `PREROUTING` drop; repeat A05 with one successful Tunnel request; add R6 | GROK-1 | §4.4, §16 |
| N9 | `release import` writes steps 1–3 plus the rename; `current` moves only in `release activate` or the full local publisher; "no partial publication" means no manifest/file mixing | GROK-2 | §8.1 |
| N10 | A19 JWKS wording: known-after-refresh `kid` verifies; still-absent `kid` is rejected and not refreshed again for that request | GROK-6 | A19 |
| N11 | Serving `atlas-web` writes only `state/control` and `state/diagnostics`; `state/live`, `jobs`, `overrides` read-only for it | GROK-10 | §7.1 |

Choices made where reviewers offered alternatives:

- N2: DEEPSEEK-2 offered a new `atlasctl overlay import` or an explicit "no refresh" statement. I wrote the lower-scope statement and left the command as a new HUMAN decision (FB-D4).
- N5: both reviewers offered a runbook-only update or a new command; I chose `atlasctl update` (GROK-8) to keep one operational interface.
- N7: the snapshot rule uses the publisher lock or refusal of concurrent imports, as both reviewers proposed.

## Decisions for HUMAN (carried forward)

Not decided by CLAUDE; the loop did not wait for them.

- **FB-D1 — Diagnostics collector.** Which bounded collector or spool, with what cap and egress, receives Atlas diagnostics? v1.3 defines the spool paths and settings (N4) but not the choice; confirm that metrics and exit status are enough for cloudflared and helper output.
- **FB-D2 — Release trust model for `release import`.** Authenticated transport only, or signed release manifests with a trust key (§8.1 allows either)?
- **FB-D3 — Leave-stopped flag.** Whether a backup or restore may ever leave the installation stopped on operator request.
- **FB-D4 — Serving-mode overlay refresh (new).** Keep the v1.3 statement (no refresh command; use the worker or re-import), or add `atlasctl overlay import` writing only `state/live`?

## Rejected or deferred

None rejected. Deferred: FB-D4 (the command itself) and the FB-D1 collector choice. The `DOCKER-USER` detail stays in the host runbook scope.

## Traceability

| Finding | Severity | Disposition |
|---|---|---|
| CHATGPT | none | No findings; FB-D1 to FB-D3 confirmed open |
| DEEPSEEK-1 | minor | Accepted, N1 |
| DEEPSEEK-2 | minor | Accepted, N2 (FB-D4) |
| DEEPSEEK-3 | minor | Accepted, N3 |
| DEEPSEEK-4 | minor | Accepted, N4 (FB-D1) |
| DEEPSEEK-5 | minor | Accepted, N5 |
| DEEPSEEK-6 | minor | Accepted, N6 |
| DEEPSEEK-7 | minor | Accepted, N7 |
| GROK-1 | minor | Accepted, N8 |
| GROK-2 | minor | Accepted, N9 |
| GROK-3 | minor | Accepted, N7 |
| GROK-4 | minor | Accepted, N1 |
| GROK-5 | minor | Accepted, N3 |
| GROK-6 | minor | Accepted, N10 |
| GROK-7 | minor | Accepted, N4 (FB-D1) |
| GROK-8 | minor | Accepted, N5 |
| GROK-9 | minor | Accepted, N6 |
| GROK-10 | minor | Accepted, N11 |

No blocking or major findings: the review converged at round 2 on spec v1.3. FB-D1 to FB-D4 remain open for HUMAN.
