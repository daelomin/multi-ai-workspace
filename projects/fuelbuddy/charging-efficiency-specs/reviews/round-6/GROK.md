# GROK review — round 6

**Specification:** local `spec.md`, v1.6, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `spec.md` v1.6 and `reviews/round-5/` (`CHATGPT.md`, `DEEPSEEK.md`, `GROK.md`, `CONSOLIDATION.md`), plus the project README. There is no `decisions.md`. Also read round-6 `CHATGPT.md` and `DEEPSEEK.md` so their findings are endorsed below and not given new ids. Accepted round-5 items J1–J15 are reopened only where the merged sentence still has a wrong or indeterminate rule. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are not re-raised.

The stage-local current split from J1 still closes on the spec's own 400/600/800 V regression: 40 kW at 800 V is 50 A at the battery, 44.44 kW and 74.07 A at 600 V, and 49.38 kW and 123.46 A at 400 V when both efficiencies are 0.9 and every resistance is zero. That check is not given a new id. J2's segment-current rule, J3's cable-versus-converter terminal split (401 V / 40.1 kW versus 410 V / 41 kW), and J12's 500 A / 375 A peak-power window are likewise unchanged.

Round-6 CHATGPT-1 is endorsed. The budget is consumed only while the component is at its exact peak rating, so a 250 A continuous / 500 A peak part held at 400 A by another limit never leaves the peak cap. The §9 sentence "A 5-minute peak budget is still available after 10 minutes spent below the peak" records that hole. CHATGPT-2 is endorsed: with `display_currency` omitted, EUR 100 and USD 110 stay in different units, and `110 * 0.8 = 88` reverses the raw-number order. CHATGPT-3 is endorsed: an engaged booster with 0.1 ohm on the output, a 400 V battery and 100 A has `V_out` 410 V, `P_out` 41 kW, `P_in` 45.56 kW and `I_in` 113.89 A at a 400 V station. The station maximum does not bound converter output voltage, so the §9 "no positive feasible current" assertion is false for that booster.

Round-6 DEEPSEEK-1 is endorsed and is not the resistance-allocation finding below. The per-element paragraph still has no `V_e` between stage k and stage k+1, and the fallback names `V_station` for anything "upstream". At 74.07 A and 600 V the inter-stage cable is 44.44 kW and fails a 40 kW cap; at 400 V it is 29.63 kW and passes. DEEPSEEK-2 is endorsed: 0.9 × 0.9 is 0.81 from stage-N output to stage-1 input, not from stage-2 input to stage-1 input. `40 / 0.81 = 49.38` kW; `44.44 / 0.81 = 54.87` kW. DEEPSEEK-3, DEEPSEEK-4 and DEEPSEEK-5 are endorsed and not repeated: a request voltage with no request convention, a bypassed booster's resistances, and peak power absent from the §5 accessory conflict list.

**Overall:** 0 blocking, 1 major, 1 minor.

### GROK-1 · Known converter side resistances are not in the inter-stage segment

- **Section:** §7.2 (Voltage-converting path; Converter stages), §9
- **Type:** error
- **Severity:** major
- **Finding:** J15 stores booster input and output resistance and says each resistance belongs to exactly one of `R_up`, `R_mid_k` and `R_down`, but the only placement rules are the single-stage ones: every `input_resistance_ohm` goes to `R_up` (station to converter input) and every `output_resistance_ohm` goes to `R_down` (converter output to battery). The joint rule then sets `R_mid_k` to 0 ohm when no passthrough element exists, both adjacent side resistances are known, and the allocation to the joint is empty. Adapter output resistance and booster input resistance therefore land on the outer segments, or drop out, instead of sitting between the two stages. With 40 kW at the battery, efficiency 0.9 on each stage and 0.1 ohm of booster input resistance at 100 A, the inter-stage loss is 1 kW and station input is 50.49 kW. Placing that ohm in `R_up`, or zeroing `R_mid`, leaves the adapter output and the booster input at the same voltage and asks the station for 49.38 kW. The same 0.1 ohm between an adapter output maximum of 400 V and a booster input minimum of 400 V leaves no positive current; `R_mid = 0` accepts 100 A. That is the round-2 headroom failure moved to the joint J1 added.
- **Proposed change:** Add: "Stage 1's input resistance is in `R_up`. Stage N's output resistance is in `R_down`. Stage k's output resistance and stage k+1's input resistance are in `R_mid_k`, added to any passthrough `resistance_ohm` in that segment. A side resistance is never placed on the far side of another converter. `R_mid_k` is 0 ohm only when every resistance in that joint is known and each is 0 ohm; a known nonzero adjacent side resistance is not an empty allocation." Add a §9 regression: booster input resistance 0.1 ohm, no inter-stage cable, efficiencies 0.9, 40 kW at the battery and 100 A between the stages gives station input about 50.49 kW, not 49.38 kW. Adapter output maximum 400 V, booster input minimum 400 V, adapter output resistance 0.1 ohm and no cable: no positive feasible current. Accepting 100 A because `R_mid` was read as 0 ohm fails.
- **Evidence:** reasoning only; `100^2 * 0.1 / 1000 = 1` kW; `(40 / 0.9 + 1) / 0.9 = 50.4938…` kW; `40 / 0.81 = 49.3827…` kW; `100 * 0.1 = 10` V. The 50.49 kW figure is the §9 round-4 regression. J15 added the resistances and the empty-joint sentence; it did not say which segment receives the adapter's output resistance or the booster's input resistance.
- **Confidence:** high

### GROK-2 · The preflight still checks every converter output at the battery voltage

- **Section:** §7.1 (Voltage across the window, converting path), §7.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** J1 limits `V_out = V_batt + I_batt * R_down` to stage N inside §7.2. The §7.1 converting-path bullet still states that formula as the check "inside the converter-output limits", and it does not say the formula is stage N only. The following sentence extends "the same local-terminal rule" to successive stages without naming `V_out_k`. An adapter whose output range is 550–650 V, feeding a booster whose output at the battery is 800 V with `R_down` 0 and adapter `V_out` 600 V, is inside both envelopes. Applying the written formula to the adapter rejects it, because 800 V is outside 550–650 V. The §7.2 override is real; this bullet was not updated with it, so the preflight and the stage equations disagree on the same candidate.
- **Proposed change:** Replace the converting-path voltage list with: "`V_station` is checked against the station connector. `V_in_1 = V_station - I_in_1 * R_up` is checked against stage 1's input limits only. `V_out_N = V_batt + I_batt * R_down` is checked against stage N's output limits only. For each k, stage k's output limits are checked at `V_out_k` and stage k+1's input limits at `V_in_(k+1)`." Add a §9 regression: adapter output range 550–650 V, adapter `V_out` 600 V, booster output 800 V at the battery, `R_down` 0: eligible. Rejecting it because 800 V is outside the adapter output range fails.
- **Evidence:** reasoning only. The voltages are the §9 round-5 600 V / 800 V pair, applied to a hypothetical adapter output window that contains 600 V and excludes 800 V. J1 rewrote the §7.2 stage block and left this §7.1 formula unqualified.
- **Confidence:** high

**Top 3**

1. GROK-1: put adapter output resistance and booster input resistance in `R_mid`, so a known 0.1 ohm joint is not treated as 0 ohm and 100 A is not accepted across a 400 V / 400 V gap.
2. DEEPSEEK-1 (endorsed): give the inter-stage cable a terminal voltage, so 44.44 kW cannot pass a 40 kW cap by being evaluated at `V_station`.
3. CHATGPT-1 (endorsed): consume the peak budget for the whole time a component is above its continuous rating, not only while it sits on the exact peak.

Result: complete
