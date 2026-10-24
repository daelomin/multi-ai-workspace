# Changelog

## 2026-10-24
**Agent:** DEEPSEEK
**Files:** `projects/jarvis/JarvisBot/reviews/round-1/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local JarvisBot spec v0.1 independently for round 1. Recorded 0 blocking, 5 major and 3 minor findings: the file ends inside an unclosed Mermaid fence and has no requirements beyond §6; Phase 0 and the path-selection decision have no scope, evidence or exit criteria; the recommended shim and reconstruction paths conflict with the §4 non-goals and have no legal/ToS gate; there is no security baseline for shell, network egress, untrusted content or remote approval; “local-first” has no enforceable offline contract; and the model-adapter, multi-agent isolation and memory/privacy requirements are undefined.
**Remaining:** CLAUDE consolidates round 1. Architecture, licensing, phase GO/NO-GO and path selection remain HUMAN decisions; this review proposes gates and requirements without deciding them.
**Verification:** Read the local spec, project README, `CONTRIBUTING.md`, `MASTER.md`, `TODO.md` and recent changelog entries (MASTER/TODO concern a different project). Findings use internal reasoning only; no candidate tool, URL, licence or capability was verified externally. Review includes the required fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-24
**Agent:** CHATGPT
**Files:** `projects/jarvis/JarvisBot/reviews/round-1/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local JarvisBot spec v0.1 independently for round 1. Recorded 0 blocking, 2 major and 1 minor findings: the document ends inside its architecture diagram without a defined Phase 0 scope or exit criteria; approval and sandbox enforcement boundaries are unspecified; candidate tooling claims lack traceable provenance.
**Remaining:** CLAUDE consolidates round 1. Architecture, licensing and phase GO/NO-GO remain HUMAN decisions; this review proposes requirements without deciding them.
**Verification:** Read the local spec, project README, repository review guidelines, MASTER, TODO and recent changelog entries. Findings use internal reasoning only; no external tooling claims were verified. Review includes required fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/specs_review_loop.py`, `generic/tests/test_specs_review_loop.py`, `CHANGELOG.md`
**Change:** The consolidation step now accepts a symlinked `spec.md`. In `charging-efficiency-specs`, `spec.md` links to `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md`; the consolidator's edit through the link showed up in git as a change to the target, and the post-step check ("CLAUDE changed files outside the consolidation") aborted round 1 after the model had finished, leaving the consolidation uncommitted. New helper `spec_rels()` adds the link's target to the allowed and committed paths, in both the normal and the resume-at-commit paths.
**Verification:** 68 mocked tests pass (2 new, one with a real git repo and a symlinked spec). Round 1 of the efficiency loop not yet resumed: its consolidation (spec v1.2, README Round 2, CONSOLIDATION.md) is still uncommitted in its worktree until the loop is rerun.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/specs_review_loop.py`, `generic/loop_monitor.py`, `generic/loop_wizard.html`, `generic/tests/test_specs_review_loop.py`, `generic/tests/test_loop_monitor.py`, `generic/REVIEW_LOOP_GUIDELINE.md`, `CHANGELOG.md`
**Change:** Cost per step. The engine records `cost_usd` and `cost_basis` in each step's timing file: DeepSeek from its token counts at DeepSeek's list prices (peak/off-peak by Beijing time, CNY converted at `CNY_USD`, default 0.14), ChatGPT from Codex's estimate, Claude from Claude Code's `total_cost_usd`, Grok flagged "not reported by Cursor". The Jarvis nodes carry cost in the name tooltip and metadata, the chips show it, and each loop card shows the round total with unreported steps listed. Claude Code's own cost for DeepSeek runs is ignored (wrong price table: flash read higher than pro).
**Verification:** 66 mocked tests pass (5 new: peak window, price maths, unknown model, zero cost, round total). The function on the real round-3/4 DeepSeek logs gives $0.18 (priced at peak: it started 3 s before the window closed) and $0.03. Not yet seen live on a running round.
**Remaining:** DeepSeek prices come from the Chinese pricing page as read by a subagent (not re-checked by hand) and the CNY rate is an assumption.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/loop_monitor.py`, `generic/loop_wizard.py`, `generic/loop_wizard.html`, `generic/run_review_loop.sh`, `generic/specs_review_loop.py`, `generic/tests/test_worktrees.py` (new), `generic/tests/test_loop_monitor.py`, `generic/tests/test_specs_review_loop.py`, `generic/REVIEW_LOOP_GUIDELINE.md`, `.gitattributes` (new), `CHANGELOG.md`
**Change:** (1) One git worktree per loop, so several loops run in parallel: new loops are created in `~/GIT/multi-ai-workspace.loops/<id>/` on their own branch; `loops.json` records `branch` and `worktree`; the launcher takes `LOOP_WORKTREE`, runs the engine (from the main checkout) with `--project <worktree>/<project>` and holds a lock per git-dir (so two loops in one worktree are refused, loops in different worktrees are not); the monitor, page and Jarvis nodes read logs and files from the worktree and show branch and path; chaining and the page cap parallel loops at `LOOP_MAX_PARALLEL` (3); the page can give a legacy loop its own worktree. (2) `.gitattributes`: `CHANGELOG.md merge=union` so parallel loop branches merge. (3) Version line: the engine now reads `**Version:** 1.1 (proposal)` and similar (it showed `v?` and would have failed the consolidation's version-bump check). (4) The monitor shows a loop whose README says "the review converged" as complete. (5) Branches untangled after two loops shared one checkout: `agent/loop/fuelbuddy-review` fast-forwarded to `4744c75` and pushed.
**Verification:** 61 mocked tests pass, 11 of them with real git worktrees. Live: `charging-efficiency-specs` was given a worktree and its preflight passed inside it (logs in the worktree, `spec v1.1`, Jarvis shows preflight nodes with branch and worktree). Two real review rounds in parallel not yet run.
**Remaining:** HUMAN commits the uncommitted tooling files in the main checkout. The stray local branch `list` (at `a769a5d`) is not mine; delete it if unwanted.
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-4/CONSOLIDATION.md`, `projects/fuelbuddy/charging-efficiency-specs/spec.md` (symlink; edited via `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md`), `projects/fuelbuddy/charging-efficiency-specs/README.md`, `CHANGELOG.md`
**Change:** Consolidated charging-efficiency-specs review round 4 (CHATGPT 1, DEEPSEEK 8, GROK 5 findings; 4 major, 10 minor; 14 findings merged into 14 items, all accepted, five with an adjustment) and updated the spec v1.4 → v1.5: single consistent converter equation system with local terminal voltages; per-side `V_e` for passthrough power caps around a converter; chained converter stages with inter-stage loss and multiplied efficiencies; `dc_peak_mode` on vehicles and chargers; single-phase voltage on a line-to-line supply; `ac_outlet_power_max_kw` applied; `battery_soh` input; `unranked` container and `baseline`/`minutes_saved` in the §8.2 contract; FX direction and `vat_amount` currency; booster bypass decided on the declared station voltage; charger DC power-cap columns and `full_performance_from_v` node; category status mapping; wider §5 conflict list; new regressions. README now points at Round 5 reviewing v1.5.
**Remaining:** Stop rule not met (four majors on three distinct items), so round 5 follows. Open HUMAN decisions carried forward unchanged: FB-D8, FB-D9, FB-D10, FB-D11; HUMAN was not asked and CLAUDE decided none. GROK's served model was unverified.
**Verification:** No external source re-fetched; all round-4 findings were reasoning-only and were checked against the spec text, with the quoted arithmetic recomputed by hand. No git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-4/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.4 for round 4 after all round-3 reviews and consolidation, plus the round-4 CHATGPT and DEEPSEEK reviews. Recorded 0 blocking, 2 major and 3 minor findings: passthrough `V_e` on a converting path still uses the battery-side formula, so a buck-path cable power cap is understated; two converter stages are forced to one intermediate voltage and one efficiency; the charger kW cap has no column and `full_performance_from_v` has no voltage node; category `status` is unmapped for the empty-candidate cases; `peak_mode`, `ac_phases` and `dc_booster_engagement` are outside the §5 conflict list.
**Remaining:** CLAUDE consolidates round 4. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 were not reopened. Endorsed round-4 CHATGPT-1 and DEEPSEEK-1 through DEEPSEEK-8 without new ids. GROK-1 is the upstream `V_e` formula; GROK-2 is the two-stage join.
**Verification:** Internal reasoning against the local spec and round-3 dispositions. Scores `800 * 110 / 1000 = 88 kW`, `400 * 110 / 1000 = 44 kW`, `0.9 * 0.9 = 0.81` and `(40 + 1) / 0.81 ≈ 50.62 kW` were computed in the review. The 150 kW and 400 A figures are the ones already quoted in spec §5 and were not re-fetched. The 230 V and 7.4 kW figures are the spec's own §7.2 illustration. No external source was re-fetched. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-4/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.4 for round 4 after all round-3 reviews and consolidation, plus the round-4 CHATGPT review. Recorded 0 blocking, 1 major and 7 minor findings: `peak_mode` was added for accessories only, so a continuous-only vehicle or charger fails the §7.1 peak-rating gate; a single-phase path on a line-to-line supply has no line-to-neutral voltage rule; `ac_outlet_power_max_kw` is stored but never applied; SoH is an argument of the BMS limit with no field, request input or assumption rule; the §8.2 contract has no container for partial-window or AC-unranked results; the best-value baseline object and `minutes_saved` are undefined; mixed-currency conversion has no storage, `vat_amount` has no currency and `fx_rate` has no direction; and the booster bypass condition is evaluated on an undefined current-dependent station-side voltage.
**Remaining:** CLAUDE consolidates round 4. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 were not reopened; the round-4 CHATGPT-1 finding was endorsed and not repeated; DEEPSEEK-5 and DEEPSEEK-6 only note contract representations needed under whatever FB-D9/FB-D11 settle on.
**Verification:** Internal reasoning against the local spec and round-3 dispositions; numerical examples are hypothetical (`400 × 32 / 1000 = 12.8 kW`, `(400/√3) × 32 / 1000 ≈ 7.39 kW`, `√3 × 400 × 32 / 1000 ≈ 22.17 kW`); no external source, product claim or live schema was verified. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-4/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.4 for round 4 after all round-3 reviews and consolidation. Recorded 0 blocking, 1 major and 0 minor findings: the retained converter equation block and shared-voltage preflight/operating-point rules contradict the newly added segment boundaries, producing inconsistent converter output power and rejecting feasible separated terminal voltages.
**Remaining:** CLAUDE consolidates round 4. Open HUMAN decisions FB-D8, FB-D9, FB-D10 and FB-D11 were not reopened; accepted changes were revisited only where merged text remains inconsistent.
**Verification:** Internal reasoning against the local spec and round-3 dispositions; checked hypothetical 40 kW battery / 41 kW converter-output and 410 V station / 400 V converter-input examples. No external product claims or live schema verified. Review includes required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-3/CONSOLIDATION.md`, `projects/fuelbuddy/charging-efficiency-specs/spec.md` (symlink; edited via `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md`), `projects/fuelbuddy/charging-efficiency-specs/README.md`, `CHANGELOG.md`
**Change:** Consolidated charging-efficiency-specs review round 3 (CHATGPT 2, DEEPSEEK 9, GROK 6 findings; 4 major, 13 minor; 17 raw findings merged into 16 items, all accepted, nine with an adjustment) and updated the spec v1.3 → v1.4: segment voltages, losses and passthrough power caps around a converter; converter operating-point policy; `V_e` convention; explicit `peak_mode`; accessory `ac_phases` and AC input fields (no default voltage or power factor); per-destination shipping/VAT table `accessory_offer_destinations`; price timestamp and FX fields in the §8.2 contract; wider §5 conflict list; test `power_convention`; charger protocol and accessory interlock fields; best value has no fallback baseline; booster engagement rule; native-session gate is "strictly faster"; envelope rule for all paths; session count does not set available power; new regressions. README now points at Round 4 reviewing v1.4.
**Remaining:** Stop rule not met (four majors), so round 4 follows. Open HUMAN decisions carried forward: FB-D8, FB-D9, FB-D10 and new FB-D11 (best-value baseline when no completed no-adapter session exists; interim: empty); ids are provisional and HUMAN was not asked. GROK's served model was unverified.
**Verification:** No external source re-fetched; all round-3 findings were reasoning-only and were checked against the spec text. No git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-3/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.3 for round 3 after reading all round-2 reviews and `CONSOLIDATION.md`, plus the round-3 CHATGPT and DEEPSEEK reviews. Recorded 0 blocking, 2 major and 4 minor findings: the best-value fallback baseline is the slowest eligible adapter, so adding a slower adapter changes the winner; a vehicle booster has no in-circuit rule and can reject a station the pack can take directly; "improves cost" is undefined against an unpriced native session; the nameplate-current prohibition sits only on the AC bullet; AC converter input power is not defined as `P_ac` and supply voltage has no field; a concurrent session count does not change available station power.
**Remaining:** CLAUDE consolidates round 3. Open HUMAN decisions FB-D8, FB-D9 and FB-D10 were not reopened. Endorsed round-3 CHATGPT-1, CHATGPT-2 and DEEPSEEK-1 through DEEPSEEK-9. GROK-1 is the E6 fallback baseline; GROK-2 is booster engagement.
**Verification:** Internal reasoning against the local spec and round-2 dispositions. Scores `80/15`, `20/15` and `80/30` were computed in the review. The 230 V and 400 V figures are the spec's own §7.2 illustration. No external source was re-fetched. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-3/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.3 for round 3 after reading all round-2 reviews and `CONSOLIDATION.md` plus the round-3 CHATGPT review. Recorded 0 blocking, 1 major and 8 minor findings: the voltage-converting path enforces only the converter's power caps, so a 400 V / 250 A / 60 kW passthrough element upstream or downstream of a converter can be modeled at 100 kW; the direct-path per-element check uses an undefined `V_e`; continuous-only accessories have no null-peak-mode rule and may fail closed; the AC power rule uses the supply's phase count while cables/adapters store none; one offer row cannot carry per-destination shipping/VAT for `ships_to`; the §8.2 contract cannot report the price timestamp or exchange-rate provenance §4.4 requires; the §5 conflict list omits minimum voltage and series resistance; stored tests have no measurement-boundary field; and charger protocol/authentication plus accessory interlock behavior have no schema fields.
**Remaining:** CLAUDE consolidates round 3. Open HUMAN decisions FB-D8, FB-D9 and FB-D10 were not reopened; CHATGPT's round-3 findings were endorsed and not repeated. DEEPSEEK-1 is the unconverted-element power-cap gap left by E1; DEEPSEEK-2 is the direct-path counterpart of CHATGPT-1.
**Verification:** Internal reasoning against the local spec and round-2 dispositions; numerical examples are hypothetical (250 A × 400 V = 100 kW; 230 V × 32 A ≈ 7.4 kW; √3 × 400 V × 32 A ≈ 22.2 kW); no external source, product claim or live schema was verified. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-3/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.3 for round 3 after reading all round-2 reviews and consolidation. Recorded 0 blocking, 1 major and 1 minor finding: converting paths still identify station/converter and converter/battery terminal voltages despite intervening series losses; converter operating-point and ranking-duration selection lack a reproducible policy.
**Remaining:** CLAUDE consolidates round 3. Open HUMAN decisions FB-D8, FB-D9 and FB-D10 were not reopened; accepted changes were revisited only for remaining gaps in the merged rules.
**Verification:** Internal reasoning against the local spec and round-2 dispositions, with hypothetical electrical counterexamples; no external product claims or live schema verified. Review includes required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-2/CONSOLIDATION.md`, `projects/fuelbuddy/charging-efficiency-specs/spec.md` (symlink; edited via `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md`), `projects/fuelbuddy/charging-efficiency-specs/README.md`, `CHANGELOG.md`
**Change:** Consolidated charging-efficiency-specs review round 2 (CHATGPT 4, DEEPSEEK 8, GROK 6 findings; 5 major, 13 minor; 18 raw findings merged into 14 items, all accepted, seven with an adjustment) and updated the spec v1.2 → v1.3: component power caps; station voltage including the `I·R` drop; per-interface voltage-window rule for direct, converting and AC paths; `I_in`/`I_out` equations for converters and boosters; only completed windows rank; no-adapter gate and best-value score (`price / minutes_saved`, positive saves only); terminal vs stored-energy power convention; omitted-term and summed-resistance rules; AC power equations and onboard-charger ratings; peak durations per side and for the vehicle; §8.2 request/response fields; wider §5 conflict list; country-level delivered price; new regressions. README now points at Round 3 reviewing v1.3.
**Remaining:** Stop rule not met (five majors), so round 3 follows. Open HUMAN decisions carried forward: FB-D8 (minimum purchase-evidence level), FB-D9 (AC cables in the three categories?), FB-D10 (new: country vs postcode granularity); ids are provisional. GROK's served model was unverified.
**Verification:** No external source re-fetched; all round-2 findings were reasoning-only and were checked against the spec text. No git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-2/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.2 for round 2 after reading all round-1 reviews and `CONSOLIDATION.md`, plus the round-2 CHATGPT and DEEPSEEK reviews. Recorded 0 blocking, 2 major and 4 minor findings: a partial SoC window can win Fastest because ranking minimizes duration; a passthrough adapter upstream of a booster has no input-current equation; best value is unordered for a negative time save and an undefined comparable price; the no-adapter baseline leaves `I_adapter` and `R_series_ohm` undefined; the AC path has no power equation; the vehicle peak current has no duration column.
**Remaining:** CLAUDE consolidates round 2. Open HUMAN decisions FB-D8 and FB-D9 were not reopened. Endorsed round-2 CHATGPT-1 through CHATGPT-4 and DEEPSEEK-1 through DEEPSEEK-8. GROK-1 is the ranking sort; GROK-2 is the converting-path current split.
**Verification:** Internal reasoning against the local spec and round-1 dispositions. The 125 A figure is the spec's own §7.3 example; 230 × 32 and √3 × 400 × 32 were computed in the review and no external source was re-fetched. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-2/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.2 for round 2 after reading all round-1 reviews and `CONSOLIDATION.md` and the round-2 CHATGPT review. Recorded 0 blocking, 1 major and 7 minor findings: the SoC-window voltage rule is undefined on a converting adapter or vehicle booster, where the station-side voltage is not `V_batt`, and on the AC path; the §8.2 request cannot carry the §7.2 station-power, sharing and battery-temperature inputs; the §8.2 contract omits the §7.3 limiting condition, dominant bottleneck, model configuration and timestamp and does not map §7.1's `unknown`; Fastest retains an unweighted evidence preference; a converting adapter has one peak duration for two current limits; the onboard charger is used as a converter without efficiency or output ratings; the §5 conflict list omits topology, power, peak and efficiency conflicts; delivered price is described per postcode but stored and requested per country.
**Remaining:** CLAUDE consolidates round 2. Open HUMAN decisions FB-D8 and FB-D9 were not reopened. Endorsed round-2 CHATGPT-1, CHATGPT-2 and CHATGPT-3; DEEPSEEK-1 is distinct from CHATGPT-2 (converting/AC station-side voltage versus direct-path resistive drop).
**Verification:** Internal reasoning against the local spec and round-1 dispositions; numerical examples are hypothetical and no external source or product claim was re-fetched. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-2/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.2 for round 2 after all round-1 reviews and consolidation. Recorded 0 blocking, 2 major and 2 minor findings: component power caps are not enforced by the power equations; resistive losses require a station-voltage feasibility check at the actual operating point; the no-adapter ranking gate conflicts with the fallback baseline; the battery-terminal versus stored-energy convention remains unresolved.
**Remaining:** CLAUDE consolidates round 2. Open HUMAN decisions FB-D8 and FB-D9 were not reopened; accepted findings were revisited only where merged rules remain incorrect or incomplete.
**Verification:** Internal reasoning against the local spec and round-1 dispositions; examples are hypothetical and external product claims were not re-verified. Review includes required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-1/CONSOLIDATION.md`, `projects/fuelbuddy/charging-efficiency-specs/spec.md` (symlink; edited via `FuelAtlas_Charging_Accessory_Charger_Research_Spec.md`), `projects/fuelbuddy/charging-efficiency-specs/README.md`, `CHANGELOG.md`
**Change:** Consolidated charging-efficiency-specs review round 1 (CHATGPT 4, DEEPSEEK 8, GROK 8 findings; 7 major, 13 minor; 20 raw findings merged into 10 items, all accepted, four with an adjustment) and updated the spec v1.1 → v1.2: battery-boundary power model without double efficiency and with peak-duration limits; SoC-window feasibility and `window_completed`; `passthrough` vs `voltage_conversion` accessory topology with input/output envelopes; fail-closed eligibility and conflict rule; deterministic best-value, no-adapter baseline, per-category status and ties; AC path; time-varying inputs; battery-variant identity; configuration-bound tests; delivered-price and offer-validity rules; new regressions. README now points at Round 2 reviewing v1.2.
**Remaining:** Stop rule not met (majors raised), so round 2 follows. Open HUMAN decisions carried forward: FB-D8 (minimum purchase-evidence level), FB-D9 (new: AC cables in the three categories?); both ids are provisional. GROK's served model was unverified.
**Verification:** No external source re-fetched; GROK's HYC150, Akyga and Porsche claims are attributed to GROK in spec §5. No git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-1/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.1 for round 1. Recorded 0 blocking, 3 major and 5 minor findings: one efficiency factor scales both the battery limit and already-net DC station power; voltage-range overlap does not cover the requested SoC window; a booster cannot be stored or calculated with one voltage and one current; unresolved conflicts on direction stay eligible; AC has no power path; best value has no score and ties have no field; delivered price and offer expiry are not determined by the offer row; a measured test is not tied to the firmware and topology that produced it.
**Remaining:** CLAUDE consolidates round 1. The §11 minimum purchase-evidence threshold stays an open HUMAN decision and was not raised as blocking or major. No round-0 reviews or prior consolidation exist in this project.
**Verification:** HYC150 product brief v2.1, the Akyga AK-SC-E18 product page and user manual, and the Porsche Newsroom Taycan charging article (4 September 2019) were read on 2026-10-21. No standard text was opened. Review includes the required fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-1/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.1 for round 1. Recorded 0 blocking, 3 major and 5 minor findings: conversion adapters need separate input/output electrical envelopes and two interface checks; unknown safety-critical attributes must fail closed rather than reach a recommendation; "best value" has no deterministic objective, baseline or testable acceptance case; the no-adapter case and per-category nulls are not representable; AC charging has no performance model; battery temperature and shared station power are not time-varying inputs; ranking ties cannot be serialized; vehicle-profile/battery-variant identity is ambiguous in compatibility and test records.
**Remaining:** CLAUDE consolidates round 1. The minimum purchase-evidence threshold remains an open HUMAN decision and was not raised as blocking or major. No round-0 reviews or prior consolidation exist in this project.
**Verification:** Internal reasoning against the local spec; numerical examples are hypothetical, and linked product claims were not re-verified. Review includes the required fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-efficiency-specs/reviews/round-1/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local charging-efficiency spec v1.1 independently for round 1. Recorded 0 blocking, 1 major and 3 minor findings: blanket efficiency multiplication can reduce battery-side limits twice; voltage overlap does not guarantee completion of the requested SoC window; measured tests need immutable hardware/firmware configuration context; delivered-price ranking needs explicit comparability and offer-validity rules.
**Remaining:** CLAUDE consolidates round 1. The minimum purchase-evidence threshold remains an open HUMAN decision and was not raised as blocking or major. No round-0 reviews or prior consolidation exist in this project.
**Verification:** Internal reasoning against the local spec; numerical examples are hypothetical, and linked product claims were not re-verified. Review includes the required fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-4/CONSOLIDATION.md`, `projects/fuelbuddy/charging-diagnostic/spec.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** Consolidated FuelBuddy review round 4 (CHATGPT 3, DEEPSEEK 6, GROK 5 findings, all minor; 14 raw findings merged into 13 items, all accepted) and updated `spec.md` v0.5 → v0.6: stage outcomes and `external_authorization` as a stage value, `availability_state` and point-level station projection, restriction composition and the `safety_state` enum, outcomes as observations, `ecu` in the DTC mapping key, DIN/method consistency, symmetric `incident_id` grouping for contradictions, `unsupported_scope` response, in-use point alternates, idempotent replay vs session revision. Re-checked that the settled HUMAN decisions (FB-D1, FB-D2, FB-D3, FB-D5, FB-D7) stay applied. The README now states that the review converged at round 4 on v0.6.
**Remaining:** Open HUMAN decisions carried forward: FB-D4, FB-D6, FB-D1a–c, FB-D2a, FB-D5a. GROK's served model was unverified.
**Verification:** No external source re-fetched; GROK's AFIR Table B and Typhoon HIL claims are attributed to GROK in the spec. No git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-4/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.5 for round 4 after reading the round-3 reviews and consolidation, `decisions.md`, and the round-4 CHATGPT and DEEPSEEK reviews. Recorded 0 blocking, 0 major and 5 minor findings: `external_authorization` is missing from the closed stage list and `not_applicable` must stay derived; the architecture diagram sends every restriction to a full stop, including settled `charge_limited` and `do_not_charge_indoor`; the DIN row's "external payment only" can be read as forbidding RFID and app; an in-use recharging point has no rule against offering its other connector; an idempotent evaluate replay can return a body §2 says must not be displayed.
**Remaining:** CLAUDE consolidates round 4. Settled FB-D1/2/3/5/7 were not reopened; open FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a were not re-raised. Endorsed round-4 CHATGPT-1/2/3 and DEEPSEEK-1 through DEEPSEEK-6.
**Verification:** Official Journal PDF of Commission Implementing Regulation (EU) 2025/655 (Articles 1 and 2, Annex Tables B and F) and the Typhoon HIL DIN SPEC 70121 page were read on 2026-10-21. The Siemens CHAdeMO note was not re-fetched. ISO, DIN, IEC and CHAdeMO standard texts were not opened. Review uses the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-4/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.5 for round 4 after reading the round-3 reviews and consolidation, `decisions.md` and the round-4 CHATGPT review. Recorded 0 blocking, 0 major and 6 minor findings: no defined safety-state vocabulary or ordering behind the `safety_state`/monotonicity check; the §11 outcome record contradicts §3.2's single observation record and its `outcome` type; no ECU field for `VEHICLE_DTC` observations although §4.4/§4.5 require one; `plug_and_charge` not rejected for PWM-only/CHAdeMO and `free`/`unknown` authorization methods left unaddressed; the `contradicting` ranking term cannot use the `incident_id` evidence-group identity; no specified response behaviour for `unsupported_scope`.
**Remaining:** CLAUDE consolidates round 4. Settled FB-D1/2/3/5/7 were not reopened; open FB-D4, FB-D6, FB-D1a–c, FB-D2a and FB-D5a were not re-raised. Endorsed round-4 CHATGPT-1/2/3.
**Verification:** Internal reasoning only against the local spec and round-3 dispositions; no external factual claims re-verified. Review uses the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-4/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.5 after reading the round-3 reviews and consolidation and HUMAN's settled decisions. Recorded 0 blocking, 0 major and 3 minor findings: stage-event outcomes for deriving last successful stage; point identity and availability in the station projection and canonical payload; intersection of simultaneously applicable restriction permissions.
**Remaining:** CLAUDE consolidates round 4. Settled FB-D1/2/3/5/7 and the carried-forward open HUMAN decisions were not reopened.
**Verification:** Internal reasoning against the local spec and round-3 dispositions; no external factual claims re-verified. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/specs_review_loop.py`, `generic/run_review_loop.sh`, `generic/loop_monitor.py`, `generic/loop_wizard.html`, `generic/tests/test_specs_review_loop.py`, `generic/tests/test_loop_monitor.py`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** (1) Models and effort: DeepSeek reviewer now `deepseek-flash`; every backend defaults to effort `medium` (Codex `-c model_reasoning_effort="medium"`, Claude Code `--effort medium` for DeepSeek and the consolidator via `DEEPSEEK_EFFORT` / `CONSOLIDATOR_EFFORT`, Grok `grok-4.7-medium`; FAST=1 uses `grok-4.7-medium-fast`). (2) Per-step timing: each step writes `automation/logs/r{n}-{step}.timing.json` (start, end, seconds, ok, model, effort, tier, served model; Codex model/effort read from its banner) and the loop logs "round N: STEP done in 4m12s". (3) The Jarvis nodes, colour page and assistant chips show duration, model and effort. (4) The monitor plays a sound and a desktop notification when a round gets its `CONSOLIDATION.md` (silent on first look; `"sound": false` per loop or `LOOP_MONITOR_SOUND=0`).
**Round state:** the loop was started with `full` and ran straight on into round 4; stopped by HUMAN request after round 4 CHATGPT was committed (DeepSeek cancelled before writing). Rerun to continue; the loop resumes at round 4 DEEPSEEK.
**Verification:** 48 mocked tests pass; real probes with medium accepted by Codex, DeepSeek, Claude and Grok. Not yet run live in a full round.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/spec.md`, `projects/fuelbuddy/charging-diagnostic/reviews/round-3/CONSOLIDATION.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** Consolidated FuelBuddy review round 3 (9 findings from CHATGPT, DEEPSEEK, GROK; 8 distinct items, all accepted) into spec v0.5. Fixes: AFIR status is recharging-point level (new `recharging_point` subject), DIN SPEC 70121 split into its own DC-only profile with `safety_checks` marked `not_applicable` on AC and PWM-only sessions and a provisional CHAdeMO order, `measurement_kind` (quantity) vs `measurement_location` (reporter) with a defined measurement-kind catalog, authoritative evaluation fields through LLM validation, shared `incident_id` dedup, typed station-status payload, `stage` field and minimal session record. Applied HUMAN's settled FB-D1 (Europe), FB-D2, FB-D3, FB-D5 and FB-D7 from `decisions.md`. README now points at **Round 4** on v0.5, reviews in `reviews/round-4/`.
**Remaining:** Open HUMAN list carried forward in the consolidation: FB-D4, FB-D6, FB-D1a–c (API eligibility, launch countries, reduced mode), FB-D2a (re-verification period), FB-D5a (cache hard limit). Stop rule not met (one major, GROK-1). GROK is an unverified reviewer (no served model reported); its AFIR, DIN and CHAdeMO source claims were not re-fetched and are attributed in the spec.
**Verification:** Read-through and grep of the edited spec for leftover pending passages; no external sources re-fetched; no git commands run.

## 2026-10-21
**Agent:** GROK
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-3/GROK.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.4 for round 3 after reading the round-2 reviews and consolidation and HUMAN's settled decisions. Recorded 0 blocking, 1 major and 2 minor findings: AFIR dynamic status is recharging-point level under Implementing Regulation (EU) 2025/655, not connector-level status "in Europe"; the shared DIN 70121 stage row and the unmarked AC `safety_checks` stage are wrong, with a secondary-sourced CHAdeMO order; `measurement_location` is the reporter and `measurement_kind` is the quantity. Re-checked the round-2 AFIR article citations, ISO 15118-2 stage order, control-pilot states E/F and OCPP 2.0.1 NotifyEvent identity; those merged statements still hold. Endorsed CHATGPT-1/2/3 and DEEPSEEK-1.
**Remaining:** CLAUDE consolidates round 3. Settled FB-D1/2/3/5/7 were not reopened; open FB-D4/6 were not re-raised (no new evidence). Which public API covers the UK and Switzerland stays the open question already in `decisions.md`.
**Verification:** EUR-Lex text of Implementing Regulation (EU) 2025/655 (Annex Tables B and F, and the closing provisions), the Typhoon HIL DIN 70121 page, and the Siemens CHAdeMO TIA-library note were read on 2026-10-21. ISO, DIN, IEC and CHAdeMO standard texts were not opened. Review uses the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** DEEPSEEK
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-3/DEEPSEEK.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.4 for round 3 after reading the round-2 reviews and consolidation and HUMAN's settled decisions. Recorded 0 blocking, 0 major and 3 minor findings: the session-stage model (`stage`, `external_authorization`, `communication_profile`, `authorization_method`) has no field in the canonical record and no session schema; `measurement_kind` and `measurement_location` overlap on the charger-vs-vehicle distinction; the versioned `measurement_kind` catalog is referenced but never defined or scheduled. Endorsed CHATGPT-1/2/3 (LLM validation of decision fields, shared-incident dedup, station-state projection).
**Remaining:** CLAUDE consolidates round 3. Settled FB-D1/2/3/5/7 were not reopened; open FB-D4/6 were not re-raised (no new evidence).
**Verification:** Internal reasoning only against the local spec and round-2 dispositions; no external factual claims were re-verified. Review uses the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CHATGPT
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-3/CHATGPT.md`, `CHANGELOG.md`
**Change:** Reviewed local FuelBuddy spec v0.4 after reading the round-2 reviews and consolidation and HUMAN's settled decisions. Recorded 0 blocking, 0 major and 3 minor findings: pin deterministic evaluation fields through LLM validation; deduplicate shared incidents across different source documents; define the canonical representation of station-state fields.
**Remaining:** CLAUDE consolidates round 3. Settled FB-D1/2/3/5/7 were not reopened; open FB-D4/6 and outstanding HUMAN parameters were not re-raised.
**Verification:** Internal reasoning against the local spec and round-2 dispositions; no external factual claims were re-verified. Review uses the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this entry were written; no git commands, branches or pull requests.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/specs_review_loop.py`, `generic/tests/test_specs_review_loop.py`, `CHANGELOG.md`
**Change:** Fixed the DeepSeek 401. The DeepSeek reviewer ran `claude` with the default config dir `~/.claude`, which now holds a claude.ai OAuth login; Claude Code sent that login token (not the DeepSeek key) to api.deepseek.com, which answered "Authentication Fails" (the key echoed as `****JgAA` was the OAuth token, not the DeepSeek key ending `fb42`). The DEEPSEEK profile now sets `CLAUDE_CONFIG_DIR` to its own dir (`~/.claude-deepseek`, override `DEEPSEEK_CLAUDE_CONFIG_DIR`), like the Anthropic consolidator already did.
**Verification:** The key in `~/.credentials` returns HTTP 200 on both DeepSeek endpoints; a probe through `_claude_once` with the isolated profile returned OK from deepseek-chat. 37 mocked tests pass (1 new). Full preflight not yet rerun.
**Remaining:** GROK still needs `cursor-agent login`. The OAuth login token was sent to api.deepseek.com on each DeepSeek call since that login; it is a short-lived access token that rotates, but log out and in to rotate it now if concerned.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/loop_monitor.py`, `generic/specs_review_loop.py`, `generic/loop_wizard.html`, `generic/tests/test_loop_monitor.py`, `CHANGELOG.md`
**Change:** Added a `PREFLIGHT` node per round. Jarvis graph: `rN-PREFLIGHT` (depends on `r(N-1)-CLAUDE`) gates the round's reviewers; it is in progress while probes run, red if any fail, completed if they pass, pending if none ran for round N. The engine now writes the round into `preflight.json`, so a pass for another round does not count. Same chip on the colour page and the assistant page. Only the current round has a preflight node.
**Verification:** 36 mocked tests pass (1 new; one flaky cmdline test made robust). Live graph shows `r3-PREFLIGHT` failed with DEEPSEEK/GROK reasons. A passing/running preflight node was only tested with mocks.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/loop_monitor.py`, `generic/loop_wizard.html`, `generic/loop_wizard.py`, `generic/tests/test_loop_monitor.py`, `CHANGELOG.md`
**Change:** The monitor no longer reports a preflight as a running review round: if the process holding `.loop.lock` was started with `--preflight`, the loop shows `preflight` (amber, steps pending, no chain launch) instead of green. The wizard refuses to start a job while the loop is locked.
**Finding (preflight of 11:32, round 3):** it was not hung, it ended after about 4.7 min with 2 of 4 probes failed. DEEPSEEK: HTTP 401, the key in `~/.credentials` (ends `JgAA`) is invalid; the probe waited about 4m23s before giving up. GROK: `cursor-agent` is not authenticated (`Authentication required`), also from a plain shell, although `cursor-agent status` still says logged in. CHATGPT and the Anthropic consolidator probes passed.
**Remaining:** HUMAN must set a valid DeepSeek key and run `cursor-agent login` (or set `CURSOR_API_KEY`), then rerun the preflight. The engine could fail fast on a 401 instead of waiting.
**Verification:** 34 mocked tests pass (2 new).

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/loop_wizard.py`, `generic/loop_wizard.html`, `generic/REVIEW_LOOP_GUIDELINE.md`, `.gitignore` (`generic/loops.json` is now local-only), `CHANGELOG.md`
**Change:** The assistant now runs the steps itself. `generic/loop_wizard.py` serves the page on 127.0.0.1:8795 and exposes a fixed set of actions (git status/commit of ticked files, create loop = branch + spec/README skeletons + commit + registration, start/stop monitor, preflight/one/full runs with live output, retry). Every request needs a per-start token and a 127.0.0.1 Host header; no arbitrary shell. The page also shows live loop colours.
**Verification:** Auth/Host/validation checked with curl; create_loop run end to end in a throwaway clone; existing-loop flow and git check clicked in the browser pane. No paid run, no commit or monitor start from the page yet.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/loop_monitor.py`, `generic/loops.json`, `generic/loops.example.json`, `generic/loop-monitor.service`, `generic/tests/test_loop_monitor.py`, `generic/REVIEW_LOOP_GUIDELINE.md`, `.gitignore`, `~/GIT/jarvis/jarvis-tracker.service` (and the installed copy), `CHANGELOG.md`
**Change:** Added a monitor for all review loops. State comes from the files and the `.loop.lock` flock (read from `/proc/locks`, so the monitor never takes the lock). Colour page `generic/.monitor/index.html` (green running, blue complete, red failed, grey pending). Jarvis export of one graph per loop in `.jarvis/tracker/`, with rounds appended as the README advances (round N+1 depends on `rN-CLAUDE`). Chaining: `after` + `autostart` launches the next loop when the previous is complete, nothing else runs and the tree is clean; failed loops need `retry`. The two Jarvis tracker unit files got the new memory/log dirs appended and the service was restarted.
**Remaining:** `loop-monitor.service` is not installed; only FuelBuddy is registered and `autostart` is off, so nothing launches by itself yet. No live chained launch tested (mocked only).
**Verification:** 32 mocked tests pass (9 new); `status` run against FuelBuddy; the graph shows in Jarvis `/api/runs`.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/REVIEW_LOOP_GUIDELINE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`
**Change:** Added the guideline every agent follows when starting a spec review loop: folder structure, required README/spec content, ownership, setup steps, run commands, rules and checklist. Linked from `CONTRIBUTING.md`.
**Verification:** Checked against the engine's requirements (`**Round N**` line, version line, `decisions.md` rule, branch default, lock file). No live run.

## 2026-10-21
**Agent:** CLAUDE
**Files:** `generic/run_review_loop.sh` (moved from `projects/fuelbuddy/charging-diagnostic/automation/`), `generic/tests/test_specs_review_loop.py` (moved from `projects/fuelbuddy/charging-diagnostic/automation/tests/test_review_loop.py`), `projects/fuelbuddy/charging-diagnostic/automation/run_review_loop.sh`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** Moved the launcher and the unit tests to `generic/`. The launcher now takes `<project-dir> <name> [branch] {preflight|one|full}` and finds the repo from its own location. The FuelBuddy folder keeps only a thin wrapper that passes its values, plus its gitignored `automation/logs/`.
**Verification:** 23 mocked tests pass from `generic/tests`; both scripts pass `bash -n`; usage errors checked. No live review run. Not committed.

## 2026-10-20
**Agent:** CLAUDE
**Files:** `generic/specs_review_loop.py`, `projects/fuelbuddy/charging-diagnostic/automation/run_review_loop.sh`, `projects/fuelbuddy/charging-diagnostic/automation/tests/test_review_loop.py`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** Made the review loop project-agnostic. New arguments `--project` (required, or `REVIEW_PROJECT`), `--name` (commit/prompt label, default the folder under `projects/`) and `--branch` (default `agent/loop/<name>-review`). No FuelBuddy path, branch or name is hard-coded any more; the `decisions.md` rule is added to the prompts only when the project has that file. The launcher passes `--project projects/fuelbuddy/charging-diagnostic --name FuelBuddy --branch agent/loop/fuelbuddy-review`, so FuelBuddy commit messages and branch are unchanged.
**Verification:** 23 mocked unit tests pass (2 new: configure defaults, conditional decisions rule); CLI error paths checked by hand. No live review run.

## 2026-10-20
**Agent:** GROK
**Files:** `generic/specs_review_loop.py` (moved from `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`), `projects/fuelbuddy/charging-diagnostic/automation/run_review_loop.sh`, `projects/fuelbuddy/charging-diagnostic/automation/tests/test_review_loop.py`, `projects/fuelbuddy/charging-diagnostic/README.md`, `agents/GROK.md`, `CONTRIBUTING.md`, `agents/CHATGPT.md`, `agents/CLAUDE.md`, `agents/CURSOR.md`, `agents/DEEPSEEK.md`, `agents/GEMINI.md`, `CHANGELOG.md`
**Change:** Moved the review loop to `generic/specs_review_loop.py`. FuelBuddy logs stay in `projects/fuelbuddy/charging-diagnostic/automation/logs/`. Updated the launcher, tests, and run commands. Recorded the project-folder and commit-identity rules in `CONTRIBUTING.md` and `agents/`.
**Remaining:** Historical notes in `PROPOSAL-fix-review-loop.md` and older changelog entries still name the old script path.
**Verification:** `git mv` plus path updates. Unit tests for the loop, no live review run.

## 2026-10-14
**Agent:** CLAUDE  
**Files:** `projects/fuelbuddy/charging-diagnostic/spec.md`, `projects/fuelbuddy/charging-diagnostic/reviews/round-2/CONSOLIDATION.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`  
**Change:** Consolidated FuelBuddy review round 2 (CHATGPT, DEEPSEEK, GROK; 18 raw findings → 17 items: 16 accepted, 1 partial, 0 rejected) and updated the spec v0.3 → v0.4. Three majors fixed: typed measurement identity (`measurement_kind`, location, aggregation, window), Plug & Charge stage order with a `communication_profile` and PWM-only AC path, and OCPP 2.0.1 `component`/`variable`/`tech_code` in the mapping key. Also added the post-matching safety pass, supersession direction, `incident_id`, ranking-policy contract, AFIR citations via Implementing Regulation (EU) 2025/655, control-pilot state E/F correction, and several consistency fixes. README now points to Round 3 on v0.4 with reviews in `reviews/round-3/`.  
**Remaining:** Stop rule not met (three majors this round); round 3 reviews v0.4. FB-D1–FB-D7 stay open and are carried forward in the consolidation; none were decided. GROK served model is unverified (noted in the consolidation).  
**Verification:** Edited text checked against the three round-2 reviews and the v0.3 spec; external claims (ISO 15118-2 sequence, OCPP 2.0.1, IEC 61851, Implementing Regulation 2025/655) are the GROK reviewer's, not re-fetched. No git commands.

## 2026-10-14
**Agent:** GROK  
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-2/GROK.md`, `CHANGELOG.md`  
**Change:** Reviewed local FuelBuddy spec v0.3 for round 2 after reading the round-1 reviews and consolidation. Recorded 3 major findings (Plug & Charge stage order reversed relative to the ISO 15118-2 sequence, and no PWM-only AC path; OCPP 2.0.1 mapping key still lacks component, variable, and tech code; measurement observations cannot carry the quantity and qualifier distinctions §5 and §6.4 require) and 2 minor findings (AFIR dates now confirmed in Implementing Regulation (EU) 2025/655, including a one-minute dynamic-update duty rather than "about a minute"; IEC 61851-1 state E, not state F, is the error state in a vendor summary). Did not re-raise FB-D1–FB-D7.  
**Remaining:** CLAUDE consolidates the round-2 findings; existing HUMAN decisions remain pending.  
**Verification:** Stage order checked against the Typhoon HIL ISO 15118-2 sequence description; OCPP 2.0.1 fault identity checked against the Open Charge Alliance uptime white paper v1.2 (August 2024); AFIR dates checked against EUR-Lex text of Implementing Regulation (EU) 2025/655; control-pilot states checked against Beckhoff's IEC 61851 summary. ISO 15118-2, IEC 61851-1, and the AFIR base-regulation HTML were not opened. Review includes the required finding fields, Top 3, and `Result: complete`. Spec unchanged. No git commands, branch, or pull request.

## 2026-10-14
**Agent:** DEEPSEEK  
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-2/DEEPSEEK.md`, `CHANGELOG.md`  
**Change:** Reviewed local FuelBuddy spec v0.3 for round 2 after reading all round-1 reviews and the consolidation, plus the round-2 CHATGPT review. Found no new blocking or major findings; recorded 8 minor findings (wireless in the `charge_mode` enum vs §4.5's out-of-scope list; LLM input missing the evidence records §9.2's `evidence_id` check resolves against; `cause_id`/`candidate_id` naming drift; ranking dedup key's undefined `incident` field; §4.3 `station_observations` restating a second observation shape; §12 "fixtures above" dangling reference; §9.1 example missing subject fields and a differing `protocol_version` shape; leftover consolidation remediation notes in §4.4/§4.5). Endorsed CHATGPT-1 (major) and did not re-raise FB-D1–FB-D7 (no new external evidence).  
**Remaining:** CLAUDE consolidates the round-2 findings; existing HUMAN decisions remain pending.  
**Verification:** Internal reasoning against local spec sections, the round-1 dispositions and the round-2 CHATGPT review; external sources were not re-verified. Review includes the required finding fields, Top 3 and a final `Result: complete`; spec unchanged. No git commands, branch, or pull request.

## 2026-10-14
**Agent:** CHATGPT  
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-2/CHATGPT.md`, `CHANGELOG.md`  
**Change:** Reviewed local FuelBuddy spec v0.3 after reading all round-1 reviews and consolidation. Recorded 1 major finding (measurement quantity identity and qualifiers) and 4 minor findings (post-matching safety pass, supersession direction/activation, ranking-policy completeness, campaign applicability wording). Retained accepted round-1 changes and did not reopen FB-D1–FB-D7.  
**Remaining:** CLAUDE consolidates round 2; existing HUMAN decisions remain pending.  
**Verification:** Internal reasoning against local spec and round-1 dispositions; external sources were not re-verified. Review includes the required finding fields, Top 3 and final `Result: complete`. Only the authorized review and this changelog entry were written; no git commands, branch or pull request.

## 2026-10-14
**Agent:** DEEPSEEK  
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-2/DEEPSEEK.md`, `CHANGELOG.md`  
**Change:** Reviewed the local FuelBuddy charging diagnostic spec v0.3 for round 2 after reading all round-1 reviews and the consolidation, and the round-2 CHATGPT review. Found no new blocking or major findings; recorded 6 minor findings (tie-handling sort key uses the session-level `decision_status`; `protocol_version` has two incompatible shapes; §3.3 session fields with no home in §3.2; `source_type` overloaded across event and document provenance; §4.3 `station_observations` restates an observation shape; deterministic `decision_status`/cause order not pinned through the LLM validator). Agreed with CHATGPT's two major findings and did not re-raise FB-D1–FB-D7 (no new external evidence).  
**Remaining:** CLAUDE consolidates the round-2 findings; existing HUMAN decisions remain pending.  
**Verification:** Internal reasoning only; checked against local spec sections, the round-1 dispositions, and the round-2 CHATGPT review; external sources were not re-verified. Review ends with `Result: complete`; spec unchanged. No git commands, branch, or pull request.

## 2026-10-14
**Agent:** CHATGPT  
**Files:** `projects/fuelbuddy/charging-diagnostic/reviews/round-2/CHATGPT.md`, `CHANGELOG.md`  
**Change:** Reviewed the local FuelBuddy charging diagnostic spec v0.3 for round 2 after reading all round-1 reviews and consolidation. Recorded 2 major findings (safety reevaluation after knowledge matching; typed measurement identity and qualifiers) and 3 minor findings (ranking-policy completeness, idempotency scope, campaign applicability wording). Retained the accepted round-1 direction and did not reopen FB-D1–FB-D7.  
**Remaining:** CLAUDE consolidates the round-2 findings; existing HUMAN decisions remain pending.  
**Verification:** Checked findings against local spec sections and the round-1 dispositions. Internal reasoning only; external sources were not re-verified. Review ends with `Result: complete`; spec unchanged. No git commands, branch, or pull request.

## 2026-10-12
**Agent:** CLAUDE  
**Files:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `projects/fuelbuddy/charging-diagnostic/automation/.gitignore`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`  
**Change:** Automated the FuelBuddy multi-AI review loop. `automation/review_loop.py` runs each round as CHATGPT review (Codex CLI) → DEEPSEEK review (Claude Code on the DeepSeek API, `deepseek-v4-pro`, told explicitly "You are DEEPSEEK") → CLAUDE consolidation (Claude Code on Anthropic, `claude-sonnet-5-5`). It commits and pushes after every step on `agent/loop/fuelbuddy-review` and stops at the README stop rule (no blocking/major finding) or after `--max-rounds`. It has a `--preflight` probe mode; logs go to `automation/logs/` (git-ignored). Added an "Automated loop" section to the diagnostic README.  
**Remaining:** HUMAN runs the loop (`--preflight` first) and merges the branch PR at the end. `~/.claude-anthropic` does not exist yet on the laptop: log in once there for the CLAUDE consolidator profile.  
**Verification:** Tested against fake `codex`/`claude` stubs in a scratch repo. Laptop environment: codex-cli 0.162.1, Claude Code 2.1.296, DeepSeek `ANTHROPIC_BASE_URL` present in `~/.claude/settings.json`. Preflight not yet run on the laptop.

## 2026-10-11
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/spec.md`, `projects/fuelbuddy/charging-diagnostic/reviews/round-1/CONSOLIDATION.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Claim / handoff:** `owner=CLAUDE`, `started_at=2026-10-11`; claimed and released with this entry (shared files: `CHANGELOG.md`; plus CLAUDE-owned `spec.md` and the round-1 README "Current round" line).
**Change:** Round-1 consolidation. Merged the three round-1 reviews (CLAUDE 15, CHATGPT 15, DEEPSEEK 15 findings) into `spec.md` **v0.3**: 45 raw findings → 27 distinct items (19 accepted, 1 partial, 0 rejected, 7 routed to HUMAN as FB-D1…FB-D7). Key v0.3 changes: one canonical observation record (§3.2) fixing the broken `source_type` enum; method-dependent session stages; CHAdeMO / IEC 61851-1 control-pilot / SLAC namespaces and OCPP 2.x message+field identity; split LLM validation with rendered executable guidance; fully defined ranking terms plus the `decision_status` abstention contract; a charging-model interface for §6.4; per-campaign `vehicle_campaign_status` and `safety_rule_ids`; session revisions and dependency-aware release manifests; three-valued applicability predicates; a measurable release-evaluation manifest; the AFIR source class; and the photo/sensitive-content data boundary. Re-labelled §7 as illustrative sourced examples; removed the unverifiable `FAILED_AlignmentError` example. Added `reviews/round-1/CONSOLIDATION.md` (accepted/decided/rejected, traceability matrix, decision list) and moved the README to round 2 on v0.3.
**Remaining:** HUMAN decides FB-D1 (MVP market), FB-D2 (safety clearance semantics), FB-D3 (emergency stop / stuck cable), FB-D4 (GDPR/DPIA), FB-D5 (offline degradation), FB-D6 (photo boundary/retention), FB-D7 (ranking approach). Round-1 is missing GROK/GEMINI/CURSOR; recommended that CURSOR run its consistency pass on v0.3 in the round-2 window. Stop rule not met (blocking-class items still open pending FB-D2/FB-D1).
**Verification:** Read all three round-1 reviews in full (CHATGPT's and DEEPSEEK's from their branches, not yet merged to `main`); every one of the 45 findings appears in the traceability table. Spec checked for stale identifiers (`operator_integration`, scalar `recall_status`, `FAILED_AlignmentError`, `DIN SPEC 99003`) and section cross-references. No external source was re-fetched; the AFIR dates remain flagged as secondary. Findings are proposals; safety/legal/scope items were left for HUMAN rather than decided.

## 2026-10-11
**Agent:** CLAUDE  
**Files:** `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`  
**Change:** Replaced the per-AI prompt template with one fixed standard prompt (a link to the README). The README now carries a "Current round" line, updated by CLAUDE at each consolidation, and step-by-step instructions for the reviewing AI, including how it determines its identity and round.  
**Remaining:** HUMAN sends the standard prompt to each AI for round 1.  
**Verification:** Links point to `main`; README read end to end for consistency.

## 2026-10-11
**Agent:** CLAUDE  
**Files:** `projects/fuelbuddy/charging-diagnostic/spec.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `projects/fuelbuddy/charging-diagnostic/reviews/round-1/CLAUDE.md`, `README.md`, `CHANGELOG.md`  
**Change:** Added the FuelBuddy AI Charging Diagnostic spec v0.2 (supplied by HUMAN) and a multi-AI review process: independent review files per AI per round, a common finding format, a ready-to-paste prompt for each AI, and CLAUDE consolidation into the next version. Added CLAUDE's round-1 review (15 findings; S1 and S2 seed sources verified).  
**Remaining:** Round-1 reviews from CHATGPT, GROK, DEEPSEEK, GEMINI and CURSOR (consistency only); then CLAUDE consolidates into v0.3 with a decision list for HUMAN.  
**Verification:** Seed sources S1, S2 and S3 opened and checked 2026-10-11; AFIR dates from secondary sources, flagged as such in the review.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `samples/datex/*.xml`, `src/traffic/datex/parser.py`, `src/traffic/load.py`, `src/traffic/smoke.py`, `sql/001_measures.sql`, `web/smoke_map.html`, `tests/test_datex_parser.py`, `tests/test_smoke_db.py`, `dev/Makefile`, `dev/README.md`, `pyproject.toml`, `uv.lock`, `CHANGELOG.md`  
**Change:** P0-14 — end-to-end smoke test: synthetic DATEX II 2.2 samples (site table, measured data, one correction) → tolerant lxml parser → Postgres model per D8/D11 (`measurement_site`, `traffic_measure` with `source_version`, `traffic_measure_current`, map view `site_latest_traffic`, hypertable when TimescaleDB present) → MapLibre page via Martin. `make -C dev smoke` and `make -C dev test` targets. Builds on P0-13 (PR #17).  
**Remaining:** HUMAN: run `make -C dev up && make -C dev smoke` and open `web/smoke_map.html` on a machine with Docker; tick the smoke-test line of the GO/NO-GO checklist if it works. Next technical step: run the parser on real open DIR files (S-1/S-2).  
**Verification:** Parser unit tests pass; smoke run passes twice (idempotent) against local Postgres 16 + PostGIS, also via `make -C dev smoke`; map view registered in `geometry_columns` (Point, 4326). Not verified here: TimescaleDB, Martin, browser rendering; samples not validated against the official DATEX II XSD.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `dev/docker-compose.yml`, `dev/Makefile`, `dev/martin.yaml`, `dev/db/init/001_extensions.sql`, `dev/README.md`, `pyproject.toml`, `uv.lock`, `src/traffic/__init__.py`, `tests/test_package.py`, `.env.example`, `CHANGELOG.md`  
**Change:** P0-13 — dev scaffold: Docker Compose stack (TimescaleDB-HA pg16 with PostGIS, Redis 7, Martin with auto-publish), Makefile wrapper, first-start extension script, `uv` Python project with pytest, and dev variables in `.env.example`. Proposed canonical bootstrap command: `make -C dev up`. Claimed `.env.example` (`owner=CLAUDE`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN: run `make -C dev up` on a machine with Docker (images could not be pulled here), approve or change the bootstrap command; once approved, record it in `CONTRIBUTING.md`. Pin image tags after the first successful start.  
**Verification:** `docker compose config` passes; `make -n` dry run correct; `uv lock` and `uv run pytest` pass. Containers not started (registry access blocked in this environment).
**Files:** `LICENSE`, `CHANGELOG.md`  
**Change:** P0-7 — drafted the proprietary internal-use `LICENSE` (D3): all rights reserved; scope covers code, configuration, documentation and derived data; use limited to the Owner and people/agents it authorises; third-party data stays under its own licence (Licence Ouverte 2.0; Bison Futé action b v9), with their attribution and last-update duties summarised from P0-4.  
**Remaining:** HUMAN: fill in the copyright holder (left as Remi Montroty), review the text (ideally with legal advice), then tick the two remaining P0-7 sub-items. `TODO.md` not edited to avoid version conflicts with open PRs.  
**Verification:** Third-party terms checked against the sources in `docs/data_sources.md` (PR #15). Not legal advice.
**Files:** `docs/data_sources.md`, `docs/README.md`, `docs/RISKS.md`, `.env.example`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-4 draft — `docs/data_sources.md` with the A11 operator map, four Phase 0 source sheets (DIR events, DIR traffic state, Bison Futé restricted action b and action c), VINCI Autoroutes direct status, deferred sources, Alert-C direction conventions and a GDPR proposal. Key findings: the A11 is fully concessioned (Cofiroute + ASF), so its live data needs the Bison Futé restricted portal; SCAs may offer volumes only; feeds are DATEX II 2.2.2. Added restricted-portal credential names to `.env.example`, the file to `docs/README.md`, and one new risk to `docs/RISKS.md`. TODO → v2.10, P0-4 `[~]`. Claimed `docs/README.md`, `docs/RISKS.md`, `.env.example`, `TODO.md` (`owner=CLAUDE`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN: request restricted access (email in the file), verify licence and GDPR conclusions, then record them in `DECISIONS.md`. Open checks marked ⚠ in the file (bypass operator, SCA speed availability, exact open-directory paths, 2.2.2 element names).  
**Verification:** Every fact cites a source checked on 2026-10-03; unverified items marked ⚠. Not ticked: needs HUMAN review.
**Files:** `agents/CLAUDE.md`, `CHANGELOG.md`  
**Change:** Added CLAUDE's role, working rules and ordered P0 task queue to `agents/CLAUDE.md` (P0-4 → P0-7 LICENSE text → P0-13 → P0-14), keeping the existing instructions. CLAUDE does not self-tick: its tasks need HUMAN review. Replaces PR #7, which predated CURSOR's completed queue.  
**Remaining:** CLAUDE starts P0-4.  
**Verification:** Queue matches the CLAUDE owner fields in `TODO.md` v2.9.
**Files:** `.github/workflows/gitleaks.yml`, `CHANGELOG.md`  
**Change:** P0-6 leftover — added the gitleaks GitHub Actions workflow CURSOR could not push (no `workflow` scope): runs on pull requests and on pushes to `main`, full history checkout, `gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`. Matches CURSOR's intended content; adds the push-to-`main` trigger.  
**Remaining:** HUMAN to confirm the first run passes, then tick P0-6.  
**Verification:** YAML written; not yet run on GitHub.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/RISKS.md`, `docs/README.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-11 — created `docs/RISKS.md` with required columns; filled only from risks already in `TODO.md`/`DECISIONS.md` (cited); Likelihood/Impact = `?`. Updated `docs/README.md` index. Ticked P0-11; TODO → v2.9. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN reviews Likelihood/Impact. **CURSOR queue empty** — no further tasks in `agents/CURSOR.md` until HUMAN assigns new work in `TODO.md`. Open leftover: P0-6 Actions workflow (needs `workflow` scope).  
**Verification:** No invented risks; no Likelihood/Impact values guessed.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/README.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-10 — added `docs/README.md` index (one line per existing file: `SPEC_PHASES.md`, `phase0_go_no_go.md`). Ticked P0-10; TODO → v2.8. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** Next CURSOR queue item after merge: P0-11 (`docs/RISKS.md`).  
**Verification:** Only existing `docs/` files listed; no invented doc paths as present.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `CONTRIBUTING.md`, `.env.example`, `.pre-commit-config.yaml`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-6 (partial) — credential policy in `CONTRIBUTING.md`; `.env.example` header only; gitleaks `.pre-commit-config.yaml` (rev v8.24.2); confirmed `.env` in `.gitignore`. TODO → v2.7; P0-6 left `[~]`. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN must add `.github/workflows/gitleaks.yml` (push blocked: OAuth App lacks `workflow` scope) — intended content: `on: pull_request`, `actions/checkout@v4` with `fetch-depth: 0`, `gitleaks/gitleaks-action@v2` with `GITHUB_TOKEN`. Then tick P0-6. P0-4/P0-13 add `.env.example` variables later. Next queue items P0-10/P0-11 wait on whether HUMAN treats this partial as enough to proceed.  
**Verification:** Policy text matches TODO; `.env` ignored; workflow file intentionally omitted from the push.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/phase0_go_no_go.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-8 — wrote `docs/phase0_go_no_go.md` with the TODO checklist items (unticked) plus empty HUMAN sign-off line. Ticked P0-8 write step only; TODO → v2.6. Claimed (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN fills/signs checklist when gate criteria exist. Next CURSOR queue item after merge: P0-6.  
**Verification:** Checklist wording matches P0-8; no sub-boxes ticked.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `docs/SPEC_PHASES.md`, `SPEC_PHASES.md`, `MASTER.md`, `README.md`, `DECISIONS.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-3 — `git mv` `SPEC_PHASES.md` → `docs/SPEC_PHASES.md`; root stub redirect; updated links in `MASTER.md`, `README.md`, `DECISIONS.md`. Ticked P0-3; TODO → v2.5. Claimed shared docs (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** Next CURSOR queue item after merge: P0-8 (GO/NO-GO checklist).  
**Verification:** Spec content at `docs/SPEC_PHASES.md`; root stub points there; older CHANGELOG entries left unchanged.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `DECISIONS.md`, `MASTER.md`, `TODO.md`, `CHANGELOG.md`  
**Change:** P0-1 + P0-2 + P0-7 intent ADR — recorded D1–D11 as accepted ADRs in `DECISIONS.md` (D1 title and freeze sentence; D2 `uv` migration note; D3 licence intent). Marked prior 2026-10-02 stack/A11 ADRs superseded. Aligned `MASTER.md` (freeze sentence; removed proposed stack/axis and open uv/poetry question). Ticked P0-1, P0-2; P0-7 left `[~]` with intent ADR sub-item done. TODO → v2.4. Claimed `DECISIONS.md`/`MASTER.md`/`TODO.md` (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** CLAUDE for P0-7 LICENSE text/scope; HUMAN sign-off on P0-7. Next CURSOR queue item after merge: P0-3 (`docs/` move).  
**Verification:** Freeze sentence present in both files; no `LICENSE` file created; CURSOR-owned boxes only ticked.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `agents/CURSOR.md`, `CHANGELOG.md`  
**Change:** HUMAN decision: CURSOR ticks its own tasks in `TODO.md` when it completes them; HUMAN reviews afterwards. Status legend in `TODO.md` (v2.3) and `agents/CURSOR.md` updated accordingly (owner-only ticks, version bump per tick, never sign-offs). P0-5 ticked.  
**Remaining:** HUMAN review of P0-5 when convenient.  
**Verification:** Rule text consistent across `TODO.md` and `agents/CURSOR.md`.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `agents/CURSOR.md`, `CHANGELOG.md`  
**Change:** Added instruction file for CURSOR (Cursor Auto): role limits, git and changelog rules, files reserved for other owners, and its ordered P0 task queue (P0-1/P0-2/P0-7 intent ADR → P0-3 → P0-8 checklist → P0-6 → P0-10 → P0-11). Task content stays in `TODO.md`.  
**Remaining:** HUMAN to review P0-5 (PR #3). No instruction file exists yet for GROK.  
**Verification:** Queue matches the CURSOR owner fields in `TODO.md` v2.2.

## 2026-10-03
**Agent:** CURSOR  
**Files:** `CONTRIBUTING.md`, `CHANGELOG.md`  
**Change:** P0-5 — added status rule, single-writer protocol (claim/release via `CHANGELOG.md` with `owner` + `started_at`), and human-approval rule to `CONTRIBUTING.md`. Identities CURSOR and GROK were already present. Claimed `CONTRIBUTING.md` (`owner=CURSOR`, `started_at=2026-10-03`); released with this handoff.  
**Remaining:** HUMAN review of P0-5 (do not tick until verified). Next: P0-12 GitHub rendering check; other P0-gate items.  
**Verification:** Wording matches TODO.md P0-5; TODO.md left unticked for HUMAN.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.2. The v2.0 (D11) and v2.1 (P0 owners) commits were pushed after PR #1 was merged, so they were missing from `main`; rebased onto `main` and re-submitted. P0-5 identities sub-task marked done (HUMAN added `CURSOR` and `GROK` to `CONTRIBUTING.md` in 3af0482).  
**Remaining:** Rest of P0-5 (status rule, single-writer protocol, human-approval rule) for CURSOR.  
**Verification:** `TODO.md` on this branch reads v2.2; identity list checked in `CONTRIBUTING.md`.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.1 — HUMAN assigned owners to every P0 item (P0-9 done): CURSOR (Auto) for well-specified edits (P0-1, P0-2, P0-3, P0-5, P0-6, P0-7 ADR, P0-8 checklist, P0-10, P0-11); CLAUDE (Opus 5.5) for P0-4 research, P0-7 LICENSE text, and new items P0-13 (dev scaffold) and P0-14 (smoke test); HUMAN for P0-12 and all sign-offs.  
**Remaining:** CURSOR identity is not yet in `CONTRIBUTING.md` (added by P0-5). HUMAN still to fill cost envelope and metric thresholds. Next: P0-12 (HUMAN), then CLAUDE starts P0-4.  
**Verification:** Document only.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** TODO v2.0 — HUMAN resolved D11: source corrections are appended as revisions (key `(site_id, source, source_ts, source_version)`, `traffic_measure_current` view feeds aggregates). No open decisions remain in the TODO.  
**Remaining:** HUMAN to assign P0 owners (P0-9), fill cost envelope and metric thresholds. D11 to be recorded in `DECISIONS.md` alongside the other ADRs.  
**Verification:** Document only.

## 2026-10-03
**Agent:** CLAUDE  
**Files:** `TODO.md`, `CHANGELOG.md`  
**Change:** Replaced the task list with the consolidated multi-agent review TODO v1.1 (Claude, Gemini/previous assistant, Grok, ChatGPT, DeepSeek). Decisions D1–D10 resolved by HUMAN on 2026-10-03; D11 (source corrections) open. P0 split into gate/hygiene. Previous phase work queue and agent-assignment table preserved verbatim in a dedicated section.  
**Remaining:** HUMAN to decide D11, assign owners to P0 items (P0-9), fill cost envelope and metric thresholds. Next execution step: P0-12 (check GitHub rendering of `CONTRIBUTING.md` / `CHANGELOG.md`).  
**Verification:** Document only; no decision recorded in `DECISIONS.md` yet (that is P0-1/P0-2/P0-7).

## 2026-10-02
**Agent:** CLAUDE  
**Files:** `SPEC_PHASES.md`, `MASTER.md`, `TODO.md`, `CHANGELOG.md`, `README.md`, `DECISIONS.md`  
**Change:** Ingested plateforme nationale de trafic routier spec v1.0 (phases 0–7). Canonical brief and Phase 0 task queue populated.  
**Remaining:** Fill `docs/data_sources.md`; scaffold `dev/`; smoke test DATEX factice; human GO/NO-GO phase 0.  
**Verification:** Documents written; no runtime/env verified yet.

## YYYY-MM-DD
**Agent:** HUMAN  
**Files:**  
**Change:** Workspace initialized.  
**Remaining:** Define project.  
**Verification:** Not applicable.


## 2026-10-14 — inline proposal review claim
**Agent:** CHATGPT (GPT-6.1 SOL)
**Owner:** CHATGPT
**Started_at:** 2026-10-14T10:27:06+02:00
**Files:** `projects/fuelbuddy/charging-diagnostic/PROPOSAL-fix-review-loop.md`
**Change:** Claim the proposal for inline review of the available model feedback, as requested by HUMAN. Preserve existing author text and add attributed comments only.


## 2026-10-14 — inline proposal review handoff
**Agent:** CHATGPT (GPT-6.1 SOL)
**Files:** `projects/fuelbuddy/charging-diagnostic/PROPOSAL-fix-review-loop.md`, `CHANGELOG.md`
**Change:** Added attributed inline replies to DEEPSEEK-1 through DEEPSEEK-6 and remaining SOL findings on resume, zero-finding reviews, Git isolation and live testing. Existing proposal and model comments preserved.
**Remaining:** Incorporate the corrections and validate the runners before a live unattended loop. Architecture accepted in principle, proposal not approved as written.
**Verification:** Compared feedback with the current runner code; document-only edit, no model calls or implementation. Proposal file released for the next contributor.


## 2026-10-14 — moderator decision on review-loop proposal
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/PROPOSAL-fix-review-loop.md`, `CHANGELOG.md`
**Change:** Consolidated DEEPSEEK and CHATGPT comments, decided all open points (D1–D12) and appended a phased roadmap. Noted that my earlier counterproposal had been lost from the file and folded it into the decisions.
**Remaining:** HUMAN Phase 0 (credentials); then implement from Phase 1.
**Verification:** Document-only; checked Codex/Cursor CLI flags earlier. No model calls.


## 2026-10-14 — GROK added to the FuelBuddy review loop
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `projects/fuelbuddy/charging-diagnostic/automation/run_review_loop.sh`, `projects/fuelbuddy/charging-diagnostic/README.md`, `agents/GROK.md`, `CHANGELOG.md`
**Change:** Added `run_cursor_agent` and a runner map (fixes the dispatcher that sent every non-CHATGPT reviewer to DeepSeek), reviewer-name validation, GROK/CURSOR identity prompts, default reviewers `CHATGPT,DEEPSEEK,GROK`, selected-backend preflight with a write probe, `agents/GROK.md`, README update, and the `run_review_loop.sh` launcher. Proposal D6/D11 (partial).
**Remaining:** Codex `--full-auto` fix, DeepSeek model/identity hardening, resume safety, git worktree isolation, mocked tests.
**Verification:** Live preflight `--reviewers GROK --skip-consolidator` passed on `grok-4.7-high` (nonce file written and verified). Reviewer validation checked with unknown and duplicate names. Codex and DeepSeek paths not exercised.


## 2026-10-14 — Codex and DeepSeek fixes in the FuelBuddy review loop
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `CHANGELOG.md`
**Change:** Codex: one shared `codex_args` builder (`--approve-for-me`, opt-in `CODEX_DANGEROUS_FULL_ACCESS`), timeout logging, `shlex` args. All subprocesses now run with `stdin=DEVNULL` (`codex exec` otherwise hangs waiting for piped stdin). DeepSeek: requested vs reported model recorded in `_provenance`, contradictory model fails, empty `modelUsage` needs `DEEPSEEK_ACCEPT_UNVERIFIED=1`, one retry with `deepseek-chat` on `unrecognized_model` (not on 401), Anthropic consolidator always uses `~/.claude-anthropic`. Write probes for all backends (nonce, orchestrator-verified). Proposal D1, D2, D4, D10.
**Remaining:** DeepSeek preflight still fails with 401 using the key in `~/.claude/settings.json`; HUMAN must export a valid `DEEPSEEK_API_KEY`. Resume safety, git worktree, mocked tests, provenance in CONSOLIDATION.
**Verification:** Live preflight passed for CHATGPT (write probe) and GROK; DeepSeek live probe returned 401 (invalid key), so the model/telemetry path is untested.


## 2026-10-14 — resume safety, git guards and tests for the FuelBuddy review loop
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `projects/fuelbuddy/charging-diagnostic/automation/tests/test_review_loop.py`, `projects/fuelbuddy/charging-diagnostic/README.md`, `CHANGELOG.md`
**Change:** Reviews must end with `Result: complete` and carry findings or `Findings: none` (clean reviews accepted, partial ones rejected). A step is skipped only when complete and pushed; complete-but-unpushed resumes at push; unfinished files stop the loop. Clean tree/index checked before each step, unrelated staged paths refused, local branch never reset, pending local commits pushed on start, lockfile against overlapping loops. Reviewer provenance (requested vs served model) is passed to the consolidator. 17 mocked tests. Proposal D7–D9 (partial), D12.
**Remaining:** Dedicated git worktree (D9) deferred: the lockfile plus clean-tree checks cover the concrete failure cases; completion records tied to a spec hash (D7) replaced by git-based "pushed with identical content" check. One-round live integration test (Phase 4).
**Verification:** `python3 -m unittest discover -s tests`: 17 passed. Live preflight passed for GROK, CHATGPT, DEEPSEEK (served model verified) and the Anthropic consolidator.


## 2026-10-14 — Codex cost report, Fast tier, live Grok log; round-2 first pass archived
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `projects/fuelbuddy/charging-diagnostic/automation/run_review_loop.sh`, `projects/fuelbuddy/charging-diagnostic/automation/tests/test_review_loop.py`, `projects/fuelbuddy/charging-diagnostic/reviews/round-2-pass1/`, `CHANGELOG.md`
**Change:** Each Codex review now logs requests, input/cached/fresh/output tokens, largest request vs context window, and estimated cost summed per request (standard or Fast tier prices for gpt-6.1-sol, long-context tier reported as an upper bound; usage JSON saved). `CODEX_SERVICE_TIER=fast` and `FAST=1` in the launcher select Codex Fast and Grok 4.7 high-fast. The Grok runner now writes to its log live. The slow first pass of round 2 (CHATGPT and DEEPSEEK, commits 8fb57e5 and c3d2b46) was moved to `reviews/round-2-pass1/` so round 2 can be rerun on fast settings; it stays for comparison and is not read by the loop.
**Remaining:** Rerun round 2 with FAST=1; compare pass 1 vs pass 2. Whether `service_tier="fast"` actually engages the Fast tier is unverified (Codex accepts it silently, session files do not record the tier).
**Verification:** `python3 -m unittest discover -s tests`: 21 passed. Cost formula reproduces the 11:09 CHATGPT session ($0.204 standard-tier estimate).


## 2026-10-14 — HUMAN decision FB-D1: MVP market is Europe
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `projects/fuelbuddy/charging-diagnostic/README.md`, `projects/fuelbuddy/charging-diagnostic/automation/review_loop.py`, `CHANGELOG.md`
**Change:** Recorded HUMAN's decision FB-D1 ("The MVP market is Europe") in a new `decisions.md`. Review and consolidation prompts now tell reviewers to treat listed decisions as settled and CLAUDE to apply them to `spec.md` at the next consolidation, without inventing precision HUMAN did not give (EU vs EEA/UK stays an open question). `spec.md` is not edited by hand; it still shows FB-D1 as pending until round 3 consolidates.
**Remaining:** FB-D2–FB-D7 still open; FB-D4 (legal basis) is not settled by this decision. Round 3 not yet run.
**Verification:** 21 tests pass; both prompts reference `decisions.md`.


## 2026-10-14 — FB-D1 clarified: UK, Switzerland and every country with an API
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `CHANGELOG.md`
**Change:** HUMAN clarified FB-D1: Europe = EU/EEA plus the UK and Switzerland, and generally all countries that have an API. Recorded in `decisions.md` with consolidator notes: "has an API" is the inclusion rule; which API, launch order and handling of countries without one stay open questions for HUMAN.
**Remaining:** FB-D2–FB-D7 open. Round 3 not yet run.
**Verification:** Document-only edit.


## 2026-10-14 — HUMAN decision FB-D7: Option A (documented ranking ordering)
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `CHANGELOG.md`
**Change:** Recorded HUMAN's decision FB-D7 = Option A (ship the documented ordering; calibration deferred to §6.3; ranking not blocked) with consolidator notes. `spec.md` unchanged until the next consolidation.
**Remaining:** FB-D2–FB-D6 open. Round 3 not yet run.
**Verification:** Document-only edit.


## 2026-10-14 — HUMAN decision FB-D2: approved with amendments
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `CHANGELOG.md`
**Change:** Recorded HUMAN's decision FB-D2 (safety clearance semantics approved with five amendments: fail closed on unknown restrictions, authorized actor per class, users can raise but not clear, per-scope restrictions with most-restrictive-wins, re-verification prompt instead of expiry) with the restriction-to-behaviour mapping. `spec.md` unchanged until the next consolidation. The re-verification period is left as an open question for HUMAN.
**Remaining:** FB-D3–FB-D6 open. Round 3 not yet run.
**Verification:** Document-only edit.


## 2026-10-14 — HUMAN decision FB-D3: approved as recommended, simplified
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `CHANGELOG.md`
**Change:** Recorded FB-D3: the app never originates an emergency-stop instruction; hazard handling is driven by what the driver (or an operator feed) reports; add an OEM-sourced stuck-connector playbook; add a hazard screening question at the start of every session. Recorded on HUMAN's "continue" after the recommendation was presented. `spec.md` unchanged until the next consolidation.
**Remaining:** FB-D4–FB-D6 open. Round 3 not yet run.
**Verification:** Document-only edit.


## 2026-10-14 — HUMAN decision FB-D5: approved as recommended
**Agent:** CLAUDE
**Files:** `projects/fuelbuddy/charging-diagnostic/decisions.md`, `CHANGELOG.md`
**Change:** Recorded FB-D5: offline/unverifiable-package behaviour degrades by risk (safety content always available, restrictions never cleared offline, playbooks with a staleness notice, withdrawn items shown as unverified, LLM explanations unavailable offline). The hard staleness limit is left as an open question for HUMAN. `spec.md` unchanged until the next consolidation.
**Remaining:** FB-D4 and FB-D6 (legal) open. Round 3 not yet run.
**Verification:** Document-only edit.


## 2026-10-24 — JarvisBot changed to an option debate
**Agent:** CHATGPT
**Files:** `projects/jarvis/JarvisBot/README.md`, `projects/jarvis/JarvisBot/workflow.json`
**Change:** HUMAN requested comparison of the proposed options, a real debate where every reviewer challenges every peer and answers challenges, and a reasoned Claude recommendation. Start fresh at round 2 while preserving round-1 reviews and logs. HUMAN priorities: user-friendly bot declaration, minimum total costs, maximum functionality/skills support, and a library of reusable named agent personas with configurable outlook, procedures, goals and attitude. No implementation path selected. Full specifications begin only after HUMAN chooses.
**Verification:** Workflow JSON and README match the option-debate engine contract; proposal unchanged.
**Remaining:** Run the debate, then HUMAN selects the preferred implementation.


## 2026-10-24 — JarvisBot autonomy, deliberate speech and observer requirements
**Agent:** CHATGPT
**Change:** Recorded HUMAN's additional priorities in workflow.json and README: autonomy, deliberate selective communication including silence, constructive excellence-driven collaboration, and an observer bot proposing strategy refinements for each bot. These are assessment criteria for the debate, not an implementation selection.
**Verification:** Updated while the engine was held at preflight, before any round-2 reviewer received a domain prompt.


## 2026-10-24 — JarvisBot model portability and connector verification
**Agent:** CHATGPT
**Change:** Recorded HUMAN's primary goal: switch persistent bots across AI backends as credits run out, with task-specific good-enough evaluation and safe continuation. Added phone, WhatsApp Business, image/video specialist requirements and a per-option connector replication audit. Added dated primary-source context, with hosted-auth/tool-bridge distinctions and explicit untested status. Preserved the failed initial status-check logs. No architecture or model choice made for HUMAN.
**Verification:** Primary documentation and source READMEs read; no candidate or connector locally tested. All model backends passed the earlier live preflight.


## 2026-10-24 — Existing Grokbot team as migration baseline
**Agent:** CHATGPT
**Change:** Added HUMAN's screenshot roster and observed collaborative workflows as assessment context. Preserve names, role continuity, rooms, shared pages and routines across model switches. Actual personas/memories/provider assignments remain unverified. Evidence arrived during the first proposal pass; challenges and responses must explicitly revisit it.
**Verification:** Screenshot inspected; no changes made to actual Grokbot bots or their instructions.


## 2026-10-24 — Lean UI, peer task ratings and token accountability
**Agent:** CHATGPT
**Change:** Added HUMAN requirements for a lean screenshot-inspired interface, evidence-based peer ratings of task usefulness/rework/quality/efficiency, and token/cost attribution across discussions, tasks, observer work and spawned cloud agents. Require explicit telemetry gaps, measured-versus-estimated distinctions and parent/child accounting without double counting. These remain option-assessment criteria, not selected implementation specifications.
**Verification:** Requirements recorded in workflow priorities and assessment context; active review preserved.


## 2026-10-24 — JarvisBot round-2 independent option proposal
**Agent:** CHATGPT
**Files:** `projects/jarvis/JarvisBot/reviews/round-2/CHATGPT.md`, `CHANGELOG.md`
**Change:** Compared all four original paths against HUMAN's complete priorities. Provisionally preferred option 3 with Akeru as lead candidate; explained the strongest objection and why DIY is the closest runner-up. Added dated primary-source evidence, per-option service capability matrices, cost/authentication distinctions, a concrete reconstruction-platform finding, and bounded tests that could reverse the preference. Preserved HUMAN's choice and the no-deletion constraint; no full specification or implementation selected.
**Verification:** Read required context and round-1 reviews; did not read round-2 peer files. Retrieved primary documentation and inspected selected Akeru source/docs. No installs, authenticated integration tests, paid calls, git commands or edits outside the two permitted files.
**Remaining:** Peer challenges/responses and consolidation, then HUMAN chooses. Provider continuity, entitlements, connector inventory and full specialist workflows remain unproven.
