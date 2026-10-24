# JarvisBot — option assessment and debate

The deliverable is an argued recommendation for HUMAN's choice. `spec.md` is the input proposal, not an approved implementation specification.

## Current round

**Round 2** — option assessment and debate on proposal v0.1. Files go in `reviews/round-2/`.

Round 1 used the former specification-review rubric. Its reviews and logs are preserved as context; they do not count as debate passes.

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

## HUMAN priorities for JarvisBot

- Maximise user friendliness for declaring bots: assess the steps from choosing a template to a usable bot, including naming and customisation.
- Minimise total costs: distinguish setup, hosting, inference/subscriptions, ongoing operations and maintenance; state assumptions and unknowns.
- Maximise useful functionality and SKILLS.md support; verify actual skill-file formats and how skills are discovered, reused, configured and extended.
- Provide an agent library of pre-declared agents with specific names, reusable as templates for named instances with custom outlook/appearance, procedures, goals, attitude and skills; distinguish template defaults from per-instance identity and memory.

These priorities were supplied by HUMAN on 2026-10-24. Do not invent numeric weights; explain tradeoffs and identify which unknowns could change the preferred option. No implementation path has been selected by HUMAN.

## Additional HUMAN priorities

- Maximise bot autonomy within the user's intent: bots should plan, act, coordinate and resolve routine issues independently, and escalate only meaningful decisions or blockers.
- Bots must deliberate before communicating and sometimes choose silence: assess when to respond, ask, act quietly or remain silent; avoid chatter, premature claims and repetitive updates. Report useful conclusions and evidence rather than private reasoning traces.
- Bot dynamics should be collaborative and driven by excellence: challenge each other's assumptions constructively, defend claims with evidence, accept corrections and improve outcomes rather than manufacture consensus or conversation.
- Include a smart observer bot that evaluates each bot's effectiveness and proposes refinements to its strategy, procedures, goals, skills and communication. Compare observer overhead and cost, feedback usefulness and how proposed strategy changes are evaluated; do not silently rewrite user-defined goals or personas.

## Primary goal and specialist capabilities (HUMAN)

PRIMARY GOAL: operate the same persistent bots across Codex, Claude, DeepSeek, Grok and other AI backends, switching when credits or quotas run out. Bot identity/persona, memory, skills, procedures, goals and task progress must not be tied to a single provider or discarded on switch. Distinguish model APIs, CLI/agent harnesses and subscription authentication; verify supported routes rather than assuming they are interchangeable.

- Critical feature: assess whether a model is good enough for each task and route accordingly. Compare task-specific acceptance criteria, representative evals/tool-use reliability, quality versus cost/latency, calibrated uncertainty and escalation to a stronger model; cheaper model preference must not silently lower required quality. Credit exhaustion, rate limits, authentication failures and poor capability are distinct failure modes.
- Switching must preserve task state and safely resume: assess checkpoints, tool/schema/context compatibility, in-flight work and preventing duplicate side effects when retrying on another backend. Compare user-initiated switching with automatic fallback and explain account/credit visibility limitations.
- Required specialist capabilities: agents that make phone calls, manage a WhatsApp Business account, generate images and create short movies. Compare native coverage, existing MCP/API integrations, custom adapter work, usability, credentials, operational requirements and ongoing costs; do not equate WhatsApp messaging support with complete Business account administration.
- Double-check Grokbot tool/connector replication using primary sources. For EVERY implementation option produce a service-by-service capability matrix identifying original Grokbot capability, concrete candidate connector/API, tools or actions covered, authentication and hosting dependency, native/reuse/custom/not supported/unverified status, setup/ongoing costs, and evidence/date. Distinguish preserving the UI or MCP tool bridge from possessing hosted connectors, OAuth registrations and tokens. Prioritise phone, WhatsApp Business, image/video generation and existing productivity integrations. Do not claim a parity percentage without a defined inventory and evidence.

Read `assessment-context.md` for dated primary-source findings to verify and challenge. Compare original paths against these HUMAN requirements even where the input proposal is incomplete. No path is chosen.

## Existing team baseline

HUMAN supplied a screenshot of the current named bots, board rooms, shared pages and routines. See `assessment-context.md`; use these as migration/continuity examples, and revisit the newly added evidence during challenges and responses. Do not infer unseen personas or provider assignments.

## UI, accountability and usage priorities

- UI direction: use HUMAN's Grokbot screenshot as the visual reference: lean, efficient, familiar bot/room navigation, conversation and shared results. Add accountability and usage visibility through compact summaries with drill-down, without turning the primary workspace into a dense dashboard.
- Task accountability: bots receiving or consuming another bot's work should rate the TASK outcome using evidence of how fully it resolved their issue, rework required, output quality and efficiency. Distinguish task ratings from bot reputation; show reviewer identity, criteria, reasons and linked deliverables/revisions. Compare mechanisms for disagreements, task difficulty/context, insufficient evidence and correction over time. Avoid rewarding chatter, self-ratings, mutual praise or cheap but unusable output.
- Usage transparency: make token usage and cost attributable across discussions, tasks, spawned cloud agents, observer/peer review work, retries and provider switches. Compare per-bot/model/provider, per-room/discussion, per-task and parent/child totals with drill-down. Distinguish input/cached/output/reasoning tokens where actually reported; distinguish measured usage, estimates, subscription/credit usage and unavailable telemetry. Show child cloud-agent usage without double counting it in rolled-up parent totals. Make review/coordination overhead visible alongside delivery cost; never invent exact token counts or equate estimated dollar values with actual subscription billing.

See assessment-context.md for peer-rating evidence and usage-accounting distinctions. Revisit this addition in the challenge and response passes.

## Early complexity and cost assessment

Early complexity/cost triage is critical: identify very large, ambiguous, integration-heavy or otherwise costly tasks before substantial execution or cloud-agent spawning. Compare estimated total cost/effort and uncertainty, including planning, implementation, tools, validation and likely rework. Route to an advanced model when judgment or complexity warrants it, OR first produce a sufficiently precise specification and decomposition that a simpler model can reliably implement the intended vision. Assess a hybrid where an advanced model specifies/reviews and simpler models implement. Require a specification-readiness check with clear scope, interfaces/dependencies, constraints, bounded subtasks and verifiable acceptance criteria; do not downgrade simply because the first model ran out of credits. Make the route and rationale visible, and re-triage when scope, evidence or expected spend changes materially. Do not invent numeric thresholds or budgets HUMAN has not supplied.

See assessment-context.md for routing and specification-readiness considerations.
