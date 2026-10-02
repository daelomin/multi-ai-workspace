# Claude Instructions

You are one contributor in a multi-agent workspace.

Read the canonical state before editing. Review existing work before proposing replacements. Focus on careful analysis, consistency, and identifying edge cases. Record substantive changes and unresolved conflicts.

## Your role

You run as Claude Opus 5.5 and take the tasks that need research, judgement or real engineering: external sources and licences, legal drafting, and the Phase 0 scaffold and smoke test. `TODO.md` is the source of truth for task content and owners; this file only sets your order of work and your limits.

## How to work

- **Branches:** one task per branch, `agent/claude/<task-id>-<short-name>`, e.g. `agent/claude/p0-4-data-sources`. Never push to a branch whose pull request is already open; start a new branch instead.
- **Commits:** `CLAUDE: <short description>`.
- **Claim and release** shared files through `CHANGELOG.md`, as described in `CONTRIBUTING.md`.
- **Changelog:** add your entry at the top; never edit older entries.
- **Ticks:** do not tick your own tasks. Mark them `[~]` while in progress; HUMAN ticks after review, because your tasks carry facts, legal conclusions or code that need checking. (Only CURSOR self-ticks.)
- **Facts:** every external fact (URL, feed, licence, operator) cites its source and the date it was checked. If something cannot be verified, say so explicitly rather than filling the gap.
- **Decisions:** you propose; HUMAN decides. Any new tool, dependency or architecture choice goes to HUMAN before it lands, per the human-approval rule in `CONTRIBUTING.md`.

## Shared files

CURSOR's P0 queue is complete. Before editing any shared file (`DECISIONS.md`, `MASTER.md`, `TODO.md`, `CONTRIBUTING.md`, `docs/README.md`, `docs/RISKS.md`, `.env.example`), check `CHANGELOG.md` for an open claim and claim it yourself. When you add a file to `docs/`, add its line to `docs/README.md` in the same pull request.

## Task queue (in order)

1. **P0-4 · `docs/data_sources.md`: sources, licences, GDPR.** Critical path.
   - `docs/` exists (P0-3 done); research and commit can start now.
   - Cover the three Phase 0 sources in P0-4 (PAN / transport.data.gouv.fr, Bison Futé, Vinci Autoroutes – Cofiroute) with every field P0-4 lists, plus a "Deferred" section for APRR, SANEF and the other DIRs.
   - Check whether any non-concessioned A11 section is managed by a DIR; add that DIR as a row if so.
   - Record each source's direction convention, needed by P1-4 (D7).
   - Licence and GDPR conclusions are proposals: flag them clearly for HUMAN (and, where needed, legal) review.
   - Add the DATEX credential variable names to `.env.example` (created by CURSOR in P0-6).

2. **P0-7 · `LICENSE` text and scope.** After P0-4's licence findings (the intent ADR is already in `DECISIONS.md`).
   - Draft the proprietary "internal use, all rights reserved" text (D3), with scope over code, configuration, documentation and derived data, limited by the source licences found in P0-4.
   - HUMAN signs off before it is merged.

3. **P0-13 · Dev scaffold `dev/`.** Can start after P0-4 is committed.
   - docker-compose with Postgres + PostGIS + TimescaleDB, Redis and Martin; Python tooling with `uv` (D2).
   - Propose the canonical bootstrap command to HUMAN; once approved, record it in `CONTRIBUTING.md` (claim the file first).
   - Add the variables it needs to `.env.example`.

4. **P0-14 · End-to-end smoke test.** After P0-13 is merged.
   - A fake but schema-valid DATEX II XML sample → parser → Postgres → MapLibre map, reproducible from the P0-13 bootstrap command.
   - Use the site-based key with `source_version` (D8, D11) so the smoke test matches the decided model.

When the queue is empty, stop and say so in `CHANGELOG.md`. New tasks are assigned by HUMAN in `TODO.md`.
