# DEEPSEEK review — round 2

**Specification:** FuelBuddy AI Charging Diagnostic System v0.3, dated 11 October 2026.
**Reviewer:** DEEPSEEK. **Review date:** 2026-10-14.
**Method:** Read the README, all three round-1 reviews and `CONSOLIDATION.md`, and the round-2 CHATGPT review before assessing the local `spec.md` v0.3. This pass continues the implementation/contract angle of my round-1 review: internal schema and normative-rule precision. All findings are internal-consistency observations ("reasoning only"); no external vehicle, protocol, or legal claim is re-verified, and no error code, campaign number, or standard clause is invented.

**Overall:** v0.3 is a substantial improvement and the round-1 consolidation was faithful. I find **no new `blocking` or `major` findings**. I agree with CHATGPT's two round-2 majors (safety re-evaluation after matching, and typed measurement identity/qualifiers) and do not duplicate them here. The remaining issues I found are all `minor`: narrow spots where the merged text is still self-contradictory or leaves a contract unrepresentable. FB-D1–FB-D7 are HUMAN decisions and are not re-raised; I have no new external evidence on any of them.

---

### DEEPSEEK-1 · Tie handling sorts causes by a session-level status that cannot separate them

- **Section:** §6.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Tie handling is made "deterministic and stable" by ordering causes on `(decision_status, score, cause_id)`, but `decision_status` is defined two paragraphs earlier as a single evaluation-level value, not a per-cause value. It is therefore constant across every cause within one evaluation, so the first sort key can never separate two causes and the tie-handling rule is not implementable as written.
- **Proposed change:** Remove `decision_status` from the per-cause sort key and order the ranked list by `(score, cause_id)`, or add an explicit per-cause status field if one is meant. State that `decision_status` is carried once on the evaluation result, not per cause.
- **Evidence:** reasoning only (spec-internal: §6.2 "Tie handling" versus the §6.2 "Decision status" table).
- **Confidence:** high

### DEEPSEEK-2 · `protocol_version` has two incompatible shapes

- **Section:** §3.2, §4.5, §9.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 gives `protocol_version` example values that embed the protocol name (`OCPP 1.6`, `ISO 15118-2`), while §4.5 composes a mapping key as `namespace + … + protocol_version + …` and the §9.1 example sets `"namespace": "OCPP"` with `"protocol_version": "1.6"`. One field cannot be both the bare version and the fully-qualified identifier, so an implementer cannot tell which shape to store.
- **Proposed change:** Pick one shape and apply it everywhere: either `protocol_version` is the bare version string (with `namespace` always separate and §4.5's composition left as written), or it is the fully-qualified identifier and §4.5 must not compose it redundantly with `namespace`. Update the §3.2 examples and the §9.1 example to match.
- **Evidence:** reasoning only (spec-internal: §3.2 `protocol_version` row vs §4.5 mapping key vs §9.1 JSON).
- **Confidence:** high

### DEEPSEEK-3 · §3.3 mandates session data the canonical record cannot hold

- **Section:** §3.2, §3.3
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.3 requires recording "the failure timestamp, raw error text, repeat count, and whether another connector, station, network, or charging mode was tested", but the single canonical observation record in §3.2 has `observed_at` and `raw_text` and no `repeat_count` field, and no field for "another connector/station/network/mode was tested". §3.3 therefore mandates fields the canonical schema cannot represent.
- **Proposed change:** Add a nullable `repeat_count` to §3.2, and either add an explicit `tested_alternatives` field or state that "tested another connector/station/network/mode" is represented as its own `session_stage_event`/`user_statement` observation sharing an `attempt_id`. Make §3.3 point at those fields rather than listing them free-form.
- **Evidence:** reasoning only (spec-internal: §3.3 final paragraph vs §3.2 field table).
- **Confidence:** high

### DEEPSEEK-4 · `source_type` is overloaded across event and document provenance

- **Section:** §3.2, §4.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.1 reuses the §3.2 `source_type` enum for evidence records, whose fields (`source_url`, `title`, `publisher`, `published_at`, `document_version`) describe a document. Several enum values — `vehicle_telemetry`, `partner_integration`, `confirmed_service_outcome`, `community_report` — describe event or observation provenance, not documents, so an evidence record with one of those types cannot satisfy its own schema (a live telemetry event has no edition or URL).
- **Proposed change:** Split the enums: keep the §3.2 event-provenance enum for observations, and give §4.1 evidence records a document-oriented `source_type` (e.g. `oem`, `regulator`, `standard`, `vendor_manual`, `operator`) plus a `non_document`/`derived` value with its own provenance fields. State explicitly which §4.1 fields are optional for non-document sources.
- **Evidence:** reasoning only (spec-internal: §3.2 `source_type` enum vs §4.1 evidence fields).
- **Confidence:** medium

### DEEPSEEK-5 · §4.3 `station_observations` restates an observation shape with different field names

- **Section:** §3.2, §4.3
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 declares there is exactly one observation record and that sections 3, 4, 9, and 11 refer to it with no restatement, yet §4.3 defines `station_observations` with its own columns — `source` and `quality` instead of `source_type`/`source_reference`, and no `clock_source`/`observed_at_precision`. This is either a second observation shape or an unnamed derived table, and an implementer cannot tell which.
- **Proposed change:** Either make `station_observations` an instance of the canonical §3.2 record (reusing `source_type`, `source_reference`, and the clock fields), or explicitly label it a derived/aggregated station-status table with its own defined semantics and state how it relates to the canonical record.
- **Evidence:** reasoning only (spec-internal: §3.2 "no section restates it" vs §4.3 `station_observations`).
- **Confidence:** medium

### DEEPSEEK-6 · Deterministic conclusions are not pinned through the LLM validator

- **Section:** §9.1, §9.2
- **Type:** gap
- **Severity:** minor
- **Finding:** The deterministic input supplies `decision_status` and `candidates` (§9.1), and the LLM is only meant to explain those structured findings, yet §9.2 re-requires `decision_status` and `ranked_causes` as output without any validator invariant asserting they equal the deterministic values and order. An LLM that flips the status, drops a cause, or reorders the list passes every listed invariant, so the deterministic conclusions are not actually pinned through the LLM.
- **Proposed change:** Add to the machine-checkable invariants: output `decision_status` must equal the deterministic evaluation's status, and `ranked_causes` must be exactly the deterministic list (same `cause_id`s, same order). Any deviation is a validation failure that falls back to the deterministic explanation.
- **Evidence:** reasoning only (spec-internal: §9.2 invariant list omits any equality check against the §9.1 deterministic `decision_status`/`candidates`).
- **Confidence:** high

---

## Top 3

1. **DEEPSEEK-6** — pin `decision_status` and cause order through the LLM validator so the LLM cannot silently override deterministic conclusions.
2. **DEEPSEEK-2** — settle the single shape of `protocol_version`; every protocol observation and mapping key depends on it.
3. **DEEPSEEK-1** — fix the tie-handling sort key so ranking is actually deterministic as claimed.

Result: complete
