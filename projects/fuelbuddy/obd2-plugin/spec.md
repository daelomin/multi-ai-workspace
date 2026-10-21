# FuelBuddy — OBD-II Telemetry Module Specification

**Version:** v0.1  
**Status:** Draft / proposed architecture (Reviewed)  
**Date:** 2026-10-21  
**Scope:** Optional paid OBD-II module, offline-first Phase 1, cloud observability Phase 2

## 1. Objectives

Build a modular vehicle telemetry capability for FuelBuddy that:
- Connects an Android phone to a compatible OBD-II adapter and discovers available vehicle data.
- Collects live signals, diagnostic trouble codes (DTCs), and supported vehicle-specific parameters.
- Normalizes readings into FuelBuddy's vehicle model without assuming every car supports every signal.
- Provides useful local diagnostics and historical dashboards without an internet connection.
- Later relays selected telemetry to a backend for fleet-scale analysis, Grafana dashboards, and advanced charging/vehicle diagnostics.
- Enables or disables premium OBD features through entitlements, without coupling telemetry storage to billing.

**Non-goals (initially):** ECU programming, clearing DTCs automatically, writing vehicle parameters, guaranteed access to proprietary OEM data, and continuous cloud streaming in Phase 1.

## 2. Key design principles

1. **Offline first:** acquisition, storage, visualization, and initial alerts work locally.
2. **Modular:** adapter transport, protocol decoding, vehicle model, storage, diagnostics, and cloud export are independently replaceable.
3. **Capability driven:** interrogate supported PIDs and mark unsupported, unavailable, or stale metrics explicitly.
4. **Safe and read-only:** no control commands or ECU modifications in the initial product.
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

> **[COMMENT — Gemini — Minor Issue]:** Ensure that the push model implementation includes robust token refreshing and secure local credential storage (e.g., EncryptedSharedPreferences or Jetpack Security) to prevent unauthorized API requests if a user's session token is intercepted on mobile.

## 4. Phased delivery

### Phase 1 — Local-only MVP

- Android integration (Kotlin if confirmed; verify actual application stack before implementation).
- Bluetooth Classic transport first, plus BLE/Wi-Fi adapter support through interfaces as needed.
- Adapter identification, connection/reconnection, supported PID discovery, error handling.
- Standard SAE J1979/OBD-II read-only Mode 01 live signals and Mode 03/07/0A DTC reads where supported.
- Local timestamped storage (e.g., Room/SQLite), local charts, trip/session history, basic diagnostic rules.
- A user-controlled premium feature entitlement; local functionality should remain usable offline with an appropriate cached entitlement policy.
- Diagnostic event capture with pre-event ring buffer and post-event window.
- Export recordings to a portable format for debugging, with user approval.
- No external telemetry server required.

**Initial metrics to probe:** RPM, vehicle speed, engine coolant temperature, calculated engine load, manifold absolute pressure (MAP), intake air temperature, throttle position, short/long-term fuel trims, and control-module voltage where supported. Optional: mass airflow, fuel pressure, commanded equivalence ratio, and oxygen sensor data. Not all vehicles expose all metrics.

**Duster 2018 1.2 TCe 125 pilot:** verify PID support, record MAP/barometric pressure where available, RPM, load, throttle, and fuel trims; estimate gauge boost only when inputs are trustworthy. Record transient loss-of-power episodes for later investigation; do not equate a boost anomaly with a confirmed turbo failure.

### Phase 2 — Cloud telemetry and observability

- Implement an exporter interface and secure backend ingestion endpoint.
- Prefer OTLP over HTTPS with protobuf and batching; optionally support JSON for debugging/interoperability.
- Integrate OpenTelemetry Collector and Prometheus-compatible metric storage; Grafana for dashboards.
- Use a separate event/log or time-series store for high-cardinality per-vehicle raw samples as needed; do not treat Prometheus as the sole archive for every raw sensor reading.
- Adaptive synchronization, compression, backpressure, retry with exponential backoff, and deduplication.
- User-configurable upload consent, retention, and delete/export controls.
- Remote analytics and charging-diagnostics enrichment; advanced alert delivery is optional and deferred.

> **[COMMENT — Gemini — Major Issue]:** Using a Prometheus-compatible store for high-cardinality per-vehicle raw time-series data at scale will lead to severe cardinality explosion and storage bloat. Prometheus is optimized for low-cardinality service metrics, not per-vehicle raw sensor streams. A dedicated time-series database (such as TimescaleDB, ClickHouse, or VictoriaMetrics) must be specified for the raw metrics backend instead of relying solely on Prometheus.

### Phase 3 — OEM/EV expansion (future)

- Manufacturer-specific PIDs and decoders, subject to validation, permissions, and licensing.
- EV BMS metrics where exposed (SOC, SOH, pack voltage/current, battery temperature, charge power).
- Vehicle/charger compatibility analytics, charging-session correlation, anomaly models, and optional fleet insights.
- OEM APIs as additional sources with explicit provenance and freshness tracking.

## 5. Module boundaries / Kotlin interfaces (illustrative)

```kotlin
interface ObdTransport {
    suspend fun connect(): ConnectionInfo
    suspend fun exchange(command: ByteArray): ByteArray
    suspend fun disconnect()
}

interface VehicleCapabilityDiscovery {
    suspend fun discover(): Set<MetricCapability>
}

interface TelemetrySource {
    fun samples(): kotlinx.coroutines.flow.Flow<VehicleMetricSample>
}

interface TelemetrySink {
    suspend fun write(batch: List<VehicleMetricSample>)
}

interface TelemetryExporter {
    suspend fun export(batch: List<VehicleMetricSample>): ExportResult
}
```

Separate adapter/transport-specific framing from ELM327 AT commands, OBD request scheduling, PID decoding, and storage. Use Kotlin coroutines/Flow where the app is native Kotlin; adapt this design to the actual stack otherwise.

> **[COMMENT — Gemini — Minor Issue]:** The `ObdTransport.exchange` function takes and returns `ByteArray`, but raw ELM327 communications often require handling carriage returns (`\r`), prompt characters (`>`), and various error states like `BUFFER FULL`, `NO DATA`, or `UNABLE TO CONNECT`. Consider defining a dedicated response wrapper or result type rather than a raw `ByteArray` to cleanly handle protocol errors and timeouts.

## 6. Canonical vehicle metric schema

Suggested fields:

| Field | Purpose |
|---|---|
| `vehicle_id` | Pseudonymous FuelBuddy vehicle identifier |
| `session_id` | Drive/charging session identifier |
| `metric_key` | Stable name, e.g. `engine.rpm` |
| `value` | Typed numeric or categorical reading |
| `unit` | Canonical unit, e.g. `rpm`, `km/h`, `kPa`, `degC` |
| `observed_at` | UTC timestamp of acquisition |
| `received_at` | Optional processing timestamp |
| `source` | `obd2`, `oem_api`, `ev_bms`, etc. |
| `protocol` | OBD mode/PID or OEM protocol identifier |
| `quality` | Valid, estimated, stale, unavailable, error |
| `sample_interval_ms` | Effective acquisition interval |
| `adapter_id` | Optional pseudonymous adapter identifier |
| `decoder_version` | Reproducibility and compatibility |

Maintain a separate **vehicle specification/profile** (make/model/year/engine, supported connectors, known issues) from **observed telemetry** and **derived diagnostics**. Track raw versus derived metrics, confidence, and source provenance.

## 7. Acquisition and throughput

- Poll only discovered supported PIDs; do not assume all can be sampled at 1 Hz simultaneously.
- Schedule fast-changing metrics (RPM, MAP, throttle) more frequently than temperatures or static status.
- Measure actual adapter/ECU round-trip latency and adjust polling to avoid overload.
- Use bounded queues and record dropped sample counts; never let network upload block the OBD polling loop.
- Stop or throttle acquisition when disconnected or under restrictive power/thermal conditions.
- Treat generic low-cost ELM327 clones as variable quality; prefer well-tested adapters for validation.

> **[COMMENT — Gemini — Blocking Issue]:** Bluetooth Classic socket management on Android (especially RFCOMM channels) is prone to abrupt drops and deadlocks if background tasks or lifecycle changes interrupt the connection stream. An explicit connection watchdog, lifecycle-aware foreground service wrapper, and automated backoff/reconnection strategy must be mandated in Phase 1 to prevent UI freezes or silent data loss during active driving sessions.

## 8. Adaptive sync policy (Phase 2)

| Condition | Suggested upload behavior |
|---|---|
| Good Wi-Fi / 5G | Batched near-real-time updates, approximately every 1–5 seconds if permitted |
| Stable 4G | Batches every 10–30 seconds |
| Weak / metered connection | Longer batches, downsampled summaries, e.g. 60 seconds |
| Offline | Durable local queue; sync later under limits |
| Diagnostic anomaly | Preserve higher-resolution pre/post-event samples locally; upload when policy permits |

These are **starting policies, not guarantees**: effective rate depends on OBD throughput, bandwidth, power, user settings, and backend cost. Network type alone is not a reliable indicator of available bandwidth; use observed performance and metering status.

**Flight recorder:** configurable ring buffer, initially 30 seconds before and 60 seconds after a detected anomaly, retaining high-resolution data locally. Use bounded storage and avoid automatic upload without consent.

## 9. Payload and storage budgeting

Do not assume telemetry is below 1 MB/hour. For example, **30 metrics each sampled once per second** produce 108,000 samples/hour. At 20–100 bytes/sample after efficient encoding/packing, that is approximately **2.2–10.8 MB/hour** before transport overhead; JSON with repeated field names may be considerably larger. Actual figures must be benchmarked.

Plan a simulator/benchmark with configurable metric count, rates, event frequency, format (JSON, protobuf/OTLP), batching, compression, and offline retention. Report bytes/hour, phone storage/day, mobile data/month, backend ingestion rate, and estimated cost per active vehicle. Test gzip/zstd where supported, while accounting for CPU/battery impact.

## 10. Diagnostics and integration with FuelBuddy

- Map OBD DTCs, vehicle model/year/engine, and observed signals into FuelBuddy's existing diagnostic reasoning pipeline.
- Preserve separation between **observations**, **hypotheses**, and **confirmed faults**.
- Rank possible causes of charging/engine anomalies; include uncertainty and recommended checks.
- Detect conditions such as sustained underboost only when sufficient data exists; avoid false diagnoses from MAP alone.
- Expose standardized metrics to the existing car profile and future charging calculator without making OBD mandatory.
- Support multiple data sources with conflict resolution and priority/freshness rules.

## 11. Entitlements and commercial module

- OBD capability is optional and may be a paid feature.
- Server validates purchase/entitlement when connected; signed or otherwise tamper-resistant cached entitlement permits a defined offline grace period.
- Gate premium UI/export/analysis at the feature layer; keep the canonical telemetry schema independent of subscription logic.
- Avoid collecting telemetry before consent or when a user has disabled the module.
- Define what happens to existing locally stored data if the subscription expires (recommended: user can still export/delete their data).

## 12. Security, privacy, and safety

- Read-only OBD commands by default; no ECU writes, actuator tests, or automatic code clearing.
- Pair only with a user-approved adapter and protect credentials/keys using Android platform facilities.
- TLS and authenticated ingestion in Phase 2; avoid VIN/location exposure unless necessary and consented.
- Explicit choices for local-only vs cloud upload, retention, data deletion, and sharing.
- Respect Android Bluetooth permissions, background execution constraints, foreground-service rules, and battery optimization behavior.
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

**Phase 1** is complete when a supported Android device can pair with a validated adapter, discover available PIDs, stream and display at least five supported live signals, record a trip offline, read available DTCs, export a recording, and recover gracefully from disconnection. Unsupported PIDs must be clearly represented.

**Phase 2** is complete when the user can opt in to authenticated cloud sync, queued samples survive offline operation and reconnect, dashboards show received data, bandwidth/retention limits are enforced, and data can be deleted per policy. Upload must not interrupt acquisition.

## 15. Open decisions and recommended next steps

1. Confirm whether FuelBuddy is native Kotlin, Flutter, React Native, or a web wrapper.
2. Select and test 2–3 OBD adapters, including one known-good Bluetooth Classic model.
3. Build a PID capability/throughput benchmark on the Dacia Duster 2018 1.2 TCe 125.
4. Agree on canonical metric names, units, source provenance, and retention defaults.
5. Prototype local acquisition + Room + basic dashboard + event recorder.
6. Benchmark JSON versus OTLP/protobuf with batching and compression using realistic samples.
7. Only then choose Phase 2 backend retention, metric aggregation, ingestion cost, and sync policy.

**Recommendation:** keep Phase 1 local-only, but define the `TelemetryExporter` interface and stable metric schema immediately so cloud support can be added without reworking acquisition or vehicle models.