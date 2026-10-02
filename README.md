# Multi-AI Collaborative Workspace

A shared workspace designed for ChatGPT, Claude, Gemini, DeepSeek and human collaborators.

**Current project:** Plateforme nationale de trafic routier — phased delivery in [`docs/SPEC_PHASES.md`](docs/SPEC_PHASES.md).

## Core rule
`MASTER.md` is the canonical project state. AI agents must read it before making changes and must record meaningful changes in `CHANGELOG.md`. Phase detail lives in `docs/SPEC_PHASES.md` (root `SPEC_PHASES.md` is a redirect stub).

## Structure
- `MASTER.md` — canonical project brief and current state
- `docs/SPEC_PHASES.md` — detailed phase plan (0–7) and acceptance criteria
- `DECISIONS.md` — durable decisions and rationale
- `TODO.md` — task queue
- `CHANGELOG.md` — chronological changes
- `CONTRIBUTING.md` — collaboration protocol
- `agents/` — AI-specific operating instructions
- `docs/` — detailed documents (spec, data sources, checklists)
- `.github/` — optional GitHub automation/templates

## Recommended workflow
1. Pull/read the latest repository state.
2. Read `MASTER.md`, `TODO.md`, and relevant docs.
3. Work on one clearly scoped task.
4. Update affected documentation.
5. Update `CHANGELOG.md` and `TODO.md` when appropriate.
6. Commit with a clear message.
7. Never silently overwrite another agent's work.
