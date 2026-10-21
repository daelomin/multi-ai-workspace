# GROK review — round 2

**Specification:** local `spec.md`, v1.2, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `spec.md` v1.2 and `reviews/round-1/` (`CHATGPT.md`, `DEEPSEEK.md`, `GROK.md`, `CONSOLIDATION.md`). There is no `decisions.md`. Also read round-2 `CHATGPT.md` and `DEEPSEEK.md` so their findings are endorsed below and not given new ids. Accepted round-1 items D1–D10 are reopened only where the merged sentence still has no implementable rule. Open HUMAN decisions FB-D8 and FB-D9 are not re-raised.

**Overall:** 0 blocking, 2 major, 4 minor.

### GROK-1 · A short partial window wins Fastest

- **Section:** §7.1, §8 step 8, §8.1, §9
- **Type:** error
- **Severity:** major
- **Finding:** §7.1 records a partial window as the time to the SoC actually reached, with `window_completed: false`, and says that result is never ranked "as completing" the requested window. §8.1 Fastest is still the minimum modeled duration, and step 8 ranks an adapter when that duration improves on the baseline. The §9 example is a 350–400 V station and a battery that runs from 360 V to 420 V. Time to the SoC where the pack hits 400 V can be a short interval, while another adapter's completed 10–80% time is longer. The minimum picks the partial session. §9 says that case is never ranked; §8.1 does not filter on `window_completed` or on equal SoC intervals. Cheapest and best value use the same candidate set, so an adapter that cannot finish the window can win those categories on price or on a short clock.
- **Proposed change:** Add to §8.1: "Fastest, cheapest and best value admit only results with `window_completed: true` whose modeled duration covers the same requested SoC window. A result with `window_completed: false`, or with feasibility `unknown`, is not a candidate in those categories. Report it only with `reached_soc`, the limiting condition and the time to the SoC reached. Do not compare durations across unequal SoC intervals, and do not treat a shorter time to an earlier SoC as an improvement over a completed window."
- **Evidence:** reasoning only; the 350–400 V / 360→420 V case is the regression already in §9. This is the ranking sort. Round-2 DEEPSEEK-1 is the converting-path voltage predicate, and round-2 CHATGPT-2 is the direct-path resistive drop.
- **Confidence:** high

### GROK-2 · A booster drops the upstream adapter out of the current limit

- **Section:** §7.2 (Direct DC path and Voltage-converting path), §6.1, §9
- **Type:** error
- **Severity:** major
- **Finding:** The only current equation is direct-DC `I_series`, and that path is forbidden when any component converts voltage or the vehicle is boosting. The converting paragraph says each side has its own limits, coupled by `P_out <= P_in * conversion_efficiency`, and it never defines `I_in` or `V_in`. A passthrough cable or adapter upstream of a vehicle booster is a series limit at the station-side current. A hypothetical path is a 125 A passthrough adapter, a station that can supply more than 125 A at 400 V, and a booster feeding an 800 V pack. Nothing in the converting rule places the 125 A limit on the booster's input current. Reusing `I_series` would compare that 125 A with battery current, which is the wrong side of the converter and is the path the spec forbids. The adapter can be modeled as carrying only the battery current, so the estimate exceeds the adapter's continuous rating.
- **Proposed change:** Add to the voltage-converting path: "I_out(t) is the minimum of the converter output limit and I_vehicle_BMS, taken on V_batt. I_in(t) is the minimum of the station-connector limit, every passthrough cable or adapter on the station side of the converter, and the converter input limit, taken on the station voltage. P_out_kW = min(V_batt * I_out / 1000, P_vehicle_charge_curve). P_in_kW = V_station * I_in / 1000. Require P_out_kW <= P_in_kW * conversion_efficiency and P_in_kW <= P_station_available, and reduce I_in and I_out together until both hold. A passthrough adapter upstream of a booster is an I_in limit. Do not compare it with battery current, and do not use direct-DC I_series on this path." Add a regression: a 125 A passthrough adapter upstream of a booster, with the station able to supply more than 125 A, never produces an input current above 125 A.
- **Evidence:** reasoning only. The 125 A figure is the spec's own continuous-rating example in §7.3 (125 A is 50 kW at 400 V). Round-2 DEEPSEEK-1 is the preflight rule that applies V_batt on the station side of a booster; this finding is the current split after a converting path has been selected. Round-2 CHATGPT-1 is the missing power cap on a component that is already inside the min.
- **Confidence:** high

### GROK-3 · Best value has no total order

- **Section:** §8 step 8, §8.1
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Best value is the lowest delivered price per minute saved, "among eligible products with a comparable delivered price". No range defines comparable, after round-1 consolidation D5 rejected a tolerance constant and left thresholds unnamed. The score is also unordered when minutes saved are negative. Step 8 still ranks an adapter that improves cost, which includes a slower cheaper adapter. Price divided by a negative save is negative, and the lowest value selects that slower adapter. The sentence "a candidate that saves no time does not win on performance" does not define the score for a negative save.
- **Proposed change:** Replace the best-value score with: "Best value is the lowest delivered_price / minutes_saved among candidates with minutes_saved > 0 against the baseline. Delete the comparable-price filter. A candidate with minutes_saved <= 0 cannot win best value. If none remain, the category is empty and the reason says no candidate saves time."
- **Evidence:** reasoning only. Round-2 CHATGPT-3 is the separate case where no native session exists and the global improvement gate can suppress fastest and cheapest.
- **Confidence:** high

### GROK-4 · The no-adapter baseline has undefined series terms

- **Section:** §7.2, §8.1, §6.3, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** Direct-DC `I_series` always mins `I_cable` and `I_adapter`. The no-adapter baseline required by §8.1 and §9 has no adapter term, and a captive station cable may already be inside `I_station_connector`. The equation does not say to omit an absent term. A reading that treats the missing rating as unknown makes the baseline unverified under §7.1; a reading that treats it as 0 A makes the baseline current zero. `R_series_ohm` has the same hole: each passthrough accessory stores `resistance_ohm`, and the equation uses one symbol without stating that it is the sum of the in-path values. Two known resistances can be applied once, partially, or not at all, while the unknown-resistance rule only covers a wholly unknown loss.
- **Proposed change:** Add: "Omit I_cable or I_adapter when that element is not in the path. The no-adapter baseline mins the vehicle limit and the station-connector limit only, plus a captive cable only when its rating is separate from the connector limit. R_series_ohm is the sum of resistance_ohm over series elements that publish one. If any in-path resistance is unknown, the loss stays unknown under the existing rule. A missing adapter is an omitted term, not 0 A and not an unknown adapter rating."
- **Evidence:** reasoning only.
- **Confidence:** high

### GROK-5 · The AC illustration has no power equation

- **Section:** §7.2 (AC path), §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The AC path says to convert current to power with phase count and voltage, and illustrates that 32 A is about 7 kW single-phase and about 22 kW on 400 V three-phase. It does not state the expression. Using phase count as a multiplier on the line voltage gives 3 × 400 V × 32 A = 38.4 kW, which the illustration has already ruled out, while √3 × 400 V × 32 A is about 22.2 kW and 230 V × 32 A is about 7.4 kW. Power factor is unnamed. The §9 single-phase versus three-phase regression can pass with either number. This does not ask HUMAN to decide FB-D9.
- **Proposed change:** Add: "For a line-to-neutral voltage, P_ac_kW = U_ln_v * I_ac * n_phases * power_factor / 1000. For a line-to-line voltage on a three-phase supply, P_ac_kW = √3 * U_ll_v * I_ac * power_factor / 1000. The 32 A illustration uses 230 V line-to-neutral and 400 V line-to-line at power factor 1, rounded. Record the voltage convention and power factor in assumptions. Do not compute three-phase power as n_phases * U_ll * I."
- **Evidence:** reasoning only; 230 × 32 = 7360 W and √3 × 400 × 32 ≈ 22170 W. No standard text was opened.
- **Confidence:** high

### GROK-6 · The vehicle peak current has no duration to expire

- **Section:** §4.1, §6.1, §7.2
- **Type:** gap
- **Severity:** minor
- **Finding:** §7.2 holds every current limit at its peak only until that component's `peak_duration_s` is used. The charger profile and the passthrough accessory row have `peak_duration_s`. `dc_booster_ratings` names a peak duration in prose. The vehicle BMS limits are `dc_charge_current_continuous_a` and `dc_charge_current_peak_a`, with no duration column, and `bms_charge_limit_map` is described as a function of SoC and temperature. A vehicle peak current therefore has no stored time at which it must fall to the continuous rating, so the peak-hold sentence cannot be executed for `I_vehicle_BMS`.
- **Proposed change:** Add `dc_charge_peak_duration_s` to `vehicle_profiles`, or state that a vehicle peak duration is a field of `bms_charge_limit_map`. A peak current with no duration is not held for the whole session; the estimate uses the continuous rating and widens the range. Round-2 DEEPSEEK-5 remains the separate case of one `conversion_peak_duration_s` for two converter currents.
- **Evidence:** reasoning only.
- **Confidence:** high

Round-2 findings endorsed and not repeated: CHATGPT-1 (component power caps are outside the current min), CHATGPT-2 (station voltage must include `I * R` before the window is called feasible), CHATGPT-3 (a connector mismatch has no native session to beat), CHATGPT-4 (terminal power versus stored-energy power is still unnamed), DEEPSEEK-1 (on a booster the station-side voltage is not `V_batt`; the §7.1 phrase carried forward from round 1 does not define that voltage), DEEPSEEK-2 (the request object omits station power, sharing and the temperature trace), DEEPSEEK-3 (`limiting_condition`, bottleneck, configuration and timestamp are outside the contract, and `unknown` has no status), DEEPSEEK-4 (Fastest still "favors" measured performance; the later sentence that ties consider reliability and support has the same undefined weight), DEEPSEEK-5 (one conversion peak duration for two currents), DEEPSEEK-6 (the onboard charger is a converter without an efficiency or a DC output envelope), DEEPSEEK-7 (topology, peak and power are outside the §5 conflict list) and DEEPSEEK-8 (postcode versus country). FB-D8 and FB-D9 stay open HUMAN decisions.

**Top 3**

1. GROK-1: rank fastest, cheapest and best value only on completed windows of equal SoC span.
2. GROK-2: limit a passthrough adapter upstream of a booster at the booster's input current, with its own `I_in` equation.
3. GROK-3: score best value only for a positive time save, and drop the undefined comparable-price filter.

Result: complete
