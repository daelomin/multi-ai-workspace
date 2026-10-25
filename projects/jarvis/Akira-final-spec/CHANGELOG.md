# Akira final specification review activity

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
