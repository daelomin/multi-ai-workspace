# ChatGPT Instructions

You are one contributor in a multi-agent workspace.

Always read `MASTER.md`, `TODO.md`, `CONTRIBUTING.md`, and relevant docs before acting.

Priorities:
1. Preserve project continuity.
2. Distinguish verified facts from assumptions.
3. Produce concrete artifacts rather than vague suggestions.
4. Record important changes and unresolved issues.
5. Do not overwrite conflicting work silently.

## Workspace rules

- Work in the project subfolder, `projects/<project-name>/`. Project files do not go at the repo root.
- Do not overwrite another agent's work. Each agent writes only its own files.
- Commit as your own name, subject prefixed with that name.
- If your name is generic (not a specific model id), append `MODEL:` and the model id you are actually running. Example: `GROK: <what changed> MODEL: grok-4.7-high`
- Do not commit under another agent's name.
