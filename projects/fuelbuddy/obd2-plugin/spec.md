# FuelBuddy — OBD-II Telemetry Module Specification

**Version:** v0.3  
**Status:** Draft / proposed architecture  
**Date:** 2026-10-21  
**Scope:** Optional paid OBD-II module, offline-first Phase 1, cloud observability Phase 2

Items marked *(provisional — FB-Dn)* depend on an open HUMAN decision listed in `reviews/round-2/CONSOLIDATION.md` (carried forward from round 1); the text shows the interim default and is not a decision.

## 1. Objectives

Build a modular vehicle telemetry capability for FuelBuddy that:
- Connects an Android phone to a compatible OBD-II adapter and discovers available vehicle data.
- Collects live signals, diagnostic trouble codes (DTCs), and supported vehicle-specific parameters.
- Normalizes readings into FuelBuddy's vehicle model without assuming every car supports every signal.
- Provides useful local diagnostics and historical dashboards without an internet connection.
- Later relays selected telemetry to a backend for fleet-scale analysis, Grafana dashboards, and advanced charging/vehicle diagnostics.
- Enables or disables premium OBD features through entitlements, without coupling telemetry storage to billing.

**Non-goals (initially):** ECU programming, clearing DTCs (automatic or user-initiated; see FB-D3), commanding actuators or on-board tests, writing vehicle parameters, guaranteed access to proprietary OEM data, and continuous cloud streaming in Phase 1.

## 2. Key design principles

1. **Offline first:** acquisition, storage, visualization, and initial alerts work locally.
2. **Modular:** adapter transport, protocol decoding, vehicle model, storage, diagnostics, and cloud export are independently replaceable.
3. **Capability driven:** interrogate supported PIDs per responding ECU and mark unsupported, unavailable, or stale metrics explicitly.
4. **Safe and read-only:** no control commands or ECU modifications in the initial product; enforced by a service allowlist (§12), not by policy alone.
5. **Adaptive and cost-aware:** sampling and upload rates depend on ECU/adapter throughput, battery, thermal state, network quality, and user policy.
6. **Privacy by design:** user consent for cloud telemetry, minimized identifiers, retention controls, and encrypted transport/storage where appropriate.
7. **Source agnostic:** OBD, OEM APIs, EV battery sources, and Android integrations feed a common metric model.

## 3. Proposed architecture

```text
             OBD-II vehicle port
                     |
          ELM327/STN-compatible adapter
                     |
         Bluetooth Classic / BLE / Wi-Fi
                     |
+-------------------- Android FuelBuddy app --------------------+
| Connection Manager -> Protocol/PID Discovery -> Decoder       |
|                                    |                          |
|                           Metric Normalizer                  |
|                                    |                          |
|                           Telemetry Event Bus                |
|                          /         |          \               |
|                  Local Store   Live UI     Local Diagnostics   |
|                  (Room/DB)    & Charts    & Event Recorder    |
|                          \         |          /               |
|                         Export/Sync Interface                 |
|                              [Phase 2]                       |
+----------------------------------|---------------------------+
                                   |
                         OTLP / HTTPS + batching
                                   |
                       Authenticated ingestion API
                                   |
                       OpenTelemetry Collector
                                   |
                    Metrics / Events / Time Series
                                   |
                     Prometheus-compatible store
                                   |
                         Grafana / Analytics
```

Prometheus generally scrapes stable endpoints; mobile phones should **push** through a secure ingestion path rather than depend on inbound scraping. OpenTelemetry is a possible instrumentation/export format, not a requirement for the local database.

Phase 2 credentials: use short-lived tokens with refresh, stored with Android platform facilities (Keystore-backed storage); a stolen access token must expire and be revocable server-side.

## 4. Phased delivery

### Phase 1 — Local-only MVP

- Android integration (Kotlin if confirmed; verify actual application stack before implementation).
- Bluetooth Classic transport first, plus BLE/Wi-Fi adapter support through interfaces as needed.
- Adapter identification, connection/reconnection, supported PID discovery per responding ECU, error handling.
- Standard SAE J1979/OBD-II read-only Mode 01 live signals and Mode 03/07/0A DTC reads where supported. Modes 02 (freeze frame) and 09 (vehicle information, incl. VIN) are not in Phase 1 *(provisional — FB-D2)*.
- Recording runs in a foreground service started while the app is visible, using the connected-device service type and permission where the platform requires one (Android 14+: `connectedDevice`), so the adapter session survives screen-off. The driving UI stays passive. The service owns a connection watchdog and automatic reconnection with backoff (§7). Applies if the stack is native Android; adapt to the actual stack otherwise.
- Local timestamped storage (e.g., Room/SQLite), local charts, trip/session history, basic diagnostic rules, under a bounded storage budget (§9).
- A user-controlled premium feature entitlement; local functionality should remain usable offline with an appropriate cached entitlement policy (FB-D1).
- Diagnostic event capture with pre-event ring buffer and post-event window.
- Export recordings, including DTC records, to a portable versioned format for debugging, with user approval.
- No external telemetry server required.

**Initial metrics to probe:** RPM, vehicle speed, engine coolant temperature, calculated engine load, manifold absolute pressure (MAP), intake air temperature, throttle position, short/long-term fuel trims, and control-module voltage where supported. Optional: mass airflow, fuel pressure, commanded equivalence ratio, and oxygen sensor data. Not all vehicles expose all metrics.

**Duster 2018 1.2 TCe 125 pilot:** verify PID support, record MAP/barometric pressure where available, RPM, load, throttle, and fuel trims; estimate gauge manifold pressure only under the derivation rule in §6. Record transient loss-of-power episodes for later investigation; do not equate a boost anomaly with a confirmed turbo failure.

### Phase 2 — Cloud telemetry and observability

- Implement an exporter interface and secure backend ingestion endpoint.
- Prefer OTLP over HTTPS with protobuf and batching; optionally support JSON for debugging/interoperability.
- Integrate OpenTelemetry Collector and Prometheus-compatible metric storage; Grafana for dashboards.
- Use a separate event/log or time-series store for high-cardinality per-vehicle raw samples; do not treat Prometheus as the sole archive for every raw sensor reading. The product for that store is chosen after the benchmark (§15 items 6–7).
- Adaptive synchronization, compression, backpressure, retry with exponential backoff, and deduplication.
- User-configurable upload consent, retention, and delete/export controls; consent and deletion apply to queued data (§11).
- Remote analytics and charging-diagnostics enrichment; advanced alert delivery is optional and deferred.

### Phase 3 — OEM/EV expansion (future)

- Manufacturer-specific PIDs and decoders (including Mode 22 reads from an explicit per-vehicle whitelist), subject to validation, permissions, and licensing.
- EV BMS metrics where exposed (SOC, SOH, pack voltage/current, battery temperature, charge power).
- Vehicle/charger compatibility analytics, charging-session correlation, anomaly models, and optional fleet insights.
- OEM APIs as additional sources with explicit provenance and freshness tracking.

## 5. Module boundaries / Kotlin interfaces (illustrative)

```kotlin
interface ObdTransport {
    suspend fun connect(): ConnectionInfo
    suspend fun exchange(request: ObdRequest): ObdExchange
    suspend fun disconnect()
}

data class ObdExchange(
    val request: ObdRequest,
    val outcomes: List<ObdResponse>,   // one or more per responder
    val completion: ExchangeCompletion // Complete | DeadlineExpired | Disconnected
)

// Per-responder outcome
sealed interface ObdResponse {
    data class Payload(val source: EcuAddress?, val bytes: ByteArray) : ObdResponse // bytes: normalised OBD payload, service byte at index 0
    data class NoData(val request: ObdRequest) : ObdResponse
    data class Negative(val source: EcuAddress, val code: Int) : ObdResponse
    data class Timeout(val request: ObdRequest) : ObdResponse
    data class AdapterError(val word: String) : ObdResponse
    object Disconnected : ObdResponse
}

interface VehicleCapabilityDiscovery {
    suspend fun discover(): Map<EcuAddress, Set<MetricCapability>>
}

interface TelemetrySource {
    fun samples(): kotlinx.coroutines.flow.Flow<VehicleMetricSample>
}

interface TelemetrySink {
    suspend fun write(batch: List<TelemetryRecord>)
}

interface TelemetryExporter {
    suspend fun export(batch: List<TelemetryRecord>): ExportResult
}

// TelemetryRecord = VehicleMetricSample | DtcRecord | DiagnosticEvent | (later) FreezeFrame
```

Separate adapter/transport-specific framing from ELM327 AT commands, OBD request scheduling, PID decoding, and storage. Use Kotlin coroutines/Flow where the app is native Kotlin; adapt this design to the actual stack otherwise.

**Single owner, one exchange at a time.** One acquisition component owns the `ObdTransport`; every request (discovery, polling, DTC reads) goes through its single-flight queue and no other component calls `exchange`. An ELM327-class adapter is one text channel: the next command is sent only after the `>` prompt, and a character sent earlier can abort the command in progress. `samples()` is a shared stream fed by that component; a second collector must not start a second poll loop. Test: discovery, polling and a DTC read run together and each response is paired with its request.

**One exchange, all responders.** One exchange collects all responder outcomes until the adapter prompt or a bounded deadline; a failure or negative response from one responder does not discard another responder's valid payload. An incomplete exchange keeps the completed outcomes together with its completion status. The single-flight queue advances only once the channel is idle or has been recovered.

**Typed results, not raw bytes.** Adapter words (`NO DATA`, `?`, `UNABLE TO CONNECT`, `CAN ERROR`, `DATA ERROR`, `BUFFER FULL`, `BUS BUSY`, `BUS ERROR`, `STOPPED`, `LV RESET`), a negative response (service byte `7F`) and timeouts are mapped to the non-payload `ObdResponse` cases and never reach the PID decoder. Progress lines (`SEARCHING...`, `BUS INIT: ...` and a following `OK`) are ignored and the exchange keeps reading until the prompt; a progress line never discards a later payload. Any other non-hex line is an `AdapterError`. A `Payload` may be decoded as `valid` only if its response service byte equals the request service + `0x40`.

**Negative and pending responses.** A normalised response `7F <requested service> <code>` is `Negative` when the code is anything other than `0x78`; the second byte must equal the service that was requested and `Negative.code` is the third byte. Code `0x78` (response pending) does not finish the exchange and does not become a sample: keep waiting for a later positive, negative or timeout from that same responder, up to one bounded wait, extended once if that responder sends `0x78` again. A positive payload from one responder does not cancel a pending wait on another.

**Payload boundary.** `Payload.bytes` is the normalised OBD payload of one responder, response service byte at index 0. The transport moves the responder address into `source`, removes ISO-TP length/sequence framing and the PCI byte (which remains in the adapter text when headers are on, even with CAN auto-formatting), and concatenates multiline frames for that responder before any check. The `+ 0x40` and `7F` tests both use that normalised byte 0. Raw adapter lines are not stored in `bytes`; keep them separately only if diagnostics need them.

**PID identity.** For service `01` a payload is `valid` only if the service byte matches and each value is taken from a PID that the request asked for, identified by the echoed PID byte, never by position in the request (replies need not follow request order). A returned PID that was not requested is `error` and is not decoded. A request may carry several supported PIDs; each echoed PID becomes its own sample. Bank 1 and bank 2 fuel trims use separate `metric_key`s (`06`/`08` short-term, `07`/`09` long-term) and are never averaged.

**Expected-response count.** An adapter expected-response count is a maximum, not a hint: a count below the number of ECUs that actually answer makes the adapter return early and drops the later responders. Measure how many responses arrive for that request and set the count to that number; until measured, wait for the adapter prompt with the default timeout and send no count. A shortened response timeout stays at least as long as the slowest responder already observed for that request.

**ECU identity.** A functional request (CAN `7DF`) may be answered by several ECUs (`7E8`–`7EF`), possibly with different supported-PID bitmaps and interleaved multiline frames. Configure the adapter so the responder is visible (headers on, or physical addressing). Reassemble multiline responses per responder. Phase 1 records the protocol the adapter actually negotiated. On 11-bit ISO 15765-4 the functional request is `7DF` and responders are `7E8`–`7EF`; on 29-bit ISO 15765-4 the responder address is the 29-bit id the adapter reports (not a value in `7E8`–`7EF`); on non-CAN protocols it is the source byte of the header. An address that does not match the negotiated protocol is `ambiguous`. If Phase 1 is later limited to 11-bit CAN, other negotiated protocols are refused at connect rather than parsed as `7E8`. Capabilities, samples and DTC records carry the responder address (`EcuAddress`, scoped to the vehicle and connection protocol) when attribution succeeds. Different responders are never merged implicitly and never averaged. The ECU used for each canonical metric comes from an explicit validated mapping in the vehicle profile; other responders are kept with their provenance. If the responder cannot be established the result is `ambiguous` (§6) and is excluded from ECU-specific diagnostics (§10).

## 6. Canonical vehicle metric schema

Suggested fields:

| Field | Purpose |
|---|---|
| `schema_version` | Record schema version (record-level) |
| `vehicle_id` | Pseudonymous FuelBuddy vehicle identifier |
| `session_id` | Recording session identifier (rules below) |
| `metric_key` | Stable name, e.g. `engine.rpm` |
| `value` | Typed numeric or categorical reading; null when no reading exists |
| `unit` | Canonical unit, e.g. `rpm`, `km/h`, `kPa`, `degC`; null for categorical values |
| `observed_at` | UTC time of acquisition (display, export, cross-device correlation) |
| `monotonic_ns` | Monotonic acquisition time within a recording epoch (ordering, durations, recorder windows) |
| `epoch_id` | Recording epoch of `monotonic_ns` (see Time); monotonic values are never compared across epochs |
| `received_at` | Optional processing timestamp (server-side in Phase 2) |
| `source` | `obd2`, `oem_api`, `ev_bms`, etc. |
| `source_address` | Responding ECU address (`EcuAddress`); required for `obd2` unless `attribution` is `ambiguous`, then null |
| `attribution` | `attributed` or `ambiguous` (samples and `DtcRecord`) |
| `protocol` | OBD mode/PID or OEM protocol identifier |
| `quality` | `valid`, `estimated`, `stale`, `unavailable`, `unsupported`, `error`, `ambiguous` |
| `stale_after_ms` | Per-metric age limit; a sample is stale when its monotonic age exceeds it |
| `sample_interval_ms` | Effective acquisition interval |
| `origin` | `raw` or `derived` |
| `derivation` | For derived samples: derivation id/formula version, input refs (metric key, `source_address`, `monotonic_ns`), confidence |
| `adapter_id` | Optional pseudonymous adapter identifier |
| `decoder_version` | Reproducibility and compatibility (raw decoding) |

**Quality and values.** `unavailable`, `unsupported` and `error` samples carry a null `value` (never zero). A `stale` sample keeps its last value but is not used for diagnosis. Diagnoses use only `valid` inputs (and `estimated` where a rule says so). An `ambiguous` sample (responder not established, null `source_address`) keeps its decoded value, is never `valid`, and is excluded from ECU-specific diagnostics and from any merging or averaging.

**Time.** Ordering, durations and recorder windows use `monotonic_ns`; the wall clock is for display and export. `observed_at` and `monotonic_ns` are stamped at response completion, when the value becomes known; where the request-to-response interval expresses uncertainty, record `request_started_monotonic_ns` separately. All age and separation comparisons use the response-completion timestamp. A recording epoch is the interval in which the monotonic clock is continuous (process or device-boot lifetime); a process restart starts a new epoch, and records and `derivation` input refs carry `epoch_id`. A reconnect does not start a new epoch: it invalidates open live inputs and diagnostic windows and adds a gap marker, while stored ordering stays comparable. A resumed session may span epochs with a gap. Test a backwards UTC clock change.

**DTCs are records, not samples.** `DtcRecord`: code, service (`03` stored, `07` pending, `0A` permanent; the three stay separate), `source_address`, `attribution`, first/last seen, occurrence count, MIL status, raw bytes. A DTC with no responder address is stored with `attribution=ambiguous` and a null `source_address`, and is excluded from diagnostic ranking. Each DTC is two bytes decoded to the five-character form: bits A7–A6 of the first byte are the category (00 P, 01 C, 10 B, 11 U) and the remaining 14 bits are the four hex digits. `0000` padding pairs in a response are not records. `mil_on` is copied from the same responder's Mode `01` PID `01` bit A7, not from the service `03` payload. `occurrence_count` is how many recordings of this vehicle and responder observed the code; it is not read from the ECU, and PID `01` bits A6–A0 (the module's stored-code count) are not stored as it.

**Diagnostic events.** `DiagnosticEvent`: event id, session id, rule id and version, status (`insufficient_data | hypothesis | confirmed`), input refs with ages and `source_address`, confidence, pre/post window range or sample refs, created timestamps. Flight-recorder windows (§8) are keyed to the event id, and exports include events with their window references. Freeze frames (Mode 02) are outside Phase 1 *(provisional — FB-D2)*; if added they name Mode 02 and link to the triggering DTC. Exports carry a versioned manifest and redact VIN and adapter identifiers unless the user chooses otherwise.

**Derived metrics.** Derived samples are marked `origin=derived` with the formula version and inputs. Gauge manifold pressure = PID `0B` (MAP) − PID `33` (barometric), both kPa, only when both inputs are `valid`, from the same `source_address`, and within the declared maximum time separation (no engine-state condition: with the engine off, MAP equals ambient and the result is a correct reading); otherwise the derived sample is `unavailable` with a null value. The result is signed (negative = vacuum). It is intake-manifold gauge pressure, not turbocharger-outlet pressure, and not a confirmed fault. If PID `33` is not supported, no estimate is produced and no constant is substituted.

**Sessions.** A session is a recording of drive data between a start and an end, with `started_at`, `ended_at`, `end_reason` and gap markers. A DTC-only read with the engine off is a `diagnostic_read`, not a drive session. Interim Phase 1 rule *(provisional — FB-D4)*: a session starts when the user starts a recording on a connected adapter and ends when the user stops it, the adapter disconnects beyond the reconnect grace period, or the recording service stops; a reconnect within the grace period resumes the same session with a gap marker. Charging sessions are a Phase 3 concern.

Maintain a separate **vehicle specification/profile** (make/model/year/engine, supported connectors, known issues, canonical-metric-to-ECU mapping) from **observed telemetry** and **derived diagnostics**.

## 7. Acquisition and throughput

- Poll only discovered supported PIDs; do not assume all can be sampled at 1 Hz simultaneously.
- **Discovery:** read Mode 01 PID `00` and follow the bitmap pages (`20`, `40`, …) only while the next-range bit is set, per responding ECU. Classify each PID `supported | unsupported | unknown | adapter_error`; a set bit means supported for that ECU. Show `unknown` in the UI rather than "not supported".
- A single `NO DATA`, timeout or `7F` sets that sample's quality to `unavailable` or `error` and leaves the capability record unchanged for the session. Re-run discovery on adapter change, protocol change, reconnect after a vehicle power cycle, or a configurable number of consecutive misses; cache per `vehicle_id` + adapter + firmware + protocol + ECU, and re-run discovery when the selected vehicle changes. Cached capabilities are hints until validated for the current vehicle connection; if the connection cannot be reliably associated with the cached vehicle, discover anew rather than reuse the cache as authoritative.
- Schedule fast-changing metrics (RPM, MAP, throttle) more frequently than temperatures or static status.
- Measure actual adapter/ECU round-trip latency and adjust polling to avoid overload. With the ELM327 default 200 ms response wait, about 4 queries/s is the ceiling; shorter timeouts and expected-response counts are part of adapter validation, under the count and timeout rules in §5.
- Use bounded queues and record dropped sample counts; never let network upload block the OBD polling loop.
- Stop or throttle acquisition when disconnected or under restrictive power/thermal conditions; throttling below the flight-recorder floor (§8) is recorded as a gap.
- **Connection resilience (Phase 1, mandatory):** Bluetooth Classic (RFCOMM) links can drop or stall on lifecycle changes. Provide a connection watchdog, a lifecycle-aware foreground service (§4) and automatic reconnection with backoff, so a drop never freezes the UI or silently loses data.
- Treat generic low-cost ELM327 clones as variable quality; prefer well-tested adapters for validation.

## 8. Adaptive sync policy (Phase 2)

| Condition | Suggested upload behavior |
|---|---|
| Good Wi-Fi / 5G | Batched near-real-time updates, approximately every 1–5 seconds if permitted |
| Stable 4G | Batches every 10–30 seconds |
| Weak / metered connection | Longer batches, downsampled summaries, e.g. 60 seconds |
| Offline | Durable local queue; sync later under limits |
| Diagnostic anomaly | Preserve higher-resolution pre/post-event samples locally; upload when policy permits |

These are **starting policies, not guarantees**: effective rate depends on OBD throughput, bandwidth, power, user settings, and backend cost. Network type alone is not a reliable indicator of available bandwidth; use observed performance and metering status.

**Flight recorder:** configurable ring buffer, initially 30 seconds before and 60 seconds after a detected anomaly, retaining high-resolution data locally. The buffer stores every locally accepted sample, independent of upload policy; "high-resolution" means the local acquisition rate. Anomaly-relevant metrics (RPM, MAP, throttle, fuel trims) have a minimum local acquisition floor *(provisional rate, e.g. ≥1 Hz — FB-D6)*; windows containing a gap are marked so diagnostics do not treat them as continuous. Each window is keyed to its `DiagnosticEvent` id (§6). Use bounded storage and avoid automatic upload without consent.

## 9. Payload and storage budgeting

Do not assume telemetry is below 1 MB/hour. For example, **30 metrics each sampled once per second** produce 108,000 samples/hour. At 20–100 bytes/sample after efficient encoding/packing, that is approximately **2.2–10.8 MB/hour** before transport overhead; JSON with repeated field names may be considerably larger. Actual figures must be benchmarked.

Plan a simulator/benchmark with configurable metric count, rates, event frequency, format (JSON, protobuf/OTLP), batching, compression, and offline retention. Report bytes/hour, phone storage/day, mobile data/month, backend ingestion rate, and estimated cost per active vehicle. Test gzip/zstd where supported, while accounting for CPU/battery impact.

**Local storage budget (Phase 1).** A configurable total budget covers normal recordings, event recordings and database overhead, with a reserved free-space threshold. At the limit the configured retention policy applies; where no eviction policy is authorized, persistence pauses and the recording gap is visibly reported *(provisional — FB-D5)*. Storage failures must not crash acquisition or build an unbounded in-memory backlog; lost-sample counts are tracked. Test budget exhaustion and write failure. Numeric defaults remain subject to §15 item 4.

## 10. Diagnostics and integration with FuelBuddy

- Map OBD DTCs, vehicle model/year/engine, and observed signals into FuelBuddy's existing diagnostic reasoning pipeline, keeping each DTC's service and responding ECU.
- Preserve separation between **observations**, **hypotheses**, and **confirmed faults**.
- Each diagnostic declares its required inputs, maximum input age and maximum time separation between inputs. Missing, stale, ambiguous or excessively separated inputs yield an insufficient-data status, not a fault hypothesis.
- Rank possible causes of charging/engine anomalies; include uncertainty and recommended checks.
- Detect conditions such as sustained underboost only when sufficient data exists; avoid false diagnoses from MAP alone.
- Expose standardized metrics to the existing car profile and future charging calculator without making OBD mandatory.
- Support multiple data sources with conflict resolution and priority/freshness rules.

## 11. Entitlements and commercial module

- OBD capability is optional and may be a paid feature.
- Server validates purchase/entitlement when connected; signed or otherwise tamper-resistant cached entitlement permits a defined offline grace period. Its duration, the clock that measures it, and whether acquisition (versus premium analysis/UI) stops at expiry are open *(FB-D1)*; the spec does not set them.
- Gate premium UI/export/analysis at the feature layer; keep the canonical telemetry schema independent of subscription logic.
- Avoid collecting telemetry before consent or when a user has disabled the module.
- Define what happens to existing locally stored data if the subscription expires (recommended: user can still export/delete their data).
- **Consent and deletion reach the queues.** Check current cloud consent and account/vehicle ownership when dispatching every batch, including retries. Revoking upload consent stops new dispatches, cancels pending retries, attempts to cancel in-flight transfers and invalidates matching upload-queue entries; retained local recordings remain subject to the user's local policy. Disabling the module also stops acquisition without implicitly deleting retained recordings. An explicit telemetry-deletion request removes the requested records from local storage, the in-memory ring and pending upload copies, and prevents retries from recreating them. Already accepted uploads require the cloud deletion flow, which must be disclosed. A later opt-in states explicitly whether historical local recordings are eligible for upload. Test revoke-while-offline then reconnect (local recordings stay exportable and no revoked batch is dispatched), and, separately, deletion with a pending retry.

## 12. Security, privacy, and safety

- **Read-only is enforced.** The framing layer, before `ObdTransport.exchange`, sends only an explicit allowlist: OBD services `01`, `03`, `07`, `0A` (plus `02`/`09` only if FB-D2 adds them) and a fixed, reviewed set of adapter-local commands: adapter identification/version query, echo and line-ending configuration, protocol identification and try-protocol (`AT TP`), response headers on, CAN header and receive-address filter (for physical addressing), and response timeout and expected-response count. Adapter commands that write adapter EEPROM or programmable parameters (including set-protocol `AT SP`), enter an unsolicited monitor mode, or replace the wakeup/keepalive message are outside the set; the app sends no wakeup-message command and defines no periodic message (the chip's own default ISO 9141/14230 keepalive may occur, its payload is not replaced). No adapter command may carry a vehicle service byte outside the OBD allowlist. Anything else is dropped and logged as an error, never passed to the adapter. In particular service `04` (clear DTCs and stored data, MIL off), service `08` (control of on-board components), UDS write/routine services and arbitrary raw CAN frames are rejected, from every caller including debug tools and user controls. Test that a forbidden service is rejected and that every allowed adapter command is in the set. Manual DTC clearing is not part of this module (FB-D3).
- Pair only with a user-approved adapter and protect credentials/keys using Android platform facilities.
- TLS and authenticated ingestion in Phase 2; avoid VIN/location exposure unless necessary and consented.
- Explicit choices for local-only vs cloud upload, retention, data deletion, and sharing.
- Respect Android Bluetooth permissions, background execution constraints, foreground-service rules (§4), and battery optimization behavior.
- No driver-distracting UI; prioritize passive collection and safe notifications.
- Include clear warnings that telemetry cannot replace professional vehicle diagnostics.

## 13. Research references / candidates to evaluate

- **AndrOBD:** Android open-source OBD diagnostics and adapter interaction; review architecture and license before reusing code.
- **OVMS (Open Vehicle Monitoring System):** vehicle-specific telemetry modules and remote monitoring patterns.
- **Freematics:** OBD/GPS acquisition hardware and telemetry pipeline examples.
- **OpenTelemetry / OTLP:** vendor-neutral telemetry data model and exporter protocols.
- **Prometheus + Grafana:** aggregated monitoring and dashboard stack.

Evaluate actual capabilities, maintenance status, licensing, and Android compatibility before selecting dependencies. No external project is assumed to meet FuelBuddy requirements out of the box.

## 14. Acceptance criteria

**Phase 1** is complete when a supported Android device can pair with a validated adapter, discover available PIDs per ECU, stream and display at least five supported live signals, record a trip offline, read available DTCs, export a recording (with DTC records), and recover gracefully from disconnection. Unsupported PIDs must be clearly represented. Measurable targets *(provisional values — FB-D6, to be set from the §15 item 3 benchmark)*: five signals at ≥1 Hz for 10 minutes with ≥95% of expected samples, reconnection within 10 seconds, achieved per-PID rate and drop count reported. Replay fixtures with two ECUs returning different support bitmaps, conflicting values and interleaved multiline responses, a positive and a negative (including `7F xx 78` pending) outcome in the same exchange, and one unattributed (`ambiguous`) reply must show that ECU attribution survives storage and export and that no ECU is dropped by a count or timeout; a `DiagnosticEvent` survives storage and export with its rule version; a test confirms forbidden services are never sent.

**Phase 2** is complete when the user can opt in to authenticated cloud sync, queued samples survive offline operation and reconnect, dashboards show received data, bandwidth/retention limits are enforced, and data can be deleted per policy, including queued copies. Upload must not interrupt acquisition.

## 15. Open decisions and recommended next steps

1. Confirm whether FuelBuddy is native Kotlin, Flutter, React Native, or a web wrapper.
2. Select and test 2–3 OBD adapters, including one known-good Bluetooth Classic model.
3. Build a PID capability/throughput benchmark on the Dacia Duster 2018 1.2 TCe 125.
4. Agree on canonical metric names, units, source provenance, and retention defaults.
5. Prototype local acquisition + Room + basic dashboard + event recorder.
6. Benchmark JSON versus OTLP/protobuf with batching and compression using realistic samples.
7. Only then choose Phase 2 backend retention, metric aggregation, ingestion cost, and sync policy.

HUMAN decisions FB-D1 to FB-D6 are tracked in `reviews/round-2/CONSOLIDATION.md`.

**Recommendation:** keep Phase 1 local-only, but define the `TelemetryExporter` interface and stable metric schema immediately so cloud support can be added without reworking acquisition or vehicle models.
