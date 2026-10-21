# GROK review — round 5

**Specification:** local `spec.md`, v1.5, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `spec.md` v1.5 and `reviews/round-4/` (`CHATGPT.md`, `DEEPSEEK.md`, `GROK.md`, `CONSOLIDATION.md`), plus the round-2 and round-3 consolidations and the project README. There is no `decisions.md`. Also read round-5 `CHATGPT.md` and `DEEPSEEK.md` so their findings are endorsed below and not given new ids. Accepted round-4 items H1–H14 are reopened only where the merged sentence still has a wrong or indeterminate rule. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are not re-raised.

The single-stage identity in the round-4 regression still closes: at 400 V, 100 A and 0.1 ohm downstream, `V_out` is 410 V, terminal power is 40 kW and `P_out_kW` is 41 kW (`100^2 * 0.1 / 1000 = 1`). That check is not given a new id. The direct-path identity `P_station_dc_kW = V_station * I_batt / 1000` is likewise unchanged.

Round-5 CHATGPT-1 is endorsed. "Each stage obeys the single-stage equations above" still sets `I_out = I_batt`, builds `V_out` from `V_batt`, and applies the vehicle BMS to every stage. With zero series resistance, efficiencies 0.9, voltages 400/600/800 V and 40 kW at the battery, battery current is 50 A and the adapter output current is 74.07 A. GROK-1 below is the passthrough element that sits in that same gap; CHATGPT-1's stage-local replacement does not rewrite the per-element paragraph, so both stay.

Round-5 CHATGPT-2 is endorsed. Downstream `R_batt_to_e` always adds `output_resistance_ohm`. With the battery at 400 V, 100 A, cable resistance 0.01 ohm and converter output resistance 0.09 ohm upstream of that cable, the cable terminal is 401 V and 40.1 kW. Including the 0.09 ohm yields 410 V and 41 kW.

Round-5 CHATGPT-3 is endorsed. Inter-stage loss of `100^2 * 0.1 / 1000 = 1` kW is upstream of the booster, so it is divided only by the adapter efficiency: `(40 / 0.9 + 1) / 0.9 = 50.4938…` kW. The merged regression's `(40 + 1) / 0.81 = 50.6173…` kW applies the booster efficiency to that loss as well. The sentence "Efficiencies multiply across stages (0.9 and 0.9 give 0.81)" needs the same qualification when the CHATGPT-3 regression is corrected: the product is the no-ohmic-loss case; an inter-stage `I^2·R` loss is not divided by the downstream efficiency.

Round-5 DEEPSEEK-1 through DEEPSEEK-8 are endorsed and not repeated: a null `full_performance_from_v`, the missing native-session `unranked` reason, charger and vehicle fields absent from the §5 conflict list, one `fx_*` pair for two source currencies, `peak_mode: rated` versus the missing-duration fallback, the undefined peak-budget clock, the unreachable `minutes_saved <= 0` rule, and AC request-versus-outlet precedence. On DEEPSEEK-7, the 40/50/45-minute regression also leaves cheapest and best value without a single status: the `no_adapter_needed` definition fits every category in that example, and `no_eligible_candidate` for "no positive `minutes_saved`" describes the case the gate excludes. That is the same inconsistency, so it has no new id.

**Overall:** 0 blocking, 1 major, 3 minor.

### GROK-1 · An inter-stage cable is checked at battery current

- **Section:** §7.2 (Voltage-converting path; Per-element power caps around a converter; Converter stages), §9
- **Type:** error
- **Severity:** major
- **Finding:** The single-stage block limits `I_batt` by "every passthrough element between converter and battery", and the per-element paragraph checks a battery-side element at `V_e * I_batt / 1000`. With two stages, the cable between the adapter and the booster is between the adapter and the battery, so both sentences apply the pack current to that cable. For a step-up booster the pack current is the smaller one: 40 kW at 800 V is 50 A at the battery and 111.11 A at a 400 V booster input with efficiency 0.9 and no downstream resistance. An 80 A cable, or a cable whose power cap is 42 kW, passes the written check (50 A and 40 kW) while carrying 111.11 A and 44.44 kW. The combination stays eligible above the cable rating. CHATGPT-1 makes each stage's own terminal limits local; this paragraph still has only `I_batt` and one `I_in_used`, so the middle segment stays on the pack current after that change.
- **Proposed change:** Add: "A path with N converter stages has N+1 conductive segments. Passthrough elements upstream of stage 1 are limited at `I_in` of stage 1. Passthrough elements between stage k and stage k+1 are limited at `I_out_k` (equal to `I_in` of stage k+1), at the voltage along that segment. Passthrough elements downstream of the final stage are limited at `I_batt`. The element's continuous and peak current limits and its power cap (`V_e * I_segment / 1000`) use that segment current. `V_e * I_batt` applies only downstream of the final stage." Add a §9 regression: booster input 400 V, battery 800 V, booster efficiency 0.9, battery-terminal power 40 kW, zero resistance between booster and battery, so the inter-stage current is 111.11 A. An inter-stage cable rated 80 A continuous, or 42 kW, forces the current down until the cable limit holds. A result that leaves 111.11 A in that cable because the battery current is 50 A fails the regression.
- **Evidence:** reasoning only; `40 * 1000 / 800 = 50` A; `40 / 0.9 = 44.444…` kW; `44.444… * 1000 / 400 = 111.111…` A; `400 * 111.111… / 1000 = 44.444…` kW; `800 * 50 / 1000 = 40` kW. This follows H2 and H3: the per-side caps and the stage join are both in v1.5, and the join assigns the middle element to the battery-side current.
- **Confidence:** high

### GROK-2 · Booster series resistance has no field, so every boosted path is indeterminate

- **Section:** §6.1, §7.2 (Voltage-converting path; Converter stages), §9
- **Type:** gap
- **Severity:** minor
- **Finding:** `dc_booster_ratings` is "required to calculate a boosted path" and lists input and output voltage, current, power, peak duration and efficiency. It does not list series resistance. §7.2 builds `R_up` and `R_down` from `input_resistance_ohm` and `output_resistance_ohm`, which exist only on `charging_accessories`, and an unknown segment resistance makes the result `unknown`. A vehicle booster with every listed rating and a null side resistance is therefore either incalculable, or, if the null is read as an omitted term, treated as zero ohms. The zero reading hides the `I·R` rise the round-2 regression already rejects (400 V battery, positive downstream resistance, station maximum 400 V). Adapter stages can store the ohms; the booster stage and a bare stage-to-stage joint cannot.
- **Proposed change:** Extend the §6.1 parenthetical with input and output series resistance, both required to calculate a boosted path. Add: "A null booster input or output resistance is `unknown` under §7.1 and is not stored as zero. Each of those resistances is counted in exactly one segment (`R_up`, `R_mid` or `R_down`). Where no passthrough element exists between two stages and both adjacent side resistances are known, `R_mid` is the sum of the resistances allocated to that joint; an empty allocation with both sides known is 0 ohm." Add a §9 regression: a booster with complete voltage, current, power and efficiency ratings and a null output resistance is `unknown`; the same booster with output resistance 0.1 ohm, 400 V battery, 100 A and a 400 V station maximum has no positive feasible current.
- **Evidence:** reasoning only; §6.1's required-field list, §7.2's `R_up`/`R_down` definitions and the unknown-resistance sentence, and the §9 round-2 case "400 V station maximum, 400 V battery, positive `R_series_ohm`". `400 + 100 * 0.1 = 410` V. H3 requires a known inter-stage resistance; the vehicle-side store for that resistance was not added.
- **Confidence:** high

### GROK-3 · The charger peak-power cap never enters the current limit

- **Section:** §7.1 (Published envelopes), §7.2 (Direct DC path), §6.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §6.2 stores `dc_power_peak_kw` beside `dc_power_continuous_kw`, and §7.2 holds each power limit at its peak only until `peak_duration_s` is used. §7.1's envelope rule always caps current with `dc_power_continuous_kw * 1000 / V_station` once `V_station` is at or above `full_performance_from_v`. During the peak window a charger at 400 V with a 200 kW peak cap and a 150 kW continuous cap is therefore limited to 375 A by the continuous formula, including when its peak current is 500 A. After the window, 375 A is the continuous cap; inside the window the peak cap allows 500 A. Two readings of the same row produce different currents and durations. The null-continuous-cap rule of H12 is a separate case and is unchanged.
- **Proposed change:** Add to the §7.1 envelope sentence: "While that charger's peak budget remains and `dc_power_peak_kw` is present, the power cap in this current limit is `dc_power_peak_kw`; after the budget is exhausted the cap is `dc_power_continuous_kw`. A present peak power cap binds during the peak window." Add a §9 regression: `dc_power_continuous_kw` 150, `dc_power_peak_kw` 200, `V_station` 400 V, peak current 500 A, `full_performance_from_v` 300, inside the peak window: current at most 500 A. After the peak budget: current at most 375 A.
- **Evidence:** reasoning only; `150 * 1000 / 400 = 375` A; `200 * 1000 / 400 = 500` A. H12 added both power columns and the continuous-cap formula; the peak column has no use in that formula.
- **Confidence:** high

### GROK-4 · The AC path has no peak-duration limit

- **Section:** §7.2 (AC path), §4.3, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The direct and converting paths hold a peak current or power only until `peak_duration_s` is used, then drop to the continuous rating. The AC path limits current by the EVSE, the cable and the inlet and converts that current with the phase equations, with no time argument and no drop to the continuous rating. An AC cable with `peak_mode: rated`, 32 A continuous, 63 A peak and `peak_duration_s` of 60 is therefore modeled at 63 A for the whole session: about 14.49 kW at 230 V single-phase and power factor 1, against about 7.36 kW continuous. DEEPSEEK-6's open question is when a DC peak budget is consumed; the AC equations never refer to the budget at all. FB-D9's interim leaves the AC result unranked, and this finding does not reopen that decision: the AC power figure is still produced.
- **Proposed change:** Add to the AC path: "AC current and power limits hold a peak value only until that component's `peak_duration_s` is used, then drop to the continuous rating, using the same peak-budget rule as the direct DC path." Add a §9 regression: an AC cable with 32 A continuous, 63 A peak and `peak_duration_s` 60 is not modeled at 63 A after that duration; at 230 V single-phase and power factor 1 the continuous power is about 7.36 kW.
- **Evidence:** reasoning only; `63 * 230 / 1000 = 14.49` kW; `32 * 230 / 1000 = 7.36` kW. The peak-hold sentence is under the direct DC path and is repeated for converter sides; the AC equations in the same section do not include it. The 230 V figure is the spec's own §7.2 illustration.
- **Confidence:** high

**Top 3**

1. GROK-1: limit the cable between two converter stages at the inter-stage current, so an 80 A cable is not accepted while it carries 111.11 A.
2. GROK-2: store booster input and output resistance, and keep a null resistance `unknown`, so a boosted path is not calculated at zero ohms.
3. GROK-3: apply `dc_power_peak_kw` during the peak window and `dc_power_continuous_kw` after it.

Result: complete
