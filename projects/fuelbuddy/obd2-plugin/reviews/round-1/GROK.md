# GROK review — round 1

Reviewed local `spec.md` **v0.1** (2026-10-21). This is round 1: there is no `reviews/round-0/` and no `decisions.md`, so no carried HUMAN decisions. The stack choice and the canonical metric-name list in §15 are already open; they are not re-filed here.

### GROK-1 · Read-only is not an allowlist

- **Section:** §1, §4, §5, §12
- **Type:** risk
- **Severity:** major
- **Finding:** The safety principle says the product is read-only, while the only command operation, `ObdTransport.exchange(command: ByteArray)`, accepts any payload. SAE J1979 service `04` clears emission-related diagnostic information (stored codes, freeze frame, and monitor status). Service `08` commands an on-board system, test, or component. The non-goal forbids clearing codes only when that clear is automatic, so a user-triggered clear still fits the written non-goal. Wikipedia also lists manufacturer services above service `09` (its example is service `22`). Nothing in the transport rejects those before they are written to the adapter.
- **Proposed change:** Add to §5 and §12: "Phase 1 may send only SAE J1979 services `01`, `03`, `07`, and `0A`, plus the adapter-local commands required to connect and to enable response headers. Service `04` and service `08` are rejected in the app, including from a user control. Manufacturer services outside that list are rejected in Phase 1. Service `09` is omitted because its PID `02` returns the VIN; a later phase that needs it requires a separate consent record. The transport drops any other vehicle request and records an error. It does not pass that request to the adapter." In §1, replace "clearing DTCs automatically" with "clearing DTCs or commanding actuators, whether the request is automatic or user-initiated."
- **Evidence:** Wikipedia, "OBD-II PIDs", services table and service `04` / service `09` PID `02`, https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21. SAE J1979 September 1997 text, §5.5 Mode `$04` and §5.9 Mode `$08`, http://electroniqueveynes.free.fr/IMG/pdf/SAE_j1979_199709mod.pdf, checked 2026-10-21 (this is the 1997 edition; the Wikipedia table checked the same day still lists `04` as clear and `08` as control, and adds service `0A`).
- **Confidence:** high

### GROK-2 · Samples and DTCs have no responding controller

- **Section:** §5, §6, §10, §14
- **Type:** error
- **Severity:** major
- **Finding:** On 11-bit CAN the functional request address is `7DF`, and any controller in `7E8`–`7EF` may answer. The ELM327 manual shows two controllers answering one request, and shows their multiline frames interleaved until headers are enabled and frames are grouped by CAN ID. `exchange` returns one `ByteArray`. `discover()` returns a set of capabilities with no address. The metric schema has `adapter_id` and no controller address. A Mode `03` code from a second controller would be stored as if it came from the same source as RPM, and §10 would rank causes from that merged observation.
- **Proposed change:** Add a required `source_address` to every transport response, capability, DTC, and `VehicleMetricSample` (CAN response ID, or that protocol's source address). "A functional request may produce one result per responding controller. Multiline payloads are reassembled per `source_address`. A sample or DTC with no `source_address` is stored with `quality=error` and is excluded from diagnostic ranking."
- **Evidence:** Elm Electronics ELM327 operation manual, header example (`01 00` → `7E8 …`) and physical addressing, https://www.manualshelf.com/manual/elm/327/operation-manual-english/page-41.html, checked 2026-10-21. Same manual, multiline replies from `7E8` and `7E9` mixed until headers are on, https://www.manualshelf.com/manual/elm/327/operation-manual-english/page-43.html, checked 2026-10-21. Wikipedia, "OBD-II PIDs", functional ID `7DF` and responses `7E8`–`7EF`, https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21.
- **Confidence:** high

### GROK-3 · One byte array cannot represent the adapter's replies

- **Section:** §5, §6, §7
- **Type:** error
- **Severity:** major
- **Finding:** An ELM327-class adapter is a single command channel: the host waits for the `>` prompt before the next command, and a character that arrives during a command can abort it. The default reply wait is 200 ms, after which the adapter prints `NO DATA` (about four queries per second at that setting when a vehicle would otherwise have answered in about 50 ms). The same datasheet defines distinct host-facing words for failure (`?`, `UNABLE TO CONNECT`, `CAN ERROR`, `DATA ERROR`, `BUFFER FULL`, `BUS BUSY`, `BUS ERROR`, `STOPPED`). A positive OBD payload uses service + `0x40` (service `01` → `41`); a negative response uses `7F`. `exchange` returns only `ByteArray`, and §7 allows any number of coroutines to poll. Those failure words and an aborted reply can be decoded as RPM, MAP, or a DTC.
- **Proposed change:** Add to §5 and §7: "`ObdTransport` runs one exchange at a time. The caller waits until the adapter is idle (ELM327: the `>` prompt) before sending another command. Overlapped polls are forbidden. `exchange` returns a typed result: `payload` (bytes plus `source_address`), `no_data`, `negative`, `timeout`, `adapter_error`, or `disconnected`. A `payload` may become `quality=valid` only when its response service byte equals the request service plus `0x40`. The words `NO DATA`, `?`, `UNABLE TO CONNECT`, `CAN ERROR`, `DATA ERROR`, `BUFFER FULL`, `BUS BUSY`, `BUS ERROR`, and `STOPPED`, and a response service byte of `7F`, map to `unavailable` or `error`. They are never passed to the PID decoder."
- **Evidence:** Elm Electronics ELM327 datasheet (SparkFun copy, copyright 2005–2013): wait for `>` (hex `3E`) before the next command; a received character aborts the command in progress; `NO DATA` after the reply timer; default timer 200 ms and about four queries per second; error-word list. https://cdn.sparkfun.com/assets/learn_tutorials/8/3/ELM327DS.pdf, checked 2026-10-21. Wikipedia, "OBD-II PIDs": response service is the request service plus `40h`; `7F` is a negative response. https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21.
- **Confidence:** high

### GROK-4 · Stored, pending, and permanent DTCs are one word in the schema

- **Section:** §4, §6, §10, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** Phase 1 reads services `03`, `07`, and `0A`. Wikipedia defines those as stored DTCs, pending DTCs, and permanent DTCs. The canonical sample has one `value`. A single categorical value cannot hold a list of codes, and it cannot keep the three services apart. §10 then maps "OBD DTCs" into reasoning as if they were one observation. Service `02` (freeze frame, including the DTC that triggered the frame) is outside the Phase 1 mode list, so a decoder that fetches it anyway is inventing scope.
- **Proposed change:** Add to §6: "Each DTC is its own observation: `service` (`03`, `07`, or `0A`), `source_address`, and the code bytes. The three services stay in separate records. Service `02` is outside Phase 1. Adding freeze frames later names service `02` explicitly and links the frame to the DTC that triggered it."
- **Evidence:** Wikipedia, "OBD-II PIDs", services `02`, `03`, `07`, and `0A`, https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21. Phase 1 mode list is the local spec §4.
- **Confidence:** high

### GROK-5 · Session time and staleness have no rule

- **Section:** §6, §8, §10
- **Type:** gap
- **Severity:** minor
- **Finding:** `observed_at` is a UTC wall clock. A phone clock step during a drive reorders samples and makes the §8 windows (30 seconds before an anomaly, 60 seconds after) ambiguous. `quality` includes `stale`, and §10 depends on fresh data for underboost and similar calls, but no field says when a sample becomes stale or that a non-valid sample has no numeric `value`. `session_id` is a drive/charging id with no start or end condition. Phase 3 is what correlates charging sessions; Phase 1 still needs a recording-session boundary.
- **Proposed change:** Add to §6: "Each sample stores `monotonic_ns`, the elapsed time of the adapter session, beside `observed_at`. Ordering and flight-recorder windows use `monotonic_ns`. The scheduler writes `stale_after_ms` for that metric. Consumers treat a sample as stale when its monotonic age exceeds `stale_after_ms`. Diagnosis uses only `quality=valid`. When `quality` is `unavailable`, `stale`, or `error`, `value` is null. A Phase 1 session starts when the user starts a recording on a connected adapter and ends when the user stops it, the adapter disconnects, or the recording service stops."
- **Evidence:** reasoning only, against §6 and §8. The 30 s / 60 s figures are the spec's own.
- **Confidence:** high

### GROK-6 · A supported-PID bit is not a promise of data

- **Section:** §2, §4, §7
- **Type:** gap
- **Severity:** minor
- **Finding:** Service `01` PID `00` returns four bytes, and each bit says whether one of the next 32 PIDs is supported. The following bitmap PIDs work the same way while the next-range bit is set. The ELM327 prints `NO DATA` when the reply timer expires. §7 says to poll discovered PIDs and to mark unsupported or unavailable metrics, but it does not say that one `NO DATA` or one `7F` leaves the capability in place for the rest of the session. Clearing the bit on the first miss drops RPM or MAP for the whole trip after a single busy reply.
- **Proposed change:** Add to §7: "Discovery walks the service `01` supported-PID bitmaps, starting at PID `00`, and continues while the next-range bit is set. A set bit records the PID as supported for that `source_address`. `NO DATA`, timeout, or a `7F` response sets that sample's `quality` to `unavailable` or `error` and leaves the capability record unchanged for the session."
- **Evidence:** Wikipedia, "OBD-II PIDs", "Service 01 PID 00 — Show PIDs supported", https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21. ELM327 datasheet, `NO DATA` when the reply timer expires, https://cdn.sparkfun.com/assets/learn_tutorials/8/3/ELM327DS.pdf, checked 2026-10-21.
- **Confidence:** high

### GROK-7 · A driving trip is specified as passive and also as in-process

- **Section:** §4, §7, §12, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** §12 requires passive collection and a UI that does not distract the driver. §14 requires an offline trip recording that recovers from disconnection. On Android 12 (API 31) an app cannot start a foreground service from the background, apart from listed exemptions. On Android 14 (API 34) a long-running Bluetooth session uses foreground service type `connectedDevice` and the permission that type requires. §12 says to respect those rules. Phase 1 never requires the recording to be a foreground service started while the app is visible, which is the session that can continue with the screen off.
- **Proposed change:** Add to §4: "Phase 1 recording runs in a foreground service started while the app is visible. Where the platform requires a service type, use the connected-device type and its permission (Android 14: `connectedDevice`). The service keeps the adapter session when the screen is off. Polling stops when the user ends the recording or the adapter disconnects. The driving UI stays passive."
- **Evidence:** Android Developers, "Restrictions on starting a foreground service from the background" (apps targeting API 31), https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start, checked 2026-10-21. Android Developers, "Foreground service types", connected device, required from Android 14 (API 34), https://developer.android.com/develop/background-work/services/fgs/service-types, checked 2026-10-21.
- **Confidence:** high

### GROK-8 · Gauge boost is a derived metric with no inputs

- **Section:** §4, §6, §10
- **Type:** gap
- **Severity:** minor
- **Finding:** The Duster pilot says to estimate gauge boost only when the inputs are trustworthy, and §6 says to track raw versus derived metrics. The schema has `quality` and `decoder_version`, and no derivation flag or input list. Wikipedia lists service `01` PID `0B` as intake manifold absolute pressure in kPa (0–255) and PID `33` as absolute barometric pressure in kPa (0–255). Their difference is intake-manifold gauge pressure when both readings are valid and from the same controller. The spec gives no rule an implementer can apply, so two builds can publish different "boost" series into §10.
- **Proposed change:** Add to §6: "Add `derivation` (`raw` or `derived`). A derived sample lists its inputs (metric key, `source_address`, `monotonic_ns`). Gauge manifold pressure is PID `0B` minus PID `33` only when both samples are `quality=valid`, both are kPa, and both share `source_address`; otherwise the derived sample is `quality=unavailable` and `value` is null. That difference is intake-manifold gauge pressure. It is not a turbocharger-outlet pressure and it is not a confirmed fault."
- **Evidence:** Wikipedia, "OBD-II PIDs", PID `0B` and PID `33`, https://en.wikipedia.org/wiki/OBD-II_PIDs, checked 2026-10-21. The subtraction rule is reasoning from those two absolute kPa definitions.
- **Confidence:** high

### GROK-9 · Deletion and consent stop short of the queues

- **Section:** §8, §11, §12, §14
- **Type:** question
- **Severity:** minor
- **Finding:** Phase 2 acceptance says data can be deleted per policy, and §11 says to avoid collection before consent or after the module is disabled. The flight-recorder ring and the durable offline queue are copies of the same samples. A delete that touches only the database still leaves a batch that §8 will upload on reconnect. The offline entitlement grace period is described as "defined" and the length is not in §15. Choosing that length is a commercial decision for HUMAN.
- **Proposed change:** Add to §11 and §12: "Withdrawing upload consent, disabling the module, or deleting telemetry discards the matching samples in the database, the in-memory ring, and the durable upload queue, and those samples are not uploaded later. Export remains available for samples the user has not deleted. The offline grace duration is an open HUMAN decision; the spec records the chosen duration once HUMAN sets it and does not invent one here."
- **Evidence:** reasoning only, against §8, §11, and §14.
- **Confidence:** medium

### GROK-10 · Comment callouts read as requirements

- **Section:** §3, §4, §5, header status
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Three Gemini callouts are inside the spec and labeled Minor, Major, and Blocking. The status line says "Draft / proposed architecture (Reviewed)" on v0.1 before this round is consolidated. The Phase 2 paragraph already says Prometheus is not the sole archive for raw per-vehicle samples. The callout under it demands a named time-series product. An implementer can treat the callout label as the requirement and treat the review as already finished.
- **Proposed change:** Remove the three Gemini callouts from `spec.md` (they belong in a review file). Set the status line to "Draft / proposed architecture". Keep the normative Phase 2 sentence that raw per-vehicle samples are not archived in Prometheus alone.
- **Evidence:** reasoning only, against the local spec text. No product claim in the callouts was re-checked.
- **Confidence:** high

## Top 3

1. **GROK-1** — Phase 1 needs a service allowlist. Service `04` and service `08` are writes, and `exchange` currently accepts them.
2. **GROK-2** — Every sample and DTC needs the responding controller. Functional `7DF` replies are a set, and multiline frames from `7E8` and `7E9` mix without headers.
3. **GROK-3** — One in-flight command, and adapter failure words stay out of the PID decoder. A `ByteArray` return makes `NO DATA` and an aborted reply look like sensor data.

Result: complete
