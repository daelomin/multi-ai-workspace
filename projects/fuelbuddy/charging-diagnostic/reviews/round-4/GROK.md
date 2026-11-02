# GROK review — round 4

**Specification:** local `spec.md`, v0.5, dated 21 October 2026.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `reviews/round-3/` (CHATGPT, DEEPSEEK, GROK, and `CONSOLIDATION.md`) and `decisions.md` before the current local spec. Also read the round-4 CHATGPT and DEEPSEEK reviews so the findings below do not repeat theirs. Settled FB-D1, FB-D2, FB-D3, FB-D5 and FB-D7 are fixed. Open FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a are not re-raised: no new evidence. Accepted round-3 items are reopened only where the merged sentence is still wrong or incomplete.

**Still holding, so not re-raised.** Re-read on 2026-10-21 from the Official Journal PDF of Commission Implementing Regulation (EU) 2025/655: Article 1(1)(b) (DATEX II, at least CEN/TS 16157-10:2022, from 14 April 2026), Article 2 (dynamic data within one minute, static data within twenty-four hours), Annex Table F (operational status `operational` / `non-operational` and availability `in use` / `reserved` / `not in use`, both at data level Point), and Annex Table B (recharging-point ID and number of connectors, both at data level Point). The §14 literals match. The Typhoon HIL DIN SPEC 70121 page still describes a DC-only sequence with no Plug & Charge, ExternalPayment as the only protocol payment option, an empty ContractAuthentication, then ChargeParameterDiscovery, CableCheck, PreCharge and PowerDelivery. The Siemens CHAdeMO note was not re-fetched; the provisional label in §3.3 stays appropriate.

**Agreement.** Round-4 CHATGPT-1 (stage events need an outcome before "last successful stage" can be derived), CHATGPT-2 (the station projection is still fixed to `connector_id`, and availability has no payload field) and CHATGPT-3 (simultaneously applicable restrictions need an intersection, not a single winner) are right. I would add one sentence to CHATGPT-1's repair: stage events with different `clock_source` values are not ordered against each other, and `received_at` is receipt order. Round-4 DEEPSEEK-1 through DEEPSEEK-6 are right and are not repeated here. One annex detail belongs with CHATGPT-2: Table B names the point identifier "Recharging Point ID code (Connector)" while its data level is Point, so a mapper that follows the parenthetical will undo the v0.5 subject split.

**Overall:** 0 blocking, 0 major, 5 minor.

### GROK-1 · `external_authorization` is required as a stage value and is absent from the stage list

- **Section:** §3.2, §3.3, §12
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §3.3 opens with a closed stage list that ends at `unknown`. §3.2 and the §12 Stages row then require `external_authorization` as its own `stage` value on a `session_stage_event`. An implementer cannot store the event the fixture requires without extending the enum the same section forbids. The same fixture says a PWM-only session "marks" four stages `not_applicable`, while §3.3 says applicability is derived and is not an observed value. Satisfying the fixture by storing `not_applicable` contradicts that rule.
- **Proposed change:** Add `external_authorization` to the §3.3 stage list and state that it is an event value, not a step in any profile order. State that `not_applicable` is not a `stage` value. In the §12 Stages row, replace "marks `communication_setup`, `authorization`, `parameter_negotiation` and `safety_checks` as `not_applicable`" with "derives those stages as `not_applicable` from the profile and does not store that word as `stage`".
- **Evidence:** reasoning only; local §3.2 `stage` field, §3.3 opening list, and §12 Stages row. This is the enum hole left beside the outcome gap in round-3 consolidation §4, which CHATGPT-1 covers separately.
- **Confidence:** high

### GROK-2 · The architecture diagram sends every restriction to a full stop

- **Section:** §2, §5, §6.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The §2 diagram routes "Hazard or restriction" to "Stop and escalate" and only continues to ranking when none is newly matched. Under that diagram, `charge_limited` and `do_not_charge_indoor` never reach the approved limited-charging instructions or the outdoor-only warning. §5, applying settled FB-D2, gives those two values their own driver-facing behaviour and reserves the full stop for `do_not_charge`, including `other` and unmapped values. An implementation that follows the diagram will not implement the settled table.
- **Proposed change:** Split the diagram's restriction edge. `do_not_charge`, `other`, and any unmapped value go to stop-and-escalate with the exact approved text and no retry or alternate-charging advice. `charge_limited` and `do_not_charge_indoor` continue only into the actions and warnings on their §5 rows. They do not enter ordinary cause ranking or an unrestricted playbook. Leave the settled behaviour table unchanged.
- **Evidence:** reasoning only; local §2 mermaid edge "Hazard or restriction" against the §5 restriction-to-behaviour table. This does not reopen FB-D2.
- **Confidence:** high

### GROK-3 · "External payment only" on the DIN row can be read as forbidding RFID and app

- **Section:** §3.3, §12
- **Type:** error
- **Severity:** minor
- **Finding:** The merged `din70121` cell says `plug_and_charge` is not allowed, then "external payment only". In FuelBuddy's own enum, external identification is `rfid`, `app`, or `ad_hoc_payment`. The secondary DIN description uses ExternalPayment as the only *protocol* payment option and sends ContractAuthentication empty. That forbids a contract certificate inside the session. It does not say the charger cannot identify the user by RFID or an app outside the protocol. An implementer who allows only `ad_hoc_payment` will reject ordinary DIN sessions.
- **Proposed change:** Replace "external payment only" with: "`plug_and_charge` is rejected. The protocol payment option is external, so the contract exchange is empty; `rfid`, `app`, `ad_hoc_payment` and `free` stay allowed and are recorded as `external_authorization` when an identification event exists. Do not treat this row as `authorization_method = ad_hoc_payment` only." Keep the DC-only order and the always-applicable `safety_checks`.
- **Evidence:** [Typhoon HIL, DIN 70121](https://typhoon-hil.com/documentation/typhoon-hil-software-manual/References/din70121_protocol.html), checked 2026-10-21: DC only, no Plug & Charge, "ExternalPayment is the only allowed PaymentOption", ContractAuthentication request contains no elements, then ChargeParameterDiscovery, CableCheck, PreCharge, PowerDelivery. Secondary description, not the DIN text. The misreading of the merged cell is reasoning only against §3.3.
- **Confidence:** high that the merged phrase over-reads the source; medium that every RFID session is in fact external to the protocol, because the DIN text itself was not opened.

### GROK-4 · A point that is in use still has no rule for its other connectors

- **Section:** §4.3, §14
- **Type:** gap
- **Severity:** minor
- **Finding:** v0.5 correctly stores AFIR status on `recharging_point` and forbids copying it onto each connector. Annex Table B also says a recharging point may have more than one connector and that only one can be used at the same time. Nothing in §14 or §4.3 stops a playbook from offering another connector on that same point as an alternate place to charge while the point's availability is `in use` or `reserved`. That alternate is the other plug of an occupied point, which the annex says cannot be used together with the first.
- **Proposed change:** Add to the §14 AFIR bullets: "A recharging point may have more than one connector, and only one of them can be used at the same time. While that point's availability is `in use` or `reserved`, do not recommend another connector on the same point as an alternate charging place. An alternate place is a different recharging point. Do not copy the point observation onto the sibling connectors." Add a §12 station-status fixture with one in-use point and two connectors: the alternate-charging advice names a different point.
- **Evidence:** [Commission Implementing Regulation (EU) 2025/655, Official Journal PDF](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202500655), Annex Table B, "Number of connectors", data level Point: "An electric recharging point may have one or more connectors, however only one can be used at the same time." Table F availability literals as already in §14. Checked 2026-10-21.
- **Confidence:** high

### GROK-5 · An idempotent replay can return an evaluation §2 says must not be displayed

- **Section:** §2, §11
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §11 says every mutation endpoint, including `POST .../evaluate`, returns the stored result for a replayed `Idempotency-Key` and appends nothing. §2 says a response whose revision or permissions are no longer current must be suppressed and reevaluated before display, and that hazard handling does not wait. A client that retries evaluate after a new hazard observation, reusing the key, is told by §11 to take the stored body. That body can still list actions the refreshed safety state no longer allows. §2 already forbids displaying it; §11 does not point at that check, so the API contract as written has two answers.
- **Proposed change:** In §11, after the replay sentence, add: "Replaying an evaluation returns the stored body and creates no second evaluation. Before display, that body is still subject to §2: if `input_revision` or the safety permissions are no longer current, suppress it and reevaluate. A replay must not restore actions a later hazard or restriction has removed."
- **Evidence:** reasoning only; local §11 idempotency paragraph against §2 session-revision paragraph and the §12 Concurrency row.
- **Confidence:** high

## Top 3

1. **GROK-2:** Route only `do_not_charge` (and unmapped values) to a full stop, and let `charge_limited` and `do_not_charge_indoor` reach the actions settled in §5.
2. **GROK-1:** Put `external_authorization` in the stage list, and keep `not_applicable` derived rather than stored.
3. **GROK-4:** While a recharging point is in use or reserved, do not offer another connector on that same point as an alternate place to charge.

Result: complete
