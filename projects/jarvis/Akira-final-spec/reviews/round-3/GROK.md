# GROK review — round 3

Reviewed `spec.md` v0.5 after `reviews/round-2/CONSOLIDATION.md` and `reviews/round-1/CONSOLIDATION.md`, with `decisions.md`, all fifteen companion documents and all eight JSON fixtures in the manifest scope. AKIRA-D1–D6 stay fixed. U4–U16 are carried forward and are not raised again. The absent `assets/` directory is already recorded and is not raised again. This is a specification review: observations are from the documents read as text. A heading count of `**AK-…**` requirements in `spec.md` is 209. No git command, installation, authentication, deployment or live integration was run.

Findings: one major and eight minor; no blocking findings.

### GROK-1 · A send can commit before the ledger says `dispatched`
**Severity:** major
**Finding:** AK-TSK-10 and `docs/04` §4.4 define `intent` as "action decided, not sent" and `dispatched` as "request possibly reached the provider", but nothing requires the `dispatched` record to be durable *before* `ConnectorAdapter.execute` runs. AK-TSK-11, AK-TSK-14, the retry/fallback columns and the `task.start` guard all key off a ledger state of `dispatched` or `unknown`. An implementation that appends `intent`, calls the connector, and appends `dispatched` only after the call returns will, if the process dies in that window, leave a sent action in `intent`. Startup reconciliation ignores `intent` and may dispatch the queued attempt again (AK-TSK-14: "queued work never dispatched (dispatch or mark)"). T-03 and F-08 start only after the ledger is already `unknown`, so they do not catch this window. N3 closed the post-dispatch retry path; it did not close the pre-record window.
**Proposed correction:** In AK-TSK-10 and `docs/05` §5, require this order: persist `intent`, then durably transition to `dispatched`, and only then invoke the connector. On recovery, an `intent` whose attempt is no longer live is treated as possibly sent (reconcile; never auto-resend) unless the executor can prove the call was never started. Add a fault case for a crash after the connector call begins and before the `dispatched` record, and extend T-03.
**Evidence:** `spec.md` AK-TSK-10, AK-TSK-11, AK-TSK-14; `docs/04-data-model.md` §4.4; `docs/05-interfaces.md` §5 (`execute` returns `confirmed|failed|unknown` with no prior-durable-`dispatched` rule) and §6; `docs/10-tests-and-acceptance.md` T-03 and F-08; `evals/fixtures/action-record.json` (state already `unknown`). Static inspection only.
**Confidence:** high

### GROK-2 · The specification-led default ranks cost across auth classes
**Severity:** minor
**Finding:** AK-TRG-10 requires cost ranking within one auth class unless the labelled routing-comparison unit is enabled (U16, default off). `docs/04` §4.3 assigns `specification-led` to "the lowest-expected-cost" floor-meeting candidate with no auth-class restriction and no rule for overlapping `MoneyRange`s. Route candidates, `UsageRecord.route` and `RouteSnapshot` do not carry `authClass` (only `ProviderCapabilities` does), so the guard cannot be checked. `route-decision.json` mixes `subscription-equivalent` (120–240 and 100–200, ranges overlap) with `price-table` (30–70) and marks two candidates `specification-led`, while the default procedure names one lowest-cost floor-meeting candidate.
**Proposed correction:** Record `authClass` on each candidate and on the usage-route snapshot. Assign `specification-led` only inside one auth class (or only through the labelled comparison unit when that policy is on). Define range ordering (for example, compare `lowMinor`, and treat overlap as unordered so the operator chooses). Give the fixture one `specification-led` candidate consistent with that rule.
**Evidence:** `spec.md` AK-TRG-07, AK-TRG-10, AK-RTE-02; `docs/04-data-model.md` §3 `RouteDecision`, §4.3, §5 `UsageRecord.route`; `docs/09-accounting.md` §1.7; `evals/fixtures/route-decision.json`.
**Confidence:** high

### GROK-3 · Candidate `support` is not the skill-floor input
**Severity:** minor
**Finding:** `meetsFloor` is defined to include "skill support >= requiredSkillSupport", but the candidate field `support` is `"verified"|"assumed"|"unknown"`, which is not the AK-SKL-04 level set and is not a per-skill `SkillSupportEntry`. `route-decision.json` sets Codex `meetsFloor: true` with `support: "assumed"` while `requiredSkillSupport` is `native-verified`. The `docs/10` §4 invariant ("no route with `meetsFloor: true` below the required skill support") has no field it can evaluate.
**Proposed correction:** Replace `support` with the per-required-skill `SkillSupportEntry` (mechanism, verified, evidence) that the floor check uses. Align the Codex fixture with that entry, or set `meetsFloor: false` if the entry is not `native-verified`.
**Evidence:** `docs/04-data-model.md` §2 `SkillSupportEntry` and §3 candidate comment; `spec.md` AK-SKL-04, AK-RTE-13; `docs/10-tests-and-acceptance.md` §4; `evals/fixtures/route-decision.json`.
**Confidence:** high

### GROK-4 · The checkpoint backup step writes into a directory it never creates
**Severity:** minor
**Finding:** `docs/12` §5.2 does `mkdir "$GEN"` and then redirects `git for-each-ref` and `git bundle create` to `$GEN/checkpoint-refs/…`. No step creates `checkpoint-refs`. With the configuration and registry trees copied beside it, that child directory does not exist, so the shell redirection fails before a ref list or bundle is written. The following `find` manifest cannot list files that were not created. The seven-item gate would then reject the generation, so the failure is closed, but the procedure as written cannot produce item 7.
**Proposed correction:** `mkdir "$GEN/checkpoint-refs"` before the workspace loop, and require each ref-list and bundle command to succeed before the manifest is written. State the empty-workspace result explicitly. Extend T-13 with one workspace that has `refs/t3/checkpoints`.
**Evidence:** `docs/12-operations.md` §5.2 (mkdir of `$GEN` only; lines that write `$GEN/checkpoint-refs/`); §5.1 item 7; `docs/10` T-13. Static inspection of the procedure; no backup was executed.
**Confidence:** high

### GROK-5 · The attempt-outcome contract test cannot pass as written
**Severity:** minor
**Finding:** `docs/10` §3 requires every "Expected attempt outcome" to be a member of `AttemptOutcomeClass`, but that column also holds action state `unknown` (F-08), `idempotent ignore` (F-09), `pending → delivered once` (F-10), watchdog activity (F-07), an invariant rejection (F-14), "no deletion" (F-15) and `n/a` (F-16). Separately, `docs/05` §6 says each error class maps to exactly one attempt outcome, while `docs/04` §4.2 both maps `network` to `failed_network` and overrides any class, once an action is `dispatched`/`unknown`, to "`interrupted` or `failed_unknown`". The membership test and the "exactly one" sentence are not satisfiable without exceptions the spec does not list.
**Proposed correction:** Give the matrix a result kind, and apply enum membership only to attempt outcomes. Name one outcome for the external-effect guard (`interrupted` when the attempt died, `failed_unknown` when acceptance is not established) instead of a disjunction. Point the "exactly one" sentence at that guard.
**Evidence:** `docs/10-tests-and-acceptance.md` §3 F-07–F-10, F-14–F-16 and the membership sentence; `docs/04-data-model.md` §4.2 mapping table; `docs/05-interfaces.md` §6 last paragraph before §7.
**Confidence:** high

### GROK-6 · AK-ACC-05's inclusive formula drops the overhead the worked example includes
**Severity:** minor
**Finding:** AK-ACC-05 says inclusive roll-ups sum "exclusive descendants plus the owner's own turn usage", and the same requirement makes `docs/09` §4 normative. In that example the owner's turn records are use-1+use-2+use-3 = $2.67, so the formula yields $2.67 + child $0.38 = $3.05. The example's inclusive total is exclusive T-142 $3.12 (turns plus tool, review, coordination and observer) + $0.38 = $3.50. Following the formula omits the $0.45 overhead that AK-ACC-07 says must stay visible. N5 fixed the CPAT numerator union; it did not change this sentence.
**Proposed correction:** Replace "the owner's own turn usage" with "the owner's own exclusive records (every category)". Keep the §4 arithmetic as the check: inclusive $3.50, overhead $0.45 inside the exclusive $3.12.
**Evidence:** `spec.md` AK-ACC-05, AK-ACC-07; `docs/09-accounting.md` §4 queries (exclusive $3.12, overhead $0.45, inclusive $3.50). Arithmetic is over the published worked example, not a vendor price.
**Confidence:** high

### GROK-7 · Integer currency minor units have no sub-cent rounding rule
**Severity:** minor
**Finding:** `docs/04` §1 stores every cost as an integer number of currency minor units and forbids stored decimals. Nothing says how a price-table estimate smaller than one minor unit is rounded before it is stored on a `UsageRecord`. A synthetic series of 100 turns at USD 0.004 each totals USD 0.40 if the sum is rounded once; rounding each record to the nearest cent first stores 0; rounding each record up stores USD 1.00. Those three results change task totals and any route comparison that reads the ledger. N7 fixed the shape, not the scale.
**Proposed correction:** Keep one fixed-point scale fine enough for per-record price-table products (or retain the unrounded source amount), and round to currency minor units only at a named display or invoice boundary. Add the 100 × 0.004 case to T-09 as a specification example, not as a claim about a vendor's current prices.
**Evidence:** `docs/04-data-model.md` §1 `amountMinor` and §5 `UsageRecord.cost`; `docs/09-accounting.md` §5 (tokens × price list); `spec.md` AK-ACC-04, AK-ACC-16.
**Confidence:** high

### GROK-8 · Silence codes are not one-to-one with the six AK-COL-05 clauses
**Severity:** minor
**Finding:** AK-COL-05 lists six justifying clauses and says the §3.2 codes "map one-to-one" onto them. `docs/08` §3.2 repeats that the sets are identical, then lists eight codes. `not_addressed` and `no_evidence` both restate "not addressed and has no evidence to add". `quiet_hours` and `policy_hold` both restate "quiet hours or an explicit room rule". The parenthetical in AK-COL-05 assigns `no_evidence` and `policy_hold` to those clauses and does not remove the other two codes.
**Proposed correction:** Keep one code per clause (drop or alias `not_addressed` and `quiet_hours`, or split the sixth clause into two clauses and say so). Change the "identical / one-to-one" sentences to match the table that remains. Point the policy-table test at that table.
**Evidence:** `spec.md` AK-COL-05; `docs/08-collaboration-and-accountability.md` §3.2 (eight rows and the sentence under the table).
**Confidence:** high

### GROK-9 · A verified projected skill has no name in the closed support set
**Severity:** minor
**Finding:** AK-SKL-04 closes support levels at `native-verified`, `native-unverified`, `projected-unverified`, `prompt-injected`, `unsupported`. `docs/04` §2 says a verified `projected` or `prompt-injected` entry "renders as such with its evidence", and the mechanism enum includes `projected`. A projected skill that has passed verification therefore has no legal level: `projected-unverified` is false, and `native-verified` would claim native execution. The skill fixture stores `{mechanism, verified}` rather than one of the five names, so the stored shape and the closed set are different contracts. N8 fixed the entry fields, not the level names.
**Proposed correction:** Add `projected-verified` (and, if prompt injection can be verified, a verified label for that mechanism) to AK-SKL-04, and state that only `native-verified` satisfies a native floor. Derive the label from `{mechanism, verified}` in `docs/04` §2, `docs/05` §3 and `docs/15` §4.
**Evidence:** `spec.md` AK-SKL-04; `docs/04-data-model.md` §2 rendered-level sentence; `docs/05-interfaces.md` §3; `evals/fixtures/skill-package.json`.
**Confidence:** high

Result: complete
