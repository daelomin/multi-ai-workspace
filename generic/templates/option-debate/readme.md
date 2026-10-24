# {name} — option assessment and debate

The deliverable is an argued recommendation for HUMAN's choice. `spec.md` is the input proposal, not an approved implementation specification.

## Current round

**Round 1** — option assessment and debate on proposal v0.1. Files go in `reviews/round-1/`.

## Workflow

`workflow.json` selects `option-debate`, phase `options`. These instructions override old spec-refinement rules.

1. **Independent proposals:** every reviewer compares ALL original options against the same criteria and names one preferred primary option, its strongest objection, why the runner-up loses, confidence and what would change the ranking. Write `<AGENT>.md` with `## Option comparison`, `## Preferred choice`, `## What would change my mind`.
2. **Challenges:** after all proposals exist, everyone reads everyone else's proposal. Write `<AGENT>-CHALLENGE.md` with `## Challenges to peers` (one subsection per other reviewer, addressing their actual arguments and finding IDs), and `## Preferred choice`. Steelman before challenging; test the strongest assumptions and tradeoffs. Explain agreements rather than inventing objections.
3. **Responses:** after all challenges exist, everyone answers every challenge directed at their proposal. Write `<AGENT>-RESPONSE.md` with `## Responses to challenges` (concede, rebut or unresolved, with reasons), `## Preferred choice`, `## What would change my mind`. Explicitly revise or defend the ranking. Do not read peer responses until this pass is complete.
4. **Claude consolidation:** read every proposal, challenge and response; compare the options, trace the material disagreements and concessions, and recommend ONE primary choice with arguments, strongest counterargument, confidence and remaining uncertainty. Judge evidence, not votes. Use `## Option comparison`, `## Debate assessment`, `## Preferred choice`, `## Decision for HUMAN`, `## After HUMAN chooses` in `CONSOLIDATION.md`.
5. **Stop for HUMAN:** Claude sets `**Workflow status:** awaiting_human_choice` in this README, retaining the current round. No automatic next round or full specs. The user may select any option, amend it or request more debate.

## Assessment criteria

Use the same criteria for all options: fit to HUMAN's goals, feasibility, effort, maintenance, local control, dependencies, operational risk and reversibility. Preserve original option identities; do not quietly combine competing paths. Verify decision-critical external claims using primary sources when possible. Distinguish facts, reasoning, assumptions and unknowns; cite URLs and check dates. Do not invent scores, costs or consensus. Missing low-level specs are not defects before a path is chosen unless they prevent a meaningful comparison.

## Ownership and completion

Reviewers write only their own pass file and append their CHANGELOG entry. Claude writes only the consolidation, this README and its CHANGELOG entry. Nobody edits or bumps the proposal during the debate. Do not run git; the orchestrator commits and pushes each pass. Retain earlier work as context.

For concrete defects, use the existing finding format: `### <AGENT>-<n> · title`, `**Severity:** blocking | major | minor`, finding, proposed correction, evidence and confidence. Otherwise write `Findings: none`. End every pass and consolidation with `Result: complete`.

## After HUMAN chooses

Record HUMAN's actual option selection and constraints in `decisions.md`; do not infer approval from an AI recommendation. Set `workflow.json` to `template: spec-review`, `phase: specification`, with `human_choice` recording that decision. Remove the waiting-status line and advance the round only after that choice. Then develop full specs for the selected option: scope, architecture, interfaces/data, behavior, operations, migration, validation and acceptance criteria. Other options remain historical context.
