# Gemini Instructions

You are one contributor in a multi-agent workspace.

Read the canonical state before editing. When research is needed, distinguish source-backed facts from inference. Keep changes scoped and document important findings for the other agents.

## Workspace rules

- Work in the project subfolder, `projects/<project-name>/`. Project files do not go at the repo root.
- Do not overwrite another agent's work. Each agent writes only its own files.
- Commit as your own name, subject prefixed with that name.
- If your name is generic (not a specific model id), append `MODEL:` and the model id you are actually running. Example: `GROK: <what changed> MODEL: grok-4.7-high`
- Do not commit under another agent's name.
