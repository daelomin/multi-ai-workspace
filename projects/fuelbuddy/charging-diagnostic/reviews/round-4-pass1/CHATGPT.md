# CHATGPT review — round 4

**Specification:** local `spec.md`, v0.5, dated 21 October 2026.  
**Reviewer:** CHATGPT. **Review date:** 2026-10-21.  
**Method:** Read the round-3 CHATGPT, DEEPSEEK and GROK reviews and `CONSOLIDATION.md` before the local spec; also read `decisions.md`. This review uses internal reasoning only. External standards, vehicle, recall and legal claims were not independently re-verified.

**Overall:** 0 blocking, 0 major, 3 minor findings. The authoritative evaluation fields, incident deduplication and measurement catalog changes address the corresponding round-3 findings. FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are fixed HUMAN decisions; FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a are not reopened. The findings below concern remaining schema details in the merged text, not the accepted policies or deferred vocabulary values.

### CHATGPT-1 · Stage events do not distinguish success from failure

- **Section:** §3.2, §3.3, §6.1 step 2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** The new session model derives the last successful stage from `session_stage_event` observations, but their only defined stage-specific field is `stage`. An event about `authorization` can describe entry, success or failure; `quality` describes confirmation rather than the stage outcome, so the canonical fields do not distinguish these cases. This is the remaining event-outcome detail explicitly deferred in round-3 consolidation §4, rather than a request to add the already-merged session record again.
- **Proposed change:** Add a typed `stage_outcome` field required for `session_stage_event`, with values `entered`, `succeeded`, `failed`, `unknown`. State: "Derive the last successful stage only from effective `succeeded` events for the relevant attempt and applicable profile; an entered, failed or unknown event does not establish success. Where attempt identity, event order or conflicting reports prevent a unique derivation, preserve uncertainty and ask for clarification rather than inferring success." Add a fixture distinguishing entry, failure and success at the same stage and keeping separate attempts apart.
- **Evidence:** reasoning only; the local canonical field list and §3.3 derivation rule, plus the explicit round-3 consolidation deferral.
- **Confidence:** high

### CHATGPT-2 · The station projection still forces every subject into a connector ID

- **Section:** §3.2, §4.3, §12, §14
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §14 and the new §12 station-status fixture correctly retain point status on a `recharging_point` subject, but §4.3 still defines `station_observations` with `connector_id` as `subject_id`. That projection cannot expose the new point observation without omitting it or relabelling its subject, contrary to the point-versus-connector distinction just accepted. The canonical record already supports the correct identity, so this needs a projection correction rather than a new policy or source claim.
- **Proposed change:** Replace `connector_id` in the §4.3 projection with the canonical `subject_type` and `subject_id`. Add: "A connector-specific convenience view may expose `connector_id` only for observations whose subject is that connector. Point observations retain their point ID; any point-to-equipment association is an explicit identity mapping with provenance, and does not create independent connector observations. Unknown associations remain unresolved." Extend the existing station-status fixture to read the point observation through this projection without relabelling it.
- **Evidence:** reasoning only; local §4.3 projection versus §3.2's subject enum and §14's explicit no-copy rule. This is a remaining inconsistency in round-3 D1/D6's merged text.
- **Confidence:** high

### CHATGPT-3 · Availability has literals and a field path but no typed payload binding

- **Section:** §3.2, §12, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** §14 requires operational status and availability to be stored as `station_status` observations with distinct field paths, but §3.2's typed payload defines only `operational_state` and `power_sharing_state`. A `field_path` locates a source value; it does not specify which typed canonical member holds availability, leaving consumers to invent a member or parse `raw_code`/`raw_text`. The already-deferred vocabulary values need not be chosen to resolve this structural omission.
- **Proposed change:** Add a nullable typed `availability_state` member to the §3.2 station-status payload, governed by a versioned vocabulary including `unknown` and bound to the release manifest. State: "The §14 operational-status field maps to `operational_state`; its availability field maps to `availability_state`. Preserve the source literal and field path as provenance, and use `unknown` for an unmapped value. Availability is not a power-sharing state." Add a fixture holding operational status and availability independently for one point, with each observation's own timestamp and provenance.
- **Evidence:** reasoning only; local §14's required two status dimensions versus the exhaustive named members of the §3.2 typed payload. No external interpretation of the source literals is asserted.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Record stage outcome so the last successful stage can be derived without guessing.
2. **CHATGPT-2:** Preserve point identity through the station-observation projection.
3. **CHATGPT-3:** Give availability an explicit typed payload binding.

Result: complete
