# DEEPSEEK review — round 1

Reviewed the local `spec.md` (v1.1), the project README and the repository contribution/loop rules. There is no `reviews/round-0/` and no previous consolidation for this project. The live schema and the linked product specifications were not verified; the findings below concern the specification's internal rules. The minimum purchase-evidence level listed in §11 is treated as an open HUMAN decision and is not raised as blocking or major.

### DEEPSEEK-1 · Conversion adapters need separate input and output envelopes end to end

- **Section:** §4.3, §6.3, §7.1–§7.2
- **Type:** gap
- **Severity:** major
- **Finding:** §7.2 correctly forbids applying one common current across a converter with different input/output voltages and the spec admits active adapters and boost/conversion architectures, but `charging_accessories` stores only one `min_voltage_v`/`max_voltage_v`/`continuous_current_a`/`peak_current_a` set and §7.1 checks a single voltage overlap. For a converter whose station-side input envelope differs from its vehicle-side output envelope (for example, a 500–950 V input and a 250–500 V output), an implementation cannot tell which side the rating belongs to and will either apply the station current at `V_batt` — the calculation §7.2 prohibits — or silently omit an input-side limit. Preflight has the same problem: the station↔adapter and adapter↔vehicle interfaces are two separate compatibility checks.
- **Proposed change:** Add explicit input- and output-side fields to `charging_accessories` (for example `input_voltage_min_v`, `input_voltage_max_v`, `input_current_continuous_a`, `input_current_peak_a`, `output_voltage_min_v`, `output_voltage_max_v`, `output_current_continuous_a`, `output_current_peak_a`, `conversion_topology`, `conversion_efficiency_curve`), or a typed JSONB envelope with the same contents; reserve the existing single-side fields for passive cables and pass-through adapters and state how they map. Define the conversion path as two coupled constraints with a declared operating point (output power = input power × efficiency) and require preflight to verify both envelopes. Add a regression with unequal input/output voltages and conversion efficiency below 1.
- **Evidence:** reasoning only; based on the spec's own definitions in §2/§4.3 and the prohibition in §7.2.
- **Confidence:** high

### DEEPSEEK-2 · Unknown safety-critical attributes must fail closed, not fall through to a recommendation

- **Section:** §6.3, §7.1, §8.1, §9
- **Type:** risk
- **Severity:** major
- **Finding:** The schema makes voltage, current and certification attributes nullable and permits compatibility status `unverified`, while §7.1 excludes only combinations that are "unsafe or incompatible" and §8.1 ranks "safe compatible options". A combination whose `max_voltage_v` or `continuous_current_a` is unknown, or whose only evidence is a seller claim, is not proven unsafe and is not marked incompatible, so an implementation can rank and recommend it; this can produce a purchase recommendation for an adapter whose voltage or current rating is unknown for the requested vehicle. The same gap applies to interlock, certification and protocol/firmware support.
- **Proposed change:** Add a fail-closed eligibility rule to §7.1 and §8.1: "A combination is eligible for a ranking category only when every safety-critical attribute needed for that combination is known from an acceptable source: adapter direction, connector compatibility, charging mode, an operating voltage range covering the entire requested window, continuous and peak current/power ratings, required certification, and required interlock/protocol support. If any is unknown, the combination is `unverified`: it may appear in a separate unranked list with the missing fields, but it must not fill fastest, cheapest or best-value, and unknown values are never treated as zero loss, unlimited, or compatible." Add a regression where an adapter with a null voltage rating is not recommended and is reported with the missing field.
- **Evidence:** reasoning only; the nullable columns and `status` enum in §6.3, read against §7.1/§8.1.
- **Confidence:** high

### DEEPSEEK-3 · "Best value" has no defined objective function, baseline or acceptance test

- **Section:** §8.1–§8.2, §9 phase 6
- **Type:** gap
- **Severity:** major
- **Finding:** "Best value: optimize delivered price versus usable charging performance ... including evidence quality and reliability" defines neither the objective, its units, the trade-off weights, nor the baseline, so two implementations can return different winners for identical inputs; §8.1 itself says cost per minute saved needs a "clearly stated baseline" but never states one. Phase 6's acceptance criterion ("Three categories with price, realistic power/time and evidence") therefore cannot determine whether the value winner is correct, and the mandatory category is not reproducible.
- **Proposed change:** Replace the definition with a deterministic rule: after the eligibility filter, require an evidence floor and a comparable offer, then either choose the lowest delivered price among options whose modeled session time is within a configurable tolerance of the fastest eligible option, or maximize a stated function such as minutes saved versus the named baseline divided by delivered price, with a defined zero-saved case. Report `ranking_method`, the baseline, the tolerance/weights and the offer used in the response, and make the thresholds configurable rather than fixed here. Add a worked regression in which headline kW and modeled usable kW rank two adapters differently.
- **Evidence:** reasoning only; the definition is qualitative while §9 requires an accepted category.
- **Confidence:** high

### DEEPSEEK-4 · The no-adapter baseline and empty-category meaning are not representable

- **Section:** §1, §8, §8.2
- **Type:** gap
- **Severity:** minor
- **Finding:** The objective asks for three adapter recommendations for every selected vehicle, but when the vehicle already matches the station connector the best option may be no adapter at all; §8.1 warns that an adapter can save no time, yet the contract gives each category only a product or `null`. "No adapter needed", "no eligible candidate", "insufficient evidence" and "unknown" are therefore indistinguishable, which can lead to recommending an unnecessary purchase and makes the required cost-per-minute comparison impossible to interpret.
- **Proposed change:** Define the no-adapter configuration as a first-class baseline and allow a per-category result object such as `{"status": "ranked" | "no_adapter_needed" | "no_eligible_candidate" | "insufficient_evidence", "product": {...} | null, "reason": "..."}`. State that an adapter is ranked only when it improves the modeled time or cost over the baseline under the stated conditions, and add regressions for a CCS2 vehicle at a CCS2 station and for a vehicle-limited case where a higher-current adapter changes nothing.
- **Evidence:** reasoning only; §8.2 has no status or reason per category.
- **Confidence:** high

### DEEPSEEK-5 · AC charging is in the catalog but has no performance model

- **Section:** §1, §4.3, §6.3, §7.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** `charging_accessories.charging_mode` explicitly admits AC and §4.3 requires AC/DC mode and AC cable ratings, but §7.2 defines only a direct-DC path and a conversion/boost path; there is no onboard-charger limit, phase count, AC voltage/frequency, control-pilot current, AC cable rating or AC session-time model. An AC cable can therefore enter the accessory catalog and the three recommendation categories without any way to estimate its performance.
- **Proposed change:** Either state that §7 performance estimation is DC-only and define an explicit `unsupported`/`dc_only` result for AC candidates (while still evaluating AC compatibility), or add an AC path with the onboard charger as a component and the grid/phase/current inputs, with acceptance tests. Also state whether the three recommendation categories include AC cables or only DC adapters.
- **Evidence:** reasoning only; comparison of §6.3's `charging_mode` and §7.2's scope.
- **Confidence:** high

### DEEPSEEK-6 · Time-varying simulation inputs are missing for battery temperature and shared power

- **Section:** §7.2, §8.2, §4.2
- **Type:** gap
- **Severity:** minor
- **Finding:** §7.2 evaluates current limits with a battery temperature `T` and a station time `t` and says derating depends on temperature and charger power sharing, but the request supplies one `battery_temperature_c` and no ambient/preconditioning trajectory, time, or simultaneous-session state. An implementation must therefore hold both constant, which is optimistic over a 10–80% session and for a shared cabinet, and the uncertainty range cannot reflect the missing dynamics.
- **Proposed change:** Either add optional inputs (`ambient_temperature_c`, `preconditioning_state`, an optional battery-temperature trace, `station_available_power_kw` or concurrent-session count/time) and define how they enter the limits, or state the constant-temperature/full-power assumption explicitly and widen the reported range, recording it in `assumptions`. Add regressions for a shared cabinet and a cold or warm pack, and require test results to record the temperatures and sharing state.
- **Evidence:** reasoning only; §7.2's `T`/`t` dependencies are not present in §8.2's inputs.
- **Confidence:** high

### DEEPSEEK-7 · Ranking ties cannot be represented by the response contract

- **Section:** §8.1–§8.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §8.1 requires the fastest category to "report ties", but §8.2 maps each category to a single recommendation object or `null`; a tie must therefore be truncated to one product or serialized in an unspecified order. The same problem applies when two offers have the same delivered price for the cheapest category.
- **Proposed change:** Make each category an ordered list of recommendations, or add `ties`/`tie_group_id` to the recommendation object, and define whether tied products occupy one category and how their order is chosen. Add a regression with two eligible adapters producing equal modeled duration and equal delivered price.
- **Evidence:** reasoning only; direct comparison of §8.1 and §8.2.
- **Confidence:** high

### DEEPSEEK-8 · Vehicle profile and battery variant identity are ambiguous in compatibility and test records

- **Section:** §2, §6.1, §6.3, §8.2
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** §2 defines a vehicle profile as including the battery variant, while §6.1 adds a separate `battery_variant_id` and §8.2 requires both identifiers; `accessory_compatibility` and `accessory_test_results` reference only `vehicle_profile_id`. If a profile can cover more than one battery variant, evidence from one variant (different pack voltage, maximum DC power or charge curve) can be matched to another; if it cannot, the extra identifier is redundant and its relationship to the profile is undefined.
- **Proposed change:** State the identity rule explicitly: a `vehicle_profile_id` identifies exactly one make/model/year/market/trim/battery variant/software configuration, or, if the existing table is model-level, add `battery_variant_id` to `accessory_compatibility` and `accessory_test_results` and make it part of the matching key. Add a regression with two battery variants of the same model that have different charge curves and maximum DC power.
- **Evidence:** reasoning only; the identifiers appear with different grain in §2, §6.1 and §8.2.
- **Confidence:** high

**Top 3**

1. DEEPSEEK-1: model input and output electrical envelopes separately for conversion adapters.
2. DEEPSEEK-2: fail closed when safety-critical attributes are unknown.
3. DEEPSEEK-3: define the best-value objective, baseline and a testable acceptance case.

Result: complete
