# DEEPSEEK review — round 5

Reviewed the local `spec.md` v1.5 (2026-10-21) after reading the round-4 reviews and `reviews/round-4/CONSOLIDATION.md`, the round-2 and round-3 consolidations, the project README, `generic/REVIEW_LOOP_GUIDELINE.md`, and the round-5 `CHATGPT.md`. There is no `decisions.md`. No external source was fetched; every finding is internal reasoning about the specification's rules, equations, contract and schema sketch, using hypothetical values. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are carried forward and are not re-raised. Accepted round-4 items are not reopened except where the merged v1.5 text remains incomplete or inconsistent; each such finding names the item it follows from. I endorse round-5 CHATGPT-1 (the remaining major item), CHATGPT-2 and CHATGPT-3 without new ids: CHATGPT-1's chained-stage inheritance is the main obstacle to a consistent two-stage path, and CHATGPT-3's corrected arithmetic is right (`(40 / 0.9 + 1) / 0.9 ≈ 50.49 kW`, not `(40 + 1) / 0.81 ≈ 50.62 kW`).

**Overall:** 0 blocking, 0 major, 8 minor.

### DEEPSEEK-1 · A null `full_performance_from_v` has no rule and can apply the nameplate current below the true threshold

- **Section:** §7.1 (Published envelopes), §6.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The envelope rule branches on `full_performance_from_v`: "Do not apply the nameplate current below the voltage from which the source states full performance begins"; below it the envelope current is used, and at or above it the current is the smaller of the nameplate/envelope and the power cap. §6.2 makes the column an optional, nullable addition, and neither §6.2 nor §7.1 says what a null threshold means. An implementation can read null as "no threshold" and apply the nameplate current over the whole voltage range, which overestimates power exactly where the source's current may be lower. The fail-closed list does not name the threshold, and the "if no envelope point exists" rule covers a missing envelope point, not a missing threshold. Two implementations can therefore rank the same charger differently, one with an unsafe overestimate.
- **Proposed change:** Add: "A null `full_performance_from_v` is not read as zero and not as 'full performance at every voltage'. If the source states no threshold and the envelope does not establish the available current at the operating voltage, the charger's available current is `unknown` and the combination is `unverified` (§7.1). If the envelope is complete, it is used at every voltage and the threshold's absence is recorded in `assumptions`; the nameplate current is never used below an unstated threshold." Add a §9 regression: a charger with a complete envelope and a null threshold is modeled from the envelope; a charger with a null threshold and no envelope point at `V_station` is `unknown`, never the nameplate.
- **Evidence:** reasoning only; §7.1's "Do not apply the nameplate current below ... (`full_performance_from_v`)" and "if no envelope point exists the current is unknown", §6.2's optional field list, and the H12 merge in round 4. The overestimate is the one the spec already guards against with `400 A × 400 V = 160 kW` versus a 150 kW cap (§9).
- **Confidence:** high

### DEEPSEEK-2 · `unranked` has no reason for an adapter excluded by the completed-native-session gate

- **Section:** §8 step 8, §8.1, §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §8 step 8 makes an adapter a candidate in fastest, cheapest and best value only when its completed-window duration is strictly shorter than a completed no-adapter session. Such an adapter is fully evaluated and completes the requested window, so §8.2's "`unranked` array holds every evaluated or unverified result that is not ranked" requires it to appear there. The only reasons listed are `unknown_attribute`, `partial_window`, `scope_undecided` and `insufficient_evidence`; none describes an eligible adapter that is merely slower than the native session. The §9 regression "Native session 40 min, adapters 50 min and 45 min" therefore has no representable entry for the two adapters. The category status `no_adapter_needed` describes the category, not the individual adapters.
- **Proposed change:** Add a reason `not_faster_than_native_session` (or `native_session_gate`) to §8.2's list and state that an adapter excluded only by the native-session gate appears in `unranked` with that reason, its `estimated_minutes` and its `minutes_saved` (negative or zero). Alternatively, if such adapters are deliberately not reported, say so and narrow "every evaluated ... result" accordingly. Add the reason to the §9 40/50/45-min regression.
- **Evidence:** reasoning only; §8 step 8's "only when its completed-window duration is strictly shorter", §8.2's `unranked` sentence and reason list, and the §9 round-3/round-4 native-session regressions (40/50/45 min). H8 created `unranked`; G14 created the gate; this is the intersection the reason list omits.
- **Confidence:** high

### DEEPSEEK-3 · §5's conflict rule omits a disagreement on a charger's or vehicle's calculation fields

- **Section:** §5, §6.1, §6.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §5 makes an accessory ineligible when retained sources disagree on a closed list of accessory fields, and extends the rule to a vehicle or charger field "that changes the path", naming only `dc_booster_engagement` and `dc_peak_mode`. A disagreement on a charger's `dc_voltage_min_v`/`dc_voltage_max_v`, `dc_current_continuous_a`, `dc_current_peak_a`, `peak_duration_s`, `dc_power_continuous_kw`, `dc_power_peak_kw`, `voltage_current_envelope` or `full_performance_from_v`, or on a vehicle's `battery_voltage_curve`, `dc_charge_current_continuous_a` or `dc_booster_ratings`, also changes feasibility, current and duration. The earlier sentence "Track conflicting sources explicitly" does not say the candidate becomes unverified, so a charger with two conflicting continuous-current ratings can still be ranked on one of them, which is the failure mode §5 exists to prevent for accessories.
- **Proposed change:** Extend the sentence to: "The same applies to a disagreement on any vehicle or charger field used in the calculation, including `dc_booster_engagement` (and its voltage condition), `dc_peak_mode`, the DC voltage range, continuous or peak current or power, `peak_duration_s`, `voltage_current_envelope`, `dc_power_continuous_kw`/`dc_power_peak_kw`, `full_performance_from_v`, the battery voltage curve and `dc_booster_ratings`; every candidate that depends on that profile is `unverified`." Add a §9 regression: two retained charger sources with different continuous-current ratings give `unverified`, no ranked category.
- **Evidence:** reasoning only; §5's second sentence and the §6.1/§6.2 field lists. H14 extended the list with `dc_booster_engagement` and `dc_peak_mode`; this names the remaining calculation fields, not a repeat of those two.
- **Confidence:** high

### DEEPSEEK-4 · The delivered price can need two conversions, but the contract has one `fx_*` pair and no defined target currency

- **Section:** §4.4, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The delivered total is `price + vat_amount + shipping_price`; `price` and `vat_amount` are in the offer's `currency`, while `shipping_price` is in `shipping_currency`. The response exposes one `fx_from`, `fx_rate`, `fx_source` and `fx_timestamp`, and §4.4 says "the exchange rate" in the singular. If the response `currency` differs from both source currencies, two conversions are needed and only one can be reported, so `price_total` is not auditable and the other conversion's provenance is lost. The spec also never says how the response `currency` is chosen (the offer currency, a request field, or a default), so both the direction and the number of conversions are undefined.
- **Proposed change:** Define the target: "`price_total` is expressed in the request's `display_currency` when present, otherwise the offer's `currency`." Replace the single `fx_*` fields with a `fx_conversions` array of records, one per converted source currency (`{fx_from, fx_rate, fx_source, fx_timestamp}`), or state that an offer requiring more than one conversion is ineligible. Add a §9 regression: an offer in EUR with shipping in USD and a response in GBP reports both conversion records (or is ineligible under the one-conversion rule).
- **Evidence:** reasoning only; §4.4's delivered-price sentence and currency assignments, §8.2's `fx_*` fields and `currency`, and the DDL's `accessory_offers.currency` / `accessory_offer_destinations.shipping_currency`. H10 fixed the direction of `fx_rate`; this is the case with more than one converted source or a third display currency.
- **Confidence:** high

### DEEPSEEK-5 · `peak_mode: rated` is defined as requiring `peak_duration_s`, contradicting the continuous-rating fallback

- **Section:** §4.3, §6.1, §6.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.3 says "`rated` needs the peak values and `peak_duration_s`", but the next sentence says "A peak current or power with no stored `peak_duration_s` is not held: the continuous rating is used and the range widened, as for vehicles (§6.1)", and the §9 regression explicitly models an adapter with a 500 A peak and no duration at 250 A with a widened range. If `rated` requires a duration, that adapter's data is invalid and the fallback contradicts the definition; if the fallback is intended, `rated` does not require a duration. The same wording propagates to `dc_peak_mode` for vehicles and chargers ("with the same meanings"). Two implementations can treat a rated peak without a duration as invalid (fail closed) or as continuous (eligible with a widened range), changing eligibility and ranking.
- **Proposed change:** Replace "`rated` needs the peak values and `peak_duration_s`" with "`rated` has stored peak values; the peak is held only when `peak_duration_s` is also stored. A peak value without a duration is modeled at the continuous rating with the range widened (as in §6.1); it is not `unknown` and does not fail closed solely for the missing duration." Keep `unknown` for a peak mode whose magnitude is unknown.
- **Evidence:** reasoning only; the two adjacent §4.3 sentences and the §9 regression "an adapter with a 500 A peak and no duration is modeled at 250 A with a widened range". H4 introduced `dc_peak_mode` and the "same meanings" clause; this resolves the `rated` definition it added.
- **Confidence:** high

### DEEPSEEK-6 · `peak_duration_s` has no rule for when the peak budget starts or how it accumulates

- **Section:** §7.2 (Direct DC path; Voltage-converting path), §6.1, §6.2, §6.3, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §7.2 says "Each current or power limit holds its peak value only until that component's `peak_duration_s` is used, then drops to its continuous rating." It does not say whether the budget is consumed from the start of the session, only while the component is actually at its peak, or cumulatively across intermittent peak use; whether it can be used again after a cooldown; or whether a second at the peak consumes a second when another limit (the charge curve or another component) was binding, so the current never reached the peak. A charger with a 5-minute boost and a vehicle that only reaches the boost current after 10 minutes of preconditioning gets a different duration under each reading, which can change the fastest and best-value winners. The §9 regression only checks that a peak held beyond the duration is rejected, not when the clock starts.
- **Proposed change:** Add a rule, for example: "`peak_duration_s` is a cumulative budget consumed only while the modeled current or power is at the component's peak rating; time spent below the peak does not consume it. Once the budget is exhausted, the continuous rating applies for the rest of the session and the budget does not regenerate. The start, consumption and exhaustion times are recorded in `assumptions`." Add a §9 regression: a 5-minute peak is still available after 10 minutes below the peak; intermittent peak use exhausts only its actual peak time.
- **Evidence:** reasoning only; §7.2's peak sentence, the §6.1/§6.2/§6.3 peak fields, and the §9 round-1 regression on a 500 A boost. No earlier consolidation defines the budget's start or accumulation.
- **Confidence:** medium

### DEEPSEEK-7 · The native-session gate makes the `minutes_saved <= 0` rule and its regression unreachable

- **Section:** §8 step 8, §8.1, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §8 step 8 makes an adapter a candidate in best value only when it is strictly faster than a completed no-adapter session. Under FB-D11's interim, the only baseline is that session, so every best-value candidate has `minutes_saved > 0`. §8.1's rule "A candidate with `minutes_saved <= 0` cannot win best value" and the §9 round-2 regression "a negative `minutes_saved` cannot win best value" therefore describe a state the gate makes impossible; a test cannot construct the case. Either the gate has an exception for equality or for a different baseline, or the rule and regression are stale. This is not a request to reopen FB-D11; it only asks that the interim's companion rule be made consistent.
- **Proposed change:** Either delete the `minutes_saved <= 0` clause and the negative-`minutes_saved` regression, or state the case in which it can occur (for example, if FB-D11 later adopts a reference-adapter baseline) and make that case conditional on the decision. If equality is meant to be allowed in best value, change "strictly shorter" to "not slower" and keep the rule.
- **Evidence:** reasoning only; §8 step 8's "strictly shorter", §8.1's "candidate with `minutes_saved <= 0`", §9 round 2's negative-`minutes_saved` regression, and FB-D11's interim (empty, no baseline). G14 created the strict gate; the rule predates it.
- **Confidence:** high

### DEEPSEEK-8 · The AC supply has two sources but no precedence rule

- **Section:** §7.2 (AC path, AC inputs), §6.2, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The AC inputs paragraph says the supply voltage, voltage convention and power factor "come from the request (`ac_supply_voltage_v`, `ac_voltage_convention`, `power_factor`; §8.2) or the charger outlet (`ac_outlet_voltage_v`, `ac_outlet_voltage_convention`, `ac_outlet_power_factor`)". It never says which source wins when both are present, or what happens when they disagree. With a 230 V request value and a 400 V line-to-line outlet value, one implementation can compute a single-phase result and another a three-phase result at the same current; the convention (line-to-neutral versus line-to-line) and the power factor have the same problem. This changes AC power, eligibility, duration and ranking.
- **Proposed change:** Add: "When both a request value and an outlet value are present, the request value is used and the outlet value is recorded as the superseded source; if both are present and inconsistent, the result is `unknown` unless the request explicitly marks the value as overriding. The source and the value used are recorded in `assumptions`." Add a §9 regression: request 230 V with an outlet declared 400 V line-to-line produces the stated outcome (request wins, or `unknown`), never an implicit mix.
- **Evidence:** reasoning only; the quoted §7.2 sentence, §8.2's request fields, and the §9 AC regressions (about 7.4 kW and 22.2 kW, based on the spec's own 230 V/400 V examples). G6 added both sources; it did not define precedence.
- **Confidence:** high

I also checked the points flagged in the round-4 consolidation's notes. The `// object or null` marker in the §8.2 sketch is illustrative, not a defect. The null-DC-power-cap rule (`dc_power_continuous_kw` absent and no `station_available_power_kw` → `unknown`) is deliberately fail-closed under H12; I am not reopening it, but phase 2 must populate that column or the three-category output will be empty for most chargers. The booster-engagement rule now references a defined voltage and the §9 520/480 V regression pins the outcome; I am not re-raising H11.

**Top 3**

1. DEEPSEEK-3: extend the §5 conflict rule to the charger and vehicle calculation fields, so a conflicting charger current, voltage or power rating cannot be ranked.
2. DEEPSEEK-1: give a null `full_performance_from_v` an envelope-only or fail-closed rule, so the nameplate current is never applied below an unstated threshold.
3. DEEPSEEK-2: add the native-session-gate reason to `unranked`, so every evaluated adapter has a contract home.

Result: complete
