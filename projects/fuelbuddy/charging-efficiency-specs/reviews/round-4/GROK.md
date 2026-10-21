# GROK review — round 4

**Specification:** local `spec.md`, v1.4, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Read `spec.md` v1.4 and `reviews/round-3/` (`CHATGPT.md`, `DEEPSEEK.md`, `GROK.md`, `CONSOLIDATION.md`). There is no `decisions.md`. Also read round-4 `CHATGPT.md` and `DEEPSEEK.md` so their findings are endorsed below and not given new ids. Accepted round-3 items G1–G16 are reopened only where the merged sentence still has a wrong or indeterminate rule. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are not re-raised.

The direct-path fixed point is unchanged and still closes: `P_station_dc_kW = P_battery_kW + (I_batt^2 * R_series_ohm) / 1000` matches `V_station * I_batt / 1000` when `P_battery_kW` is terminal power. That check is not given a new id.

Round-4 CHATGPT-1 is endorsed. The retained converting-path block still sets `P_out_kW` from `V_batt * I_out` and still applies the station current and `P_station_available` at `V_in`, while the segment block sets `P_out_kW = P_battery_kW + I_batt^2 * R_down / 1000` and applies station limits at `V_station`. §7.1 and the operating-point policy still require one shared station/converter-input voltage. The same split applies to the converter output: §7.1 puts `V_batt` inside the output window, and the segment rule puts output limits at `V_out`. No separate id.

Round-4 DEEPSEEK-1 through DEEPSEEK-8 are endorsed and not repeated: vehicle and charger `peak_mode`, single-phase voltage on a line-to-line supply, `ac_outlet_power_max_kw`, SoH, the unranked-result container, the baseline object and `minutes_saved`, FX storage and rate direction, and which voltage the booster bypass uses.

**Overall:** 0 blocking, 2 major, 3 minor.

### GROK-1 · Upstream of a converter, `V_e` is still the battery-side formula

- **Section:** §7.2 (Direct DC path; Segments around a converter), §9
- **Type:** error
- **Severity:** major
- **Finding:** G1 checks every passthrough element at `V_e * I / 1000` and then says `V_e` is "defined as on the direct path." That definition is `V_e = V_batt + I_batt * R_battery_to_e`, with the fallback `V_e = V_station` when only a total resistance is known. On the station side of a booster those variables are the wrong node and the wrong current. A buck example: battery 400 V, station 800 V, upstream current 110 A, cable cap 60 kW. The cable's station-side power is `800 * 110 / 1000 = 88 kW`, above the cap, but the battery-side formula yields about `400 * 110 / 1000 = 44 kW` and accepts the cable. A boost example with the imported fallback is the mirror: station 400 V, converter output 800 V, downstream current 100 A, cable cap 50 kW. Power at the converter output is `80 kW`, and a check at `V_station` yields `40 kW` and accepts it. Downstream of a single converter, the battery-referenced formula is the right pattern; upstream it understates power on a buck path, so a published power cap does not protect the cable.
- **Proposed change:** Replace the converting-path `V_e` sentence with: "On the battery side of a converter, `V_e = V_batt + I_batt * R_batt_to_e`, where `R_batt_to_e` sums `output_resistance_ohm` and the `resistance_ohm` of passthrough elements from the battery up to and including e. On the station side, `V_e = V_in + I_in_used * R_in_to_e`, where `R_in_to_e` sums `input_resistance_ohm` and the `resistance_ohm` of passthrough elements from the converter input up to and including e. Power is `V_e * I_batt / 1000` on the battery side and `V_e * I_in_used / 1000` on the station side. The direct-path fallback `V_e = V_station` applies only on a path with no converter. `R_down` is `output_resistance_ohm` plus downstream passthrough `resistance_ohm`; `R_up` is `input_resistance_ohm` plus upstream passthrough `resistance_ohm`. A resistance that is already stored on one of those columns is added once." Add a §9 regression: station 800 V, battery 400 V, upstream current 110 A, upstream cable cap 60 kW → ineligible; station 400 V, `V_out` 800 V, downstream current 100 A, downstream cable cap 50 kW → ineligible.
- **Evidence:** reasoning only; `800 * 110 / 1000 = 88 kW`, `400 * 110 / 1000 = 44 kW`, `800 * 100 / 1000 = 80 kW`, `400 * 100 / 1000 = 40 kW`. This is the voltage G1's per-element cap uses once a converter separates the two sides. It is independent of CHATGPT-1, which is the retained `P_out` definition and the shared-voltage preflight.
- **Confidence:** high

### GROK-2 · Two converter stages are joined at one voltage and one efficiency

- **Section:** §7.1 (Booster engagement), §7.2 (Voltage-converting path; Segments around a converter), §9
- **Type:** inconsistency
- **Severity:** major
- **Finding:** G13 says a `voltage_conversion` adapter and an engaged booster are two stages "joined at an intermediate voltage equal to the upstream stage's output and the downstream stage's input." The segment model then puts a resistive drop between any two terminals, so those two voltages differ whenever the inter-stage resistance and the current are both positive. The power equations are written for one converter: one `conversion_efficiency`, one `P_out_kW <= P_in_kW * conversion_efficiency`. Nothing states that the downstream stage's input power is the upstream stage's output power minus the inter-stage loss, or that both efficiencies apply. With stage efficiencies 0.9 and 0.9, chaining gives `0.81` and using either factor alone gives `0.9`, so the same limits produce two battery powers. The §9 booster regression is one stage (direct path at 700 V, booster retained at 400 V) and does not fix a two-stage path.
- **Proposed change:** Replace the join sentence with: "Number converter stages from the station toward the battery. Each stage has its own `V_in`, `V_out`, `I_in_used`, `I_out`, resistance pair and `conversion_efficiency`, and obeys the single-stage segment equations at its own terminals. Between stage k and stage k+1, `I_out_k = I_in_{k+1}`, `V_out_k = V_in_{k+1} + I_out_k * R_mid_k`, and `P_in_{k+1}_kW = P_out_k_kW - (I_out_k^2 * R_mid_k) / 1000`, with `P_out_k_kW <= conversion_efficiency_k * P_in_k_kW`. The two terminal voltages are equal only when `R_mid_k` is zero. An unknown inter-stage resistance or an unknown stage efficiency makes the result `unknown`." Add a §9 regression: adapter efficiency 0.9, booster efficiency 0.9, `R_mid` 0.1 ohm, intermediate current 100 A, battery-side power 40 kW. Required adapter input is greater than `(40 + 100^2 * 0.1 / 1000) / 0.81` kW, and `V_out` of the adapter is 10 V above `V_in` of the booster.
- **Evidence:** reasoning only; `0.9 * 0.9 = 0.81`, `100^2 * 0.1 / 1000 = 1 kW`, `(40 + 1) / 0.81 ≈ 50.62 kW`. G13 fixed when the booster is engaged; this is the electrical join between two engaged stages after G1's segment drops.
- **Confidence:** high

### GROK-3 · The charger's published kW cap has no column, and `full_performance_from_v` has no voltage node

- **Section:** §4.2, §6.2, §7.1 (Published envelopes), §7.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.2 requires a rated cabinet output in kW. §6.2 stores current, voltage and `full_performance_from_v`, and does not store that power. §7.2 forbids inventing a power cap from maximum voltage times maximum current, and it applies the nameplate current once the operating voltage is at or above `full_performance_from_v`. A connector published at 150 kW and 400 A then runs at `400 * 400 / 1000 = 160 kW` wherever the envelope has no lower point. The same paragraph applies the envelope rule on the AC path, and it never says that `full_performance_from_v` is the DC connector voltage `V_station`. A row with `full_performance_from_v` 300 and an AC supply of 230 V falls below the threshold, so the AC path becomes `unknown` where the §9 AC regressions expect about 7.4 kW. `ac_outlet_power_max_kw` is the separate outlet cap in DEEPSEEK-3.
- **Proposed change:** Add `dc_power_continuous_kw` and `dc_power_peak_kw` to `charger_profiles`. State: "`full_performance_from_v` is compared with the DC connector voltage `V_station` on direct and converting paths. It is not compared with `V_batt`, `V_in` or an AC supply voltage. At and above it, available current is the minimum of the nameplate or envelope current and `dc_power_continuous_kw * 1000 / V_station` when that power is present. Below it, missing envelope behaviour is unchanged. A null DC power cap is an unknown station power limit under §7.1 when the request also omits `station_available_power_kw`." Add a §9 regression: 400 A continuous, `full_performance_from_v` 300, `V_station` 400, `dc_power_continuous_kw` 150 → current at most 375 A. An AC supply of 230 V on that same charger row still follows the AC equations.
- **Evidence:** reasoning only; `400 * 400 / 1000 = 160 kW`, `150 * 1000 / 400 = 375 A`. The 150 kW and 400 A figures are the ones already quoted in §5; they were not re-fetched. The 230 V and 7.4 kW figures are the spec's own §7.2 illustration.
- **Confidence:** high

### GROK-4 · Category `status` never maps onto the empty-candidate cases

- **Section:** §8 step 8, §8.1, §8.2
- **Type:** gap
- **Severity:** minor
- **Finding:** The contract allows `ranked`, `no_adapter_needed`, `no_eligible_candidate` and `insufficient_evidence`. The prose defines a mapping only for `insufficient_evidence` (§7.1 `unknown`) and defines the reason strings for an empty best-value category. It does not say which status is used when a completed native session is strictly faster than every adapter, when best value has no baseline, or when no candidate has `minutes_saved > 0`. `no_adapter_needed` is otherwise unused. One implementation returns `no_adapter_needed` and another `no_eligible_candidate` for the same native-session gate. This leaves FB-D11's interim (empty best value, no baseline) as it is and only names the status that interim already requires.
- **Proposed change:** Add to §8.2: "`ranked` means the category has at least one result. `no_adapter_needed` means a completed no-adapter session exists and no adapter has a strictly shorter completed duration; adapter `results` are empty and that session's duration is the `baseline`. `no_eligible_candidate` means the category has no result for a known reason, including best value with no baseline and best value with no positive `minutes_saved`. `insufficient_evidence` stays the §7.1 `unknown` outcome." Add a §9 regression: native session 40 min, adapters 50 min and 45 min → fastest status `no_adapter_needed`; best value with no completed native session → status `no_eligible_candidate` and an empty result list.
- **Evidence:** reasoning only. The status strings are the §8.2 sketch; the native-session gate is the G14 text. FB-D11 is not reopened.
- **Confidence:** high

### GROK-5 · New path-changing attributes are outside the §5 conflict list

- **Section:** §5, §4.3, §6.1, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 makes an accessory ineligible when retained sources disagree on a closed list of fields. G9 added minimum voltage and series resistance. v1.4 also stores `peak_mode`, `ac_phases` and `dc_booster_engagement`, and a disagreement on any of those changes the current, the phase count or whether the booster is in the circuit. A pair of sources that disagree on `dc_booster_engagement` for one vehicle can still produce a ranked session, because that field is not in the list. The list is what the ineligibility rule checks.
- **Proposed change:** Extend the §5 disagreement list with `peak_mode`, `ac_phases` and `dc_booster_engagement` (including the bypass voltage condition). State that a conflict on a vehicle-profile field makes every candidate that depends on that profile `unverified`. Add a §9 regression: two retained sources, one `dc_booster_engagement: always` and one `bypassable`, → `unverified`, no ranked category.
- **Evidence:** reasoning only. The closed list is the §5 paragraph updated by G9; the three fields are the v1.4 additions in §4.3 and §6.1.
- **Confidence:** medium

**Top 3**

1. GROK-1: compute each passthrough element's voltage on its own side of the converter, so a buck-path cable is capped at station-side power.
2. GROK-2: give each converter stage its own terminal voltages, resistance and efficiency, with inter-stage loss between them.
3. CHATGPT-1 (endorsed): make the retained converter equations, the §7.1 voltage check and the operating-point policy use those same terminal boundaries.

Result: complete
