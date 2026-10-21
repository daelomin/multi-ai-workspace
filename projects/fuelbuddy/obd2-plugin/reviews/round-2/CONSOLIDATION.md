# Round 2 consolidation — obd2-plugin spec

Consolidates `CHATGPT.md`, `DEEPSEEK.md` and `GROK.md` (round 2, spec v0.2) into **spec v0.3**. Totals: 18 findings (0 blocking, 0 major, 18 minor). Round 2 produced no blocking or major finding, so the stop rule is met and **this is the last round**: the review converged at round 2. No `decisions.md` existed. HUMAN did not answer during the loop; no HUMAN decision was made here.

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified**: the provider reported no served model |

GROK's findings are consolidated on their content: each cites the ELM327 datasheet or the public PID table, and the overlapping ones (GROK-3 with DEEPSEEK-7, GROK-8 with DEEPSEEK-1) agree with verified reviewers. The datasheet and Wikipedia claims were not re-fetched here. The model that produced them is not confirmed.

## Accepted and merged

| Theme | Findings | Where in v0.3 |
|---|---|---|
| `exchange` returns an `ObdExchange` (per-responder outcomes plus completion status); one negative or failed responder does not discard another's payload; the queue advances once the channel is idle or recovered. | CHATGPT-1 | §5, §14 |
| Capability cache key includes `vehicle_id`; rediscovery on vehicle change; cache is a hint until validated. | CHATGPT-2 | §7 |
| Upload-consent revocation keeps local recordings under local policy; explicit deletion removes local, ring and queued copies; two separate tests. | CHATGPT-3 | §11 |
| Closed, reviewed adapter-command set (identification, echo/line-ending, `AT TP`, headers, CAN filter, timeout/response count); EEPROM writes, `AT SP`, monitor mode and wakeup-message commands excluded; no vehicle service byte outside the allowlist; test that allowed commands are in the set. | DEEPSEEK-1, GROK-8 | §12 |
| `ambiguous` added to `quality`, `attribution` field, `source_address` null only when ambiguous; unattributed case in the fixture. | DEEPSEEK-2 | §5, §6, §14 |
| Acquisition time defined as response completion; request start recorded separately. | DEEPSEEK-3 | §6 |
| Recording epoch defined; `epoch_id` on records and derivation refs; reconnect keeps the epoch and adds a gap marker; process restart starts a new epoch. | DEEPSEEK-4 | §6 |
| `DiagnosticEvent` record added to `TelemetryRecord`; flight-recorder windows keyed to the event id; export and fixture coverage. | DEEPSEEK-5 | §5, §6, §8, §14 |
| "Engine known to be running" removed from the derived-metric rule (option 1 of the finding; engine-off MAP equals ambient, so the result is a correct reading). | DEEPSEEK-6 | §6 |
| Normalised payload: header moved to `source`, ISO-TP framing and PCI byte removed, multiline concatenated, service byte at index 0; `+0x40` and `7F` tests use it. | DEEPSEEK-7, GROK-3 | §5 |
| Expected-response count is a maximum: measure first, never below the measured count, no count digit until measured; shortened timeout not below the slowest observed responder. | GROK-1 | §5 (referenced from §7) |
| `7F xx 78` response pending is a wait, not a `Negative`; one bounded wait extended once; a positive from one responder does not cancel another's wait; `Negative.code` is the third byte. | GROK-2 | §5, §14 |
| Responder identity per negotiated protocol (11-bit `7E8`–`7EF`, 29-bit reported id, non-CAN header source byte); mismatches are `ambiguous`. The 29-bit functional request id was not added because no reviewer sourced one. | GROK-4 | §5 |
| Service `01` validity requires the echoed PID to be a requested one; each echoed PID is its own sample; bank 1/2 fuel trims on separate keys. | GROK-5 | §5 |
| DTC decoding (two bytes, category bits), `0000` padding ignored, `mil_on` from Mode `01` PID `01`, `occurrence_count` defined as locally observed recordings. PID `01` is inside the existing allowlist, so FB-D2 is unaffected. | GROK-6 | §6 |
| Progress lines ignored (`SEARCHING...`, `BUS INIT: ...`, `OK`); `LV RESET` and other non-hex lines are `AdapterError`. | GROK-7 | §5 |

## Decisions for HUMAN (carried forward)

All six are still open. None was decided in round 1 or round 2, and no round-2 finding changes them. The spec marks the interim defaults *provisional*. Ids are stable.

| Id | Decision | Interim default in v0.3 | Source |
|---|---|---|---|
| FB-D1 | Offline entitlement: grace duration, the clock that measures it, and whether acquisition/local storage/export stop at expiry or only premium analysis/UI is gated. | None set; §11 states it is open. | R1: DEEPSEEK-11, GROK-9 |
| FB-D2 | Phase 1 service scope: add Mode 02 (freeze frames) and/or Mode 09 (VIN, consent needed)? DEEPSEEK wanted both; GROK wanted them left out. | Left out; allowlist is 01, 03, 07, 0A. | R1: DEEPSEEK-4, GROK-1, GROK-4 |
| FB-D3 | Manual (user-initiated) DTC clearing: never in this module, or a later separate tool? Safety and scope. | Not in this module. | R1: DEEPSEEK-1, GROK-1 |
| FB-D4 | Session boundary: user-started recording versus automatic engine-running detection; resume grace period. | User-started, resume within a grace period. | R1: DEEPSEEK-5, GROK-5 |
| FB-D5 | Local storage: may the oldest data be evicted automatically, or must persistence pause? Numeric budget and retention defaults. | Pause and report the gap unless an eviction policy is authorized. | R1: CHATGPT-3 |
| FB-D6 | Numeric acceptance thresholds and the flight-recorder acquisition floor (5 signals ≥1 Hz, 10 min, ≥95%, reconnect ≤10 s; floor ≥1 Hz). | Provisional; to be set from the §15 item 3 benchmark. | R1: DEEPSEEK-8, DEEPSEEK-12 |

## Rejected or deferred

| Item | Decision | Reason |
|---|---|---|
| DEEPSEEK-6 alternative: define engine-running as RPM `valid` and greater than zero | Not adopted | The finding offered it as an alternative; the first option removes an unneeded precondition and adds no new input. |
| DEEPSEEK-1 wording on "set is fixed" for non-volatile parameters beyond `AT SP` | Merged, not extended | Covered by the "EEPROM or programmable parameters" exclusion; no further command list invented. |
| GROK-2 numeric 5-second pending wait | Not written as a number | The finding cites the datasheet rather than a J1979 clause. The spec says "one bounded wait" and leaves the value to the §15 item 3 benchmark. |
| GROK-4 29-bit functional request id | Not added | No reviewer sourced one. |
| Server-side ordering and clock offset (from round 1) | Still deferred | Phase 2 detail. |

## Traceability

| Finding | Severity | Outcome | Spec v0.3 |
|---|---|---|---|
| CHATGPT-1 | minor | Accepted | §5, §14 |
| CHATGPT-2 | minor | Accepted | §7 |
| CHATGPT-3 | minor | Accepted | §11 |
| DEEPSEEK-1 | minor | Accepted (merged with GROK-8) | §12 |
| DEEPSEEK-2 | minor | Accepted | §5, §6, §14 |
| DEEPSEEK-3 | minor | Accepted | §6 |
| DEEPSEEK-4 | minor | Accepted | §6 |
| DEEPSEEK-5 | minor | Accepted | §5, §6, §8, §14 |
| DEEPSEEK-6 | minor | Accepted, option 1 | §6 |
| DEEPSEEK-7 | minor | Accepted (merged with GROK-3) | §5 |
| GROK-1 | minor | Accepted | §5, §7 |
| GROK-2 | minor | Accepted, no numeric wait | §5, §14 |
| GROK-3 | minor | Accepted (merged with DEEPSEEK-7) | §5 |
| GROK-4 | minor | Accepted, no 29-bit request id | §5 |
| GROK-5 | minor | Accepted | §5 |
| GROK-6 | minor | Accepted | §6 |
| GROK-7 | minor | Accepted | §5 |
| GROK-8 | minor | Accepted (merged with DEEPSEEK-1) | §12 |

## Next

The review converged at round 2 on spec v0.3. README says so, and no round 3 is scheduled. FB-D1 to FB-D6 remain with HUMAN. Items to settle before implementation are in spec §15; the pending-wait duration and the expected-response count are to be measured in the §15 item 3 benchmark.
