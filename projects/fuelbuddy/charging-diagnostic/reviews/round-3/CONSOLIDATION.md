# Round-3 consolidation — CLAUDE

**Spec consolidated:** v0.4 (14 October 2026) → **v0.5** (21 October 2026).
**Consolidator:** CLAUDE.
**Date:** 2026-10-21.
**Reviews merged:** `CHATGPT.md` (3 findings: 3 minor), `DEEPSEEK.md` (3 minor), `GROK.md` (3: 1 major, 2 minor). All three ended with `Result: complete`.

## Reviewer provenance

Requested versus served model, as reported by the automation:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-v4-pro | deepseek-v4-pro | verified |
| GROK | grok-4.7-high | not reported | **unverified**: the provider reported no served model |

**Unverified reviewer: GROK.** It raised the only `major` finding (GROK-1) and the only findings with new external-source claims (EU Implementing Regulation 2025/655 Annex Tables B and F; the Typhoon HIL DIN SPEC 70121 page; the Siemens CHAdeMO library note). I did not re-fetch any of these. v0.5 attributes each to GROK in the text (§14, §15 [S9]–[S11]) and labels the CHAdeMO stage order provisional. CHATGPT's and DEEPSEEK's findings are spec-internal ("reasoning only") and were checked against the spec text by me.

## Result

9 raw findings deduplicate to **8 distinct items** (D1–D8; GROK-3 and DEEPSEEK-2 are one item): **8 accepted** into v0.5, **0 rejected**. The CHAdeMO part of D2 is accepted as provisional (see §4).

Also applied: the five settled HUMAN decisions in `decisions.md` (FB-D1, FB-D2, FB-D3, FB-D5, FB-D7), see §2. **No new HUMAN decision** arose from the reviews; the settled decisions did raise five parameter questions (FB-D1a–c, FB-D2a, FB-D5a), carried forward in §3.

**Stop rule: not met.** GROK-1 is a `major` finding (AFIR status is recharging-point level, not connector level). It is fixed in v0.5, but v0.5 also contains substantial new normative text from the settled decisions (restriction clearance, hazard screening, cached packages, Europe scope), so a round on v0.5 is needed to confirm that text. No reviewer re-raised an open FB-D item as `blocking`/`major`; none of the settled items was reopened.

Convergence: CHATGPT-1/2/3 were endorsed by DEEPSEEK and GROK; DEEPSEEK-1 was endorsed by GROK; the measurement-axis point was raised independently by DEEPSEEK-2 and GROK-3.

**One reviewer disagreement.** DEEPSEEK-2 proposed that a valid power comparison requires equal kind *and* equal location; GROK-3 says charger output as reported by the vehicle and as read by a meter are the same kind and may be compared under a catalog rule. I kept the conservative existing rule (different locations are not substituted) and added GROK's exception only as an explicit catalog rule, so nothing becomes comparable by default. This is a technical point, not a HUMAN decision.

---

## 1. Accepted and merged into v0.5

| # | Theme | Raised by | What v0.5 now says | v0.5 § |
|---|---|---|---|---|
| D1 | **AFIR status is recharging-point level, not connector level** (major) | GROK-1 | New `recharging_point` subject type; §14 says the feed gives recharging-point operational status and availability (Annex Table F data level Point; a point may hold several connectors); status is not copied onto each connector; literals `operational`/`non-operational` and `in use`/`reserved`/`not in use` recorded as `station_status` observations with `source_type` `regulator`; not a hazard or restriction trigger; MCS connector type stays `unsupported_scope`; the regulation does not cover the UK or Switzerland, and coverage of other countries is the open FB-D1a. Attribution kept: read by GROK on 2026-10-21, not re-fetched by me | §3.2, §12, §14 |
| D2 | **DIN 70121 shares an ISO row; `safety_checks` unmarked on AC and PWM-only; CHAdeMO order missing** | GROK-2 | `din70121` has its own DC-only row, `safety_checks` always applicable, `plug_and_charge` not allowed; `iso15118` marks `safety_checks` `not_applicable` on AC; PWM-only also marks `authorization` and `safety_checks` `not_applicable`; CHAdeMO order added as **provisional**, from a vendor note, with protocol `authorization` `not_applicable`; fixture extended; refs [S10], [S11] | §3.3, §12, §15 |
| D3 | **`measurement_kind` is the quantity, `measurement_location` the reporter** | GROK-3, DEEPSEEK-2 | Kind = physical quantity (e.g. charger output power vs battery input power); location = reporter; a comparison requires the same kind; same kind from differing reporters is comparable only under an explicit catalog rule; §6.4 wording and the measurement fixture updated | §3.2, §6.4, §12 |
| D4 | **Deterministic evaluation fields not pinned through LLM validation** | CHATGPT-1 | `decision_status` and reasons, ranked cause IDs in evaluated order, and evidence strength are authoritative; the renderer copies them; any LLM-returned copy must match exactly, else deterministic fallback; two fixtures (reversed order, changed abstention status) | §9.2, §12 |
| D5 | **Shared incident still counted per source document** | CHATGPT-2 | Evidence-group identity is `incident_id` when non-null, regardless of source URL and version; null means the record is its own incident (`evidence_id`); source metadata is provenance only; fixture with two URLs and versions on one incident | §4.1, §6.2, §12 |
| D6 | **Station-state projection introduces undefined fields** | CHATGPT-3 | §3.2 gains a typed station-status payload (`operational_state`, `power_sharing_state`) from versioned vocabularies including `unknown`, with values not listed; `available_power_kw` is an alias of a canonical `measurement` observation (catalog kind: available station allocation); §4.3 projection resolves observations by ID and keeps no competing state; vocabularies are bound to the release manifest | §3.2, §4.3, §12 |
| D7 | **Session-stage model has no field or session schema** | DEEPSEEK-1 | `stage` field added to the canonical record for `session_stage_event` (stages plus `external_authorization`); minimal session record (`session_id`, `communication_profile`, `authorization_method`, revision); last successful stage and stage applicability are derived, not stored; `not_applicable` is not an observed value | §3.2, §3.3, §12 |
| D8 | **`measurement_kind` catalog referenced but never defined** | DEEPSEEK-3 | Catalog defined as a separate versioned, reviewed artefact (id, version, allowed units/subjects/qualifiers, comparison rule for differing reporters, model bindings, evidence, reviewer); named in the release manifest and the evidence-foundation phase; distinguished from the §4 knowledge catalog | §3.2, §12, §13 |

---

## 2. HUMAN decisions applied from `decisions.md`

Applied as written, with no detail added that HUMAN did not give. Each is removed from the open list.

| ID | Applied to | What changed in v0.5 |
|---|---|---|
| FB-D1 (Europe) | §1.1, §4.5, §7, §9.1 note, §10, §14 | MVP market is the EU/EEA, UK and Switzerland, and generally every country with an API ("has an API" is the inclusion rule, not a list). North America and `SAE_J3400` are later-phase. Consequence stated: no single regulator, recall source or legal frame; connector types and protocols are set per country in the manifest. US seed examples are marked illustrative, not MVP evidence. §10 stays a proposal for FB-D4. Recall row in §14 no longer assumes one regulator |
| FB-D2 (clearance semantics) | §4.4, §5, §12 | Pending passages replaced by the settled semantics plus the five amendments (fail closed on `other`/unmapped; authorized actor per class; users raise, never clear; equipment vs vehicle/campaign scope, most restrictive wins; re-verification prompt, never expiry by time). Restriction-to-behaviour table added. Emergency numbers are reviewed per-country configuration. Fixture row added |
| FB-D3 (emergency stop, stuck connector, screening) | §4.7, §5, §6.1, §12, §13 | App never originates an emergency-stop instruction (operator-published, registry-approved guidance may be shown as operator-originated). Stuck-connector playbook required, OEM/standards-sourced, never advises force; says so and escalates when no OEM procedure exists. Every session starts with hazard screening, also on free text and voice; photos only raise a question; station fault codes alone are not evidence of fire. §5 observation rows are now visibly driver-reported or feed-reported |
| FB-D5 (cached packages) | §4.1, §12 | Risk-based degradation table (safety content always; restrictions never cleared offline, recall status stays `unknown`; playbooks with a notice; withdrawn items; no offline LLM explanations). Stale data never more permissive. Weak connectivity noted; no hard block on "cannot verify" |
| FB-D7 (Option A) | §6.2, §6.3, §12 | Pending passage replaced by the documented, not yet calibrated, ordering; calibration stays a planned follow-up in §6.3; ranking is not blocked. The round-2 D6 reference ("ordering follows the FB-D7 policy once decided") now reads as settled. No numbers or sources added |

The legal-review notes in `decisions.md` (safety-policy wording, emergency message, with FB-D4) are recorded in §5 and §4.7 as non-blocking.

---

## 3. Decisions for HUMAN — carried forward (single open list)

HUMAN is not answering during the automated loop. CLAUDE did not decide any of these. Reviewers must not raise them as `blocking`/`major`.

| ID | Question | Spec § | Status |
|---|---|---|---|
| FB-D4 | Legal/privacy basis (GDPR frame for the EU/EEA part, lawful basis per purpose, DPIA, LLM processor agreement as release gates; UK and Switzerland have their own rules) — needs legal review | §10 | open; no new evidence this round. Not settled by FB-D1 |
| FB-D6 | Photo-processing boundary and retention (client vs server vs provider; retention and deletion incl. derived stores) | §10 | open |
| FB-D1a | Which API makes a country eligible (recall/safety data, charge-point status, location data…)? The spec names none | §1.1, §14 | open, from `decisions.md` notes |
| FB-D1b | Which countries launch first? | §1.1 | open |
| FB-D1c | Is a country without a usable API excluded, or served in a reduced mode? | §1.1 | open |
| FB-D2a | Period after which advice to other drivers about an equipment restriction downgrades to "unverified, last reported on <date>" | §5 | open; no number invented |
| FB-D5a | Hard age limit after which a cached package is restricted to safety content plus an "update when you have signal" message | §4.1 | open; no number invented |

FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are settled and no longer open. FB-D1a–c, FB-D2a and FB-D5a are follow-up parameters derived from the notes in `decisions.md`; the "a/b/c" ids are mine, for tracking only.

---

## 4. Rejected / deferred / partial

**None rejected.**

| Item | Disposition | Reason |
|---|---|---|
| GROK-2 — CHAdeMO stage order | **Accepted, provisional** | Round 2 left the order unspecified for lack of a source. GROK now cites a vendor library note (medium confidence). The order is added labelled provisional, tied to [S11], and flagged for confirmation against the CHAdeMO text before encoding. I did not re-fetch the note |
| GROK-1, GROK-2 — annex and vendor-page claims | **Accepted with attribution** | Not re-fetched by me; the spec says GROK read them on 2026-10-21 |
| DEEPSEEK-2 — equal location required for any comparison | **Partial** | Kept as the default; GROK-3's exception is allowed only through an explicit catalog rule (see Result) |
| CHATGPT-3 — concrete vocabularies for `operational_state`, `power_sharing_state` | **Deferred** | The finding asks for versioned vocabularies including `unknown`, not values. Listing values would be invention; they are bound to the release manifest |
| DEEPSEEK-1 — stage `not_applicable` as an enum value | **Adjusted** | `not_applicable` is derived from the profile, not observed, so it is not a `stage` value (§3.2, §3.3). Stage success/failure outcome per event is not specified further; a round-4 reviewer may raise it |

---

## 5. Traceability

| Review finding | Item | Disposition |
|---|---|---|
| CHATGPT-1 | D4 | accepted |
| CHATGPT-2 | D5 | accepted |
| CHATGPT-3 | D6 | accepted; vocabulary values deferred |
| DEEPSEEK-1 | D7 | accepted; `not_applicable` kept derived |
| DEEPSEEK-2 | D3 | accepted; duplicate of GROK-3 (partial on comparison rule) |
| DEEPSEEK-3 | D8 | accepted |
| GROK-1 | D1 | accepted (major) |
| GROK-2 | D2 | accepted; CHAdeMO order provisional |
| GROK-3 | D3 | accepted |

All 9 raw findings are accounted for above.

---

## 6. Round completeness

CHATGPT, DEEPSEEK and GROK all delivered complete reviews. CURSOR's consistency pass was not run. v0.5 added several new tables and fields (§3.3 profiles, §4.1 cache table, §5 clearance and screening, `stage`, `recharging_point`), so a CURSOR consistency check on v0.5 (cross-references, field names, enum drift) remains advisable but is optional for the loop.
