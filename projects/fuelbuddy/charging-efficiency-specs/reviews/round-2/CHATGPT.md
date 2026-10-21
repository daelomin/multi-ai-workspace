# CHATGPT review — round 2

Reviewed the local `spec.md` v1.2 after reading all round-1 reviews and `CONSOLIDATION.md`, plus the project README and repository contribution/review instructions. Findings concern internal equations and contracts; numerical examples are hypothetical, and no live schema or external product claims were verified. Accepted round-1 changes are not reopened except where the merged rules remain incomplete or inconsistent. Open HUMAN decisions FB-D8 and FB-D9 are carried forward without new findings.

### CHATGPT-1 · Enforce component power caps in addition to voltage and current limits

- **Section:** §4.3, §6.1, §6.3, §7.2, §9
- **Type:** gap
- **Severity:** major
- **Finding:** The direct-DC calculation never applies `continuous_power_kw` from the accessory row, while the converting-path rule limits voltage, current and efficiency but does not explicitly enforce the converter's independent input/output power ratings. A hypothetical passthrough adapter rated for 400 V, 250 A and 60 kW continuous can therefore be modeled at 100 kW when the station and battery allow it; similarly, a converter's voltage/current bounds do not establish its continuous power capability. This permits estimates and rankings above a known component limit, despite the new fail-closed eligibility check establishing that ratings are known.
- **Proposed change:** Add: “At each time step, enforce every component's applicable continuous or time-limited peak power cap as well as its voltage/current envelope, at that component's declared measurement boundary. For a passthrough accessory, enforce `continuous_power_kw` after any documented peak interval; for a converter or vehicle booster, retain and enforce separate input/output power caps where specified. A power cap may be derived from a complete documented operating envelope, but must not be inferred solely by multiplying independent maximum voltage and current ratings.” Extend the converter/booster schema sketch accordingly. Add regressions for the 400 V / 250 A / 60 kW accessory (no more than 60 kW at its rated boundary) and a converter whose power cap binds before either current limit.
- **Evidence:** reasoning only; the hypothetical 100 kW follows directly from the §7.2 equation, which omits the stored 60 kW cap. This is a remaining enforcement gap after consolidation D1/D3, rather than a request to restore a blanket efficiency factor or a single converter envelope.
- **Confidence:** high

### CHATGPT-2 · Include resistive voltage drop in station operating-point feasibility

- **Section:** §7.1–§7.2, §9
- **Type:** error
- **Severity:** major
- **Finding:** The revised direct-DC path adds `I_batt² * R_series_ohm` to station power, but still checks station voltage limits and evaluates its current envelope at `V_batt`. With a hypothetical 400 V battery, 200 A and 0.05 Ω resistance downstream of the station boundary, the required station voltage is 410 V; a station capped at 400 V cannot supply that operating point even if its power limit passes. At a battery voltage equal to the station maximum and positive series resistance, no positive charging current is feasible, yet the current rules can report a completed window.
- **Proposed change:** Add: “For direct DC with known downstream series resistance, solve `V_station = V_batt + I_batt * R_series_ohm` together with the current and power constraints. Evaluate the station voltage range and current-versus-voltage envelope at `V_station`, and check each downstream component at its own terminal voltages using the resistance distribution where needed. Reduce current to satisfy all constraints; if no positive feasible current exists, apply §7.1's incomplete-window rule. If missing resistance or its distribution prevents establishing voltage feasibility, return unknown feasibility rather than certifying completion from battery voltage alone.” Add a regression for the 400 V maximum / 400 V battery / positive-resistance case and one where voltage headroom reduces current before the power cap does.
- **Evidence:** reasoning only; `200 A × 0.05 Ω = 10 V`, consistent with the resistive-loss model introduced by consolidation D1. Consolidation D2's window check remains incomplete at the actual station measurement boundary.
- **Confidence:** high

### CHATGPT-3 · Reconcile the fallback baseline with the global ranking gate

- **Section:** §8 step 8, §8.1–§8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** Step 8 permits an adapter to rank only when it improves time or cost over the no-adapter configuration, but §8.1 introduces a longest-eligible-candidate baseline when no no-adapter session exists. In the central case of a connector mismatch, the no-adapter duration is undefined; the text does not say whether the global gate is waived, so it can suppress otherwise valid fastest/cheapest results, including a sole eligible adapter. The fallback clause also applies “if no adapter is required,” even though a feasible native session then exists.
- **Proposed change:** Replace the gate with: “When a feasible no-adapter session exists, use it for the improvement comparison. When it is known to be incompatible, eligible adapters remain rankable in fastest and cheapest without a native-session improvement test; use the longest eligible completed session only as the best-value scoring baseline. An unknown native-session result is recorded as unknown and is not assigned an invented duration. If no candidate saves positive time against the best-value baseline, return an empty best-value result with an explicit reason.” Remove “If no adapter is required” from the fallback condition. Add connector-mismatch cases with one eligible adapter and with equal-duration adapters.
- **Evidence:** reasoning only; comparison of the two rules introduced under consolidation D5.
- **Confidence:** high

### CHATGPT-4 · Actually select or parameterize the battery-power convention

- **Section:** §7.2 measurement boundary and integration, §8.2, §9
- **Type:** inconsistency
- **Severity:** minor
- **Finding:** The measurement-boundary paragraph says the spec fixes one convention but leaves “terminal power, or net stored-energy power” unresolved. The equation calculates terminal power (`V_batt * I_batt`), while integration uses usable battery energy without defining how terminal energy becomes stored energy; two implementations can therefore derive different session times while claiming to follow the fixed convention. The upstream double-efficiency error is resolved, but the integration convention requested in consolidation D1 is still not stated.
- **Proposed change:** Add: “The direct-DC `P_battery_kW = V_batt * I_batt / 1000` quantity is battery-terminal power. SoC integration uses net stored-energy power, with any battery-internal charging loss or auxiliary draw between these boundaries explicitly modeled once. If the inherited calculator uses a simplified terminal-to-stored-energy mapping, retain and identify that mapping as an assumption. Every calculated curve and measured test declares its boundary; compare only matching boundaries or document the conversion.” Expose the convention/model version in the response and add a regression with a stated nonzero terminal-to-stored-energy loss, distinct from upstream path loss.
- **Evidence:** reasoning only; dimensional and boundary comparison of the revised equation with the integration paragraph. No new efficiency value is assumed.
- **Confidence:** high

**Top 3**

1. CHATGPT-1: enforce component power caps, including converter input/output caps, before estimating performance.
2. CHATGPT-2: solve station voltage and current at the actual operating point when including series resistance.
3. CHATGPT-3: keep connector-mismatch adapters rankable when a native session cannot exist.

Result: complete
