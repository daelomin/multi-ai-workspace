# FuelBuddy — OBD-II Telemetry Module Specification

**Version:** v0.2  
**Status:** Draft / proposed architecture  
**Date:** 2026-10-21  
**Scope:** Optional paid OBD-II module, offline-first Phase 1, cloud observability Phase 2

Items marked *(provisional — FB-Dn)* depend on an open HUMAN decision listed in `reviews/round-1/CONSOLIDATION.md`; the text shows the interim default and is not a decision.

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
    suspend fun exchange(request: ObdRequest): ObdResponse
    suspend fun disconnect()
}

sealed interface ObdResponse {
    data class Payload(val source: EcuAddress, val bytes: ByteArray) : ObdResponse
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

// TelemetryRecord = VehicleMetricSample | DtcRecord | (later) FreezeFrame
```

Separate adapter/transport-specific framing from ELM327 AT commands, OBD request scheduling, PID decoding, and storage. Use Kotlin coroutines/Flow where the app is native Kotlin; adapt this design to the actual stack otherwise.

**Single owner, one exchange at a time.** One acquisition component owns the `ObdTransport`; every request (discovery, polling, DTC reads) goes through its single-flight queue and no other component calls `exchange`. An ELM327-class adapter is one text channel: the next command is sent only after the `>` prompt, and a character sent earlier can abort the command in progress. `samples()` is a shared stream fed by that component; a second collector must not start a second poll loop. Test: discovery, polling and a DTC read run together and each response is paired with its request.

**Typed results, not raw bytes.** Adapter words (`NO DATA`, `?`, `UNABLE TO CONNECT`, `CAN ERROR`, `DATA ERROR`, `BUFFER FULL`, `BUS BUSY`, `BUS ERROR`, `STOPPED`), a negative response (service byte `7F`) and timeouts are mapped to the non-payload `ObdResponse` cases and never reach the PID decoder. A `Payload` may be decoded as `valid` only if its response service byte equals the request service + `0x40`.

**ECU identity.** A functional request (CAN `7DF`) may be answered by several ECUs (`7E8`–`7EF`), possibly with different supported-PID bitmaps and interleaved multiline frames. Configure the adapter so the responder is visible (headers on, or physical addressing). Reassemble multiline responses per responder. Capabilities, samples and DTC records carry the responder address (`EcuAddress`, scoped to the vehicle and connection protocol). Different responders are never merged implicitly and never averaged. The ECU used for each canonical metric comes from an explicit validated mapping in the vehicle profile; other responders are kept with their provenance. If the responder cannot be established the result is `ambiguous` and is excluded from ECU-specific diagnostics (§10).

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
| `received_at` | Optional processing timestamp (server-side in Phase 2) |
| `source` | `obd2`, `oem_api`, `ev_bms`, etc. |
| `source_address` | Responding ECU address (`EcuAddress`); required for `obd2` |
| `protocol` | OBD mode/PID or OEM protocol identifier |
| `quality` | `valid`, `estimated`, `stale`, `unavailable`, `unsupported`, `error` |
| `stale_after_ms` | Per-metric age limit; a sample is stale when its monotonic age exceeds it |
| `sample_interval_ms` | Effective acquisition interval |
| `origin` | `raw` or `derived` |
| `derivation` | For derived samples: derivation id/formula version, input refs (metric key, `source_address`, `monotonic_ns`), confidence |
| `adapter_id` | Optional pseudonymous adapter identifier |
| `decoder_version` | Reproducibility and compatibility (raw decoding) |

**Quality and values.** `unavailable`, `unsupported` and `error` samples carry a null `value` (never zero). A `stale` sample keeps its last value but is not used for diagnosis. Diagnoses use only `valid` inputs (and `estimated` where a rule says so).

**Time.** Ordering, durations and recorder windows use `monotonic_ns`; the wall clock is for display and export. Define whether acquisition time is request start or response completion, and keep request/response timing where it expresses uncertainty. A reconnect or recording-epoch change invalidates prior live inputs. Test a backwards UTC clock change.

**DTCs are records, not samples.** `DtcRecord`: code, service (`03` stored, `07` pending, `0A` permanent; the three stay separate), `source_address`, first/last seen, occurrence count, MIL status, raw bytes. A DTC with no responder address is stored as `ambiguous` and excluded from diagnostic ranking. Freeze frames (Mode 02) are outside Phase 1 *(provisional — FB-D2)*; if added they name Mode 02 and link to the triggering DTC. Exports carry a versioned manifest and redact VIN and adapter identifiers unless the user chooses otherwise.

**Derived metrics.** Derived samples are marked `origin=derived` with the formula version and inputs. Gauge manifold pressure = PID `0B` (MAP) − PID `33` (barometric), both kPa, only when both inputs are `valid`, from the same `source_address`, within the declared maximum time separation, and the engine is known to be running; otherwise the derived sample is `unavailable` with a null value. The result is signed (negative = vacuum). It is intake-manifold gauge pressure, not turbocharger-outlet pressure, and not a confirmed fault. If PID `33` is not supported, no estimate is produced and no constant is substituted.

**Sessions.** A session is a recording of drive data between a start and an end, with `started_at`, `ended_at`, `end_reason` and gap markers. A DTC-only read with the engine off is a `diagnostic_read`, not a drive session. Interim Phase 1 rule *(provisional — FB-D4)*: a session starts when the user starts a recording on a connected adapter and ends when the user stops it, the adapter disconnects beyond the reconnect grace period, or the recording service stops; a reconnect within the grace period resumes the same session with a gap marker. Charging sessions are a Phase 3 concern.

Maintain a separate **vehicle specification/profile** (make/model/year/engine, supported connectors, known issues, canonical-metric-to-ECU mapping) from **observed telemetry** and **derived diagnostics**.

## 7. Acquisition and throughput

- Poll only discovered supported PIDs; do not assume all can be sampled at 1 Hz simultaneously.
- **Discovery:** read Mode 01 PID `00` and follow the bitmap pages (`20`, `40`, …) only while the next-range bit is set, per responding ECU. Classify each PID `supported | unsupported | unknown | adapter_error`; a set bit means supported for that ECU. Show `unknown` in the UI rather than "not supported".
- A single `NO DATA`, timeout or `7F` sets that sample's quality to `unavailable` or `error` and leaves the capability record unchanged for the session. Re-run discovery on adapter change, protocol change, reconnect after a vehicle power cycle, or a configurable number of consecutive misses; cache per adapter + firmware + protocol + ECU.
- Schedule fast-changing metrics (RPM, MAP, throttle) more frequently than temperatures or static status.
- Measure actual adapter/ECU round-trip latency and adjust polling to avoid overload. With the ELM327 default 200 ms response wait, about 4 queries/s is the ceiling; shorter timeouts and expected-response counts are part of adapter validation.
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

**Flight recorder:** configurable ring buffer, initially 30 seconds before and 60 seconds after a detected anomaly, retaining high-resolution data locally. The buffer stores every locally accepted sample, independent of upload policy; "high-resolution" means the local acquisition rate. Anomaly-relevant metrics (RPM, MAP, throttle, fuel trims) have a minimum local acquisition floor *(provisional rate, e.g. ≥1 Hz — FB-D6)*; windows containing a gap are marked so diagnostics do not treat them as continuous. Use bounded storage and avoid automatic upload without consent.

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
- **Consent and deletion reach the queues.** Check current cloud consent and account/vehicle ownership when dispatching every batch, including retries. Revoking consent, disabling the module or deleting telemetry stops new dispatches, cancels pending retries and attempts to cancel in-flight transfers, and discards the matching samples in the database, the in-memory ring and the durable upload queue, so reconnect or retry cannot recreate deleted data. Already accepted uploads require the cloud deletion flow, which must be disclosed. Local recordings remain under the user's local policy. A later opt-in states explicitly whether historical local recordings are eligible for upload. Test revoke-while-offline then reconnect, and deletion with a pending retry.

## 12. Security, privacy, and safety

- **Read-only is enforced.** The framing layer, before `ObdTransport.exchange`, sends only an explicit allowlist: OBD services `01`, `03`, `07`, `0A` (plus `02`/`09` only if FB-D2 adds them) and the adapter-local commands needed to connect and enable response headers. Anything else is dropped and logged as an error, never passed to the adapter. In particular service `04` (clear DTCs and stored data, MIL off), service `08` (control of on-board components), UDS write/routine services and arbitrary raw CAN frames are rejected, from every caller including debug tools and user controls. Test that a forbidden service is rejected. Manual DTC clearing is not part of this module (FB-D3).
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

**Phase 1** is complete when a supported Android device can pair with a validated adapter, discover available PIDs per ECU, stream and display at least five supported live signals, record a trip offline, read available DTCs, export a recording (with DTC records), and recover gracefully from disconnection. Unsupported PIDs must be clearly represented. Measurable targets *(provisional values — FB-D6, to be set from the §15 item 3 benchmark)*: five signals at ≥1 Hz for 10 minutes with ≥95% of expected samples, reconnection within 10 seconds, achieved per-PID rate and drop count reported. Replay fixtures with two ECUs returning different support bitmaps, conflicting values and interleaved multiline responses must show that ECU attribution survives storage and export; a test confirms forbidden services are never sent.

**Phase 2** is complete when the user can opt in to authenticated cloud sync, queued samples survive offline operation and reconnect, dashboards show received data, bandwidth/retention limits are enforced, and data can be deleted per policy, including queued copies. Upload must not interrupt acquisition.

## 15. Open decisions and recommended next steps

1. Confirm whether FuelBuddy is native Kotlin, Flutter, React Native, or a web wrapper.
2. Select and test 2–3 OBD adapters, including one known-good Bluetooth Classic model.
3. Build a PID capability/throughput benchmark on the Dacia Duster 2018 1.2 TCe 125.
4. Agree on canonical metric names, units, source provenance, and retention defaults.
5. Prototype local acquisition + Room + basic dashboard + event recorder.
6. Benchmark JSON versus OTLP/protobuf with batching and compression using realistic samples.
7. Only then choose Phase 2 backend retention, metric aggregation, ingestion cost, and sync policy.

HUMAN decisions FB-D1 to FB-D6 are tracked in `reviews/round-1/CONSOLIDATION.md`.

**Recommendation:** keep Phase 1 local-only, but define the `TelemetryExporter` interface and stable metric schema immediately so cloud support can be added without reworking acquisition or vehicle models.
