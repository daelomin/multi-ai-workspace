# DEEPSEEK review — round 1

Reviewing `spec.md` v0.1 (2026-10-21) independently. I read the local spec, the project README, `CONTRIBUTING.md` and `generic/REVIEW_LOOP_GUIDELINE.md`; I did not read the other round-1 review. Section numbers refer to `spec.md` v0.1. External facts were checked on 2026-10-21 and are cited per finding; everything else is reasoning against the spec text. I recorded two major and ten minor findings; none is blocking. The three inline `COMMENT — Gemini` blocks are comments rather than normative text; I do not repeat them except where a finding adds a distinct issue.

### DEEPSEEK-1 · Make read-only an enforced service allowlist

- **Section:** §12 (also §1, §5)
- **Type:** risk
- **Severity:** major
- **Finding:** §12 says "Read-only OBD commands by default; no ECU writes, actuator tests, or automatic code clearing", and §1 only forbids clearing DTCs automatically, so the qualifiers leave room for a manual clear or a debug/raw-command path while §5's `exchange(command: ByteArray)` accepts any frame. OBD service 04 clears stored DTCs and stored values and turns off the MIL, service 08 controls on-board components, and raw 29-bit UDS frames can reach write services; one such command erases diagnostic evidence and emissions readiness. "Read-only" therefore needs an enforced allowlist, not a policy sentence.
- **Proposed change:** Add to §12 (and mirror in §5): "The app MUST send only read-only service modes from an explicit allowlist — initially 01, 02, 03, 07, 09 and 0A; 05/06 only if a later requirement adds them. It MUST NOT send 04 (clear DTCs), 08 (actuator control), 2F/31/34–3E (UDS), or arbitrary raw CAN frames. Mode 22 read PIDs are allowed only from an explicit per-vehicle whitelist introduced in Phase 3." Enforce the allowlist in the framing layer before `ObdTransport.exchange`, not in the UI, and add a test that a forbidden mode is rejected. If manual DTC clearing is ever wanted, it needs a separate HUMAN decision and a dedicated tool, not this module.
- **Evidence:** Spec §1, §5, §12; Wikipedia, "OBD-II PIDs", service-mode table (Mode 04 = clear DTCs, Mode 08 = control on-board system), https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21; ELM327 datasheet p. 41 (Mode 22 physical addressing), https://www.elmelectronics.com/wp-content/uploads/2017/01/ELM327DS.pdf, checked 2026-10-21. The enforcement gap is reasoning against the spec.
- **Confidence:** high

### DEEPSEEK-2 · Attribute OBD responses and capabilities to an ECU

- **Section:** §5, §6 (also §4, §7)
- **Type:** error
- **Severity:** major
- **Finding:** A functional OBD request can be answered by several ECUs; the ELM327 datasheet shows the engine ECU (10) and transmission ECU (18) both answering `0100`, and notes that with headers off the responses are "difficult to decipher". The spec's `exchange` has no source address, `discover()` returns one `Set<MetricCapability>`, and `VehicleMetricSample` has no ECU field. Because supported-PID bitmaps and DTCs are per ECU, a union of capabilities and a merged stream cannot say which module supported a PID or produced a value, and two ECUs reporting different values for the same PID are indistinguishable.
- **Proposed change:** Introduce an `EcuAddress` and an `ObdResponse(data, source, raw, error)`; change discovery to `Map<EcuAddress, Set<MetricCapability>>`; add `ecu` to `VehicleMetricSample` and to the DTC record. During discovery set headers on (`ATH1`) or use physical addressing (`7E0..7E7`) so the source is visible, and record whether the adapter supports headers/multi-ECU at all. Define a precedence rule for duplicate metrics (e.g. engine ECU before transmission) and never average values from different ECUs. If per-ECU attribution is deliberately out of scope, say so and define a single-ECU fallback that refuses to guess when more than one ECU answers.
- **Evidence:** ELM327 datasheet (Elm Electronics, ELM327DSK), pp. 41–43: functional `7DF` vs physical `7En`, and the engine ECU 10 + transmission ECU 18 both answering `0100` with headers-off ambiguity, https://www.elmelectronics.com/wp-content/uploads/2017/01/ELM327DS.pdf, checked 2026-10-21; Wikipedia OBD-II PIDs (`7DF` broadcast, `7E8`–`7EF` replies), checked 2026-10-21; spec §5–§7. This adds source attribution to the response-wrapper issue already noted in the §5 Gemini comment.
- **Confidence:** high

### DEEPSEEK-3 · Single-flight and share the acquisition pipeline

- **Section:** §5 (also §3, §7)
- **Type:** risk
- **Severity:** minor
- **Finding:** The ELM327 is a single request/response text channel ending in a prompt, but the spec exposes `exchange` and defines several consumers (discovery, live UI, recorder, diagnostics) without stating that one component owns the adapter and serialises requests. A cold `TelemetrySource.samples()` flow can be collected more than once, and a discovery or DTC read can overlap a poll. The next response can then be consumed by the wrong caller, so a sample can be attributed to the wrong PID or fail to parse.
- **Proposed change:** State a single-writer rule in §5: one `AcquisitionEngine`/`ObdSession` owns the `ObdTransport`; every request goes through a single-flight queue or `Mutex`; no other component calls `exchange`. `TelemetrySource.samples()` must return a hot, shared flow (`shareIn` with replay) fed by that engine, and starting a second collector must not start a second poll loop. Add a concurrency test that runs discovery, polling and a DTC read together and asserts every response is paired with its request.
- **Evidence:** ELM327 datasheet p. 50 (prompt/interrupt behaviour) and p. 53 (request/response timing, 200 ms default wait), checked 2026-10-21; spec §3 and §5. The concurrency hazard is reasoning from the single-channel protocol.
- **Confidence:** high

### DEEPSEEK-4 · Give DTCs and freeze frames a record type and an export path

- **Section:** §4, §5, §6, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** Phase 1 requires Mode 03/07/0A DTC reads and §14 requires reading available DTCs, but the only sink/exporter contracts carry `List<VehicleMetricSample>` and §6 has no DTC entity. A DTC is not a time-series sample: it needs code, status, ECU, first/last seen, occurrence count, MIL/readiness context and the freeze frame that explains when it set. Without a record type, DTCs end up in a categorical metric or an ad-hoc table the exporter cannot carry, so "export a recording" omits the most useful diagnostic data; Mode 02 and Mode 09 are also absent.
- **Proposed change:** Add a `DtcRecord` (code, status `stored|pending|permanent`, ecu, first_seen_at, last_seen_at, occurrence_count, mil_status, readiness, raw_bytes), a `FreezeFrame` record (trigger DTC, Mode 02 PID values, captured_at) and a versioned export manifest; extend `TelemetrySink`/`TelemetryExporter` with DTC/freeze-frame operations or replace the metric-only batch with a `TelemetryRecord` sealed type. Add Mode 02 and Mode 09 (VIN/CVN only with consent) to the Phase 1 read-only set, or state explicitly that they are deferred. Define redaction of VIN and adapter identifiers in debug exports.
- **Evidence:** Spec §4, §5, §6, §14; Wikipedia OBD-II PIDs (Modes 02, 03, 07, 09, 0A), checked 2026-10-21; reasoning for the contract gap.
- **Confidence:** high

### DEEPSEEK-5 · Define session and trip boundaries

- **Section:** §6 (also §4, §8, §14)
- **Type:** gap
- **Severity:** minor
- **Finding:** Every sample requires a `session_id`, and Phase 1 acceptance requires recording "a trip", but the spec never defines when a session starts or ends. OBD gives no reliable ignition signal: the adapter may be powered with the ignition off, RPM 0 means idle or engine off, and the link can drop when the phone leaves the car. Implementers will segment trips differently, which changes trip history, event windows, upload batches and deduplication, and a DTC-only read with the engine off has no defined session.
- **Proposed change:** Add session rules to §6: start on connection plus engine-running evidence (e.g. RPM > 0 for N consecutive samples, or PID 0101 engine status), end after K seconds below the RPM threshold or on an ignition-off indication, and close after grace period T on disconnect; a reconnect within T resumes the same session with a `gap` marker, otherwise it starts a new one. Store `started_at`, `ended_at`, `end_reason`, `gap_count`; allow manual split/merge; cap a session at a maximum duration. State that a DTC read with the engine off is a `diagnostic_read`, not a drive session.
- **Evidence:** Spec §4, §6, §8, §14; reasoning only for the OBD ignition/connection ambiguity.
- **Confidence:** high

### DEEPSEEK-6 · Define value nullability, quality states and staleness

- **Section:** §2.3, §6
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §2.3 says unsupported, unavailable and stale metrics are marked explicitly, but the §6 `quality` enum is `valid, estimated, stale, unavailable, error` and has no `unsupported`. `value` has no nullability rule although `unavailable` and `error` samples have no numeric value, `unit` has no rule for categorical values, and `stale` has no age threshold. Two implementations can represent the same missing reading differently, and a database constraint on `value` will either reject the required quality states or store a fake zero.
- **Proposed change:** Define `MetricQuality` as `valid | estimated | stale | unavailable | error | unsupported` (or remove `unsupported` from §2.3 and keep it only in `MetricCapability`); make `value` explicitly nullable or a sealed type (`Numeric(value, unit)`, `Categorical(code)`, `NoValue(reason)`); make `unit` nullable for categorical values; add `stale_after_ms` per metric or metric class with the rule "stale when now − observed_at > stale_after_ms". State that an `unavailable` sample carries no value, not zero, and that `observed_at` is the time of the failed acquisition. Normalise the enum spelling to lower case.
- **Evidence:** Spec §2.3 and §6; reasoning only.
- **Confidence:** high

### DEEPSEEK-7 · Track raw vs derived values, confidence and schema version

- **Section:** §6 (also §4, §10)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §6 says "Track raw versus derived metrics, confidence, and source provenance", and §10 requires observations, hypotheses and confirmed faults to stay separate, but the schema table has no origin flag, no derivation/formula identifier and no confidence. `decoder_version` covers raw decoding only; it cannot identify a boost estimate or a fused value. A derived `engine.boost` can therefore be plotted or diagnosed as if it were a sensor reading, and the derivation cannot be reproduced; for the Duster pilot, gauge boost also changes sign (vacuum below barometric pressure) and is not defined.
- **Proposed change:** Add `origin` (`raw | derived`), `derivation_id`/`formula_version`, `input_refs`, `confidence` (0–1 or an enum) and a record-level `schema_version`; keep `decoder_version` for raw parsing. Define `engine.boost_gauge = max(0, MAP − barometric)` and `engine.vacuum = max(0, barometric − MAP)` (or an explicit signed field), require a fresh barometric reading and engine-running state, and mark the result `quality=estimated` with the formula version.
- **Evidence:** Spec §4, §6, §10; boost/vacuum sign is reasoning only; no external source re-fetched for the naming.
- **Confidence:** high

### DEEPSEEK-8 · Make the flight-recorder resolution consistent with adaptive sampling

- **Section:** §8 (also §7)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §8 says the flight recorder keeps "30 seconds before and 60 seconds after" an anomaly and retains "high-resolution data locally", while §7 allows acquisition to be stopped or throttled under power/thermal conditions and §8 downsamples on weak links. The pre-event buffer can only contain samples that were acquired; if acquisition was throttled, the "high-resolution" pre-event data does not exist. The spec does not define the buffer's rate, the anomaly-relevant metric set, or what happens to a window that crosses a gap.
- **Proposed change:** State that the ring buffer stores every locally accepted sample, independent of upload policy; define a minimum always-on acquisition floor for anomaly-relevant metrics (e.g. RPM, MAP, throttle and fuel trims at ≥1 Hz) and make throttling below that floor a recorded quality/gap event, not silent downsampling. Define "high-resolution" as the local acquisition rate, not an upload rate, and mark windows that contain a gap so diagnostics do not treat them as continuous.
- **Evidence:** Spec §7 and §8; reasoning only.
- **Confidence:** high

### DEEPSEEK-9 · Define capability discovery and negative-result caching

- **Section:** §5, §7
- **Type:** gap
- **Severity:** minor
- **Finding:** §7 says "Poll only discovered supported PIDs", but the spec does not define how support is discovered or cached. Supported-PID bitmaps are paged (`0100` → `0120` → `0140` …), and `NO DATA` can mean unsupported, a timeout, the wrong protocol, or a dropped response. Treating any of these as permanently unsupported hides valid metrics, while treating all as supported wastes polling time, and the spec does not say when discovery is redone.
- **Proposed change:** Define discovery in §7: read `0100`, follow only advertised pages, and classify each PID as `supported | unsupported | unknown | adapter_error`; require a repeated probe before persisting `unsupported`; cache per adapter ID + firmware + protocol + ECU and invalidate on adapter change, protocol change, battery disconnect, or N consecutive `NO DATA` replies. Show `unknown` in the UI rather than "not supported".
- **Evidence:** Wikipedia OBD-II PIDs (paged supported-PID bitmaps), checked 2026-10-21; ELM327 datasheet p. 53 (`NO DATA`, 200 ms default timeout), checked 2026-10-21; spec §5 and §7.
- **Confidence:** high

### DEEPSEEK-10 · Add a monotonic timestamp for ordering and event windows

- **Section:** §6 (also §8)
- **Type:** risk
- **Severity:** minor
- **Finding:** `observed_at` is defined as the UTC timestamp of acquisition and `received_at` is optional; there is no monotonic timestamp. Phone wall clocks jump on NTP correction, timezone change or manual change, and OBD responses arrive 4–200 ms after the request. Event windows, sample ordering, deduplication and cross-source freshness rules that use wall-clock time can therefore reorder or misalign data, especially around the pre/post-event recorder; the server also cannot distinguish device clock error from real time when it receives a batch.
- **Proposed change:** Add `monotonic_ns` (Android `elapsedRealtimeNanos`) alongside `observed_at`, plus `request_sent_at`/`response_received_at` where the distinction matters; state that ordering and event windows use monotonic time while wall clock is for display and cross-device correlation. Record the wall-clock↔monotonic offset on change and a clock-adjustment event. In Phase 2, record server `received_at` and use it for ingestion ordering, not the device clock.
- **Evidence:** Spec §6 and §8; reasoning only.
- **Confidence:** high

### DEEPSEEK-11 · Define what happens to acquisition when offline entitlement expires

- **Section:** §11 (also §4, §12)
- **Type:** question
- **Severity:** minor
- **Finding:** §11 says a cached entitlement permits "a defined offline grace period" but does not define it or say what happens to acquisition when it expires while the phone is offline. §4 says local functionality should remain usable offline with an appropriate cached entitlement policy, and §11 recommends that an expired subscription still allows export/delete. Without an explicit invariant, an implementation could stop the recorder at grace expiry and lose a drive the user has already paid for, or keep premium acquisition running forever offline; both are product/commercial choices.
- **Proposed change:** Ask HUMAN to choose and then state the invariant: either (a) acquisition, local storage and export/delete are never gated by entitlement expiry, and only premium analysis/UI is gated, or (b) acquisition stops after grace, with a defined notice and retention rule. In both cases define the grace duration, the clock used to measure it (monotonic vs server time), and how the signed cached entitlement is refreshed. This is a product decision; I am not deciding it.
- **Evidence:** Spec §4, §11, §12; reasoning only.
- **Confidence:** high

### DEEPSEEK-12 · Quantify the Phase 1 signal-rate acceptance criterion

- **Section:** §14 (also §7)
- **Type:** suggestion
- **Severity:** minor
- **Finding:** The Phase 1 acceptance criterion "stream and display at least five supported live signals" has no rate, duration or drop tolerance. An ELM327 with the default 200 ms response timeout sustains about 4 queries per second; the datasheet shows that 100 ms gives about 7 per second and an expected-response count gives 10–12 per second. Five signals at 1 Hz therefore needs at least 5 successful queries per second and tuning the spec does not require, so two implementations can both claim acceptance while one is far too slow for live charts or the event recorder.
- **Proposed change:** Add measurable acceptance: e.g. five supported signals at ≥1 Hz for 10 minutes with ≥95% of expected samples and reconnection within 10 seconds; record the achieved per-PID rate and drop count in the benchmark. State that the default ELM327 timeout (~4 queries/s) is insufficient for this target and that `AT ST`/expected-response tuning is part of adapter validation. Keep the Duster 2018 1.2 TCe 125 as the reference vehicle.
- **Evidence:** ELM327 datasheet p. 53 (200 ms default timeout → ~4 readings/s; 100 ms → ~7/s; expected-response count → 10–12/s), checked 2026-10-21; spec §7 and §14.
- **Confidence:** high

## Top 3

1. **DEEPSEEK-1 — enforce read-only.** The module's safety claim needs a runtime allowlist; "by default" and "automatic" leave Mode 04 and raw commands reachable.
2. **DEEPSEEK-2 — attribute responses to ECUs.** Without an ECU address in the transport, the capability set and the sample schema, multi-ECU vehicles produce silently ambiguous data.
3. **DEEPSEEK-5 — define session boundaries.** `session_id` is in every sample and "record a trip" is the Phase 1 acceptance, but no start/end/resume rule exists.

Result: complete
