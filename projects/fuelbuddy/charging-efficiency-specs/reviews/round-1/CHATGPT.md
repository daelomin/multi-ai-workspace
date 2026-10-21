# CHATGPT review — round 1

Reviewed the local `spec.md` (v1.1), project README, repository review guideline and contribution instructions. This is an independent first-round review: the project has no `reviews/round-0/` or previous consolidation. The live schema and linked product specifications were not verified; the findings below concern the specification's internal rules. The minimum purchase-evidence level already listed in §11 remains a HUMAN decision and is not treated as a blocking or major finding.

### CHATGPT-1 · Apply losses before comparing limits at a common measurement boundary

- **Section:** §7.2, §9
- **Type:** error
- **Severity:** major
- **Finding:** The formula multiplies the entire minimum by `efficiency`, including `V_batt * I_vehicle_BMS` and `P_vehicle_charge_curve`, without defining their measurement boundaries. If those are battery-side limits, a hypothetical 50 kW battery-side curve with 100 kW available upstream and 90% path efficiency incorrectly produces 45 kW rather than 50 kW; upstream losses should not reduce an already battery-side cap a second time. This changes the core duration calculation and can penalize an accessory even when the vehicle remains the bottleneck, conflicting with the vehicle-limited ranking rule and no-adapter regression requirement.
- **Proposed change:** Replace the final blanket efficiency multiplier with: “Every power curve, current limit and efficiency has a declared measurement boundary. Transform each source/component constraint to the battery boundary, applying only the losses between that constraint and the battery, then take the minimum with battery-side BMS and vehicle-curve limits. Do not multiply battery-side limits by upstream path efficiency. Define whether modeled battery power is terminal or net stored-energy power and use the same convention for SoC integration and measured-test comparison.” Add a regression with a 50 kW battery-side limit, 100 kW upstream availability and 0.9 path efficiency; the battery-terminal result must be 50 kW. Preserve the existing no-adapter calculation under its documented boundary convention.
- **Evidence:** reasoning only; counterexample evaluates the §7.2 formula with explicitly hypothetical inputs.
- **Confidence:** high

### CHATGPT-2 · Distinguish voltage overlap from completion of the requested SoC window

- **Section:** §7.1–§7.3, §8.1–§8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** Preflight requires overlapping operating voltage, but overlap alone does not establish that a requested session can start or reach its target. For example, a hypothetical direct path with a 350–400 V station and a battery rising from 360 V to 420 V over the requested window passes an interval-overlap check but cannot complete that window; the spec does not define the resulting duration or ranking behavior when feasible power becomes zero.
- **Proposed change:** Add: “Evaluate feasible voltage/current/power throughout the requested SoC window using the applicable conversion architecture. If any required segment is infeasible or modeled net charging power is nonpositive, report the limiting condition and reachable SoC; do not return a finite full-window charging time or rank the candidate as completing that window. If feasibility cannot be established from available data, return an explicit unknown result rather than assuming overlap proves completion.” Add partial-voltage-overlap and zero-progress regression cases.
- **Evidence:** reasoning only; hypothetical interval counterexample against §7.1's overlap rule.
- **Confidence:** high

### CHATGPT-3 · Bind measured tests to immutable equipment and firmware configurations

- **Section:** §4.1–§4.3, §6.3, §7.3
- **Type:** gap
- **Severity:** minor
- **Finding:** Compatibility rows include firmware fields, but `accessory_test_results` has only equipment IDs and no hardware/firmware configuration snapshot. Since the referenced profiles contain mutable firmware/version fields, updating a profile can make an old test appear to support a different configuration, despite the requirement to distinguish configuration-specific measured results from extrapolation.
- **Proposed change:** Add: “Each test references immutable configuration versions or stores a snapshot of vehicle battery variant and software/BMS, accessory hardware/firmware, charger hardware/firmware, connector and installation limits as tested. Record unknown values explicitly. Updating current equipment profiles must not relabel historical tests; using a test for a different configuration must be marked as extrapolation.” The illustrative schema may implement this with version references or a structured `tested_configuration` field.
- **Evidence:** reasoning only; comparison of §6.3's test and compatibility fields with the configuration requirements in §4 and §7.3.
- **Confidence:** high

### CHATGPT-4 · Define when delivered prices are comparable enough to rank

- **Section:** §4.4, §6.3, §8.1–§8.2, §9
- **Type:** gap
- **Severity:** minor
- **Finding:** The spec requires delivered-price ranking and tests for expired offers, but defines neither an offer-validity rule nor behavior for unknown VAT/shipping, unavailable stock or different currencies. A dated base-price listing is therefore not sufficient to determine the cheapest delivered offer, and treating missing charges as zero could select the wrong winner.
- **Proposed change:** Add: “Price ranking uses a stated delivery country/postcode, a configurable offer-freshness policy and an identified eligible offer for each product. Unknown VAT or shipping makes the delivered total unknown, never zero; unknown totals, expired offers and offers unavailable to that destination cannot establish a cheapest/value winner. Compare totals in a common currency and report the exchange-rate source and timestamp when conversion is needed. Return null with a reason when a category has insufficient comparable data.” Add regression cases for unknown shipping, mixed currencies and stale offers. Keep policy thresholds configurable rather than inventing a fixed expiry period in this review.
- **Evidence:** reasoning only; the required offer fields and ranking criteria do not specify these comparison rules.
- **Confidence:** high

**Top 3**

1. CHATGPT-1: normalize power limits to a declared boundary before applying losses and integrating time.
2. CHATGPT-2: reject finite full-window predictions when a feasible session cannot reach the target SoC.
3. CHATGPT-3: preserve the exact configuration behind every measured test.

Result: complete
