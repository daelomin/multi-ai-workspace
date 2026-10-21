# DEEPSEEK review — round 4

**Specification:** local `spec.md`, v0.5, dated 21 October 2026.
**Reviewer:** DEEPSEEK. **Review date:** 2026-10-21.
**Method:** Read the round-3 CHATGPT, DEEPSEEK and GROK reviews and `reviews/round-3/CONSOLIDATION.md`, then `decisions.md` and the current local spec; also read the round-4 CHATGPT review so my findings are non-overlapping. All findings are spec-internal ("reasoning only"); no external source was re-fetched, and no error code, recall number or standard clause is invented. FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are settled by HUMAN and are not reopened. The open items carried forward (FB-D4, FB-D6, FB-D1a–c, FB-D2a, FB-D5a) are not re-raised. I agree with the round-3 dispositions, including the partial on DEEPSEEK-2, and with round-4 CHATGPT-1 (stage outcomes), CHATGPT-2 (point projection and availability) and CHATGPT-3 (restriction composition); I do not repeat them.

**Overall:** 0 blocking, 0 major, 6 minor findings. The round-3 corrections and the settled HUMAN decisions are applied consistently, and the safety policy is materially sounder than in v0.4. The remaining findings are contract and schema details: one makes a stated release-gate check unenforceable, and the rest leave an implementer to invent a representation. None is unsafe guidance and none reopens a settled decision.

---

### DEEPSEEK-1 · The safety-state vocabulary and its ordering are undefined

- **Section:** §5, §9.1, §9.2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** §9.1 supplies a safety token (`"state": "no_blocking_hazard_observed"`) and §9.2 requires `safety_state` in the output and makes "`safety_state` is monotonic and not contradicted" a machine-checkable invariant, but no section defines the set of states or their order. §5's "typed safety state" is an object of `rule_ids`, affected scope, `observation_ids` and clearance conditions, not a state value, so the LLM input and output tokens have no canonical source and "monotonic" cannot be evaluated. An implementer must therefore invent both the vocabulary and the ordering behind a release-gate check.
- **Proposed change:** Add to §5 a closed `safety_state` enum with a documented partial order from least to most restrictive, derived from the typed state object and set only by the safety engine; state that a later observation or an LLM response can never make it less restrictive without an authorized clearance under the existing rules. Proposed labels for review (the consolidator may replace them): `normal`, `no_blocking_hazard_observed`, `hazard_reported`, `restricted`, `emergency`; the prohibition is on weakening, not on the exact labels. Carry the same enum in §9.1/§9.2 and add a §12 fixture: an LLM response that lowers the state is rejected and the deterministic state is preserved.
- **Evidence:** reasoning only; §5 typed safety state versus §9.1 `state` and §9.2 `safety_state`/monotonicity.
- **Confidence:** high

### DEEPSEEK-2 · The outcome record contradicts the single-observation rule and the `outcome` type

- **Section:** §3.2, §11
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 says "There is exactly one observation record. Sections 3, 4, 9, and 11 refer to this definition; no section restates it", and its `observation_type` enum includes `outcome`. §11 then defines a separate "outcome record" (`cause_id`, supporting and contradicting `observation_ids`, `confirmation_quality`, `actor`, `evidence_ids`) that lacks the §3.2 required fields (`observation_id`, `session_id`, `subject_type`/`subject_id`, `source_type`, `source_reference`, `quality`, `received_at`) and renames `quality` to `confirmation_quality`; its own `/outcomes` endpoint reinforces the separate-record reading. Either reading is implementable, but the spec currently asserts both.
- **Proposed change:** Choose one and state it. If outcomes are observations: keep `observation_type = outcome`, define a typed outcome payload with those fields, reuse the §3.2 `quality` field, and route them through the observations endpoint. If they are a separate record: remove `outcome` from `observation_type`, change §3.2's claim so §11 is the stated exception rather than a section that "refers to this definition", and keep the `/outcomes` endpoint with `confirmation_quality` as its own field (or rename it `quality`). Add a fixture that the chosen path stores and retrieves an outcome with the same provenance requirements as other evidence.
- **Evidence:** reasoning only; §3.2 field table and single-record rule versus §11 outcome fields and endpoint.
- **Confidence:** high

### DEEPSEEK-3 · A `VEHICLE_DTC` observation cannot carry the ECU the mapping key needs

- **Section:** §3.2, §4.4, §4.5, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.4's `dtc_codes` requires "Issuer, ECU, code, version, and confirmed meaning" and §4.5 scopes `VEHICLE_DTC` to "the OEM/ECU", but the §3.2 observation has no ECU field: `issuer` is the standard body, vendor, OEM or operator, and `component`, `variable` and `tech_code` are null outside OCPP 2.x device-model events. The §4.5 mapping key therefore cannot separate two ECUs on one vehicle that publish the same numeric code, and §12's Error scope fixture only checks collisions across issuers. This is a field gap in the record §3.2 says every section uses, not a request for a new code.
- **Proposed change:** Add an `ecu` string field to §3.2, required when `namespace = VEHICLE_DTC` and null otherwise, and add it to the §4.5 mapping key; or, if the intent is that `issuer` carries the ECU for this namespace, say so explicitly in §3.2 and §4.5 and describe it as part of the key. Add a §12 Error scope fixture with the same numeric DTC reported by two ECUs on one vehicle: the mappings must not collide, and a mapping without an ECU must not match a `VEHICLE_DTC` observation.
- **Evidence:** reasoning only; §4.4 `dtc_codes`, §4.5 `VEHICLE_DTC` and namespace nullity, §3.2 field list, §12 Error scope.
- **Confidence:** high

### DEEPSEEK-4 · `plug_and_charge` is not rejected for profiles whose table says authorization cannot occur

- **Section:** §3.3, §12
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** `plug_and_charge` is defined as the method where the protocol `authorization` stage carries the contract exchange, and the `din70121` row explicitly forbids it, but the `iec61851_pwm_only` and `chademo` rows mark protocol authorization `not_applicable` without forbidding the method; only the §12 Stages fixture checks the DIN case. The session record can therefore hold a combination its own profile table says cannot occur. The same paragraph defines the `external_authorization` event for `rfid`, `app` and `ad_hoc_payment` but not for the `free` and `unknown` enum values.
- **Proposed change:** Add a profile/method consistency rule: `plug_and_charge` is allowed only with `iso15118`; it is rejected for `iec61851_pwm_only`, `chademo` and `din70121`; when the profile is `unknown`, preserve the combination as unknown rather than assuming. For `free`, state that no `external_authorization` event is required; for `unknown`, do not infer one. Extend the §12 Stages fixture to cover the PWM-only and CHAdeMO rejections and a `free` session.
- **Evidence:** reasoning only; §3.3 `authorization_method` definition and profile rows, §12 Stages.
- **Confidence:** high

### DEEPSEEK-5 · The `contradicting` ranking term cannot use the evidence-group identity that `supporting` uses

- **Section:** §3.2, §4.1, §6.2, §12
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** `supporting` is a sum over "distinct evidence groups" whose identity is `incident_id` on §4.1 evidence records, while `contradicting` is "the same function over contradicting observations". Observations have no `incident_id` (they carry `conflict_group_id`), and the function's `reliability_weight` is a source/evidence property, so the round-3 dedup fix applies to support only and two copied or incident-linked contradicting reports can reduce a cause's score twice. "The same function" is not executable as written.
- **Proposed change:** Define `contradicting` over the same evidence-group identity as `supporting` (group the evidence behind each contradicting observation), or give observations an incident-group reference and name it as the dedup key; state that `conflict_group_id` groups mutually conflicting observations and is not the incident-dedup key. State that a copied contradicting report adds one group contribution, and define where the reliability and quality weights come from for observations. Add the symmetric §12 fixture: two contradicting documents with different URLs and versions linked to one `incident_id` add one contradiction contribution, not two.
- **Evidence:** reasoning only; §6.2 `supporting`/`contradicting`, §4.1 `incident_id`, §3.2 observation fields.
- **Confidence:** high

### DEEPSEEK-6 · `unsupported_scope` has no specified response behaviour

- **Section:** §1.1, §5, §6.2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** §1.1 requires the supported-scope manifest to state "what general guidance remains available *outside* that scope" and says out-of-manifest requests resolve to `unsupported_scope`, but §6.2 defines that status only as a condition and gives `insufficient_evidence` an output contract (approved questions/escalation) without giving one to `unsupported_scope`. §5 runs safety independently and §12 requires decision statuses to "behave as specified", yet no section says whether an `unsupported_scope` response still shows safety/restriction content, returns the manifest's general guidance as approved actions/questions, or what the validator permits. The promised general guidance has no delivery path, and an implementer must invent the response.
- **Proposed change:** Add to §6.2: a response with `decision_status = unsupported_scope` still runs and displays the §5 safety evaluation and any applicable restriction; it returns the manifest's declared general guidance as approved questions/actions and escalation, states which manifest entry is missing or unsupported, and must not be presented as `supported_hypothesis` or as a cause-specific playbook. Add a §12 fixture for an out-of-manifest configuration. This defines the response contract only; it does not choose which countries or configurations are in scope.
- **Evidence:** reasoning only; §1.1 supported-scope manifest, §5, §6.2 decision-status table, §12 Ranking.
- **Confidence:** high

---

## Top 3

1. **DEEPSEEK-1:** define the safety-state vocabulary and its ordering, so the §9.2 monotonicity check and the §12 safety gate are implementable rather than invented per client.
2. **DEEPSEEK-5:** apply the `incident_id` evidence-group identity to contradictions as well as support, so the round-3 dedup fix is symmetric and copied reports cannot double-penalise a cause.
3. **DEEPSEEK-3:** give `VEHICLE_DTC` observations an ECU field and add it to the §4.5 mapping key, so DTCs from different ECUs on one vehicle cannot collide.

FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are settled and not reopened. FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a remain open HUMAN items; I have no new evidence on them, so I do not comment on them.

Result: complete
