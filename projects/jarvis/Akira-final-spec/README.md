# Akira specification review

**Round 4** — independent review of Akira **v0.6**, the production specification for
the Akeru spin-off (rounds 1–3 reviewed v0.3, v0.4 and v0.5 and are consolidated).

**Workflow status:** round 3 consolidated by **CHATGPT**, completing CLAUDE's partial
v0.6 edits after a credit-exhaustion handoff. All 21 findings are accounted for, including
**two major findings** about the same action-ledger crash window. Review convergence has
**not** been reached. The next review input is **`spec.md` v0.6**, with its companion
contracts in `docs/` and representative records in `evals/fixtures/`.
AKIRA-D1–D6 are settled and applied. The single carried-forward open HUMAN list is in
`reviews/round-3/CONSOLIDATION.md` §2 (U4–U16); HUMAN answers are not awaited by the loop.

Historical material is preserved and out of scope: the original options proposal and completed debate in the separate `jarvisbot` worktree (`projects/jarvis/JarvisBot/`). Do not review the old proposal as Akira's specification,
and do not rerun the option assessment.

---

## Current round

**Round 4**: reviewers read `spec.md` **v0.6** independently, after reading
`reviews/round-3/CONSOLIDATION.md` and the prior consolidations, and write
`reviews/round-4/<AGENT>.md`. Do not repeat accepted findings unless the correction
remains incomplete, with new evidence. Round 3 is complete (CHATGPT 3 minor; DEEPSEEK
1 major + 8 minor; GROK 1 major + 8 minor; all accepted). Open HUMAN decisions are carried
forward without deciding them. This consolidation did not launch reviewers or round 4.

**Imported-source note (2026-10-25).** The source folder had a CHATGPT review of v0.2. That historical review is not present in this registered loop and is not a completed pass here. All reviewers in this loop independently review the imported v0.3 package. At import time the preflight had passed and no live round had started; this is
historical context, superseded by the workflow status above.

## Documents and reading order

1. `spec.md` — normative requirements (read first, completely).
2. `decisions.md` — HUMAN-settled decisions (fixed; do not re-open).
3. `docs/01-product-scope.md` — scope, users, workflows, success measures.
4. `docs/02-akeru-baseline.md` — pinned-revision source inspection, reuse matrix, gap matrix.
5. `docs/03-architecture.md` — components, boundaries, ADR records, rejected alternatives.
6. `docs/04-data-model.md` — schemas, state machines, invariants.
7. `docs/05-interfaces.md` — command/adapter contracts, error taxonomy, versioning.
8. `docs/06-ux.md` — flows and wireframes.
9. `docs/07-integrations.md` — routes, skills, connectors, specialists, support levels.
10. `docs/08-collaboration-and-accountability.md` — rooms, silence, challenge, ratings, observer.
11. `docs/09-accounting.md` — ledger, attribution, worked example.
12. `docs/10-tests-and-acceptance.md` — acceptance scenarios, fault matrix, traceability.
13. `docs/11-backlog.md` — phases, effort, exit criteria, vertical slice, deferrals.
14. `docs/12-operations.md` — security, deployment, backup/restore, migration, incidents.
15. `docs/13-open-decisions.md` — resolved HUMAN answers and the remaining reversible defaults.
16. `docs/14-evidence-log.md` — exactly what was inspected and what was not.
17. `docs/15-skills-v1.md` — the v1 skill catalogue and what `SKILLS.md` contains.

`evals/fixtures/*.json` are representative records; validate them against the schemas
while reviewing.

## What this specification is, and is not

It is the implementation baseline for Akira: the complete target, the Akeru components to
reuse/extend/replace/build, the gaps, the acceptance criteria and the phase plan.

It is not a deployment, an implementation, or a claim that any capability works. Nothing
was installed or executed. Evidence labels in `spec.md` §0 state what is inspected (`V`),
documented (`D`), maintainer-reported (`M`), reasoned (`R`), assumed (`A`) or unknown (`U`).

---

## Instructions for the reviewing AI

**Scope.** Assess whether this specification is complete, correct, implementable and
safe for Akira's stated goals. Judge the design against the requirements, not against
your preferred architecture. The base choice (Akeru) is fixed by AKIRA-D1.

**Do not re-open** (these are settled and must not be raised as blocking/major):

- that Akeru is the base and the product is Akira;
- the no-deletion rule and the prohibition on real customer communication, paid jobs or
  deployment in this work;
- numbers HUMAN has not supplied (budgets, weights, thresholds, SLO values). Challenge the
  *policy surface* and the labelled defaults, not the absence of a HUMAN-approved number.

**What to check, in priority order.**

1. Does every HUMAN requirement in `spec.md` §2 map to a requirement, and does the
   requirement have an implementable design and a test?
2. Is there exactly one authority for dispatch, retries, task state and usage? Find any
   place the design accidentally creates a second one.
3. Is "same bot across providers" actually preserved by the proposed mechanisms
   (state ownership, checkpoint, persona, memory, skills), or only asserted?
4. Are external side effects handled honestly (idempotency, unknown, reconciliation)?
5. Are routing/adequacy/triage decisions evidence-based, and is the credit-exhaustion
   path free of silent quality degradation?
6. Do skills actually execute per route, and is the support-level claim verifiable?
7. Does silence hide nothing, and can ratings/observer be gamed?
8. Is accounting free of double counting and invented precision? Check the worked example.
9. Are migration and restore complete, and is what cannot be imported stated?
10. Are security, approvals, secrets and operations sufficient for a production spin-off?
11. Are effort, dependencies and exit criteria plausible and internally consistent?
12. Are unresolved decisions honest, scoped and non-blocking where claimed?

**Finding format.** Use the repository format:

```
### <AGENT>-<n> · short title
**Severity:** blocking | major | minor
**Finding:** what is wrong and where (requirement ID, document section).
**Proposed correction:** the smallest change that fixes it.
**Evidence:** file/section/URL and what it shows.
**Confidence:** high | medium | low
```

If you find nothing material: `Findings: none`.

End the review with `Result: complete` on its own line. A review that lacks it is
incomplete and will be rejected by the loop.

**Severity discipline.** `blocking`/`major` keep the loop running — use them only for
problems that would make the spec unsafe, wrong or unimplementable. Everything else is
`minor`. Do not repeat findings already accepted and merged in a previous consolidation.

**Evidence discipline.** Upstream repository claims are maintainer-reported until
inspected. Do not assert runtime behaviour that this specification explicitly marks
unverified; if you inspect the pinned source, cite the path and SHA
`524eb68a293c4b6a38acf722ab4232cfe5e22625`. Do not install, deploy, authenticate, spend,
call real numbers, message real people or delete anything.

**Decisions and changes.** Reviewers write only their own review file and a CHANGELOG
entry. Do not edit `spec.md`, docs, fixtures, another review or `decisions.md`. The
consolidator (CHATGPT for the round-3 recovery handoff) applies accepted findings to `spec.md`/docs and writes the
consolidation.

---

## Stop rule and consolidation

The loop stops when a round has no `blocking` or `major` finding, or after the configured
maximum number of rounds. The authorized consolidator then consolidates: writes `reviews/round-N/CONSOLIDATION.md`,
applies accepted changes, bumps the spec version, and updates "Current round" here.
HUMAN decisions are never waited for during the loop; they are carried forward in the
consolidation.

## Running the loop

This folder's `loop.json` is authoritative. From this folder:

```bash
bash automation/run_review_loop.sh preflight
bash automation/run_review_loop.sh one
bash automation/run_review_loop.sh full
```

The wrapper resolves the shared toolkit and reads the project path/name/branch from the manifest. Preflight only tests backends; a live round requires one or full. Reviewers append this project CHANGELOG.md; the consolidator may edit only the declared specification/companion paths. Unrelated root task queues are outside this loop's scope.

## Ownership and preservation

| Who | Writes |
|---|---|
| CHATGPT / DEEPSEEK / GROK | only their own `reviews/round-N/<AGENT>.md` + CHANGELOG entry |
| Consolidator (CHATGPT completed round 3 after CLAUDE handoff) | `spec.md`, `docs/`, `evals/`, `assets/`, `README.md`, round consolidation and project CHANGELOG |
| HUMAN | `decisions.md`, merges |

Earlier proposals, reviews, logs and this folder's history are preserved. Nothing is
deleted, pruned or reset (AKIRA-D2).
