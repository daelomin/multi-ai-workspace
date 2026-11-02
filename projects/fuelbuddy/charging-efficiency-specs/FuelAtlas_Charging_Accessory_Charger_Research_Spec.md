# Fuel Atlas — Charging Equipment, Adapter and Battery Research Specification

**Version:** 1.1 (proposal)  
**Date:** 2026-10-21  
**Status:** Draft; live database/repository schema not yet inspected

## 1. Objective

Extend Fuel Atlas and FuelBuddy to research, normalize, verify and compare EV charging **cables, adapters, charger models and battery/vehicle limits**, and estimate charging performance for a specific vehicle and charging station. For a selected vehicle, return **three adapter recommendations**: fastest, cheapest eligible, and best value-to-performance, including current prices, purchase links, compatibility evidence and expected charging power/time.

**Principles:** reuse the existing vehicle profiles, charger profiles, charging curves, diagnostic rules and matching engine; preserve backward compatibility; distinguish manufacturer claims, calculations and field measurements; never present an unverified rating as a measured outcome.

## 2. Scope and terminology

- **Vehicle profile:** make/model/year/market/trim/battery variant, charge inlet, firmware and charging limits.
- **Battery profile:** voltage versus state of charge (SoC), current and thermal limits, usable capacity, SoH and preconditioning behavior.
- **Charger model:** manufacturer, model, hardware/firmware, connector configuration, voltage/current operating envelope and shared-power rules. A charger network/operator is a separate entity.
- **Charger installation:** physical unit with station ID, site/network, installed connector options, configured output and firmware. A model's headline power is not necessarily the installed unit's available power.
- **Cable:** conductive charging assembly with connector types, voltage/current/thermal ratings, cooling and certification.
- **Adapter:** passive electrical conversion or active protocol translation, with explicitly defined **direction** (e.g. CCS2 station -> CHAdeMO vehicle).
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
- AC/DC inlet types and protocol revisions; maximum AC/DC power and voltage/current; onboard boost or conversion constraints.
- Charge curve with SoC points, battery temperature, ambient temperature, preconditioning, charger context and source quality.

### 4.2 Charger models and installations (NEW REQUIRED DOMAIN)

- Manufacturer, canonical model name, model family, product URL, datasheet/manual URL.
- Hardware revision, firmware version/range, protocol support (e.g. CCS/ISO 15118/DIN SPEC, CHAdeMO), authentication requirements.
- Rated cabinet output kW, module configuration, **DC voltage min/max**, maximum continuous/peak current, peak duration, current-versus-voltage envelope, efficiency and derating.
- Per-connector limits and connector variant (CCS2, CHAdeMO, etc.), cable length/current/cooling, number of simultaneous outputs, power-sharing rules.
- Installation-specific limits: network/operator, station ID, site, firmware, configured power, local grid cap, connector availability, outages.
- Documented incompatibilities, handshake failures and known issues, linked to existing diagnostic knowledge.

### 4.3 Cables and adapters

- Canonical manufacturer/model/SKU, OEM/rebrand mapping, input/output connector, **direction**, AC/DC mode, active/passive conversion, protocol translation.
- Voltage min/max, continuous current, peak current, peak duration, continuous/advertised power, cable length, resistance/losses, cooling, thermal derating.
- Firmware/hardware versions, auxiliary power requirements, connector lock/interlock behavior, fault shutdown and certification evidence.
- Vehicle/charger/firmware compatibility status and evidence; reject unsupported safety-critical combinations.

### 4.4 Commercial data

- Seller, country, offer URL, SKU, currency, base price, VAT inclusion, shipping, total delivered price, stock, lead time, warranty and date checked.
- Maintain price history snapshots rather than overwriting historical prices.

## 5. Source-link policy (MANDATORY)

Every **named charger, cable or adapter model** in research output must have a clickable official manufacturer product page or official technical document where available. If neither exists, provide the exact retailer listing and label it accordingly. Each claim about a rating must point to its supporting source; do not use a generic manufacturer homepage as proof of a model-specific value.

Minimum provenance fields: `source_url`, `source_title`, `publisher`, `evidence_type`, `retrieved_at`, `published_at` (nullable), `applicable_model_revision`, `confidence`, `claim_field`. Track conflicting sources explicitly.

### Charger-model seed registry (research targets, NOT prevalidated specifications)

| Manufacturer | Charger model/family | Link | Research notes |
|---|---|---|---|
| Alpitronic | HYC150 | [HYC150 product brief (PDF)](https://esb-metelen.de/wp-content/uploads/HYC150_PRODUCT-BRIEF_V2-1_DE.pdf) | Verify revision, 150 kW configuration, voltage/current envelope and installed connector options |
| Alpitronic | HYC300 | [Official Hypercharger product family](https://www.alpitronic.it/en/hypercharger) | Find model-specific official datasheet and configuration |
| ABB E-mobility | Terra HP | [Official ABB E-mobility](https://e-mobility.abb.com/) | Resolve exact generation and power module, not just family name |
| ChargePoint | Express 250 | [Official ChargePoint](https://www.chargepoint.com/) | Resolve model-specific datasheet and configured power |
| Tesla | Supercharger V3 | [Official Tesla Supercharging](https://www.tesla.com/supercharger) | Validate non-Tesla access, site restrictions and vehicle voltage |

**Important:** The HYC150 is a **charger**, not a CCS2-to-CHAdeMO adapter. The cited LEAF e+ adapter test is a combination of vehicle + adapter + HYC150 configuration, not an adapter-only power guarantee. Seed links are research starting points; live link and specification validation remains required.

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

`battery_variant_id`, `battery_voltage_min_v`, `battery_voltage_max_v`, `battery_voltage_curve`, `dc_charge_current_continuous_a`, `dc_charge_current_peak_a`, `bms_charge_limit_map`, `battery_thermal_limit_map`, `dc_protocol_version`, `software_version`, `dc_booster_capability`.

### 6.2 Existing `charger_profiles` (optional additions)

`product_url`, `datasheet_url`, `hardware_revision`, `firmware_version`, `dc_voltage_min_v`, `dc_voltage_max_v`, `dc_current_continuous_a`, `dc_current_peak_a`, `peak_duration_s`, `voltage_current_envelope`, `connector_configurations`, `power_sharing_policy`, `thermal_derating`, `source_metadata`.

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
  min_voltage_v NUMERIC,
  max_voltage_v NUMERIC,
  continuous_current_a NUMERIC,
  peak_current_a NUMERIC,
  peak_duration_s NUMERIC,
  continuous_power_kw NUMERIC,
  advertised_power_kw NUMERIC,
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
  shipping_price NUMERIC,
  stock_status TEXT,
  warranty_months INTEGER,
  product_url TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE accessory_compatibility (
  id UUID PRIMARY KEY,
  accessory_id UUID NOT NULL REFERENCES charging_accessories(id),
  vehicle_profile_id UUID,
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
  charger_profile_id UUID,
  charger_installation_id UUID,
  start_soc NUMERIC,
  end_soc NUMERIC,
  battery_temp_c NUMERIC,
  ambient_temp_c NUMERIC,
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

Add FKs and indexes only after checking actual PK types, existing table names and data volume. For flexible source provenance, prefer reuse of an existing source/evidence table over duplication.

## 7. Charging simulation

### 7.1 Compatibility preflight

Before estimating power, verify adapter direction, physical connector, charging mode, overlapping operating voltage, protocol negotiation, safety interlocks and supported firmware/configurations. An unsafe or incompatible combination is **not eligible** for recommendations.

### 7.2 Instantaneous power

At battery voltage `V_batt(SoC, T)` calculate each relevant component's feasible current/power envelope. For a simplified direct DC path:

```text
I_allowed = min(
  I_vehicle_BMS(SoC, T, SoH),
  I_station(V_batt, connector, installation, t),
  I_cable(V_batt, T_cable, t),
  I_adapter(V_batt, T_adapter, t)
)
P_battery ≈ min(V_batt * I_allowed / 1000,
                P_station_available,
                P_vehicle_charge_curve(SoC, T, SoH)) * efficiency
```

For conversion/boost architectures, calculate input and output sides separately and include converter voltage/current limits and efficiency. Do **not** apply one common current across a converter with different input/output voltages.

Integrate over SoC using battery usable energy and the SoC-dependent effective power, while tracking accessory thermal state and time-limited peak ratings. Derating can depend on temperature, duration, charger power sharing, cable cooling and battery preconditioning. Missing curves should produce uncertainty ranges, not fictitious precision.

### 7.3 Outputs

- Theoretical electrical ceiling at specified battery voltage, advertised maximum, continuous/peak ratings.
- Estimated peak kW, sustained/average kW, and 10–80% time (or user-defined SoC window).
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
8. Rank and return exactly three **categories** when enough eligible candidates exist; the same product may win more than one category. Do not fabricate three distinct winners.

### 8.1 Ranking definitions

- **Fastest:** minimum modeled charging duration under comparable conditions, favoring verified compatibility and measured performance; report ties.
- **Cheapest:** lowest **delivered** price (VAT + shipping) among safe compatible options meeting a stated minimum performance/evidence threshold.
- **Best value:** optimize delivered price versus **usable** charging performance for that vehicle, including evidence quality and reliability; avoid rewarding headline kW the car cannot use.

Where charging times are equal, consider reliability, warranty, support and price. Cost per minute saved is meaningful only against a clearly stated baseline and if time is actually saved. For a vehicle already limited to 50 kW, a 250 A adapter may offer no benefit over a reliable lower-current model.

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
  "recommendations": {
    "fastest": null,
    "cheapest": null,
    "best_value": null
  },
  "required_per_recommendation": [
    "manufacturer", "model", "sku", "product_url",
    "compatibility_status", "charger_model_context",
    "continuous_current_a", "peak_current_a",
    "theoretical_max_kw", "expected_peak_kw",
    "expected_average_kw", "estimated_minutes",
    "performance_range", "price_total", "currency",
    "merchant", "purchase_url", "warranty_months",
    "performance_confidence", "evidence_urls",
    "assumptions", "recommendation_reason"
  ]
}
```

The above is a contract sketch: actual responses should populate recommendation objects and use `null` when values are unknown. Prices must be timestamped; model performance must be linked to test conditions and a specific charger model or installation.

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

Regression tests must cover voltage mismatch, peak-versus-continuous rating confusion, adapter reversal, charger power sharing, thermal derating, firmware incompatibility, duplicate OEM products, expired offers, missing data, and vehicle-limited cases.

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
- Decide minimum evidence level for a product to qualify for a purchase recommendation.
