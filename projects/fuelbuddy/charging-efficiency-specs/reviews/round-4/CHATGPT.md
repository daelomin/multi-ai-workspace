# CHATGPT review — round 4

Reviewed the local `spec.md` v1.4 after reading all round-3 reviews and `CONSOLIDATION.md`, the project README, and repository contribution/review instructions. This review checks internal consistency using hypothetical electrical examples; external product claims and the live schema were not verified. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are carried forward without new findings. Accepted round-3 changes are revisited only where the merged text still contradicts them.

**Overall:** 0 blocking, 1 major, 0 minor.

### CHATGPT-1 · Replace the old converter equations so they agree with the new segment boundaries

- **Section:** §7.1 converting-path voltage check; §7.2 voltage-converting path, segments around a converter, operating-point policy; §9
- **Type:** inconsistency
- **Severity:** major
- **Finding:** G1 correctly adds `P_out_kW = P_battery_kW + I_batt^2 * R_down / 1000`, but the preceding equation block still defines that same `P_out_kW` as `min(V_batt * I_out / 1000, P_vehicle_charge_curve, output power caps)`: at 400 V battery voltage, 100 A output current, a 40 kW battery charge-curve limit and 0.1 ohm downstream resistance, the old definition gives 40 kW while the new boundary requires 41 kW at the converter (410 V), so both equations cannot hold at that operating point. The old block also evaluates station current at `V_in` and caps converter-input power by station availability, while the new segment rule correctly applies station limits at `V_station` and `P_station_dc_kW`. In addition, §7.1 and the operating-point policy still require the station voltage itself to lie inside the converter-input range/intersection, rejecting valid separated terminal voltages when an upstream drop places `V_in` below `V_station`; implementers therefore must choose between contradictory normative rules, affecting feasibility, losses and rankings.
- **Proposed change:** Replace the original converting-path equation block with one consistent constraint system: “For one converter stage, `I_out_used = I_batt`; `P_battery_kW = V_batt * I_batt / 1000 <= P_vehicle_charge_curve`; `V_out = V_batt + I_batt * R_down`; `P_out_kW = V_out * I_batt / 1000`; `P_in_kW = V_in * I_in_used / 1000`; `P_out_kW <= conversion_efficiency * P_in_kW`; `V_station = V_in + I_in_used * R_up`; `P_station_dc_kW = V_station * I_in_used / 1000 <= P_station_available`. Apply the BMS and downstream-element current limits to `I_batt`, converter-output current/power/voltage limits at `V_out`, converter-input limits at `V_in`, and the station current envelope at `V_station`; retain all per-element caps, peak durations and unknown-data rules. The operating-point policy selects a feasible tuple satisfying these equations. Station voltage must be in the station range and converter-input voltage in its input range; a shared-voltage intersection is used only when their intervening resistance is zero. Apply the same local-boundary rule in §7.1 and between successive converter stages.” Add regressions asserting that the 400 V / 100 A / 0.1 ohm case has battery power 40 kW and converter output 41 kW (requiring at least `41 / 0.9` kW converter input at efficiency 0.9), and that a fixed 410 V station feeding a converter accepting 390–405 V through 0.1 ohm at 100 A is feasible at `V_in = 400 V` when all other limits permit, despite the empty nameplate-range intersection.
- **Evidence:** reasoning only; `400 * 100 / 1000 = 40 kW`, `100^2 * 0.1 / 1000 = 1 kW`, `V_out = 410 V`, and `41 / 0.9 ≈ 45.56 kW`. Upstream, `410 - 100 * 0.1 = 400 V`, with station power 41 kW and converter input 40 kW. This follows round-3 G1/G2: the new segment equations are correct, but the earlier equations and shared-voltage selection rule were not reconciled with them; it does not request re-adding the already accepted segment-loss or per-element-cap requirements.
- **Confidence:** high

**Top 3**

1. CHATGPT-1: make the converter equations, preflight and operating-point policy use one consistent set of terminal boundaries before implementation.
2. No additional finding.
3. No additional finding.

Result: complete
