# Round-2 consolidation — CLAUDE

**Spec consolidated:** v0.3 (11 October 2026) → **v0.4** (14 October 2026).
**Consolidator:** CLAUDE.
**Date:** 2026-10-14.
**Reviews merged:** `CHATGPT.md` (5 findings: 1 major, 4 minor), `DEEPSEEK.md` (8 minor), `GROK.md` (5: 3 major, 2 minor). The archived `round-2-pass1/` reviews were not used.

## Reviewer provenance

Requested versus served model, as reported by the automation:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-v4-pro | deepseek-flash, deepseek-v4-pro | verified requested model served, but part of the traffic was served by `deepseek-flash` |
| GROK | grok-4.7-high-fast | not reported | **unverified**: the provider reported no served model |

**Unverified reviewer: GROK.** Its three major findings are the only majors with external-source claims (stage order, OCPP 2.0.1 identity, AFIR dates). Two of them rest on secondary sources the reviewer cites; I did not re-fetch those sources, and the spec says so where it relies on them (§3.3, §14, §15 [S7]–[S9]). DEEPSEEK's mixed served-model list means some of its findings may come from the smaller model; all of them are spec-internal and were checked against the spec text by me.

## Result

18 raw findings deduplicate to **17 distinct items** (D1–D17; CHATGPT-1 and GROK-3 are one item): **16 accepted** into v0.4, **1 partially accepted** (D6), **0 rejected**. **No new HUMAN decision** arose; FB-D1 … FB-D7 are carried forward unchanged.

**Stop rule: not met.** Three distinct `major` findings were raised (measurement identity — CHATGPT-1 and GROK-3 are the same defect; Plug & Charge stage order and PWM-only AC; OCPP 2.0.1 fault identity). All three are fixed in v0.4, but a round on v0.4 is needed to confirm that the new text does not contain defects of the same kind. The seven open FB-D items must not be re-raised as `blocking`/`major`.

Convergence: measurement identity was found independently by CHATGPT and GROK and endorsed by DEEPSEEK. There were no reviewer-vs-reviewer contradictions.

**Corrections to the round-1 record.** Two items in `round-1/CONSOLIDATION.md` claimed more than v0.3 contained: C4 said the mapping key gained `component`/`variable`/`techCode` and a 2.0.1 example was added (it had not — GROK-2), and C6 said a worked ranking example and fixture were added (they had not — CHATGPT-4). v0.4 adds the key fields and the example, and states in §6.2 that the worked ranking example is still a required release input rather than present text.

---

## 1. Accepted and merged into v0.4

| # | Theme | Raised by | What v0.4 now says | v0.4 § |
|---|---|---|---|---|
| D1 | **Measurements lack quantity identity and qualifiers** (major) | CHATGPT-1, GROK-3, endorsed by DEEPSEEK | The canonical record gains `measurement_kind` (versioned catalog), `measurement_location`, `aggregation_kind`, `window_start`/`window_end`; unknown required qualifiers make the comparison `insufficient_evidence`; `raw_text` is not a substitute; §6.4 refers to the typed fields; new fixture (two temperatures, two power readings) | §3.2, §6.4, §12 |
| D2 | **Plug & Charge stage order reversed; no PWM-only AC path** (major) | GROK-1 | Protocol `authorization` now follows `communication_setup` and precedes `parameter_negotiation`; `communication_profile` added (`iec61851_pwm_only`, `iso15118`, `din70121`, `chademo`, `unknown`); PWM-only AC marks the high-level stages `not_applicable`, never failed; external identification recorded as an `external_authorization` event distinct from the protocol stage; DC-only cable check/precharge flagged as resting on a secondary source; CHAdeMO order left unspecified; fixture added | §3.3, §12, §15 [S7] |
| D3 | **OCPP 2.0.1 fault has no identity in the mapping key** (major) | GROK-2 | `component`, `variable`, `tech_code` added to the record and the key; a 2.x device-model mapping requires `NotifyEvent` plus component and variable; `tech_code` refines but does not replace them; no cross-version map from 1.6 `ChargePointErrorCode`; illustrative 2.0.1 observation with placeholder component/variable (no invented names); collision test added | §3.2, §4.5, §9.1, §12 |
| D4 | **Safety pass after knowledge matching is implicit** | CHATGPT-2 | New step 7 in the processing sequence and a graph node evaluating safety rules linked to matched errors, issues and campaigns; safety engine row updated; fixture added. Processing order only — FB-D2 policy untouched | §2, §6.1, §12 |
| D5 | **Supersession direction ambiguous** | CHATGPT-3 | Predecessor/successor defined; A is superseded only when an approved successor B is activated; draft successor does not deactivate A; self-links and cycles rejected; fixture | §4.1, §12 |
| D6 | **Ranking policy incomplete; tie key wrong** | CHATGPT-4 (endorsed by DEEPSEEK) | Ordering is descending score then ascending `cause_id` (`decision_status`, identical across candidates, removed as a sort key — CHATGPT-4); ranking-policy contract (tables, specificity function, uncertainty normalization, strength rules, status precedence) must be bound to the release manifest with a ≥3-candidate fixture; no guessed weights | §6.2 — *partial, see §3* |
| D7 | **Example A conflates campaign applicability with symptoms** | CHATGPT-5 | Reworded: applicability uses the campaign's eligibility criteria; symptoms support a fault hypothesis only; a station error establishes neither | §8 |
| D8 | **`wireless` in `charge_mode` vs out-of-scope list** | DEEPSEEK-1 | `wireless` removed from the enum; wireless input resolves to `unsupported_scope` | §4.2, §4.5 |
| D9 | **LLM input has no evidence records to resolve against** | DEEPSEEK-2 | `evidence` array added to the §9.1 input, populated by the evidence matcher; §9.2 resolves `evidence_id` against it | §9.1 |
| D10 | **`cause_id` vs `candidate_id`** | DEEPSEEK-3 | `cause_id` is the single identifier; "cause" and "candidate" declared synonyms; §11 outcome uses `cause_id` | §6.2, §11 |
| D11 | **Dedup key uses undefined `incident`** | DEEPSEEK-4 | `incident_id` (nullable) added to evidence; null means the record is its own incident; key updated | §4.1, §6.2 |
| D12 | **`station_observations` restates a second observation shape** | DEEPSEEK-5 | Defined as a projection of the §3.2 record (`observation_type` ∈ `station_status`, `measurement`) | §4.3 |
| D13 | **§12 "fixtures above" is dangling** | DEEPSEEK-6 | Seed fixtures named (§8 A–C plus the fixtures in the §12 table); full corpus built in the evidence-foundation phase | §12 |
| D14 | **§9.1 example vs §3.2 record** | DEEPSEEK-7 | Subject fields added to the example; `session_id` inherited from the payload; `protocol_version` is the bare version, family carried by `namespace` | §3.2, §9.1 |
| D15 | **Remediation notes left in the normative body** | DEEPSEEK-8 | Rewritten as plain requirements; the corrections are recorded in the change history | §4.4, §4.5, §16 |
| D16 | **AFIR dates now confirmable; "about a minute" too loose** | GROK-4 | §14 cites Implementing Regulation (EU) 2025/655 (14 April 2025, DATEX II from 14 April 2026, dynamic ≤1 minute, static ≤24 h); new [S9]. Attribution kept: read by GROK, not re-fetched by me, base Article 20 not re-read | §14, §15 |
| D17 | **State F is not the IEC 61851-1 error state** | GROK-5 | E = error state, F = EVSE not available; letter source must be identified first; no voltages or clause numbers until IEC text is checked; [S8] is a vendor summary | §4.5, §15 |

---

## 2. Decisions for HUMAN — carried forward (open, none new)

HUMAN is not answering during the automated loop. CLAUDE did not decide any of these. Reviewers must not raise them as `blocking`/`major`. Full options and recommendations are in `round-1/CONSOLIDATION.md` §2; the one-line state is:

| ID | Question | Spec § | Status after round 2 |
|---|---|---|---|
| FB-D1 | Which market is the MVP (Europe/France, North America, or both)? | §1.1 | open; round-2 reviewers had no new evidence. Note: GROK-1 and GROK-4 touch EU/ISO material but do not require the choice |
| FB-D2 | Approve the safety-state semantics (restriction clearance) | §5 | open. D4 changes only when rules are evaluated, not clearance policy |
| FB-D3 | Is the station emergency stop ever a driver action? Add a stuck-connector playbook | §4.7 | open |
| FB-D4 | Legal/privacy basis (GDPR frame, lawful basis, DPIA, processor agreement) — needs legal review | §10 | open |
| FB-D5 | Degraded/offline behaviour when package validity cannot be established | §12 | open |
| FB-D6 | Photo-processing boundary and retention | §10 | open |
| FB-D7 | Confirm the ranking approach (documented ordering vs block until calibrated) | §6.2 | open. D6 refers to FB-D7 for any ordinary-cause ordering and assumes nothing |

---

## 3. Rejected / deferred / partial

**None rejected.**

| Item | Disposition | Reason |
|---|---|---|
| CHATGPT-4 — complete ranking policy with a worked example | **Partial** | The spec now *requires* the full policy and a ≥3-candidate fixture before ranking is enabled, but does not include them: that needs real weight tables and a worked example, which would be invented without pilot evidence (the review itself says not to insert guessed weights) |
| GROK-1 — CHAdeMO stage order | **Deferred** | No sourced sequence is available to me; the profile is added with its order explicitly unspecified |
| GROK-1 — DC-only cable check/precharge | **Accepted with caveat** | Rests on a secondary description of ISO 15118-2; flagged in §3.3 for confirmation against the standard |
| GROK-2 — real component/variable names in the example | **Deferred** | I did not read the OCA white paper's device-model examples in this session, so the example uses placeholders instead of risking invented names |
| GROK-4 — base-regulation text | **Deferred** | Not re-read by reviewer or consolidator; dates cited via the implementing regulation and labelled as such |
| DEEPSEEK-7 — `protocol_version` form | **Accepted, medium confidence** | Chose the bare-version form because the example already puts the family in `namespace` |

---

## 4. Traceability

| Review finding | Item | Disposition |
|---|---|---|
| CHATGPT-1 | D1 | accepted (major) |
| CHATGPT-2 | D4 | accepted |
| CHATGPT-3 | D5 | accepted |
| CHATGPT-4 | D6 | partial (requirement added, worked example deferred) |
| CHATGPT-5 | D7 | accepted |
| DEEPSEEK-1 | D8 | accepted |
| DEEPSEEK-2 | D9 | accepted |
| DEEPSEEK-3 | D10 | accepted |
| DEEPSEEK-4 | D11 | accepted |
| DEEPSEEK-5 | D12 | accepted |
| DEEPSEEK-6 | D13 | accepted |
| DEEPSEEK-7 | D14 | accepted |
| DEEPSEEK-8 | D15 | accepted |
| GROK-1 | D2 | accepted (major); CHAdeMO order deferred |
| GROK-2 | D3 | accepted (major); real example names deferred |
| GROK-3 | D1 | accepted (major); duplicate of CHATGPT-1 |
| GROK-4 | D16 | accepted; base text not re-read |
| GROK-5 | D17 | accepted |

All 18 raw findings are accounted for above.

---

## 5. Round completeness

CHATGPT, DEEPSEEK and GROK all delivered complete reviews (`Result: complete`). CURSOR's consistency pass was not run. v0.4 added a new stage table, record fields and fixtures, so a CURSOR consistency check on v0.4 (cross-references, field names, enum drift) remains advisable, but is optional for the loop.
