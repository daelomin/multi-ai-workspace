# Cursor Instructions

You are one contributor in a multi-agent workspace, running as Cursor Auto.

Read `MASTER.md`, `TODO.md`, `CONTRIBUTING.md` and the recent `CHANGELOG.md` entries before every task. `TODO.md` is the source of truth for task content and owners; this file only sets your order of work and your limits.

## Your role

You handle well-specified edits: the task text in `TODO.md` already says what to write. You do not research external facts, choose new tools or dependencies, or make decisions. If a task needs any of those, stop and say so in your `CHANGELOG.md` entry instead of guessing.

## How to work

- **One task (or one listed bundle) per branch:** `agent/cursor/<task-id>-<short-name>`, e.g. `agent/cursor/p0-3-docs-move`.
- **Commits:** `CURSOR: <short description>`.
- **Claim and release** each shared file through `CHANGELOG.md`, as described in `CONTRIBUTING.md`.
- **Changelog:** add your entry at the top; never edit older entries.
- **Do not tick boxes in `TODO.md`.** HUMAN ticks after review.
- **Do not push to a branch whose pull request is already open**; start a new branch instead.
- **Never invent values:** URLs, licence terms, metric thresholds, costs, owners. Leave `______` blanks as they are.

## Files you must not edit

These belong to other owners in `TODO.md`:

- `docs/data_sources.md` (P0-4, CLAUDE)
- `LICENSE` (P0-7 text, CLAUDE)
- `dev/` and any smoke-test code (P0-13, P0-14, CLAUDE)

## Task queue (in order)

Start each task only when the one before it is merged into `main`.

1. **P0-5 · Coordination rules.** Done (PR #3); awaiting HUMAN review. Nothing to do.

2. **P0-1 + P0-2 + P0-7 (intent ADR only) · Decision records.** One branch, one commit.
   - In `DECISIONS.md`, record decisions D1–D11 from the "Resolved decisions" table in `TODO.md`, one ADR per decision, dated 2026-10-03, decided by HUMAN. Use the ADR title given in P0-1 for D1, and the migration note given in P0-2 for D2.
   - In `MASTER.md`, add the matching sentence required by P0-1 (stack frozen for Phases 0–1, A11 pilot only), and remove any wording that calls the stack "proposed".
   - Do **not** create a `LICENSE` file.

3. **P0-3 · `docs/` folder.**
   - Move `SPEC_PHASES.md` to `docs/SPEC_PHASES.md` with `git mv`.
   - Leave a short root `SPEC_PHASES.md` stub pointing to the new path.
   - Update every link to the old path (search the whole repo, including `README.md`, `MASTER.md`, `AGENT_PROMPT.md`, `agents/`, `TODO.md`).

4. **P0-8 · GO/NO-GO checklist (writing only).**
   - Create `docs/phase0_go_no_go.md` containing exactly the checklist in P0-8, plus an empty sign-off line (name, date).
   - Do not tick anything; signing is HUMAN's.

5. **P0-6 · Credential policy and secret scanning.**
   - Add the policy text from P0-6 to `CONTRIBUTING.md`.
   - Add secret scanning with **gitleaks**: a pre-commit hook config and a GitHub Actions workflow that runs on pull requests.
   - Create `.env.example` with only a header comment for now; variables are added later by P0-4 and P0-13.
   - Check that `.env` is in `.gitignore`.

6. **P0-10 · `docs/README.md` index.** Once `docs/` contains at least the spec and the checklist: one line per file in `docs/` saying what it is and when to read it.

7. **P0-11 · `docs/RISKS.md`.**
   - Create the table with the columns given in P0-11.
   - Fill it only with risks already written in `TODO.md` or `DECISIONS.md`, citing the item each comes from.
   - Leave Likelihood and Impact as `?` for HUMAN.

When the queue is empty, stop and say so in `CHANGELOG.md`. New tasks are assigned by HUMAN in `TODO.md`.
