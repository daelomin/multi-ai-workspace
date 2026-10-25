# DEEPSEEK review — round 2

Reviewed `spec.md` v0.4 after `reviews/round-1/CONSOLIDATION.md` and all three round-1 reviews, with `decisions.md`, companion documents `docs/01`–`docs/15`, and the eight records in `evals/fixtures/`. AKIRA-D1–D6 are settled and are not re-opened; U4–U16 are carried forward and none is raised again. The declared `assets/` directory is absent, as recorded in round 1, and no requirement reviewed here depends on it. Records were read as text; no validator, git command, install, deployment, authentication, spend or live integration was run, and no upstream runtime behaviour is asserted.

Findings: one major, five minor.

### DEEPSEEK-1 · Backup procedure omits most of the declared restore set

**Severity:** major

**Finding:** AK-OPS-04 requires a backup of the complete restore set, and `docs/12` §5.1 enumerates seven items. The §5.2 procedure collects item 1 (the SQLite snapshot) and items 2–3 (`attachments/`, `artifacts/`, `memory/`), but no step collects item 4 (secrets, encrypted separately), item 5 (configuration: `settings.json`, routing policy, price tables, `upstream.yaml` + patch list, service unit), item 6 (export bundles/content-addressed files for templates, skills and procedures) or item 7 (git checkpoint refs and objects). The procedure says a backup is complete only when a manifest lists every item, yet it defines no manifest step. A run that follows it can pass the file-copy check while being unable to restore the routing policy, price-table versioning, skill/template content or workspace checkpoint refs that AK-OPS-05 and the restore checks require. The database snapshot is also named only to the day (`state-$(date +%F).sqlite`), so it is not a uniquely named per-run generation as AK-OPS-16 requires. This is a remaining defect in the runbook amended by M1: the append-only rule is now correct, but the generation is incomplete.

**Proposed correction:** Add explicit, checked steps for the separately-encrypted secret set, configuration, the content-addressed template/skill/procedure store (or its export bundle), and the checkpoint-ref list and objects; name the database snapshot with the same per-run timestamp as `$GEN`; generate the manifest with one entry and checksum per §5.1 item; extend T-13 and the T-11 restore checklist to assert every item is present and restorable.

**Evidence:** `spec.md` AK-OPS-04 (1308–1311), AK-OPS-05 (1313–1316), AK-OPS-16 (1363–1366); `docs/12` §5.1 items 1–7 (119–131) compared with §5.2's command block (136–147) and its "manifest lists every item" sentence (149–150); `docs/10` T-11 (182–194) and T-13 (214–224) cover unresolved rows and cross-generation preservation, not the omitted items.

**Confidence:** high

### DEEPSEEK-2 · Failure taxonomy and attempt outcomes are separate closed sets with no mapping

**Severity:** minor

**Finding:** The specification has two closed vocabularies for failure and no mapping between them. `AttemptOutcomeClass` (`docs/04` §4.2) is `completed | failed_capability | failed_tool_contract | failed_context_overflow | failed_auth | failed_quota | failed_rate_limit | failed_network | failed_safety_block | failed_unknown | cancelled | interrupted`. The error taxonomy (`docs/05` §6) is `quota_exhausted | rate_limited | auth_missing | auth_expired | entitlement | capability_gap | tool_contract | context_overflow | network | safety_block | unknown`. The fault matrix and runbooks use the taxonomy names as expected outcomes: F-01 expects `auth_expired`, F-04 `quota_exhausted`, F-05 `tool_contract`, and `docs/12` §7.3 says attempts are "recorded as `auth_expired`". None of those is a valid `AttemptOutcomeClass`, and `auth_missing` and `entitlement` have no stated attempt outcome at all. Separately, AK-TSK-14 says a restart marks a running attempt "failed", while §4.2 names that outcome `interrupted`. An implementer cannot satisfy the closed enum, the fault matrix and the runbook without guessing.

**Proposed correction:** Add one mapping table (error class → attempt outcome) covering every taxonomy value, including `auth_missing`/`auth_expired` → `failed_auth` and an explicit outcome for `entitlement`; use outcome names in F-01/F-04/F-05, `docs/12` §7.3 and AK-TSK-14 (`interrupted`, not "failed"); add a contract test that every fault-matrix expected outcome is a member of the closed set.

**Evidence:** `docs/04` §4.2 (274–282) and §4.1 (transition table); `docs/05` §6 (215–233); `docs/10` F-01 (258), F-02 (259), F-04 (261), F-05 (262); `docs/12` §7.3 (243); `spec.md` AK-TSK-14 (730–734).

**Confidence:** high

### DEEPSEEK-3 · Checkpoint records cannot detect a task-definition mismatch

**Severity:** minor

**Finding:** AK-TSK-14 requires reconciliation of "checkpoint/task version mismatches (surface, do not guess)", and AK-TSK-09 requires a compatibility check before resume. The records cannot express that comparison. `Task` (`docs/04` §3) has no revision or version field; `TaskCheckpoint.taskRevision` holds only `{title, acceptanceCriteria, triageRevision}`, and in `checkpoint.json` `acceptanceCriteria` is a list of ids. A change to a criterion's statement or validation, to the assignee, to dependencies or to another task field leaves every stored field equal, so a resume can continue against a stale task definition while the required check reports no mismatch. The only detectable differences are the title, the id set and the triage revision.

**Proposed correction:** Add a monotonic `revision` (or the event sequence) and a content hash to `Task`, store them in `TaskCheckpoint.taskRevision` (for example `{taskId, revision, contentHash}`), and require resume/reconcile to compare and surface a mismatch before dispatch. Add the stale-definition case to T-02 or T-14.

**Evidence:** `spec.md` AK-TSK-06 (685–689), AK-TSK-09 (701–704), AK-TSK-14 (730–734); `docs/04` §3 `Task` (166–180), `TaskCheckpoint` (224–237), §4.1; `evals/fixtures/checkpoint.json` lines 7–11; `evals/fixtures/task.json` acceptance criteria.

**Confidence:** high

### DEEPSEEK-4 · `Money` is undefined and the cost records use two representations

**Severity:** minor

**Finding:** `Money` is used as a type in `CostSummary` and `UsageRecord.cost` but is never defined, and the two shapes disagree. `docs/04` §1 says money is stored as minor units plus currency; `UsageRecord.cost` uses `amountMinor`, and `usage-record.json` records `"amountMinor": 184`. `CostSummary.subtotals` uses `providerReported: Money | null` and the other fields beside a separate `currency`, and `combinedEstimate` is `{amount: Money; currency: string}` — currency appears twice if `Money` includes it. `task.json` stores plain decimals (`0.82`, `3.12`) in all three cost summaries, with no minor units and no object shape. The fixture cannot be validated against the published `CostSummary`, and changing either side to match the other is a schema break.

**Proposed correction:** Define `Money` once (for example `{amountMinor: integer; currency: string}`) and use it consistently for `UsageRecord.cost`, `CostSummary.subtotals` and `combinedEstimate` (dropping the duplicate `currency` there), then regenerate the fixture amounts in minor units — or define `Money` as a decimal amount and change `UsageRecord`. Add the shape to the fixture validator called for by `docs/10` §4.

**Evidence:** `docs/04` §1 (Money convention), §5 `UsageRecord.cost` (369–370), `CostSummary` (379–386); `evals/fixtures/task.json` cost summaries (62–81); `evals/fixtures/usage-record.json` cost (35–41); `docs/10` §4 (290–294).

**Confidence:** high

### DEEPSEEK-5 · No incident runbook for an unauthorized action

**Severity:** minor

**Finding:** AK-OPS-08 requires incident recovery to be documented for ten classes. `docs/12` §7 documents nine: provider outage, credit exhaustion, credential revocation, database corruption, duplicate/lost external action (covering lost acknowledgement and duplicate send), secret exposure, runaway spend, disk full and deletion accident. There is no runbook for an **unauthorized action** — a bot acting outside its grant, an actor using a scope it should not have, or an unexpected external write. An operator has no specified containment, evidence-preservation or revocation procedure for that class.

**Proposed correction:** Add §7.10 "Unauthorized action": halt dispatch for the affected bot/connector (kill switch if scope is unclear), preserve the event/action/audit records and affected artifact hashes, revoke the credential or grant, reconcile any dispatched/unknown external effect before restart, notify the operator and record the incident. Add the runbook to the release-gate check in `docs/10` §7.

**Evidence:** `spec.md` AK-OPS-08 (1327–1329); `docs/12` §7.1–7.9 (228–280); `docs/10` §7 (357–366); `docs/03` ADR-12 and `docs/05` §8.1 constrain grants, but no response procedure exists.

**Confidence:** high

### DEEPSEEK-6 · Connector effort bases disagree between the backlog and integrations

**Severity:** minor

**Finding:** The connector effort basis is inconsistent between the two planning documents. `docs/11` §10 budgets "2–6 ew per service (see `docs/07` §6.2)" and derives "specialists plus the first three connectors: 12–28 ew" and "full target: 47–78 ew" from that figure. `docs/07` §6.2 prices the same first-party adapters with tests at 4–7 person-days (Gmail), 3–5 (Calendar) and 6–10 (Drive/Sheets): 13–22 person-days, or about 2.6–4.4 engineer-weeks for the first three, not 6–18. The totals cannot be reproduced from the per-service estimate they cite, and the stated ±50% bands do not close the gap.

**Proposed correction:** State which scope the 2–6 ew covers beyond the `docs/07` adapter estimate (auth custody, per-bot grants, health check, ledger integration, docs) and publish the decomposition; then recompute either the per-service range or the 12–28 and 47–78 totals so both documents use one basis. Add a note in `docs/07` §6.2 that its person-days are the adapter-only subset.

**Evidence:** `docs/11` totals (13–15) and §10 P8 (218–228); `docs/07` §6.2 effort column and its "first-party adapter with tests, not vendor onboarding" note (229–249).

**Confidence:** medium

Result: complete
