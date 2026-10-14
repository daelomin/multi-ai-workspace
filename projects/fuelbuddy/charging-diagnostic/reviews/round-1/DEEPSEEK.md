# DEEPSEEK review — round 1

**Specification:** FuelBuddy AI Charging Diagnostic System v0.2, 11 October 2026.
**Reviewer:** DEEPSEEK. **Date checked:** 2026-10-11.
**Method:** Independent review of the local `spec.md` v0.2; findings are derived from the spec itself. External protocol/standard knowledge is marked "reasoning only" and no error code, recall campaign number, or standard clause is invented. This review focuses on what would block or slow an implementation: schema/contract precision, reproducibility, testability, and efficient data modelling.

**Overall:** v0.2 is a disciplined baseline — it separates facts from hypotheses, puts safety before ranking, refuses unverified seed data, and restricts the LLM. The main problems for an implementer are *contract* problems rather than *policy* problems: the canonical observation record is defined three different ways (one of them carrying a broken enum value), the ranking formula is not reproducible, the safety engine has no defined link to issue severity or recall restrictions, and several schemas are missing the fields their own later sections require. There is **1 blocking, 9 major, and 5 minor** finding. The stop rule is not met.

---

### DEEPSEEK-1 · The observation record has three incompatible shapes and one broken enum value

- **Section:** §3.2, §4.1, §4.5, §9.1
- **Type:** inconsistency
- **Severity:** blocking
- **Finding:** Three sections describe a different observation shape. §3.2 requires `value`, `unit`, `source_type`, `source_reference`, `observed_at`, `received_at`, `quality`. §4.5's mapping key is `namespace + issuer + protocol_version + product_model + firmware_scope + raw_code`. §9.1's example observation carries `namespace`, `protocol_version`, `raw_code`, `source_type`, `quality` — omitting the §3.2 fields `observed_at`, `received_at`, `source_reference`, `value`, `unit` that §9.1's own note calls required. Separately, §9.1 sets `"source_type": "operator_integration"`, which is not a member of the §4.1 enum (`OEM`, `regulator`, `standard`, `vendor manual`, `operator`, `confirmed service outcome`, `community report`). An implementer cannot define the canonical observation table or API payload.
- **Proposed change:** Publish one observation schema. Recommended: keep the §4.5 mapping-key fields as the canonical record and add the §3.2 fields (`value`, `unit`, `observed_at`, `received_at`, `source_reference`, `quality`) to it; then make §3.2 and §9.1 reference that schema verbatim. Fix the §9.1 example to use `"source_type": "operator"` and to include `observed_at`, `received_at`, and `source_reference`. Add a JSON Schema for an observation and a test asserting that all three sections' examples validate against it.
- **Evidence:** spec-internal (§3.2, §4.1, §4.5, §9.1). reasoning only.
- **Confidence:** high

### DEEPSEEK-2 · Session stages are a single fixed order, but Plug & Charge authorizes after communication setup

- **Section:** §3.3
- **Type:** error
- **Severity:** major
- **Finding:** §3.3 lists `authorization` before `communication_setup` as one linear sequence and says to record "last successful stage" against it. For ISO 15118 Plug & Charge, authorization happens *after* communication setup and service selection; for RFID or app authorization it can precede plugging in. Recording against a single fixed order will mislocate failures and corrupt the "last successful stage" that ranking and safety key on.
- **Proposed change:** Model the stage sequence as a graph keyed by `authorization_method` (`rfid`, `app`, `plug_and_charge`, `ad_hoc_payment`, `free`, `unknown`), with a per-method stage order, and store `authorization_method` on the session. Interpret "last successful stage" relative to that method's order. Add a unit test asserting that, for `plug_and_charge`, `authorization` is not reachable before `communication_setup`.
- **Evidence:** reasoning only (ISO 15118-2 message sequence — contract authorization follows session setup and service selection; verify against the standard's sequence diagrams before encoding).
- **Confidence:** high on the principle, medium on exact message names.

### DEEPSEEK-3 · `charge_mode`, `authorization_method`, `supported_protocols`, and adapters have no shared vocabulary

- **Section:** §3.3, §4.2, §4.3, §6.4
- **Type:** gap
- **Severity:** major
- **Finding:** "Charging mode" appears as `charge_mode` (§4.2 `vehicle_connectors`, §4.3 `connectors`), as "charging mode" in §3.3's "whether another … charging mode was tested", and as AC/DC in §6.4, but no enum fixes the values or their relationship to `supported_protocols` and `supported_adapters` (both free-form). Without a shared enum, mode-based applicability and slow-charging logic cannot be joined reliably across the schema.
- **Proposed change:** Add a `charge_mode` enum (`ac`, `dc`, `wireless`, `unknown`) and an `authorization_method` enum (from DEEPSEEK-2). Enumerate `supported_protocols` against the §4.5 namespaces plus any in-scope `CHAdeMO`, `IEC 61851-1`, `SAE J3400`. Make `supported_adapters` a relation to connector records rather than free text, and reference these enums everywhere the words "mode" or "protocol" appear.
- **Evidence:** spec-internal (§3.3, §4.2, §4.3, §6.4). reasoning only.
- **Confidence:** high

### DEEPSEEK-4 · Vehicle schema cannot express the AC onboard-charger envelope that §6.4 and §4.6 need

- **Section:** §4.2, §4.6, §6.4
- **Type:** gap
- **Severity:** major
- **Finding:** §6.4's AC slow-charging analysis requires "vehicle onboard charger capability, supply phases/current", and §4.6 compares electrical ranges. `vehicle_variants` has `max_ac_kw` but no AC input voltage range, phase count, or max AC input current — so the AC path of both compatibility and slow-charge cannot be computed. The DC path is covered (`dc_input_voltage_min/max_v`); AC is not.
- **Proposed change:** Add to `vehicle_variants` (or a new `vehicle_obc` table): `ac_input_voltage_min_v`, `ac_input_voltage_max_v`, `ac_input_current_max_a`, `ac_phase_count`, `obc_power_kw`, linked to `supported_protocols`/`charge_mode`. Mirror the DC fields so AC and DC are symmetric.
- **Evidence:** spec-internal (§4.2 lists DC-only electrical fields; §6.4 names the AC inputs it needs). reasoning only.
- **Confidence:** high

### DEEPSEEK-5 · The "expected charging envelope" is an undefined external dependency

- **Section:** §6.4
- **Type:** gap
- **Severity:** major
- **Finding:** §6.4 defines slow charging by comparing observed power "against an expected envelope derived from the existing FuelBuddy charging model", but that model is neither specified nor linked here. "Derived" is ambiguous (table? curve? function?), so §6.4 cannot be implemented from this document.
- **Proposed change:** Either inline the envelope definition (inputs, formula, and the exact sources for vehicle charging curves), or add an explicit external reference with owner and version and mark §6.4 as blocked until it exists. At minimum state the envelope's inputs (SoC, temperature, mode, station constraints) and output (a power band over time), and add one worked numeric example.
- **Evidence:** spec-internal (§6.4). reasoning only.
- **Confidence:** high

### DEEPSEEK-6 · No rule links a known issue's severity or a recall to the safety engine

- **Section:** §4.4, §5, §6.1
- **Type:** gap
- **Severity:** major
- **Finding:** §4.4 gives issues a `severity` (`Critical`/`high`/`medium`/`low`) and recall records carry `instructions`/`remedy`, but §5's safety behavior keys on hazard observations (smoke, ground fault, …), not on issue severity. §6.1 step 3 says "evaluate safety and vehicle-specific restrictions" without saying how a known Critical issue or an open recall with a charging restriction becomes a restriction. A Critical known issue could therefore be ranked without ever affecting safety.
- **Proposed change:** Add a structured restriction field to the recall record (enum `none`, `do_not_charge`, `charge_limited`, `do_not_charge_indoor`, `other`, plus free text) and a rule mapping an issue's `severity`+`category` (or an explicit `safety_rule_ids` field on the issue) to safety-engine states. Require every active playbook/restriction to reference a safety rule; add a test that a `Critical` issue with a `do_not_charge` restriction suppresses retries.
- **Evidence:** spec-internal (§4.4, §5, §6.1). reasoning only.
- **Confidence:** high

### DEEPSEEK-7 · "Rejects unsupported facts" is not machine-checkable for free-text output

- **Section:** §2, §9.2
- **Type:** gap
- **Severity:** major
- **Finding:** §9.2 requires the deterministic validator to reject "unsupported facts", but `summary` is natural language. Unauthorized actions, invented probabilities, and contradictory safety language are checkable (against `allowed_action_ids`, format rules, and `safety_state`); "unsupported facts" in prose is not. As written the gate is unimplementable and could create false confidence in the fallback path.
- **Proposed change:** Split validation into (a) machine-checkable invariants — schema, `action_id` ∈ allowed set, no numeric percentages, `safety_state` monotonic, all `evidence_ids` resolve, no repair/recall-completion claims — and (b) human-reviewed claims. Constrain `summary` to be assembled from structured fields (cause + strength + missing info + action) rather than free prose, so no new fact can be introduced. State explicitly that free-text fact-checking is out of scope for the deterministic validator.
- **Evidence:** spec-internal (§2, §9.2). reasoning only.
- **Confidence:** high

### DEEPSEEK-8 · Applicability is modelled twice, with no stated precedence

- **Section:** §4.2, §4.4
- **Type:** inconsistency
- **Severity:** major
- **Finding:** `vehicle_issue_applicability` (§4.2) is a join table expressing which issues apply to which variant, while `issue.support_conditions`/`contradiction_conditions` (§4.4) also express applicability as predicates. The spec does not say which is authoritative or how they compose; a join query and a predicate evaluator will drift over time.
- **Proposed change:** Pick one mechanism. Recommend keeping the predicate fields as human-readable evidence and deriving the join table from evaluated predicates, or storing applicability only in the join table and keeping predicates as display text. Add a note on precedence and a test that both paths return the same issue set for a fixed variant.
- **Evidence:** spec-internal (§4.2 vs §4.4). reasoning only.
- **Confidence:** high

### DEEPSEEK-9 · Ranking formula terms are undefined and not reproducible

- **Section:** §6.2
- **Type:** gap
- **Severity:** major
- **Finding:** `score(cause) = supporting_evidence - contradicting_evidence + applicability_specificity - uncertainty_penalty` leaves every term undefined: are the first two counts of evidence records, of distinct incidents, or weighted sums? What are the scale and units of `applicability_specificity` and `uncertainty_penalty`? "Avoid double-counting correlated evidence" implies a dedup rule that is never given. The ranking engine is therefore not implementable or testable as written.
- **Proposed change:** Define each term as a concrete function over observation/evidence records, state each term's range (e.g. all in [-1, 1]), specify the dedup key (e.g. group by `source_url` + `document_version` + incident), and add a worked example with three causes and expected ordering plus a unit test over a fixed fixture.
- **Evidence:** spec-internal (§6.2). reasoning only.
- **Confidence:** high

### DEEPSEEK-10 · Release gates name checks but no concrete cases, thresholds, or fixtures

- **Section:** §12, §13
- **Type:** gap
- **Severity:** major
- **Finding:** §12 lists check categories and metrics (coverage, abstention rate, top-k recall, user-action success, incorrect escalation, unsafe-action violations) but no target thresholds, no ground-truth acquisition method, and no concrete fixtures for "the curated safety cases" or "the adversarial validation suite". "Release requires complete passing results" is therefore not measurable.
- **Proposed change:** Add a machine-readable test corpus (safety fixtures, adversarial LLM prompts, missing-data fixtures, slow-charging fixtures), a target for each metric (to be filled by pilot evidence per §13), and a definition of "calibration" (e.g. expected calibration error per segment). Mark pilot-derived thresholds as `TBD` placeholders rather than leaving the gate unmeasurable.
- **Evidence:** spec-internal (§12, §13). reasoning only.
- **Confidence:** high

### DEEPSEEK-11 · Outcome records don't link back to the candidate or evidence they confirm

- **Section:** §3.2, §11, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** §11 lists outcome values (`charged_after_retry`, `dealer_confirmed_component_fault`, …) and §14 treats outcomes as a knowledge source, but the outcome schema has no `candidate_id`, `observation_ids`, confirmation quality, or evidence link. A resolved session therefore cannot feed the confirmation loop that §3.2's `confirmed` quality and §14 imply.
- **Proposed change:** Add to the outcome record: `candidate_id`, `supporting_observation_ids`, `contradicting_observation_ids`, `confirmation_quality` (reuse the §3.2 quality enum), `actor`, and `evidence_ids`.
- **Evidence:** spec-internal (§3.2, §11, §14). reasoning only.
- **Confidence:** high

### DEEPSEEK-12 · Supersession is expressed three ways

- **Section:** §4.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** `verification_status` includes `superseded`, while `supersedes_id` and `valid_until` independently encode the same fact. A record could be `approved` yet carry a `supersedes_id`, or `superseded` with no successor — ambiguous states.
- **Proposed change:** Keep `supersedes_id` as the single source of truth; drop `superseded` from `verification_status` (or define it as derived), and state that `valid_until` is informational. Add the invariant: `superseded` ⇔ `supersedes_id` non-null.
- **Evidence:** spec-internal (§4.1). reasoning only.
- **Confidence:** medium

### DEEPSEEK-13 · Idempotency is asserted but no key is specified

- **Section:** §11
- **Type:** gap
- **Severity:** minor
- **Finding:** §11 requires "idempotency handling" for mutations while also describing observations as immutable/appended. A retried `POST …/observations` without an idempotency key would duplicate observations. No `Idempotency-Key` header or client token is specified.
- **Proposed change:** Specify an `Idempotency-Key` header (or client-supplied `client_request_id`) on all mutation endpoints, and state that a replayed request with the same key returns the stored result and appends nothing.
- **Evidence:** spec-internal (§11). reasoning only.
- **Confidence:** high

### DEEPSEEK-14 · Seed example S2 leans on the very evidence class §7.1 warns against

- **Section:** §7.1, §15 [S2]
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §7.1 lists the Mercedes CLA 400V-converter claim as a "source-backed example" resting on a product page (`mbusa.com/en/future-vehicles/…`), while §7.1 itself warns that "older product pages are not evidence that a particular vehicle has the equipment". The seed assertion is a fine illustration of an applicability-limited claim, but citing a marketing page as "source-backed" overstates its evidentiary weight.
- **Proposed change:** Re-label the S2 example's `source_type` as a vendor product page, `verification_status` `under_review`, confidence low, and keep the "verify build/variant/converter fitment" limitation. Optionally replace S2 with OEM service documentation or configurator data when available.
- **Evidence:** spec-internal (§7.1 vs §15 [S2]). reasoning only.
- **Confidence:** medium

### DEEPSEEK-15 · Uploaded photos are untrusted content but no redaction rule exists

- **Section:** §9.2, §10
- **Type:** risk
- **Severity:** minor
- **Finding:** §10 treats user uploads as untrusted, requires excluding sensitive identifiers from LLM payloads, and supports photo transcription. Error screenshots can contain VINs, precise location, account names, or payment fields. The spec gives no rule for redacting or excluding such content from a photo before it reaches the LLM or analytics.
- **Proposed change:** Add a rule that photo-derived text is redacted of VIN, precise location, account identifiers, and payment data before transcription reaches the LLM, and that the raw image is retained only as long as §10's retention policy allows. Reference the privacy gate in §12.
- **Evidence:** spec-internal (§9.2, §10). reasoning only.
- **Confidence:** medium

---

## Top 3

1. **DEEPSEEK-1** — settle the canonical observation schema and fix the broken `source_type` enum value; every downstream contract (§3, §4, §9, §11) depends on it.
2. **DEEPSEEK-6** — wire issue severity and recall restrictions into the safety engine; this is the highest-safety gap.
3. **DEEPSEEK-9** — define the ranking formula concretely so the ranking engine is implementable and testable.
