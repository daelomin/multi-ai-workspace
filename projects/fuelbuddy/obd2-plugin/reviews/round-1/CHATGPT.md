# CHATGPT review — round 1

Reviewed the local `spec.md` v0.1 dated 2026-10-21 against the project README. This is the initial independent round; no previous consolidation or project `decisions.md` exists. Counts: 0 blocking, 1 major, 3 minor. Proposed field names below are additions, not identifiers claimed to exist already.

### CHATGPT-1 · Preserve ECU identity through discovery, decoding and storage

- **Section:** §4 Phase 1; §5; §6; §14
- **Type:** gap
- **Severity:** major
- **Finding:** Discovery returns vehicle-wide capabilities and the sample schema identifies the adapter and mode/PID, but neither preserves the responding ECU. Multiple ECUs can answer the same request, including with different supported-PID bitmaps; flattening these replies can mix measurements or lose DTC attribution. The current acceptance criteria could pass such an implementation even though its vehicle diagnostics are wrong.
- **Proposed change:** Add: “Preserve the responding ECU address/header in discovered capabilities, decoded samples and DTC records, scoped to the vehicle and connection protocol. Discover support per ECU; never merge different responders implicitly. Select the ECU used for each canonical metric by an explicit validated mapping, retaining alternatives with their provenance. Configure adapter framing to retain responder identity; if identity cannot be established, represent the result as ambiguous and exclude it from ECU-specific diagnostics. Reassemble multiline responses separately per responder. Phase 1 acceptance includes replay fixtures with two ECUs returning different support bitmaps, conflicting values and interleaved responses, verifying that attribution survives storage and export.”
- **Evidence:** [Elm Electronics ELM327 datasheet](https://www.elmelectronics.com/wp-content/uploads/2016/07/ELM327DS.pdf), printed pp. 41–43, checked 2026-10-21. The examples show multiple ECU replies to `01 00` and explain using headers to distinguish responders and group multiline replies. The consequence for the proposed schema is reasoning from those examples.
- **Confidence:** high

### CHATGPT-2 · Define timing and freshness for derived diagnostics

- **Section:** §6; §7; §8; §10
- **Type:** gap
- **Severity:** minor
- **Finding:** UTC acquisition timestamps and an effective sampling interval do not define how to order samples or measure sustained conditions if the phone clock changes. Adaptive sequential polling also means that the latest MAP, RPM and throttle readings need not describe the same instant; no rule bounds their age or separation before a diagnostic combines them.
- **Proposed change:** Add: “Retain UTC time for display/export and a monotonic acquisition time scoped to a recording epoch for ordering, durations and recorder windows. Define whether acquisition time denotes request start or response completion, and retain request/response timing where needed to express uncertainty. Each diagnostic declares required inputs, maximum input age and maximum time separation; missing, stale, ambiguous or excessively separated inputs produce insufficient-data status rather than a fault hypothesis. Reconnects and recording-epoch changes explicitly invalidate prior live inputs. Test a backwards UTC clock change and a delayed required PID.”
- **Evidence:** reasoning only; a hypothetical clock correction or delayed response exposes a missing temporal rule without requiring a particular adapter or diagnostic threshold.
- **Confidence:** high

### CHATGPT-3 · Apply bounded storage to ordinary offline recordings

- **Section:** §4 Phase 1; §8; §9; §14
- **Type:** gap
- **Severity:** minor
- **Finding:** The flight recorder has bounded storage, but ordinary trip history has no explicit capacity or disk-full behavior in Phase 1. Budget benchmarking and later selection of retention defaults do not specify what acquisition should do when its local sink cannot persist another batch.
- **Proposed change:** Add: “Phase 1 shall enforce a configurable total local storage budget covering normal recordings, event recordings and database overhead, with a reserved free-space threshold. At the limit, apply the user's configured retention policy; where no eviction policy is authorized, pause persistence and visibly report the recording gap. Storage failures must not crash acquisition or cause an unbounded in-memory backlog. Track lost sample counts and test budget exhaustion and write failure. Numeric defaults remain subject to the §15 retention decision.”
- **Evidence:** reasoning only; finite storage and an offline producer require a defined capacity-exhaustion path. This proposes behavior, not a particular retention duration.
- **Confidence:** high

### CHATGPT-4 · Specify consent changes for queued uploads

- **Section:** §4 Phase 2; §8; §11; §12; §14
- **Type:** gap
- **Severity:** minor
- **Finding:** Consent, durable retries and deletion are required independently, but their interaction is unspecified. A batch queued under an earlier consent setting could otherwise be retried after the user disables cloud sync, or re-upload data after its deletion.
- **Proposed change:** Add: “Check current cloud consent and account/vehicle ownership when dispatching every batch, including retries. Revocation stops new dispatches, disables pending retries and attempts cancellation of in-flight transfers; disclose that already accepted uploads require the cloud deletion flow. Local recordings are retained under the user's local policy. A deletion request must invalidate corresponding pending uploads so that reconnect or retry cannot recreate deleted data. A later opt-in must explicitly establish whether historical local recordings are eligible for upload. Test revoke-while-offline followed by reconnect, and deletion with a pending retry.”
- **Evidence:** reasoning only; the existing durable queue and retry requirements create these state transitions. This proposes technical semantics without making a legal determination or choosing retention defaults.
- **Confidence:** high

**Top 3**

1. Preserve ECU identity so discovery, readings and DTC attribution remain correct (CHATGPT-1, major).
2. Define sample timing and freshness before combining signals into diagnostic hypotheses (CHATGPT-2, minor).
3. Specify bounded offline recording and storage-failure behavior for Phase 1 (CHATGPT-3, minor).

Result: complete
