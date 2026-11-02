# CHATGPT review — round 2

**Specification:** local `spec.md`, v0.3, dated 11 October 2026.  
**Reviewer:** CHATGPT. **Review date:** 2026-10-14.  
**Method:** Read the round-1 CHATGPT, CLAUDE and DEEPSEEK reviews and `CONSOLIDATION.md` before reviewing the current local spec. This review checks the merged contracts through internal reasoning; external sources were not re-verified. The archived round-2 first-pass reviews were not read.

**Overall:** 0 blocking, 1 major and 4 minor findings. The accepted round-1 direction is retained. Findings below identify remaining defects in the merged text rather than repeat the original requests. FB-D1–FB-D7 remain HUMAN decisions; no new evidence warrants reopening them here.

### CHATGPT-1 · Canonical measurements lack quantity identity and qualifiers

- **Section:** §3.2, §6.4, §10, §12
- **Type:** gap
- **Severity:** major
- **Finding:** The canonical record distinguishes only `observation_type = measurement`, with numeric `value`, `unit` and a subject; it has no typed quantity identifier. Two vehicle measurements in degrees Celsius therefore cannot distinguish battery temperature from ambient temperature, and two power measurements cannot encode measurement location or averaging window even though §6.4 requires those distinctions. C1 and C8 added identity and a model interface, but the merged schema still cannot represent the inputs needed for a correct slow-charging comparison without inventing an additional contract or interpreting free text.
- **Proposed change:** Add: "Measurement observations require a versioned `measurement_kind` identifying the quantity. The catalog defines allowed units, subject types, required qualifiers and model-input bindings for each kind. Power observations carry `measurement_location`, `aggregation_kind` and, for averages, `window_start`/`window_end`; temperature observations distinguish battery and ambient quantities explicitly. Unknown required qualifiers remain unknown and make the relevant comparison insufficient evidence. These fields are part of the §3.2 canonical record; raw text is not their authoritative substitute." Require a fixture with two temperatures sharing the same subject/unit and with instantaneous and averaged power at different locations; validate that they cannot be substituted for one another.
- **Evidence:** reasoning only; local §3.2 measurement fields versus §6.4 measurement contract and §10 instantaneous/averaged-power distinction.
- **Confidence:** high

### CHATGPT-2 · Make the safety pass after matching explicit

- **Section:** §2, §4.4, §5, §6.1, §12
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The graph and numbered sequence evaluate safety before configuration resolution and retrieval of applicable errors/issues, although those later steps can discover linked safety rules or campaign restrictions. §5 already requires safety evaluation during final validation, so this is not an established permission bypass; the remaining ambiguity is when newly matched restrictions reach action selection. C10's rule links are useful, but the processing sequence should show their evaluation explicitly.
- **Proposed change:** Add after §6.1 step 6: "Evaluate the safety rules linked to newly matched errors, issues and applicable campaigns using the resolved context, independently of candidate ranking. Refresh the typed safety state before selecting questions, playbooks or actions. Final validation checks permissions against that refreshed state." Add the corresponding graph edge and a fixture where only knowledge matching identifies an applicable approved restriction; both normal and fallback output must honor it. This changes processing order, not the pending FB-D2 restriction/clearance policy.
- **Evidence:** reasoning only; local §6.1 steps 3–6, §4.4 safety-rule links and §5 final safety evaluation.
- **Confidence:** high

### CHATGPT-3 · Supersession definition can mark the successor obsolete

- **Section:** §4.1
- **Type:** error
- **Severity:** minor
- **Finding:** The merged definition says a record is superseded if "`supersedes_id` points at it, or it is referenced as such", leaving the direction of the relation ambiguous. In a revision B with `B.supersedes_id = A.id`, B supersedes A; B is not itself superseded merely because it contains a non-null pointer. C20's removal of a redundant status is retained, but its derived-state rule needs an unambiguous definition to avoid invalidating the new record with the old one.
- **Proposed change:** Replace the parenthetical with: "For B with `B.supersedes_id = A.id`, A is the predecessor and B is the successor. A is superseded for production activation only when an approved successor B is activated under the release policy; B's non-null pointer does not make B superseded. An unapproved draft successor does not deactivate A. Reject self-links and cycles." Require a fixture showing A remaining active while B is under review, then B replacing A on activation.
- **Evidence:** reasoning only; local §4.1 `supersedes_id`, approval requirement and dependency-aware activation.
- **Confidence:** high

### CHATGPT-4 · Ranking policy still needs a complete reproducibility contract

- **Section:** §6.2, §12, §13
- **Type:** gap
- **Severity:** minor
- **Finding:** C6 added ranges and a supporting-evidence formula, but `specificity` still lacks a function, `uncertainty` lacks its proportionality rule, and no worked example appears despite the consolidation recording one. Tie handling sorts by the evaluation-level `decision_status`, which is identical across candidates, and does not specify score direction; evidence-strength labels also lack decision rules. These can be supplied as implementation policy without reopening FB-D7's choice of ranking approach, but the spec should require that policy before the corresponding release gate passes.
- **Proposed change:** Add: "Each ranking-policy version defines the reliability/quality tables, within-group aggregation, specificity function, missing-discriminator normalization, evidence-strength rules, and precedence among decision statuses. Within an evaluation, sort by descending score and then ascending stable `cause_id`; any additional ordinary-cause ordering follows the approved FB-D7 policy. Before enabling ranking in a release, bind the complete policy to the release manifest and provide a fixture with at least three candidates, including a tie, missing inputs and contradictory evidence, with exact expected scores, labels and ordering. Pilot-derived thresholds remain separately versioned." Do not insert guessed weights or thresholds.
- **Evidence:** reasoning only; local §6.2 definitions and round-1 consolidation C6/C7/C26.
- **Confidence:** high

### CHATGPT-5 · Example A conflates campaign applicability with fault symptoms

- **Section:** §4.4, §8 example A
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Example A says ICCU campaign applicability can be checked through `vehicle_campaign_status`, "but it is established through vehicle warnings and low-voltage symptoms". The antecedent is campaign applicability, which §4.4 treats separately from evidence of a current component fault. C15/C16 correctly separated those concepts elsewhere; this sentence can still teach an implementation to use symptoms as campaign eligibility evidence.
- **Proposed change:** Replace the sentence with: "Check campaign applicability and per-vehicle status using the campaign's authoritative eligibility criteria and campaign-specific evidence. Vehicle warnings and low-voltage symptoms can support investigation of a current ICCU-related fault hypothesis; they do not establish campaign applicability or an open campaign. A generic station error establishes neither." This wording asserts no new campaign scope or diagnostic fact.
- **Evidence:** reasoning only; local §4.4 per-campaign recall state versus §8 example A wording.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Give measurements typed quantity identities and the qualifiers required by the charging-model interface.
2. **CHATGPT-2:** Explicitly evaluate safety restrictions discovered during knowledge matching before action selection.
3. **CHATGPT-3:** Define supersession direction and activation so a successor remains usable.

Result: complete
