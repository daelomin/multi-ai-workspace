# GROK review — round 1

Reviewed `spec.md` v0.3 (2026-10-25), `decisions.md`, companion documents `docs/01`–`docs/15`, and the eight JSON fixtures under `evals/fixtures/`. AKIRA-D1–D6 are fixed. This registered loop has no previous consolidation. The declared `assets/` directory is absent; no requirement depends on a file there. Nothing was executed, and the pinned Akeru tree was not re-inspected in this session. Upstream behaviour below is cited only as this package records it.

### GROK-1 · Backup procedure deletes files from the backup set
**Severity:** major
**Finding:** `docs/12-operations.md` §5.2 copies attachments, artifacts and memory with `rsync -a --delete-after` into one reused directory, `/backup/files/`. `--delete-after` removes destination files that are not in the current source. After a named purge, or after any source file is absent for a run, the next backup deletes the retained copy. Database snapshots are dated (`state-YYYY-MM-DD.sqlite`); the file set is not. That contradicts AKIRA-D2, AK-OPS-11, and the same runbook’s §10 rule that backup rotation is a HUMAN-named operation. The purge procedure in §10 depends on a pre-purge backup remaining available (§7.9).
**Proposed correction:** Drop `--delete-after`. Write each run to a new timestamped directory (or an append-only store) and checksum it. Make any later removal of backup directories a separate HUMAN-named operation, with the same explicit-id rule as purge. Add a drill: back up, remove a source file, back up again, and assert the earlier copy is still present.
**Evidence:** `docs/12-operations.md` §5.2, §7.9 and §10; `spec.md` AK-OPS-04 and AK-OPS-11; `decisions.md` AKIRA-D2.
**Confidence:** high

### GROK-2 · Upstream `bot.delete` stays callable; only the UI path is guarded
**Severity:** major
**Finding:** Akeru’s decider command `bot.delete` removes routine and skill assignments and emits `bot.deleted` (`docs/02-akeru-baseline.md` B-33). Akira’s change for that command is “remove hard delete from the UI” (B-33) and P0 item 2, “remove/guard the hard-delete UI path” (`docs/11-backlog.md` §2). The Akira command table adds `purge.request` and does not require the server to reject `bot.delete` (`docs/05-interfaces.md` §1.1, §1.5). §8.1 says scopes are enforced server-side and that UI gating is presentation only. T-12 checks that a retention timer does not dispatch `bot.delete`; it does not check a direct command. A client that still sends the upstream command bypasses named ids, backup-first and the `destructive` scope.
**Proposed correction:** Remove `bot.delete` from the decider command surface, or make it an alias that fails unless it satisfies the `purge.request` guards. Add a server test that a direct `bot.delete` is rejected without explicit ids, a verified backup, the `destructive` scope and an audit record.
**Evidence:** `docs/02-akeru-baseline.md` B-32 and B-33; `docs/11-backlog.md` Phase 0 item 2; `docs/05-interfaces.md` §1.5 and §8.1; `docs/10-tests-and-acceptance.md` T-12; `spec.md` AK-OPS-11 and AK-UX-16.
**Confidence:** high

### GROK-3 · Restoring an older snapshot can dispatch effects the snapshot never recorded
**Severity:** major
**Finding:** AK-TSK-14 reconciles action rows that are already `dispatched` or `unknown`, and it dispatches queued work that was never dispatched. Restore (`docs/12-operations.md` §5.3) and upgrade rollback (§3.4) start the server on the restored snapshot. They do not disable autonomous dispatch, routines or outbound writes, and they do not define the interval between the snapshot and the failure. A task that was `ready` in the snapshot can be dispatched again after the live system already confirmed a non-idempotent send that the snapshot does not contain. There is then no ledger row to reconcile. T-03 and T-11 cover an unknown row that is present, and unresolved rows that are restored as unresolved. They do not cover an effect that exists only in the lost interval. §2 states that state inside the proposed RPO may be lost; the external system is not rolled back with it.
**Proposed correction:** Require restore and rollback to boot with dispatch, routines and external writes off. Record the snapshot time and the uncertain interval. Reconcile tasks that could have acted in that interval against preserved post-snapshot evidence or the external system before enabling them. If the effect cannot be established, leave the task blocked for a HUMAN. Do not run the restored environment while the original is still writing. Add a fault test that restores a snapshot taken before a later confirmed non-idempotent write and asserts no second write.
**Evidence:** `spec.md` AK-TSK-11, AK-TSK-14, AK-OPS-05 and AK-OPS-06; `docs/12-operations.md` §2, §3.4 and §5.3; `docs/10-tests-and-acceptance.md` T-03 and T-11.
**Confidence:** high

### GROK-4 · A mid-stream failure may be classified as an automatic infrastructure retry
**Severity:** major
**Finding:** The error taxonomy defines `network` as DNS, TLS, or timeout before acceptance, and AK-RTE-12 / `docs/04-data-model.md` §4.2 allow automatic infrastructure fallback only for `failed_rate_limit` and `failed_network`. Fault F-03 injects a 5xx mid-stream and accepts attempt outcome `network` or `unknown`, while also requiring that tool side effects are not duplicated. A 5xx after a tool request was sent is not “before acceptance”. Classifying it as `network` authorizes another attempt. The action ledger does not, in this row, force the attempt out of the fallback set when an action is `dispatched` or `unknown`.
**Proposed correction:** If the attempt has dispatched any external action, the attempt outcome is `interrupted` or `failed_unknown` and is ineligible for automatic fallback until reconciliation. Reserve `failed_network` for failures with no dispatched external action. Change F-03’s expected outcome to that rule, and add the case to the fault matrix.
**Evidence:** `docs/10-tests-and-acceptance.md` F-03; `docs/05-interfaces.md` §6 (`network`); `docs/04-data-model.md` §4.2; `spec.md` AK-RTE-12 and AK-TSK-11.
**Confidence:** high

### GROK-5 · The task state machine has no resume path, and `not-ready` blocks every route
**Severity:** major
**Finding:** `docs/04-data-model.md` §4.1 lists entries into `awaiting_input`, `blocked` and `paused`, and cancel from any non-terminal state. It lists no transition back to `ready` or `running`. The invariant that forbids `blocked → running` without resolving the blocker assumes that transition exists. `task.resume` is a command (`docs/05-interfaces.md` §1.2) with no matching edge. T-02 requires a quota failure to land in `paused`/`blocked` and then resume as a new attempt; that resume is not a legal event. Separately, `triaged → ready` requires readiness ≠ `not-ready` unless an undefined “assessment override” is recorded. AK-TRG-07 and §4.3 say `not-ready` forbids only the specification-led downgrade and still allows an advanced route. T-10’s pass condition is the narrower rule. The table and the requirement cannot both be implemented.
**Proposed correction:** Add `awaiting_input → ready` when the question is answered, `blocked → ready` when the blocker is resolved, and `paused → ready` on explicit resume, including `failed_quota`. Record the new attempt on `task.start` from `ready`. Change the `triaged → ready` guard so `not-ready` rejects only a below-floor or specification-led route; an advanced route that meets the floor may proceed with the risks attached. Drop “assessment override” unless it is a named, authorized command.
**Evidence:** `docs/04-data-model.md` §4.1 and §4.3; `docs/05-interfaces.md` §1.2; `docs/10-tests-and-acceptance.md` T-02 and T-10; `spec.md` AK-TSK-01, AK-TRG-07 and AK-UX-12.
**Confidence:** high

### GROK-6 · `meetsFloor` records quota loss and prompt-injection as capability
**Severity:** major
**Finding:** AK-RTE-13 and AK-TRG-13 require credit exhaustion to stay a cost/availability event and forbid lowering or relabelling the capability floor. `RouteDecision.candidates` has a single `meetsFloor` flag and one USD `estimatedCost` (`docs/04-data-model.md` §3). The golden route decision sets Codex `meetsFloor: false` because the account is quota-exhausted, while the note says the failure is `quota_exhausted`, not capability. The same record sets DeepSeek `meetsFloor: true` with `requiredSkillSupport: native-verified` and a note that skills are prompt-injected and support is unknown. AK-TRG-09 and AK-SKL-10 say a route below the required skill level is not selectable. The recovery wireframe offers “resume on deepseek” for that task (`docs/06-ux.md` §8) without a floor failure.
**Proposed correction:** Add an availability field (`available` / `quota_exhausted` / `auth` / `unknown`) separate from `meetsFloor`. Quota and auth must not clear `meetsFloor`. Set `meetsFloor` false when skill support is below `requiredSkillSupport`. Update `evals/fixtures/route-decision.json` and the recovery wireframe so a prompt-injected route is not offered as adequate for a native-verified floor.
**Evidence:** `spec.md` AK-RTE-12, AK-RTE-13, AK-TRG-09, AK-TRG-13 and AK-SKL-10; `docs/04-data-model.md` §3 `RouteDecision`; `evals/fixtures/route-decision.json`; `docs/06-ux.md` §8.
**Confidence:** high

### GROK-7 · The normative cost total adds subscription-equivalent to API estimates
**Severity:** major
**Finding:** `docs/09-accounting.md` §1 principle 6 forbids summing API dollars, subscription-equivalent dollars, plan percentages and credits into one spend number. §8 says the route view must not compare subscription-equivalent with API dollars as if equal. The normative worked example (§4, required by AK-ACC-05) adds use-2 ($1.84) into exclusive $3.12 and inclusive $3.50. `evals/fixtures/usage-record.json` is that use-2 row: measurement `provider-reported`, cost provenance `subscription-equivalent`, account “Max 20x”. `evals/fixtures/task.json` stores one exclusive amount, 3.12 USD, provenance `mixed`. T-09 requires those combined numbers. `docs/06-ux.md` §7 shows a team total of $41.20 beside Claude subscription-equivalent and DeepSeek API amounts, then says those units are never summed. AK-TRG-10 selects the lowest expected total delivery cost, and route candidates carry a single USD range (`route-decision.json` uses `subscription-equivalent` only as Codex `estimateBasis`). An implementer who follows the example and T-09 will rank routes by an incomparable sum.
**Proposed correction:** Keep cash charges, price-table estimates and subscription-equivalent amounts as separate subtotals in `CostSummary`, the worked example, the task fixture and the usage wireframe. Define route ranking over one labelled comparison unit (for example an API-equivalent estimate) that is not displayed as spend, or restrict automatic cost ranking to candidates in the same `auth_class` and leave cross-class choice to the operator. Change T-09 so a passing total preserves the split.
**Evidence:** `docs/09-accounting.md` §1.6, §4, §5 and §8; `spec.md` AK-ACC-04, AK-ACC-05 and AK-TRG-10; `evals/fixtures/usage-record.json`; `evals/fixtures/task.json`; `evals/fixtures/route-decision.json`; `docs/06-ux.md` §7; `docs/10-tests-and-acceptance.md` T-09.
**Confidence:** high

### GROK-8 · Usage categories are three different closed sets, and imported rows are unmapped
**Severity:** minor
**Finding:** AK-ACC-02 requires categories turn, tool, delegation, routine, review, observer, embed/recall and other. AK-ACC-07 requires coordination overhead to be a visible category. The schema and `docs/09-accounting.md` §3 use turn, tool, delegation, routine, review, observer, media and other, with no coordination, embed or recall. The usage wireframe still shows a coordination amount (`docs/06-ux.md` §7), and the CPAT formula adds a coordination term (`docs/09-accounting.md` §9). The inspected Akeru ledger uses turn, tool, observer, reflector, extraction, recall, routine and delegated (`docs/02-akeru-baseline.md` B-22). `docs/04-data-model.md` §7 adds nullable columns and says existing rows stay valid; it does not map `reflector`, `extraction`, `recall` or `delegated` onto the new union. Roll-ups that switch on the new union drop or reject the history AK-ACC-16 uses for routing calibration.
**Proposed correction:** Publish one category union that includes coordination and the legacy values, with an explicit map (for example delegated→delegation, reflector→observer, extraction/recall→other, unknown→other) and a migration test that each pre-migration row keeps one category and is counted once.
**Evidence:** `spec.md` AK-ACC-02, AK-ACC-07 and AK-ACC-16; `docs/04-data-model.md` §5 and §7; `docs/09-accounting.md` §3 and §9; `docs/02-akeru-baseline.md` B-22; `docs/06-ux.md` §7.
**Confidence:** high

### GROK-9 · Coverage arithmetic and the CPAT sentence do not match the records
**Severity:** minor
**Finding:** §8 defines `coverage = reported + estimated / (reported + estimated + unknown record count)`, which is `reported + (estimated / total)` rather than `(reported + estimated) / total`. `CostSummary.coverage` counts only reported, estimated and unknown, so a `subscription-equivalent` record has no bucket. `task.json` exclusive coverage is reported 3, estimated 3 for the T-142 set. use-2 is provider-reported tokens with subscription-equivalent cost; counting it as reported yields 4 reported and 2 estimated, and the schema cannot count it apart. The worked-example overhead is review+observer = $0.30, while the fixture overhead is $0.45 (that sum plus the triage turn) with provenance `estimated`, although two of those three records are provider-reported. §9 says “Rework attempts are in both (cost and denominator)” under a denominator of accepted tasks. Read literally, each rework attempt increments the accepted-task count and lowers CPAT for routes that rework.
**Proposed correction:** Define coverage as `(reported + estimated) / (reported + estimated + unknown)`, plus a subscription-equivalent count, and state the zero-record case. Split overhead so triage is not silently folded into the $0.30 definition. Define CPAT as attributable cost divided by the number of distinct accepted tasks; rework adds cost only.
**Evidence:** `docs/09-accounting.md` §4, §8 and §9; `docs/04-data-model.md` §5 `CostSummary`; `evals/fixtures/task.json`; `evals/fixtures/usage-record.json`.
**Confidence:** high

### GROK-10 · Traceability phases disagree with the backlog, and two skill requirements are outside the matrix range
**Severity:** minor
**Finding:** `docs/10-tests-and-acceptance.md` §5 marks every row a release gate and assigns phases that do not match `docs/11-backlog.md`: tasks are phase 3 (backlog P2), triage phase 4 (P3), skills phase 5 (P4), accounting phase 4 (P5), specialists phase 8 (P7). The skill row is `AK-SKL-01..12`. AK-SKL-13 and AK-SKL-14 (the v1 catalogue and the connector-conditional rule) are outside that range, so the catalogue exit criterion in Phase 4 is not in the traceability gate.
**Proposed correction:** Point the Phase column at P0–P10, or rename it if it means something else. Extend the skill row through AK-SKL-14 and name T-04 plus the `docs/15-skills-v1.md` fixture rule as the test.
**Evidence:** `docs/10-tests-and-acceptance.md` §5; `docs/11-backlog.md` §§4–10; `spec.md` AK-SKL-13 and AK-SKL-14.
**Confidence:** high

### GROK-11 · The readiness skill counts eight criteria; the gate schema has nine
**Severity:** minor
**Finding:** AK-TRG-06 lists eight readiness items, with “dependencies and interfaces” as one item. `ReadinessResult.criteria` stores `dependencies` and `interfaces` as separate keys, nine fields, and `task.json` marks all nine `pass`. `docs/15-skills-v1.md` S2 says the readiness skill scores “the 8 readiness criteria”. A skill that returns eight results cannot fill the gate that admits a route. The same catalogue points S11 at `evals/fixtures/skill-package.json` and says other fixture directories are not in this draft, while that JSON’s validation command references `evals/fixtures/sheet-fixture.json`, which is not in the package.
**Proposed correction:** Make the checklist one list: either merge the schema fields or change S2 and AK-TRG-06 to nine named criteria. Point the skill-package validation fixture at a path this draft actually contains, or mark the command as a Phase 4 placeholder in the JSON.
**Evidence:** `spec.md` AK-TRG-06; `docs/04-data-model.md` §4.3; `docs/15-skills-v1.md` §1 and S2, S11; `evals/fixtures/task.json`; `evals/fixtures/skill-package.json`.
**Confidence:** high

### GROK-12 · Rework is a 1–5 score in the anchor table and an enum in the record
**Severity:** minor
**Finding:** `docs/08-collaboration-and-accountability.md` §5.1 types `rework` as `none | minor | major`. §5.2 puts Rework on the same 1 / 3 / 5 anchor scale as the numeric criteria, with 5 meaning “none”. §5.3’s evidence-weighted mean averages criteria. `rating.json` stores `"rework": "minor"`. A mean over mixed number and enum fields is not defined, and a reader can treat the right-hand column as the high numeric score.
**Proposed correction:** Keep rework as the three-value enum and remove it from the 1–5 anchor table. State that reputation averages only the numeric criteria, and that rework is reported as a count. Map the enum in one direction if a formula needs a number.
**Evidence:** `docs/08-collaboration-and-accountability.md` §5.1–§5.3; `evals/fixtures/rating.json`; `spec.md` AK-RAT-02 and AK-RAT-06.
**Confidence:** high

### GROK-13 · Steady-state maintenance effort is below the sum of the same table
**Severity:** minor
**Finding:** `docs/11-backlog.md` §15 lists quarterly rebase (1–2 ew), provider updates (0.5–1 ew per month), connector drift (0.5 ew per connector per quarter), a backup drill (0.5 ew), a security review (0.5–1 ew per release) and price-table updates (0.25 ew per month). The same section states steady state as 2–4 ew per quarter. One quarter that includes the monthly rows plus one rebase and one connector is already above 4 ew. P0–P10 range arithmetic for the phase totals is consistent (core 35–50 ew; specialists plus three connectors 12–28 ew; full target 47–78 ew).
**Proposed correction:** Replace the 2–4 ew figure with the sum of the rows that the table says occur in the same quarter, still labelled as a placeholder, or say which rows are excluded from the 2–4 ew band.
**Evidence:** `docs/11-backlog.md` §15, and the totals in the preamble and §§2–12.
**Confidence:** medium

### GROK-14 · Room-routing defaults disagree, and two citations point at the wrong decision
**Severity:** minor
**Finding:** AK-COL-02 keeps Akeru’s “boss answers every message, last mention wins” as the default room rule. `docs/08-collaboration-and-accountability.md` §2.3 says that behaviour is the `lead-bot` configuration, “not the universal default”, and that multiple mentions use first-listed wins unless last-wins is configured. A new room has two defaults. Separately, AK-SPC-03 cites AKIRA-D4 for WhatsApp template support; AKIRA-D4 is the Linux host decision, and template scope is U5. `docs/12-operations.md` §4 sends a suspected secret leak to “§9.6”; the secret-exposure runbook is §7.6.
**Proposed correction:** Name one default rule (`mention` or `lead-bot`) and one multi-mention winner in both places. Cite U5 for template scope. Point the secret-leak sentence at §7.6.
**Evidence:** `spec.md` AK-COL-02 and AK-SPC-03; `docs/08-collaboration-and-accountability.md` §2.3; `decisions.md` AKIRA-D4; `docs/13-open-decisions.md` U5; `docs/12-operations.md` §4 and §7.6.
**Confidence:** high

Result: complete
