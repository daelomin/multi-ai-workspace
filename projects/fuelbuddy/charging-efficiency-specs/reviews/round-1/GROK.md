# GROK review — round 1

**Specification:** local `spec.md`, v1.1, dated 2026-10-21.
**Reviewer:** GROK. **Review date:** 2026-10-21.
**Method:** Round 1, so this review reads the local spec only. There is no `reviews/round-0/` and no previous `CONSOLIDATION.md`. §11 already asks HUMAN to decide the minimum evidence level for a purchase recommendation. That decision is not raised again here.

**Overall:** 0 blocking, 3 major, 5 minor.

### GROK-1 · One efficiency factor scales the battery limit and the station's DC output

- **Section:** §7.2
- **Type:** error
- **Severity:** major
- **Finding:** The simplified formula takes the minimum of battery-side current, station current, cable current and adapter current, converts that current at `V_batt`, then multiplies the minimum of that power, `P_station_available` and `P_vehicle_charge_curve` by one `efficiency`. On a direct DC path the series current is already the battery current, so `V_batt * I` is battery-side power. Scaling the BMS limit or the vehicle curve by station efficiency understates what the car will take. The same factor also treats station efficiency as a loss after the DC output. The published HYC150 brief states 160 kW AC input at 150 kW DC output and efficiency greater than 94% at full charge, so that efficiency already sits on the AC side of the 150 kW DC figure. Applying it again to a DC nameplate, or to the vehicle curve, shortens the estimated session for the wrong reason. The formula also never says that a peak current lasts only for `peak_duration_s`. The same brief lists a CCS2 output as 400 A including a 500 A boost mode, so a session that holds 500 A will overstate energy.
- **Proposed change:** Replace the §7.2 equation with: "Direct DC path, only when the vehicle is not boosting and the cable or adapter does not convert voltage. Each current limit stays at its peak only until that component's `peak_duration_s` is used, then drops to its continuous rating. `I_series(t) = min(I_vehicle_BMS(SoC, T, SoH), I_station_connector(V_batt, installation, sharing, t), I_cable(T_cable, t), I_adapter(T_adapter, t))`. `P_battery_kW = min(V_batt(SoC, T) * I_series(t) / 1000, P_vehicle_charge_curve(SoC, T, SoH))`. `P_station_dc_kW = P_battery_kW + (I_series(t)^2 * R_series_ohm) / 1000`. `P_station_available` is DC power at that connector after power sharing. Require `P_station_dc_kW <= P_station_available`. Do not multiply `P_battery_kW` or the vehicle curve by station efficiency or by a single path efficiency. If `R_series_ohm` is unknown, omit the loss term and report the loss as unknown. Voltage-converting path: `P_out_kW <= P_in_kW * eta`, with input and output currents limited on their own voltages. Do not use one current on both sides."
- **Evidence:** [Alpitronic HYC150 product brief v2.1 (English copy)](https://www.lbltrading.com/wp-content/uploads/2025/01/HYC150_PRODUCT-BRIEF_V2-1_EN.pdf), checked 2026-10-21: "160 kW (model) at 150 kW DC output power", "Efficiency >94% at full charge", "CCS2 @400 A (including 500 A boost mode)". The placement of `efficiency` in the local equation is reasoning only.
- **Confidence:** high

### GROK-2 · Voltage-range overlap does not mean the requested SoC window is reachable

- **Section:** §7.1, §7.2, §7.3
- **Type:** error
- **Severity:** major
- **Finding:** §7.1 accepts a combination once the operating-voltage ranges overlap, and §7.3 then reports a 10–80% time, or another requested window, for that combination. Overlap does not keep `V_batt` inside the station and adapter limits at every SoC in the window. A window that leaves the station's maximum before the target SoC cannot be given a time to that target. The same gap exists inside a range that does overlap: the HYC150 brief publishes 150–1000 V DC and, separately, full performance from 300 V battery voltage. A preflight that stops at overlap, and a power estimate that then uses the nameplate current, will treat a battery below that full-power threshold as if the cabinet could deliver its headline power.
- **Proposed change:** Replace "overlapping operating voltage" in §7.1 with: "The combination is eligible for the requested SoC window only when `V_batt(SoC, T)`, on the station side of any booster, is inside the station-connector and adapter voltage limits at every SoC in that window. Overlap of the two nameplate ranges is not sufficient. If only part of the window is reachable, `estimated_minutes` covers the reachable interval and the response records the SoC actually reached. It does not present the requested target as completed. Inside a published voltage range, use the current-versus-voltage envelope. Do not apply the nameplate current below the voltage at which the source states that full performance begins."
- **Evidence:** [Alpitronic HYC150 product brief v2.1 (English copy)](https://www.lbltrading.com/wp-content/uploads/2025/01/HYC150_PRODUCT-BRIEF_V2-1_EN.pdf), checked 2026-10-21: "Output DC voltage range 150Vdc - 1000Vdc" and "Full performance from 300 V battery voltage". The SoC-window rule is reasoning only.
- **Confidence:** high

### GROK-3 · A converter cannot be calculated from one voltage and one current

- **Section:** §4.3, §6.1, §6.3, §7.2
- **Type:** gap
- **Severity:** major
- **Finding:** §7.2 says a conversion or boost path has separate input and output limits and must not share one current. §6.1 stores only `dc_booster_capability`. §6.3 stores one `min_voltage_v`, one `max_voltage_v` and one current pair for every accessory, and it has no series resistance even though §4.3 lists resistance and losses. An implementation that follows the schema has nowhere to put a 400 V input limit and an 800 V battery limit. Porsche's 2019 Taycan description is that case: an 800 V system, with a separate on-board DC charger for 400 V stations, rated 50 kW at first and 150 kW as an option. Those are different currents. The seed CCS2-to-CHAdeMO adapter is the other case: Akyga publishes one 1000 V DC and 250 A rating and a connector resistance of 0.5 mΩ, which is a passthrough, not a boost stage. One envelope is right for that product and wrong for the booster the spec also requires.
- **Proposed change:** Add `electrical_topology` with values `passthrough` and `voltage_conversion`. Keep the single voltage and current columns for `passthrough` only, and add `resistance_ohm`. For `voltage_conversion`, store input and output voltage min/max, continuous current, peak current, peak duration and power, plus `conversion_efficiency`. On `vehicle_profiles`, when a booster is present, store the same input/output ratings rather than only `dc_booster_capability`. §7.2 uses the passthrough equation from GROK-1 only when every series element is `passthrough` and the vehicle booster is absent.
- **Evidence:** [Porsche Newsroom, "The charging process", 4 September 2019](https://newsroom.porsche.com/en/products/taycan/charging-18558.html), checked 2026-10-21: 800 V charging, and "For charging at 400-volt charging points, an on-board DC charger, initially with 50 kW and optionally 150 kW, is installed." [Akyga AK-SC-E18 product page](https://www.akyga.com/products/1319-ev-ccs2-chademo-adapter-ak-sc-e18-1000v-dc-250a.html), checked 2026-10-21: supply voltage 1000 V DC, maximum current 250 A, maximum power 250 kW, connector resistance 0.5 mΩ, CHAdeMO male and CCS Combo 2 female. The schema comparison is reasoning only.
- **Confidence:** high

### GROK-4 · A conflict on direction can still become the stored direction

- **Section:** §4.3, §5, §7.1
- **Type:** risk
- **Severity:** minor
- **Finding:** §5 says to track conflicting sources. It does not say an unresolved conflict on a safety-critical attribute blocks eligibility. The Akyga AK-SC-E18 manual's specification table labels the power inlet as CHAdeMO and the output connector as CCS2, and it names a single communication protocol, DIN 70121. The same manual's procedure says to connect the adapter to the car and then the CCS plug to the adapter. The product page describes CCS2 stations and CHAdeMO vehicles, with a CHAdeMO male plug and a CCS Combo 2 female plug. A row that stores the manual's inlet/outlet labels verbatim is reversed relative to the product page and to the manual's own procedure, and a single stored protocol drops the CHAdeMO side. §7.1 will then "verify" that reversed row.
- **Proposed change:** Add: "If retained sources disagree on direction, which connector faces the station, maximum voltage, continuous current, or the protocol on either side, the accessory is not eligible. Record every conflicting value with its source. Tracking the conflict is not a resolution, and the recommendation uses a value only after the rejected alternatives are stored as rejected."
- **Evidence:** [Akyga AK-SC-E18 user manual](https://si.akyga.com/app_products_attachments/instruction/symbol/AK-SC-E18/code/si), checked 2026-10-21: specification table "Power inlet: CHAdeMO", "Output connector: CCS2", and "The communication protocol is DIN 70121"; procedure step 4 connects the adapter to the car, then the CCS plug to the adapter. [Akyga AK-SC-E18 product page](https://www.akyga.com/products/1319-ev-ccs2-chademo-adapter-ak-sc-e18-1000v-dc-250a.html), checked 2026-10-21: CCS2 stations, CHAdeMO vehicles, CHAdeMO male, CCS Combo 2 female. This does not set the purchase-evidence threshold in §11.
- **Confidence:** high

### GROK-5 · AC charging has no power path

- **Section:** §4.1, §6.3, §7.2
- **Type:** gap
- **Severity:** minor
- **Finding:** Vehicle attributes include an AC inlet and AC power limit, and a charger can expose an AC outlet. The HYC150 brief lists that outlet as 3-phase, maximum 32 A or 22 kW. §7.2 defines a DC series current and a voltage-converting exception. An AC cable is neither: the onboard charger, not the station, is the converter into the battery. Putting the AC current into `I_series` and multiplying by `V_batt` produces a DC power the AC path does not have. The same 32 A rating is about 7 kW on a single phase and about 22 kW on 400 V three-phase, so a current-only AC record is also ambiguous.
- **Proposed change:** Add an AC path: "Limit AC current by the EVSE, the cable and the vehicle inlet. Convert current to power with the supply's phase count and voltage. Limit AC power by the onboard charger rating. Battery-side current comes from that onboard converter through the voltage-converting split. Do not put the AC current into the direct-DC `I_series` formula."
- **Evidence:** [Alpitronic HYC150 product brief v2.1 (English copy)](https://www.lbltrading.com/wp-content/uploads/2025/01/HYC150_PRODUCT-BRIEF_V2-1_EN.pdf), checked 2026-10-21: "Output AC voltage range 3-phase, max. 32 A or 22 kW". [Porsche Newsroom, 4 September 2019](https://newsroom.porsche.com/en/products/taycan/charging-18558.html), checked 2026-10-21: on-board AC charger, 11 kW. The single-phase versus three-phase arithmetic is reasoning from those published ratings.
- **Confidence:** high

### GROK-6 · Best value has no score, and a tie has nowhere to go

- **Section:** §8.1, §8.2
- **Type:** gap
- **Severity:** minor
- **Finding:** Fastest is a minimum duration. Cheapest is a minimum delivered price. Best value is "optimize delivered price versus usable charging performance", including evidence quality and reliability, with no score, baseline or tie break. Two implementations can both satisfy §8 and return different winners. §8.1 also says to report ties, while §8.2 gives each category one object and no list of equal candidates. Phase 6 cannot be tested against a single expected winner.
- **Proposed change:** Add: "Best value ranks eligible products by delivered price per minute saved against the no-adapter session for the same vehicle, charger, SoC window and stated conditions. If no adapter is required, or no no-adapter session exists, the baseline is the eligible candidate with the longest estimated duration. A candidate that saves no time does not win on performance. Ties break by lower delivered price, then longer `warranty_months`, and the response lists every remaining tie in `tied_with`. Evidence quality is an eligibility decision and is not a second weight in this score." Leave the §11 evidence threshold to HUMAN.
- **Evidence:** reasoning only.
- **Confidence:** medium

### GROK-7 · Delivered price is not determined by the offer fields

- **Section:** §4.4, §6.3, §8.1
- **Type:** gap
- **Severity:** minor
- **Finding:** Cheapest and best value compare delivered price, defined as VAT plus shipping. An offer stores `price`, `vat_included`, `shipping_price`, `currency` and `country`, and not a VAT amount, a shipping currency, or a validity end. A net price and a gross price can be sorted as if they were the same kind of number. §9 requires a regression for expired offers, and the only time on the row is `observed_at`. There is no rule for when that observation stops being the price used to rank.
- **Proposed change:** Add `vat_amount`, `shipping_currency` and `valid_until`. State: "Delivered price is `price + shipping_price` when `vat_included` is true, and `price + vat_amount + shipping_price` when it is false, all in one currency. An offer with `vat_included` false and no `vat_amount`, or with mixed currencies and no stored conversion, is excluded from cheapest and best value. An offer is expired when `valid_until` is before the ranking time or when `valid_until` is absent. Expired offers stay in price history and cannot win a category."
- **Evidence:** reasoning only. No VAT rate is proposed.
- **Confidence:** high

### GROK-8 · A measured test is not tied to the hardware that produced it

- **Section:** §6.3, §7.3, §8
- **Type:** gap
- **Severity:** minor
- **Finding:** `accessory_test_results` stores the accessory, an optional vehicle profile and an optional charger profile, plus one battery temperature and one ambient temperature. It does not store accessory hardware revision, accessory firmware, vehicle firmware, charger firmware, installation, or the topology used. §7.3 requires the estimate to name the model and firmware configuration. Pipeline step 7 attaches measured tests to a candidate. A test of one firmware can therefore be attached to another firmware of the same `accessory_id`, and a passthrough measurement can be reused as if it were a booster result.
- **Proposed change:** Add to `accessory_test_results`: `accessory_hardware_revision`, `accessory_firmware`, `vehicle_firmware`, `charger_firmware`, `charger_installation_id` already present stays, plus `electrical_topology` and `initial_battery_temp_c`. State: "A measured test may support an estimate only when those fields match the candidate being ranked. A test with a null firmware or topology supports an uncertainty range and does not replace the calculated curve."
- **Evidence:** reasoning only, against the local `accessory_test_results` column list and §7.3.
- **Confidence:** high

## Top 3

1. GROK-1: stop multiplying battery-side power and DC station power by a single efficiency, and drop peak current to continuous after its allowed duration.
2. GROK-2: require the station and adapter voltage limits to cover the requested SoC window, and use the voltage-current envelope inside that range.
3. GROK-3: store separate input and output limits for a booster or converting adapter; keep one envelope for a passthrough such as the CCS2-to-CHAdeMO seed.

Result: complete
