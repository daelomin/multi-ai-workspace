# CHATGPT review — round 3

**Specification:** local `spec.md`, v0.4, dated 14 October 2026.  
**Reviewer:** CHATGPT. **Review date:** 2026-10-21.  
**Method:** Read the round-2 CHATGPT, DEEPSEEK and GROK reviews and `CONSOLIDATION.md` before the current local spec; also read `decisions.md`. This review checks internal contracts through reasoning only and does not independently verify standards, vehicle, recall or legal claims.

**Overall:** 0 blocking, 0 major, 3 minor findings. The round-2 major fixes are present. FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are treated as settled by HUMAN; their remaining pending-decision passages are not reviewed. FB-D4, FB-D6 and the outstanding HUMAN parameters are not reopened. The findings below require neither new policy decisions nor a change to the settled ranking approach.

### CHATGPT-1 · Preserve deterministic evaluation results through output validation

- **Section:** §6.1, §6.2, §9.1, §9.2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** The ranking engine decides `decision_status`, candidate order and evidence strength before the LLM runs, but §9.2 validates candidate membership without explicitly requiring those returned fields to match the evaluation. An output could use only supplied cause IDs while reversing their order or changing `insufficient_evidence` to `supported_hypothesis`; the enumerated machine checks do not explicitly reject either mutation. The general prohibition on unsupported diagnoses provides the intended boundary, but a simple equality contract would make it directly enforceable.
- **Proposed change:** Add: "The response renderer copies `decision_status`, its reasons, ranked cause IDs in their evaluated order, and per-cause and evaluation-level evidence strength from the current deterministic evaluation. These are authoritative fields, not LLM decisions. If the LLM output includes them, the validator requires exact equality; a mismatch uses the deterministic fallback. Narrative omissions cannot change the authoritative ranked list or abstention state." Add fixtures returning valid supplied cause IDs in reversed order and changing an abstention status; both must preserve the evaluated response through rejection/fallback.
- **Evidence:** reasoning only; local §6.1 steps 9–10 and §6.2 assign these decisions to the ranking engine, while §9.2 lists membership and safety checks without equality checks for these fields.
- **Confidence:** high

### CHATGPT-2 · A shared incident still counts separately across source documents

- **Section:** §4.1, §6.2, §12
- **Type:** error
- **Severity:** minor
- **Finding:** Round-2 D11 defines `incident_id` to group documents describing the same real-world failure so that they count once, but the composite deduplication key still includes `source_url` and `document_version`. Records `(URL-A, v1, incident-X)` and `(URL-B, v1, incident-X)` therefore remain distinct groups even when their shared incident is known, allowing copied reports to increase support. Adding the incident field resolved the undefined identifier, but the merged grouping rule does not yet implement its stated purpose.
- **Proposed change:** Replace the deduplication rule with: "For records with a non-null `incident_id`, the evidence-group identity is that incident ID, independent of source URL and document version. For a null `incident_id`, the record is its own incident, identified by `evidence_id`. Preserve source and document metadata as provenance; they do not split a known shared incident. The ranking policy defines aggregation within each group for supporting and contradicting evidence." Add a fixture with two different URLs and document versions linked to one incident; the second document must not add an independent evidence-group contribution.
- **Evidence:** reasoning only; local §4.1's `incident_id` meaning versus the §6.2 composite grouping key. This is a remaining defect in D11's merged text, not a request to add the already-defined field again.
- **Confidence:** high

### CHATGPT-3 · Station-state projection still introduces undefined canonical fields

- **Section:** §3.2, §4.3, §6.4
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Round-2 D12 now calls `station_observations` a projection of the canonical record, but it includes `operational_state`, `available_power_kw` and `power_sharing_state`, none of which §3.2 defines. The numeric `value` field can represent available power through the measurement catalog, but the spec does not identify that binding or a typed representation for the two state values. Calling the table a projection therefore leaves the same representational choice unresolved, although it is a routine schema clarification rather than a reason to block implementation.
- **Proposed change:** Add to §3.2 a typed station-status payload with versioned `operational_state` and `power_sharing_state` vocabularies, including unknown values. Define `available_power_kw` in §4.3 as a derived alias of a canonical `measurement` observation whose catalog kind means available station allocation, with unit kW and the required subject, location and temporal qualifiers. State that §4.3's projection resolves those status and measurement observations by their IDs and retains each value's own provenance and timestamp; it does not store an independent competing state.
- **Evidence:** reasoning only; local §3.2's single-record rule and field list versus §4.3's projection and §6.4's station-allocation input. This narrows the remaining defect in D12's merged representation.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Keep abstention, ranking order and evidence strength authoritative through LLM validation.
2. **CHATGPT-2:** Make a shared incident count once even when multiple source documents describe it.
3. **CHATGPT-3:** Give station state and available allocation an explicit canonical representation.

Result: complete
