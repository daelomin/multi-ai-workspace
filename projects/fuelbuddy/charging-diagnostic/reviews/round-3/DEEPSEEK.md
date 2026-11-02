# DEEPSEEK review — round 3

**Specification:** local `spec.md`, v0.4, dated 14 October 2026.
**Reviewer:** DEEPSEEK. **Review date:** 2026-10-21.
**Method:** Read the round-2 reviews (CHATGPT, DEEPSEEK, GROK) and `CONSOLIDATION.md`, then `decisions.md` and the current local spec; also read the round-3 CHATGPT review so my findings are non-overlapping. All findings are spec-internal ("reasoning only"); no error code, recall number, or standard clause is invented, and no external source was re-fetched. FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are settled by HUMAN and are not reopened; FB-D4 and FB-D6 remain open and I have no new external evidence on them, so they are not re-raised.

**Overall:** 0 blocking, 0 major, 3 minor findings. The round-2 major fixes are present and correct in v0.4. I agree with the round-2 dispositions and have no disagreements to record. I also endorse the round-3 CHATGPT findings (CHATGPT-1, -2, -3); CHATGPT-2's incident-dedup point is the strongest of the round. My three findings below are the remaining internal-consistency and schema gaps the new v0.4 text still leaves open; none is unsafe or unimplementable, but each would slow an implementer.

---

### DEEPSEEK-1 · The session-stage model has no field in the canonical record and no session schema

- **Section:** §3.2, §3.3 (also §4.5, §6.1, §12)
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.3 requires recording a stage: the stage list, the new `external_authorization` event, and the session fields `communication_profile` and `authorization_method` ("Session records MUST carry a `communication_profile`"). But §3.2's canonical observation record has no `stage` field, `observation_type = session_stage_event` has no defined payload, and no session schema is defined anywhere in the document. An implementer following §3.2's "exactly one observation record, no section restates it" rule has no place to store the stage that §4.5 error mappings ("session stage"), §6.1 step 2 ("last successful stage") and the §12 Stages fixture all depend on, and no place to distinguish `external_authorization` from the protocol `authorization` stage.
- **Proposed change:** Add a `stage` field to the §3.2 record, carried by `session_stage_event` observations, whose enum is the §3.3 stage list plus `external_authorization` and `not_applicable`; or define a minimal session record holding `communication_profile`, `authorization_method`, and the last-successful-stage. State that `external_authorization` is recorded as a `session_stage_event` with `stage = external_authorization`, distinct from the protocol `authorization` stage.
- **Evidence:** reasoning only; §3.2 field list versus §3.3/§4.5/§6.1/§12.
- **Confidence:** high

### DEEPSEEK-2 · `measurement_kind` and `measurement_location` both encode the charger-vs-vehicle distinction

- **Section:** §3.2, §6.4
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2's `measurement_kind` description gives "charger-side power versus vehicle-side power" as an example of a *kind*, while `measurement_location` (`vehicle_reported`, `charger_reported`, `meter`) and §6.4 assign the same charger-vs-vehicle distinction to *location*. The measurement-identity rule ("different kinds, locations, or aggregations MUST NOT be substituted") treats them as separate axes, but the spec never says whether charger-side and vehicle-side power are one quantity at two locations or two different quantities. §6.4's rule "charger output and battery-reported power MUST NOT be compared as though they measured the same quantity" depends on that answer.
- **Proposed change:** Reserve `measurement_kind` for the physical quantity (e.g. AC charger output power vs DC battery-input power) and `measurement_location` for the reporting point, and state that a valid power comparison requires equal kind *and* equal location. Remove "charger-side power versus vehicle-side power" from the `measurement_kind` example if that split is meant to be a location distinction rather than a kind distinction.
- **Evidence:** reasoning only; §3.2 `measurement_kind`/`measurement_location` definitions versus §6.4's measurement contract.
- **Confidence:** medium

### DEEPSEEK-3 · The versioned `measurement_kind` catalog is referenced but never defined

- **Section:** §3.2, §6.4, §12, §13
- **Type:** gap
- **Severity:** minor
- **Finding:** §3.2 makes `measurement_kind` "a versioned catalog id" whose catalog "fixes the allowed units, subject types, required qualifiers, and the charging-model inputs (§6.4) it may feed", and §6.4 consumes those bindings. No section defines the catalog's schema, versioning, provenance, approval, or where it lives; §13's "narrow approved catalog" is ambiguous and reads as the §4 knowledge catalog, not the measurement-kind catalog. Unlike the charging-model interface (§6.4), the action registry (§4.7) and the release manifest (§12), this required dependency has no definition or named deliverable.
- **Proposed change:** Add a short definition of the measurement-kind catalog (id, version, per-kind allowed units/subjects/qualifiers/model bindings, evidence, reviewer), name it in the §12 release manifest, and clarify in §13 that the evidence-foundation "approved catalog" includes it or is a separate catalog.
- **Evidence:** reasoning only; §3.2/§6.4 references versus §12/§13 deliverables.
- **Confidence:** medium

---

## Top 3

1. **DEEPSEEK-1:** give the session-stage model (`stage`, `external_authorization`, `communication_profile`, `authorization_method`) an actual field or session schema, so the §3.3 model is representable in the canonical record it forbids other sections from restating.
2. **CHATGPT-2 (endorsed):** make a shared `incident_id` count once even when multiple source documents describe the same failure — the current dedup key still splits it.
3. **DEEPSEEK-2 / CHATGPT-3 (endorsed):** clean up the overlapping `measurement_kind`/`measurement_location` axes and define the canonical representation of the station-state fields the §4.3 projection still introduces.

FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are settled and not reopened. FB-D4 and FB-D6 remain open HUMAN decisions; I have no new external evidence on either, so I do not comment on them.

Result: complete
