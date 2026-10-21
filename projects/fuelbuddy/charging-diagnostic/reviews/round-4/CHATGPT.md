# CHATGPT review — round 4

**Specification:** local `spec.md`, v0.5, dated 21 October 2026.  
**Reviewer:** CHATGPT. **Review date:** 2026-10-21.  
**Method:** Read the round-3 CHATGPT, DEEPSEEK and GROK reviews and `CONSOLIDATION.md` before reviewing the current local spec; also read `decisions.md`. Findings use internal reasoning only. No external standard, vehicle, recall, product or legal claim is independently re-verified here.

**Overall:** 0 blocking, 0 major, 3 minor findings. The round-3 corrections are present; the findings below concern remaining representation and composition details. FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 remain fixed. Open FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a are not reopened. I agree with the previous consolidation's dispositions, subject to the remaining station-projection mismatch described below.

### CHATGPT-1 · Stage events need an outcome to derive the last successful stage

- **Section:** §3.2, §3.3, §6.1 step 2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** The new `stage` field identifies which stage an event concerns, but neither it nor the minimal session record distinguishes entry, success and failure. Consequently, a `session_stage_event` naming `authorization` can describe either successful authorization or the failure being investigated, while §3.3 requires the last successful stage to be derived from these events. This is the outcome detail explicitly left unspecified in the round-3 consolidation, rather than a request to add the already-merged stage field again.
- **Proposed change:** Add a typed `stage_outcome` to `session_stage_event`, with values `entered`, `succeeded`, `failed`, `unknown`; unspecified outcomes remain `unknown`. State: "Only an effective event with `stage_outcome = succeeded` establishes stage success. Derive the last successful stage for the current attempt using the applicable profile and clock rules; do not infer success merely from the presence of a stage event or inherit it from a previous attempt. If attempt membership or ordering cannot be resolved, preserve uncertainty." Add a fixture with a successful authorization in attempt A and failed authorization in attempt B; attempt B must not inherit A's success.
- **Evidence:** reasoning only; local §3.2 stage field and §3.3 derived-success requirement; round-3 consolidation §4 explicitly leaves stage success/failure unspecified.
- **Confidence:** high

### CHATGPT-2 · The station projection still excludes the new point subject and availability payload

- **Section:** §3.2 station-status payload, §4.3, §12, §14
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §14 now correctly requires storing point operational status and availability separately on a `recharging_point` subject, but §4.3 still fixes the station projection to `connector_id` as `subject_id`. In addition, the typed §3.2 station-status payload defines `operational_state` and `power_sharing_state` without a typed availability field, leaving §14's availability tokens to an unspecified payload location. The merged point-level rule is clear, but the projection and payload need to carry it without relabeling a point as a connector or conflating availability with operational state.
- **Proposed change:** Replace the projection's fixed `connector_id` identity with the underlying `subject_type` and `subject_id`; retain connector resolution only when a documented identity relation supports it, never by copying point observations. Add a nullable typed `availability_state` to the station-status payload, with its versioned vocabulary and source-field binding in the release manifest, separate from `operational_state` and `power_sharing_state`. Define §14's availability field path as resolving to that payload member. Extend the station-status fixture with one point having multiple connectors and independent operational-status and availability observations; the projection must preserve the point subject and both values' provenance.
- **Evidence:** reasoning only; local §14's existing point-subject and separate-status requirements versus §4.3's fixed connector projection and §3.2's payload members. This checks internal representation and does not reassert external AFIR claims.
- **Confidence:** high

### CHATGPT-3 · Define how restrictions with different dimensions compose

- **Section:** §5 restriction mapping and scope, §4.7, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** The settled rule says the most restrictive restriction wins, but `charge_limited` and `do_not_charge_indoor` need not be ordered: one can limit charging conditions while the other limits location. Selecting either restriction alone could discard a condition imposed by the other. The existing requirement supports a conservative implementation; specifying intersection would remove ambiguity without changing HUMAN's policy or approved instructions.
- **Proposed change:** Add: "For simultaneously applicable restrictions, an action is permitted only if every restriction permits it. `do_not_charge` (including unmapped values) permits no charging action; otherwise retain all applicable limits and approved warnings rather than choosing one enum value. Evaluate each restriction against its own subject scope. If no approved action satisfies the combined conditions, return approved escalation guidance." Add a fixture combining an approved limited-charging instruction with an outdoor-only restriction, and verify that neither condition is dropped.
- **Evidence:** reasoning only; local §5's 'most restrictive wins' rule and restriction-to-behaviour table. This specifies composition under settled FB-D2 and does not propose a different clearance or scope policy.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Record stage outcomes so last-successful-stage derivation does not mistake a failure event or a previous attempt for success.
2. **CHATGPT-2:** Carry point identity and separate availability through the canonical payload and station projection.
3. **CHATGPT-3:** Intersect applicable restriction permissions and retain every applicable condition.

Result: complete
