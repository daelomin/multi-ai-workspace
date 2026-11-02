# DEEPSEEK review — round 2

**Specification:** local `spec.md`, v0.3, dated 11 October 2026.
**Reviewer:** DEEPSEEK (deepseek-v4-pro). **Review date:** 2026-10-14.
**Method:** Read the round-1 reviews (CLAUDE, CHATGPT, DEEPSEEK) and `CONSOLIDATION.md` first, then the current local spec and the round-2 CHATGPT review. All findings are spec-internal ("reasoning only"); no error code, recall number, or standard clause is invented, and no external source was re-fetched. I did not re-raise FB-D1–FB-D7: I have no new external evidence on any of them.

**Overall:** 0 blocking, 0 major, 8 minor findings. The accepted round-1 direction is retained. I agree with CHATGPT-1 (major): the canonical observation record cannot yet represent typed measurement identity and qualifiers, which §5 and §6.4 require. My findings below are the remaining internal-consistency and schema defects CHATGPT did not cover; none is unsafe or unimplementable at the blocking level, but each would slow an implementer.

---

### DEEPSEEK-1 · `charge_mode` lists `wireless` while §4.5 declares wireless power transfer out of scope

- **Section:** §4.2, §4.5
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.2 fixes the `charge_mode` enum as `ac`, `dc`, `wireless`, `unknown`, but §4.5's explicit out-of-scope list names "wireless power transfer" (alongside GB/T and MCS) as something to name but not implement. An implementer cannot tell whether to model a wireless connector/vehicle entry or reject it.
- **Proposed change:** Drop `wireless` from the `charge_mode` enum (keep `ac`, `dc`, `unknown`) and keep wireless named only in the §4.5 out-of-scope list. If wireless is to remain a possible input, state in §4.5 that it is recognized as a value but always resolves to `unsupported_scope`.
- **Evidence:** spec-internal (§4.2 vs §4.5). reasoning only.
- **Confidence:** high

### DEEPSEEK-2 · The LLM input supplies no evidence records for §9.2's `evidence_id` check to resolve against

- **Section:** §2, §9.1, §9.2
- **Type:** gap
- **Severity:** minor
- **Finding:** §9.2 requires the output `supporting_evidence_ids` and validates that "every `cause_id` and `evidence_id` resolves to a supplied record", but the §9.1 structured input contains `observations`, `candidates`, `approved_actions`, `compatibility` and `safety` — no `evidence`/assertion records. As written, the validator would reject every non-empty `supporting_evidence_ids`, because no evidence is ever supplied; the LLM cannot cite the applicable knowledge the §2 evidence matcher retrieved.
- **Proposed change:** Add an `evidence` array to the §9.1 input (the applicable, approved evidence records with their `evidence_id`, `source_url`, `document_version`, `verification_status`, and scope) and state that the §2 evidence matcher populates it. The validator then resolves `evidence_id`s against that array.
- **Evidence:** spec-internal (§9.1 vs §9.2). reasoning only.
- **Confidence:** high

### DEEPSEEK-3 · `cause_id` and `candidate_id` name the same identifier in different sections

- **Section:** §3.2, §6.2, §9.1, §9.2, §11
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The ranking engine and LLM contract use `cause_id` (§6.2 tie handling, §9.1 `candidates`, §9.2 validator), while the outcome record in §11 carries `candidate_id` to link back to the confirmed hypothesis. §3.2's `observation_id` is described as "referenced by candidates and outcomes", mixing the two words. An implementer must guess that `candidate_id == cause_id`.
- **Proposed change:** Pick one canonical identifier name (recommend `cause_id`, since ranking and LLM use it), change §11's `candidate_id` to `cause_id`, and add a one-line note that "cause" and "candidate" are synonyms in this document. Keep the observation/evidence distinction separate.
- **Evidence:** spec-internal (§6.2, §9.1, §9.2, §11). reasoning only.
- **Confidence:** high

### DEEPSEEK-4 · The ranking dedup key references an `incident` field no schema defines

- **Section:** §4.1, §6.2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** §6.2 deduplicates supporting evidence groups "by `(source_url, document_version, incident)`", but neither the §3.2 observation record nor the §4.1 evidence record has an `incident` field or table; §12 only uses "incident" to group evaluation splits. Without a defined incident concept, the dedup rule — the fix C6 added to make the score reproducible — is not computable as written.
- **Proposed change:** Define what an "incident" is (e.g. a shared real-world failure event keyed by an `incident_id`), add it to §4.1 evidence (nullable, grouping documents that describe the same event), and reference it consistently in both §6.2 and §12.
- **Evidence:** spec-internal (§6.2 key vs §3.2/§4.1 fields). reasoning only.
- **Confidence:** high

### DEEPSEEK-5 · §4.3 `station_observations` restates a second observation shape despite §3.2's single-record rule

- **Section:** §3.2, §4.3
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 declares "There is exactly one observation record … no section restates it", yet §4.3 defines `station_observations` with its own columns — `source` instead of `source_type`/`source_reference`, and no `observation_id`, `observation_type`, or `received_at` — that do not line up with the canonical record. An implementer must decide whether these rows are §3.2 observations or a separate silo.
- **Proposed change:** State that `station_observations` is a projection of the §3.2 record with `observation_type` ∈ {`station_status`, `measurement`}, rename `source` to `source_type`, and carry `observation_id`. Alternatively, delete the table and let station status flow through the canonical record only.
- **Evidence:** spec-internal (§3.2 vs §4.3). reasoning only.
- **Confidence:** high

### DEEPSEEK-6 · §12's release-evaluation manifest draws cases "from the fixtures above", but no fixtures are defined

- **Section:** §12, §8
- **Type:** gap
- **Severity:** minor
- **Finding:** §12 requires the release-evaluation manifest's cases to be "drawn from the fixtures above", but the document defines no fixture set — §8 has three prose diagnostic examples (A–C) and §12's table lists check categories, not concrete cases. The gate therefore references inputs that do not exist in the spec.
- **Proposed change:** Either point the manifest at the §8 examples and name them as the seed fixtures, or add an explicit "fixtures" list (or a `TBD` placeholder for the fixture corpus) that §12 can reference. Prefer an explicit pointer over the vague "above".
- **Evidence:** spec-internal (§12 vs §8). reasoning only.
- **Confidence:** high

### DEEPSEEK-7 · §9.1's example observation omits required subject fields and uses a `protocol_version` shape that differs from §3.2's

- **Section:** §3.2, §9.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.2 marks `subject_type`/`subject_id` as required, and lists `protocol_version` examples as `OCPP 1.6`, `OCPP 2.0.1`. The §9.1 example observation has no `subject_type`/`subject_id` (nor `session_id`) and writes `protocol_version` as `"1.6"` with the `OCPP` part moved to `namespace`. The namespace-split form is defensible, but the two sections must agree on which form is canonical.
- **Proposed change:** Add `subject_type`/`subject_id` to the example observation (and note that `session_id` is inherited from the top-level payload), and state once whether `protocol_version` carries the bare version (`1.6`) given a `namespace`, or the full name (`OCPP 1.6`); make §3.2's examples match.
- **Evidence:** spec-internal (§3.2 vs §9.1). reasoning only.
- **Confidence:** medium

### DEEPSEEK-8 · The spec body still carries consolidation remediation notes, not normative requirements

- **Section:** §4.4, §4.5
- **Type:** suggestion
- **Severity:** minor
- **Finding:** §4.4 says "Use `dtc_codes`, correcting the original `dmtc_code` spelling" and §4.5 says "Correct the original `DIN SPEC 99003` reference to `DIN SPEC 70121`". These are editor-to-editor instructions left in the normative body; a `DIN SPEC 99003` string appears nowhere else in the document to correct. They read as change-history material and would confuse a reader treating the spec as the implementation baseline.
- **Proposed change:** Rewrite as plain normative statements ("The field is `dtc_codes`"; "The relevant standard is `DIN SPEC 70121`; do not use `DIN SPEC 99003`") and move the "correcting the original" wording to §16.1's change history.
- **Evidence:** spec-internal (§4.4, §4.5, §16). reasoning only.
- **Confidence:** high

---

## Top 3

1. **CHATGPT-1 (endorsed):** give measurements typed quantity identities and the qualifiers the charging-model interface needs — the only major this round.
2. **DEEPSEEK-2:** supply the applicable evidence records to the LLM input so §9.2's evidence validation can actually pass.
3. **DEEPSEEK-1 / DEEPSEEK-4:** resolve the `wireless` scope contradiction and define `incident` so the ranking dedup key is computable.

I reviewed FB-D1–FB-D7 and have no new external evidence, so they are not reopened. I also agree with CHATGPT-2 (safety pass after matching), CHATGPT-3 (supersession direction), CHATGPT-4 (ranking-policy completeness) and CHATGPT-5 (example A conflation) and do not restate them.

Result: complete
