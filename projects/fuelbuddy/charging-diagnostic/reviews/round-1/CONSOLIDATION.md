# Round-1 consolidation — CLAUDE

**Spec consolidated:** v0.2 (11 October 2026) → **v0.3**.
**Consolidator:** CLAUDE.
**Date:** 2026-10-11.
**Reviews merged:** `CLAUDE.md` (15 findings), `CHATGPT.md` (15: 2 blocking, 12 major, 1 minor), `DEEPSEEK.md` (15: 1 blocking, 9 major, 5 minor).

**Reviews missing this round:** `GROK.md`, `GEMINI.md`, `CURSOR.md` were not submitted. They are not blocking — the stop rule is already unmet — but the two consistency-only classes (CURSOR) and the second research pass (GEMINI/GROK) may add findings. See *Round completeness* at the end.

## Result

45 raw findings deduplicate to **27 distinct items**: **18 accepted** into v0.3, **1 partially accepted**, **0 rejected**, and **8 routed to HUMAN** because they are safety policy, legal/privacy, or scope — which this process reserves for HUMAN (`README.md`; `agents/CLAUDE.md`).

**Stop rule: not met.** Blocking-class items remain open (observation-contract conflicts; safety-state semantics pending HUMAN). Round 2 runs on v0.3.

The three reviews agreed on more than they disagreed on. There were **no direct reviewer-vs-reviewer contradictions**; the disagreements are all reviewer-vs-HUMAN (policy/scope), not reviewer-vs-reviewer. The strongest convergence: the observation record is under-specified or self-contradictory (raised independently by all three), the LLM validator's "reject unsupported facts" is unimplementable as written (all three), the ranking formula is not reproducible (all three), and the slow-charging "expected envelope" is an undefined dependency (all three).

---

## 1. Accepted and merged into v0.3

| # | Theme | Raised by | Was | What v0.3 now says | v0.3 § |
|---|---|---|---|---|---|
| C1 | **Observation record is defined three incompatible ways; `source_type` enum broken** | DEEPSEEK-1 (blocking), CHATGPT-4, CLAUDE-13 | §3.2 envelope ≠ §4.5 key ≠ §9.1 example; `operator_integration` not in the §4.1 enum; no `observation_id`, subject, correction, conflict, or clock fields | One canonical observation record; adds `observation_id`, `session_id`, `attempt_id`, `subject_type`/`subject_id`, `observation_type`, `corrects_observation_id`, `conflict_group_id`, `clock_source`, UTC + timestamp origin/precision; example fixed to `operator` | §3.2, §9.1 |
| C2 | **Session stages are not one linear order** | CLAUDE-1, DEEPSEEK-2 | fixed `authorization → communication_setup` order | adds `authorization_method` enum and a per-method stage order; "last successful stage" is interpreted per method | §3.3 |
| C3 | **Protocol/connector families and shared vocabularies missing** | CLAUDE-2, DEEPSEEK-3 | namespaces cover only OCPP/ISO 15118/DIN/vendor/DTC; no `charge_mode`/protocol enums | adds `IEC61851_CP_STATE`, `CHADEMO`, `SLAC` namespaces, explicit `charge_mode` and `authorization_method` enums, protocols enumerated, `supported_adapters` as a relation, explicit out-of-scope list | §4.2–4.5 |
| C4 | **OCPP 2.x errors cannot be represented** | CLAUDE-5, CHATGPT-10 | key has only `raw_code` + version; example is 1.6 | mapping key gains `message_type`, `field_path`, `component`/`variable`, `techCode`; standard-field vs vendor-firmware mappings separated; 2.0.1 example added | §4.5, §9.1 |
| C5 | **LLM "reject unsupported facts" is not machine-checkable** | CLAUDE-8, CHATGPT-3, DEEPSEEK-7 | validator must judge free prose | executable guidance is *rendered* from approved versioned text; the LLM returns references + a structured explanation; validator checks mechanical invariants only; free-text fact-checking declared out of scope | §2, §9.2 |
| C6 | **Ranking formula terms undefined / not reproducible** | DEEPSEEK-9, CLAUDE-7 | `supporting − contradicting + specificity − uncertainty` with no units | each term defined as a function over records with ranges; dedup key specified; specificity only applies when a supporting observation exists; worked example + fixture test | §6.2 |
| C7 | **No abstention contract** | CHATGPT-6, DEEPSEEK-9 | abstention only implied, later model only | adds MVP `decision_status` (`supported_hypothesis`, `insufficient_evidence`, `conflicting_evidence`, `unsupported_scope`), evidence-strength rules, allowed empty ranked list, scope manifest | §6.2, §1.1 |
| C8 | **Slow-charging "expected envelope" is an undefined dependency** | CLAUDE-12, DEEPSEEK-5, CHATGPT-7 | "derived from the existing FuelBuddy charging model", never defined | adds a charging-model *interface* (version, inputs/outputs, provenance, power-measurement location + averaging interval, uncertainty) and a measurement contract; missing required inputs ⇒ `insufficient_evidence` | §6.4 |
| C9 | **Applicability predicates have no evaluation semantics** | CHATGPT-5, DEEPSEEK-8 | predicates named, semantics and precedence unstated; modelled twice (§4.2 join vs §4.4 predicates) | three-valued (`true`/`false`/`unknown`) typed grammar; unknown required input cannot satisfy a predicate; issuer-defined software ordering; the join table is derived from predicates (single source of truth) | §4.1–4.2, §4.6 |
| C10 | **Safety state has no structure and no clearance rule** *(policy parts → FB-D2)* | CHATGPT-1 (blocking), DEEPSEEK-6 | hazard rows key on observations only; nothing links issue `severity`/recall to safety; no clearing rule | adds a typed safety-state object (rule IDs, scope, triggering observations, clearance) and a `safety_rule_ids` link from issues/recalls; **the clearance semantics are proposed and pending HUMAN** | §4.4, §5 |
| C11 | **Stale evaluations can restore obsolete actions** | CHATGPT-2 (blocking) | reevaluation required, ordering/invalidation unspecified | every accepted observation increments a session *revision*; evaluations carry `evaluation_id`/`input_revision`/validity conditions; responses whose revision is not current are suppressed; hazard handling does not wait on the LLM | §2, §11 |
| C12 | **Action IDs do not constrain free-form instructions / retry budget not tracked** | CHATGPT-3, CHATGPT-8 | `max retries` + `repeat_count`, no action registry | adds a versioned *action registry* (`action_id` → playbook, actor, approved text, parameters, hazards, retry-budget scope) and an attempt ledger; budget is not reset by a new session | §4.7, §11 |
| C13 | **Evidence approval / offline validity not propagated** | CHATGPT-11 | approved records can be superseded without invalidating dependants; cached fallback validity unspecified | dependency-aware activation; immutable versioned *release manifests* with integrity, review date, validity policy, rollback, revocation | §4.1, §12 |
| C14 | **Reads and provider identity are unauthenticated** | CHATGPT-12 | auth required for mutations only | all reads *and* writes require object-level authorization; partner events need authenticated provider identity; confirmation labels distinguish user-reported from verified | §11 |
| C15 | **Recall state is a scalar; NHTSA lookup limits ignored** | CHATGPT-9, CLAUDE-3 | one `recall_status` per vehicle | `vehicle_campaign_status` keyed by vehicle × campaign, with status, `checked_at`, source, lookup scope/limitations, supersession; no-result stays `unknown`; a completed campaign does not prove no current fault | §4.4, §9.1 |
| C16 | **Seed examples overstate their evidentiary weight** | CHATGPT-15, CLAUDE-3, CLAUDE-4, DEEPSEEK-14 | §7.1 "source-backed examples"; CLA inlet split and converter fitment treated as settled | §7 renamed "Illustrative sourced examples and unresolved claims"; each example carries source locator, retrieval date, status, exact scope; CLA AC/DC inlet split marked unverified; the spring-2026 date is the manufacturer's *published* statement | §7, §15 |
| C17 | **Unverifiable example error code** | CLAUDE-11 | `FAILED_AlignmentError` used as an example | removed from the normative example; the caution is kept as a *question* about verifying any such identifier | §4.5 |
| C18 | **Who approves safety content is undefined** | CLAUDE-14 | playbooks have "approval status", no accountable role | adds a `safety_reviewer` role (qualified, named per release) recorded in `reviewed_by`; every blocking-hazard rule/playbook needs that approval | §4.7, §12 |
| C19 | **Outcome records cannot feed the confirmation loop** | DEEPSEEK-11 | outcome values listed, no linkage | outcome record gains `candidate_id`, supporting/contradicting `observation_ids`, `confirmation_quality`, `actor`, `evidence_ids` | §11 |
| C20 | **Supersession encoded three ways** | DEEPSEEK-12 | `verification_status=superseded` + `supersedes_id` + `valid_until` | `supersedes_id` is the single source of truth; `superseded` is derived; `valid_until` is informational | §4.1 |
| C21 | **Idempotency asserted, no key given** | DEEPSEEK-13 | "idempotency handling" required | specifies an `Idempotency-Key` (or client `client_request_id`) on mutation endpoints; a replay returns the stored result and appends nothing | §11 |
| C22 | **Vehicle schema lacks the AC envelope §6.4/§4.6 need** | DEEPSEEK-4 | DC electrical fields only | adds AC fields (`ac_input_voltage_min/max_v`, `ac_input_current_max_a`, `ac_phase_count`, `obc_power_kw`), making AC and DC symmetric | §4.2 |
| C23 | **Release gates are not measurable** | CHATGPT-14, DEEPSEEK-10 | check *categories* + metric names, no cases/thresholds/denominators | adds a versioned *release-evaluation manifest* (supported scope, cases, expected permitted/forbidden actions, provenance, adjudicators, unresolved labels, segment coverage), metric denominators, and dev/held-out grouping by incident | §12, §13 |
| C24 | **Photo/sensitive content can bypass field-level exclusions** | CHATGPT-13, DEEPSEEK-15 | exclusions named for fields only | defines the data boundary for photo/OCR/retrieval/explanation separately; allowlisted minimal projection for LLM payloads; detection+redaction before any external model call; same exclusions apply to traces/logs/analytics. **Retention/purposes → FB-D6** | §10 |
| C25 | **Europe has a public live-status source the spec ignores** | CLAUDE-6 | Europe listed as a market, no European data source | adds an "AFIR national access point (EU)" source class to §3.1/§14 (status, not diagnostics). Dates are from secondary sources and are flagged for verification in the text | §3.1, §14 |

**Partially accepted:** C26 — **CLAUDE-7's `base_rate` term.** The gating rule is accepted (specificity cannot lift a cause with no supporting observation). The *base-rate ordering* itself is accepted only as a documented, non-numeric ordering for now, with calibration deferred to §6.3; the approach is confirmed by HUMAN under FB-D7.

---

## 2. Decisions for HUMAN (FB-D1 … FB-D7)

These are safety policy, legal/privacy, or scope. Per `README.md` and `agents/CLAUDE.md`, CLAUDE proposes and HUMAN decides. Each is a specific either/or.

### FB-D1 · Which market is the MVP? *(CLAUDE-15; blocks C3's connector scope)*
Every seed source, recall reference and example in v0.2 is US (NHTSA, NACS/J1772), but §1.1 names Europe and North America as separate record sets, and C25 adds an EU data source.

- **Option A — Europe/France first:** add EU recall sources (there is no EU-wide public VIN lookup equivalent to NHTSA's; OEM campaign lookups and Safety Gate are partial), CCS2 connectors, GDPR forward. SAE J3400/CHAdeMO become out of scope.
- **Option B — North America first:** keep NHTSA, NACS/J1772, SAE J3400 in scope; defer AFIR/GDPR specifics.
- **Option C — both from the start:** doubles the seed/recall/connector work and the privacy surface for the MVP.

**Recommendation:** Option A, because the workspace is EU-based and AFIR gives connector-level public status without an operator contract — but this is a scope call for HUMAN. **Blocks:** C3's in-scope protocol list, the recall source class, seed examples, and §10's legal basis.

### FB-D2 · Approve the safety-state semantics *(CHATGPT-1 blocking, DEEPSEEK-6)*
v0.3 adds the *structure* (C10). The *semantics* are proposed, not decided:

> Credible reports of damage or a potentially safety-related warning suspend retry and alternate-charging recommendations pending the relevant approved triage playbook; a generic unclassified error alone does not establish a hazard. Missing or contradictory observations do not clear an active restriction. A restriction is cleared only by evidence and an actor authorized by its approved rule; a successful charging session does not itself clear it.

- **Option A — accept as written.**
- **Option B — accept but weaken clearing** (allow a successful session to clear a *reported* — not confirmed — restriction).
- **Option C — reject; keep the current observation-keyed rows only.**

**Recommendation:** Option A — it is the conservative choice and matches "abstain when evidence is insufficient". **Blocks:** the safety release gate in §12.

### FB-D3 · Is the station emergency stop ever a driver action? *(CLAUDE-9)*
Two undefined cases: (1) "press the station's emergency stop if safely reachable" — a *physical* control, so the "no station control" rule does not settle it; (2) a **stuck connector** after charging, a common non-hazard case needing an OEM-sourced unlock playbook.

- **Option A —** emergency stop may be offered as a driver action only inside an approved hazard playbook with an operator/OEM source.
- **Option B —** never a driver action; driver only moves away and calls emergency services.
- **Either way:** add a `stopping`-stage stuck-cable playbook sourced from an OEM owner's manual.

**Recommendation:** Option A with a required operator/OEM source, and add the stuck-cable playbook. Needs a qualified safety source.

### FB-D4 · Legal/privacy basis (needs legal review) *(CLAUDE-10)*
v0.3 restructures §10 around data flows but does not assert a lawful basis.

- **Question:** confirm GDPR is the governing frame for the chosen market, that *performance of the requested diagnosis* (not consent) is the primary lawful basis, and add **"DPIA completed"** and **"LLM processor agreement in place"** as release gates. Community photos: blur plates/faces before publication.
- **Note:** these are proposals for legal review, not legal conclusions.

### FB-D5 · Degraded/offline behaviour when validity cannot be established *(CHATGPT-11)*
- **Option A —** when an offline cached package's validity cannot be established, offer only approved minimal emergency/contact guidance and disclose that diagnostic evidence is unavailable; never erase a known restriction.
- **Option B —** keep serving the last cached package regardless of validity.

**Recommendation:** Option A.

### FB-D6 · Photo-processing boundary and retention *(CHATGPT-13, DEEPSEEK-15)*
- Where does OCR/transcription run (client vs server vs model provider)? May images or extracted text cross the LLM boundary at all before redaction?
- Confirm purposes, recipients, retention/deletion (including derived stores), and the community-publication redaction rules.

**Recommendation:** process and redact on-device or server-side *before* any external model call; if safe processing cannot be established, require a manual sanitized transcription.

### FB-D7 · Confirm the ranking approach *(CLAUDE-7, CHATGPT-6)*
- **Option A —** a documented, non-numeric ordering now (ordinary causes first; a specifically matching known issue cannot outrank an ordinary cause unless a supporting observation exists), with calibrated base rates and abstention thresholds only after validated outcomes.
- **Option B —** block the ranking engine until calibrated thresholds exist.

**Recommendation:** Option A — it lets the MVP ship without inventing probabilities, which v0.2 already forbids.

---

## 3. Rejected / deferred

**None rejected outright this round.** Items not applied to v0.3 were deferred, not refused:

| Item | Disposition | Reason |
|---|---|---|
| CLAUDE-2 — SAE J3400 (NACS) and CHAdeMO namespaces | **Deferred** to FB-D1 | Whether they are in scope depends on the market decision; the technical namespaces are ready to add. |
| DEEPSEEK-14 — *replace* S2 with OEM service documentation | **Partial** | No accessible OEM service document was found on 2026-10-11; the example is instead re-labelled low-confidence with a product-page `source_type`. Revisit when a better source exists. |
| CLAUDE-4 — confirm the CLA AC/DC inlet split | **Deferred** | Not resolvable from the marketing page; marked unverified in §7 and left for a spec sheet/owner's manual. |
| CHATGPT-6 — "do not invent numeric thresholds" | **Accepted as guidance, not a change** | v0.3 keeps thresholds out of the spec text and defers them to pilot evidence (already consistent with §6.3/§13). |

---

## 4. Traceability

| Review finding | Consolidation item | Disposition |
|---|---|---|
| CLAUDE-1 | C2 | accepted |
| CLAUDE-2 | C3 | accepted (SAE J3400 part deferred → FB-D1) |
| CLAUDE-3 | C15, C16 | accepted |
| CLAUDE-4 | C16 | accepted; inlet split deferred |
| CLAUDE-5 | C4 | accepted |
| CLAUDE-6 | C25 | accepted |
| CLAUDE-7 | C6, C26 | partial (gating accepted; base-rate → FB-D7) |
| CLAUDE-8 | C5 | accepted |
| CLAUDE-9 | — | HUMAN → FB-D3 |
| CLAUDE-10 | C24 | accepted structurally; legal basis → FB-D4 |
| CLAUDE-11 | C17 | accepted |
| CLAUDE-12 | C8 | accepted |
| CLAUDE-13 | C1 | accepted |
| CLAUDE-14 | C18 | accepted |
| CLAUDE-15 | — | HUMAN → FB-D1 |
| CHATGPT-1 | C10 | structure accepted; semantics → FB-D2 |
| CHATGPT-2 | C11 | accepted |
| CHATGPT-3 | C5, C12 | accepted |
| CHATGPT-4 | C1 | accepted |
| CHATGPT-5 | C9 | accepted |
| CHATGPT-6 | C7 | accepted |
| CHATGPT-7 | C8 | accepted |
| CHATGPT-8 | C12 | accepted |
| CHATGPT-9 | C15 | accepted |
| CHATGPT-10 | C4 | accepted |
| CHATGPT-11 | C13 | accepted; degraded-mode policy → FB-D5 |
| CHATGPT-12 | C14 | accepted |
| CHATGPT-13 | C24 | accepted; retention/purposes → FB-D6 |
| CHATGPT-14 | C23 | accepted |
| CHATGPT-15 | C16 | accepted |
| DEEPSEEK-1 | C1 | accepted |
| DEEPSEEK-2 | C2 | accepted |
| DEEPSEEK-3 | C3 | accepted |
| DEEPSEEK-4 | C22 | accepted |
| DEEPSEEK-5 | C8 | accepted |
| DEEPSEEK-6 | C10 | accepted; semantics → FB-D2 |
| DEEPSEEK-7 | C5 | accepted |
| DEEPSEEK-8 | C9 | accepted |
| DEEPSEEK-9 | C6, C7 | accepted |
| DEEPSEEK-10 | C23 | accepted |
| DEEPSEEK-11 | C19 | accepted |
| DEEPSEEK-12 | C20 | accepted |
| DEEPSEEK-13 | C21 | accepted |
| DEEPSEEK-14 | C16 | accepted (partial; see §3) |
| DEEPSEEK-15 | C24 | accepted; boundary/retention → FB-D6 |

Every one of the 45 raw findings is accounted for above.

---

## 5. Round completeness

Round 1 ran with three of the expected reviewers. The two missing classes are not the same risk:

- **CURSOR** (consistency-only: cross-references, field names, enum drift). This is the class most likely to find *mechanical* problems that v0.3, having grown by 25 items, may have introduced. **Recommended before round 2 is declared closed.**
- **GEMINI / GROK** (research pass). Lower marginal value here: the research-heavy findings (S1/S2/S3 sources) were already checked by CLAUDE and CHATGPT independently and agree.

**Question for HUMAN:** run CURSOR's consistency pass on **v0.3** (fast, mechanical, catches regressions introduced by this consolidation), or on v0.2 first? Recommendation: **on v0.3**, in the same round-2 window.
