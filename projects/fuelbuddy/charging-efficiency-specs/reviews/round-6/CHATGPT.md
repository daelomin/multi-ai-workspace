# CHATGPT review — round 6

Reviewed local `spec.md` v1.6 after reading every round-5 review and `CONSOLIDATION.md`, the project README and repository contribution/review instructions. This review checks internal consistency using hypothetical examples; external product claims and the live schema were not verified. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 are carried forward without new findings. Accepted round-5 changes are revisited only where the merged text remains wrong.

**Overall:** 0 blocking, 1 major, 2 minor.

### CHATGPT-1 · Consume the peak budget whenever continuous ratings are exceeded

- **Section:** §7.2 (Peak budget; direct, converting and AC paths), §9
- **Type:** error
- **Severity:** major
- **Finding:** J10 consumes the budget only while current or power is at its exact peak rating and explicitly excludes time below that peak. A component rated 250 A continuous and 500 A peak for 60 seconds, with another component limiting the path to 400 A and all power caps nonbinding, therefore carries 400 A indefinitely without consuming any budget. This permits sustained operation above the only documented continuous rating and can make an unsupported electrical operating condition eligible for purchase recommendations; the issue is the newly specified consumption rule, not the previously missing clock definition.
- **Proposed change:** Replace the default consumption rule with: “Unless a source supplies a different applicable duration/derating rule, consume one second of the component's peak budget per second whenever its modeled current exceeds its continuous-current rating or its modeled power exceeds its continuous-power rating. Operation within both continuous ratings consumes no budget. For converters, apply this rule to each side's own budget. Once exhausted, enforce all corresponding continuous limits for the remainder of the session; do not infer a longer permitted duration at an intermediate load.” Retain source-specific semantics and no regeneration. Update the below-peak regression to distinguish operation within continuous ratings from operation between continuous and peak ratings; add a 250/500 A, 60-second case capped elsewhere at 400 A that drops to at most 250 A after 60 seconds of overload use.
- **Evidence:** reasoning only; `250 < 400 < 500`, so the existing “at its peak rating” condition is never met, although the continuous-current limit is exceeded throughout. No vendor-specific thermal behavior is assumed; the proposed default avoids inventing unlimited intermediate-load endurance.
- **Confidence:** high

### CHATGPT-2 · Use one comparison currency across offers when display currency is absent

- **Section:** §4.4, §8.1, §8.2
- **Type:** gap
- **Severity:** minor
- **Finding:** J8 makes the response currency default to each offer's own currency when `display_currency` is omitted. That defines each delivered total but leaves cheapest, price-based tie-breaks and `delivered_price / minutes_saved` comparing amounts in different units, with no common comparison currency or conversion requirement between offers. For example, with a hypothetical available rate of 0.8 EUR per USD, delivered totals of EUR 100 and USD 110 should compare as EUR 100 versus EUR 88; both can currently remain unconverted because each offer's shipping is already in its own currency.
- **Proposed change:** Add: “All prices used together in a ranking or price tie-break are converted to one common comparison currency. Use `display_currency` when supplied; otherwise use a configured default currency independent of candidate enumeration order, and expose the selected comparison currency. Record conversions needed for comparison in `fx_conversions`; if a required rate is unavailable, exclude that offer from price-based selection.” Add a regression with omitted `display_currency`, EUR 100 and USD 110 delivered totals, the explicitly supplied hypothetical rate 0.8 EUR/USD, and equal performance: the USD offer wins cheapest regardless of enumeration order.
- **Evidence:** reasoning only; `110 * 0.8 = 88 EUR < 100 EUR`, whereas comparing the raw numbers gives the opposite order. J8 resolves multi-source conversion within an offer but its per-offer default does not resolve cross-offer comparison.
- **Confidence:** high

### CHATGPT-3 · Do not apply direct-path voltage headroom to an engaged booster regression

- **Section:** §9 (Round 5 booster-resistance regression), §7.2
- **Type:** error
- **Severity:** minor
- **Finding:** J15's new regression asserts that a booster with 0.1 ohm output resistance, a 400 V battery and a 400 V station maximum has no positive feasible current. That conclusion follows on a direct path, but a booster can raise its output terminal above the station voltage: the stated data alone do not establish infeasibility. The assertion contradicts the separate terminal-voltage equations and can fail a correct converter implementation.
- **Proposed change:** Keep the null-resistance test, but replace the second assertion with a fully specified booster case: “Engaged booster, station at 400 V, zero upstream resistance, battery 400 V at 100 A, output resistance 0.1 ohm, efficiency 0.9, input/output voltage envelopes covering 400/410 V respectively and all other limits nonbinding: feasible, with output 410 V / 41 kW and station input about 45.56 kW / 113.89 A.” For the intended no-positive-current counterpart, additionally constrain the booster output maximum to 400 V; then every positive current requires an output above its maximum.
- **Evidence:** reasoning only; `V_out = 400 + 100 * 0.1 = 410 V`, `P_out = 410 * 100 / 1000 = 41 kW`, `P_in = 41 / 0.9 = 45.555... kW`, and `I_in = 45.555... * 1000 / 400 = 113.888... A`. These satisfy §7.2 with the declared nonbinding envelopes; the station maximum alone does not bound converter output voltage.
- **Confidence:** high

**Top 3**

1. CHATGPT-1: consume peak budget throughout operation above continuous ratings, including below-peak loads.
2. CHATGPT-2: compare all offer prices in one common currency even without `display_currency`.
3. CHATGPT-3: correct the booster regression to respect separate input and output voltage limits.

Result: complete
