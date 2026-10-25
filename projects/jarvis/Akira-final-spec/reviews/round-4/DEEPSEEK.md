# DEEPSEEK review — round 4

**Reviewer:** DEEPSEEK · **Date:** 2026-10-25

Reviewed `spec.md` v0.6 after the round-3 consolidation and the prior consolidations,
with `decisions.md`, all fifteen companion documents and all eight JSON fixtures in the
manifest scope. AKIRA-D1–D6 remain fixed and are not reopened; U4–U16 are treated as
carried-forward open HUMAN decisions and no answer is requested here. This is a
specification review, not verification of Akira or upstream runtime behaviour: every
observation comes from the documents and fixtures read as text. Read-only checks covered
the worked-example arithmetic, the fixture shapes and schema versions, and the
cross-references cited below; no validator, runtime test, git command, installation,
authentication, deployment or paid operation was run.

Findings: seven minor; no blocking or major findings.

### DEEPSEEK-1 · Logical action keys and provider idempotency keys are conflated
**Severity:** minor
**Finding:** AK-TSK-13 requires action keys to be "scoped to the task and the logical intent, not to a retry". `docs/04` §4.4 then says a new action with the same logical intent "reuses the idempotency key only if the provider semantics permit it; otherwise it is a new key and the ledger records the link", and the state table sends `failed → intent (new action id)`. `docs/04` §6 declares `ActionRecord` unique on `(connector, idempotency_key)` without saying whether the constraint is on the append-only table or only the open-action projection. The spec never defines whether "action key" in AK-TSK-13 is the logical key or the provider key. If it is the provider key, the new-key branch violates AK-TSK-13; if it is a separate logical key, that key is absent from the ledger schema and the "link" has no defined fields. A reused provider key on a new action record also collides with the unique constraint on the natural reading of the append-only table. The failed-then-retried write path — the path reconciliation depends on — therefore cannot be implemented or validated consistently.
**Proposed correction:** Define two named keys: `logicalActionKey` (stable for the task and intent across attempts/retries) and `providerIdempotencyKey` (the value sent to the connector, present only where the provider supports one). Give a new action a `supersedes`/`linkedActionId` link, and state the uniqueness scope explicitly (for example, unique `(connector, providerIdempotencyKey)` on dispatched provider calls, or a partial unique index over non-terminal actions). Update AK-TSK-13, `docs/04` §4.4/§6 and `docs/05` §5 to use the two names.
**Evidence:** `spec.md` AK-TSK-10, AK-TSK-11, AK-TSK-13; `docs/04-data-model.md` §4.4 state table and rule, §6 ActionRecord row; `docs/05-interfaces.md` §5.
**Confidence:** high

### DEEPSEEK-2 · Backup-account takeover and the no-fallback defaults for quota/auth are not reconciled
**Severity:** minor
**Finding:** AK-RTE-09 says backup takeover "on a usage limit serves the *next* request" and the request that hit the limit fails; `docs/05` §6 says `auth_expired` fallback is "no (unless another verified account)". Both can be read as automatic account-level fallback for quota or auth. That reading conflicts with the conservative default in AK-RTE-12 (automatic fallback only for rate limit/transient transport; none for exhausted credits unless policy explicitly says so), AK-RTE-13's paused-with-options path, `docs/04` §4.1/§4.2 (`failed_quota → paused`, `failed_auth → blocked`, "no fallback"), `docs/10` F-01 ("no fallback by default") and `docs/12` §7.2, where the operator chooses wait, switch route or switch account. The spec does not say whether account takeover is an explicit exception to AK-RTE-12, a policy-gated fallback, or an operator repair for the next request, so the same quota or auth error can legitimately take two different paths.
**Proposed correction:** State the relationship. Either make backup-account takeover a policy-gated fallback subject to AK-RTE-12 (default off for `quota_exhausted`/`auth_expired`, with the policy basis recorded), or state that AK-RTE-09 describes operator-initiated account repair for the next request and that the failed request still pauses/blocks as §4.1 requires. If "usage limit" is intended to mean only rate limits, say so. Align the `auth_expired` parenthetical in `docs/05` §6 with the chosen rule.
**Evidence:** `spec.md` AK-RTE-09, AK-RTE-12, AK-RTE-13; `docs/04` §4.1/§4.2; `docs/05` §6; `docs/10` F-01/T-02; `docs/12` §7.2.
**Confidence:** medium-high

### DEEPSEEK-3 · AK-ACC-14's failed-attempt separation has no schema or derivation
**Severity:** minor
**Finding:** AK-ACC-14 requires a task cost summary to separate delivery cost from overhead "and from failed attempts". AK-ACC-07 defines delivery as every category except review/coordination/observer, and `docs/09` §4 says failed-attempt cost is "included in delivery cost, not hidden in a separate 'waste' bucket". The canonical `Task.cost` is only `{exclusive, inclusive, overhead}` (`docs/04` §3; the task fixture has no failed-attempt subtotal), so the required separation cannot be stored or validated. `docs/06` §3 shows a "failures" line and `docs/09` §8 lists "failed attempts" as a view, but neither defines the filter or the arithmetic. The same amount is thus both "not separate" and "MUST separate".
**Proposed correction:** Keep delivery as the enclosing total and make failed-attempt cost a required sub-line of it, with an explicit filter (for example, usage records attributed to attempts whose outcome is one of `failed_*` or `interrupted`, with cancelled-before-usage and rework stated separately). Either add a `failedAttempts`/`byOutcome` subtotal to `Task.cost`/`CostSummary`, or state that the line is a query over attempt records and cannot be used as a ledger total. Align `docs/09` §4/§8, `docs/06` §3 and the task fixture.
**Evidence:** `spec.md` AK-ACC-07, AK-ACC-14; `docs/09` §4, §8; `docs/04` §3 `Task.cost`; `docs/06` §3; `evals/fixtures/task.json`.
**Confidence:** high

### DEEPSEEK-4 · `PersonaPatch` is referenced but never defined
**Severity:** minor
**Finding:** AK-IDE-04 requires instance overrides to be a diff against the template revision, with field-level provenance (template, instance, HUMAN) and a reproducible effective persona. `docs/04` §2 encodes this as `PersonaRevision.composedFrom.overrides: PersonaPatch[]` and `BotInstance.overrides.persona?: PersonaPatch[]`, then states "Persona overrides are field-level patches with provenance". `PersonaPatch` is defined nowhere in the package (only those two references), and `docs/05` §1.1 accepts "document or patch" for `persona.create-revision` with no patch contract. There is no field-path/operation/value shape, no merge order (template → instance → HUMAN), no same-field conflict rule, and no way to validate field-level provenance or recompute the effective document. This is a core mechanism for preserving one bot identity across providers, so an implementer is left to invent it.
**Proposed correction:** Define `PersonaPatch` in `docs/04` §2: field path against `PersonaDocument`, operation (set/replace/remove/add), value, base template/persona hash, author/provenance (`template` | `instance` | `human`, actor id), and timestamp/revision. Define a deterministic application order and conflict rule (for example, later explicit HUMAN patch wins; otherwise reject an ambiguous same-field patch). Reference the type from `docs/05` §1.1 and add a recomputation/provenance test.
**Evidence:** `spec.md` AK-IDE-04; `docs/04` §2 PersonaRevision, BotInstance and rules; `docs/05` §1.1; no other `PersonaPatch` definition in the package.
**Confidence:** high

### DEEPSEEK-5 · Usage-record idempotency uniqueness is undefined for non-bot owners
**Severity:** minor
**Finding:** AK-ACC-01 requires a stable idempotency key for every usage record and names Akeru's `UNIQUE(bot_id, source_key)` as the base. `docs/04` §5 annotates `idempotencyKey` as "unique per owner + source"; §6 says the table is "keyed by `idempotencyKey`"; §7 preserves `UNIQUE(bot_id, source_key)` for legacy rows. Owners include task, room, observer and connector, which have no `bot_id`. The uniqueness scope for those rows is therefore undefined, and the two descriptions imply different constraints (composite per owner versus global key). `docs/09` §12.3 then requires export/merge to dedupe by `idempotencyKey` alone, which is safe only if the key is globally unique. A duplicate report of one turn under a changed owner, or a merge of two databases, can collide or double-count — the failure the idempotency rule exists to prevent.
**Proposed correction:** Define the key for every owner kind, for example `(owner_kind, owner_id, source, idempotency_key)`, and state whether it is globally unique across exports. Use that same constraint in `docs/04` §5/§6/§7 and in `docs/09` §12.3's merge rule, and add a migration/merge test.
**Evidence:** `spec.md` AK-ACC-01; `docs/04` §5, §6, §7; `docs/09` §12.3; `evals/fixtures/usage-record.json` (owner kind `task`).
**Confidence:** medium

### DEEPSEEK-6 · Decision-register and cross-references do not resolve
**Severity:** minor
**Finding:** Three references point to the wrong item or to no item. (1) `docs/01` §5 says "HUMAN has supplied no budgets or thresholds (`docs/13-open-decisions.md` U6)". U6 is rating aggregation; budgets, spend caps, concurrency caps and approval thresholds are U4. (2) AK-OPS-09 assigns the SLO proposal to "(U4)", but U4's register row does not cover availability/RPO/RTO/notice time; `docs/12` §2 contains those proposals and no register row owns them. (3) AK-TRG-10, `docs/09` §8 and `docs/13` U16 cite `docs/09-accounting.md` §1.7. `docs/09` §1 is a numbered principle list; the routing-comparison principle is item 7 and there is no §1.7 heading. These are the pointers an implementer or HUMAN follows to the governing decision and route rule; (1) and (2) make a budget question and an SLO question look settled or registered when they are not.
**Proposed correction:** Change `docs/01` §5 to U4. Either extend U4's row in `docs/13` to name SLO targets, or make AK-OPS-09 cite `docs/12` §2 as a labelled proposal and add the SLO item to the open register if it is meant to be one. Change the three `§1.7` references to "§1 item 7" (or add a real §1.7 heading). This asks for reference repair only; no new HUMAN answer is requested.
**Evidence:** `docs/01` §5; `docs/13` U4, U6, U16; `spec.md` AK-OPS-09, AK-TRG-10; `docs/09` §1, §8; `docs/12` §2.
**Confidence:** high

### DEEPSEEK-7 · F-07 accepts a watchdog notification without the required `interrupted` outcome
**Severity:** minor
**Finding:** `docs/05` §2 rule 4 requires a terminal event for every turn "or the ingestion watchdog marks the attempt interrupted." `docs/10` F-07 (provider silent 90 s) has result kind `watchdog` and expected result "operator inbox activity, no terminal failure", with recovery "operator decides; not auto-failed". Read together, the test says the attempt is not terminated, while the adapter contract says the watchdog marks it `interrupted`. `interrupted` is a terminal attempt outcome (`docs/04` §4.2) and leads to a resumable checkpoint and `blocked`/`awaiting_input` (`docs/04` §4.1). F-07 asserts neither, so an implementation that notifies the operator and leaves the attempt running indefinitely would pass. The row can keep its `watchdog` result kind (round-3 P11) and still assert the derived attempt outcome.
**Proposed correction:** In F-07, assert the watchdog notification and, when no terminal event has arrived, the attempt outcome `interrupted` with a resumable checkpoint and task `blocked`/`awaiting_input`. If 90 s of silence is only a notification and the attempt may continue, amend `docs/05` §2 rule 4 to say so and define when `interrupted` is recorded. Add the assertion to T-03/T-14 coverage.
**Evidence:** `docs/05` §2 rule 4; `docs/10` F-07 and its AK-COL-03..07 traceability row; `spec.md` AK-TSK-14; `docs/04` §4.1, §4.2.
**Confidence:** medium-high

All seven findings are minor; none is a blocking or major defect. They concern contract clarity and cross-reference integrity in the action ledger, fallback policy, accounting summary, persona overrides, usage idempotency, decision register and watchdog testing. No accepted round-1–3 correction is re-opened. This was a read-only document/fixture review; no validator, runtime integration, git command, deletion or deployment was performed.

Result: complete
