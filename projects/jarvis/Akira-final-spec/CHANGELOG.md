# Akira final specification review activity

## 2026-10-25 — Round 4 specification review

Agent: CHATGPT

Reviewed v0.6 after all round-3 reviews and consolidation and the prior consolidations,
with settled decisions, all fifteen companion documents and eight JSON fixtures within
the manifest scope. Recorded three minor findings: missing sandbox-hour/host-month ledger
units; a category drill-down shape that cannot preserve multiple currencies; and an
unknown-action fixture note suggesting retry after a second read or 24 hours without
proof of non-acceptance. No blocking or major findings. AKIRA-D1–D6 remain fixed and
U4–U16 carried forward unchanged. Read-only checks passed for JSON parsing/schema versions,
task/checkpoint identity, summary arithmetic, selected skill-floor evidence, exact sub-cent
arithmetic and 209 unique requirement IDs. Review complete at `reviews/round-4/CHATGPT.md`;
specification and other inputs unchanged. No git commands, deletion, live integrations,
authentication, paid operations or deployment performed.

## 2026-10-25 — Round 3 consolidation completed after recovery handoff

Agent: CHATGPT

Completed the same v0.6 consolidation begun by CLAUDE before weekly-credit exhaustion;
preserved and assessed its partial edits without bumping to v0.7. Read all three completed
reviews and manifest inputs. Accepted all 21 findings (2 major, 19 minor), grouped into
11 changes with complete traceability in `reviews/round-3/CONSOLIDATION.md`. Completed
write-ahead action ordering and recovery guards; safety-control commands; route auth,
options, provenance and per-skill floors; within-class cost-range role defaults; inclusive
and root-cohort CPAT formulas; exact fixed-point usage costs and observer Money; projected
skill labels; silence mapping with legacy alias; seven-item checked backup/manifest
contract; and a typed 18-row fault matrix. Aligned companion contracts and JSON examples,
retaining Codex skill support as unverified rather than inventing evidence. Settled
AKIRA-D1–D6 were already applied; U4–U16 carried forward unchanged, none decided here.
GROK served-model provenance is unverified and recorded. README now says Round 4 reviewing
v0.6 under `reviews/round-4/`; convergence is not claimed and no further review was run.
Static checks passed for all eight JSON fixtures, required contract fields and semantic
invariants, exact sub-cent arithmetic, 18 fault rows and 209 requirement IDs. These are
specification checks, not runtime acceptance tests. No git commands, deletion, live
integration, deployment or out-of-project activity recording performed.

## 2026-10-25 — Round 3 specification review

Agent: GROK

Reviewed v0.5 after the round-1 and round-2 consolidations, with settled decisions, all fifteen companion documents and eight JSON fixtures within the manifest scope. Recorded one major finding (an external send can complete before the action ledger durably records `dispatched`, so startup reconciliation can miss it and send again) and eight minor findings covering cross-auth-class specification-led ranking, the undefined route `support` field, the checkpoint backup directory, the attempt-outcome membership test, the inclusive-cost formula versus the worked example, sub-cent rounding, silence-code cardinality, and verified projected skills. No blocking findings. A requirement-heading count is 209. Review complete at `reviews/round-3/GROK.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 3 specification review

Agent: DEEPSEEK

Reviewed v0.5 after the round-1 and round-2 consolidations, with settled decisions, all fifteen companion documents and eight JSON fixtures within the manifest scope. Recorded one major finding (the action ledger has no write-ahead ordering, so a crash after a send but before the `dispatched` record can leave a sent action in `intent`, outside startup reconciliation) and eight minor findings covering the missing kill-switch and quarantine-release commands, missing `auth_class` on route records and the cross-auth-class role default, the undefined `RouteDecision.support` field and its floor-fixture contradiction, AK-ACC-05/AK-ACC-14 formula drift from the normative worked example, decimal observer-proposal money, the unrepresentable verified-projected support level, the false one-to-one silence-code mapping, and the backup completeness/manifest mismatch. No blocking findings. Read-only checks confirmed the 209 requirement count, traceability coverage, fixture syntax/schema versions, task/checkpoint identity and the docs/09 accounting arithmetic. Review complete at `reviews/round-3/DEEPSEEK.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 3 specification review

Agent: CHATGPT

Reviewed v0.5 after the round-2 reviews and both consolidations, with settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded three minor findings: the checkpoint-backup output directory is not created; the fault matrix mixes attempt outcomes with other component states despite its enum-membership gate; and integer-minor-unit cost storage lacks a sub-cent precision/rounding policy. No blocking or major findings. Read-only checks confirmed JSON parsing, schema versions, task cost-subtotal arithmetic and task/checkpoint revision/hash agreement. Review complete at `reviews/round-3/CHATGPT.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 2 consolidation

Agent: CLAUDE

Consolidated the three round-2 reviews (19 findings: CHATGPT 4, DEEPSEEK 6, GROK 9; all accepted, none rejected) into `reviews/round-2/CONSOLIDATION.md` and bumped `spec.md` to v0.5. Backup generation is now complete and per-tree with a per-run database snapshot and manifest; recovery quarantine covers every task that could have acted and constrains startup reconciliation; error classes map to attempt outcomes with reconciliation guards on retry, fallback, cancel and new attempts; the specification-led guard has a route `role` predicate; CPAT uses a record-union cohort; tasks carry `revision`/`contentHash` in checkpoints; `Money` and skill support entries have one shape; runbook 7.10 (unauthorized action) added; connector effort uses one basis. Updated docs 04, 05, 07, 09, 10, 11, 12 and fixtures task, route-decision, skill-package, checkpoint. `decisions.md` (AKIRA-D1–D6) was already applied; no change. Open HUMAN decisions U4–U16 carried forward unchanged. GROK's served model was unverified and is noted in the consolidation. README set to Round 3 on v0.5. No git commands run.

## 2026-10-25 — Round 2 specification review

Agent: GROK

Reviewed v0.4 after the round-1 consolidation, with settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded four major findings (the backup procedure is not a faithful complete generation; startup reconciliation can still dispatch during recovery quarantine; unresolved external actions can still be followed by another send; the specification-led dispatch guard has no decision procedure) and five minor findings covering CPAT descendant overlap, checkpoint task-definition identity, the undefined Money shape, per-route skill verification records, and the missing unauthorized-action runbook. A read-only rsync dry run confirmed colliding relative paths; SQLite VACUUM INTO behaviour was checked against the published language page. No validator, git command or runtime integration executed. Review complete at `reviews/round-2/GROK.md`; specification and other inputs unchanged.

## 2026-10-25 — Round 2 specification review

Agent: DEEPSEEK

Reviewed v0.4 after the round-1 consolidation, with settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded one major finding (the backup procedure collects only the database and three file trees, omitting configuration, secrets, content-addressed skill/template files and checkpoint refs, and names the database snapshot only to the day) and five minor findings covering the unmapped failure/attempt-outcome vocabularies, the missing task-revision link for checkpoint mismatch detection, the undefined `Money` representation in cost schemas and fixtures, the absent unauthorized-action incident runbook, and inconsistent connector effort bases. Records read as text; no validator, git command or runtime integration executed. Review complete at `reviews/round-2/DEEPSEEK.md`; specification and other inputs unchanged.

## 2026-10-25 — Round 2 specification review

Agent: CHATGPT

Reviewed v0.4 after the round-1 reviews and consolidation, with settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded one major finding (backup command merges source directory trees) and three minor findings covering CPAT descendant overlap and route attribution, recovery-checklist coverage, and remaining fixture/schema mismatches. JSON parsing, schema-version presence and cost-subtotal arithmetic checked; rsync destination layout inspected with a read-only dry run. Review complete at `reviews/round-2/CHATGPT.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 1 consolidation

Agent: CLAUDE

Consolidated the three round-1 reviews (38 findings, all accepted; none rejected) into `reviews/round-1/CONSOLIDATION.md` and bumped `spec.md` to v0.4. Added AK-OPS-15..17 (recovery quarantine, append-only backup, guarded `bot.delete`), separated route availability from capability, split cost summaries by unit and provenance (new `coordination` category, corrected coverage/CPAT formulas), added task resume and attempt-outcome transitions, and added T-13..T-15 and F-16. Updated companion docs 02, 04, 05, 06, 08, 09, 10, 11, 12, 13 (U16), 15 and all fixtures in `evals/fixtures/`. `decisions.md` (AKIRA-D1–D6) was already applied; no change. Open HUMAN decisions U4–U16 carried forward. GROK's served model was unverified and is noted in the consolidation. README set to Round 2 on v0.4. No git commands run.

## 2026-10-25 — Round 1 specification review

Agent: GROK

Reviewed v0.3, settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded seven major findings (backup pruning, server-callable hard delete, snapshot restore replay, mid-stream retry of external effects, task resume and not-ready transitions, quota stored as a capability-floor failure, and mixed-unit cost totals) and seven minor findings covering usage categories, coverage and CPAT, traceability, readiness criteria, rating scales, maintenance effort and routing defaults. Review complete at `reviews/round-1/GROK.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 1 specification review

Agent: DEEPSEEK

Reviewed v0.3, settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded five major findings (backup pruning, server-callable hard delete, quota recorded as a capability-floor failure, missing coordination category, and mixed-unit cost totals driving route selection) and eleven minor findings covering accounting consistency, evidence and traceability, silence, disputes, audit coverage, migration and phase/slice planning. Review complete at `reviews/round-1/DEEPSEEK.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Round 1 specification review

Agent: CHATGPT

Reviewed v0.3, settled decisions, all companion documents and eight JSON fixtures within the manifest scope. Recorded two major findings (deletion-enabled backup and external-effect replay after snapshot restore) and six minor findings covering accounting, recovery transitions, fixture contracts and skill traceability. Review complete at `reviews/round-1/CHATGPT.md`; specification and other inputs unchanged. No git commands or runtime integrations executed.

## 2026-10-25 — Generic loop setup

Preserved the specification package and preflight records. Added a portable manifest, project-scoped activity and corrected instructions. This registered loop has no completed reviews; its preflight passed. No live review was launched by this migration. Original operational files are retained under automation/logs/generic-migration-*/.
