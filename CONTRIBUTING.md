# Multi-AI Collaboration Protocol

## Roles
Humans own final decisions. AIs research, draft, review, implement, test and propose changes.

## Source of truth
`MASTER.md` is authoritative for current project state. Detailed material belongs in `docs/`.

## Before editing
Every agent MUST:
1. Read `MASTER.md`.
2. Read `TODO.md`.
3. Read relevant documents.
4. Check recent `CHANGELOG.md` entries.

## Editing rules
- Make the smallest coherent change.
- Preserve existing correct work.
- Do not delete another agent's work merely to replace it with a preferred approach.
- If two approaches conflict, document the conflict in `DECISIONS.md` and mark it for human review.
- Never claim a task is completed unless it was actually completed or verified.

## Change attribution
Use one of these identities:
- HUMAN
- CHATGPT
- CLAUDE
- GEMINI
- DEEPSEEK
- GROK
- CURSOR

## Handoff protocol
When handing work to another AI, add a short entry to `CHANGELOG.md` containing:
- date
- agent
- files changed
- what changed
- remaining work
- verification status

## Git protocol
Preferred branch naming:
`agent/<agent-name>/<short-task>`

Commit format:
`<AGENT>: <short description>`

Examples:
`CHATGPT: add station data schema`
`CLAUDE: review API fallback logic`
`GEMINI: document deployment steps`
`DEEPSEEK: optimize GeoJSON pipeline`
