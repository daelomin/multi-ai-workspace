# DEEPSEEK review — round 4

Reviewed the local `spec.md` v1.4 (2026-10-21) after reading all round-3 reviews and `reviews/round-3/CONSOLIDATION.md`, the project README and `generic/REVIEW_LOOP_GUIDELINE.md`, and the round-4 `CHATGPT.md`. There is no `decisions.md`. No external source was fetched; all findings are internal reasoning about the specification's rules, equations, contract and schema sketch, using hypothetical values. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are carried forward and are not re-raised. Accepted round-3 items are not reopened except where the merged v1.4 text still has no determinate rule; each such finding names the consolidation item it follows from. I endorse the round-4 CHATGPT-1 finding (converter terminal voltages and the retained equation block) and do not repeat it.

**Overall:** 0 blocking, 1 major, 7 minor.

### DEEPSEEK-1 · Vehicles and chargers have no `peak_mode`, so a continuous-only profile can fail closed

- **Section:** §7.1 (Fail closed), §7.2 (Direct DC path), §4.3, §6.1, §6.2, §6.3, §9
- **Type:** inconsistency
- **Severity:** major
- **Finding:** G4 fixed the null-peak ambiguity for accessories only: `peak_mode` (`none`/`rated`/`unknown`) exists on `charging_accessories` (§4.3, §6.3), but `vehicle_profiles` (§6.1: `dc_charge_current_peak_a`, `dc_charge_peak_duration_s`) and `charger_profiles` (§6.2: `dc_current_peak_a`, `peak_duration_s`) have no equivalent. Yet §7.2's direct path says "A null peak rating is read by `peak_mode` (§4.3), not guessed", and the same `I_series` minimum covers the vehicle BMS, the station connector, the cable and the adapter. For a vehicle or charger there is no `peak_mode` to read. §7.1's fail-closed list explicitly requires "continuous and peak current/power ratings" to be known, so a literal reading marks any vehicle or charger that publishes only a continuous rating `unverified`; that is a common profile, so ordinary combinations would return `insufficient_evidence` and nothing could be ranked. The opposite reading (a null peak means no peak mode, use the continuous rating) is the accessory rule and is not stated for vehicles or chargers. Two implementations therefore derive different eligibility and rankings from the same data — the exact ambiguity G4 removed for accessories.
- **Proposed change:** Extend the G4 rule to all three entities: add `peak_mode` (`none`, `rated`, `unknown`) to `vehicle_profiles` and `charger_profiles` (or state that a null peak field on them is read as `none` when the source publishes no peak, and as `unknown` only when a source indicates an unquantified boost). In §7.1, replace "continuous and peak current/power ratings" with "every applicable continuous and peak current/power rating: an entity with `peak_mode: none` needs no peak value and satisfies the check, while `peak_mode: unknown` fails closed". In §7.2, say that a null peak on a vehicle or charger is read by its `peak_mode`, as §4.3 provides for accessories. Add a §9 regression: a vehicle and a charger with continuous-only ratings (`peak_mode: none`) are eligible and modeled at their continuous ratings; `peak_mode: unknown` on either makes the combination `unverified`.
- **Evidence:** reasoning only; the quoted §7.2 sentence, §7.1's fail-closed list, and the field lists in §6.1, §6.2 and §6.3. This is the vehicle/charger counterpart of G4/DEEPSEEK-3 (round 3), which resolved the same ambiguity for accessories; it is not a repeat of that accepted text.
- **Confidence:** high

### DEEPSEEK-2 · A single-phase path on a line-to-line supply has no voltage rule

- **Section:** §7.2 (AC path, AC inputs), §6.2, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The phase count is the minimum over the EVSE outlet, every in-path cable/adapter, the vehicle inlet and the onboard charger, so a 32 A single-phase cable on a three-phase EVSE reduces the count to one. The single-phase equation is written as `P_ac_kW = U_ln_v * I_ac * power_factor / 1000`, but the supply is described by one voltage plus a convention, and a 400 V three-phase EVSE is declared `line_to_line`. When the count is reduced to one on a line-to-line supply, the spec never says that the single-phase equation uses the line-to-neutral voltage `U_ln = U_ll / sqrt(3)` (nor that such a path is ineligible). An implementation that feeds the supplied 400 V into the single-phase equation gets `400 * 32 / 1000 = 12.8 kW` instead of about 7.4 kW, contradicting the §9 regression. The illustration "7.4 kW at 230 V single-phase and 22.2 kW at 400 V line-to-line three-phase" describes two supplies and does not state the conversion.
- **Proposed change:** Add to the AC inputs paragraph: "When the selected phase count is one and the supply voltage is declared `line_to_line`, the single-phase equation uses the line-to-neutral voltage `U_ln = U_ll / sqrt(3)`; when the supply is declared `line_to_neutral`, `U_ln` is the supplied value. The selected phase count and the voltage actually used are recorded in `assumptions`." Add a §9 regression: a 400 V line-to-line three-phase EVSE with a 32 A single-phase cable and an 11 kW onboard charger yields about 7.4 kW, while the same cable rated for three phases yields about 22.2 kW.
- **Evidence:** reasoning only; `400 * 32 / 1000 = 12.8 kW`, `(400 / sqrt(3)) * 32 / 1000 ≈ 7.39 kW`, `sqrt(3) * 400 * 32 / 1000 ≈ 22.17 kW`; §7.2's equations and the existing round-3 §9 regression. G6 added the convention fields and forbade defaults; this is the voltage selection after those fields exist.
- **Confidence:** high

### DEEPSEEK-3 · `ac_outlet_power_max_kw` is stored but never applied

- **Section:** §4.2, §6.2, §7.2 (AC path), §9
- **Type:** gap
- **Severity:** minor
- **Finding:** §4.2 requires the AC outlet's "phase count, current and power" as charger research attributes, and §6.2 adds `ac_outlet_power_max_kw`. §7.2's AC path limits current by the EVSE, the cable and the inlet and power by the onboard charger only; it reads the outlet's voltage, convention and power factor but never its power cap. The column is therefore orphaned, and an outlet whose published power cap binds below voltage × current (for example a 400 V three-phase outlet limited to 11 kW by the site or by sharing, with 32 A available) is modeled at `sqrt(3) * 400 * 32 / 1000 ≈ 22.2 kW`. Sharing is handled for DC through `station_available_power_kw`, but no equivalent AC limit is wired in.
- **Proposed change:** In the AC path, state: "The AC power limit is the minimum of the EVSE outlet's `ac_outlet_power_max_kw` when present, every in-path cable/adapter power cap at its own boundary, and the onboard-charger rating. When `ac_outlet_power_max_kw` is absent but the outlet voltage, current and phase count are known, the voltage × current bound from the equations applies; its absence is not treated as unlimited and not as an invented value." Add a §9 regression: a 400 V three-phase outlet with a 32 A current rating and an 11 kW outlet power cap, connected to a 22 kW onboard charger, yields 11 kW, not 22.2 kW.
- **Evidence:** reasoning only; §4.2 and §6.2 against the AC path text; `sqrt(3) * 400 * 32 / 1000 ≈ 22.17 kW`. Not the same as G6, which wired the voltage, convention and power factor, and not the same as G16, which concerns DC session count.
- **Confidence:** high

### DEEPSEEK-4 · SoH is an argument of the BMS limit but has no source or assumption rule

- **Section:** §2, §4.1, §6.1, §7.2, §8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** `SoH` is an argument of the current limit in both path equations (`I_vehicle_BMS(SoC, T, SoH)`), and §4.1 requires state of health as a research attribute. No schema field or request input carries it: §6.1's vehicle additions have no SoH, §8.2's request has no SoH, and the §3 audit table does not list it. It is also per battery unit, while `vehicle_profile_id` identifies a make/model/year/market/trim/variant combination, so a profile-level SoH would apply one pack's health to every vehicle of that profile. §7.1's fail-closed list does not mention SoH, so an implementation may silently assume a value (typically a new pack, SoH = 1) and overstate power and shorten the estimated time for a degraded battery, with no assumption recorded.
- **Proposed change:** Add an optional request field `battery_soh` (0–1) or an explicit per-request battery-health input, and state: "When SoH is absent, the assumption used — including the inherited calculator's SoH treatment — is recorded in `assumptions`, the reported range is widened, and the result is not presented as measured. A profile-level SoH is not used as if it described a specific vehicle." If SoH is safety-critical for eligibility, add it to the §7.1 list; otherwise say explicitly that it is not. Add a §9 regression: the same profile at SoH 1.0 and 0.8 with a SoH-dependent BMS map gives different durations and reports the SoH assumption.
- **Evidence:** reasoning only; the function calls in §7.2, the §4.1 attribute list, the §6.1/§8.2 field lists, and the §2 identity rule. This is the input-side counterpart of G10 (test measurement boundary), not a repeat of it.
- **Confidence:** high

### DEEPSEEK-5 · The response contract has no container for partial-window or AC-unranked results

- **Section:** §7.1, §8.1, §8.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §8.1 says a result with `window_completed: false` "is reported only with `reached_soc`, the limiting condition and the time to the SoC reached", and that AC candidates are "evaluated and listed unranked". §7.1 says an unknown-attribute combination "may appear in a separate unranked list with its missing fields". The §8.2 contract has one `unranked_unverified` array plus the three category objects, whose `results` hold ranked candidates. Nothing in the contract can carry an evaluated partial-window result or an AC-scope-unranked result. An implementation must either drop them, contradicting §8.1, or place them in `unranked_unverified`, where "unverified" mislabels a result whose limiting condition is established (a partial window is not an unknown attribute, and an AC candidate is evaluated).
- **Proposed change:** Add an `unranked` array (keep `unranked_unverified` as an alias or replace it) whose entries carry a `reason` (`unknown_attribute`, `partial_window`, `scope_undecided`, …), the missing or limiting fields, `reached_soc`, `limiting_condition`, `time_to_reached_soc`, `window_completed` and the calculation configuration. State that `recommendations.<category>.results` holds only ranked candidates and never a partial-window result. The `scope_undecided` entry implements FB-D9's interim without deciding FB-D9.
- **Evidence:** reasoning only; the quoted §8.1 sentences, §7.1's "separate unranked list", and the §8.2 sketch (`unranked_unverified`, `recommendations.*.results`). G5/E5 made partial results non-candidates and required them to be reported; this is the missing output field, not a request to change the candidate set.
- **Confidence:** high

### DEEPSEEK-6 · The best-value baseline object and `minutes_saved` are not defined in the contract

- **Section:** §8.1 (Best value), §8.2
- **Type:** gap
- **Severity:** minor
- **Finding:** Best value is the lowest `delivered_price / minutes_saved`, and §8.1 says the response reports "the baseline and the offer used". The §8.2 sketch has a top-level `"baseline": null` with no defined shape, and `required_per_recommendation` contains `estimated_minutes` but not `minutes_saved`. The baseline's duration, SoC window, conditions and `window_completed` are therefore not part of the contract, so the reported score cannot be recomputed or audited from the response: a client sees each candidate's `estimated_minutes` but not the baseline duration that produced the denominator. This is independent of how FB-D11 resolves (empty versus some other baseline); any baseline the decision allows needs a defined representation.
- **Proposed change:** Define `baseline` as an object or `null`, for example `{kind: "no_adapter_session", estimated_minutes, window_completed, vehicle_profile_id, charger_profile_id, charger_installation_id, start_soc, target_soc, conditions, power_convention}`. Add `minutes_saved` to `required_per_recommendation`, and state that `minutes_saved = baseline.estimated_minutes - estimated_minutes` and is null when there is no baseline. Add a §9 regression: a response whose best-value winner has a 40-minute baseline and a 35-minute candidate reports `minutes_saved: 5` and the baseline fields used.
- **Evidence:** reasoning only; §8.1's score and "the baseline and the offer used", the §8.2 field list, and the round-3 G12 baseline rule. G8 added price provenance to the contract; this is the analogous provenance for the best-value denominator.
- **Confidence:** high

### DEEPSEEK-7 · Mixed-currency conversion has no storage, `vat_amount` has no currency, and `fx_rate` has no direction

- **Section:** §4.4, §6.3, §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §4.4 says a mixed-currency offer with "no stored conversion" cannot win, but §6.3 has no field or table in which a conversion could be stored: `accessory_offers` holds `price` and `currency`; the destination row holds `shipping_price` and `shipping_currency`; `vat_amount` has no currency column, so it is unclear whether it is in the offer currency or the shipping currency. The §8.2 `fx_rate` also has no defined pair or direction, so a client cannot tell whether it is output-currency-per-source-unit or the inverse; two correct-looking conversions can differ by the square of the rate. The result is that "stored conversion" is unsatisfiable from the schema and a converted `price_total` is not independently auditable.
- **Proposed change:** State that `vat_amount` is in the offer currency (or add `vat_currency`), and either add a conversion record to the offer/destination row (`fx_rate`, `fx_source`, `fx_timestamp`, source and target currency) or replace "no stored conversion" with "no conversion available at ranking time, with its source and timestamp reported". Define `fx_rate` as units of the response `currency` per unit of the converted source currency, or add `fx_base`/`fx_quote`. Add a regression: an offer priced in EUR with shipping in USD and no rate is ineligible; with a rate and a recorded direction, the total, the rate direction and the provenance are returned.
- **Evidence:** reasoning only; §4.4's delivered-price formula and "no stored conversion" sentence, the `accessory_offers`/`accessory_offer_destinations` DDL, and the `fx_*` fields added by G8. This is the storage/direction counterpart of G8's response-field fix, not a repeat of it.
- **Confidence:** medium

### DEEPSEEK-8 · The booster's bypass condition is evaluated on an undefined "station-side voltage"

- **Section:** §6.1, §7.1 (Booster engagement), §7.2 (Direct DC path, Segments around a converter), §9
- **Type:** question
- **Severity:** minor
- **Finding:** G13 makes a `bypassable` booster engaged when "the station-side voltage lies outside the condition under which the booster is bypassed", and §6.1 stores the bypass condition with the booster. But §7.2 defines the station-side voltage as current-dependent: `V_station = V_batt + I_batt * R_series_ohm` on a direct path and `V_station = V_in + I_in_used * R_up` on a converting path, and the engagement decision itself changes the path and therefore the current. Near the threshold the decision can depend on the current and on itself: a station whose declared voltage is above the bypass threshold but whose loaded terminal voltage falls below it (or the reverse) can be modeled as engaged or bypassed by two implementations, or flip during a session. The §9 regression uses 700 V and 400 V stations, far from any threshold, so it does not pin the rule.
- **Proposed change:** State which voltage the bypass decision uses — for example the station's declared/rated DC output voltage at the connector (the operating-point target) or the open-circuit voltage before current-dependent drops — and that the decision is made once per session (or define hysteresis and the re-evaluation rule) and recorded in `assumptions`. Add a regression: a bypass condition at 500 V and a station at 520 V with enough current to drop its terminal voltage to 480 V produces one stated outcome, not a path that depends on the solved current.
- **Evidence:** reasoning only; §7.1's engagement sentence, §6.1's `dc_booster_engagement`, §7.2's `V_station` definitions, and the round-3 §9 booster regression. G13 added the engagement states; this finding is the voltage the state is evaluated at.
- **Confidence:** medium

I endorse the round-3 findings that remain relevant and the round-4 CHATGPT-1 finding; none is given a new id here. FB-D8, FB-D9, FB-D10 and FB-D11 stay open and were not raised as blocking or major; DEEPSEEK-5 only notes that FB-D9's interim needs a contract field, and DEEPSEEK-6 only notes that whatever baseline FB-D11 selects needs a representation.

**Top 3**

1. DEEPSEEK-1: extend `peak_mode` to vehicles and chargers, so a continuous-only profile is modeled at its continuous rating instead of failing closed.
2. DEEPSEEK-4: give SoH a request input or a stated assumption, so the BMS limit is not evaluated on an unstated pack health.
3. DEEPSEEK-5: add an `unranked` container for partial-window and AC-unranked results, so §8.1's reporting rule has a contract home.

Result: complete
