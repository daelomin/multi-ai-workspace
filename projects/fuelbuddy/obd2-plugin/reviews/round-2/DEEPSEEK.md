# DEEPSEEK review — round 2

Reviewed local `spec.md` **v0.2** (2026-10-21) after reading the project `README.md`, all three round-1 reviews, `reviews/round-1/CONSOLIDATION.md`, and the round-2 review by CHATGPT that was present in `reviews/round-2/` at read time. Counts: **0 blocking, 0 major, 7 minor**. I do not re-raise the items accepted and merged in round 1, and I do not re-raise FB-D1–FB-D6; every finding below is a residual inconsistency or gap in the merged v0.2 text. No external claim is made and no source was re-fetched: all evidence is reasoning against the local spec, as stated per finding. Proposed names are additions, not claims about existing implementation.

### DEEPSEEK-1 · Widen the adapter-command allowlist to the commands the spec requires

- **Section:** §12 (also §4, §5, §7)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §12 permits the OBD services `01`, `03`, `07`, `0A` "and the adapter-local commands needed to connect and enable response headers". Three behaviours mandated elsewhere need adapter-local commands outside that description: §5 allows "physical addressing" as the alternative to headers-on, which needs a header/receive-filter command rather than a header-enable command; §4 requires adapter identification and §7 keys the capability cache by adapter + firmware + protocol, which requires querying adapter and protocol identity; and §7 makes "shorter timeouts and expected-response counts" part of adapter validation, which are adapter-local settings. Read literally, the safety boundary forbids commands the rest of the spec requires, so an implementer must either fail those requirements or widen the allowlist ad hoc without a rule.
- **Proposed change:** Replace "the adapter-local commands needed to connect and enable response headers" with a named closed set, for example: adapter identification/version query, echo and line-ending configuration, protocol selection and identification, response headers on, CAN header and receive-address filter (for physical addressing), response timeout and expected-response count. State that the set is fixed and reviewed, that no command in it may carry a vehicle service byte outside the OBD allowlist, and that adapter commands which change non-volatile adapter configuration (e.g. programmable parameters) or place the adapter in an unsolicited streaming monitor mode are outside the set. Keep the existing rejection test and add one asserting every allowed adapter command is in the set.
- **Evidence:** reasoning only; the requirements are in §4 Phase 1, §5 ECU identity, §7 discovery/latency and §12 of v0.2.
- **Confidence:** high

### DEEPSEEK-2 · Give `ambiguous` a representation in the record schema

- **Section:** §5, §6 (also §10)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §5 says that if the responder cannot be established "the result is `ambiguous` and is excluded from ECU-specific diagnostics", §6 says a DTC with no responder address is stored as `ambiguous`, and §10 consumes "ambiguous" inputs. But the §6 `quality` enum has no `ambiguous` member, and the schema table marks `source_address` as "required for `obd2`", so an ambiguous record has no legal representation: it must invent a quality value, write null into a field declared required, or be dropped. §5's rule that samples and DTC records "carry the responder address" cannot hold for these records either, although the exclusion semantics in §10 presuppose that they are stored.
- **Proposed change:** Add `ambiguous` to the quality enum and state its value rule (retain the decoded value, never treat it as `valid`, exclude it from ECU-specific diagnostics and from any merging or averaging). Make `source_address` nullable exactly when attribution is ambiguous, and add a companion `attribution` field (`attributed | ambiguous`) to samples and `DtcRecord`, or use wording with the same effect; change §5's rule to "carry the responder address when attribution succeeds". Add an unattributed case to the existing two-ECU replay fixture.
- **Evidence:** reasoning only; the three uses of "ambiguous" are in §5, §6 and §10 and the enum is in §6.
- **Confidence:** high

### DEEPSEEK-3 · Define acquisition time instead of instructing the implementer to define it

- **Section:** §6
- **Type:** gap
- **Severity:** minor
- **Finding:** The §6 Time paragraph still reads "Define whether acquisition time is request start or response completion, and keep request/response timing where it expresses uncertainty." That is an instruction, not a rule; `observed_at` is defined only as "UTC time of acquisition". Every stored timestamp, every `stale_after_ms` age and every §10 maximum-separation comparison depends on the choice the spec leaves open, and two implementations can both conform while stamping the same sample up to a response timeout apart — which matters at the §8 1 Hz floor and to the §14 acceptance measurement. This is residual, not a re-raise: the round-1 timing item was merged as an acquisition-time definition, but v0.2 does not state one.
- **Proposed change:** Replace the sentence with a definition, for example: "`observed_at` and `monotonic_ns` are stamped at response completion, when the value becomes known; where the request-to-response interval expresses uncertainty, record `request_started_monotonic_ns` separately. All age and separation comparisons use the response-completion timestamp." Choose one instant rather than leaving both legal.
- **Evidence:** reasoning only; §6 Time and the canonical schema table.
- **Confidence:** high

### DEEPSEEK-4 · Define the recording epoch and its behaviour across a reconnect

- **Section:** §6 (also §8)
- **Type:** gap
- **Severity:** minor
- **Finding:** `monotonic_ns` is "monotonic acquisition time within a recording epoch" and §6 says "A reconnect or recording-epoch change invalidates prior live inputs", but a recording epoch is never defined, while the session rule says a reconnect within the grace period resumes the same session with a gap marker. If a reconnect starts a new epoch, monotonic timestamps on either side of the gap are not comparable, which breaks ordering, durations, flight-recorder windows and `derivation` input refs across the resumed session; if it does not, the "reconnect or recording-epoch change" phrasing is redundant or contradicts "within a recording epoch". Implementers must guess which.
- **Proposed change:** Define the recording epoch as the interval in which the monotonic clock is continuous (for example, process or device-boot lifetime), add an `epoch_id` to records and to `derivation` input refs, and state: a reconnect does not create a new epoch; it invalidates open live inputs and diagnostic windows and adds a gap marker, while stored ordering stays comparable. A process restart starts a new epoch; a resumed session spans epochs with a gap, and monotonic times are never compared across `epoch_id`. This does not change the provisional session rule (FB-D4).
- **Evidence:** reasoning only; §6 schema, §6 Time and Sessions, §8 windows.
- **Confidence:** high

### DEEPSEEK-5 · Add a record type for diagnostic events and anomaly windows

- **Section:** §4, §5, §6, §8 (also §10)
- **Type:** gap
- **Severity:** minor
- **Finding:** Phase 1 requires "local diagnostics" and "Diagnostic event capture with pre-event ring buffer and post-event window", and §8 keys its 30 s/60 s windows to "a detected anomaly"; §10 requires keeping observations, hypotheses and confirmed faults separate with ranked causes and uncertainty. But the only record types are `VehicleMetricSample`, `DtcRecord` and (later) `FreezeFrame`, and `TelemetryRecord` is what `TelemetrySink` and `TelemetryExporter` carry. No record identifies an anomaly or diagnosis, its rule and version, the inputs and ages used, its status, or which samples form its window, so the event recorder, the flight recorder and export have no common object and a stored hypothesis cannot be reproduced.
- **Proposed change:** Add a `DiagnosticEvent` record — event id, session id, rule id + version, status (`insufficient_data | hypothesis | confirmed`), input refs with ages and `source_address`, confidence, pre/post window sample refs or time range, and created timestamps — and include it in `TelemetryRecord`. State that flight-recorder windows are keyed to the event id and that exports include events with their window references; extend the acceptance fixture so an event survives storage and export with its rule version.
- **Evidence:** reasoning only; §4 Phase 1, §5 `TelemetryRecord`, §6 DTC/derived rules, §8, §10.
- **Confidence:** high

### DEEPSEEK-6 · Define the "engine known to be running" precondition for the derived metric

- **Section:** §6 (also §4)
- **Type:** gap
- **Severity:** minor
- **Finding:** The gauge manifold pressure rule requires "the engine is known to be running", but the spec defines no engine-running signal or threshold anywhere, and the interim session rule deliberately does not detect engine state (FB-D4), so an implementer has no rule to apply. The condition is also not obviously needed for correctness: with the engine off, manifold pressure is at ambient and the derived gauge value is ≈ 0 kPa, which is a correct reading, so an undefined precondition can only suppress valid estimates.
- **Proposed change:** Either state that the derivation requires only a `valid`, fresh MAP and barometric sample from the same `source_address` within the declared maximum separation, and delete "and the engine is known to be running"; or define the condition operationally, e.g. "the engine is running when PID `0C` (RPM) is `valid` and greater than zero for the same `source_address` within the maximum separation", and state that this is an input condition only, independent of the session-start rule. Do not leave the phrase undefined.
- **Evidence:** reasoning only; §6 derived metrics and §6 sessions. The engine-off equality is a physical inference, not a re-fetched source.
- **Confidence:** medium

### DEEPSEEK-7 · Define the payload boundary after header parsing and reassembly

- **Section:** §5 (also §6)
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 requires headers on or physical addressing so the responder is visible, and it requires multiline responses to be reassembled per responder. With headers enabled, the adapter's output begins with the responder address, and CAN replies carry ISO-TP length/sequence bytes around the service data. `Payload` carries `source` plus opaque `bytes`, but the spec never says whether `bytes` is the raw adapter line, the data after the header including framing, or only the reassembled OBD data. That decides whether "its response service byte" is `bytes[0]`, `bytes[1]` or `bytes[2]`, so the same valid reply can be accepted or rejected by the service + `0x40` rule, and `decoder_version` cannot guarantee reproducibility.
- **Proposed change:** State that after attribution is configured, the transport normalises each responder's reply into an OBD payload: move the header into `source`, strip ISO-TP length/sequence and adapter formatting, concatenate multiline frames per responder, and place the response service byte first. Define `bytes` as this normalised payload, keep the raw line separately only if diagnostics need it, and apply the service + `0x40` test to normalised byte 0.
- **Evidence:** reasoning only; §5's headers-on/physical-addressing and per-responder reassembly requirements plus the `Payload` type. The framing detail follows from the spec's own multiline premise.
- **Confidence:** high

## Top 3

1. **DEEPSEEK-2** — `ambiguous` is used as a state in three sections but has no field or enum member, so unattributed records have no legal representation.
2. **DEEPSEEK-5** — Phase 1 requires diagnostic event capture, but no diagnostic/anomaly record exists in the `TelemetryRecord` union.
3. **DEEPSEEK-1** — the §12 adapter-command allowlist is narrower than the adapter commands §4, §5 and §7 require.

Result: complete
