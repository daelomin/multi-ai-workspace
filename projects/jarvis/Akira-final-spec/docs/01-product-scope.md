# 01 — Product scope, users and workflows

**Status:** Final specification v0.7 · **Normative requirements:** `spec.md` §4, §15 · **Evidence labels:** V/D/M/R/A/U as defined in `spec.md` §0.

This document explains what Akira is for, who uses it, and what a working day looks
like. Requirements live in `spec.md`; this document supplies the product reasoning
another engineer needs to make judgment calls during implementation.

---

## 1. What Akira adds over Akeru, in one page

Akeru is a strong local-first bot workspace. It already has named bots, per-bot memory,
groups, delegation, routines, approvals and a usage page. Akira keeps that and closes the
gaps that make Akeru unsuitable as a *production team platform*:

| Gap in inspected Akeru | Evidence | Akira addition |
|---|---|---|
| Bot identity is name/title/description/tone + avatar. There is no free-text persona, goals or procedures. | `OrchestrationBot` in `packages/contracts/src/orchestration/roster.ts`; instructions are generated in `AkeruAgentInstructions.ts` (V) | Versioned template/persona/instance model, goals, procedures, per-instance overrides |
| No reusable template library; copying a persona is manual | `docs/user/bots.md` (D), no template commands in `rosterCommands.ts` (V) | Agent library of named specialists, instantiation, upgrade diff, clone rules |
| A task is a chat turn; no acceptance criteria, attempts, checkpoint record or review | turn/thread model in `packages/contracts/src/orchestration/events.ts` (V) | First-class Task aggregate with attempts, checkpoints, action ledger, review |
| Routing is a saved per-bot model that fails closed; no per-task adequacy, triage or readiness gate | `docs/user/bots.md` "Akeru never switches it for you"; `docs/operations/provider-model-routing.md` (D) | Good-enough routing, triage, specification readiness, visible route decisions |
| Skills are per-driver: Claude scans files, Grok probes its CLI, Codex lists via app-server, Custom API/Kimi/OpenCode Go declare `skills: []` | `ClaudeSkills.ts`, `GrokSkills.ts`, `CodexCapabilitiesProbe.ts`, `CustomOpenaiDriver.ts:211`, `KimiDriver.ts:89` (V) | Canonical `SKILL.md` package, per-route adapters, support levels, E2E verification |
| Group chat: boss answers every message, last mention wins; no silence outcome | `docs/user/chats.md` §Group chats (D) | Rooms/boards, publish gate, justified silence, anti-ping-pong |
| Delegation delivers a result once, but a restart fails running work; retry is a new card | `docs/internals/delegation.md` (D) | Task handoff with checkpoint and resumable attempts |
| Ratings and effectiveness observer do not exist. Observer/Reflector are memory curation stages | `akeruUsage.ts` categories + `AkeruMemory.ts` callbacks (V) | Task ratings with disputes; observer proposals with evaluation |
| Usage ledger exists per bot/turn/category but has no task, attempt, account, room or parent link | migration 056 `akeru_bot_usage_entries` (V) | Extended dimensions, exclusive/inclusive roll-ups, cost provenance |
| No telephony, no video, WhatsApp direct messages only, images only via subscription | channels/voice/image docs (D) | Specialist capability contracts and adapters |
| Plugin catalog has 54 entries, none installable | `plugins/entries/*/plugin.json` (V) | Honest connector inventory, custom MCP/Composio/first-party paths |
| Archived bots are deleted after 7 days | `roster.ts:358`, `archivedBotRetention.ts` (V) | Retention disabled; archive-first lifecycle |

The full inventory, including what is reused unchanged, is
`docs/02-akeru-baseline.md`.

---

## 2. Users and their jobs

**HUMAN operator (primary).** Declares bots, sets intent, reviews consequential actions,
reads outcomes and costs. Wants: fast declaration, trustworthy autonomy, no surprises on
spend or external effects, and a lean workspace. Does not want to edit YAML, manage
queues or watch dashboards.

**Bot (worker and peer).** Receives tasks, plans, executes with tools, collaborates,
challenges, reports evidence, asks when it should, and stays silent when it should. Wants:
clear goals, stable identity across models, reliable memory and skills, and no duplicate
or conflicting work.

**Bot-admin (secondary human role).** Curates templates, approves observer refinements,
manages connector grants and route policy. May be the same person as the operator in v1;
the role exists so delegation of authority is explicit.

**Observer bot (system role).** Reads outcome evidence and proposes refinements. Never
owns goals or personas, never activates its own proposals.

**Teams of bots in rooms (the unit of collaboration).** Technical Board, Bringing In
Deepseek, GETTING TO PRODUCTION and Administration board map to rooms with different
routing rules and different approval strictness.

### Jobs to be done

1. "Give me a named specialist that already knows our conventions, connect it to the
   tools it needs, and let it start." → declaration flow + library + dependency checks.
2. "Keep working when my Codex credits run out." → same bot, same task, another route,
   without re-explaining anything.
3. "Don't let a cheap model quietly do a job badly." → capability floor, triage,
   readiness, escalation.
4. "Tell me what this cost, per task, including the failed attempts and the review." →
   usage ledger and task cost view.
5. "Don't ping me for routine work, and don't fill the room with noise." → autonomy
   boundaries, silence policy, meaningful notifications.
6. "Challenge each other and show evidence; I want better outcomes, not agreement." →
   challenge protocol, ratings with reasons, dissent records.
7. "Get the old team working again without inventing what I told them." → migration with
   drafts and gaps visible.

---

## 3. Primary workflows

### 3.1 Declare a bot (target: under three minutes to first task)

1. **Choose or describe.** Pick a library specialist, or describe the role in a sentence
   ("review our pricing experiments and challenge the statistics"). Akira proposes a
   template match and a draft persona.
2. **Confirm identity.** Name, avatar, tone/outlook, and the room(s) it joins. Draft
   persona fields are editable and show which are template defaults.
3. **Pick policy.** Route policy (best available / balanced / economical), tool grants,
   connector access, communication policy (when it may speak, quiet hours).
4. **Resolve dependencies.** Missing provider account, connector OAuth, skill bundle or
   workspace path is listed with a fix; nothing is silently skipped.
5. **Start work.** Akira proposes a first task derived from the role and the room's
   current board, with acceptance criteria. The bot starts when the operator accepts.

The instance is isolated from the template and from every other instance from step one.

### 3.2 Run a task

1. Requester (human or bot) states the outcome; Akira proposes acceptance criteria.
2. Triage estimates complexity/cost, flags large/ambiguous/integration-heavy work, and
   checks readiness.
3. Route decision selects an adequate route, with reason and cost band.
4. Execution produces attempts; each attempt has a checkpoint before and after and an
   action ledger for external effects.
5. Review: requester or peer reviews against acceptance criteria, rates, and either
   accepts, requests rework (a new attempt with a reason), or disputes.
6. Done: artifacts, decisions, attempts, ratings and usage are linked to the task.

### 3.3 Switch route

- **User-initiated:** per bot (future tasks), per task (next attempt), or per attempt
  (this turn). Consequence preview shows what changes (skills support, quota, cost).
- **Policy-initiated:** infrastructure failures by default; quota only under an explicit
  `always-adequate` policy (docs/04 §4.2). All eligibility and unresolved-action guards
  apply. Visible, logged, reversible.
- **Credit exhaustion:** task pauses with a quota reason and options. Resume on another
  adequate route uses the checkpoint; no re-explanation, no identity change.

### 3.4 Collaborate in a room

- The room has a topic, members/roles, a board and a decision log.
- Messages route by mention or room rule; the boss default is configurable.
- A bot may act quietly (board update) or end silently with a reason.
- Cross-bot work is a handoff task with acceptance criteria, not a chat message.
- Challenges carry claim/evidence/objection/test; dissent is recorded.

### 3.5 Review and observe

- Consumers rate the task outcome with evidence; ratings are disputable.
- The observer reads outcomes, proposes a refinement, evaluates it on held-out tasks,
  and waits for HUMAN/bot-admin approval. Overhead is visible.
- Accepted refinements create a new version and can be rolled back.

### 3.6 Operate

- Operators see health, blockers, quota staleness, unresolved external effects,
  proposals, backup age and last restore verification.
- Destructive operations are explicit, named and audited; nothing is auto-pruned.

---

## 4. What "production-grade" means here

Production-grade is not "more features". It means these properties are designed,
tested and operable:

1. **Durability.** No silent loss of tasks, memory, decisions or money records across
   restarts, crashes, provider changes or upgrades.
2. **Honesty.** Unknown is displayed as unknown; estimates are labelled; failures are
   classified; no fabricated token counts or parity claims.
3. **Recoverability.** Every failure has a documented path back: resume, retry,
   reassign, restore from backup, roll back a release.
4. **Accountability.** Every consequential action is attributable to a bot, task, route,
   approval and HUMAN intent, with evidence retained.
5. **Reversibility.** Templates, personas, procedures and refinements are versioned;
   releases and migrations can be rolled back.
6. **Bounded autonomy.** Clear permission boundaries, spend and blast-radius guards, and
   a kill switch that preserves state.
7. **Maintainability.** A pinned upstream, a reviewed patch series and a documented
   rebase process, so Akira does not become an unmaintainable fork.

The acceptance suite (`docs/10-tests-and-acceptance.md`) is the definition of done.

---

## 5. Success measures

Measured from the ledger and task records, not from sentiment:

| Measure | Definition | Why it matters |
|---|---|---|
| Declaration time | Median time from "create bot" to first accepted task | HUMAN priority: easy declaration |
| Task acceptance rate | Accepted tasks / completed tasks, per task class and route | Quality, not fluency |
| Rework ratio | Rejected-and-redone attempts / accepted tasks | Hidden cost of bad routing |
| Cost per accepted task | Total delivery cost (incl. retries, review, observer) / accepted tasks | The real cost metric |
| Route switch success | Switches that resume without losing identity/task state / all switches | Primary goal |
| Unresolved external effects | Count and age of `unknown` actions | Safety |
| Silence quality | Silent turns with a recorded valid reason / silent turns; operator complaints per 100 turns | Deliberate communication |
| Rating coverage | Accepted tasks with at least one evidenced consumer rating | Accountability |
| Restore success | Verified full restores / attempted | Operability |
| Observer hit rate | Accepted refinements that improve held-out outcomes / evaluated proposals | Observer value, not activity |

Initial targets are deliberately omitted: HUMAN has supplied no budgets or thresholds
(`docs/13-open-decisions.md` U4). The measures and their data sources are fixed now so
baselines can be established during the vertical slice.

---

## 6. Migration baseline (what exists today)

From the supplied Grokbot screenshot and the assessment context, treated as observed UI
state, not verified data:

- **Bots:** Natalia; CodeBot Rajiv; Stefano The QA; DeepSeek Batch'it crazee; Sarah The
  Critic; Godzilla the Dataminer; MarketingBot Kristin; SeniorEngineer Arns; Counsel
  Helmut; Grok Bot Optimus.
- **Rooms:** Technical Board; Bringing In Deepseek; GETTING TO PRODUCTION; Administration
  board.
- **Shared results:** a page titled "Fuel Atlas + FuelBuddy: Road to Play" in the Natalia
  conversation; task/result cards in conversation.
- **Routines:** "Weekly bot scorecard".
- **Unknown:** the actual instructions, memory exports, backend assignments and connector
  set. A bot named DeepSeek is not proof of its provider.

Migration therefore has two lanes: *mechanical* (names, roles, room membership, routine
schedule, artifact import where an export exists) and *human-supplied* (persona text,
memory, provider policy). Akira drafts the second lane and marks it for review; it never
invents it. Detail: `docs/12-operations.md` §8 and `docs/06-ux.md` §11.
