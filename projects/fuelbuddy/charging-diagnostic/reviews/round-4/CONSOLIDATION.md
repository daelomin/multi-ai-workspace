# Round-4 consolidation — CLAUDE

**Spec consolidated:** v0.5 (21 October 2026) → **v0.6** (21 October 2026; same day, version bumped).
**Consolidator:** CLAUDE.
**Date:** 2026-10-21.
**Reviews merged:** `CHATGPT.md` (3 findings: 3 minor), `DEEPSEEK.md` (6 minor), `GROK.md` (5 minor). All three ended with `Result: complete`.

## Reviewer provenance

Requested versus served model, as reported by the automation:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified**: the provider reported no served model |

**Unverified reviewer: GROK.** Two of its findings carry external-source claims: GROK-3 (Typhoon HIL DIN SPEC 70121 page) and GROK-4 (Annex Table B of Implementing Regulation (EU) 2025/655, "only one connector can be used at the same time"), plus the Table B label remark. I did not re-fetch any of them. v0.6 attributes them to the GROK reviewer in §14 and §15 [S10]. GROK-1, GROK-2 and GROK-5 are spec-internal and I checked them against the spec text. CHATGPT's and DEEPSEEK's findings are all "reasoning only" and were checked against the spec text.

## Result

14 raw findings deduplicate to **13 distinct items** (D1–D13; GROK-3 and DEEPSEEK-4 are one item): **13 accepted** into v0.6, **0 rejected**, 0 routed to HUMAN. Two are accepted with an adjustment (see §4).

**Stop rule: met.** No `blocking` or `major` finding, and no reviewer re-raised a settled or open FB item. This is the **last round**; the review converged at round 4 on v0.6, and the README says so. Minor findings that remain unforeseen are for implementation, not for another round, unless HUMAN asks for one.

Convergence: CHATGPT-1/2/3 were endorsed by DEEPSEEK and GROK; DEEPSEEK-1 to -6 were endorsed by GROK. No reviewer contradicted another.

---

## 1. Accepted and merged into v0.6

| # | Theme | Raised by | What v0.6 now says | v0.6 § |
|---|---|---|---|---|
| D1 | **Stage events have no outcome** | CHATGPT-1, GROK (clock note) | `stage_outcome` (`entered`, `succeeded`, `failed`, `unknown`) on stage events; only an effective `succeeded` event establishes success; last successful stage is derived per attempt, never inferred from presence or inherited from a previous attempt; events on different `clock_source` values are not ordered against each other, `received_at` is receipt order; unresolved membership or ordering stays `unknown`; fixture added | §3.2, §3.3, §12 |
| D2 | **Station projection still connector-only; availability has no payload member** | CHATGPT-2, GROK (Table B label note) | Projection keys on `subject_type`/`subject_id` (connector or `recharging_point`); point observations are never copied to connectors; `availability_state` added to the station-status payload, separate from `operational_state`; §14 maps each AFIR data type to its own member; Table B's "(Connector)" label is not followed over its Point data level (attributed to GROK); fixture with a multi-connector point | §3.2, §4.3, §14, §12 |
| D3 | **Restrictions with different dimensions do not compose** | CHATGPT-3 | "Combining restrictions": each restriction is evaluated in its own scope; an action is allowed only if all permit it; `do_not_charge`/`other`/unmapped permits no charging action; otherwise all limits and warnings are kept; no satisfying action → approved escalation. Composes the settled "most restrictive wins" rule and changes no approved text; fixture | §5, §12 |
| D4 | **Safety-state vocabulary and ordering undefined** | DEEPSEEK-1 | Closed, versioned `safety_state` enum set only by the safety engine, ordered `no_blocking_hazard_observed` < `restricted` < `stopped`; never lowered by an observation, missing warning, LLM or fallback; lowered only by a clearance; §9.2 monotonicity now refers to it; fixtures. Labels are **provisional** pending `safety_reviewer` approval (see §4) | §5, §9.2, §12 |
| D5 | **Outcome record contradicts the single-observation rule** | DEEPSEEK-2 | Outcomes are `outcome` observations on the session subject; the payload adds `cause_id`, outcome value, supporting/contradicting `observation_ids`, `actor`, `evidence_ids`; confirmation quality is the `quality` field; `POST .../outcomes` is a typed entry point that appends one; fixture | §3.2, §11, §12 |
| D6 | **`VEHICLE_DTC` cannot carry the ECU the key needs** | DEEPSEEK-3 | `ecu` field, required for `VEHICLE_DTC`, null otherwise, added to the §4.5 mapping key; a mapping without an ECU never matches; fixture | §3.2, §4.5, §12 |
| D7 | **DIN row wording and profile/method consistency** | GROK-3, DEEPSEEK-4 | DIN row: `plug_and_charge` rejected, contract exchange empty, `rfid`/`app`/`ad_hoc_payment`/`free` stay allowed; new consistency rule: `plug_and_charge` only with `iso15118`, preserved as unknown under an unknown profile; no `external_authorization` required for `free`, none inferred for `unknown`; [S10] wording aligned; fixtures | §3.3, §12, §15 |
| D8 | **`contradicting` cannot use the evidence-group identity** | DEEPSEEK-5 | Same group identity as `supporting` (via the evidence behind each observation, `incident_id`, else `evidence_id`; an observation with no evidence is its own group); weights come from the ranking-policy tables keyed by `source_type` and `quality`; `conflict_group_id` is not the dedup key; symmetric fixture | §6.2, §12 |
| D9 | **`unsupported_scope` has no response behaviour** | DEEPSEEK-6 | Still runs and shows the §5 safety evaluation and restrictions; returns the manifest's general guidance and names the missing manifest entry; never presented as a supported hypothesis or cause-specific playbook; says nothing about which countries are in scope (FB-D1a–c); fixture | §6.2, §12 |
| D10 | **`external_authorization` missing from the stage list; `not_applicable` stored vs derived** | GROK-1 | `external_authorization` added as an event value, not a profile step; `not_applicable` is never a `stage` value; §12 Stages row says "derives", not "marks" | §3.3, §12 |
| D11 | **Diagram sends every restriction to a full stop** | GROK-2 | §2 diagram split: hazard, `do_not_charge`, `other`, unmapped → stop and escalate; `charge_limited` and `do_not_charge_indoor` → restricted-mode actions and warnings only, not ordinary ranking; sentence in §2; fixture. The §5 table is unchanged | §2, §12 |
| D12 | **Other connectors of an in-use point offered as alternates** | GROK-4 | AFIR bullet: a point may hold several connectors, only one usable at a time; while the point is `in use`/`reserved`, no sibling connector is recommended as an alternate (a different point is); attributed to GROK, not re-fetched; fixture | §14, §12 |
| D13 | **Idempotent replay can return a stale evaluation** | GROK-5 | §11: a replayed `evaluate` returns the stored body but it stays subject to the §2 revision/permission check and is suppressed and reevaluated if stale; fixture | §11, §12 |

---

## 2. HUMAN decisions applied from `decisions.md`

All five decisions in `decisions.md` (FB-D1, FB-D2, FB-D3, FB-D5, FB-D7) were applied in v0.5. I re-read each against the v0.6 text: the matching passages carry the settled wording, no "Pending HUMAN decision" passage remains for them, and none appears in the carried-forward list. This round adds no detail HUMAN did not give: D3 and D11 compose and route the settled restriction behaviour without changing any approved instruction, and D9 states no scope choice. Remaining "Pending HUMAN decision" text in the spec concerns only FB-D4 and FB-D6 (§10).

---

## 3. Decisions for HUMAN — carried forward (single open list)

HUMAN is not answering during the automated loop. CLAUDE did not decide any of these. No new HUMAN decision arose this round.

| ID | Question | Spec § | Status |
|---|---|---|---|
| FB-D4 | Legal/privacy basis (GDPR frame for the EU/EEA part, lawful basis per purpose, DPIA, LLM processor agreement as release gates; UK and Switzerland have their own rules) — needs legal review | §10 | open; no new evidence. Not settled by FB-D1 |
| FB-D6 | Photo-processing boundary and retention (client vs server vs provider; retention and deletion incl. derived stores) | §10 | open |
| FB-D1a | Which API makes a country eligible (recall/safety data, charge-point status, location data…)? The spec names none | §1.1, §14 | open |
| FB-D1b | Which countries launch first? | §1.1 | open |
| FB-D1c | Is a country without a usable API excluded, or served in a reduced mode? | §1.1 | open |
| FB-D2a | Period after which advice to other drivers about an equipment restriction downgrades to "unverified, last reported on <date>" | §5 | open; no number invented |
| FB-D5a | Hard age limit after which a cached package is restricted to safety content plus an "update when you have signal" message | §4.1 | open; no number invented |

The "a/b/c" ids are CLAUDE's, for tracking only (from the notes in `decisions.md`).

---

## 4. Rejected / deferred / adjusted

**None rejected, none deferred.**

| Item | Disposition | Reason |
|---|---|---|
| DEEPSEEK-1 — proposed `safety_state` labels | **Adjusted** | The reviewer offered labels and left the choice to me. I used three labels aligned with the §5 table and §2 flow (`no_blocking_hazard_observed`, `restricted`, `stopped`), kept `no_blocking_hazard_observed` because §9.1 already uses it, and marked all labels provisional until the `safety_reviewer` approves them. I did not add the proposed `normal`, `hazard_reported` or `emergency` labels, which would duplicate or split the §5 behaviours without a HUMAN-approved basis |
| DEEPSEEK-2 — outcome record vs observation | **Adjusted** | The reviewer left the choice open. I chose "outcomes are observations" because §11 already defines `confirmation_quality` as the §3.2 `quality` enum, and it gives outcomes the same provenance fields as other evidence. This is a technical choice, not a HUMAN decision |
| GROK-3, GROK-4 — external claims | **Accepted with attribution** | Typhoon HIL and Table B were not re-fetched by me; the spec attributes them to the GROK reviewer (GROK is the unverified reviewer) |

---

## 5. Traceability

| Review finding | Item | Disposition |
|---|---|---|
| CHATGPT-1 | D1 | accepted |
| CHATGPT-2 | D2 | accepted |
| CHATGPT-3 | D3 | accepted |
| DEEPSEEK-1 | D4 | accepted; labels provisional |
| DEEPSEEK-2 | D5 | accepted; observation path chosen |
| DEEPSEEK-3 | D6 | accepted |
| DEEPSEEK-4 | D7 | accepted; merged with GROK-3 |
| DEEPSEEK-5 | D8 | accepted |
| DEEPSEEK-6 | D9 | accepted |
| GROK-1 | D10 | accepted |
| GROK-2 | D11 | accepted |
| GROK-3 | D7 | accepted; attributed, not re-fetched |
| GROK-4 | D12 | accepted; attributed, not re-fetched |
| GROK-5 | D13 | accepted |

All 14 raw findings are accounted for. GROK's agreement notes (clock sources for CHATGPT-1; the Table B label for CHATGPT-2) were merged into D1 and D2.

---

## 6. Round completeness

CHATGPT, DEEPSEEK and GROK all delivered complete reviews. CURSOR's consistency pass was not run in any round. v0.6 adds several fields and tables (`stage_outcome`, `ecu`, `availability_state`, the `safety_state` enum), so a consistency check of cross-references and enum drift is still advisable before implementation. It is optional and does not reopen the loop.
