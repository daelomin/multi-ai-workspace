# Round 1 consolidation — vps-fuelatlas-version

Consolidated by CLAUDE on 22 October 2026. Reviewed: `spec.md` v1.1 (README labelled it v0.1; all three reviewers used the actual v1.1). Result: `spec.md` **v1.2**. No round-0 consolidation exists, so there were no earlier decisions to carry.

Totals: 19 findings (CHATGPT 3, DEEPSEEK 7, GROK 9), 0 blocking, 5 major (DEEPSEEK-1, DEEPSEEK-2, GROK-1, GROK-2, GROK-3), 14 minor. Several are duplicates, so they merge into 11 changes.

## Reviewer provenance

Requested vs served model:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | unverified (provider reported no served model) | **unverified** |

GROK is the only unverified reviewer. Its findings were still used. Its external claims were weighed on their evidence, and the only one I could check locally (port 8099 in `docs/ATLAS-SPEC.md`) was confirmed.

## Accepted and merged

| # | Change in spec v1.2 | Findings | Where |
|---|---|---|---|
| M1 | Replace the host-wide deny of 80/443 with an Atlas-scoped rule: Atlas publishes no ports; deny to Atlas container addresses and 8088; keep owner-approved neighbor listeners; 8099 defined as the local-only Python query server; Docker firewall caveats; A05 clarified | CHATGPT-1, DEEPSEEK-3, DEEPSEEK-4, GROK-1 | §4.4, A05 |
| M2 | Origin must see the public hostname: classify by the `Host` delivered to `atlas-web`, ignore `X-Forwarded-Host`; per hostname either show the connector preserves `Host` or set `httpHostHeader` to that exact hostname; record the observed behavior; A17 | DEEPSEEK-1, GROK-5 | §4.1, A17 |
| M3 | `/internal/*` not forwarded by either hostname and refused by the app outside loopback/probe source; A16 | DEEPSEEK-6, GROK-6 | §4.1, §5.1, A16 |
| M4 | `atlasctl release import` for an existing installation (writes only `data/releases/<id>/`), linked from §8.1 | DEEPSEEK-2, GROK-2 | §8.1, §10, A19 |
| M5 | Mount `data/` (containing `releases/` and `current`) read-only in web; publisher mounts it writable | GROK-3 | §7.1 |
| M6 | Single-release binding for manifest and dependent tiles/indexes; A18 | CHATGPT-2 | §8.1, A18 |
| M7 | Backup records the running service set and restores only that set after failure or interruption; recovery command; leave-stopped flag | CHATGPT-3, GROK-7 | §10, S07 |
| M8 | `restore` accepts only complete snapshots and stops only the target installation's writers | GROK-8 | §10, S07 |
| M9 | Logging: `logging.driver: none` for all Atlas services; diagnostics go straight to a bounded spool or collector; `docker logs` is not the path; collector egress in §4.2 | DEEPSEEK-5, GROK-4 | §4.2, §12, §12.2 |
| M10 | `atlasctl init` added (idempotent, no recursive chown); §6.2 and §11.2 aligned | DEEPSEEK-7 | §6.2, §10, §11.2, A19 |
| M11 | JWKS selection by `kid`, refresh shorter than the 7-day overlap, one immediate refresh on unknown `kid` | GROK-9 | §5.1, A19 |

Conflict resolved in M2: DEEPSEEK-1 says the origin receives the service host by default; GROK-5 says (from cloudflared source) the original `Host` is preserved unless `httpHostHeader` is set. Neither was tested against a live Tunnel. v1.2 requires verifying the behavior with the pinned connector and setting a per-hostname value if it is not preserved, which holds under either reading.

## Decisions for HUMAN (carried forward)

Not decided by CLAUDE; the loop continues without them. No earlier FB-D items existed.

- **FB-D1 — Diagnostics collector.** Which bounded collector or spool, with what cap and egress, receives Atlas diagnostics under M9? Needed before WP0/§12.2 can be implemented; v1.2 only requires that preflight fail when none is configured. Related: cloudflared and helper output cannot reach an app-level spool; confirm that metrics and exit status are enough for them.
- **FB-D2 — Release trust model for `release import`.** Authenticated transport only, or signed release manifests with a trust key (§8.1 allows either)? The choice sets the producer workflow and the key to hold.
- **FB-D3 — Leave-stopped flag.** Whether a backup or restore may ever leave the installation stopped on operator request (M7/M8 permit it only by explicit flag); safety/availability policy.

## Rejected or deferred

None rejected outright. Partial adoptions:

- GROK-1's proposed text was shortened and merged into M1; the `DOCKER-USER` detail stays in the host runbook scope.
- DEEPSEEK-7 offered "fold init into preflight" as an alternative; kept the separate `init` because `preflight` must stay non-mutating (§4.0).
- DEEPSEEK-1's request for a rejecting origin test is covered by A17 rather than a new origin-level rejection rule.
- The `cloudflared` log gap under `logging.driver: none` is documented, with the decision deferred to FB-D1.

## Traceability

| Finding | Severity | Disposition |
|---|---|---|
| CHATGPT-1 | minor | Accepted, M1 |
| CHATGPT-2 | minor | Accepted, M6 |
| CHATGPT-3 | minor | Accepted, M7 |
| DEEPSEEK-1 | major | Accepted, M2 |
| DEEPSEEK-2 | major | Accepted, M4 |
| DEEPSEEK-3 | minor | Accepted, M1 |
| DEEPSEEK-4 | minor | Accepted, M1 |
| DEEPSEEK-5 | minor | Accepted, M9 (FB-D1) |
| DEEPSEEK-6 | minor | Accepted, M3 |
| DEEPSEEK-7 | minor | Accepted, M10 |
| GROK-1 | major | Accepted, M1 |
| GROK-2 | major | Accepted, M4 (FB-D2) |
| GROK-3 | major | Accepted, M5 |
| GROK-4 | minor | Accepted, M9 |
| GROK-5 | minor | Accepted, M2 |
| GROK-6 | minor | Accepted, M3 |
| GROK-7 | minor | Accepted, M7 (FB-D3) |
| GROK-8 | minor | Accepted, M8 (FB-D3) |
| GROK-9 | minor | Accepted, M11 |

Because major findings were present, the stop rule does not end the loop; Round 2 reviews v1.2.
