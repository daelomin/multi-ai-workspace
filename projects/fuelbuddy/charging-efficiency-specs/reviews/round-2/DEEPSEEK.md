# DEEPSEEK review — round 2

Reviewed the local `spec.md` (v1.2, 2026-10-21) after reading `reviews/round-1/CHATGPT.md`, `reviews/round-1/DEEPSEEK.md`, `reviews/round-1/GROK.md`, `reviews/round-1/CONSOLIDATION.md` and the round-2 `CHATGPT.md`. There is no `decisions.md`. The open HUMAN decisions FB-D8 and FB-D9 are carried forward and are not re-raised here. No external source was re-fetched; all findings are internal reasoning about the specification's rules and schema sketch. Accepted round-1 items are not reopened except where the merged text is still incomplete or internally inconsistent, and each such finding names the consolidation item it follows from.

**Overall:** 0 blocking, 1 major, 7 minor.

### DEEPSEEK-1 · The SoC-window voltage rule cannot be evaluated on a converting path or an AC path

- **Section:** §7.1 (Voltage across the window), §7.2 (Voltage-converting path), §4.1, §2
- **Type:** error
- **Severity:** major
- **Finding:** §7.1 makes a combination eligible only when `V_batt(SoC, T)`, "on the station side of any booster", lies inside the station-connector and adapter voltage limits at every SoC of the window. On a `voltage_conversion` adapter or a vehicle booster there is no station-side voltage equal to `V_batt`: the station offers its own voltage (a hypothetical 400 V station) and the converter produces the battery voltage (an 800 V pack), which is precisely the case §2, §4.1 and §7.2 require the model to support. "On the station side of any booster" names no transform, and §7.2's converting path never derives a station-side voltage from `V_batt`, so the rule cannot be evaluated; read literally it rejects the boosted combinations the spec requires. The same rule is shaped around a DC battery voltage and is equally undefined for the AC path, which §8.1 evaluates whichever way FB-D9 is decided (this is not a request to decide FB-D9).
- **Proposed change:** Replace the first sentence of "Voltage across the window" with an interface-by-interface rule: "Overlap of nameplate voltage ranges is not sufficient. For a direct path, the voltage at the station connector and at each series element lies inside that element's limits at every SoC of the requested window. For a `voltage_conversion` adapter or a vehicle booster, preflight checks two interfaces throughout the window: the station's offered input voltage must lie inside the station-connector and converter-input limits, and `V_batt(SoC, T)` must lie inside the converter-output and battery limits; the converter's input and output voltage, current, peak duration and efficiency must cover the operating point at every SoC. A battery voltage outside the station's range is not a rejection when a converter separates the two sides, and a converter whose input range excludes the station's offered voltage is not eligible even when its output range covers the battery. For AC, apply the same per-interface rule to the AC supply, cable, inlet and onboard charger; do not use `V_batt` as the AC-side voltage." Keep the positive-net-power requirement and the existing `window_completed` / `unknown` outcomes.
- **Evidence:** reasoning only; §2 defines `voltage_conversion` with separate input and output envelopes, §4.1 requires booster input and output ratings, §7.2 defines the two-side calculation, and §7.1 applies `V_batt` to the station side. This is distinct from round-2 CHATGPT-2, which concerns the resistive drop at the station boundary of a direct path; this finding concerns the converting and AC paths, where the station-side voltage is not `V_batt` at all.
- **Confidence:** high

### DEEPSEEK-2 · The §8.2 request cannot carry the §7.2 time-varying inputs

- **Section:** §7.2 (Time-varying inputs), §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §7.2 admits `station_available_power_kw` (or a concurrent-session count over time), a battery-temperature trace and the ambient/preconditioning inputs, and requires an absent input to be recorded in `assumptions` with a widened range. The §8.2 request object carries `ambient_temperature_c` and `preconditioning_state` but has no field for available station power, concurrent sessions or a battery-temperature trace. A client that follows the contract can therefore never supply the optional inputs §7.2 defines, the implementation always holds full station power and constant battery temperature, and the §9 shared-cabinet regression cannot be exercised through the request contract. Consolidation D7 claimed §8.2 was updated; only two of the four inputs reached it.
- **Proposed change:** Add optional request fields `station_available_power_kw`, `concurrent_session_count` and `battery_temperature_trace_c` (each scalar or time series as §7.2 permits), and state that when they are absent the constant-temperature/full-power assumption is recorded in `assumptions` and widens the reported range.
- **Evidence:** reasoning only; comparison of §7.2's optional-input list with the §8.2 request object and the §9 shared-cabinet regression. Follows consolidation D7.
- **Confidence:** high

### DEEPSEEK-3 · The §8.2 contract omits required §7.3 outputs and leaves `unknown` unmapped

- **Section:** §7.3, §7.1, §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §7.3 requires a "Dominant bottleneck by SoC segment", the limiting condition, the "model/firmware configuration" and a calculation timestamp; §7.1 separately requires the limiting condition when `window_completed` is false. `required_per_recommendation` in §8.2 has no field for the limiting condition, the dominant bottleneck, the model/firmware configuration used, or the timestamp, so a response can satisfy the contract while omitting outputs the spec declares mandatory. §7.1 also says an indeterminate window produces "an explicit `unknown`", while the category statuses in §8.2 are `ranked | no_adapter_needed | no_eligible_candidate | insufficient_evidence`; `unknown` is never mapped to a response value. Consolidation D2 added `window_completed` and `reached_soc` to the contract but not the accompanying limiting condition.
- **Proposed change:** Add `limiting_condition`, `dominant_bottleneck`, `model_configuration` (accessory, vehicle and charger hardware/firmware used for the calculation) and `calculated_at` to `required_per_recommendation`; and either add `unknown` to the category status values or state that §7.1's `unknown` result is returned as `insufficient_evidence` with a reason.
- **Evidence:** reasoning only; direct comparison of the required outputs in §7.1 and §7.3 with the §8.2 contract. Follows consolidation D2.
- **Confidence:** high

### DEEPSEEK-4 · "Fastest" still contains an unweighted evidence preference

- **Section:** §8.1, §7.1, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** "Fastest" is defined as the minimum modeled duration "favoring verified compatibility and measured performance". That is a soft, unweighted preference inside the category, and it contradicts the same section's rule that evidence quality is an eligibility decision, "not a second weight in this score". Two implementations can return different fastest winners from the same eligible set: one takes the minimum duration, the other prefers a slightly slower candidate with a measured test, and neither violates the text. Consolidation D5 made the eligibility/weight separation explicit for best value but left this phrase in fastest.
- **Proposed change:** "Fastest: minimum modeled charging duration among eligible candidates under comparable conditions. Evidence quality is an eligibility gate (§7.1); it is not a duration discount or a weight. Report ties." Move any reliability or warranty preference to the stated tie-break list.
- **Evidence:** reasoning only; §8.1's fastest sentence against §8.1's best-value sentence and §7.1's fail-closed rule. Follows consolidation D5.
- **Confidence:** high

### DEEPSEEK-5 · A converting adapter has one peak duration for two current limits

- **Section:** §6.3, §7.2, §4.3
- **Type:** gap
- **Severity:** minor
- **Finding:** `charging_accessories` stores separate input and output peak currents for a `voltage_conversion` adapter but only one `conversion_peak_duration_s`. §7.2 requires each current limit to hold its peak value only for that component's `peak_duration_s`, and on a converter the input and output sides are distinct limits on distinct voltages. A datasheet that gives a different boost or peak duration on the station side and the vehicle side cannot be stored, so the peak rule is either unimplementable for the second side or applied with the wrong duration. The DDL is also narrower than consolidation D3's stated disposition, which describes input and output peak-duration fields.
- **Proposed change:** For `voltage_conversion`, add `input_peak_duration_s` and `output_peak_duration_s`; keep a single `peak_duration_s` for `passthrough`, and either remove `conversion_peak_duration_s` or define it as applying only when both sides share the same duration.
- **Evidence:** reasoning only; the DDL at §6.3 and the peak-hold rule at §7.2. Follows consolidation D3.
- **Confidence:** medium

### DEEPSEEK-6 · The onboard charger is used as a converter without its converter ratings

- **Section:** §7.2 (AC path), §6.1, §4.1
- **Type:** gap
- **Severity:** minor
- **Finding:** The AC path says battery-side current "comes from the onboard converter through the voltage-converting rule", and that rule requires separate input and output limits plus `conversion_efficiency`. The vehicle profile stores only `ac_phases`, `ac_current_max_a`, `onboard_charger_kw` and `dc_booster_ratings`; there is no AC-to-DC efficiency or onboard-charger output envelope. An implementation must therefore invent the efficiency, and §7.1's fail-closed rule ("unknown values are never treated as zero loss") gives it no declared default or uncertainty value to use.
- **Proposed change:** Either add `onboard_charger_efficiency`, `onboard_charger_dc_voltage_min_v`, `onboard_charger_dc_voltage_max_v` and `onboard_charger_dc_current_max_a` (or `onboard_charger_output_ratings`) to the vehicle profile and use them in the AC converting step, or state that the onboard charger is modeled with a documented default efficiency and output envelope and that the resulting assumption must widen the performance range.
- **Evidence:** reasoning only; §7.2's AC and converting paragraphs read against the vehicle fields in §6.1.
- **Confidence:** medium

### DEEPSEEK-7 · The §5 conflict rule does not cover topology, power or peak ratings

- **Section:** §5, §4.3, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 makes an accessory ineligible when retained sources disagree on direction, which connector faces the station, maximum voltage, continuous current or the protocol on either side. It does not list connector type, charging mode, electrical topology, peak current, peak duration, continuous or advertised power, or conversion efficiency. A product whose sources disagree on topology (`passthrough` versus `voltage_conversion`) or on peak/continuous power is not covered, so an implementation can take the favourable value into a ranking — the behaviour §5 says tracking a conflict must not permit, and the failure mode §8 warns about with headline kW. Consolidation D4 merged the rule with this list.
- **Proposed change:** Extend the list to "direction, which connector faces the station, connector type, charging mode, electrical topology (`passthrough`/`voltage_conversion`), maximum voltage, continuous and peak current, continuous and advertised power, peak duration, conversion efficiency, or the protocol on either side", and add a regression with conflicting advertised power or conflicting topology.
- **Evidence:** reasoning only; §5's conflict list against the accessory attributes in §4.3 and the DDL in §6.3. Follows consolidation D4.
- **Confidence:** high

### DEEPSEEK-8 · Delivered price is described per postcode but stored and requested per country

- **Section:** §4.4, §6.3, §8.2
- **Type:** question
- **Severity:** minor
- **Finding:** §4.4 computes delivered price for "a stated destination country/postcode", but `accessory_offers.ships_to` is an array of destination countries, the §8.2 request has only `delivery_destination` (a country code such as `"DE"`), and there is no postcode or region field in the offer table. If postcode granularity is intended — shipping prices commonly vary by destination — an offer whose shipping cost or availability depends on the postcode cannot be represented or requested, and the cheapest ranking silently operates at country level. If only country-level delivery is intended, the text should not imply postcode support.
- **Proposed change:** Either add `delivery_postcode` to the request and postcode/region eligibility or shipping rules to `accessory_offers`, or remove "postcode" from §4.4 and state that delivered price and availability are evaluated at country level. Consolidation D10's formula then applies at the stated granularity without further change.
- **Evidence:** reasoning only; §4.4 against `ships_to` in §6.3 and `delivery_destination` in §8.2. Follows consolidation D10.
- **Confidence:** high

I endorse the round-2 CHATGPT-1 (component power caps), CHATGPT-2 (station operating point with series resistance) and CHATGPT-3 (no-adapter gate versus fallback baseline) findings; none is repeated above. DEEPSEEK-1 is adjacent to CHATGPT-2 but covers the converting and AC paths, where the station-side voltage is not `V_batt`, rather than the direct-path resistive drop.

**Top 3**

1. DEEPSEEK-1: evaluate the SoC-window voltage rule per interface, because on a booster or converting adapter the station-side voltage is not `V_batt`.
2. DEEPSEEK-2: let the §8.2 request carry the station-power, sharing and battery-temperature inputs the §7.2 model already defines.
3. DEEPSEEK-4: remove the unweighted "favoring verified compatibility and measured performance" from Fastest so the category has one reproducible winner.

Result: complete
