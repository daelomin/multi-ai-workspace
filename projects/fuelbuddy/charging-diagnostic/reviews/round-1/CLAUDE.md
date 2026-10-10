# CLAUDE review — round 1

**Spec version reviewed:** v0.2 (11 October 2026)
**Reviewer:** CLAUDE (Claude Opus 5.5)
**Sources checked:** 11 October 2026

**Overall:** v0.2 is a strong baseline. It already separates facts from hypotheses, puts safety before ranking and refuses unverified seed data. The main gaps are in the session-stage model, protocol coverage beyond OCPP/ISO 15118, the ranking formula, the LLM validator, and the European context (data sources, privacy law, recalls), which the spec treats as secondary although its examples are all US.

The two seed sources I could open (§7.1 S1 and S2) match the spec's wording; details in CLAUDE-3 and CLAUDE-4.

---

### CLAUDE-1 · Session stages are not a single linear sequence

- **Section:** §3.3
- **Type:** error
- **Severity:** major
- **Finding:** The stage list puts `authorization` before `communication_setup`. That holds for RFID or app authorization (external identification means), which can even happen before plugging in, but not for ISO 15118 Plug & Charge, where authorization happens after the vehicle and station have set up communication and a session. Recording "last successful stage" against a single fixed order will mislocate failures for Plug & Charge sessions.
- **Proposed change:** Keep the stage enum, but state that the order depends on the authorization method. Add an `authorization_method` field (`rfid`, `app`, `plug_and_charge`, `ad_hoc_payment`, `free`, `unknown`) and define the expected stage order per method. "Last successful stage" is then interpreted against that order.
- **Evidence:** reasoning from the ISO 15118-2 message sequence (contract authorization follows session setup and service selection); verify against the standard's sequence diagrams before encoding.
- **Confidence:** high on the principle, medium on exact message names.

### CLAUDE-2 · Missing protocol and connector families

- **Section:** §4.5, §4.2–4.3
- **Type:** gap
- **Severity:** major
- **Finding:** Error namespaces cover OCPP, ISO 15118, DIN SPEC 70121, vendor codes and vehicle DTCs. They miss: CHAdeMO (CAN-based, its own error and status flags), the IEC 61851-1 control-pilot states A–F (the most basic AC observable: state F is an error state, and "stuck in state B" is a frequent AC symptom), the SLAC/HomePlug Green PHY matching step that precedes ISO 15118/DIN communication, and, if North America stays in scope, SAE J3400 (NACS). GB/T and MCS are probably out of scope but should be named as such.
- **Proposed change:** Add namespaces `IEC61851_CP_STATE`, `CHADEMO`, `SLAC`, and `SAE_J3400` (if NA in scope). Add a `communication_setup` sub-step for SLAC. Add an explicit "out of scope" list (GB/T, MCS, wireless charging).
- **Evidence:** reasoning only (standard structures); no specific codes are proposed, so none need verifying here.
- **Confidence:** high.

### CLAUDE-3 · S1 Hyundai recall: verified, but two limits must be encoded

- **Section:** §7.1, §8 A
- **Type:** inconsistency
- **Severity:** major
- **Finding:** The owner notice matches the spec: NHTSA 24V-868 / Hyundai campaign 272, 2022–2024 IONIQ 5 and 2023–2025 IONIQ 6; the ICCU's MOSFET can fail and open its fuse, the 12 V battery stops charging, and drive power is gradually lost. Remedy: ICCU software update, and ICCU and fuse replacement if needed. However: (a) the notice gives **no build-date range** (placeholder only) and (b) **no charging restriction or charging instruction**. The failure presents through 12 V / fail-safe warnings and power loss, not through a charging error.
- **Proposed change:** In the seed record, set build range to "unknown — take from the Part 573 defect report", and record "no interim charging restriction in the owner notice". In example A, add that ICCU applicability is checked through **vehicle warnings and low-voltage symptoms**, never inferred from the station error.
- **Evidence:** [Hyundai owner notice, 24V-868](https://static.nhtsa.gov/odi/rcl/2024/RCONL-24V868-8658.pdf), checked 2026-10-11.
- **Confidence:** high.

### CLAUDE-4 · S2 Mercedes CLA: verified; connector wording ambiguous

- **Section:** §7.1, §8 B
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The page confirms up to 320 kW DC, 800 V architecture, an included CCS-to-NACS adapter, and that 400 V DC charging needs a factory converter offered from spring 2026: "Vehicles without the converter cannot charge at 400-volt DC chargers." Example B's reasoning is therefore right. But the page describes the CLA as having "both a J1772 plug and NACS charging port for DC Fast Charging", which does not clearly say which inlet serves AC; the spec's "NACS DC/J1772 AC" is an interpretation. It is also a "future vehicles" marketing page.
- **Proposed change:** Mark the AC/DC inlet split as unverified until confirmed in a specification sheet or owner's manual; snapshot the page (per §15).
- **Evidence:** [Mercedes-Benz USA, 2026 CLA](https://www.mbusa.com/en/future-vehicles/2026-mercedes-benz-cla-sedan), checked 2026-10-11.
- **Confidence:** high.

### CLAUDE-5 · OCPP 2.0.1 reports errors differently from 1.6

- **Section:** §4.5, §9.1
- **Type:** gap
- **Severity:** major
- **Finding:** In OCPP 1.6, errors arrive in `StatusNotification.errorCode` (fixed list) plus free-text `vendorErrorCode`/`info`. In OCPP 2.0.1, `errorCode` is gone from StatusNotification; errors come through `NotifyEvent` against device-model components and variables, with free-format `techCode`/`techInfo`. The mapping key in §4.5 ("message field") cannot represent a 2.0.1 event, and the only example is 1.6.
- **Proposed change:** For OCPP 2.x, extend the mapping key with `component`, `variable` and `techCode`. Add one 2.0.1 example to §9.1. State whether OCPP 2.1 is in scope.
- **Evidence:** [OCA, Improving Uptime Monitoring with OCPP v1.2 (Aug 2024)](https://openchargealliance.org/wp-content/uploads/2024/08/improving_uptime_with_ocpp_v1_2.pdf), checked 2026-10-11.
- **Confidence:** high.

### CLAUDE-6 · Europe has a public live-status source the spec doesn't use

- **Section:** §3.1, §14
- **Type:** gap
- **Severity:** major
- **Finding:** Under AFIR (Regulation (EU) 2023/1804, Article 20), operators of public charging points must publish static data and dynamic data, including operational status, availability and ad hoc price, through national access points. Secondary sources date the obligation from 14 April 2025, with DATEX II delivery required from 14 April 2026, and dynamic updates within about a minute. In France, data.gouv.fr already hosts the national IRVE base (static) and per-operator "IRVE dynamique" datasets. This gives connector-level operational status in Europe without an operator contract. It is still operator-reported status, not internal diagnostics, which the spec's caution covers.
- **Proposed change:** Add "AFIR national access point (EU)" as a source class in §14 and to the public-data-assisted mode in §3.1, with its freshness and its limit (status, not diagnostics). Treat it as a Phase-1 input for the European MVP. (This workspace's DATEX II parser could be reused.)
- **Evidence:** [Spirii, AFIR Article 20](https://www.spirii.com/en/resources/blog/afir-article-20-what-cpos-need-to-know-about-it); [Innobu, DATEX II charging data obligation 2026](https://www.innobu.com/en/articles/datex-ii-charging-data-obligation-2026.html); [EUR-Lex, Delegated Regulation (EU) 2025/671](https://eur-lex.europa.eu/eli/reg_del/2025/671/oj) (metadata only); [data.gouv.fr, Base nationale des IRVE](https://www.data.gouv.fr/datasets/base-nationale-des-irve-infrastructures-de-recharge-pour-vehicules-electriques); [data.gouv.fr, IRVE dynamique example](https://www.data.gouv.fr/datasets/irve-dynamique-organisation-fuzed-fuzed). All checked 2026-10-11. **The dates come from secondary sources; confirm in the regulation text before relying on them.**
- **Confidence:** high that the obligation exists; medium on exact dates and format.

### CLAUDE-7 · The ranking formula favours specific known issues over common causes

- **Section:** §6.2
- **Type:** risk
- **Severity:** major
- **Finding:** `+ applicability_specificity` raises a cause's score merely because a precisely-matching known issue exists. A rare, well-documented defect would then outrank common, unspecific causes (station fault, authorization, cable, user setup) even with no supporting evidence. The spec already says severity is not likelihood; specificity is not likelihood either.
- **Proposed change:** (a) Specificity only modifies the score when at least one supporting observation exists. (b) Add a per-cause-class `base_rate` term, initially a documented ordering (ordinary causes first) and later estimated from confirmed FuelBuddy outcomes. (c) Add a test in §12: "a known issue with no supporting observation never outranks an ordinary cause with supporting observations".
- **Evidence:** reasoning only.
- **Confidence:** high.

### CLAUDE-8 · "Reject unsupported facts" needs a concrete, checkable rule

- **Section:** §9.2, §2
- **Type:** gap
- **Severity:** major
- **Finding:** A deterministic validator cannot judge free text for "unsupported facts". As written, the requirement is untestable, and §12 gates depend on it.
- **Proposed change:** Constrain the LLM to structured output: it selects only supplied `cause_id`s, `action_id`s and evidence IDs, and writes only `summary` as free text. Validate `summary` with mechanical rules:
  - no numbers, codes, model names or organisations that are absent from the input;
  - no percentages or probability words;
  - no imperative instruction that maps to an action outside `allowed_action_ids`;
  - no contradiction of `safety.state` (e.g. "safe to retry" when a hazard is set).
  
  On any failure, use the template fallback. Put OCR'd or user-typed station text in a separate data field, never in the instruction part of the prompt.
- **Evidence:** reasoning only.
- **Confidence:** high.

### CLAUDE-9 · Safety table: emergency stop and stuck cable are undecided

- **Section:** §5, §4.7, §3.3
- **Type:** question
- **Severity:** major
- **Finding:** Two common situations have no defined behaviour. (1) Whether "press the station's emergency stop, if it can be reached safely" is an approved driver action in a hazard. It is a physical control, not an app control, so the "no station control" rule doesn't settle it. (2) A connector that will not release after charging, a frequent non-hazard case that belongs to the `stopping` stage and needs an OEM-sourced unlock playbook.
- **Proposed change:** Add both to the safety/playbook backlog with the source type required (operator/OEM emergency guidance; OEM owner's manual for the unlock procedure). HUMAN to decide whether the emergency stop is ever a driver action.
- **Evidence:** reasoning only.
- **Confidence:** high that these are gaps; the answers need a qualified safety source.

### CLAUDE-10 · Privacy section should name GDPR and plan a DPIA

- **Section:** §10, §12
- **Type:** gap
- **Severity:** major (if the EU is in the MVP)
- **Finding:** §10 is built around consent. In the EU, GDPR applies: VIN and precise location are personal data, consent is not always the right lawful basis (performing the requested diagnosis may rest on contract), and processing location plus vehicle data at scale probably calls for a data protection impact assessment. Sending data to an LLM provider makes it a processor, which needs a processing agreement and, outside the EU, a transfer assessment. Community photos can contain number plates and faces.
- **Proposed change:** Name GDPR; define a lawful basis per purpose (diagnosis, analytics, community publication, model improvement); add "DPIA completed" and "LLM processor agreement in place" as release gates in §12; blur plates and faces before any community publication.
- **Evidence:** reasoning only. **A proposal for legal review, not a legal conclusion.**
- **Confidence:** medium.

### CLAUDE-11 · Unverifiable example error code

- **Section:** §4.5
- **Type:** risk
- **Severity:** minor
- **Finding:** I could not find `FAILED_AlignmentError` in any public source. ISO 15118-20 itself is paywalled, and "alignment" appears in public material mainly for wireless power transfer. The name may have been carried over from the original draft without verification.
- **Proposed change:** Remove the example, or keep it only after verifying the exact edition, message and charging mode in which it is defined.
- **Evidence:** web search on the exact string, 2026-10-11, no primary source found.
- **Confidence:** medium.

### CLAUDE-12 · Slow-charging analysis depends on an undefined model

- **Section:** §6.4
- **Type:** gap
- **Severity:** minor
- **Finding:** The expected envelope comes from "the existing FuelBuddy charging model", which this document never references or defines. The slow-charging tests in §12 cannot be written without it.
- **Proposed change:** Link the model's specification, or define its inputs and outputs here (inputs listed in §6.4; output: expected power range in kW with an evidence-strength flag).
- **Evidence:** reasoning only.
- **Confidence:** high.

### CLAUDE-13 · Conflicts and clocks need fields, not just a rule

- **Section:** §3.2
- **Type:** gap
- **Severity:** minor
- **Finding:** "Conflicting observations are retained and flagged" has no field to carry the flag. Timestamps come from different clocks (station, vehicle, phone, operator backend), and the spec's stage and freshness logic compares them.
- **Proposed change:** Add `conflict_group_id` and `clock_source` (`station`, `vehicle`, `phone`, `backend`, `unknown`) to the observation envelope.
- **Evidence:** reasoning only.
- **Confidence:** high.

### CLAUDE-14 · Who approves safety content?

- **Section:** §4.7, §12
- **Type:** gap
- **Severity:** minor
- **Finding:** Playbooks have an "approval status" and release requires "source-backed approval", but no role is accountable for safety approval, and no qualification is required.
- **Proposed change:** Define a `safety_reviewer` role (a qualified person, named per release) who must approve every safety rule and blocking-hazard playbook; record it in `reviewed_by`.
- **Evidence:** reasoning only.
- **Confidence:** high.

### CLAUDE-15 · Which market is the MVP?

- **Section:** §1.1, §7, §15
- **Type:** question
- **Severity:** major
- **Finding:** §1.1 says Europe and North America need separate records, but every seed source, recall reference (NHTSA) and example is US. If the MVP is European, the recall sources change: there is no EU-wide public VIN recall lookup equivalent to NHTSA's. Seed examples, connectors (CCS2 vs NACS) and privacy rules change too.
- **Proposed change:** HUMAN decides the MVP market. If Europe/France: add EU recall sources (OEM campaign lookups, EU Safety Gate) and replace or supplement the US seed examples.
- **Evidence:** reasoning only.
- **Confidence:** high.

---

## Top 3

1. **CLAUDE-15:** decide the MVP market. It changes sources, examples, connectors and privacy rules.
2. **CLAUDE-7:** fix the ranking so specific known issues can't outrank common causes without evidence.
3. **CLAUDE-8:** turn "reject unsupported facts" into concrete, testable validation rules.
