# DEEPSEEK review — round 1

Reviewed `spec.md` v0.3, `decisions.md`, `docs/01`–`15`, and the eight records in `evals/fixtures/`, validated against the schemas in `docs/04`. Read-only review: no git command, install, deployment, authentication, spend or live integration was performed. AKIRA-D1–D6 are treated as settled and are not re-opened. There is no previous consolidation for round 1; the findings below are independent.

Findings: five major, eleven minor.

---

### DEEPSEEK-1 · The backup runbook prunes the backup set

**Severity:** major

**Finding:** `docs/12-operations.md` §5.2 instructs `rsync -a --delete-after ... /backup/files/`. `--delete-after` makes the backup destination an exact mirror of the live source. Two concrete failures follow: (a) any source file temporarily absent (partial mount, interrupted restore, operator move) is deleted from the backup; (b) after a HUMAN-named purge removes a bot's files from live state, the next backup run deletes the pre-purge copy from `/backup/files/`, defeating the "backup first" guarantee the purge procedure relies on. This contradicts AKIRA-D2 and the same document's §10 statement that "rotation of backup files is a HUMAN-named operation". The backup procedure itself must not delete from the backup destination.

**Proposed correction:** Remove `--delete-after`; make the file backup append-only or write a new timestamped snapshot directory per run. If pruning is ever wanted, make it a separate, explicit HUMAN-named rotation, never part of the automated backup. Add a test: create a backup, remove a source file (simulating a purge), run the backup again, assert the old backup copy still exists.

**Evidence:** `docs/12-operations.md` §5.2 (lines 136–144; flag at 142), §10 (line 308); `decisions.md` AKIRA-D2; `spec.md` §2.1.

**Confidence:** high

---

### DEEPSEEK-2 · The upstream hard-delete command is left callable; only the UI path is removed

**Severity:** major

**Finding:** The deletion design removes the retention sweep and makes the UI "delete" archive, and adds `purge.request` with named ids, backup-first, `destructive` scope and audit (`docs/02` B-33, `docs/03` ADR-08, `docs/05` §1.5). But Akeru's `bot.delete` decider command still exists upstream (`docs/02` B-33, `docs/14` §2), and the specification never requires it to be removed or gated; the only P0 work item is "remove/guard the hard-delete UI path" (`docs/11` P0 item 2). Because `docs/05` §8.1 requires scopes to be enforced server-side and says "UI gating is presentation only", a client with the command's scope can still dispatch `bot.delete` and bypass the purge safeguards. T-12 tests only that a timer does not dispatch `bot.delete`; it does not test a direct command. The hard rule is therefore enforced at the presentation layer, not at the authority.

**Proposed correction:** In the decider, remove `bot.delete` from the command surface (it is already absent from the Akira command table in `docs/05` §1.1) or make it an alias that requires the `purge.request` controls. Add a server-level test that a direct `bot.delete` is rejected unless it carries explicit ids, a verified backup, the `destructive` scope and an audit record.

**Evidence:** `docs/02` B-33 (line 98) and X-02 (line 126); `docs/03` ADR-08 (lines 234–251); `docs/05` §1.1 commands (24–28), §1.5 (line 78), §8.1 (line 257); `docs/10` T-12 (lines 183–194); `docs/11` P0 (line 48); `docs/14` §2 (`decider/bots.ts`); `decisions.md` AKIRA-D2.

**Confidence:** high

---

### DEEPSEEK-3 · A quota-exhausted route is recorded as failing the capability floor

**Severity:** major

**Finding:** AK-TRG-13 makes credit exhaustion a cost/availability event and forbids recording it as an adequacy decision. `RouteDecision.candidates` (`docs/04` §4.2) has no availability field: it records `meetsFloor`, `estimatedCost`, `estimateBasis`, `support` and `note`. The representative `evals/fixtures/route-decision.json` sets the Codex candidate to `meetsFloor: false` with the note "account quota exhausted at decision time", while its own `chosen.alternativesRejected` says "quota exhausted (failure class: quota_exhausted, not capability)". The same record thus asserts and denies a floor failure. A policy reading `meetsFloor` would treat the route as inadequate and escalate to a stronger/more expensive model instead of pausing, exactly the silent quality change AK-TRG-13 and AK-RTE-13 prohibit.

**Proposed correction:** Add an availability dimension to the candidate record (for example `available: boolean` plus `availabilityReason`/`availabilitySource`), keep `meetsFloor` strictly capability-based, update the schema and the fixture, and add a test that a quota-blocked route is recorded as `meetsFloor: true, available: false` and causes a pause, not an escalation.

**Evidence:** `spec.md` AK-TRG-13 (615–617), AK-RTE-13 (502–506); `docs/04` §4.2 candidate schema (208–216) and error mapping (265–267); `evals/fixtures/route-decision.json` lines 15, 20–23.

**Confidence:** high

---

### DEEPSEEK-4 · Coordination overhead has no category; triage is counted twice

**Severity:** major

**Finding:** AK-ACC-07 requires observer, peer review, spec writing and handoffs to be a visible category, not absorbed into delivery, and AK-ACC-14 requires delivery cost to be separated from review/observer overhead. `UsageRecord.category` is closed to `turn|tool|delegation|routine|review|observer|media|other`; there is no `coordination`, `planning` or `triage` value, and `CostSummary.byCategory` is keyed by that enum. The worked example consequently records the triage turn as a `turn` (use-9), which is delivery, but the UX's `overhead $0.45` includes triage. The result cannot be reconciled: the example's "Overhead" line is $0.30 (review+observer, no triage), the UX and `task.json` say $0.45 (includes triage), and "delivery-only" $2.82 includes the same $0.15 triage that the $0.45 overhead includes. Delivery plus overhead therefore exceeds the exclusive total. The UX's separate `coordination $0.80` line (`docs/06` §7) also has no record that can produce it.

**Proposed correction:** Add `coordination` (and either a `planning`/`triage` category or define triage as coordination) to the closed enum and to `CostSummary.byCategory`; classify use-9 as coordination; define delivery-only as `turn`+`tool`; then delivery $2.67 + overhead $0.45 = exclusive $3.12. Update `docs/09` §4 and §9, `docs/06` §3/§7, `task.json` and `usage-record.json`, and add a T-09 assertion that every record belongs to exactly one category and delivery + overhead + child = inclusive.

**Evidence:** `spec.md` AK-ACC-07 (993–994), AK-ACC-14 (1019–1021); `docs/04` §5 (330, 343–350); `docs/09` §4 (91, 95–111), §9; `docs/06` §3 (85), §7 (185); `evals/fixtures/task.json` cost block; `evals/fixtures/usage-record.json`.

**Confidence:** high

---

### DEEPSEEK-5 · The accounting example and usage view sum unlike units, then route selection compares them

**Severity:** major

**Finding:** `docs/09` §1.6 states that API dollars, subscription-equivalent dollars, plan percentages and credits are different units that may be shown side by side but "never summed into one 'spend' number"; §8 repeats that the route view must not compare subscription-equivalent to API dollars "as if equal". The normative worked example (§4, made normative by AK-ACC-05) does exactly the forbidden sum: use-2 is `subscription-equivalent` $1.84, the other costed records are API dollars, and "Exclusive T-142" is reported as a single $3.12 (and inclusive $3.50); `task.json` stores `cost.exclusive.amount: 3.12` with `provenance: "mixed"`. The UX usage view likewise shows a single team "total $41.20" while listing `claude $21.3 (subscription-equivalent)` and `deepseek $6.8 (API)`, then says they are never summed. AK-TRG-10 then selects routes by "lowest expected total delivery cost" across candidates priced in those different units (the route-decision fixture prices Codex `subscription-equivalent` and Claude/DeepSeek in API dollars), and no routing comparison basis is defined. The headline cost-per-accepted-task metric (AK-TRG-14) is therefore a mixed-unit number. AKIRA-D5 permits the subscription routes; the defect is the unit arithmetic, not the permission.

**Proposed correction:** Separate the units at every level: report API cash, subscription-equivalent usage, and plan/credit meters as distinct amounts, never one "total". Define an explicitly named routing comparison unit (for example "API-equivalent estimate") and use it only for route selection, labelled as not spend; or restrict cost-based selection to routes in the same auth class and make cross-class choice a policy/operator decision. Update the worked example, the UX totals, the fixtures, and T-09 to assert the unit split.

**Evidence:** `spec.md` AK-ACC-04 (979–982), AK-ACC-05 (984–987), AK-TRG-10 (600–602), AK-TRG-14 (619–622); `docs/09` §1.6 (24–26), §4 (95–108), §5 (130–145), §8 (188); `docs/06` §7 (178–191); `evals/fixtures/task.json` lines 51–55; `evals/fixtures/usage-record.json`; `evals/fixtures/route-decision.json` line 15.

**Confidence:** high

---

### DEEPSEEK-6 · Requirement count, traceability and version metadata are stale

**Severity:** minor

**Finding:** `spec.md` §0 says "All 204 requirements"; the file defines 206 requirement IDs (the v0.3 additions AK-SKL-13 and AK-SKL-14 are not reflected in the count). The traceability matrix in `docs/10` §5 maps `AK-SKL-01..12` only, so the two new MUSTs (the v1 catalogue and the connector-availability gate) have no acceptance/test row, despite §0's claim that every requirement has an ID used by the matrix. The footer still says "Version 0.1 — first complete draft" while the header and companions are v0.3.

**Proposed correction:** Update the count to 206 (or generate it), add AK-SKL-13/14 rows with their tests (catalogue completeness, a negative "advertise a conditional skill before its connector is workflow-verified" test), and make the footer version match the header.

**Evidence:** `spec.md` §0 line 25, AK-SKL-13/14 (796–806), footer (1411); `docs/10` §5 (253); `docs/15` §3/§5.

**Confidence:** high

---

### DEEPSEEK-7 · CPAT formula can double count overhead; the usage view mislabels inclusive cost

**Severity:** minor

**Finding:** `docs/09` §9 defines `CPAT = Σ exclusive delivery cost + Σ child delivery cost + Σ review/observer/coordination cost ÷ accepted tasks`. The worked example's "exclusive" $3.12 already contains the review, observer and triage records, and the example's CPAT $3.50 is exclusive + child; read literally, the formula adds review/observer/coordination a second time. Separately, the usage view says `T-142 $3.12 incl. child`, but the worked example and the task inspector give inclusive $3.50 (exclusive $3.12 + child $0.38); $3.12 is the exclusive total and cannot be "incl. child".

**Proposed correction:** Define "exclusive delivery" in the formula as `turn`+`tool` only (or remove the separate review/observer/coordination term), and make the usage view use inclusive $3.50 for the "incl. child" row (or drop the "incl. child" label). Add both checks to T-09.

**Evidence:** `docs/09` §4 (95–108), §9 (200–206); `docs/06` §7 (182), §3 (85); `docs/10` T-09 (142–153); `evals/fixtures/task.json`.

**Confidence:** high

---

### DEEPSEEK-8 · CostSummary coverage has no bucket for subscription-equivalent

**Severity:** minor

**Finding:** `CostSummary.coverage` counts only `reported`, `estimated` and `unknown`, while `UsageRecord.measurement` and cost provenance include `subscription-equivalent`. A subscription record therefore belongs to no coverage bucket. The fixture shows the consequence: `task.json` reports exclusive coverage `{reported: 3, estimated: 3, unknown: 0}` for six costed records, but use-2 is `measurement: provider-reported` with `cost.provenance: subscription-equivalent`; counting it as reported gives 4/2, and separating it gives 3 reported + 2 estimated + 1 subscription that the schema cannot count. The 3/3 split is not derivable without counting the subscription record as an estimate, which contradicts its measurement. The coverage formula in `docs/09` §8 also lacks parentheses (`reported + estimated / (...)`), so it computes `reported + (estimated / total)` rather than `(reported + estimated) / total`.

**Proposed correction:** Add a `subscription` bucket to `CostSummary.coverage`, define the counting rule per record, fix the formula's parentheses, and regenerate the fixture's coverage numbers with a test that the buckets sum to the costed records and that a subscription record is neither silently "reported" nor lost.

**Evidence:** `docs/04` §5 (331, 348); `docs/09` §5 (134), §8 (193–194); `evals/fixtures/usage-record.json`; `evals/fixtures/task.json` lines 51–54.

**Confidence:** high

---

### DEEPSEEK-9 · `prompt-injected` cannot be marked verified

**Severity:** minor

**Finding:** AK-SKL-04's support levels are `native-verified`, `native-unverified`, `projected-unverified`, `prompt-injected`, `unsupported`. `docs/05` §3's rule says a support level without a matching `verify` record is downgraded to `*-unverified`, and `docs/15` §4 requires `prompt-injected` to be verified on the non-native routes, but the enum has no `prompt-injected-verified`/`prompt-injected-unverified` pair (and no `projected-verified`). The level alone therefore cannot tell a tested prompt-injected route from an untested one; the fixture lists `deepseek/deepseek-chat: "prompt-injected"` with no `supportEvidence`, and the UI cannot show whether it was executed.

**Proposed correction:** Make verification orthogonal to the execution mechanism (add the two prompt-injected levels, or a separate `verified` flag plus evidence reference), make the downgrade rule total, and update the fixture and `SKILLS.md` rendering.

**Evidence:** `spec.md` AK-SKL-04 (756–759), AK-SKL-06 (765–768), AK-SKL-12; `docs/05` §3 (154–157); `docs/15` §4 (95–101); `evals/fixtures/skill-package.json`.

**Confidence:** high

---

### DEEPSEEK-10 · Readiness criteria carry no evidence links

**Severity:** minor

**Finding:** AK-TRG-06 requires readiness to be evidenced, not asserted, and AK-TRG-07 requires "per-criterion evidence links". `ReadinessResult.criteria` records only `pass|fail|partial` values (plus ellipses for the criterion text) and `risks`; there is no evidence field per criterion. The fixture marks all nine criteria `"pass"` with `risks: []`, so a `pass` is indistinguishable from an assertion — the exact failure mode the requirement targets.

**Proposed correction:** Add an evidence link (or an `{outcome, evidence, note}` object) to each readiness criterion, update the fixture, and make T-10 fail when a `pass` criterion has no evidence link.

**Evidence:** `spec.md` AK-TRG-06 (579–584), AK-TRG-07 (585–589); `docs/04` §4.3 (271–280); `evals/fixtures/task.json` `triage.readiness`; `docs/10` T-10 (155–167).

**Confidence:** high

---

### DEEPSEEK-11 · The documented silence set is wider than the normative list

**Severity:** minor

**Finding:** AK-COL-05 enumerates the only justified silence reasons. `docs/08` §3.2 declares a different "closed set" and adds `policy_hold` and `no_evidence`. `policy_hold` maps to the normative "explicit room rule" clause, but `no_evidence` ("bot would have to speculate") is not limited to the normative "not addressed and has no evidence to add" case: a directly addressed bot with no evidence could satisfy the code, while T-06 lists "silence on a direct question" as a fail signal. The two closed sets must be identical for the command guard (`turn.complete-silent` takes a code from the closed set) to be enforceable.

**Proposed correction:** Add `no_evidence` to AK-COL-05 with the `not_addressed` guard, or remove it and map that condition to `not_addressed`; state that `policy_hold` is the explicit-room-rule case. Add a policy-table test that every code maps to an AK-COL-05 clause and that a direct question cannot be silent.

**Evidence:** `spec.md` AK-COL-05 (833–838); `docs/08` §3.2 (79–93); `docs/05` §1.3 `turn.complete-silent` (line 55); `docs/10` T-06 (102–113).

**Confidence:** high

---

### DEEPSEEK-12 · A rating's author can resolve a dispute about that rating

**Severity:** minor

**Finding:** AK-RAT-05 lets the rated bot or a HUMAN dispute a rating. `docs/08` §5.4 resolves disputes with "a reviewer other than the disputant". If the rated bot disputes, the rating's author is a reviewer other than the disputant and can resolve their own rating; the dispute mechanism can therefore be captured by the person whose rating is contested. The observer rule already requires an approver distinct from the observer (`docs/04` invariant 7), and ratings are used as routing evidence (AK-TRG-11), so independence matters.

**Proposed correction:** Require the resolver to be distinct from both the rating author and the disputant (or a HUMAN), record the resolver, and add a T-07 case where the rating author attempts to resolve and is rejected.

**Evidence:** `spec.md` AK-RAT-05 (904–906), AK-TRG-11 (604–607); `docs/08` §5.4 (238–245); `docs/04` §8 invariant 7 (396–397); `docs/10` T-07.

**Confidence:** high

---

### DEEPSEEK-13 · Export and restore are not in the audit requirement

**Severity:** minor

**Finding:** AK-SEC-08 enumerates the audited actions: credential changes, permission changes, approvals, destructive actions, connector actions, route overrides, template/persona activation and observer activation. `export.create` copies the whole team (memory, tasks, ratings, usage, checkpoints) into a bundle, and `restore.apply` creates or replaces state on a target; both are consequential, but neither is in the audit list or the security suite. Export is also the main confidentiality egress path, and restore is the main way a wrong bundle can overwrite a target.

**Proposed correction:** Add export and restore to AK-SEC-08 (actor, scope, bundle id, destination, checksum, result), and add a security test that both produce audit records and that an export's destination and included scopes are visible.

**Evidence:** `spec.md` AK-SEC-08 (1195–1198); `docs/05` §1.5 (74–76); `docs/12` §5; `docs/10` §6 (269–282).

**Confidence:** high

---

### DEEPSEEK-14 · Traceability phases contradict the backlog; routing depends on a later phase

**Severity:** minor

**Finding:** The phase column in `docs/10` §5 does not match the phase plan in `docs/11`: for example AK-IDE is phase 2 vs P1, AK-TSK phase 3 vs P2, AK-TRG phase 4 vs P3, AK-SKL phase 5 vs P4, AK-ACC phase 4 vs P5, AK-OBS phase 7 vs P6, AK-SPC phase 8 vs P7, and AK-SEC phase 9 vs P10. Separately, `docs/11` P3 says it depends on "P5 partly (cost estimates)" while the phase diagram places P5 after P3, so the plan does not show how P3's cost-based selection is delivered before the accounting/price-table work it depends on.

**Proposed correction:** Use one phase numbering in both documents, and move the estimate/price-table inputs P3 needs into P2 or an explicit P3 prerequisite (or split P5 and sequence the estimate part before P3).

**Evidence:** `docs/10` §5 (245–265); `docs/11` §1 diagram (22–31), §5 (111–126), §7 (150–163).

**Confidence:** high

---

### DEEPSEEK-15 · The vertical slice ships a connector-conditional skill without its connector

**Severity:** minor

**Finding:** `docs/15` §5 says the first slice ships S11 `sheet-ops`, and describes it as proving native execution and resource access "using the existing fixture". S11's own row says it requires the Google Sheets connector (`sheet.read`/`sheet.write`, P8), and §3 says a conditional skill "must not be listed as available until the corresponding connector reaches workflow-verified status". The slice in `docs/11` §13 has only "one stub connector", and `docs/15` §0 says the only existing fixture is the `sheet-ops` package example; the referenced validation fixture `fixtures/skill-sheet/` does not exist, and the package points at `evals/fixtures/sheet-fixture.json`, which is also absent. So the slice either violates AK-SKL-14 or cannot run S11. The conditional table also omits the triggers and expected route support that AK-SKL-13 requires for every catalogue entry.

**Proposed correction:** Either put the real Sheets connector (and its fixture) in the slice and adjust the effort/exit criteria, or make the second slice skill a connector-free skill (S2/S4) and defer S11. Add the missing triggers/route-support columns and real fixture paths.

**Evidence:** `spec.md` AK-SKL-13/14 (796–806); `docs/15` §0 (12–15), §3 (74–87), §5 (105–114); `docs/11` §13 (252–274); `evals/fixtures/skill-package.json`.

**Confidence:** high

---

### DEEPSEEK-16 · Legacy usage categories are not mapped by the migration

**Severity:** minor

**Finding:** Akeru's usage ledger records categories `turn/tool/observer/reflector/extraction/recall/routine/delegated` (V, `docs/14` §5). Akira's `UsageRecord.category` is a different closed enum: `turn/tool/delegation/routine/review/observer/media/other`. `docs/04` §7's migration only adds columns and says existing rows stay valid with nulls; it never maps `reflector`, `extraction`, `recall` or `delegated`, so post-migration category roll-ups will either reject those rows or classify them as `unknown`/`other` and lose the existing history that AK-ACC-01/02 and the exclusive/inclusive totals rely on.

**Proposed correction:** Define an explicit legacy-to-Akira category mapping (for example delegated→delegation, reflector→observer, extraction/recall→other) with a deterministic rule for unknown values, and add a migration test that a pre-migration row retains a valid category and is included once in exclusive totals.

**Evidence:** `docs/14` §5 (147); `docs/04` §5 (330), §7 (369–375), §1 closed-enum rule; `docs/09` §1.1; `spec.md` AK-ACC-01/02.

**Confidence:** high

---

Result: complete
