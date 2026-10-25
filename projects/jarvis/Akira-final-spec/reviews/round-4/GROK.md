# GROK review — round 4

Reviewed `spec.md` v0.6 after `reviews/round-3/CONSOLIDATION.md` and the prior consolidations, with `decisions.md`, all fifteen companion documents and all eight JSON fixtures in the `loop.json` scope. AKIRA-D1–D6 stay fixed. U4–U16 stay carried forward; no new HUMAN answer is requested. Accepted round-3 corrections, including the write-ahead `intent → dispatched → execute` order and the dead-attempt `intent` block, are not reopened: those passages now agree. This is a specification review. Observations below are from the documents and fixtures read as text.

Read-only checks: 209 unique requirement headings in `spec.md`; all eight fixtures parse as JSON and carry `schemaVersion` `1.0`; the worked-example sums are exclusive $3.12, overhead $0.45, delivery $2.67, inclusive $3.50, and 100 × USD 0.004 = USD 0.40. No validator, runtime, git command, installation, authentication, deployment or deletion was run.

Findings: seven minor; no blocking or major findings.

### GROK-1 · The skill floor is not a decidable predicate
**Severity:** minor
**Finding:** `docs/04-data-model.md` §3 names `capabilityFloor: CapabilityFloor` and defines `meetsFloor` as “skill support >= requiredSkillSupport”, but `CapabilityFloor` is never defined and no order is given over `native-verified`, `native-unverified`, `projected-verified`, `projected-unverified`, `prompt-injected` and `unsupported`. AK-SKL-04 and `docs/05-interfaces.md` §3 decide only one case: `native-verified` is the only level that satisfies a native floor. Spec §7.1’s T3 floor (“native or projected skill”) cannot be written as that comparison. `SkillAdapter.canExecute` returns `SupportLevel`, a name with no definition. `ProviderCapabilities.models[].skills` is closed to `native | prompt-injected | none`, so a probe cannot report the `projected` mechanism AK-SKL-04 requires. A route can therefore be marked above or below the floor only by an implementer inventing the order.
**Proposed correction:** Define `CapabilityFloor.requiredSkillSupport` as a predicate over `SkillSupportEntry` (allowed mechanisms, and whether `verified` is required), not a string comparison. Define `SupportLevel` as the derived label. Add `projected` to the probe skills enum. State that `projected-verified` meets a projected floor and does not meet a native floor. Add a T-10 case for the same candidate against both floors.
**Evidence:** `spec.md` AK-SKL-04 and §7.1 T3; `docs/04-data-model.md` §3 `CapabilityFloor` / `meetsFloor`; `docs/05-interfaces.md` §2.1 `skills` enum and §3 `SupportLevel`; package search finds `CapabilityFloor` and `SupportLevel` only at those declarations.
**Confidence:** high

### GROK-2 · A direct question is both unsilienceable and silenceable
**Severity:** minor
**Finding:** AK-COL-05 ends with “A directly addressed bot cannot be silent on a direct question.” `docs/10-tests-and-acceptance.md` §5 requires a policy test that “a direct question cannot be silent.” `docs/08-collaboration-and-accountability.md` §3.2 attaches that guard only to `no_evidence`. `no_new_work` is allowed “always”; `quiet_hours` is allowed when “policy in force”; `policy_hold` is allowed when the “rule matches.” A direct question during quiet hours passes the table and fails the test, or the reverse. The closed code set does not say which reading wins.
**Proposed correction:** Either apply the direct-address guard to every code, or name the codes that may still end a directly addressed turn (`no_new_work`, `already_answered`, `duplicate`, `waiting_dependency`) and narrow AK-COL-05 and the policy test to that list. Put the chosen guard on `quiet_hours` and `policy_hold`.
**Evidence:** `spec.md` AK-COL-05; `docs/08-collaboration-and-accountability.md` §3.2 allowed-when column; `docs/10-tests-and-acceptance.md` silence traceability row.
**Confidence:** high

### GROK-3 · `transportPermission` is not on the route that dispatch records
**Severity:** minor
**Finding:** AK-RTE-04 and AKIRA-D5 require every route to record `transportPermission`, and `forbidden` or `unknown` disables that route. `docs/05-interfaces.md` §2.1 stores the field on `ProviderCapabilities` only. `RouteSnapshot` and `RouteDecision.candidates` in `docs/04-data-model.md` §3 do not include it, and `evals/fixtures/route-decision.json` does not either. `StartTurnInput.route` is a `RouteSnapshot`. The attempt record therefore cannot show the permission that was supposed to disable the route, and a floor-meeting candidate can be chosen from the decision record alone.
**Proposed correction:** Copy `transportPermission` onto `RouteSnapshot` and each route candidate, reject `forbidden` and `unknown` in the `task.select-route` / `task.start` guards, and add the field to the route-decision fixture and T-02/T-10.
**Evidence:** `spec.md` AK-RTE-04; `decisions.md` AKIRA-D5; `docs/07-integrations.md` §2.3; `docs/05-interfaces.md` §2.1 versus `docs/04-data-model.md` §3 `RouteSnapshot` and candidate fields; `evals/fixtures/route-decision.json`.
**Confidence:** high

### GROK-4 · `always-adequate` and the quota transition name different policies
**Severity:** minor
**Finding:** `RouteDecision.fallbackPolicy` allows `always-adequate`, and that value is never given a decision procedure (it appears once in the package). AK-RTE-12 says automatic fallback for exhausted credits is forbidden unless policy explicitly allows it. `docs/04-data-model.md` §4.1 sends `failed_quota` to `paused` with “no fallback”, and §4.2 says `failed_quota` pauses and asks, with no policy exception. An explicit policy that AK-RTE-12 permits has no state-machine edge, and the recorded enum value has no meaning.
**Proposed correction:** Define each `fallbackPolicy` value against the outcome table. Keep the default `infrastructure-only` as specified. If `always-adequate` is the explicit quota exception, add a guarded edge that still requires the alternate route to meet the floor and that still refuses fallback while an action is `dispatched`, `unknown` or dead-attempt `intent`. If quota fallback is never allowed, delete `always-adequate` and narrow AK-RTE-12.
**Evidence:** `spec.md` AK-RTE-12; `docs/04-data-model.md` §3 `fallbackPolicy` and §4.1 `failed_quota` row; package search finds `always-adequate` only in that union.
**Confidence:** high

### GROK-5 · Effective usage does not say which states are summed
**Severity:** minor
**Finding:** AK-ACC-05 and AK-ACC-09 say queries take one effective revision per logical usage record and never sum superseded tokens. `UsageRecord.state` is `reserved | reported | corrected | released | unavailable` (`docs/04-data-model.md` §5). Nothing says a `released` reservation is excluded, or that a `reported` settlement counts instead of its `reserved` row when they do not share `supersedes`. `docs/09-accounting.md` §12.2 says a crash between completion and settlement is reconciled from the reservation, which is right only if that row is in the effective set once and is replaced, not added, when the provider report arrives. Two implementable filters double-count or drop the in-flight estimate.
**Proposed correction:** Define the effective row as the latest non-superseded revision of a logical key. Exclude `released`. Include `reserved` and `unavailable` in the totals and coverage under their measurement label. Require the settlement to `supersede` its reservation. Add a T-09 case for reserve-then-report and for release.
**Evidence:** `spec.md` AK-ACC-05, AK-ACC-09; `docs/04-data-model.md` §5 `UsageRecord.state`; `docs/09-accounting.md` §7 and §12.2.
**Confidence:** medium

### GROK-6 · A failed-only route makes cost-per-accepted-task undefined
**Severity:** minor
**Finding:** `docs/09-accounting.md` §9 defines CPAT as a division by the number of accepted root tasks attributed to the delivering route. The same section puts failed-attempt cost in that route’s numerator and “not at all” in its denominator. A route whose attempts all failed has a non-zero numerator and a zero denominator. Coverage already defines the empty case as `n/a` (§8). CPAT does not. AK-ACC-16 feeds this metric to routing calibration, so the zero-denominator case the prose describes has no value.
**Proposed correction:** When the accepted-root denominator is 0, CPAT is `n/a` and the cost is still listed. Do not treat it as 0 or as infinite. Add that case to T-09 beside the delivering-route assertion.
**Evidence:** `spec.md` AK-ACC-14, AK-ACC-16; `docs/09-accounting.md` §8 coverage `n/a` rule and §9 route-attribution paragraph and formula.
**Confidence:** high

### GROK-7 · The dispatch command and one fault row drop the dead-attempt intent guard
**Severity:** minor
**Finding:** `docs/05-interfaces.md` §1 says its command tables are the implementation contract. `task.start`’s guards are “one active attempt; compatibility check.” They do not mention an unresolved action. `docs/04-data-model.md` §4.1 and invariant 4 reject `task.start` while any action is `dispatched`, `unknown`, or `intent` on an attempt that is no longer live. The `failed_rate_limit` / `failed_network` transition parenthetical says “no dispatched external action” and omits `unknown` and dead `intent`. F-02’s expected result uses the same shorter set (`dispatched` / `unknown` only). The outcome-mapping table in §4.2 includes dead-attempt `intent`. A command implementation that follows §1.2, or a fault test that follows F-02 alone, can start fallback while that `intent` is still unresolved.
**Proposed correction:** Add the unresolved-action guard (`dispatched`, `unknown`, and dead-attempt `intent`) to `task.start` and `checkpoint.resume`. Use that same set in the §4.1 infrastructure-fallback row and in F-02. Keep the decider invariant as the authority.
**Evidence:** `docs/05-interfaces.md` §1 and §1.2 `task.start`; `docs/04-data-model.md` §4.1 transition row, the paragraph after the table, §4.2 mapping, and §8 invariant 4; `docs/10-tests-and-acceptance.md` F-02; `spec.md` AK-TSK-10, AK-TSK-14.
**Confidence:** high

No accepted round-1–3 correction is reopened. U4–U16 are unchanged. No blocking or major defect: the default dispatch, quota, backup and accounting paths have a single stated rule; the findings are predicates, fields and edge cases the contracts leave unnamed.

Result: complete
