# Fuel Atlas — Charging Equipment, Adapter and Battery Research Specification

**Version:** 1.2 (proposal)  
**Date:** 2026-10-21  
**Status:** Draft; live database/repository schema not yet inspected. Round-1 review consolidated (see `reviews/round-1/CONSOLIDATION.md`); open HUMAN decisions are listed in §11.

## 1. Objective

Extend Fuel Atlas and FuelBuddy to research, normalize, verify and compare EV charging **cables, adapters, charger models and battery/vehicle limits**, and estimate charging performance for a specific vehicle and charging station. For a selected vehicle, return **three adapter recommendations**: fastest, cheapest eligible, and best value-to-performance, including current prices, purchase links, compatibility evidence and expected charging power/time.

**Principles:** reuse the existing vehicle profiles, charger profiles, charging curves, diagnostic rules and matching engine; preserve backward compatibility; distinguish manufacturer claims, calculations and field measurements; never present an unverified rating as a measured outcome.

## 2. Scope and terminology

- **Vehicle profile:** make/model/year/market/trim/battery variant, charge inlet, firmware and charging limits. **Identity rule:** a `vehicle_profile_id` identifies exactly one such combination. If the existing table turns out to be model-level, `battery_variant_id` is added to `accessory_compatibility` and `accessory_test_results` and is part of the matching key, so evidence for one battery variant is never matched to another.
- **Battery profile:** voltage versus state of charge (SoC), current and thermal limits, usable capacity, SoH and preconditioning behavior.
- **Charger model:** manufacturer, model, hardware/firmware, connector configuration, voltage/current operating envelope and shared-power rules. A charger network/operator is a separate entity.
- **Charger installation:** physical unit with station ID, site/network, installed connector options, configured output and firmware. A model's headline power is not necessarily the installed unit's available power.
- **Cable:** conductive charging assembly with connector types, voltage/current/thermal ratings, cooling and certification.
- **Adapter:** passive electrical conversion or active protocol translation, with explicitly defined **direction** (e.g. CCS2 station -> CHAdeMO vehicle) and an **electrical topology**: `passthrough` (one voltage/current envelope on both sides) or `voltage_conversion` (separate input and output envelopes, e.g. a booster).
- **Offer:** dated seller listing, VAT/shipping/stock/warranty, country and purchase URL.
- **Evidence:** manufacturer datasheet, official manual, certification, field test, telemetry or retailer listing, with URL, access date and confidence.

## 3. Current schema audit (provisional)

The previously specified FuelBuddy architecture contains `vehicle_profiles`, `charger_profiles`, `known_vehicle_issues`, `known_charger_issues`, `protocol_error_mappings` and `compatibility_matrix`, plus a charging-curve calculator. This is a **spec-level inventory**, not a verified inventory of live Fuel Atlas tables or columns.

| Capability | Prior specification | Minimal change |
|---|---|---|
| Vehicle make/model/year, connector | Defined | Reuse |
| Battery capacity and max DC power | Defined in calculator concept | Verify actual columns |
| SoC-to-power charging curve | Defined in calculator concept | Reuse; add test conditions |
| Vehicle nominal battery voltage | Present in example profiles | Add min/max and voltage-vs-SoC if absent |
| Vehicle BMS current/thermal limits | Not established | Add optional maps |
| Charger manufacturer/model/network | Defined | Reuse `charger_profiles`; extend |
| Charger voltage/current operating envelope | Not established consistently | Add nullable fields |
| Charger hardware/firmware and installation config | Partial | Extend and optionally add installations |
| Charging cables/adapters and OEM relationships | Not established | Add accessory catalog |
| Vehicle × adapter × charger compatibility | Not established | Add accessory compatibility records |
| Retail offers and dated prices | Not established | Add offers |
| Measured accessory/charger charging tests | Not established | Add test results |
| Source links for every named equipment model | Not guaranteed | Add provenance requirement |

**Audit gate:** inspect the actual repository schema, migrations, ORM, API and existing rows. Mark each proposed attribute as `existing`, `equivalent`, `missing` or `not applicable`. Do not run migration SQL until ID types and existing constraints are confirmed.

## 4. Research attributes

### 4.1 Vehicle and battery

- Vehicle make, model, generation, year, market, trim, battery variant, software/BMS version.
- Gross/usable capacity (kWh), chemistry, state of health (SoH), battery nominal/min/max voltage, voltage-vs-SoC curve.
- Charge current continuous/peak, peak duration, current limits as a function of SoC and temperature, battery thermal derating, preconditioning.
- AC/DC inlet types and protocol revisions; maximum AC/DC power and voltage/current; onboard boost or conversion constraints (input and output ratings of any booster, not only its presence); AC phase count and onboard-charger rating.
- Charge curve with SoC points, battery temperature, ambient temperature, preconditioning, charger context and source quality.

### 4.2 Charger models and installations (NEW REQUIRED DOMAIN)

- Manufacturer, canonical model name, model family, product URL, datasheet/manual URL.
- Hardware revision, firmware version/range, protocol support (e.g. CCS/ISO 15118/DIN SPEC, CHAdeMO), authentication requirements.
- Rated cabinet output kW, module configuration, **DC voltage min/max**, maximum continuous/peak current, peak duration, current-versus-voltage envelope, efficiency and derating.
- Per-connector limits and connector variant (CCS2, CHAdeMO, etc.), cable length/current/cooling, number of simultaneous outputs, power-sharing rules, AC outlet phase count, current and power, and the voltage from which the published full performance applies.
- Installation-specific limits: network/operator, station ID, site, firmware, configured power, local grid cap, connector availability, outages.
- Documented incompatibilities, handshake failures and known issues, linked to existing diagnostic knowledge.

### 4.3 Cables and adapters

- Canonical manufacturer/model/SKU, OEM/rebrand mapping, input/output connector, **direction**, AC/DC mode, active/passive conversion, **electrical topology** (`passthrough` or `voltage_conversion`), protocol translation (the protocol on each side).
- Voltage min/max, continuous current, peak current, peak duration, continuous/advertised power, cable length, series resistance/losses, cooling, thermal derating. For `voltage_conversion`, these are stored separately for the input (station) side and the output (vehicle) side, plus conversion efficiency.
- Firmware/hardware versions, auxiliary power requirements, connector lock/interlock behavior, fault shutdown and certification evidence.
- Vehicle/charger/firmware compatibility status and evidence; reject unsupported safety-critical combinations.

### 4.4 Commercial data

- Seller, country, offer URL, SKU, currency, base price, VAT inclusion and VAT amount, shipping and its currency, total delivered price, stock, lead time, warranty, date checked and offer validity end.
- Maintain price history snapshots rather than overwriting historical prices.
- **Delivered price** is computed for a stated destination country/postcode, all in one currency: `price + shipping_price` when `vat_included` is true, `price + vat_amount + shipping_price` when it is false. Unknown VAT or shipping makes the delivered total **unknown, never zero**. An offer with an unknown total, mixed currencies and no stored conversion, no availability to the destination, or that is expired cannot win cheapest or best value. When conversion is needed, the exchange-rate source and timestamp are reported.
- **Offer freshness:** an offer is expired when `valid_until` is before the ranking time; if `valid_until` is absent, when `observed_at` is older than a configurable maximum age (no fixed period is set here). Expired offers stay in price history.

## 5. Source-link policy (MANDATORY)

Every **named charger, cable or adapter model** in research output must have a clickable official manufacturer product page or official technical document where available. If neither exists, provide the exact retailer listing and label it accordingly. Each claim about a rating must point to its supporting source; do not use a generic manufacturer homepage as proof of a model-specific value.

Minimum provenance fields: `source_url`, `source_title`, `publisher`, `evidence_type`, `retrieved_at`, `published_at` (nullable), `applicable_model_revision`, `confidence`, `claim_field`. Track conflicting sources explicitly. **Tracking a conflict is not resolving it:** if retained sources disagree on direction, which connector faces the station, maximum voltage, continuous current, or the protocol on either side, the accessory is **not eligible** for any ranking category. Every conflicting value is stored with its source; a value is used for a recommendation only after the rejected alternatives are stored as rejected.

### Charger-model seed registry (research targets, NOT prevalidated specifications)

| Manufacturer | Charger model/family | Link | Research notes |
|---|---|---|---|
| Alpitronic | HYC150 | [HYC150 product brief (PDF)](https://esb-metelen.de/wp-content/uploads/HYC150_PRODUCT-BRIEF_V2-1_DE.pdf) | Verify revision, 150 kW configuration, voltage/current envelope and installed connector options |
| Alpitronic | HYC300 | [Official Hypercharger product family](https://www.alpitronic.it/en/hypercharger) | Find model-specific official datasheet and configuration |
| ABB E-mobility | Terra HP | [Official ABB E-mobility](https://e-mobility.abb.com/) | Resolve exact generation and power module, not just family name |
| ChargePoint | Express 250 | [Official ChargePoint](https://www.chargepoint.com/) | Resolve model-specific datasheet and configured power |
| Tesla | Supercharger V3 | [Official Tesla Supercharging](https://www.tesla.com/supercharger) | Validate non-Tesla access, site restrictions and vehicle voltage |

**Important:** The HYC150 is a **charger**, not a CCS2-to-CHAdeMO adapter. The cited LEAF e+ adapter test is a combination of vehicle + adapter + HYC150 configuration, not an adapter-only power guarantee. Seed links are research starting points; live link and specification validation remains required.

**Reviewer-reported source facts (round 1; GROK reviewer, whose served model was unverified; not re-fetched by CLAUDE, to be validated in phase 2/3):**

- HYC150 product brief v2.1 (an English copy, `lbltrading.com`, differs from the seed link): 160 kW input at 150 kW DC output, efficiency above 94% at full charge (so efficiency sits on the AC side of the DC figure), DC range 150–1000 V with full performance from 300 V battery voltage, CCS2 at 400 A including a 500 A boost mode, AC outlet 3-phase max. 32 A or 22 kW.
- Akyga AK-SC-E18: product page gives 1000 V DC, 250 A, 0.5 mΩ connector resistance, CHAdeMO male and CCS Combo 2 female; the user manual's specification table labels the power inlet CHAdeMO and the output CCS2 and names one protocol (DIN 70121), while its procedure connects the adapter to the car first. This is an example of a direction conflict that makes the product ineligible until resolved (§5).
- Porsche Taycan (newsroom, 4 September 2019): 800 V system with an on-board DC charger for 400 V stations (initially 50 kW, optionally 150 kW) and an 11 kW on-board AC charger: an example of a vehicle-side booster that needs input/output ratings.

### Adapter-model seed registry (research targets)

| Supplier/model | Source |
|---|---|
| EVniculus / Longood CCS2-to-CHAdeMO | [EVniculus listing](https://evniculus.eu/products/adapter-ccs2-to-chademo-for-nissan-leaf) |
| Electway CCS2-to-CHAdeMO | [Electway product page](https://www.electway-charger.com/CCS2_to_CHAdeMO_adapter.html) |
| Vanton EV CCS2-to-CHAdeMO | [Vanton product page](https://www.evcharger-vanton.com/ccs2-to-chademo-adapter.html) |
| Akyga AK-SC-E18 | [Akyga product page](https://www.akyga.com/products/1319-ev-ccs2-chademo-adapter-ak-sc-e18-1000v-dc-250a.html) |
| Voldt CCS2-to-CHAdeMO | [Voldt product page](https://voldt.eu/products/ev-charging-adapter-ccs2-to-chademo) |
| Wireload CCS2-to-CHAdeMO | [Wireload listing](https://www.wireload.de/shop/CCS2-zu-CHAdeMO-EV-Adapter-250A-250kW-V2G-fahig-inkl-Transportkoffer-p688291928) |

Do not assume these are distinct OEM designs. Deduplicate on verified manufacturer, electronics/firmware and mechanical design where evidence permits. Verify all links, prices, ratings and availability at research time.

## 6. Minimal schema delta

Prefer nullable columns on existing entities and four new accessory entities. Add `charger_installations` **only if** the existing charger profile cannot already represent physical installations. Preserve existing IDs, endpoint contracts and diagnostic mappings.

### 6.1 Existing `vehicle_profiles` (optional additions)

`battery_variant_id`, `battery_voltage_min_v`, `battery_voltage_max_v`, `battery_voltage_curve`, `dc_charge_current_continuous_a`, `dc_charge_current_peak_a`, `bms_charge_limit_map`, `battery_thermal_limit_map`, `dc_protocol_version`, `software_version`, `dc_booster_capability`, `dc_booster_ratings` (input and output voltage min/max, continuous and peak current, peak duration, efficiency; required to calculate a boosted path), `ac_phases`, `ac_current_max_a`, `onboard_charger_kw`.

### 6.2 Existing `charger_profiles` (optional additions)

`product_url`, `datasheet_url`, `hardware_revision`, `firmware_version`, `dc_voltage_min_v`, `dc_voltage_max_v`, `dc_current_continuous_a`, `dc_current_peak_a`, `peak_duration_s`, `voltage_current_envelope`, `connector_configurations`, `power_sharing_policy`, `thermal_derating`, `full_performance_from_v`, `ac_outlet_phases`, `ac_outlet_current_max_a`, `ac_outlet_power_max_kw`, `source_metadata`.

If charger model and site instance are conflated, separate installation attributes into an optional `charger_installations` entity with FK to `charger_profiles`, `station_id`, `network`, `firmware`, `configured_power_kw`, `connector_config`, `site_limits`.

### 6.3 New accessory tables (illustrative PostgreSQL DDL)

```sql
-- Illustrative only: adapt PK/FK types to the existing database.
CREATE TABLE charging_accessories (
  id UUID PRIMARY KEY,
  manufacturer TEXT NOT NULL,
  model TEXT NOT NULL,
  sku TEXT,
  oem_model_id UUID,
  kind TEXT NOT NULL,  -- cable, passive_adapter, active_adapter
  input_connector TEXT NOT NULL,
  output_connector TEXT NOT NULL,
  direction TEXT NOT NULL,
  charging_mode TEXT NOT NULL, -- AC, DC
  protocol_in TEXT,
  protocol_out TEXT,
  protocol_conversion BOOLEAN,
  hardware_revision TEXT,
  firmware_version TEXT,
  electrical_topology TEXT,  -- passthrough, voltage_conversion
  -- passthrough: the single envelope below applies on both sides
  min_voltage_v NUMERIC,
  max_voltage_v NUMERIC,
  continuous_current_a NUMERIC,
  peak_current_a NUMERIC,
  peak_duration_s NUMERIC,
  continuous_power_kw NUMERIC,
  advertised_power_kw NUMERIC,
  resistance_ohm NUMERIC,
  -- voltage_conversion: input = station side, output = vehicle side (single envelope left null)
  input_voltage_min_v NUMERIC,
  input_voltage_max_v NUMERIC,
  input_current_continuous_a NUMERIC,
  input_current_peak_a NUMERIC,
  output_voltage_min_v NUMERIC,
  output_voltage_max_v NUMERIC,
  output_current_continuous_a NUMERIC,
  output_current_peak_a NUMERIC,
  conversion_peak_duration_s NUMERIC,
  conversion_efficiency NUMERIC,
  cable_length_m NUMERIC,
  cooling_type TEXT,
  thermal_derating JSONB,
  safety_certifications JSONB,
  auxiliary_power JSONB,
  product_url TEXT,
  datasheet_url TEXT,
  source_metadata JSONB,
  updated_at TIMESTAMPTZ
);

CREATE TABLE accessory_offers (
  id UUID PRIMARY KEY,
  accessory_id UUID NOT NULL REFERENCES charging_accessories(id),
  merchant TEXT NOT NULL,
  country TEXT,
  price NUMERIC,
  currency TEXT,
  vat_included BOOLEAN,
  vat_amount NUMERIC,           -- required when vat_included is false
  shipping_price NUMERIC,
  shipping_currency TEXT,
  ships_to TEXT[],              -- destination countries
  stock_status TEXT,
  warranty_months INTEGER,
  product_url TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  valid_until TIMESTAMPTZ
);

CREATE TABLE accessory_compatibility (
  id UUID PRIMARY KEY,
  accessory_id UUID NOT NULL REFERENCES charging_accessories(id),
  vehicle_profile_id UUID,
  battery_variant_id UUID,      -- part of the matching key if vehicle profiles are model-level
  charger_profile_id UUID,
  charger_installation_id UUID,
  vehicle_firmware TEXT,
  charger_firmware TEXT,
  accessory_firmware TEXT,
  status TEXT NOT NULL, -- confirmed, reported, unverified, incompatible
  limitations JSONB,
  evidence JSONB,
  checked_at TIMESTAMPTZ
);

CREATE TABLE accessory_test_results (
  id UUID PRIMARY KEY,
  accessory_id UUID NOT NULL REFERENCES charging_accessories(id),
  vehicle_profile_id UUID,
  battery_variant_id UUID,
  charger_profile_id UUID,
  charger_installation_id UUID,
  -- configuration as tested (snapshot; later profile edits never relabel it; unknown stored as NULL)
  accessory_hardware_revision TEXT,
  accessory_firmware TEXT,
  vehicle_firmware TEXT,
  charger_firmware TEXT,
  electrical_topology TEXT,
  start_soc NUMERIC,
  end_soc NUMERIC,
  initial_battery_temp_c NUMERIC,
  ambient_temp_c NUMERIC,
  preconditioning_state TEXT,
  station_sharing_state JSONB,  -- concurrent sessions / available power during the test
  peak_power_kw NUMERIC,
  average_power_kw NUMERIC,
  duration_minutes NUMERIC,
  power_curve JSONB,
  success BOOLEAN,
  source_url TEXT,
  evidence_quality TEXT,
  tested_at TIMESTAMPTZ
);
```

**Measured tests and configuration:** a test supports an estimate only when its stored accessory hardware/firmware, vehicle firmware, charger firmware, installation and topology match the candidate being ranked. A test with a null firmware or topology, or applied to a different configuration, is marked as extrapolation: it supports an uncertainty range and does not replace the calculated curve. Updating a current equipment profile must not relabel historical tests.

Add FKs and indexes only after checking actual PK types, existing table names and data volume. For flexible source provenance, prefer reuse of an existing source/evidence table over duplication.

## 7. Charging simulation

### 7.1 Compatibility preflight

Before estimating power, verify adapter direction, physical connector, charging mode, operating voltage, protocol negotiation, safety interlocks and supported firmware/configurations. For a `voltage_conversion` adapter or a vehicle booster, the station↔adapter and adapter↔vehicle interfaces are two separate checks, each against its own envelope. An unsafe or incompatible combination is **not eligible** for recommendations.

**Fail closed.** A combination is eligible for a ranking category only when every safety-critical attribute needed for it is known from an acceptable source: direction, connector compatibility, charging mode, an operating voltage range covering the requested SoC window (below), continuous and peak current/power ratings, required certification, and required interlock/protocol support. Unknown values are never treated as zero loss, unlimited or compatible. A combination with an unknown attribute, or with unresolved source conflicts (§5), is `unverified`: it may appear in a separate unranked list with its missing fields, but cannot fill fastest, cheapest or best value. (This rule concerns unknown attributes; the minimum evidence level for a purchase recommendation remains a HUMAN decision, §11.)

**Voltage across the window.** Overlap of nameplate voltage ranges is not sufficient. The combination is eligible for a requested SoC window only when `V_batt(SoC, T)`, on the station side of any booster, lies inside the station-connector and adapter voltage limits at every SoC in that window, and the modeled net charging power is positive throughout. If only part of the window is reachable, the result reports the limiting condition, the SoC actually reached and the time to that SoC, flagged `window_completed: false`; it is never presented, or ranked, as completing the requested window. If feasibility cannot be established from the data, the result is an explicit `unknown`, not a finite time. Inside a published voltage range, use the current-versus-voltage envelope; do not apply the nameplate current below the voltage from which the source states full performance begins.

### 7.2 Instantaneous power

**Measurement boundary.** Every power curve, current limit and efficiency has a declared measurement boundary. Each constraint is transformed to the battery boundary, applying only the losses between that constraint and the battery. Battery-side limits (BMS current, vehicle charge curve) are never multiplied by upstream path efficiency, and station efficiency is not applied to a DC output rating (it already sits on the AC side of that figure). The spec fixes one convention for modeled battery power (terminal power, or net stored-energy power) and uses it for SoC integration and for comparison with measured tests. The no-adapter calculation keeps its documented boundary convention.

**Direct DC path** (used only when no component converts voltage and the vehicle is not boosting). Each current limit holds its peak value only until that component's `peak_duration_s` is used, then drops to its continuous rating.

```text
I_series(t) = min(
  I_vehicle_BMS(SoC, T, SoH),
  I_station_connector(V_batt, installation, sharing, t),
  I_cable(T_cable, t),
  I_adapter(T_adapter, t)
)
P_battery_kW = min(V_batt(SoC, T) * I_series(t) / 1000,
                   P_vehicle_charge_curve(SoC, T, SoH))
I_batt       = P_battery_kW * 1000 / V_batt
P_station_dc_kW = P_battery_kW + (I_batt^2 * R_series_ohm) / 1000
require P_station_dc_kW <= P_station_available   (DC power at the connector after power sharing)
```

If `P_station_dc_kW` would exceed `P_station_available`, reduce current until equal. If `R_series_ohm` is unknown, omit the loss term and report the loss as unknown.

**Voltage-converting path** (`voltage_conversion` adapter or vehicle booster): calculate input and output sides separately, each with its own voltage and current limits on its own voltage, coupled by `P_out <= P_in * conversion_efficiency` at a declared operating point. Do **not** apply one common current across a converter with different input/output voltages.

**AC path.** Limit AC current by the EVSE, the cable and the vehicle inlet; convert current to power with the supply's phase count and voltage (the same 32 A is about 7 kW single-phase and about 22 kW on 400 V three-phase); limit AC power by the onboard-charger rating. Battery-side current comes from the onboard converter through the voltage-converting rule. AC current is never placed in the direct-DC `I_series` formula.

**Time-varying inputs.** Optional inputs: `ambient_temperature_c`, `preconditioning_state`, a battery-temperature trace, and `station_available_power_kw` or concurrent-session count over time. When absent, the simulation holds battery temperature and full station power constant; that assumption is recorded in `assumptions` and the reported range is widened. Test results record temperatures and sharing state (§6.3).

Integrate over SoC using battery usable energy and the SoC-dependent effective power, while tracking accessory thermal state and time-limited peak ratings. Derating can depend on temperature, duration, charger power sharing, cable cooling and battery preconditioning. Missing curves should produce uncertainty ranges, not fictitious precision.

### 7.3 Outputs

- Theoretical electrical ceiling at specified battery voltage, advertised maximum, continuous/peak ratings.
- Estimated peak kW, sustained/average kW, and 10–80% time (or user-defined SoC window).
- `window_completed`, the SoC actually reached, and the limiting condition when the requested window is not fully reachable (§7.1).
- Dominant bottleneck by SoC segment, thermal/protocol limitations and success probability if evidenced.
- Confidence, assumptions, model/firmware configuration, test/source links and calculation timestamp.

**Example:** 250 A × 400 V = 100 kW theoretical current-limited power; this does **not** establish a 100 kW sustained LEAF session. A 125 A *continuous* rating corresponds to 50 kW at 400 V.

## 8. Research and recommendation pipeline

1. Resolve exact vehicle, market, year, battery variant and charging port.
2. Resolve candidate charger models and optionally actual station installations.
3. Discover cable/adapter models, OEM equivalents and retailer offers.
4. Verify manufacturer specifications and source links; separate continuous/peak/advertised ratings.
5. Match vehicle × battery × adapter × charger model × installation/firmware; reject unsafe/incompatible candidates.
6. Simulate each eligible combination under standardized SoC, temperature and station conditions.
7. Attach measured tests where available; flag extrapolated or missing evidence.
8. Rank and return exactly three **categories** when enough eligible candidates exist; the same product may win more than one category. Do not fabricate three distinct winners. The **no-adapter configuration** is a first-class baseline, and an adapter is ranked only when it improves modeled time or cost over it under the stated conditions.

### 8.1 Ranking definitions

- **Fastest:** minimum modeled charging duration under comparable conditions, favoring verified compatibility and measured performance; report ties.
- **Cheapest:** lowest **delivered** price (VAT + shipping) among safe compatible options meeting a stated minimum performance/evidence threshold.
- **Best value:** among eligible products with a comparable delivered price, the lowest delivered price per minute saved against the **baseline**: the no-adapter session for the same vehicle, charger, SoC window and conditions. If no adapter is required, or no no-adapter session exists, the baseline is the eligible candidate with the longest estimated duration. A candidate that saves no time does not win on performance. Ties break by lower delivered price, then longer `warranty_months`; every remaining tie is listed. Evidence quality is an eligibility decision (§7.1), not a second weight in this score. The response reports `ranking_method`, the baseline and the offer used; any thresholds are configurable and not fixed here. Avoid rewarding headline kW the car cannot use.

Where charging times are equal, consider reliability, warranty, support and price. For a vehicle already limited to 50 kW, a 250 A adapter may offer no benefit over a reliable lower-current model.

**Ties.** Each category holds an ordered list of results; products that tie occupy the same category, are ordered by the tie-breaks above and are all returned (`tied_with`). **AC.** The §7.2 AC path evaluates AC candidates; whether the three categories include AC cables or only DC adapters is a HUMAN decision (§11). Until it is settled, AC candidates are evaluated and listed unranked.

### 8.2 Recommendation response contract

```json
{
  "vehicle_profile_id": "vehicle-id",
  "battery_variant_id": "battery-id",
  "market": "DE",
  "charger_profile_id": "optional-charger-model-id",
  "charger_installation_id": "optional-site-unit-id",
  "start_soc": 10,
  "target_soc": 80,
  "battery_temperature_c": 25,
  "ambient_temperature_c": null,
  "preconditioning_state": null,
  "delivery_destination": "DE",
  "ranking_method": "price_per_minute_saved_vs_baseline",
  "baseline": null,
  "recommendations": {
    "fastest":    { "status": "ranked | no_adapter_needed | no_eligible_candidate | insufficient_evidence", "results": [], "reason": "" },
    "cheapest":   { "status": "...", "results": [], "reason": "" },
    "best_value": { "status": "...", "results": [], "reason": "" }
  },
  "unranked_unverified": [],
  "required_per_recommendation": [
    "manufacturer", "model", "sku", "product_url",
    "compatibility_status", "charger_model_context",
    "continuous_current_a", "peak_current_a",
    "theoretical_max_kw", "expected_peak_kw",
    "expected_average_kw", "estimated_minutes",
    "performance_range", "price_total", "currency",
    "merchant", "purchase_url", "warranty_months",
    "window_completed", "reached_soc", "tied_with",
    "performance_confidence", "evidence_urls",
    "assumptions", "recommendation_reason"
  ]
}
```

The above is a contract sketch: actual responses should populate recommendation objects and use `null` when values are unknown. A category's `status` distinguishes "no adapter needed", "no eligible candidate" and "insufficient evidence" from a ranked result. Prices must be timestamped; model performance must be linked to test conditions and a specific charger model or installation.

## 9. Validation and acceptance criteria

| Phase | Deliverable | Acceptance criterion |
|---|---|---|
| 1 | Live schema audit | Field-by-field existing/equivalent/missing map and migration impact |
| 2 | Charger model registry | Canonical models, revisions, voltage/current envelopes and official source links |
| 3 | Accessory catalog | OEM deduplication, direction, ratings, firmware, evidence and prices |
| 4 | Compatibility | Vehicle × accessory × charger/firmware; unsafe combinations excluded |
| 5 | Calculator integration | No-adapter results remain unchanged; new constraints enforced |
| 6 | Recommendations | Three categories with price, realistic power/time and evidence |
| 7 | Field validation | Predicted vs measured peak/average kW and session time tracked |

Regression tests must cover voltage mismatch, peak-versus-continuous rating confusion, adapter reversal, charger power sharing, thermal derating, firmware incompatibility, duplicate OEM products, expired offers, missing data, and vehicle-limited cases. Round 1 adds:

- 50 kW battery-side limit, 100 kW upstream availability, 0.9 path efficiency: battery-terminal result is 50 kW; no-adapter results unchanged.
- Peak current held beyond `peak_duration_s` is rejected; a 500 A boost mode is not sustained.
- Partial voltage overlap (e.g. 350–400 V station, battery 360→420 V) and zero-progress windows: `window_completed: false` or `unknown`, never a finite full-window time or rank.
- Unequal input/output voltages with conversion efficiency below 1; a passthrough adapter uses the single envelope.
- A null voltage or current rating, or an unresolved direction/voltage/current/protocol source conflict (e.g. the Akyga inlet/outlet labels): not ranked, reported with the missing field.
- No-adapter baseline (CCS2 vehicle at a CCS2 station); vehicle-limited case where a higher-current adapter changes nothing; a case where headline kW and modeled usable kW rank two adapters differently (best value).
- Two adapters tied on duration and delivered price: both returned.
- AC: 32 A single-phase versus three-phase; AC cable evaluated through the onboard charger.
- Shared cabinet; cold and warm pack; test results with temperatures and sharing state.
- Two battery variants of one model with different charge curves and maximum DC power.
- Test on firmware A not attached to firmware B or to a different topology; later profile edits do not relabel tests.
- Unknown shipping/VAT (unknown, not zero), mixed currencies without a stored rate, stale or `valid_until`-expired offers, offer not shipping to the destination.

## 10. Rollout strategy

1. Inspect the actual Fuel Atlas schema and identify equivalent existing columns.
2. Extend `charger_profiles` and `vehicle_profiles` with nullable attributes only where needed.
3. Add accessory, offer, compatibility and test-result entities; add installation entity only if necessary.
4. Integrate accessory and charger operating envelopes as optional constraints in the existing calculator.
5. Seed linked charger/adapter catalogs with source-backed specifications and dated prices.
6. Validate against measured charging sessions, then activate the three-category ranking.

**Non-goals:** inventing charger model specs from family-level marketing, assuming every 250 kW label represents continuous output, treating unverified seller compatibility as certified, or rebuilding the existing FuelBuddy charging engine.

## 11. Outstanding verification work

- Inspect the live Fuel Atlas repository/database to confirm existing tables, columns and APIs.
- Verify manufacturer-specific charger datasheets and exact model/firmware variants, including HYC150 installation configurations.
- Refresh all adapter product links, prices, stock and warranty by market.
- Obtain reproducible vehicle × adapter × charger test curves, especially LEAF e+ with CCS2-to-CHAdeMO adapters.
- Validate the reviewer-reported HYC150, Akyga and Porsche facts quoted in §5 against the primary sources.

### Open HUMAN decisions (single carried-forward list)

HUMAN is not answering during the automated loop; CLAUDE has not decided these. The ids continue the FuelBuddy `FB-D` series for this project and are provisional tracking ids.

| ID | Question | Spec § | Status |
|---|---|---|---|
| FB-D8 | Minimum evidence level for a product to qualify for a purchase recommendation (e.g. manufacturer datasheet only vs. plus a field test) | §7.1, §8.1, §9 | open |
| FB-D9 | Do the three recommendation categories include AC cables, or only DC adapters? (Interim: AC candidates are evaluated and listed unranked.) | §8.1 | open |
