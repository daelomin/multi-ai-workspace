# CHATGPT review — round 2

**Specification:** Local `spec.md` v0.3, dated 11 October 2026.  
**Reviewer:** CHATGPT. **Review date:** 2026-10-14.  
**Method:** Read the README and all round-1 reviews and consolidation before assessing the current local specification. This pass checks internal contracts and the actual merged text; evidence is reasoning from the specification, without re-verifying external vehicle, protocol, or legal claims.

**Findings:** 0 blocking, 2 major, 3 minor. The stop rule is not met because of the two implementation defects below. FB-D1 through FB-D7 remain with HUMAN and are not re-raised. The accepted round-1 direction is retained; where a finding revisits an accepted item, it identifies what remains incomplete in v0.3.

### CHATGPT-1 · Safety must consume restrictions discovered during matching

- **Section:** §2, §4.4–§4.5, §5, §6.1, §12
- **Type:** gap
- **Severity:** major
- **Finding:** The numbered sequence evaluates safety at step 3, before resolving configuration at step 4 and retrieving applicable errors/issues at step 6; the architecture likewise routes matching directly onward to ranking and playbooks. An issue's `safety_rule_ids`, or safety semantics from a newly resolved error mapping, can therefore become known after the safety state was computed, without a new observation or revision triggering another evaluation. Final validation against that earlier state does not establish that these newly discovered restrictions were applied; this is the remaining execution-order gap in consolidation C10, independent of the clearance policy in FB-D2.
- **Proposed change:** Add: "Run an immediate safety pass on incoming observations. After identity resolution and applicable knowledge/error matching, evaluate safety again using all matched safety rules and campaign restrictions before selecting actions. If later processing changes a safety-relevant fact or applicable rule, recompute safety and action permissions before publication, even when `input_revision` is unchanged. Final validation uses that completed safety evaluation and its pinned knowledge versions." Add a fixture where matching discovers an already approved blocking rule after the initial safety pass and assert that both normal and fallback outputs suppress its forbidden actions.
- **Evidence:** reasoning only; the §6.1 execution order versus the rule links defined in §4.4–§4.5 and the final validation requirement in §5.
- **Confidence:** high

### CHATGPT-2 · Canonical measurements lack the identity and qualifiers the model needs

- **Section:** §3.2, §6.4, §10, §12
- **Type:** gap
- **Severity:** major
- **Finding:** The canonical record identifies a numeric observation only as `observation_type=measurement`, with `subject`, `value`, and `unit`; it has no defined measurement key or typed qualifiers. Two temperatures about the same vehicle cannot reliably distinguish battery from ambient temperature, and two power readings cannot carry the required measurement boundary or averaging window in a defined field. C1/C8 added the envelope and model interface, but their merged text still leaves the model unable to consume these distinctions without inventing another observation format or parsing untrusted text.
- **Proposed change:** Extend the single §3.2 record with a versioned `measurement_kind` catalog and typed qualifiers: measurement location/boundary, aggregation kind, and interval start/end or duration where applicable. Define which qualifiers each measurement kind requires and validate compatible units; unknown identity or required qualifiers make a reading unusable for that model comparison. Reference those fields from §6.4 and add fixtures distinguishing ambient/battery temperature and instantaneous/averaged power at different measurement boundaries. Do not infer these qualifiers from `raw_text` or source name.
- **Evidence:** reasoning only; the fields in §3.2 cannot structurally represent the measurement contract required by §6.4 and the distinctions required by §5/§10.
- **Confidence:** high

### CHATGPT-3 · Finish the versioned ranking policy without choosing new thresholds

- **Section:** §6.2, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** C6 is described as defining every function, but `specificity` still has only a range and a gate, while `uncertainty` is merely "proportional" to missing discriminators without a denominator or cap rule. Grouping by `(source_url, document_version, incident)` also needs a defined incident identity and aggregation rule; copied reports with different URLs would otherwise remain separate groups. These are configuration details that can be supplied during implementation, but the release contract should require them explicitly rather than implying the current formula is reproducible on its own.
- **Proposed change:** Add: "Each ranking-policy version defines weight lookup tables, within-group aggregation, cross-source incident/copy linkage and unknown-identity handling, the specificity function, the discriminator catalog and normalized uncertainty function, evidence-strength bands, and deterministic status/tie precedence. Supply a fixed worked fixture with expected contributions and ordering before activation." Keep numerical values subject to pilot validation and leave FB-D7's choice of ranking approach unchanged.
- **Evidence:** reasoning only; comparison of §6.2 with consolidation C6 and its claimed worked-example/fixture resolution, which is absent from the current specification.
- **Confidence:** high

### CHATGPT-4 · Scope idempotency keys and reject conflicting reuse

- **Section:** §11
- **Type:** gap
- **Severity:** minor
- **Finding:** The new replay rule returns the stored result for "the same key" without defining whether the key is scoped to an authenticated caller, operation, or session, or what happens when the request body changes. Independent clients can reuse the same key, and a client bug can reuse an observation key for a later, different observation; the current wording does not distinguish a valid retry from either collision.
- **Proposed change:** Add: "Scope idempotency records by authenticated principal/tenant, operation, target resource, and key; store a canonical request fingerprint. Replay only an identical request, reject reuse with a different fingerprint, and handle concurrent identical requests atomically. Document retention and expired-key behavior. Authorization and current action-validity checks still apply to replayed results." Add fixtures for cross-session key reuse, changed-body reuse, and simultaneous identical submissions.
- **Evidence:** reasoning only; the §11 replay contract and its immutable observation semantics.
- **Confidence:** high

### CHATGPT-5 · Separate campaign eligibility from symptom-based diagnosis in example A

- **Section:** §4.4, §7.1, §8 example A
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Example A says "ICCU campaign applicability can be checked via `vehicle_campaign_status`, but it is established through vehicle warnings and low-voltage symptoms." Grammatically, "it" refers to campaign applicability, conflating eligibility/status with evidence supporting a component-fault hypothesis. That conflicts with §4.4's campaign-specific status contract and with §7.1's warning that the example does not establish an individual vehicle's campaign state.
- **Proposed change:** Replace that sentence with: "Assess campaign eligibility using the campaign's authoritative applicability criteria, and preserve individual-vehicle status in `vehicle_campaign_status`. Separately, vehicle warnings and low-voltage symptoms may support investigation of a vehicle-side fault; a generic station error establishes neither an ICCU diagnosis nor campaign status." Keep unknown campaign status unknown until the evidence required by §4.4 is available.
- **Evidence:** reasoning only; internal wording conflict between §8 example A and §4.4/§7.1. This finding makes no new claim about the actual campaign or its eligibility criteria.
- **Confidence:** high

## Top 3

1. **CHATGPT-1:** Reevaluate safety after matching discovers applicable restrictions, before selecting any actions.
2. **CHATGPT-2:** Give canonical measurements typed identities and the qualifiers required by the charging-model interface.
3. **CHATGPT-3:** Require a complete ranking-policy artifact and worked fixture, preserving pilot validation and FB-D7.

Result: complete
