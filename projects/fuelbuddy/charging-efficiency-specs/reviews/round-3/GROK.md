# GROK review — round 3

**Specification:** local `spec.md`, v1.3, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `spec.md` v1.3 and `reviews/round-2/` (`CHATGPT.md`, `DEEPSEEK.md`, `GROK.md`, `CONSOLIDATION.md`). There is no `decisions.md`. Also read round-3 `CHATGPT.md` and `DEEPSEEK.md` so their findings are endorsed below and not given new ids. Accepted round-2 items E1–E14 are reopened only where the merged sentence still has no determinate rule. Open HUMAN decisions FB-D8, FB-D9 and FB-D10 are not re-raised.

The direct-path fixed point is implementable as written: start from the current-limit minimum and reduce `I_batt` until the station envelope at `V_station = V_batt + I_batt * R_series_ohm`, the voltage window, `P_station_available` and the power caps all hold. That search is not given a new id. `P_station_dc_kW = P_battery_kW + (I_batt^2 * R_series_ohm) / 1000` matches `V_station * I_batt / 1000` when `P_battery_kW` is terminal power.

**Overall:** 0 blocking, 2 major, 4 minor.

### GROK-1 · The best-value fallback baseline changes the winner when a slower adapter is added

- **Section:** §8.1 (Best value), §9
- **Type:** error
- **Severity:** major
- **Finding:** When no completed no-adapter session exists, the baseline is the eligible candidate with the longest duration, and that candidate is inside the scored set. `minutes_saved` for every other candidate therefore depends on who else was discovered. With A at 45 min and €20 and B at 30 min and €80, the baseline is 45 min, A saves nothing, and B wins with `80 / 15`. Adding C at 60 min and €500, which itself saves nothing and cannot win, moves the baseline to 60 min: A scores `20 / 15` and B scores `80 / 30`, so A wins. One eligible adapter alone scores `minutes_saved` 0 against itself, so best value is empty until a second adapter appears. E6's positive-save rule is in place; this is the fallback duration that rule still uses.
- **Proposed change:** Replace the fallback sentence with: "If no completed no-adapter session exists, best value has no baseline. The category is empty and the reason says there is no completed no-adapter session to save time against. Do not use another candidate's duration as the baseline. Fastest and cheapest are unchanged." Add a §9 regression with the 45 min / €20, 30 min / €80 and 60 min / €500 set: the best-value winner with only the first two candidates stays the winner after the third is added, and a single eligible adapter does not become a best-value winner by being compared with itself.
- **Evidence:** reasoning only; `80 / 15 ≈ 5.333`, `20 / 15 ≈ 1.333`, `80 / 30 ≈ 2.667`. This is the E6 fallback after the merged positive-save rule, not a repeat of that rule.
- **Confidence:** high

### GROK-2 · A vehicle booster has no rule for when it is in the circuit

- **Section:** §7.1 (Converting path), §7.2 (Direct DC path and Voltage-converting path), §6.1, §9
- **Type:** gap
- **Severity:** major
- **Finding:** The direct path applies only when "the vehicle is not boosting", and the converting path applies for "a `voltage_conversion` adapter or vehicle booster". Nothing says when a vehicle that has `dc_booster_ratings` is boosting. One reading always inserts the booster. A hypothetical pack window of 600–800 V, a booster input window of 200–500 V, and a station at 700 V then has an empty station/booster-input intersection, so §7.1 rejects a session the pack can take directly. The other reading always bypasses the booster and drops its input current limit on a 400 V station. A `voltage_conversion` adapter and a booster that are both engaged are also one converting stage in the equations, so one of the two current limits can be omitted. The upstream passthrough case merged in E4 stays a single booster with an `I_in` limit.
- **Proposed change:** Add: "Insert the vehicle booster only when the profile says it is engaged at the station-side voltage, or when that voltage is outside the battery window and inside the booster input window and the profile says the booster can be bypassed otherwise. When it is disengaged, ignore its efficiency and input limit and use the direct path, or the adapter path alone. When a `voltage_conversion` adapter and the booster are both engaged, model two stages, each with its own input and output limits and efficiency, and an intermediate voltage equal to the upstream output and the downstream input. If the profile does not say whether the booster is in series, feasibility is `unknown` under §7.1." Add a §9 regression: pack 600–800 V, booster input 200–500 V, station 700 V, profile says the booster is bypassed inside the pack window → eligible on the direct path; the same vehicle at 400 V keeps the booster input limit; unknown engagement → `unknown`, not a ranked session.
- **Evidence:** reasoning only. The spec's §5 Porsche note (800 V pack, onboard DC charger for 400 V stations) is the same shape; those figures were not re-fetched. This is the engagement rule E3's per-interface check does not state.
- **Confidence:** high

### GROK-3 · "Improves cost" is undefined, so cheapest's candidate set is not fixed

- **Section:** §8 step 8, §8.1 (Cheapest)
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Step 8 admits an adapter, once a completed no-adapter session exists, only when it "improves modeled time or cost". No equation defines cost, and the no-adapter configuration has no delivered price. §8.1 cheapest is the lowest delivered price among safe compatible options and does not repeat the gate. A completed native session of 40 min, a 50 min adapter at €30 and a 35 min adapter at €200: reading the gate as purchase price against an unpriced native session drops the €30 adapter; reading §8.1 alone makes it cheapest. E6's gate is the source of the sentence; the two sections still disagree.
- **Proposed change:** Replace the step 8 clause with: "When a completed no-adapter session exists, an adapter is a candidate in fastest, cheapest and best value only when its completed-window duration is strictly shorter than that session. Cheapest is the lowest delivered price among those candidates. The no-adapter session has no delivered purchase price and is not a cheapest row. Delete the cost test." Add a §9 regression for the 40 min native session, the 50 min / €30 adapter and the 35 min / €200 adapter: cheapest is the €200 adapter.
- **Evidence:** reasoning only. Distinct from GROK-1, which is the fallback used when no native session exists.
- **Confidence:** high

### GROK-4 · The nameplate-current prohibition sits on the AC bullet only

- **Section:** §7.1 (AC path bullet), §6.2, §7.2 (Direct DC path), §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §6.2 stores `full_performance_from_v` and `voltage_current_envelope`. The only sentence that forbids nameplate current below the full-performance voltage is inside the AC-path bullet of §7.1. The direct and converting equations call `I_station_connector(V_station)` but never mention that column. A DC station with a nameplate current, `full_performance_from_v` above the battery voltage, and no envelope point at that voltage can be modeled at the nameplate. The incomplete-window rule is not this gap: the direct path already cites it.
- **Proposed change:** Move "Inside a published voltage range, use the current-versus-voltage envelope; do not apply the nameplate current below the voltage from which the source states full performance begins." to the paragraph above the three path bullets, so it covers direct, converting and AC paths. Below `full_performance_from_v`, use the envelope current when one exists; when it does not, the current is unknown and §7.1 returns `unknown`, not the nameplate. Add a §9 regression: DC nameplate current, `full_performance_from_v` above the battery voltage, no envelope point at that voltage → `unknown`.
- **Evidence:** reasoning only. The "full performance from 300 V" figure in §5 is the spec's reviewer-reported HYC150 note and was not re-fetched; the finding does not depend on that number.
- **Confidence:** high

### GROK-5 · AC input power is not wired to the converter equation, and supply voltage has no field

- **Section:** §7.2 (AC path and Voltage-converting path), §6.2, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The AC path says battery-side current comes from the voltage-converting rule, whose input power is `V_in * I_in_used / 1000`. The AC equations instead produce `P_ac_kW` from `U_ln_v` or `U_ll_v` and `power_factor`. No charger column and no §8.2 request field supplies that voltage or the power factor; §7.2 only says to record them in `assumptions`. One implementation substitutes `P_in_kW = P_ac_kW`. Another looks for a DC `V_in` and returns `unknown`. A third assumes 230 V, 400 V and power factor 1. Phase count on the cable is round-3 DEEPSEEK-4 and is not repeated here. AC candidates stay unranked until FB-D9; this is the evaluated power, not that decision.
- **Proposed change:** Add: "On the AC path, `P_in_kW` is `P_ac_kW` from the phase equations. Do not form `P_in` as `V_in * I_in` on the AC voltage. `ac_supply_voltage_v`, `ac_voltage_convention` (`line_to_neutral` or `line_to_line`) and `power_factor` are request or AC-outlet inputs. If any is absent, do not assume 230 V, 400 V or power factor 1; AC power is unknown and the result stays unranked." Add the three fields to §6.2 or §8.2 and a §9 regression: missing supply voltage → unknown AC power, not 7.4 kW or 22.2 kW.
- **Evidence:** reasoning only. `230 * 32 / 1000 = 7.36` and `√3 * 400 * 32 / 1000 ≈ 22.17` are the spec's own §7.2 illustration. No grid code was opened.
- **Confidence:** high

### GROK-6 · A concurrent session count does not change available station power

- **Section:** §7.2 (Time-varying inputs), §6.2, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The direct path requires `P_station_dc_kW <= P_station_available` after power sharing, and §6.2 stores `power_sharing_policy`. §7.2 says that when the optional inputs are absent the simulation holds full station power. It does not say how `concurrent_session_count` changes that power when `station_available_power_kw` is null. A count of 2 on a shared cabinet can be modeled at the full cabinet power, which is the same result as omitting the count. The §9 row only requires the request to carry both fields.
- **Proposed change:** Add: "`station_available_power_kw`, when present, is the connector limit after sharing. `concurrent_session_count` does not by itself divide cabinet power. If the count is present, `station_available_power_kw` is absent, and `power_sharing_policy` does not evaluate to a connector power, feasibility is `unknown` under §7.1. Do not apply the full-power default while a session count greater than one is present." Add a §9 regression: count 2, null `station_available_power_kw`, policy not evaluable → `unknown`, not the cabinet nameplate.
- **Evidence:** reasoning only. E12 added the request fields; it did not state this evaluation rule.
- **Confidence:** high

Round-3 findings endorsed and not repeated: CHATGPT-1 (upstream and downstream series resistance on a converting path still uses one `V_in` and one power for the station and the converter), CHATGPT-2 (no operating-point or ranking-duration policy inside the converter voltage intersection), DEEPSEEK-1 (a passthrough element's power cap is not applied on either side of a converter), DEEPSEEK-2 (`V_e` in the direct-path cap check is undefined), DEEPSEEK-3 (a null accessory peak rating has no "no peak mode" rule), DEEPSEEK-4 (AC phase count is taken from the supply while the cable stores none), DEEPSEEK-5 (one offer row cannot store per-destination shipping and VAT), DEEPSEEK-6 (the §8.2 contract has no price timestamp or exchange-rate provenance), DEEPSEEK-7 (the §5 conflict list omits minimum voltage and series resistance), DEEPSEEK-8 (a stored test has no measurement-boundary field) and DEEPSEEK-9 (charger protocol support and accessory interlock behavior have no columns). FB-D8, FB-D9 and FB-D10 stay open HUMAN decisions.

**Top 3**

1. GROK-1: do not use the slowest eligible adapter as the best-value baseline; adding an adapter that cannot win can change the winner.
2. GROK-2: state when a vehicle booster is in the circuit, so an in-window station is not rejected on the booster's input range.
3. GROK-3: drop the undefined cost test and admit, when a native session exists, only adapters that finish sooner.

Result: complete
