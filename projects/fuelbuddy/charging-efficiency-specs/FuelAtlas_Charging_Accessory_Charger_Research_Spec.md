# Fuel Atlas — Charging Equipment, Adapter and Battery Research Specification

**Version:** 1.7 (proposal)  
**Date:** 2026-10-21  
**Status:** Draft; live database/repository schema not yet inspected. Round-1, round-2, round-3, round-4, round-5 and round-6 reviews consolidated (see `reviews/round-1/CONSOLIDATION.md`, `reviews/round-2/CONSOLIDATION.md`, `reviews/round-3/CONSOLIDATION.md`, `reviews/round-4/CONSOLIDATION.md`, `reviews/round-5/CONSOLIDATION.md`, `reviews/round-6/CONSOLIDATION.md`); open HUMAN decisions are listed in §11.

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
- Voltage min/max, continuous current, peak current, peak duration, continuous/advertised power, cable length, series resistance/losses, cooling, thermal derating, and for AC accessories the supported phase count (`ac_phases`). For `voltage_conversion`, these are stored separately for the input (station) side and the output (vehicle) side (voltage, current, **power**, and peak duration for each side), plus conversion efficiency. Power caps are stored as published; a cap is never derived solely by multiplying independent maximum voltage and current ratings.
- **Peak mode:** whether the accessory has a peak/boost rating is stored explicitly (`peak_mode`: `none`, `rated` or `unknown`). `none` means the continuous rating applies at all times and satisfies the §7.1 rating check; `rated` has stored peak values, and the peak is held only when `peak_duration_s` is also stored; `unknown` is an unknown attribute under §7.1. A peak current or power with no stored `peak_duration_s` is not held and is not `unknown`: the continuous rating is used and the range widened, as for vehicles (§6.1), and the missing duration alone does not fail closed. Vehicle profiles (§6.1) and charger profiles (§6.2) carry the same flag as `dc_peak_mode`, with the same meanings; a bare null peak rating on any entity is never read as `none`.
- Firmware/hardware versions, auxiliary power requirements, connector lock/interlock behavior (`interlock_behavior`), fault shutdown (`fault_shutdown`) and certification evidence.
- Vehicle/charger/firmware compatibility status and evidence; reject unsupported safety-critical combinations.

### 4.4 Commercial data

- Seller, country, offer URL, SKU, currency, base price, VAT inclusion and VAT amount, shipping and its currency, total delivered price, stock, lead time, warranty, date checked and offer validity end.
- Maintain price history snapshots rather than overwriting historical prices.
- **Delivered price** is computed for a stated destination **country** (postcode or region granularity is not supported; FB-D10), all in one currency, from the offer row and its destination row for that country (`accessory_offer_destinations`, §6.3; `country` on the offer is the seller's country): `price + shipping_price` when `vat_included` is true, `price + vat_amount + shipping_price` when it is false. Shipping and VAT amounts are per destination; one destination's figures are never used for another. Unknown VAT or shipping makes the delivered total **unknown, never zero**. An offer with an unknown total, mixed currencies and no exchange rate available at ranking time, no availability to the destination, or that is expired cannot win cheapest or best value. `vat_amount` is in the offer's `currency`; `shipping_price` is in `shipping_currency`. The response `currency` is the single **comparison currency** for the request: the request's `display_currency` when present, otherwise a configured default comparison currency that does not depend on candidate enumeration order. Every price used together in a ranking, a price tie-break or `delivered_price / minutes_saved` is expressed in that one currency, so offers in different currencies are never compared as raw numbers (EUR 100 against USD 110 at 0.8 EUR per USD compares as EUR 100 against EUR 88). When conversion is needed, each converted source currency (the offer `currency` and `shipping_currency` can each need one) is reported as its own record with its exchange rate, source and timestamp, and `fx_rate` is the number of units of the response `currency` per one unit of that record's source currency (`fx_from`). An offer whose conversion rate is unavailable for any source currency is ineligible.
- **Offer freshness:** an offer is expired when `valid_until` is before the ranking time; if `valid_until` is absent, when `observed_at` is older than a configurable maximum age (no fixed period is set here). Expired offers stay in price history.

## 5. Source-link policy (MANDATORY)

Every **named charger, cable or adapter model** in research output must have a clickable official manufacturer product page or official technical document where available. If neither exists, provide the exact retailer listing and label it accordingly. Each claim about a rating must point to its supporting source; do not use a generic manufacturer homepage as proof of a model-specific value.

Minimum provenance fields: `source_url`, `source_title`, `publisher`, `evidence_type`, `retrieved_at`, `published_at` (nullable), `applicable_model_revision`, `confidence`, `claim_field`. Track conflicting sources explicitly. **Tracking a conflict is not resolving it:** if retained sources disagree on direction, which connector faces the station, connector type, charging mode, electrical topology (`passthrough` or `voltage_conversion`), minimum or maximum voltage, series resistance (including per-side resistance of a `voltage_conversion` adapter), continuous or peak current, continuous, peak or advertised power (including each side's continuous and peak power cap of a `voltage_conversion` adapter), peak duration, `peak_mode`, AC phase count (`ac_phases`), conversion efficiency, or the protocol on either side, the accessory is **not eligible** for any ranking category. The same applies to a disagreement on any vehicle or charger field used in the calculation: `dc_booster_engagement` (including its voltage condition), `dc_booster_ratings` (including its resistances), `dc_peak_mode`, the DC voltage range, continuous or peak current or power, `peak_duration_s`, `voltage_current_envelope`, `full_performance_from_v`, or the battery voltage curve makes every candidate that depends on that profile `unverified`. Every conflicting value is stored with its source; a value is used for a recommendation only after the rejected alternatives are stored as rejected.

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

Prefer nullable columns on existing entities and five new accessory entities (accessories, offers, offer destinations, compatibility, test results). Add `charger_installations` **only if** the existing charger profile cannot already represent physical installations. Preserve existing IDs, endpoint contracts and diagnostic mappings.

### 6.1 Existing `vehicle_profiles` (optional additions)

`battery_variant_id`, `battery_voltage_min_v`, `battery_voltage_max_v`, `battery_voltage_curve`, `dc_charge_current_continuous_a`, `dc_charge_current_peak_a`, `dc_charge_peak_duration_s` (a peak current with no stored duration is not held: the estimate uses the continuous rating and widens the range), `dc_peak_mode` (`none`, `rated` or `unknown`; §4.3), `bms_charge_limit_map`, `battery_thermal_limit_map`, `dc_protocol_version`, `software_version`, `dc_booster_capability`, `dc_booster_engagement` (`always`, `bypassable` or `unknown`, with the voltage condition under which a bypassable booster is bypassed; §7.1), `dc_booster_ratings` (input and output voltage min/max, continuous and peak current, continuous and peak power, peak duration per side, input and output series resistance in ohm, efficiency; required to calculate a boosted path; a null resistance is `unknown` under §7.1 and is never stored or read as zero), `ac_phases`, `ac_current_max_a`, `onboard_charger_kw`, `onboard_charger_ratings` (DC output voltage min/max, maximum DC current, efficiency; required to model the AC path as a converter).

State of health is a property of a battery unit, not of a profile: no profile-level SoH is stored or used as if it described a specific vehicle. It enters the calculation only as the request input `battery_soh` (§7.2, §8.2).

### 6.2 Existing `charger_profiles` (optional additions)

`product_url`, `datasheet_url`, `hardware_revision`, `firmware_version`, `dc_voltage_min_v`, `dc_voltage_max_v`, `dc_current_continuous_a`, `dc_current_peak_a`, `peak_duration_s`, `dc_peak_mode` (`none`, `rated` or `unknown`; §4.3), `dc_power_continuous_kw` and `dc_power_peak_kw` (the published connector power cap, stored as published and never derived from maximum voltage times maximum current), `voltage_current_envelope`, `connector_configurations`, `power_sharing_policy`, `thermal_derating`, `full_performance_from_v`, `ac_outlet_phases`, `ac_outlet_current_max_a`, `ac_outlet_power_max_kw`, `ac_outlet_voltage_v`, `ac_outlet_voltage_convention` (`line_to_neutral` or `line_to_line`), `ac_outlet_power_factor`, `protocol_support` (e.g. JSONB array of `{protocol, revision}`), `authentication_requirements`, `source_metadata`.

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
  ac_phases INTEGER,         -- AC accessories: supported phase count
  peak_mode TEXT,            -- none, rated, unknown (§4.3)
  interlock_behavior JSONB,
  fault_shutdown JSONB,
  -- passthrough: the single envelope below applies on both sides
  min_voltage_v NUMERIC,
  max_voltage_v NUMERIC,
  continuous_current_a NUMERIC,
  peak_current_a NUMERIC,
  peak_duration_s NUMERIC,
  continuous_power_kw NUMERIC,  -- enforced as a cap (§7.2)
  peak_power_kw NUMERIC,        -- time-limited, held for peak_duration_s
  advertised_power_kw NUMERIC,
  resistance_ohm NUMERIC,
  -- voltage_conversion: input = station side, output = vehicle side (single envelope left null)
  input_voltage_min_v NUMERIC,
  input_voltage_max_v NUMERIC,
  input_current_continuous_a NUMERIC,
  input_current_peak_a NUMERIC,
  input_power_continuous_kw NUMERIC,
  input_power_peak_kw NUMERIC,
  input_peak_duration_s NUMERIC,
  output_voltage_min_v NUMERIC,
  output_voltage_max_v NUMERIC,
  output_current_continuous_a NUMERIC,
  output_current_peak_a NUMERIC,
  output_power_continuous_kw NUMERIC,
  output_power_peak_kw NUMERIC,
  output_peak_duration_s NUMERIC,
  input_resistance_ohm NUMERIC,   -- series resistance on each side of the converter
  output_resistance_ohm NUMERIC,
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
  country TEXT,                 -- seller's country, not the destination
  price NUMERIC,
  currency TEXT,
  vat_included BOOLEAN,         -- whether the listed price includes VAT
  stock_status TEXT,
  warranty_months INTEGER,
  product_url TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  valid_until TIMESTAMPTZ
);

-- one row per (offer, destination country); a country with no row is not shipped to
CREATE TABLE accessory_offer_destinations (
  offer_id UUID NOT NULL REFERENCES accessory_offers(id),
  destination_country TEXT NOT NULL,
  shipping_price NUMERIC,
  shipping_currency TEXT,
  vat_amount NUMERIC,           -- in the offer's currency; required when the offer's vat_included is false
  PRIMARY KEY (offer_id, destination_country)
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
  vehicle_protocol_version TEXT,
  charger_protocol_version TEXT,
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
  power_convention TEXT,        -- battery_terminal, stored_energy, station_dc, unknown; required when a power is stored
  measurement_boundary TEXT,
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

**Measured tests and configuration:** a test supports an estimate only when its stored accessory hardware/firmware, vehicle firmware, charger firmware, installation and topology match the candidate being ranked. A test with a null firmware or topology, or applied to a different configuration, is marked as extrapolation: it supports an uncertainty range and does not replace the calculated curve. Updating a current equipment profile must not relabel historical tests. A test supports a calculated estimate only when its `power_convention` equals the estimate's, or the conversion is documented; a test with a null or `unknown` convention supports only an uncertainty range.

Add FKs and indexes only after checking actual PK types, existing table names and data volume. For flexible source provenance, prefer reuse of an existing source/evidence table over duplication.

## 7. Charging simulation

### 7.1 Compatibility preflight

Before estimating power, verify adapter direction, physical connector, charging mode, operating voltage, protocol negotiation, safety interlocks and supported firmware/configurations. For a `voltage_conversion` adapter or a vehicle booster, the station↔adapter and adapter↔vehicle interfaces are two separate checks, each against its own envelope. An unsafe or incompatible combination is **not eligible** for recommendations.

**Booster engagement.** A vehicle booster is in the circuit only as `dc_booster_engagement` states (§6.1): `always`, or `bypassable` and the station-side voltage lies outside the condition under which the booster is bypassed. That decision is made once per session on the station's declared DC output voltage at the connector (the operating-point voltage the policy selects, §7.2), not on the loaded terminal voltage, so it does not depend on the solved current; the decision and the voltage used are recorded in `assumptions`. If that voltage is not declared, or the policy's feasible range straddles the bypass condition, engagement is `unknown`. A bypassed booster contributes no input limit, no efficiency and no series resistance: its `dc_booster_ratings` resistances describe the boost path and are not part of `R_series_ohm` while it is bypassed, and the direct path (or the adapter path alone) applies. A bypass-path resistance, when a source states one, is stored and used; otherwise the bypass is treated as a zero-ohm connection and that assumption is recorded in `assumptions`. When a `voltage_conversion` adapter and an engaged booster are both in the path, they are two converter stages solved as chained stages (§7.2, "Converter stages"). If a vehicle has `dc_booster_ratings` but engagement is `unknown`, feasibility is `unknown`.

**Published envelopes.** Inside a published voltage range, use the current-versus-voltage envelope on every path (direct, converting and AC). Do not apply the nameplate current below the voltage from which the source states full performance begins (`full_performance_from_v`); there, use the envelope current, and if no envelope point exists the current is unknown and the result is `unknown`, not the nameplate. `full_performance_from_v` is compared with the DC connector voltage `V_station` on direct and converting paths; it is never compared with `V_batt`, `V_in` or an AC supply voltage, and the AC path follows the AC equations (§7.2). At and above it, available current is the smaller of the nameplate or envelope current and `dc_power_continuous_kw * 1000 / V_station` when that power cap is present. While the charger's peak budget remains (§7.2) and `dc_power_peak_kw` is present, the power cap in this current limit is `dc_power_peak_kw`; after the budget is exhausted it is `dc_power_continuous_kw`. A charger with a null DC power cap and no `station_available_power_kw` in the request has an unknown station power limit, which is `unknown` under the fail-closed rule below.

A null `full_performance_from_v` is not read as zero and not as "full performance at every voltage". If the source states no threshold and the envelope does not establish the available current at the operating voltage, the charger's available current is `unknown` and the combination is `unverified`. If the envelope is complete, it is used at every voltage, the threshold's absence is recorded in `assumptions`, and the nameplate current is never used below an unstated threshold.

**Fail closed.** A combination is eligible for a ranking category only when every safety-critical attribute needed for it is known from an acceptable source: direction, connector compatibility, charging mode, an operating voltage range covering the requested SoC window (below), continuous and peak current/power ratings, every applicable continuous and peak current/power rating of the accessory, the vehicle and the charger (an entity with `peak_mode: none` needs no peak value and satisfies the check; `peak_mode: unknown` fails closed), required certification, and required interlock/protocol support. State of health is not an eligibility attribute; its absence is an assumption under §7.2. Unknown values are never treated as zero loss, unlimited or compatible. A combination with an unknown attribute, or with unresolved source conflicts (§5), is `unverified`: it may appear in a separate unranked list with its missing fields, but cannot fill fastest, cheapest or best value. (This rule concerns unknown attributes; the minimum evidence level for a purchase recommendation remains a HUMAN decision, §11.)

**Voltage across the window.** Overlap of nameplate voltage ranges is not sufficient. Voltage is checked interface by interface, at every SoC in the requested window, and the modeled net charging power must be positive throughout.

- **Direct path** (no converter, no boost): the voltage at the station connector and at each series element's terminals lies inside that element's limits. With known downstream series resistance the station-side voltage is `V_batt + I_batt * R_series_ohm`, not `V_batt` (§7.2).
- **Converting path** (`voltage_conversion` adapter or vehicle booster): two interfaces, each checked at its own terminal voltage (§7.2): `V_station` inside the station-connector limits, `V_in_1 = V_station - I_in_1 * R_up` inside stage 1's converter-input limits only, `V_out_N = V_batt + I_batt * R_down` inside stage N's converter-output limits only (the final stage; for a single converter, `V_in` and `V_out`) and `V_batt(SoC, T)` inside the battery limits. For N > 1, an intermediate terminal is checked at its own stage-local voltage: stage k's output limits at `V_out_k` and stage k+1's input limits at `V_in_(k+1)`; the battery-side formula is never applied to a converter that is not the final stage. The station and converter-input ranges need to overlap only when `R_up` is zero; with a positive upstream resistance they are separate terminals. A battery voltage outside the station's range is not a rejection when a converter separates the two sides; a converter whose input range cannot be met at `V_in` for any feasible `V_station` is ineligible even if its output range covers the battery. The same local-terminal rule applies between successive converter stages.
- **AC path:** the same per-interface rule applies to the AC supply, cable, inlet and onboard charger. `V_batt` is never used as an AC-side voltage. If only part of the window is reachable, the result reports the limiting condition, the SoC actually reached and the time to that SoC, flagged `window_completed: false`; it is never presented, or ranked, as completing the requested window. If feasibility cannot be established from the data, the result is an explicit `unknown`, not a finite time.

### 7.2 Instantaneous power

**Measurement boundary.** Every power curve, current limit and efficiency has a declared measurement boundary. Each constraint is transformed to the battery boundary, applying only the losses between that constraint and the battery. Battery-side limits (BMS current, vehicle charge curve) are never multiplied by upstream path efficiency, and station efficiency is not applied to a DC output rating (it already sits on the AC side of that figure). The spec fixes one convention: `P_battery_kW = V_batt * I_batt / 1000` is **battery-terminal power**, and SoC integration uses **net stored-energy power**, with any battery-internal charging loss or auxiliary draw between the two boundaries modeled exactly once and separately from upstream path loss. If the inherited calculator uses a simplified terminal-to-stored-energy mapping, that mapping is retained and recorded as an assumption; no loss value is invented. Every calculated curve and measured test declares its boundary; compare only matching boundaries or document the conversion. The response exposes the convention (`power_convention`). The no-adapter calculation keeps its documented boundary convention.

**Direct DC path** (used only when no component converts voltage and the vehicle is not boosting). Each current or power limit holds its peak value only until that component's `peak_duration_s` is used, then drops to its continuous rating. A vehicle peak with no stored duration is not held (§6.1). **Peak budget:** unless a source supplies a different applicable duration or derating rule, `peak_duration_s` is a cumulative budget that is consumed at one second per second whenever the component's modeled current exceeds its continuous-current rating or its modeled power exceeds its continuous-power rating, whether the load is at the peak rating or between the continuous and peak ratings. Operation within both continuous ratings consumes no budget. For a converter, each side applies this rule to its own budget. Once exhausted, every corresponding continuous limit applies for the rest of the session and the budget does not regenerate; no longer permitted duration is inferred for an intermediate load. The convention is recorded in `assumptions`; a source that states a different semantic (for example a window counted from session start) is used instead and recorded.

```text
I_series(t) = min(
  I_vehicle_BMS(SoC, T, SoH),
  I_station_connector(V_station, installation, sharing, t),
  I_cable(T_cable, t),        -- omitted when no separately rated cable is in the path
  I_adapter(T_adapter, t)     -- omitted in the no-adapter baseline
)
P_battery_kW = min(V_batt(SoC, T) * I_series(t) / 1000,
                   P_vehicle_charge_curve(SoC, T, SoH))
I_batt       = P_battery_kW * 1000 / V_batt
V_station    = V_batt + I_batt * R_series_ohm      (V_station = V_batt when R_series_ohm is zero)
P_station_dc_kW = P_battery_kW + (I_batt^2 * R_series_ohm) / 1000
require P_station_dc_kW <= P_station_available   (DC power at the connector after power sharing)
require V_station within the station voltage range
require, for every series element e: V_e * I_batt / 1000 <= that element's applicable
         continuous or peak power cap (e.g. passthrough continuous_power_kw), at e's declared boundary
```

`V_e` is the voltage at element e's station-side terminal: `V_e = V_batt + I_batt * R_battery_to_e`, where `R_battery_to_e` is the sum of `resistance_ohm` of the elements between the battery and that terminal, including e's own. If only the total `R_series_ohm` is known, every element is evaluated at the conservative bound `V_e = V_station` and that is recorded in `assumptions`. A null peak rating of any element, the vehicle or the station is read by that entity's `peak_mode` / `dc_peak_mode` (§4.3), not guessed: `none` uses the continuous rating, `unknown` fails closed (§7.1).

An absent element is an **omitted term**, not 0 A and not an unknown rating. The no-adapter baseline takes the vehicle limit and the station-connector limit only, plus a captive cable only when its rating is separate from the connector limit. `R_series_ohm` is the sum of `resistance_ohm` over the in-path series elements; if any in-path resistance is unknown, the loss stays unknown (omit the loss term and report it as unknown) and voltage feasibility at the station boundary cannot be certified from `V_batt` alone: the result is `unknown` under §7.1.

The current-limited quantities are solved together: reduce `I_batt` until the station current envelope (evaluated at `V_station`), the station voltage range, `P_station_available` and every component power cap all hold. A component power cap is never inferred solely by multiplying independent maximum voltage and current ratings. If no positive feasible current exists (e.g. the battery is already at the station's maximum voltage and `R_series_ohm` is positive), apply the incomplete-window rule of §7.1.

**Voltage-converting path** (`voltage_conversion` adapter or vehicle booster): calculate input and output sides separately, each with its own voltage and current limits on its own voltage, coupled by `P_out <= P_in * conversion_efficiency` at a declared operating point. Do **not** apply one common current across a converter with different input/output voltages, and do **not** use the direct-DC `I_series` on this path.

One converter stage has four terminals, each with its own voltage, and one current on each side (`I_out = I_batt`; `I_in_used` upstream). `R_up` is the sum of `input_resistance_ohm` and the `resistance_ohm` of upstream passthrough elements, between station and converter input; `R_down` is the sum of `output_resistance_ohm` and the `resistance_ohm` of downstream passthrough elements, between converter output and battery. A resistance stored on more than one of those columns is added once. For a chain of stages, a converter's side resistance is placed in the segment it physically borders and never on the far side of another converter: stage 1's `input_resistance_ohm` is in `R_up`, stage N's `output_resistance_ohm` is in `R_down`, and stage k's `output_resistance_ohm` and stage k+1's `input_resistance_ohm` are in `R_mid_k` (see "Converter stages").

```text
I_batt       = min(converter output current limit, I_vehicle_BMS(SoC, T, SoH),
                   every passthrough element between converter and battery)   (single stage, or the final stage; see "Converter stages")
P_battery_kW = V_batt * I_batt / 1000        <= P_vehicle_charge_curve(SoC, T, SoH)
V_out        = V_batt + I_batt * R_down
P_out_kW     = V_out * I_batt / 1000 = P_battery_kW + I_batt^2 * R_down / 1000   (<= output power caps)

I_in_used   <= min(I_station_connector(V_station, installation, sharing, t),
                   every passthrough cable or adapter on the station side,
                   converter input current limit)
V_in         = V_station - I_in_used * R_up
P_in_kW      = V_in * I_in_used / 1000                        (<= input power caps)
P_station_dc_kW = V_station * I_in_used / 1000 = P_in_kW + I_in_used^2 * R_up / 1000
require P_station_dc_kW <= P_station_available
require P_out_kW <= P_in_kW * conversion_efficiency
```

The vehicle charge curve limits `P_battery_kW` (battery-terminal power), not `P_out_kW`; the converter output carries the downstream loss on top of it. Station limits (voltage range, current envelope, `P_station_available`) apply at `V_station`; converter input limits at `V_in`; converter output limits at `V_out`; battery limits at `V_batt`. Conversion efficiency couples `P_out_kW` and `P_in_kW`. A passthrough adapter upstream of a booster is an `I_in_used` limit and is never compared with battery current. Reduce `I_in_used` and `I_batt` together until all constraints hold. Each side's peak current and power hold only for that side's own peak duration. If a converter efficiency or a side's power cap is unknown, it is not treated as lossless or unlimited (§7.1).

**Per-element power caps around a converter.** Every in-path passthrough cable or adapter is checked against its own continuous or peak power cap at its own terminal voltage, on its own side of the converter. On the battery side of the final converter, `V_e = V_batt + I_batt * R_batt_to_e`, where `R_batt_to_e` sums only the physical resistances from the battery up to and including e's station-side terminal (a converter's `output_resistance_ohm` is included only when its declared location lies within that interval; otherwise it contributes to `V_out` but not to `V_e`), and the check is `V_e * I_batt / 1000`. A path with N converter stages has N+1 conductive segments: passthrough elements upstream of stage 1 are limited at `I_in_1` (`I_in_used`), elements between stage k and stage k+1 at `I_out_k` (equal to `I_in_(k+1)`) and at the voltage along that segment, and elements downstream of the final stage at `I_batt`; an element's continuous and peak current limits and its power cap use its own segment current, so `V_e * I_batt` applies only downstream of the final stage. For an element in the segment between stage k and stage k+1, `V_e = V_out_k - I_out_k * R_outk_to_e`, where `R_outk_to_e` sums the resistances allocated between stage k's output and e's stage-k-side terminal (not including e's own resistance), and the check is `V_e * I_out_k / 1000`; when only that segment's total resistance is known, every element of it is evaluated at `V_out_k`. The fallback bound for the segment upstream of stage 1 is `V_station`, and for the segment downstream of the final stage it is `V_out_N`; `V_station` is never used for a middle segment. On the station side, `V_e = V_in + I_in_used * R_in_to_e`, where `R_in_to_e` sums `input_resistance_ohm` and the `resistance_ohm` of passthrough elements from the converter input up to and including e, and the check is `V_e * I_in_used / 1000`. The direct-path fallback `V_e = V_station` applies only on a path with no converter; on a converting path, if only the total of a segment's resistance is known, each element of that segment is evaluated at that segment's conservative terminal bound (`V_station` upstream of stage 1, `V_out_N` downstream of the final stage, `V_out_k` between stages k and k+1) and that is recorded in `assumptions`. The converter's "input/output power caps" are its own and do not replace these per-element checks. If an in-path element's power cap or either segment's resistance is unknown, the result is `unknown` (§7.1). If no positive feasible current exists (e.g. station maximum 400 V, converter input minimum 400 V, `R_up` > 0), apply the incomplete-window rule of §7.1.

**Converter stages.** When two converter stages are in the path (a `voltage_conversion` adapter and an engaged booster), number them 1 to N from the station toward the battery. The single-stage block above is the N = 1 case; for N > 1 the battery-endpoint relations in it do not apply to an intermediate stage. Each stage k is solved with stage-local terms: `P_in_k = V_in_k * I_in_k / 1000`, `P_out_k = V_out_k * I_out_k / 1000` and `P_out_k <= conversion_efficiency_k * P_in_k`, within that stage's own terminal voltage, current, power and peak-duration limits. Station constraints (voltage range, current envelope, `P_station_available`) apply only to the segment upstream of stage 1, where `V_in_1 = V_station - I_in_1 * R_up`; battery constraints (BMS current, charge curve, `V_batt`) apply only downstream of stage N, where `I_out_N = I_batt` and `V_out_N = V_batt + I_batt * R_down`. Each physical resistance is allocated to exactly one segment (`R_up`, `R_mid_k`, `R_down`). Between stage k and stage k+1 the passthrough and wiring resistance is `R_mid_k`, and `I_out_k = I_in_(k+1)`, `V_out_k = V_in_(k+1) + I_out_k * R_mid_k` and `P_in_(k+1) = P_out_k - I_out_k^2 * R_mid_k / 1000`. The two terminal voltages are equal only when `R_mid_k` is zero. With no inter-stage loss, efficiencies multiply from stage 1's input to stage N's output (0.9 and 0.9 give 0.81, so `P_in_1 = P_out_2 / 0.81`); between stage 2's input and stage 1's input only stage 1's efficiency applies (`P_in_1 = P_in_2 / 0.9`). An inter-stage `I^2 * R_mid` loss is added at the stage-1 output and passes through stage 1's efficiency only, not stage 2's. An unknown inter-stage resistance, stage efficiency or booster side resistance makes the result `unknown` (§7.1). `R_mid_k` is the sum of stage k's `output_resistance_ohm`, stage k+1's `input_resistance_ohm` and the `resistance_ohm` of any passthrough element between them. It is 0 ohm only when every resistance at that joint is known and each is 0 ohm (or none exists); a known nonzero adjacent side resistance is never treated as an empty allocation.

**Operating-point policy.** The policy selects a feasible tuple (`V_station`, `V_in`, `V_out`, currents) that satisfies the converting-path equations: `V_station` inside the station voltage range and `V_in` inside the converter-input range. The two are the same voltage, and the intersection of the ranges is used, only when `R_up` is zero. The implementation uses one versioned operating-point policy (station/converter voltage-control constraints and the rule that selects the feasible point at each time step), identified in `model_configuration` and applied identically to every candidate and to the baseline; the choice must not depend on candidate enumeration order. The duration fed to ranking is the one the policy selects; the performance range reports the spread over the intersection. If no policy point estimate or configured range-comparison rule exists, the result is listed unranked with an insufficient-evidence reason. The policy's content is not fixed here.

**AC path.** Limit AC current by the EVSE, the cable and the vehicle inlet; convert current to power with the supply's phase count and voltage; limit AC power by the minimum of the outlet's `ac_outlet_power_max_kw` when present, every in-path cable or adapter power cap at its own boundary, and the onboard-charger rating. An absent `ac_outlet_power_max_kw` is not treated as unlimited and no value is invented: the voltage-times-current bound from the equations below then applies. Battery-side current comes from the onboard converter through the voltage-converting rule, using `onboard_charger_ratings` (§6.1). AC current is never placed in the direct-DC `I_series` formula. AC current and power limits hold a peak value only until that component's `peak_duration_s` is used, then drop to the continuous rating, under the same peak-budget rule as the direct DC path; a peak with no stored duration is not held.

```text
single-phase, line-to-neutral:   P_ac_kW = U_ln_v * I_ac * power_factor / 1000
three-phase, line-to-line:       P_ac_kW = sqrt(3) * U_ll_v * I_ac * power_factor / 1000
three-phase, line-to-neutral:    P_ac_kW = 3 * U_ln_v * I_ac * power_factor / 1000
```

**AC inputs.** The phase count used is the minimum of the EVSE outlet (`ac_outlet_phases`), every in-path cable or adapter (`ac_phases`), the vehicle inlet and (consistently) the onboard charger (`ac_phases`), recorded in `assumptions`; a 32 A single-phase cable on a three-phase EVSE yields single-phase power. `P_in_kW` of the onboard converter is `P_ac_kW` from the equations above, never `V_in * I_in` on the AC voltage. The supply voltage, voltage convention and power factor come from the request (`ac_supply_voltage_v`, `ac_voltage_convention`, `power_factor`; §8.2) or the charger outlet (`ac_outlet_voltage_v`, `ac_outlet_voltage_convention`, `ac_outlet_power_factor`). The voltage and the convention that interprets it come from the same source: if the request supplies a voltage, its convention must also come from the request, and a missing request convention makes AC power `unknown`, never the request voltage with the outlet convention. When both a request voltage (with its convention) and an outlet voltage are present, the request pair is used and the outlet pair is recorded in `assumptions` as superseded. The power factor is taken from the request when present, otherwise from the outlet. The source of each value used is recorded. If any value is absent from both sources, AC power is `unknown`: 230 V, 400 V and power factor 1 are used only in the examples below, never as defaults. When the selected phase count is one and the supply is declared `line_to_line`, the single-phase equation uses the line-to-neutral voltage `U_ln = U_ll / sqrt(3)`; when it is declared `line_to_neutral`, `U_ln` is the supplied value. The phase count and the voltage actually used are recorded in `assumptions`.

The same 32 A is about 7.4 kW at 230 V single-phase and about 22.2 kW at 400 V line-to-line three-phase, both at power factor 1. Three-phase power is never computed as `n_phases * U_ll * I`. The voltage convention and power factor are recorded in `assumptions`. If the onboard charger's efficiency or DC output envelope is unknown, `onboard_charger_kw` serves only as an upper bound, the loss is reported unknown, the range is widened and the AC result is not ranked.

**Time-varying inputs.** Optional inputs: `ambient_temperature_c`, `preconditioning_state`, a battery-temperature trace, and `station_available_power_kw` or concurrent-session count over time. When absent, the simulation holds battery temperature and full station power constant; that assumption is recorded in `assumptions` and the reported range is widened. `station_available_power_kw`, when present, is the connector limit after sharing. `concurrent_session_count` does not by itself divide cabinet power: if the count is greater than one, `station_available_power_kw` is absent and `power_sharing_policy` does not evaluate to a connector power, feasibility is `unknown` (§7.1) and the full-power default is not applied. Test results record temperatures and sharing state (§6.3). The optional input `battery_soh` (0 to 1) is the SoH argument of the BMS limit. When it is absent, the SoH treatment used (including the inherited calculator's) is recorded in `assumptions`, the reported range is widened and the result is not presented as measured.

Integrate over SoC using battery usable energy and the SoC-dependent effective power, while tracking accessory thermal state and time-limited peak ratings. Derating can depend on temperature, duration, charger power sharing, cable cooling and battery preconditioning. Missing curves should produce uncertainty ranges, not fictitious precision.

### 7.3 Outputs

- Theoretical electrical ceiling at specified battery voltage, advertised maximum, continuous/peak ratings.
- Estimated peak kW, sustained/average kW, and 10–80% time (or user-defined SoC window).
- `window_completed`, the SoC actually reached, and the limiting condition when the requested window is not fully reachable (§7.1).
- `power_convention` (§7.2) and the calculation configuration (accessory, vehicle and charger hardware/firmware used).
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
8. Rank and return exactly three **categories** when enough eligible candidates exist; the same product may win more than one category. Do not fabricate three distinct winners. The **no-adapter configuration** is a first-class baseline. When a completed no-adapter session exists, an adapter is a candidate in fastest, cheapest and best value only when its completed-window duration is strictly shorter than that session; the no-adapter session has no delivered price and is not a cheapest row (there is no cost test). When the no-adapter configuration is known to be incompatible (e.g. a connector mismatch), eligible adapters remain rankable in fastest and cheapest without a native-session improvement test. An unknown native-session result is recorded as unknown, is not assigned an invented duration, and is noted in `assumptions`.

### 8.1 Ranking definitions

**Candidate set.** Fastest, cheapest and best value admit only results with `window_completed: true` over the same requested SoC window. A result with `window_completed: false`, or with feasibility `unknown`, is not a candidate in any category; it is reported only with `reached_soc`, the limiting condition and the time to the SoC reached. Durations are never compared across unequal SoC intervals.

- **Fastest:** minimum modeled charging duration among eligible candidates under comparable conditions. Evidence quality is an eligibility gate (§7.1), not a duration discount or a weight. Report ties.
- **Cheapest:** lowest **delivered** price (VAT + shipping) among safe compatible options meeting a stated minimum performance/evidence threshold.
- **Best value:** the lowest `delivered_price / minutes_saved` among candidates with `minutes_saved > 0` against the **baseline**: the completed no-adapter session for the same vehicle, charger, SoC window and conditions. If no completed no-adapter session exists (it is known incompatible, unknown or partial), best value has **no baseline**: the category is empty and its reason says there is no completed no-adapter session to save time against. Another candidate's duration is never used as the baseline, so a candidate cannot win by being compared with itself and adding a candidate that cannot win never changes the winner. Fastest and cheapest are unchanged (FB-D11). A candidate with `minutes_saved <= 0` cannot win best value; under the interim baseline the native-session gate (§8 step 8) already excludes such candidates, so this clause is a safeguard that becomes reachable only if FB-D11 adopts another baseline. With a completed native session and no candidate strictly faster, the category status is `no_adapter_needed` (§8.2). There is no comparable-price filter. Ties break by lower delivered price, then longer `warranty_months`; every remaining tie is listed. Evidence quality is an eligibility decision (§7.1), not a second weight in this score. The response reports `ranking_method`, the baseline and the offer used; any thresholds are configurable and not fixed here. Avoid rewarding headline kW the car cannot use.

Where fastest durations are equal, order by lower delivered price, then longer `warranty_months`; support and reliability are not scored. For a vehicle already limited to 50 kW, a 250 A adapter may offer no benefit over a reliable lower-current model.

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
  "battery_soh": null,
  "preconditioning_state": null,
  "battery_temperature_trace_c": null,
  "station_available_power_kw": null,
  "concurrent_session_count": null,
  "ac_supply_voltage_v": null,
  "ac_voltage_convention": null,
  "power_factor": null,
  "delivery_destination": "DE",
  "display_currency": null,
  "ranking_method": "price_per_minute_saved_vs_baseline",
  "baseline": null,  // object or null (below)
  "recommendations": {
    "fastest":    { "status": "ranked | no_adapter_needed | no_eligible_candidate | insufficient_evidence", "results": [], "reason": "" },
    "cheapest":   { "status": "...", "results": [], "reason": "" },
    "best_value": { "status": "...", "results": [], "reason": "" }
  },
  "unranked": [],
  "required_per_recommendation": [
    "manufacturer", "model", "sku", "product_url",
    "compatibility_status", "charger_model_context",
    "continuous_current_a", "peak_current_a",
    "theoretical_max_kw", "expected_peak_kw",
    "expected_average_kw", "estimated_minutes",
    "performance_range", "minutes_saved", "price_total", "currency",
    "price_observed_at", "price_valid_until",
    "fx_conversions",
    "merchant", "purchase_url", "warranty_months",
    "window_completed", "reached_soc", "limiting_condition",
    "dominant_bottleneck", "model_configuration", "power_convention",
    "calculated_at", "tied_with",
    "performance_confidence", "evidence_urls",
    "assumptions", "recommendation_reason"
  ]
}
```

The above is a contract sketch: actual responses should populate recommendation objects and use `null` when values are unknown. A category's `status` distinguishes "no adapter needed", "no eligible candidate" and "insufficient evidence" from a ranked result. `ranked` means the category has at least one result. `no_adapter_needed` means a completed no-adapter session exists and no adapter has a strictly shorter completed duration (§8 step 8): adapter `results` are empty and that session is the `baseline`; this status applies to every category (fastest, cheapest and best value) in that situation. `no_eligible_candidate` means the category has no result for a known reason, including best value with no baseline and best value with no positive `minutes_saved`. `insufficient_evidence` is the §7.1 `unknown` outcome, returned with a reason.

`recommendations.<category>.results` holds only ranked candidates, never a partial-window result. The `unranked` array holds every evaluated or unverified result that is not ranked, each entry with a `reason` (`unknown_attribute`, `partial_window`, `scope_undecided` for AC candidates under FB-D9's interim, `not_faster_than_native_session` for an eligible, completed adapter excluded only by the §8 step 8 gate, reported with its `estimated_minutes` and `minutes_saved` (zero or negative), or `insufficient_evidence`), the missing or limiting fields, `reached_soc`, `limiting_condition`, `time_to_reached_soc`, `window_completed` and the calculation configuration. `baseline` is `null` or `{kind: "no_adapter_session", estimated_minutes, window_completed, vehicle_profile_id, charger_profile_id, charger_installation_id, start_soc, target_soc, conditions, power_convention}`; `minutes_saved = baseline.estimated_minutes - estimated_minutes`, and is null when there is no baseline. The baseline object is the representation of whichever baseline FB-D11 allows; it does not decide FB-D11. The optional inputs `battery_temperature_trace_c`, `station_available_power_kw` and `concurrent_session_count` are scalars or time series as §7.2 permits; when absent, the constant-temperature/full-power assumption is recorded in `assumptions` and the range widened. `price_observed_at` is the winning offer's `observed_at`; `price_valid_until` is null when the offer has no `valid_until`; `fx_conversions` is null unless a conversion was used, else an array with one record `{fx_from, fx_rate, fx_source, fx_timestamp}` per converted source currency, where `fx_rate` is in units of the response `currency` (the comparison currency: the request's `display_currency`, else the configured default comparison currency; §4.4) per one unit of `fx_from`. An offer already in the response `currency` needs no record for its price; one whose required rate is unavailable is excluded from price-based selection. The optional AC inputs follow §7.2 (absent → AC power `unknown`). Prices must be timestamped; model performance must be linked to test conditions and a specific charger model or installation.

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

Round 2 adds:

- Passthrough accessory rated 400 V / 250 A / 60 kW continuous: modeled power does not exceed 60 kW at its boundary; a converter whose power cap binds before either current limit.
- 400 V station maximum, 400 V battery, positive `R_series_ohm`: no positive feasible current, `window_completed: false`; a case where voltage headroom reduces current before the power cap does; unknown resistance gives `unknown` feasibility.
- Booster or converting adapter with a 400 V station and an 800 V pack: eligible by the per-interface voltage rule; converter input range excluding the station voltage: ineligible; a 125 A passthrough adapter upstream of a booster never yields input current above 125 A.
- Converter with different input and output peak durations; vehicle peak current with no stored duration uses the continuous rating.
- A partial-window result (e.g. 350–400 V station, battery 360→420 V) with a shorter clock than a completed window never wins fastest, cheapest or best value.
- Connector mismatch with one eligible adapter (rankable without a native session) and with two equal-duration adapters; a negative `minutes_saved` cannot win best value; a baseline with no cable or adapter term is not read as 0 A or unknown.
- A stated nonzero terminal-to-stored-energy loss, distinct from upstream path loss.
- AC: 32 A at 230 V single-phase about 7.4 kW and at 400 V line-to-line three-phase about 22.2 kW; onboard charger with unknown efficiency is an upper bound only and unranked.
- Conflicting topology or advertised power between sources: not ranked.
- Request carrying `station_available_power_kw` and `concurrent_session_count` (shared cabinet) through the §8.2 contract.

Round 3 adds:

- 400 V station maximum, 400 V converter input minimum, positive upstream resistance: no positive feasible current, `window_completed: false`; a downstream-resistance case where `V_out` exceeds `V_batt`; unknown segment resistance gives `unknown`.
- Differing feasible input voltages change duration: changing candidate enumeration order does not change the operating point or the winner; no policy point estimate gives an unranked result with an insufficient-evidence reason.
- A 400 V / 250 A / 60 kW passthrough adapter upstream of a booster never carries more than 60 kW, and the same for a downstream passthrough element.
- Two series elements with a power cap that passes at `V_station` but fails at `V_batt` (or the reverse): deterministic result under the `V_e` convention.
- A 250 A continuous-only adapter (`peak_mode: none`) is eligible and modeled at 250 A; an adapter with a 500 A peak and no duration is modeled at 250 A with a widened range; `peak_mode: unknown` is `unverified`.
- A 32 A single-phase cable on a three-phase EVSE with an 11 kW onboard charger yields about 7.4 kW, not 11 or 22.2 kW; missing supply voltage, convention or power factor gives `unknown` AC power, not 7.4 or 22.2 kW.
- A merchant shipping one adapter to DE and FR at different shipping prices gives different delivered totals and possibly a different cheapest winner; a country with no destination row is not shipped to.
- A converted shipping price returns `fx_rate`, `fx_source` and `fx_timestamp` and `price_observed_at` in the response.
- Two sources giving different minimum voltages, or different series resistances, for one accessory: not ranked, conflicting field reported.
- A station-DC test is not attached to a battery-terminal estimate; a stored-energy test is not compared without conversion; a test with a null convention supports a range only.
- Vehicle supporting only DIN SPEC 70121 at a charger supporting only ISO 15118: `unverified`, not ranked.
- Best value with candidates 45 min / €20 and 30 min / €80 and no completed no-adapter session: category empty; adding a 60 min / €500 candidate changes nothing; a single eligible adapter is not a best-value winner against itself.
- Completed native session of 40 min, adapters of 50 min / €30 and 35 min / €200: only the 35 min adapter is a candidate and cheapest is the €200 adapter.
- Pack 600–800 V, booster input 200–500 V, station 700 V, profile says the booster is bypassed inside the pack window: eligible on the direct path; the same vehicle at a 400 V station keeps the booster input limit; unknown engagement gives `unknown`.
- DC nameplate current, `full_performance_from_v` above the battery voltage and no envelope point there: `unknown`.
- `concurrent_session_count` 2, null `station_available_power_kw`, sharing policy not evaluable: `unknown`, not the cabinet nameplate.

Round 4 adds:

- Converter, 400 V battery, 100 A, 0.1 ohm downstream, 40 kW battery charge-curve limit: `P_battery_kW` 40, `V_out` 410 V, `P_out_kW` 41, converter input at efficiency 0.9 at least `41 / 0.9` (about 45.56 kW).
- Fixed 410 V station, converter accepting 390–405 V, 0.1 ohm upstream, 100 A: feasible at `V_in` 400 V when all other limits permit, although the nameplate ranges do not intersect.
- Station 800 V, battery 400 V, upstream current 110 A, upstream cable cap 60 kW: ineligible (88 kW at the cable). Station 400 V, `V_out` 800 V, downstream current 100 A, downstream cable cap 50 kW: ineligible (80 kW).
- Adapter efficiency 0.9 plus booster efficiency 0.9, `R_mid` 0.1 ohm, 100 A between them, 40 kW battery-side power, all other resistances and losses zero: booster input at least `40 / 0.9` (about 44.44 kW), adapter output `44.44 + 1` (about 45.44 kW), adapter input at least `(40 / 0.9 + 100^2 * 0.1 / 1000) / 0.9` (about 50.49 kW; not `(40 + 1) / 0.81`, about 50.62 kW) and the adapter's `V_out` is 10 V above the booster's `V_in`.
- Vehicle and charger with continuous-only ratings (`dc_peak_mode: none`): eligible, modeled at the continuous ratings; `unknown` on either: `unverified`.
- 400 V line-to-line three-phase EVSE, 32 A single-phase cable, 11 kW onboard charger: about 7.4 kW (`400 / sqrt(3) * 32 / 1000`, not 12.8 kW); the same cable rated three-phase gives about 22.2 kW at the AC input, limited to 11 kW by the onboard charger.
- 400 V three-phase outlet, 32 A, `ac_outlet_power_max_kw` 11, 22 kW onboard charger: 11 kW.
- Same profile at `battery_soh` 1.0 and 0.8 with an SoH-dependent BMS map: different durations; absent SoH reports the SoH assumption and a widened range.
- A partial-window result appears in `unranked` with reason `partial_window` and never in a category's `results`; an AC candidate appears there as `scope_undecided`.
- Best-value winner with a 40 min baseline and a 35 min candidate: `minutes_saved` 5 and the baseline fields are returned.
- Offer in EUR with shipping in USD and no rate available: ineligible; with a rate, the total, the rate direction (`fx_from`, units of response currency per unit) and provenance are returned.
- Bypass condition at 500 V, station declared at 520 V whose loaded terminal voltage falls to 480 V: engagement is decided on 520 V once, whatever the solved current.
- Charger 400 A continuous, `full_performance_from_v` 300, `V_station` 400 V, `dc_power_continuous_kw` 150: current at most 375 A; a 230 V AC supply on the same row still follows the AC equations; null DC power cap and no `station_available_power_kw`: `unknown`.
- Native session 40 min, adapters 50 min and 45 min: fastest status `no_adapter_needed`; best value with no completed native session: `no_eligible_candidate` with an empty result list.
- Two retained sources, one giving `dc_booster_engagement: always` and one `bypassable`, for one vehicle: `unverified`, no ranked category.

Round 5 adds:

- Two stages, zero resistance, efficiency 0.9 each, station/adapter-output/battery voltages 400/600/800 V, 40 kW battery power, non-binding component limits: final output current 50 A, intermediate current about 74.07 A, station current about 123.46 A are feasible; the adapter's output current is not forced equal to the battery current.
- Booster input 400 V, battery 800 V, efficiency 0.9, 40 kW battery-terminal power, zero resistance between booster and battery (inter-stage or booster-input current about 111.11 A): an 80 A or a 42 kW inter-stage cable forces the current down until its limit holds; leaving 111.11 A in it because the battery current is 50 A fails.
- Battery 400 V, 100 A, cable 0.01 ohm, converter output resistance 0.09 ohm upstream of that cable: cable `V_e` 401 V and 40.1 kW, converter `V_out` 410 V and 41 kW; a cable cap of 40.5 kW passes.
- Booster with complete voltage, current, power and efficiency ratings and a null output resistance: `unknown`; for the case with output resistance 0.1 ohm, see the corrected booster regression in round 6.
- Charger with a complete envelope and a null `full_performance_from_v`: modeled from the envelope; null threshold and no envelope point at `V_station`: `unknown`, never the nameplate current.
- `dc_power_continuous_kw` 150, `dc_power_peak_kw` 200, `V_station` 400 V, peak current 500 A, `full_performance_from_v` 300: current at most 500 A inside the peak window and at most 375 A after the peak budget is used.
- A 5-minute peak budget is still available after 10 minutes spent within both continuous ratings; only time above a continuous rating consumes it (see round 6 for load between the continuous and peak ratings).
- AC cable 32 A continuous, 63 A peak, `peak_duration_s` 60: after 60 s of peak use it is modeled at 32 A (about 7.36 kW at 230 V single-phase, power factor 1), not 63 A (about 14.49 kW).
- AC request 230 V with an outlet declared 400 V line-to-line: the request value is used, the outlet value is recorded as superseded, and no field is mixed between the two.
- Two retained charger sources with different continuous-current ratings (or different voltage ranges): `unverified`, no ranked category.
- Offer in EUR with shipping in USD and a GBP `display_currency`: `fx_conversions` holds one record for EUR and one for USD; with no rate for either, the offer is ineligible.
- `peak_mode: rated` with a peak current and no `peak_duration_s`: modeled at the continuous rating with a widened range, not `unknown`.
- Native session 40 min, adapters 50 min and 45 min: both adapters appear in `unranked` as `not_faster_than_native_session` with `minutes_saved` -10 and -5; fastest, cheapest and best value all have status `no_adapter_needed`.

Round 6 adds:

- Component 250 A continuous / 500 A peak for 60 s, another limit holding the path at 400 A, all power caps nonbinding: the 400 A load consumes the peak budget and after 60 s of overload use the component is limited to 250 A. A load within both continuous ratings consumes none.
- Omitted `display_currency`, delivered totals EUR 100 and USD 110, supplied rate 0.8 EUR per USD, equal performance: the USD offer (EUR 88) wins cheapest regardless of enumeration order; the comparison currency is exposed as the response `currency`; with no rate for the USD offer it is excluded from price-based selection.
- Engaged booster, station 400 V, zero upstream resistance, battery 400 V at 100 A, output resistance 0.1 ohm, efficiency 0.9, input and output envelopes covering 400 V and 410 V, other limits nonbinding: feasible, `V_out` 410 V, `P_out` 41 kW, station input about 45.56 kW and 113.89 A. With the booster output maximum set to 400 V: no positive feasible current.
- Two stages at 400/600/800 V, 40 kW battery power, 0.9 per stage, zero resistance, 40 kW power cap on an inter-stage cable: the cable carries 600 V x 74.07 A = 44.44 kW and is ineligible; evaluating it at `V_station` (29.63 kW) and passing it is wrong.
- Two stages with efficiency 0.9 each, zero resistance, 40 kW at the battery: stage-1 input 49.38 kW (`40 / 0.81`), not `44.44 / 0.81`.
- Request supplies `ac_supply_voltage_v` 230 but no `ac_voltage_convention`, outlet declares 400 V line-to-line: AC power `unknown`, never 230 V with the outlet convention. With a request convention given, the request voltage and convention are used and the outlet pair is recorded as superseded.
- Vehicle booster bypassed inside the pack window, with stored `dc_booster_ratings` side resistances: the direct path stays eligible and `R_series_ohm` excludes them.
- Two retained sources with different peak powers (or different per-side power caps) for one accessory: `unverified`, no ranked category.
- Booster input resistance 0.1 ohm, no inter-stage cable, efficiencies 0.9, 40 kW at the battery, 100 A between the stages: station input about 50.49 kW, not 49.38 kW. Adapter output maximum 400 V, booster input minimum 400 V, 0.1 ohm at the joint, no cable: no positive feasible current; accepting 100 A because `R_mid` was read as 0 ohm fails.
- Adapter output range 550-650 V, adapter `V_out` 600 V, booster output 800 V at the battery, `R_down` 0: eligible; rejecting it because 800 V is outside the adapter's output range fails.

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
| FB-D10 | Is delivered price and availability evaluated at country level only, or at postcode/region granularity? (Interim: country level; `delivery_destination` is a country code.) | §4.4, §6.3, §8.2 | open (new, round 2) |
| FB-D11 | When no completed no-adapter session exists (e.g. connector mismatch), should best value stay empty, or use some other stated baseline such as a reference adapter? (Interim: empty, no baseline.) | §8.1 | open (new, round 3) |
