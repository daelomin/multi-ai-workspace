# DEEPSEEK review — round 3

Reviewed the local `spec.md` (v1.3, 2026-10-21) after reading `reviews/round-2/CHATGPT.md`, `DEEPSEEK.md`, `GROK.md` and `CONSOLIDATION.md`, the project README, and the round-3 `CHATGPT.md`. There is no `decisions.md`. The open HUMAN decisions FB-D8, FB-D9 and FB-D10 are not re-raised. No external source was fetched; all findings are internal reasoning about the specification's rules, equations, contracts and schema sketch. Accepted round-2 items are not reopened except where the merged v1.3 text is still incomplete or internally inconsistent, and each such finding names the consolidation item it follows from.

**Overall:** 0 blocking, 1 major, 8 minor.

### DEEPSEEK-1 · A converting path never enforces a passthrough element's power cap at its own boundary

- **Section:** §7.2 (Direct DC path / Voltage-converting path), §4.3, §6.3, §9
- **Type:** error
- **Severity:** major
- **Finding:** The direct-DC path requires every series element to stay within its applicable continuous or peak power cap at its declared boundary (E1). The voltage-converting path lists "every passthrough cable or adapter on the station side" only as an `I_in` current limit and "any series element between converter and battery" only as an `I_out` current limit; its `P_out_kW`/`P_in_kW` lines say "output power caps"/"input power caps" without defining them, and the only cap named explicitly is the converter's ("a side's power cap"). A passive element on either side of a converter therefore has no stated power cap. With a hypothetical passthrough adapter rated 400 V, 250 A, 60 kW continuous upstream of a booster at a 400 V station, the equations allow `I_in` = 250 A and `P_in` = 100 kW through the adapter, above its 60 kW cap; the round-2 regression only tests the 125 A current limit. The same gap applies to a 60 kW passthrough element between the converter and the battery, where the output side can exceed its cap.
- **Proposed change:** Add to the converting path: "Every in-path cable or adapter on either side of the converter is also checked against its own applicable continuous or peak power cap at its own terminal voltage: upstream elements against `V_e * I_in_used / 1000`, downstream elements against `V_e * I_out / 1000`. 'Input power caps' and 'output power caps' mean the converter's own caps; they do not replace the per-element checks. Reduce `I_in_used` and `I_out` until those caps hold as well, and if an in-path element's power cap is unknown, apply §7.1's fail-closed rule." Use the `V_e` convention proposed in DEEPSEEK-2, applied with `I_in_used` on the station side and `I_out` on the battery side. Add a §9 regression: a 400 V / 250 A / 60 kW passthrough adapter upstream of a booster never carries more than 60 kW, and the same for a downstream passthrough element.
- **Evidence:** reasoning only; `250 A × 400 V = 100 kW`, and a 60 kW cap at 400 V binds at 150 A. The direct-path per-element clause is explicitly scoped to "Direct DC path (used only when no component converts voltage...)"; consolidation E1's converting-path disposition named only "converter input/output power caps". This is the unconverted elements around the converter, not a request to re-add E1.
- **Confidence:** high

### DEEPSEEK-2 · The direct-path per-element power-cap check uses an undefined `V_e`

- **Section:** §7.2 (Direct DC path), §6.3, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** E1's check requires `V_e * I_batt / 1000 <= that element's ... power cap` "at e's declared boundary", but the spec defines only `V_station = V_batt + I_batt * R_series_ohm` and defines `R_series_ohm` as the sum over all in-path elements. `V_e` is never defined, and `charging_accessories` stores one `resistance_ohm` per accessory with no stored terminal side. For an element near the station, `V_e` is close to `V_station`; for an element near the battery, it is close to `V_batt`. When a 60 kW cap is close to `V * I`, evaluating the same element at either terminal changes whether it passes, so two implementations can return different eligibility and rankings from the same data. The round-2 consolidation noted that per-element voltages "use the same sum" and that a finer distribution is left to implementation, but that note is not in the spec, "the same sum" does not say which terminal voltage to use, and the DDL stores no per-side resistance for a converter.
- **Proposed change:** Define the convention in §7.2: "`V_e` is the voltage at the element's station-side (higher-voltage) terminal, `V_e = V_batt + I_batt * R_{battery→e}`, where `R_{battery→e}` is the sum of the resistances of the elements between the battery and that terminal, including e's own resistance. If only the total `R_series_ohm` is stored, evaluate every element at the conservative upper bound `V_e = V_station` and record that assumption; if an element's resistance is unknown, apply the existing unknown-resistance rule." Add `input_resistance_ohm`/`output_resistance_ohm` (or a resistance distribution) for a `voltage_conversion` adapter if the per-segment check is extended to it. Add a §9 regression: two series elements with a power cap that passes at `V_station` but fails at `V_batt` (or the reverse) must produce a deterministic, stated result.
- **Evidence:** reasoning only; §7.2's `V_e` clause, the `R_series_ohm` definition, the DDL's single `resistance_ohm`, and the round-2 consolidation's note for round 3 ("the single summed `R_series_ohm` used for per-element voltages"). This is the direct path; round-3 CHATGPT-1 concerns the converter's upstream/downstream segments.
- **Confidence:** high

### DEEPSEEK-3 · A continuous-rated accessory with no peak mode has no rule and may fail closed

- **Section:** §7.1, §7.2 (Direct DC path), §6.3, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §7.1 makes eligibility depend on "continuous and peak current/power ratings" being known, and §7.2 says every current or power limit "holds its peak value only until that component's `peak_duration_s` is used, then drops to its continuous rating". The accessory DDL makes `peak_current_a`, `peak_power_kw` and `peak_duration_s` nullable, and a normal passive adapter or cable has no peak/boost mode. The spec never says what a null peak field means for an accessory. One implementation treats null as "no peak mode, use the continuous rating"; another applies the fail-closed rule literally and marks the accessory `unverified` because a peak rating is not known. The vehicle rule already resolves the analogous case (a peak current with no stored duration is not held and uses the continuous rating with a widened range), but no equivalent sentence exists for accessories.
- **Proposed change:** Add: "For a cable or adapter with no peak/boost mode, `peak_current_a`, `peak_power_kw` and `peak_duration_s` are null and the continuous rating applies at all times; a null peak rating is a known 'no peak mode', not an unknown, and satisfies the §7.1 rating check. A non-null peak current or power with a null `peak_duration_s` is not held: the continuous rating is used and the range is widened, as §6.1 provides for vehicles." Add a §9 regression: a 250 A continuous-only adapter is eligible and modeled at 250 A; an adapter with a 500 A peak and no duration is modeled at 250 A.
- **Evidence:** reasoning only; §7.1's rating list, §7.2's peak-hold sentence, the nullable DDL columns, and the contrast with §6.1's vehicle rule. This is the accessory counterpart of E11 (which covered the vehicle and converter sides).
- **Confidence:** high

### DEEPSEEK-4 · The AC power rule uses the supply's phase count, but a cable or adapter has no phase count

- **Section:** §7.2 (AC path), §4.3, §6.1, §6.2, §6.3, §9
- **Type:** error
- **Severity:** minor
- **Finding:** The AC path says to "convert current to power with the supply's phase count and voltage". The vehicle stores `ac_phases` and a charger stores `ac_outlet_phases`, but `charging_accessories` has no phase-count column and §4.3 does not list one for a cable or adapter. A hypothetical 32 A single-phase cable on a three-phase 400 V line-to-line EVSE is therefore modeled as `sqrt(3) * 400 * 32 / 1000 ≈ 22.2 kW`, not the 7.4 kW the cable can carry. An 11 kW three-phase onboard charger caps that at 11 kW rather than the correct 7.4 kW. The onboard-charger cap masks the error only when it is at or below the single-phase power.
- **Proposed change:** Add an `ac_phases` attribute to cables and adapters (§4.3, and a nullable `ac_phases` column in `charging_accessories`). State in §7.2 that the AC phase count is the minimum supported by the EVSE outlet, every in-path cable/adapter and the vehicle inlet (and consistent with the onboard charger), recorded in `assumptions`. Add a §9 regression: a 32 A single-phase cable on a three-phase EVSE with an 11 kW onboard charger yields about 7.4 kW (not 11 or 22.2 kW). This does not ask HUMAN to decide FB-D9; AC candidates remain evaluated and unranked.
- **Evidence:** reasoning only; `230 × 32 = 7.36 kW`, `√3 × 400 × 32 ≈ 22.17 kW` (the spec's own §7.2 example), the AC equations, and the DDL/field lists in §6.1, §6.2 and §6.3.
- **Confidence:** high

### DEEPSEEK-5 · One offer row cannot carry per-destination shipping and VAT for `ships_to`

- **Section:** §4.4, §6.3, §8.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.4 computes the delivered total for the destination country as `price + shipping_price` or `price + vat_amount + shipping_price`. The `accessory_offers` row stores one `country` (the spec does not say whether it is the seller's or the destination country), one `shipping_price`, one `shipping_currency` and one `vat_amount`, but `ships_to` is an array of destination countries. If the row is the seller's offer across those destinations, different destinations' shipping prices (and, where applicable, VAT amounts) cannot be represented, and the ranking would use one destination's figure for another. If `country` is instead the single destination, `ships_to` is misleading and one row cannot serve the other destinations. Either reading leaves the §4.4 formula unimplementable for a multi-country offer. This is about multiple destination countries in one row, not about postcode granularity (FB-D10 remains open at country level).
- **Proposed change:** Make the price dimensions destination-specific: either one offer row per (merchant, destination country) keyed by `destination_country`, or a separate `offer_destination_prices` table with `(offer_id, country, shipping_price, shipping_currency, vat_amount, availability, valid_until)`. Keep `country` as the seller/offer country, and have the ranking select the destination row for `delivery_destination`. Add a §9 regression: a merchant shipping the same adapter to DE and FR at different shipping prices produces different delivered totals and a different cheapest winner.
- **Evidence:** reasoning only; §4.4's formula and the `accessory_offers` DDL (`country`, `shipping_price`, `shipping_currency`, `vat_amount`, `ships_to`).
- **Confidence:** high

### DEEPSEEK-6 · The §8.2 contract cannot report the price timestamp or the exchange-rate provenance §4.4 requires

- **Section:** §4.4, §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.4 requires that when a currency conversion is needed "the exchange-rate source and timestamp are reported", and §8.2 says "Prices must be timestamped". The response contract has `price_total`, `currency`, `merchant`, `purchase_url` and `calculated_at`, but no offer observation time, no offer validity end and no exchange-rate rate/source/timestamp. `calculated_at` is the calculation time, not when the price was observed, so a response can satisfy the contract while omitting information the spec declares mandatory. A client cannot tell whether a price is fresh or how a converted total was derived.
- **Proposed change:** Add to `required_per_recommendation` (or a nested `price` object): `price_observed_at`, `price_valid_until` (nullable), `price_currency`, and, when conversion is used, `fx_rate`, `fx_source` and `fx_timestamp`. State that `price_observed_at` comes from the winning offer's `observed_at` and that `price_valid_until` is null when the offer has no `valid_until`. Add a §9 regression: an offer whose shipping price is converted from another currency returns the rate, source and timestamp.
- **Evidence:** reasoning only; §4.4's exchange-rate sentence, §8.2's "Prices must be timestamped" and the `required_per_recommendation` list.
- **Confidence:** high

### DEEPSEEK-7 · The §5 conflict list still omits minimum voltage and series resistance

- **Section:** §5, §4.3, §7.1, §7.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** E13 widened the conflict list to direction, station-facing connector, connector type, charging mode, topology, maximum voltage, continuous/peak current, continuous/advertised power, peak duration, conversion efficiency and protocol. It still lists only "maximum voltage", not minimum voltage, and does not list series resistance. Eligibility under §7.1 depends on the voltage range covering the station's operating voltage at every SoC, so a source conflict on `min_voltage_v` (for example 200 V versus 400 V) can pass a station the true minimum excludes, while §5 does not make the accessory ineligible because only the maxima agree. A conflict on `resistance_ohm` similarly changes `V_station` and whether a window is feasible under §7.2, and is not covered.
- **Proposed change:** Extend the §5 list to "minimum and maximum voltage, series resistance (including per-side resistance for a `voltage_conversion` adapter)" and add a §9 regression: two sources give different minimum voltages (or different resistances) for one accessory; it is not ranked and reports the conflicting field.
- **Evidence:** reasoning only; §5's list against §4.3's voltage/resistance attributes and the §7.1/§7.2 use of the minimum voltage and `R_series_ohm`. Follows consolidation E13, which added the other fields.
- **Confidence:** high

### DEEPSEEK-8 · A stored test has nowhere to declare its measurement boundary

- **Section:** §7.2 (Measurement boundary), §6.3, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §7.2 requires that "Every calculated curve and measured test declares its boundary" and that boundaries be compared only when they match. `accessory_test_results` stores `peak_power_kw`, `average_power_kw`, `duration_minutes` and `power_curve`, but no power-convention or boundary field; `evidence_quality` is not a boundary. The §8.2 `power_convention` is a property of the calculated recommendation, not of a stored test. A test measured at the station's DC output can therefore be attached to a battery-terminal calculation, or the reverse, with no stored flag to prevent the comparison; the "matching boundaries" rule cannot be executed.
- **Proposed change:** Add `power_convention` (at least `battery_terminal`, `stored_energy`, `station_dc`, or an explicit `unknown`) and, where useful, `measurement_boundary` to `accessory_test_results`; require it when `peak_power_kw` or `average_power_kw` is populated. A test with a null or `unknown` convention supports only an uncertainty range and is never a matching test. Add a §9 regression: a station-DC test is not attached to a battery-terminal estimate, and a stored-energy test is not compared without conversion.
- **Evidence:** reasoning only; §7.2's measurement-boundary sentence, the `accessory_test_results` DDL and the §8.2 per-recommendation `power_convention`. Follows E8, which introduced the boundary requirement without a storage field.
- **Confidence:** high

### DEEPSEEK-9 · Charger protocol support and accessory interlock behavior have no schema fields

- **Section:** §4.2, §4.3, §6.2, §6.3, §7.1, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.2 makes protocol support (e.g. CCS/ISO 15118/DIN SPEC, CHAdeMO) and authentication requirements required research attributes for a charger model; §4.3 requires connector lock/interlock behavior and fault shutdown for an accessory; §7.1's preflight must verify protocol negotiation and its fail-closed list requires "required interlock/protocol support" to be known. The §6.2 charger additions and §6.3 accessory DDL contain no protocol-support, authentication, interlock or fault-shutdown field. The vehicle has `dc_protocol_version` and the accessory has `protocol_in`/`protocol_out`, so the missing pieces are the charger side and the accessory's safety behavior. Unless the live audit finds existing columns (the §3 gate is unresolved), the preflight has no structured data to evaluate and implementations must either use unstructured JSONB or mark combinations `unverified` under the fail-closed rule.
- **Proposed change:** Add `protocol_support` (for example a JSONB array of `{protocol, revision}`) and `authentication_requirements` to `charger_profiles`; add `interlock_behavior` and `fault_shutdown` (or a `safety_behavior` JSONB) to `charging_accessories`; carry the vehicle/charger/accessory protocol versions in `accessory_compatibility`'s matching fields (it currently stores firmware only). Add a §9 regression: a vehicle supporting only DIN SPEC 70121 at a charger supporting only ISO 15118 is `unverified`/ineligible, not ranked.
- **Evidence:** reasoning only; §4.2 and §4.3 research attributes, §6.2/§6.3 field lists, and §7.1's preflight and fail-closed list. This is the charger/accessory counterpart of the accessory `protocol_in`/`protocol_out` columns, not a request to change the evidence threshold (FB-D8 stays open).
- **Confidence:** medium

I endorse the round-3 CHATGPT-1 (converter-side segment voltages and losses) and CHATGPT-2 (converter operating-point and ranking-duration policy) findings; neither is repeated above. DEEPSEEK-2 is the direct-path counterpart of CHATGPT-1, not a duplicate, and DEEPSEEK-1 is the remaining unconverted-element power-cap gap that E1 did not cover.

**Top 3**

1. DEEPSEEK-1: enforce every passthrough element's power cap on both sides of a converter, so a 60 kW adapter cannot be modeled at 100 kW.
2. DEEPSEEK-3: state the null peak-mode rule, so ordinary continuous-rated adapters are not all treated as unknown under the fail-closed rule.
3. DEEPSEEK-9: give the charger protocol, authentication and accessory interlock data a structured home, so the §7.1 preflight is implementable.

Result: complete
