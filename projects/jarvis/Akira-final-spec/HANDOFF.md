# HANDOFF — Akira specification review

**From:** specification agent (AKIRA-SPEC-001 author)
**To:** the next agent / HUMAN running the repository's `spec-review` workflow
**Date:** 2026-10-24
**Status:** draft complete, review not started

---

## 1. What is being handed over

A complete Akira production specification (v0.3, incorporating HUMAN decisions
AKIRA-D4–D6 and the v1 skill catalogue) at:

```
projects/jarvis/JarvisBot/akira/
```

The review input is **`akira/spec.md` v0.3** plus its companion documents in
`akira/docs/` and fixtures in `akira/evals/fixtures/`. `akira/README.md` defines the
reading order, the review instructions, the finding format and the stop rule.

This is a fresh specification review. It is **not** a continuation of the option debate:

- the historical proposal `projects/jarvis/JarvisBot/spec.md` stays untouched;
- `reviews/round-1/` and `reviews/round-2/` stay untouched;
- nothing in the debate is re-litigated; AKIRA-D1 settles the base.

## 2. Settled decision and authority

**AKIRA-D1** (recorded in `projects/jarvis/JarvisBot/decisions.md` and
`akira/decisions.md`): Akeru is the base, the product is Akira, the deliverable is a
production specification and plan. `akira/decisions.md` also records AKIRA-D2 (no deletion without explicit naming),
AKIRA-D3 (no deployment, paid service, real customer contact or paid media job),
AKIRA-D4 (Linux single node, always on), AKIRA-D5 (subscription logins permitted for
personal use) and AKIRA-D6 (private deployment). Reviewers must not raise these as
blocking or major findings.

## 3. What the specification contains

- normative requirements across identity/library, routes, triage, tasks/continuation,
  skills, collaboration/silence, ratings/observer, accounting, specialists, connectors,
  UX, security and operations;
- an inspected-source baseline of Akeru at
  `524eb68a293c4b6a38acf722ab4232cfe5e22625`, with reuse/extend/replace/build decisions,
  licensing/provenance and an explicit "not inspected" list;
- canonical schemas and state machines, interface contracts, UX flows, integration
  matrices, acceptance scenarios and fault injection, a phased backlog with a vertical
  slice, operations runbooks, and an unresolved-decisions register;
- twelve mandatory acceptance scenarios, including the same bot moving
  Codex → Claude → DeepSeek → Grok and back, quota exhaustion mid-task, lost
  acknowledgement after a stub write, skill execution after switching, template
  isolation, justified silence, disputed ratings, observer evaluation, no-double-count
  accounting, early triage, full export/restore, and deletion safety.

## 4. Preconditions for starting the review

The loop launcher requires all of these. None has been done here:

1. **Commit the specification folder** and the CHANGELOG entry, so the worktree is clean.
2. **Create/check out the review branch** (default `agent/loop/akira-review`). The
   launcher refuses a dirty tree and switches only to the configured branch.
3. **Run the preflight** and fix every failing backend:

   ```bash
   generic/run_review_loop.sh projects/jarvis/JarvisBot/akira Akira preflight
   ```

   The preflight checks `codex`, `claude`, `cursor-agent`, the Anthropic consolidator
   profile and the DeepSeek key. It has **not** been run; it spends model calls and needs
   those credentials. Do not claim it passed.
4. **Run the generic tests** if the loop engine was touched (it was not):
   `python3 -m unittest discover -s generic/tests`.

## 5. Starting the review (explicitly authorized, no implementation)

```bash
# one live round: CHATGPT, DEEPSEEK, GROK independently review, CLAUDE consolidates
generic/run_review_loop.sh projects/jarvis/JarvisBot/akira Akira agent/loop/akira-review one

# or up to 5 rounds
generic/run_review_loop.sh projects/jarvis/JarvisBot/akira Akira agent/loop/akira-review full
```

`automation/run_review_loop.sh` wraps the same command. The loop commits and pushes each
review as `<AGENT>: …`; it stops when a round has no `blocking`/`major` finding.

**Not authorized by this handoff:** implementing any phase, installing or deploying
Akeru/Akira, buying services, contacting real people, calling real numbers, paid media,
or deleting data. The specification's own AKIRA-D3 applies to the next agent too.

## 6. What to check before accepting the review result

- The reviews reference requirement IDs and documents, not just general impressions.
- Blocking/major findings are genuinely blocking; minor findings are not hidden majors.
- The consolidation applies accepted changes to `spec.md`/docs (not just to the
  consolidation), bumps the version, and updates the README round.
- Every mandatory scenario is still covered after edits, and the traceability matrix is
  consistent.
- AKIRA-D1/D2/D3 remain intact; no proposal re-opens the base choice or adds a silent
  deletion or external-contact path.
- The "unresolved decisions" register is updated, not bypassed, when a reviewer raises a
  question only HUMAN can answer.

## 7. Known weaknesses a reviewer should expect to find

These are stated honestly rather than hidden; finding them again is fine, but a reviewer
should distinguish "already acknowledged" from "new":

- Effort ranges are estimates without historical velocity (±50% stated).
- Several integration rows (Twilio idempotency, WhatsApp template costs, vendor pricing,
  video provider capabilities) are `U`; no live verification was done.
- The Mastra-routed Claude skill path and Codex `$name` execution are unverified and
  explicitly assigned to tests.
- The rating aggregation and routing thresholds are policy surfaces without HUMAN values;
  defaults are labelled proposed.
- The single-node SQLite assumption is bounded by a workload model, not benchmarked.
- Migration content (personas, memory, shared pages) is draft-by-design; the specification
  never invents the original instructions.

## 8. Files touched by this handoff

New (all under `projects/jarvis/JarvisBot/akira/`): `spec.md`, `README.md`,
`decisions.md`, `HANDOFF.md`, `docs/01`–`docs/14`, `evals/fixtures/*`, `automation/*`,
`reviews/round-1/` (empty, awaiting reviewers).

Changed outside the folder: one append-only `CHANGELOG.md` entry at the repository root.

Nothing else was modified, moved, deleted or reset. No git commit or push was performed by
the specification agent.
