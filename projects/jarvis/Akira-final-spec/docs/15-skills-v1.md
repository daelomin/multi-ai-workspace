# 15 — Akira v1 skill catalogue and `SKILLS.md`

**Status:** draft v0.3 · **Normative:** `spec.md` AK-SKL-01..14 · **Schema:** `docs/04-data-model.md` §2.

This document answers one question: **which skills ship in Akira v1, and what does
`SKILLS.md` contain?**

It is a specification of the catalogue, not evidence that any skill executes. Every
package below still needs its validation fixture to pass on the routes listed before it
may be marked available (`docs/10-tests-and-acceptance.md` T-04).

**Fixture status:** the `fixtures/skill-<name>/` paths in the tables are the planned
locations under `evals/fixtures/`. Only the `sheet-ops` package example exists today
(`evals/fixtures/skill-package.json`); the other fixture directories are created with
their skill in Phase 4 and must not be presented as present in this draft.

---

## 1. What `SKILLS.md` is

There is exactly **one generated `SKILLS.md`** at the registry root (e.g.
`<state>/skills/SKILLS.md`). It is a human- and bot-readable index generated from the
skill registry, never hand-edited, and **never the execution contract**.

Each entry in `SKILLS.md` has:

| Field | Example |
|---|---|
| Name and version | `sheet-ops` 1.3.0 |
| Purpose (one line) | Read/update reviewed Google Sheets ranges with citations |
| Triggers | "update the sheet", "read the range" |
| Requires | tools + connectors + runtime |
| Route support | `claude: native-verified`, `codex: native-unverified`, `deepseek: prompt-injected`, … |
| Validation | fixture name + last verified date |
| Provenance | authored / vendored (with license) |
| Status | `v1-mandatory`, `v1-conditional`, `deferred`, `deprecated` |

A literal file named `SKILLS.md` is **not** discovered as a skill by Claude Code, Codex
or Grok (none of the inspected mechanisms reads it — `docs/02` B-11..B-14). Akira uses
`SKILL.md` packages for execution and generates `SKILLS.md` for humans and for bots that
want an index. This substitution is stated in the skill settings screen.

---

## 2. v1 mandatory skills (ship in every v1 build)

These require no first-party connector beyond tools Akira already exposes (workspace
read/write, shell, WebFetch) and must work on **every supported route** (native where
available, prompt-injected otherwise).

| # | Skill | Purpose | Triggers | Requires | Expected route support | Validation fixture |
|---|---|---|---|---|---|---|
| S1 | `task-plan` | Turn an intent into a bounded plan with acceptance criteria, validation per step, risks and open questions | any non-trivial task at triage | none (text) | all routes; text-only, so native or injected | `fixtures/skill-task-plan/`: intent with 3 constraints → ≤7 steps, each with a validation, no invented dependency |
| S2 | `readiness-check` | Score a brief/spec against the 8 readiness criteria and return `ready` / `ready-with-risks` / `not-ready` with named gaps | before a specification-led handoff | none (text) | all routes | `fixtures/skill-readiness/`: deliberately incomplete brief → `not-ready` + the 3 missing criteria |
| S3 | `evidence-brief` | Answer a question as a cited brief: sources, confidence, contradictions, unanswered parts | research, "find out", "compare" | `web.fetch` | Claude/Codex/Grok native; DeepSeek/Kimi/OpenCode Go injected | `fixtures/skill-evidence/`: 3 synthetic sources incl. one contradiction → all cited, conflict flagged |
| S4 | `challenge-review` | Produce a structured peer challenge: claim, evidence, objection, proposed test, severity | review, "challenge", "poke holes" | none (text) | all routes | `fixtures/skill-challenge/`: a flawed artifact → ≥1 major finding with evidence + test, no unsupported blocking |
| S5 | `code-change` | Bounded repository change: read, plan, patch, run tests, checkpoint, report diff | code task assigned to an engineer bot | workspace read/write, shell, test runner | tool-capable routes only (T2 floor) | `fixtures/skill-code/`: failing test → patch passes, diff confined to target files, no secrets |
| S6 | `code-review` | Review a diff for correctness, tests, risk; findings with severity and evidence | "review this PR/diff" | workspace read, diff | tool-capable routes | `fixtures/skill-review/`: seeded defect → found; no false blocking findings |
| S7 | `qa-regression` | Turn acceptance criteria into a test plan, execute it, attach evidence | QA task, pre-release check | shell/test runner, artifact store | tool-capable routes | `fixtures/skill-qa/`: 4 criteria → 4 covered checks + evidence links |
| S8 | `data-extract` | Extract structured data from local CSV/JSON with provenance, null policy and a schema | data mining on files | workspace read, file tools | tool-capable routes | `fixtures/skill-data/`: messy CSV → schema-valid output, `unknown` handling explicit |
| S9 | `scorecard` | Build the weekly bot scorecard from task ratings, rework and usage (the migrated routine) | scheduled Monday run | ratings/usage queries | all routes (data access is server-side) | `fixtures/skill-scorecard/`: fixture ratings/usage → per-bot rows with sample size, no double-counted child cost |
| S10 | `handoff-pack` | Package a task for another bot: state, decisions, artifacts, open questions, next step | reassignment, end of shift | checkpoint + artifact access | all routes | `fixtures/skill-handoff/`: partial task → pack has every checkpoint field; resume on a stub route succeeds |

**Why these ten.** They cover the actual work the existing team does (planning,
challenging, engineering, QA, data, scorekeeping, handoff) and every one is verifiable
with a deterministic fixture. They are also the skills the routing/eval loop needs in
order to calibrate cheap models: a plan, a challenge, a review and an extraction are
representative task shapes.

---

## 3. v1 conditional skills (ship only with their connector)

These are specified for v1 but must **not** be listed as available until the corresponding
connector reaches workflow-verified status (`docs/07` §6). If a connector slips, the
skill slips to v1.1 — it is not replaced by a browser-automation imitation.

| # | Skill | Purpose | Requires | Validation fixture | Depends on |
|---|---|---|---|---|---|
| S11 | `sheet-ops` | Read a reviewed range, transform, write only a reviewed range, cite range and sheet id | Google Sheets connector + `sheet.read`/`sheet.write` | `fixtures/skill-sheet/` (existing example in `evals/fixtures/skill-package.json`) | Sheets connector (P8) |
| S12 | `inbox-triage` | Classify inbox items, summarise threads, draft replies; send requires approval | Gmail connector (`gmail.readonly`, `gmail.compose`/`gmail.send`) | `fixtures/skill-inbox/`: 6 synthetic threads → correct labels, drafts, no send without approval | Gmail connector (P8) |
| S13 | `calendar-plan` | Read events/free-busy, propose slots for a task; writes approval-gated | Calendar connector | `fixtures/skill-calendar/`: conflicting events → 2 viable slots, timezone correct | Calendar connector (P8) |
| S14 | `release-checklist` | Verify release gates against repo, CI and issues; produce an evidence table | GitHub connector + CI access | `fixtures/skill-release/`: one red check → gate fails with the check linked | GitHub connector (P8) |

Support for S11–S14 is connector-dependent, not route-dependent: they work on any route
whose floor includes the connector's tools, with the skill's support level recorded per
route as usual.

---

## 4. Route support policy for v1

| Skill class | Required evidence before "available" |
|---|---|
| Text-only (S1, S2, S4, S9, S10) | passes on **all four** routes (Codex, Claude, DeepSeek, Grok), native or injected; fixture output validated |
| Tool + workspace (S5–S8) | `native-verified` on at least one route; `prompt-injected` verified on the other supported routes; resource access proven |
| Connector-dependent (S11–S14) | `native-verified` or `prompt-injected` on the routes the bot may use; connector auth + a real read proven first |

A skill with no passing fixture is `deferred`, not "experimental". The UI shows the
support level and the last verification date on the skill row and in the generated
`SKILLS.md`.

---

## 5. What ships in the first vertical slice

The slice (`docs/11` §13) ships **two** skills:

- **S1 `task-plan`** — proves the skill pipeline end-to-end on a text-only skill across
  all four routes without depending on a connector.
- **S11 `sheet-ops`** — proves native execution and resource access on Claude, plus the
  `prompt-injected` path on DeepSeek, using the existing fixture.

The rest of the catalogue follows in P4 once the registry and adapters are in place.

---

## 6. Explicitly not in v1

| Skill | Why deferred | Trigger to add |
|---|---|---|
| `call-script` (PSTN conversation script + consent handling) | P7 telephony adapter not in v1 unless the specialist lands; recording consent policy needed | Telephony adapter accepted and a test number verified |
| `whatsapp-template-ops` (create/submit templates, sender registration) | Administration capability is separate from messaging and vendor-gated | Meta Business admin scopes verified |
| `video-storyboard` / `video-assemble` | Video workflow is P7 and approval-gated; the skill depends on job semantics | First video provider adapter + render approval policy |
| `image-prompt-pack` | Image generation exists as a tool; a dedicated skill adds little until brand/style assets exist | A repeatable brand style guide + artifact library |
| `deep-research` (multi-hour autonomous research) | Expensive, needs triage/budget controls and better citation evals | Cost policy (U4) + evidence-brief eval data |
| Vendored third-party skill packs | License/provenance review per pack | A pack with a clear license and a passing fixture |

Deferred skills are not silently dropped: they stay in this table with the trigger.

---

## 7. Provenance, licensing and updates

- **Authored** skills belong to the Akira project, carry an internal license, and are
  versioned by content hash.
- **Vendored** skills require a recorded license, source URL and a review; a vendored
  skill that cannot be validated is not installed.
- Skills are data: adding or updating one is a registry operation with a new version,
  not a server release. A skill version change invalidates its per-route verification
  evidence until re-run (`docs/04` §2, `docs/07` §4).
- Deprecation is a status, not a deletion: old versions stay resolvable for tasks that
  pinned them (AKIRA-D2).

---

## 8. Catalogue ownership

| Role | Responsibility |
|---|---|
| Operator / bot-admin | approves a new skill version and its tool grants |
| Skill author | writes package + fixture, records provenance |
| Reviewer | checks instructions for injection risk, scope and resource use |
| QA | runs the fixture on the required routes and records evidence |
| Observer | may propose skill refinements; cannot publish or activate them |

The catalogue is exported in the full-team bundle and restored with its support matrix;
a restore on a different host marks native verifications stale until re-run (CLI or
route changes invalidate them).
