# CHATGPT review — round 1

Reviewed `spec.md` v0.3, `decisions.md`, all fifteen companion documents, and all eight representative JSON fixtures against the declared `loop.json` scope. AKIRA-D1–D6 are fixed. There is no previous consolidation in this registered loop. The declared `assets/` directory is absent; no asset-dependent claims were independently verified. This is a specification review, not runtime verification or an upstream-source inspection.

### CHATGPT-1 · Backup procedure enables deletion without a named HUMAN request
**Severity:** major
**Finding:** `docs/12-operations.md` §5.2 prescribes `rsync -a --delete-after` into a reused backup destination. A subsequent backup can remove destination files absent from the current source, including older preserved data. This directly contradicts AKIRA-D2 and AK-OPS-11; the backup procedure contains no specific HUMAN authorization for those removals. Calling the procedure staging-first does not resolve the contradiction in the production runbook.
**Proposed correction:** Specify a fresh, uniquely named backup directory for every snapshot and a copy operation without deletion flags. Preserve earlier generations; any removal remains a separate operation requiring a HUMAN request naming the items. Add a synthetic backup check proving that a later snapshot preserves a file present only in an earlier generation.
**Evidence:** `docs/12-operations.md` §5.2 contains the deletion-enabled command; §10 says backup rotation is a HUMAN-named operation. `decisions.md` AKIRA-D2 prohibits deleting backups or user data without an explicit named HUMAN request.
**Confidence:** high

### CHATGPT-2 · Restoring an older snapshot can replay effects missing from its ledger
**Severity:** major
**Finding:** AK-TSK-14 reconciles actions present as `dispatched`/`unknown`, but the restore and upgrade-rollback runbooks start an older database without defining a dispatch quarantine for the interval lost to recovery. Example: snapshot contains a ready task; the live system subsequently sends a non-idempotent message and confirms it; recovery restores the snapshot, which contains neither the action nor its confirmation. Ordinary startup can dispatch the ready task again. There is no unknown ledger row to reconcile. The same risk applies to restored routines and to a restore drill retaining enabled work. Preserving unresolved rows alone does not make rollback safe against external systems that were not rolled back.
**Proposed correction:** Require restore/rollback to start with autonomous dispatch, routines, outbound channel delivery and external writes disabled. Record the recovery point and uncertain interval; reconcile potentially affected tasks against preserved post-snapshot evidence/external state before releasing them. Where the prior effect cannot be established, block for HUMAN reconciliation rather than replay. Fence or stop the original environment before enabling the restored one. Add a fault test restoring a snapshot taken before a later confirmed non-idempotent write and prove no second write occurs.
**Evidence:** `spec.md` AK-TSK-11/14 and AK-OPS-05/06; `docs/12-operations.md` §3.4 and §5.3 restart the restored server; §2 explicitly allows state loss within the proposed RPO. `docs/10-tests-and-acceptance.md` T-03 tests a restart with the action ledger intact, and T-11 tests preserving existing unresolved rows; neither tests actions absent from an older snapshot.
**Confidence:** high

### CHATGPT-3 · The normative total mixes subscription equivalents with other money
**Severity:** minor
**Finding:** The worked example supplies one exclusive/inclusive dollar total, but its corresponding `usage-record.json` identifies the $1.84 Claude amount as `subscription-equivalent`. Other example rows have different measurement bases. `CostSummary` offers one amount and a `mixed` provenance, without a required breakdown by cash charge, API estimate and subscription equivalent. Consequently the normative $3.50 total cannot demonstrate the explicit rule that these units must remain separate; a `mixed` label alone cannot recover the components.
**Proposed correction:** Make summaries retain separate subtotals by currency and cost provenance, including coverage for unknown amounts. Update the worked example, fixture and UI examples to show those subtotals. If a combined economic estimate is useful, define and label it separately from spend and retain its components.
**Evidence:** `docs/09-accounting.md` §1 principle 6 and §5 prohibit summing these units into spend; §4 nevertheless defines a single normative $3.50 inclusive total. `evals/fixtures/usage-record.json` marks use_T142_2 as subscription-equivalent. `docs/04-data-model.md` §5 defines the single-amount `CostSummary`.
**Confidence:** high

### CHATGPT-4 · Accounting formulas contradict accepted-task and coverage definitions
**Severity:** minor
**Finding:** `docs/09-accounting.md` §9 says rework attempts enter the CPAT denominator, although that denominator is the number of accepted tasks. One accepted task with three attempts must count once, or extra rework artificially improves the metric. The displayed CPAT expression also lacks parentheses around the entire cost numerator. In §8, `reported + estimated / (...)` lacks parentheses around the coverage numerator and can exceed 100% under ordinary arithmetic precedence. These are formula defects, independent of any unsettled weights or thresholds.
**Proposed correction:** Define CPAT as the complete attributable cost numerator divided by the count of distinct accepted tasks; rework adds cost, not accepted tasks. Define coverage as `(reported + estimated) / (reported + estimated + unknown)`, state the zero-record case, and add examples with one accepted task/multiple attempts and mixed known/unknown records.
**Evidence:** `spec.md` AK-ACC-06/16 and AK-TRG-14; `docs/09-accounting.md` §8 coverage expression and §9 CPAT expression plus the bullet “Rework attempts are in both (cost and denominator).”
**Confidence:** high

### CHATGPT-5 · Late token telemetry is reduced to a cost-only correction
**Severity:** minor
**Finding:** AK-ACC-09 and `docs/09-accounting.md` §7 describe late cache-token corrections as changing cost only because tokens have already been counted. That works when a complete token breakdown was known initially, but not when cached input was initially null or the first record was unavailable. In those cases cost-only correction leaves the required token dimensions and coverage permanently wrong. Append-only replacement can correct token telemetry without adding a second execution's tokens.
**Proposed correction:** Define a correction as a superseding effective usage snapshot for whichever token and cost fields become known. Queries select the effective revision once per logical usage record, preserving prior revisions for audit. Test unavailable-to-reported settlement and a late cached/uncached breakdown, as well as cost-only correction.
**Evidence:** `spec.md` AK-ACC-03/09; `docs/09-accounting.md` §4 double-counting check 5 and §7 row “Provider reports cache tokens later”; `docs/04-data-model.md` §5 already provides `supersedes` but does not define field replacement semantics.
**Confidence:** high

### CHATGPT-6 · Canonical task transitions omit resume and failure recovery
**Severity:** minor
**Finding:** The canonical state table has transitions into `paused`, `blocked` and `awaiting_input`, but no outgoing resume transitions. It also maps “attempt ended” to `review` only with artifacts and acceptance evidence, without rows for quota, network, cancellation or restart interruption. The prose and command contracts clearly require these recovery paths, so this is an incomplete normative state table rather than a new product decision. Implementers should not have to invent which states and guards a required `task.resume` uses.
**Proposed correction:** Add explicit transitions for resolving input/blockers, resuming a paused task, and handling each attempt-outcome class, including when a new checkpoint, re-triage or route check is required. Align the supervisor flow with the table and exercise these paths in its state-machine tests.
**Evidence:** `docs/04-data-model.md` §4.1 contains no outgoing rows for those three states; §4.2 describes quota pause and infrastructure fallback. `docs/05-interfaces.md` §1.2 exposes `task.resume`, and §4 allows `task.ready` after an outcome. `spec.md` AK-TSK-09/14 and AK-RTE-13 require recovery.
**Confidence:** high

### CHATGPT-7 · Golden fixtures do not yet satisfy their declared contracts
**Severity:** minor
**Finding:** All eight fixture files parse as JSON, but none contains the `schemaVersion` required by the interface versioning contract. The route-decision fixture sets DeepSeek `meetsFloor: true` despite a `native-verified` skill floor and its own note saying prompt-injected skills/tool transcript pending. The task fixture's overhead is $0.45 while the normative accounting query defines overhead as review plus observer ($0.30), with triage classified as delivery. These are inconsistent positive examples for schema, routing and roll-up tests, even though the chosen route itself is safe.
**Proposed correction:** Add schema versions consistently to the canonical shapes and fixtures; distinguish capability-floor compliance from account availability and verification eligibility; make the DeepSeek candidate fail this native-skill floor. Choose one overhead definition and update the worked query, task fixture and UI accordingly. Validate semantic invariants as well as JSON syntax before calling these golden records complete.
**Evidence:** `docs/05-interfaces.md` §7 requires a contract version in every schema. `evals/fixtures/route-decision.json` contains the conflicting floor/candidate. `evals/fixtures/task.json` reports overhead 0.45; `docs/09-accounting.md` §4 reports overhead 0.30 and delivery including triage. `docs/04-data-model.md` §9 describes the fixtures as small but complete.
**Confidence:** high

### CHATGPT-8 · New catalogue requirements are absent from release traceability
**Severity:** minor
**Finding:** v0.3 adds AK-SKL-13/14, but the requirement-to-test matrix still stops at AK-SKL-12. T-04 exercises one resource-bearing skill across routes, not the ten mandatory skills or the conditional availability gate. The backlog mentions catalogue fixtures, so the intent exists, but the claimed complete requirement mapping does not yet cover the new requirements.
**Proposed correction:** Add AK-SKL-13/14 rows linking each mandatory catalogue fixture to the required route matrix and testing that conditional skills remain unavailable until connector workflow verification. Include a negative test for advertising a skill whose fixture failed or whose connector is missing. Keep planned fixture directories clearly labelled as planned.
**Evidence:** `spec.md` AK-SKL-13/14; `docs/10-tests-and-acceptance.md` §5 lists only AK-SKL-01..12; T-04 covers one skill. `docs/15-skills-v1.md` §2–§4 defines the broader catalogue and explicitly identifies uncreated fixture directories; `docs/11-backlog.md` P4 requires the ten fixtures.
**Confidence:** high

Result: complete
