# Round-4 consolidation — CLAUDE

**Spec consolidated:** v1.4 (21 October 2026) → **v1.5** (21 October 2026; same day, version bumped).
**Consolidator:** CLAUDE.
**Date:** 2026-10-21.
**Reviews merged:** `CHATGPT.md` (1 finding: 1 major), `DEEPSEEK.md` (8: 1 major, 7 minor), `GROK.md` (5: 2 major, 3 minor). All three ended with `Result: complete`. GROK and DEEPSEEK also endorsed earlier round-4 findings without new ids; endorsements are not counted as findings.

## Reviewer provenance

Requested versus served model, as reported by the automation:

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified**: the provider reported no served model |

**Unverified reviewer: GROK.** All five GROK round-4 findings are "reasoning only"; I checked each against the spec text and re-did the arithmetic by hand (`800 * 110 / 1000 = 88 kW`, `0.9 * 0.9 = 0.81`, `(40 + 1) / 0.81 ≈ 50.62 kW`, `400 * 400 / 1000 = 160 kW`). The GROK source claims quoted in spec §5 (round 1) remain reviewer-reported and unvalidated (§11).

## Result

14 raw findings (1 + 8 + 5) deduplicate to **14 distinct items** (H1–H14; the three GROK/DEEPSEEK endorsements of CHATGPT-1 and of DEEPSEEK-1..8 are not findings): **14 accepted** into v1.5 (five with an adjustment, see §4), **0 rejected**, **0 deferred**, **0 new HUMAN decisions**; FB-D8, FB-D9, FB-D10 and FB-D11 stay open.

**Stop rule: not met.** Three `major` findings were raised on distinct points (CHATGPT-1, DEEPSEEK-1, GROK-1, GROK-2: four majors, three distinct items), so there is a **round 5** on v1.5. No finding is `blocking`.

---

## 1. Accepted and merged into v1.5

| # | Theme | Raised by | What v1.5 now says | v1.5 § |
|---|---|---|---|---|
| H1 | **Converter equations contradict the segment boundaries** (major) | CHATGPT-1 (endorsed by DEEPSEEK, GROK) | One equation system per converter stage: `I_out = I_batt`; the charge curve limits `P_battery_kW`; `P_out_kW = V_out*I_batt/1000`; station limits at `V_station`, `P_station_dc_kW` against `P_station_available`; `V_in = V_station - I_in_used*R_up`. §7.1 converting-path check and the operating-point policy use local terminals; the shared-range intersection applies only when `R_up` is zero | §7.1, §7.2, §9 |
| H2 | **`V_e` upstream of a converter uses the battery-side formula** (major) | GROK-1 | Per-element power caps evaluated per side: battery side `V_e = V_batt + I_batt*R_batt_to_e`, station side `V_e = V_in + I_in_used*R_in_to_e`; `V_e = V_station` fallback only without a converter; segment-total fallback bound recorded in `assumptions` | §7.2, §9 |
| H3 | **Two converter stages share one voltage and one efficiency** (major) | GROK-2 | "Converter stages": numbered stages, `V_out_k = V_in_(k+1) + I*R_mid_k`, inter-stage loss, efficiencies multiply; unknown `R_mid` or efficiency → `unknown` | §7.1, §7.2, §9 |
| H4 | **`peak_mode` exists for accessories only** (major) | DEEPSEEK-1 | `dc_peak_mode` (`none`/`rated`/`unknown`) on vehicle and charger profiles; fail-closed list reads "every applicable continuous and peak rating", `none` satisfies it; bare null never read as `none` | §4.3, §6.1, §6.2, §7.1, §7.2, §9 |
| H5 | **Single phase on a line-to-line supply** (minor) | DEEPSEEK-2 | Single-phase on `line_to_line` uses `U_ll/sqrt(3)`; phase count and voltage recorded | §7.2, §9 |
| H6 | **`ac_outlet_power_max_kw` never applied** (minor) | DEEPSEEK-3 | AC power limit = min(outlet cap when present, in-path caps, onboard charger); absent cap not unlimited, no value invented | §7.2, §9 |
| H7 | **SoH has no input or assumption rule** (minor) | DEEPSEEK-4 | Optional `battery_soh` request input; absent → treatment recorded in `assumptions`, range widened; no profile-level SoH; not an eligibility attribute | §6.1, §7.1, §7.2, §8.2, §9 |
| H8 | **No contract container for partial-window / AC-unranked results** (minor) | DEEPSEEK-5 | `unranked_unverified` replaced by `unranked` with `reason` (`unknown_attribute`, `partial_window`, `scope_undecided`, `insufficient_evidence`) and reached-SoC fields; category `results` hold only ranked candidates | §8.2, §9 |
| H9 | **Baseline object and `minutes_saved` undefined** (minor) | DEEPSEEK-6 | `baseline` object shape; `minutes_saved` in the required fields, null with no baseline; does not decide FB-D11 | §8.2, §9 |
| H10 | **FX storage, `vat_amount` currency, `fx_rate` direction** (minor) | DEEPSEEK-7 | `vat_amount` in offer currency; "no stored conversion" → "no exchange rate available at ranking time"; `fx_rate` = response-currency units per unit of `fx_from` | §4.4, §6.3, §8.2, §9 |
| H11 | **Booster bypass voltage undefined** (minor) | DEEPSEEK-8 | Decided once per session on the station's declared DC output voltage, not the loaded voltage; recorded; undeclared or straddling range → `unknown` | §7.1, §9 |
| H12 | **Charger kW cap has no column; `full_performance_from_v` node undefined** (minor) | GROK-3 | `dc_power_continuous_kw`/`dc_power_peak_kw` on `charger_profiles`; threshold compared with `V_station` only; current also limited by the power cap; null cap without `station_available_power_kw` → `unknown` | §6.2, §7.1, §9 |
| H13 | **Category `status` unmapped for empty cases** (minor) | GROK-4 | Defined `ranked`, `no_adapter_needed`, `no_eligible_candidate`, `insufficient_evidence` | §8.2, §9 |
| H14 | **New path-changing fields outside the §5 conflict list** (minor) | GROK-5 | List extended with `peak_mode`, `ac_phases`; vehicle/charger `dc_booster_engagement` and `dc_peak_mode` conflicts make dependent candidates `unverified` | §5, §9 |

---

## 2. HUMAN decisions

No `decisions.md` exists for this project, so no decision was applied.

## 3. Decisions for HUMAN — carried forward (single open list)

HUMAN is not answering during the automated loop. CLAUDE did not decide any of these. The same list is in spec §11.

| ID | Question | Spec § | Status |
|---|---|---|---|
| FB-D8 | Minimum evidence level for a product to qualify for a purchase recommendation | §7.1, §8.1, §9 | open; not re-raised in round 4 |
| FB-D9 | Do the three categories include AC cables or only DC adapters? | §8.1 | open. Interim: AC candidates are evaluated and listed in `unranked` as `scope_undecided` |
| FB-D10 | Is delivered price/availability evaluated at country level only, or at postcode/region granularity? | §4.4, §6.3, §8.2 | open. Interim: country level |
| FB-D11 | When no completed no-adapter session exists, should best value stay empty or use another stated baseline? | §8.1 | open. Interim: empty, no baseline (`no_eligible_candidate`) |

The ids are provisional tracking ids by CLAUDE, continuing the FuelBuddy `FB-D` series; they appear in no `decisions.md`.

---

## 4. Rejected / deferred / adjusted

**None rejected, none deferred.**

| Item | Disposition | Reason |
|---|---|---|
| CHATGPT-1 — converter equations | **Adjusted** | Adopted the single constraint system; the proposed "apply the same rule between stages" is carried by the H3 stage rule instead of a separate clause. The 41 kW and 410 V/400 V regressions are in §9 |
| DEEPSEEK-1 — `peak_mode` for vehicles/chargers | **Adjusted** | Chose the explicit column (`dc_peak_mode`) over "a null is read as `none`", for the same reason as round-3 G4: a bare null cannot distinguish `none` from `unknown` |
| DEEPSEEK-4 — SoH | **Adjusted** | Took the "not an eligibility attribute" branch of the proposal (assumption recorded, range widened); whether SoH should be safety-critical is not decided here and can be raised by a reviewer |
| DEEPSEEK-8 — bypass voltage | **Adjusted** | Picked the station's declared connector voltage, evaluated once per session, as a modeling convention; a straddling range is `unknown` (fail closed). Content of the operating-point policy itself is still not fixed (round-3 G2) |
| GROK-3 — charger kW cap | **Adjusted** | Accepted, but note the consequence: a charger row with no published DC power cap is `unknown` unless the request carries `station_available_power_kw`. Population of those columns is a phase-2 research task |

All other items were accepted as proposed.

---

## 5. Traceability

| Review finding | Item | Disposition |
|---|---|---|
| CHATGPT-1 | H1 | accepted (adjusted) |
| DEEPSEEK-1 | H4 | accepted (adjusted) |
| DEEPSEEK-2 | H5 | accepted |
| DEEPSEEK-3 | H6 | accepted |
| DEEPSEEK-4 | H7 | accepted (adjusted) |
| DEEPSEEK-5 | H8 | accepted |
| DEEPSEEK-6 | H9 | accepted |
| DEEPSEEK-7 | H10 | accepted |
| DEEPSEEK-8 | H11 | accepted (adjusted) |
| GROK-1 | H2 | accepted |
| GROK-2 | H3 | accepted |
| GROK-3 | H12 | accepted (adjusted) |
| GROK-4 | H13 | accepted |
| GROK-5 | H14 | accepted |

All 14 raw findings are accounted for. The endorsements in DEEPSEEK.md and GROK.md of CHATGPT-1 map to H1, and GROK's endorsement of DEEPSEEK-1..8 maps to H4–H11.

---

## 6. Notes for round 5

- Round 5 reviews v1.5. Check the rewritten converting-path system (§7.2) for circularity and unit consistency, especially the new `V_e` per-side rule, the chained-stage equations, and that the §7.1 local-terminal check agrees with the operating-point policy.
- Check the effect of `dc_peak_mode`, `dc_power_continuous_kw` and the null-power-cap rule on how many ordinary combinations still rank (fail-closed strictness).
- Check the §8.2 contract sketch: `unranked` replaces `unranked_unverified`; the `baseline` object; the `// object or null` comment in the sketch is illustrative, not JSON.
- `spec.md` is a symbolic link to `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md` in the same directory; edits were made to the target, so `spec.md` reads as v1.5.
