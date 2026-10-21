# Round 1 consolidation — obd2-plugin spec

Consolidates `CHATGPT.md`, `DEEPSEEK.md` and `GROK.md` (round 1, spec v0.1) into **spec v0.2**. No `reviews/round-0/` and no `decisions.md` existed. Totals: 26 findings (0 blocking, 6 major, 20 minor) plus the three inline Gemini callouts that were in v0.1. HUMAN did not answer during the loop; no HUMAN decision was made here.

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified**: the provider reported no served model |

GROK's findings are consolidated on their content (each was cross-checked against the other reviews or the spec text), but the model that produced them is not confirmed.

## Accepted and merged

| Theme | Findings | Where in v0.2 |
|---|---|---|
| Read-only enforced as a service allowlist in the framing layer, before `exchange`; 04/08/UDS/raw frames rejected from every caller, with a test. Non-goal reworded. | DEEPSEEK-1, GROK-1 | §1, §5, §12, §14 |
| ECU identity in responses, capabilities, samples and DTCs; per-responder reassembly; no implicit merging or averaging; explicit validated metric-to-ECU mapping; `ambiguous` when the responder is unknown; two-ECU replay fixtures in acceptance. CHATGPT's explicit mapping was used rather than DEEPSEEK's "engine before transmission" precedence heuristic. | CHATGPT-1, DEEPSEEK-2, GROK-2 | §2, §5, §6, §10, §14 |
| Typed `ObdResponse` instead of `ByteArray`; adapter error words and `7F` never reach the decoder; `valid` only if response service = request + `0x40`. | GROK-3, Gemini §5 callout | §5 |
| Single owner and one exchange at a time; shared sample stream; no second poll loop; concurrency test. | DEEPSEEK-3, GROK-3 | §5 |
| DTCs as their own record (service `03`/`07`/`0A` kept apart, ECU, first/last seen, MIL); versioned export manifest; VIN/adapter redaction in exports; `TelemetryRecord` in sink/exporter. | DEEPSEEK-4, GROK-4 | §4, §5, §6, §14 |
| Quality enum gets `unsupported`; null `value` for unavailable/unsupported/error; `stale_after_ms`; `stale` keeps its last value but is not used for diagnosis. | DEEPSEEK-6, GROK-5 | §6 |
| Timing: `monotonic_ns` for ordering and windows, UTC for display; acquisition-time definition; per-diagnostic input age and separation limits; insufficient-data status; reconnect invalidates live inputs. | CHATGPT-2, DEEPSEEK-10, GROK-5 | §6, §10 |
| Raw vs derived: `origin`, `derivation`, `schema_version`. Gauge manifold pressure = PID `0B` − PID `33`, same ECU, both valid, signed, no substituted constant, not turbo-outlet pressure. The signed result was kept instead of DEEPSEEK's `max(0, …)` clamp so vacuum is not lost. | DEEPSEEK-7, GROK-8 | §4, §6 |
| Capability discovery: follow bitmap pages, four-state classification, a single miss does not remove a capability, re-discovery triggers. | DEEPSEEK-9, GROK-6 | §7 |
| Flight recorder stores every locally accepted sample; throttling below a floor is a recorded gap; gap-marked windows. Floor value is provisional. | DEEPSEEK-8 | §8 |
| Bounded local storage budget and write-failure behavior in Phase 1. | CHATGPT-3 | §9 |
| Consent and deletion reach the durable queue, ring buffer and retries; revoke-while-offline and delete-with-pending-retry tests. | CHATGPT-4, GROK-9 | §11, §14 |
| Measurable Phase 1 acceptance (rate, duration, drop tolerance, reconnect time); default ELM327 timeout limits throughput to about 4 queries/s. Values are provisional. | DEEPSEEK-12 | §7, §14 |
| Foreground service started while visible, `connectedDevice` type on Android 14+, watchdog and backoff reconnect mandated in Phase 1. Conditional on a native Android stack (§15 item 1). | GROK-7, Gemini §7 callout (blocking) | §4, §7, §12 |
| Session definition and `diagnostic_read` for engine-off DTC reads; interim rule is provisional. | DEEPSEEK-5, GROK-5 | §6 |
| Inline Gemini callouts removed; status line no longer says "(Reviewed)". Token refresh and Keystore-backed storage merged into §3; the TSDB point is already normative in §4 Phase 2. | GROK-10, Gemini §3 callout | header, §3, §4 |

## Decisions for HUMAN (carried forward)

None were answered. The spec shows an interim default where one is needed, marked *provisional*. Ids are stable across rounds.

| Id | Decision | Interim default in v0.2 | Source |
|---|---|---|---|
| FB-D1 | Offline entitlement: grace duration, the clock that measures it, and whether acquisition/local storage/export stop at expiry or only premium analysis/UI is gated. | None set; §11 states it is open. | DEEPSEEK-11, GROK-9 |
| FB-D2 | Phase 1 service scope: add Mode 02 (freeze frames) and/or Mode 09 (VIN, consent needed)? DEEPSEEK wants both added; GROK wants them left out. | Left out; allowlist is 01, 03, 07, 0A. | DEEPSEEK-4, GROK-1, GROK-4 |
| FB-D3 | Manual (user-initiated) DTC clearing: never in this module, or a later separate tool? Safety and scope. | Not in this module. | DEEPSEEK-1, GROK-1 |
| FB-D4 | Session boundary: user-started recording (GROK) versus automatic engine-running detection (DEEPSEEK); resume grace period. | User-started, resume within a grace period. | DEEPSEEK-5, GROK-5 |
| FB-D5 | Local storage: may the oldest data be evicted automatically, or must persistence pause? Numeric budget and retention defaults. | Pause and report the gap unless an eviction policy is authorized. | CHATGPT-3 |
| FB-D6 | Numeric acceptance thresholds and the flight-recorder acquisition floor (5 signals ≥1 Hz, 10 min, ≥95%, reconnect ≤10 s; floor ≥1 Hz). | Provisional; to be set from the §15 item 3 benchmark. | DEEPSEEK-8, DEEPSEEK-12 |

## Rejected or deferred

| Item | Decision | Reason |
|---|---|---|
| Name a time-series product (Gemini §4 callout, "major") | Deferred | v0.1 already says Prometheus is not the sole raw archive. The product depends on the cost benchmark (§15 items 6–7). |
| Explicit blocklist details: 05/06, 2F/31/34–3E, Mode 22 whitelist now (DEEPSEEK-1) | Partly rejected | Deny by default makes a list of forbidden modes unnecessary. Mode 22 stays a Phase 3 item. |
| Engine-before-transmission precedence for duplicate metrics (DEEPSEEK-2) | Rejected | Replaced by an explicit validated mapping (CHATGPT-1). |
| `max(0, MAP − baro)` clamp (DEEPSEEK-7) | Rejected | A signed result keeps vacuum information. |
| Server-side ordering by `received_at` and clock-offset events (DEEPSEEK-10) | Deferred | Phase 2 detail; `received_at` is kept in the schema. |
| Cap on session length, manual split/merge (DEEPSEEK-5) | Deferred | Depends on FB-D4. |
| Cache invalidation after N consecutive misses (DEEPSEEK-9) | Merged, N unset | Kept as a configurable trigger; no number invented. |
| Library choices (`shareIn`, `Mutex`, `elapsedRealtimeNanos`) | Not adopted | The stack is unconfirmed (§15 item 1); the requirement is stated without the API. |

## Traceability

| Finding | Severity | Outcome | Spec v0.2 |
|---|---|---|---|
| CHATGPT-1 | major | Accepted | §5, §6, §14 |
| CHATGPT-2 | minor | Accepted | §6, §10 |
| CHATGPT-3 | minor | Accepted; FB-D5 | §9 |
| CHATGPT-4 | minor | Accepted | §11, §14 |
| DEEPSEEK-1 | major | Accepted; FB-D3 | §1, §12 |
| DEEPSEEK-2 | major | Accepted, precedence rule rejected | §5, §6 |
| DEEPSEEK-3 | minor | Accepted | §5 |
| DEEPSEEK-4 | minor | Accepted; Modes 02/09 FB-D2 | §4, §5, §6 |
| DEEPSEEK-5 | minor | Accepted as provisional; FB-D4 | §6 |
| DEEPSEEK-6 | minor | Accepted | §6 |
| DEEPSEEK-7 | minor | Accepted, clamp rejected | §6 |
| DEEPSEEK-8 | minor | Accepted; FB-D6 | §8 |
| DEEPSEEK-9 | minor | Accepted | §7 |
| DEEPSEEK-10 | minor | Accepted; server part deferred | §6 |
| DEEPSEEK-11 | minor | Not decided; FB-D1 | §11 |
| DEEPSEEK-12 | minor | Accepted; FB-D6 | §7, §14 |
| GROK-1 | major | Accepted | §1, §12 |
| GROK-2 | major | Accepted | §5, §6 |
| GROK-3 | major | Accepted | §5, §7 |
| GROK-4 | minor | Accepted | §6 |
| GROK-5 | minor | Accepted | §6 |
| GROK-6 | minor | Accepted | §7 |
| GROK-7 | minor | Accepted, stack-conditional | §4 |
| GROK-8 | minor | Accepted | §6 |
| GROK-9 | minor | Accepted; grace duration FB-D1 | §11 |
| GROK-10 | minor | Accepted | header, §3, §4 |
| Gemini §3 (minor) | — | Merged | §3 |
| Gemini §4 (major) | — | Deferred | §4 |
| Gemini §5 (minor) | — | Merged with GROK-3 | §5 |
| Gemini §7 (blocking) | — | Merged with GROK-7 | §4, §7 |

## Next

README now points at **Round 2**, reviewing `spec.md` v0.2. Round 2 reviewers should not re-raise the accepted items above as blocking or major, and should treat FB-D1 to FB-D6 as open.
