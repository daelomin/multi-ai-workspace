# Akira — production specification

**Document ID:** AKIRA-SPEC-001
**Version:** 0.4 (v0.2 recorded HUMAN decisions AKIRA-D4–D6; v0.3 added the v1 skill catalogue; v0.4 consolidates review round 1: append-only backup, guarded hard delete, recovery quarantine, availability vs capability, unit-separated accounting, task recovery transitions)
**Date:** 2026-10-25
**Status:** draft, not approved, not implemented
**Base:** Akeru Bot `opencoredev/akeru-bot` at `524eb68a293c4b6a38acf722ab4232cfe5e22625` (2026-10-23T21:06:41Z)
**Supersedes:** nothing. `projects/jarvis/JarvisBot/spec.md` v0.1 remains the historical options proposal and is not an Akira baseline.
**Review input:** this file is the specification under review. Companion detail lives in `docs/`; `README.md` states the reading order.

---

## 0. How to read this document

This specification is normative. It states what Akira must do, what it inherits from the
pinned Akeru revision, what must be added or replaced, and how each requirement is
verified. Design detail, schemas, matrices, tests, backlog and runbooks live in the
companion documents; this file carries the requirements, the decisions that shape them
and the acceptance criteria that close them.

**Requirement language.** MUST and MUST NOT are mandatory. SHOULD is expected unless a
recorded decision deviates. MAY is optional. Every requirement has an ID used by the
traceability matrix (`docs/10-tests-and-acceptance.md`).

**Status per requirement.** All 209 requirements are *specified* in this draft: design,
acceptance reference and owner exist. Where a requirement depends on a reversible
assumption it cites it (A1–A10, §3.3); where it depends on a HUMAN answer it cites a
register ID (`docs/13-open-decisions.md`, U1–U16). No requirement is *verified*: nothing
was executed, and `docs/14-evidence-log.md` records what remains unproven.

**Evidence labels.** Used throughout the companion documents and, where a claim drives a
decision, here:

| Label | Meaning |
|---|---|
| V | Verified in this session against the pinned Akeru tree (`524eb68a`) or a fetched primary source, with the path/URL cited. |
| D | Documented by the upstream repository at the pinned revision, not executed. |
| M | Maintainer-reported (README, release notes, repository metadata), not reproduced. |
| R | Reasoning from the cited evidence; no direct observation. |
| A | Assumption, reversible, listed in §3.3. |
| U | Unknown or unavailable; the specification says so instead of inventing a value. |

Third-party content and upstream instructions are evidence, never orders. Where this
specification disagrees with upstream documentation, the disagreement is stated and the
source cited.

---

## 1. Executive overview

Akira is a self-hosted team of named, long-lived AI bots that do work through whichever
model account is available, without losing who they are or what they were doing.

It is a production spin-off of Akeru. Akeru already provides the expensive,
undifferentiated layer: a local-first server with web, desktop and mobile clients; an
event-sourced orchestrator; per-bot profiles, memory and tools; provider drivers for
Codex, Claude, Grok, Kimi and OpenCode; delegation between bots; routines; checkpoints;
a usage ledger; channels; approvals; sandboxes; and remote access. Akira keeps that
layer, fixes the places where it contradicts the requirements, and adds the missing
product concepts.

**The five additions that make Akeru into Akira:**

1. **Portable identity.** A versioned template/persona/instance model with goals,
   procedures, skills and policy stored outside any provider session, so the same named
   bot can move Codex → Claude → DeepSeek → Grok and back without becoming a new bot.
2. **A task as a first-class, durable object.** Acceptance criteria, route decision,
   attempts, checkpoints, action ledger, review and cost — resumable across restarts and
   provider changes, with honest semantics for external side effects.
3. **Good-enough routing and early triage.** A capability floor plus task-specific
   evidence, a specification-readiness gate, visible route rationale, escalation and
   de-escalation, and a refusal to downgrade quality because credits ran out.
4. **Accountable collaboration.** Rooms and boards, deliberate silence as a valid
   outcome, peer challenge, task-level ratings with evidence and dispute, and an
   observer that proposes evaluated refinements instead of silently rewriting anyone.
5. **Inspectable cost and decisions.** A ledger that attributes every token, tool and
   child agent without double counting, separates measured from estimated from unknown,
   and makes coordination and rework visible.

**What Akira explicitly is not:** a hosted multi-tenant SaaS, a marketplace, a
replacement for the provider vendors, a guarantee of Grokbot connector parity, or a
claim that every model is interchangeable. It is an owned, auditable system for a small
professional team of bots and humans, designed to grow.

**Delivery shape.** One server process owns dispatch, retries, durable state and usage
attribution. Provider CLIs and APIs are adapters behind it. The web client is the primary
surface; desktop and mobile reuse the same server contract. Akeru's upstream remains the
base, maintained as a pinned revision plus a reviewed patch series.

---

## 2. Authority, settled decisions and scope

### 2.1 Settled (do not reopen)

| ID | Decision |
|---|---|
| AKIRA-D1 | Akeru is the base; the product is Akira; this deliverable is a production specification and plan. |
| AKIRA-D2 | Nothing is deleted, trashed or pruned without an explicit HUMAN message naming the items; Docker images always need specific approval. Akeru's seven-day archived-bot deletion is neutralized before real data. |
| AKIRA-D3 | No deployment, paid service, real customer contact or paid media job is authorized by this specification. Integrations are verified with stubs, synthetic fixtures or separately authorized test accounts. |
| AKIRA-D4 | Target host: Linux x86_64, single node, systemd service, always available enough for routines and WhatsApp webhooks. |
| AKIRA-D5 | The operator's own subscription logins may be used through Akira for personal work; API keys remain supported. |
| AKIRA-D6 | Private, internal deployment; no publication or redistribution of builds or the specification. |

Full text and consequences: `decisions.md`.

### 2.2 Requirements inherited from HUMAN

The HUMAN priorities in `projects/jarvis/JarvisBot/workflow.json` remain in force. In
Akira's terms:

- the same persistent bots across Codex, Claude, DeepSeek, Grok and later backends,
  switching when credits or quotas run out;
- identity, persona, memory, skills, goals, procedures and task progress independent of
  a provider session;
- a good-enough decision per task, not a permanent model label;
- easy bot declaration and a reusable agent library of named specialists;
- low total delivery cost, with setup, hosting, inference, operations and maintenance
  distinguished;
- maximum useful capability, including a real skill format (`SKILL.md` versus the
  broader "SKILLS.md" request);
- autonomy inside the user's intent, deliberate communication and legitimate silence;
- constructive peer challenge, evidence over consensus;
- task accountability with ratings that separate task evidence from bot reputation;
- an observer that proposes refinements with visible overhead and evaluated benefit;
- phone calls, WhatsApp Business management, images and short movies as real
  integrations, not marketing;
- a lean workspace modelled on the supplied team screenshot, with compact indicators
  and drill-down rather than a dense dashboard;
- early detection of large, ambiguous, integration-heavy or expensive tasks;
- migration of the named team, rooms, shared results and routines without inventing
  missing content.

### 2.3 Scope of this release

**In scope:** the Akeru-derived server and web client; identity/template library; goal,
procedure and skill model; durable tasks and checkpoints; routing and triage; usage
accounting; rooms, silence, ratings and observer; PSTN and WhatsApp specialist adapters
with stub-first verification; connector framework and the first required integrations;
migration of the named team; security and operations.

**Out of scope for the first production release (deliberately deferred, not dropped):**
native mobile feature parity (mobile may be read/reply only initially), desktop
packaging beyond the upstream Electron shell, hosted multi-tenant deployment, a public
plugin marketplace, real-time voice-to-voice PSTN streaming at scale, automated video
editing/assembly quality beyond scripted renders, and cross-organization federation.

### 2.4 What Akira keeps from Akeru, in one paragraph

The event-sourced orchestration engine and its decider/projector/reactor split; the
provider driver/registry architecture and Mastra-based controller; bot profiles with
per-bot memory files and observational memory; groups, delegation child threads,
routines, checkpoints (git refs), channels, approvals, sandboxes, remote access, the
usage ledger and the multi-client contract. Reuse, extension and replacement per
component are itemised in `docs/02-akeru-baseline.md`.

---

## 3. System model

### 3.1 One authority

**AK-GOV-01.** Exactly one component decides to start, retry, or abandon model work:
the orchestration engine's command path, with provider dispatch performed by the
existing `ProviderCommandReactor`. No adapter, connector, observer, UI or scheduler may
start or retry a provider turn directly. All such actions are commands (MUST).

**AK-GOV-02.** Akeru's `AgentController` remains the only place provider runtimes are
driven, and the `ProviderRuntimeIngestion` path remains the only place provider events
are normalized. Adapters translate protocols; they do not own retry policy, task state
or accounting (MUST).

**AK-GOV-03.** Durable state has one owner per fact. Chat and task history: the event
store. Working files and artifacts: the artifact store and project workspaces. Secrets:
the environment secret store. Provider sessions: the provider session directory, treated
as disposable. External systems: their own API, with Akira's action ledger recording what
Akira believes happened (MUST, §3.2).

**AK-GOV-04.** Cross-cutting features (routing, accounting, ratings, observer) attach to
the same command/event path and read the same projections. They may not maintain a
parallel task database or a parallel retry loop (MUST). If a feature can only be built by
adding a second authority, it is deferred until the authority problem is solved
(`docs/03-architecture.md`, ADR-01 and rejected alternatives).

**AK-GOV-05.** Every consequential autonomous action is attributable to a bot, a task,
a route, a policy version and a HUMAN intent. Akira must be able to answer "why did this
bot do this, under which instructions, with whose credentials, and what did it cost"
from durable records, without storing private chain-of-thought (MUST).

**AK-GOV-06.** The system remains usable with no provider available: history, memory,
tasks, ratings, usage and exports are readable and exportable offline (MUST). Akira must
not make bot identity or history depend on a provider account remaining valid.

### 3.2 Durable state ownership

| State | Owner | Storage | Survives provider switch | Survives host restart | Exported |
|---|---|---|---|---|---|
| Bot template, persona revision, instance record | Akira orchestrator | SQLite events + projections | yes (provider-neutral) | yes | yes |
| Goal, procedure, skill registry entry | Akira orchestrator | SQLite events + content-addressed files | yes | yes | yes |
| Task, attempt, route decision, checkpoint record | Akira orchestrator | SQLite events + projections | yes | yes | yes |
| Chat transcript, messages, activities | Akira orchestrator | SQLite events + projections | yes | yes | yes |
| Bot memory (`USER.md`, `MEMORY.md`, `GROUP.md`, task memory) | `BotMemoryStore` | files under the state dir, 0600 | yes | yes | yes, separate bundle |
| Observational memory (per-thread summaries) | Provider-neutral store (Mastra) | SQLite | yes | yes | yes, with memory bundle |
| Artifacts and attachments | Artifact store | files + hashes + metadata | yes | yes | yes |
| Workspace file checkpoints | Checkpoint store | hidden git refs per turn | partial (same workspace) | yes | refs + bundle |
| Action ledger | Akira orchestrator | SQLite append-only table | yes | yes | yes |
| Usage ledger | Akira orchestrator | SQLite append-only table | yes | yes | yes |
| Provider session / resume cursor | Provider session directory | SQLite metadata + provider-side state | **no** (disposable) | partial | no |
| Provider credentials | Secret store | `secrets/subscription-auth.json` 0600 | not applicable | yes | never |
| Provider-reported quota/credit meters | Provider status cache | cache + last-good values | not applicable | stale after restart until refreshed | snapshot only |

**AK-GOV-07.** Provider-private state (native session ids, resume cursors, cached
reasoning, tool-call replay buffers) MUST be treated as disposable. No requirement may
depend on it transferring between providers or surviving a restart (MUST). Its loss may
cost money and time, but must not lose task identity, decisions, artifacts or memory.

**AK-GOV-08.** The checkpoint record is the portable unit of continuation. It MUST be
sufficient for a different route to continue the task without the previous provider's
session (MUST; schema in `docs/04-data-model.md`, semantics in §8).

### 3.3 Reversible assumptions

Each assumption is labelled, has a reversible default, and states what would change it.
They exist so the specification can be implemented without waiting for answers that are
not genuinely blocking. Rows marked **settled** are retained for traceability; the
HUMAN decision now governs and the default is no longer provisional.

| ID | Assumption | Default taken | Resolved by / changes if |
|---|---|---|---|
| A1 | **Settled by AKIRA-D4.** Target host is Linux with systemd, always available enough to receive WhatsApp webhooks | Single-node Linux, systemd user service, SQLite | A later host change is a deployment decision; WhatsApp without a public origin becomes outbound-only |
| A2 | **Settled by AKIRA-D5.** Bots run with the operator's own accounts; subscriptions may be used for personal work | Per-account credentials in the environment secret store; subscription routes as `subscription-equivalent` | A vendor whose terms forbid the use disables that route (recorded), not the class; API keys remain |
| A3 | Team size is 10–30 bots, 2–10 humans, 4–20 rooms; one environment per team | Single environment, single writer | Growth beyond this → Postgres and multi-process triggers (ADR-10) |
| A4 | Chat, not email, is the primary collaboration surface | Web client first; channels are adapters | HUMAN wants email-first → notification and artifact model change |
| A5 | "Phone calls" means PSTN calls to real numbers, with recording/consent constraints | PSTN adapter contract, stub-tested | HUMAN means in-app voice only → upstream voice is sufficient |
| A6 | "Short movies" means scripted, render-based video with human review before paid renders | Async job workflow, approval gate before paid render | HUMAN wants live/animated avatar video → provider and effort change |
| A7 | Existing team migration can be done from names/roles plus HUMAN-supplied instruction text; unseen personas are drafted and reviewed, never invented silently | Draft personas from role, marked `needs-human-review` | Exports exist → import replaces drafts |
| A8 | **Settled by AKIRA-D6.** Akira is a private, internal deployment | Private fork, no redistribution, upstream notices preserved | Publishing later is a new HUMAN decision with a licensing/trademark/distribution review |
| A9 | A single task is executed by one bot at a time; concurrency is across tasks, not within one task | One active attempt per task | Parallel sub-execution needed → attempt fan-out with a join node |
| A10 | The team can accept a small amount of duplicated provider spend during route changes and retries, recorded honestly | Attempt ledger includes failed/duplicate turns | Cost pressure → stricter routing and cache policy |

**AK-GOV-09.** An implementation MUST make each assumption's state visible in the
configuration and in exported state, so a later HUMAN answer can be applied without a
schema migration (MUST).

---

## 4. Product scope and workflows

Detailed flows and wireframes: `docs/06-ux.md`. This section is normative for behaviour
a user sees.

### 4.1 Declaring a bot

**AK-UX-01.** Declaring a bot MUST be a short, resumable flow: choose a template or
describe the role in a sentence; confirm the proposed name, role, persona and working
style; choose the route policy (best available / balanced / economical) and the rooms it
joins; connect required dependencies; start with a first useful task. No YAML editing is
required for the default path (MUST).

**AK-UX-02.** The flow MUST show what the bot will be allowed to do, what it will cost
to run (range with uncertainty, not a false precision), and which dependencies are
missing (MUST). Missing credentials pause the declaration; they never silently disable a
capability the user selected.

**AK-UX-03.** Template instantiation MUST create a fully isolated instance: distinct bot
id, memory, task list, usage attribution and credential references. Two instances of the
same template share nothing mutable (MUST). Cloning MUST NOT copy another instance's
memory, chats, tasks or credentials (MUST NOT).

**AK-UX-04.** The workspace MUST remain lean: bot roster, rooms/boards, the selected
conversation or board, and a contextual inspector. Task status, route, quality and usage
appear as compact indicators with drill-down, not as a permanent dashboard (MUST).

**AK-UX-05.** Silence and progress are legible: a bot that is working shows meaningful
progress; a bot that chose not to speak shows no message but leaves an inspectable record
(§9). "Nothing to say" is never a chat message (MUST).

### 4.2 Doing work

**AK-UX-06.** A request becomes a task when it is non-trivial or long-running, with
acceptance criteria visible to the requester; trivial chat stays a chat turn (MUST).
"The task" is the unit rated, routed, costed and resumable.

**AK-UX-07.** Before a costly or ambiguous task is dispatched, the requester sees the
triage result: complexity drivers, estimated cost band and uncertainty, specification
readiness, proposed route and reason, and a one-click "discovery first" or "escalate"
choice (MUST).

**AK-UX-08.** Route changes and fallbacks are visible as task events with the reason and
the failure class, never silent (MUST). A reroute reported by a provider is surfaced as
`model.rerouted` with requested and effective model (Akeru behaviour, retained).

**AK-UX-09.** Every completed task exposes: outcome against acceptance criteria, artifacts
and revisions, review/ratings, attempts (including failed ones), and exclusive plus
rolled-up usage (MUST).

### 4.3 Switching and fault handling

**AK-UX-10.** Switching a bot's route can be user-initiated (per bot or per task) or
policy-initiated (fallback). Both MUST preserve the bot, the task, the memory, the
skills and the checkpoint, and MUST state what could not be preserved (for example a
provider-native cache) (MUST).

**AK-UX-11.** Failure presentation MUST distinguish: credit/quota exhausted, rate limit,
authentication or entitlement problem, network/transport failure, capability gap (model
or tool contract), context overflow, safety/approval block, and unknown. Each offers the
action that can actually fix it (MUST). A capability gap MUST NOT be presented as a
credit problem.

**AK-UX-12.** Recovery MUST be possible from the UI without editing files: resume from
the last checkpoint, retry as a new attempt, reassign to another bot, cancel with a
reason, or request help. An unresolved external effect is shown as unknown with its
reconciliation state (MUST).

### 4.4 Rooms, boards and review

**AK-UX-13.** Rooms MUST support: a topic, members and roles, addressed messages and
mentions, shared task and result items (board), decision records, and a room-level usage
summary. A room is not a chat log with a title (MUST).

**AK-UX-14.** The board is the durable artifact surface: tasks, results, decisions,
proposals, ratings and alerts are items with stable links; conversation refers to them
instead of duplicating them (MUST).

### 4.5 Operating the team

**AK-UX-15.** An operator view MUST show: bot roster with current route/health, active
tasks and blockers, unresolved external effects, quota/credit status per account,
observer proposals awaiting review, backups and last restore verification (MUST).

**AK-UX-16.** All destructive or irreversible operations are explicit, named, confirmed
and audited. No bulk "clean up", automatic prune or retention timer may remove HUMAN
data (MUST; AKIRA-D2).

---

## 5. Bot identity and the agent library

Design detail: `docs/04-data-model.md` §2–§4; flow: `docs/06-ux.md` §2.

### 5.1 The canonical model

**AK-IDE-01.** Akira MUST define three separate records: **BotTemplate** (reusable
defaults), **PersonaRevision** (immutable, versioned identity content) and
**BotInstance** (named bot with overrides and working state) (MUST). Template defaults,
instance identity and working state MUST NOT be conflated in one mutable record.

**AK-IDE-02.** A bot instance MUST carry: stable id, display name, role/title,
description, avatar/appearance, persona revision reference, goals, procedure references,
skill enablement, tool grant, route policy, memory policy, communication policy, room
memberships, credential references, lifecycle state and timestamps (MUST). Akeru's
`OrchestrationBot` supplies name/title/label/description/avatar/engine/tools/runtime
mode; the remaining fields are additions (`docs/02-akeru-baseline.md` B-03).

**AK-IDE-03.** Persona content MUST be an explicit document (structured fields plus
Markdown body) covering outlook, attitude/tone, working style, boundaries and escalation
rules. It MUST be addressable by content hash and revision number, and MUST be injected
into every provider route identically (MUST). A numeric tone slider may remain as a
convenience, but it MUST NOT be the only way to define a persona (MUST NOT).

**AK-IDE-04.** Instance overrides MUST be recorded as a diff against the template
revision, with field-level provenance (template, instance, HUMAN). Effective persona is
computed and the computation MUST be reproducible from exported state (MUST).

**AK-IDE-05.** Goals MUST be durable records with statement, success criteria, owner,
parent goal, horizon, status and evidence (MUST). HUMAN-defined goals are immutable to
bots: a bot may propose a change, never apply it (MUST NOT). A goal's status changes are
audited.

**AK-IDE-06.** Procedures MUST be versioned, reusable work definitions: steps,
preconditions, required skills/tools/connectors, validation steps, owner and provenance
(MUST). A routine is a schedule bound to a procedure and a bot, not a free-text prompt
(MUST). A procedure change invalidates prior approval and requires re-approval (Akeru
already requires approval for routine procedures; retained and generalised).

### 5.2 The library

**AK-IDE-07.** Akira MUST ship a library of named specialist templates (minimum: software
engineer, code reviewer, QA/test engineer, data miner, research analyst, marketing
operator, counsel/compliance reviewer, operations/coordinator, observer, and a general
assistant), each with default persona, procedures, skill set, tool grants and route
policy (MUST). The library is data, not code: adding a template requires no server
change.

**AK-IDE-08.** Template publication MUST be versioned and immutable once instantiated
(MUST). Editing a published template creates a new version; existing instances keep
their pinned version until an explicit upgrade.

**AK-IDE-09.** Upgrading an instance MUST be a reviewed diff: changed persona fields,
procedures, skills, tool grants and route policy are shown; overrides and working state
are preserved; the operation records old and new revisions (MUST). There is no silent
upgrade on restart.

**AK-IDE-10.** Cloning MUST support two modes: *clone as new instance* (fresh working
state, same identity input) and *derive template from instance* (extract reusable
defaults without private memory or task history) (MUST). Neither mode may copy secrets.

**AK-IDE-11.** Credentials MUST be referenced by id and resolved at execution time from
the environment secret store. A bot record, template, export or log MUST NOT contain a
secret value (MUST NOT).

**AK-IDE-12.** The same bot changing model/provider MUST remain the same instance id,
memory scope, task list and reputation history (MUST). Creating a stronger duplicate bot
is not an acceptable implementation of "switch model".

### 5.3 Migration of the existing team

**AK-IDE-13.** Akira MUST provide an import path for the ten named bots (A7, U8) (Natalia, CodeBot
Rajiv, Stefano The QA, DeepSeek Batch'it crazee, Sarah The Critic, Godzilla the Dataminer,
MarketingBot Kristin, SeniorEngineer Arns, Counsel Helmut, Grok Bot Optimus), the four
rooms (Technical Board, Bringing In Deepseek, GETTING TO PRODUCTION, Administration
board), the shared result pages and the Weekly bot scorecard routine (MUST). The import
creates templates and instances; it does not invent persona text, memory or provider
assignments.

**AK-IDE-14.** Imported-but-unfilled fields MUST be marked `needs-human-review` and
surfaced as a checklist. A draft persona is visibly a draft; it MUST NOT be presented as
the original bot's instructions (MUST NOT). Names alone never establish a backend or a
memory export (assessment-context evidence).

---

## 6. Models, providers, harnesses and accounts

Design detail and evidence: `docs/07-integrations.md` §1–§3.

### 6.1 Vocabulary and separation

**AK-RTE-01.** Akira MUST treat these as separate, composable dimensions: **model**
(weights/version), **API provider** (who serves it), **agent harness/runtime** (who runs
the tool loop: Akeru's Mastra controller, a subscription runtime, a CLI), and **account
entitlement** (subscription plan, API key, credit balance, seat) (MUST). UI and records
must name the dimension, not collapse them into "provider".

**AK-RTE-02.** A route MUST be recorded as `{harness, driver, provider, model,
account/instance, auth_class, options}` with provenance (verified/assumed) and the
Akeru driver it maps to (MUST). A route is only usable when every component is available
and the capability profile says it satisfies the task's floor (§7).

**AK-RTE-03.** Akira MUST NOT assume an OpenAI-compatible endpoint reproduces every API
feature. Tool-call shape, parallel calls, streaming, structured output, image input,
caching and usage reporting are probed or declared per route and per model; unsupported
features are explicit (MUST). Akeru's Custom API driver is the pattern: one endpoint,
its own key, optional model discovery, empty skill catalog (`CustomOpenaiDriver.ts`
line 211) — Akira extends it with declared capabilities and honest gaps.

**AK-RTE-04.** A subscription login is not, by itself, proof that a third-party runtime
may use it. HUMAN has accepted personal-use responsibility for the operator's own
subscription routes (AKIRA-D5), so those routes MAY be used and MUST record a
`transportPermission` of `verified` or `assumed-for-personal-use` (default;
`forbidden`/`unknown` disable the route). Each route's permission status is visible; a
vendor whose terms prohibit the use disables that route with the reason recorded, and
the cost case falls back to API keys for it (MUST). This is an honesty and
traceability requirement, not a legal opinion.

**AK-RTE-05.** Credential handling MUST follow the secret boundary: credentials live in
the environment secret store with 0600/0700 permissions; OAuth refresh tokens never enter
sandboxes, checkpoints, events, projections, logs or client state; only short-lived
access tokens may be passed to a runtime for a run; API keys are passed only to the
provider runtime that needs them (MUST; Akeru's documented boundary, retained).

### 6.2 Discovery, capabilities and settings

**AK-RTE-06.** Model discovery MUST be automatic where the provider supports it, with
last-good catalogs on failure, clear staleness, and manual additions where discovery is
absent (MUST). Provider model lists change; a saved bot must never silently acquire a
different model.

**AK-RTE-07.** Capability profiles MUST record at minimum: tool calling and dialect,
parallel tool calls, maximum context, max output, reasoning controls (levels/switch),
image input, structured output, native skills, streaming, usage reporting granularity,
and known limitations (MUST). Profiles are versioned and carry their evidence source.

**AK-RTE-08.** Reasoning effort/speed settings MUST be expressed as route options with
provider-specific mapping and a "provider default" choice, preserved per bot and per
task where the route supports it (MUST). Unsupported options are disabled with a reason,
never silently dropped.

**AK-RTE-09.** Account selection MUST be visible and ordered: main account, backups, and
separate accounts with independent credentials (Akeru's model). Backup takeover on a
usage limit serves the *next* request; the request that hit the limit fails and is
recorded as a failed attempt (MUST). Akira must not present a fallback as if the same
account served the turn.

**AK-RTE-10.** Quota/credit meters MUST show only provider-reported values, with a
timestamp and staleness; when a provider exposes nothing, the value is `unknown` (MUST).
Akira MUST NOT infer a credit balance from token counts or pricing assumptions.

### 6.3 Switching and fallback

**AK-RTE-11.** User-controlled switching MUST be available at three scopes: bot default,
room/task override, and single-attempt override, with the most specific scope winning
and the effective route visible (MUST).

**AK-RTE-12.** Policy fallback MUST be configurable and default to conservative:
automatic fallback only for classified infrastructure failures (rate limit, transient
transport) when the alternate route meets the capability floor; **no** automatic
fallback for capability gaps, safety blocks, unknown failures or exhausted credits unless
the policy explicitly says so (MUST). A fallback that lowers capability below the floor
is a policy violation, not a convenience. A failure after an external action was
dispatched (ledger state `dispatched` or `unknown`) — for example a 5xx after a tool
request was sent — is `interrupted` or `failed_unknown`, never `failed_network`, and is
ineligible for automatic fallback until the action is reconciled (MUST; AK-TSK-11).

**AK-RTE-13.** Credit exhaustion MUST be a distinct terminal condition for the attempt:
the task pauses with a monetary/quota reason and a recommended action (wait, switch
account, switch route, escalate). It MUST NOT silently become a cheaper model (MUST).
If no adequate route is available, the task blocks and asks, rather than degrading.
Route candidates MUST record capability (`meetsFloor`) and availability (`available`,
`quota_exhausted`, `auth`, `rate_limited`, `unknown`) as separate fields: quota, auth or
rate state never clears or sets `meetsFloor`, and a route below the task's required skill
support is `meetsFloor: false` however available it is (MUST).

**AK-RTE-14.** Before a turn is dispatched on a new route, Akira MUST run a compatibility
check: context budget, tool dialect, required skills present and executable, required
connectors authorised, and output requirements. A failed check blocks dispatch with a
specific repair action (MUST).

**AK-RTE-15.** Route provenance MUST be recorded for every attempt: which model the
provider actually reported (including reroutes), which account, which harness, and
whether the effective model differs from the requested one (MUST). Akeru's
`turn.started` payload and Codex `model.rerouted` event are the hooks; trace
instrumentation must be extended because Mastra driver turns currently do not annotate
provider/model in the trace (`docs/operations/provider-model-routing.md`, D).

**AK-RTE-16.** An unsupported case MUST fail closed with a typed, actionable error. No
silent substitution of model, provider, account or tool dialect is permitted (MUST).

---

## 7. Good-enough evaluation and early triage

Design detail: this section, with per-route support in `docs/07-integrations.md` §2 and
the delivery plan in `docs/11-backlog.md` §5.

The rule that organises this section: **adequacy is task-specific and evidence-based;
cost is optimised only above the capability floor.**

### 7.1 Task classes (initial configuration)

Classes, floors and preferences are **data**, reviewed by an operator. They are not
HUMAN-approved policy and must not be presented as such. The initial set:

| Class | Example | Capability floor (initial) | Default preference |
|---|---|---|---|
| T1 quick response | answer a question, draft a short reply | text, verified route | cheapest adequate, lowest latency |
| T2 code change | bounded repository change with tests | tool calling, repo read/write, verified dialect | ability-verified route, then cost |
| T3 data extraction | read a sheet/CSV, produce cited results | tools + native or projected skill | native skills if required by the task |
| T4 research brief | multi-source synthesis with citations | web fetch, ≥64k context, structured output | context and citation reliability |
| T5 integration build | new connector/API workflow | full tool suite, long context, judgment | strongest adequate route; spec-first hybrid |
| T6 high-stakes review | legal, security, production change | highest capability + human review gate | best available + mandatory human review |

A task may be reclassified by re-triage; class changes are recorded with reasons. The
floors are deliberately coarse: precision belongs in the eval record, not in a prose
table.

### 7.2 Triage before dispatch

**AK-TRG-01.** Akira MUST triage a task before substantial execution or spawning any
child agent: classify the task, estimate effort/cost range and uncertainty, list
complexity drivers, check specification readiness, and record a proposed route with
reasons (MUST). Triage records are inspectable and immutable; a later re-triage creates
a new revision.

**AK-TRG-02.** Complexity drivers MUST include, at minimum: requirement ambiguity,
number and novelty of integrations, context size, validation difficulty, expected
rework, external dependencies, and irreversibility of side effects (MUST). A task with
any driver above the configured threshold is flagged *large/complex* and cannot be
auto-dispatched to a below-floor route.

**AK-TRG-03.** When the task cannot be estimated honestly, triage MUST schedule bounded
discovery with an explicit budget (time/tokens/cost) and a stopping rule, and MUST
require a re-triage on the discovery result (MUST). Discovery is a task, not an
unbounded conversation.

**AK-TRG-04.** The estimate MUST be a range with a stated basis (task-class priors, past
accepted outcomes, observed usage) and a confidence, not a single invented number
(MUST). Estimates, actuals and revisions are retained so calibration is measurable.

**AK-TRG-05.** Triage MUST be re-run when: actual spend exceeds the estimate band, a new
integration/dependency appears, acceptance criteria change, the chosen route fails
capability checks, or rework passes the configured threshold (MUST).

### 7.3 Specification readiness

**AK-TRG-06.** A task is *ready for simpler-model execution* only when all of the
following are evidenced, not asserted: intended outcome; scope and exclusions;
dependencies and interfaces; constraints; bounded subtasks and handoff boundaries;
acceptance examples; independent validation method; unknowns either resolved or
explicitly assigned to a named decision-maker (MUST). A long document is not evidence.
These are nine named criteria (`dependencies` and `interfaces` are separate), each
carrying an evidence link; a `pass` with no evidence link is invalid.

**AK-TRG-07.** Readiness MUST be a scored checklist with per-criterion evidence links,
returning `ready`, `ready-with-risks` (named risks accepted by policy or HUMAN) or
`not-ready` (MUST). "Not ready" prohibits the specification-led downgrade path; it does
not prohibit advanced-model execution.

**AK-TRG-08.** The readiness result MUST travel with the task and be validated again by
the executing bot's admission check; an implementer that finds an unresolved interface
or contradictory constraint MUST stop and raise it rather than guess (MUST).

### 7.4 Adequacy, escalation and cost

**AK-TRG-09.** Each task class MUST define a capability floor: required tool support,
minimum context, required skill execution level, and reliability evidence for the
dialect it uses (MUST). Floors are configuration with an evidence record, not prose.

**AK-TRG-10.** Among routes that meet the floor, selection SHOULD prefer the lowest
expected total delivery cost (including retries, review and rework), then latency.
Below-floor routes MUST NOT be selected for cost reasons (MUST). Cost ranking MUST
compare like with like: within one auth class by default; ranking across auth classes
uses a single labelled routing comparison unit (the API-equivalent price-table estimate,
displayed as "routing comparison, not spend") and only when the routing policy enables
it, otherwise the operator chooses (MUST; `docs/09-accounting.md` §1.7).

**AK-TRG-11.** Adequacy estimates MUST be empirical: per-route, per-task-class accepted
outcome rates with sample size and recency, derived from task ratings and rework
evidence. A new route starts as `unknown` and may run only in bounded trial mode on
non-critical tasks until it has evidence (MUST).

**AK-TRG-12.** Escalation MUST be triggered by evidence: repeated failed attempts,
review rejection, capability error, readiness failure, or a task class that requires
judgment. De-escalation MUST happen when a task becomes well specified and the cheaper
route's trial evidence supports it (MUST). Escalation and de-escalation are recorded
route decisions with reasons.

**AK-TRG-13.** Switching models because credits ran out is a *cost/availability* event.
It MUST NOT be recorded or rationalised as an adequacy decision, and it MUST NOT lower
the floor (MUST).

**AK-TRG-14.** Total delivery cost is the unit of optimisation: planning, discovery,
model turns, tools, child agents, review, retries, rework, coordination and observer
overhead are all included (MUST). Cost-per-accepted-task is the headline metric, not
tokens or price per million alone.

**AK-TRG-15.** Numeric thresholds, budgets and approval limits MUST be configuration,
versioned and visible, with the specification's proposed defaults clearly marked
"proposed, not HUMAN-approved" (MUST). No requirement in this document depends on a
threshold value being correct.

**AK-TRG-16.** The triage decision and its rationale MUST be visible before dispatch in
the UI and MUST be recorded in the task's decision record (evidence, alternatives,
assumptions, uncertainty) (MUST).

---

## 8. Durable tasks and safe continuation

Schemas and state machines: `docs/04-data-model.md` §5–§8. Contracts:
`docs/05-interfaces.md` §4.

### 8.1 Task lifecycle

**AK-TSK-01.** A task MUST be an orchestration aggregate with a stable id and a state
machine: `proposed → triaged → ready → running → (awaiting_input | blocked | paused) →
review → done | failed | cancelled`; `reopened` is allowed from terminal states with a
recorded reason (MUST). Transitions are events; projections are derived. The canonical
transition table (`docs/04-data-model.md` §4.1) MUST define every recovery edge:
`awaiting_input`, `blocked` and `paused` each return to `ready` through a named event
(answer recorded, blocker resolved, `task.resume`), and each attempt-outcome class has a
defined next state (quota → `paused`; capability/tool-contract/safety → re-triage;
interrupted/unknown → `blocked` or `awaiting_input` after reconciliation). A `not-ready`
readiness result blocks only specification-led or below-floor routes (AK-TRG-07).

**AK-TSK-02.** A task MUST carry: requester, assignee bot, acceptance criteria, route
decision reference, priority, deadline (optional), dependencies, artifacts, review
references and cost rollup (MUST).

**AK-TSK-03.** Exactly one attempt may be active per task (assumption A9). Starting a
new attempt while one is active MUST be rejected unless the active attempt is first
cancelled with a recorded reason (MUST).

**AK-TSK-04.** An attempt MUST record: task id, attempt number, route, bot, start/end,
outcome class, provider-reported model, tokens/cost, checkpoint-before reference,
artifacts produced, and the reason it ended (MUST). Attempts are append-only.

**AK-TSK-05.** Cancellation MUST stop provider work, mark the attempt cancelled, keep
completed artifacts, stop child work started by that attempt (Akeru cancels children of
an interrupted turn), and leave the task in a resumable or terminal state as chosen by
the canceller (MUST).

### 8.2 Checkpoints

**AK-TSK-06.** A checkpoint MUST capture the durable, portable state needed to continue
elsewhere: task definition revision, acceptance criteria, plan with step status, decisions
made (with evidence), open questions, artifact references and hashes, memory deltas,
skill/procedure versions, action-ledger watermark, and next-step intent (MUST). It MUST
be sufficient for a different provider to continue without the previous session (MUST).

**AK-TSK-07.** A checkpoint MUST NOT contain provider private reasoning traces, raw
chain-of-thought, credentials or unbounded logs (MUST NOT). A summary of conclusions and
evidence is required; a transcript of hidden thinking is neither required nor acceptable.

**AK-TSK-08.** Checkpoints MUST be created at: task start, before and after every
external side effect, on attempt end, before a route switch, before a pause/block, and on
a configurable cadence during long work (MUST). The record is small and versioned; the
workspace file snapshot remains a separate git-ref checkpoint (Akeru's mechanism,
retained).

**AK-TSK-09.** Resuming MUST reconstruct the task context from the checkpoint and the
canonical transcript, then run a compatibility check (§6.3) before dispatch. The resume
record MUST name what was lost (for example provider cache) and what is assumed (MUST).

### 8.3 External effects

**AK-TSK-10.** Every external write MUST pass through one Action Executor and be recorded
in an append-only action ledger with: action id, task/attempt, connector and operation,
request hash, target, idempotency key (where the provider supports one), state
(`intent → dispatched → confirmed | failed | unknown`), external id and reconciliation
method (MUST).

**AK-TSK-11.** Akira MUST NOT retry an external action whose outcome is unknown until
reconciliation has established whether the first attempt took effect (MUST NOT). It may
reconcile by reading external state, by idempotency lookup, or by asking a HUMAN. An
unresolvable unknown escalates and blocks dependent work.

**AK-TSK-12.** Exactly-once is claimed only where the external API provides a mechanism
that makes it true (idempotency key, dedupe id, natural key). Everywhere else the
specification claims at-least-once with reconciliation, and says so (MUST). Chat-result
delivery exactly-once is a separate mechanism (Akeru acknowledges delegation results in
the same persisted step as the next turn start; retained).

**AK-TSK-13.** Actions MUST be idempotent by construction where possible: create-with-key,
upsert, or a read-back check. Action keys are scoped to the task and the logical intent,
not to a retry (MUST).

### 8.4 Recovery, concurrency and reconciliation

**AK-TSK-14.** On server start, Akira MUST reconcile: running attempts with no live
session (mark failed with a resumable checkpoint), queued work never dispatched
(dispatch or mark), action-ledger entries in `dispatched`/`unknown` (verify), and
checkpoint/task version mismatches (surface, do not guess) (MUST). Akeru's
`reconcileDelegations` startup pattern is reused as the model.

**AK-TSK-15.** Restart MUST NOT lose or duplicate a chat result, and MUST NOT silently
mark a task done. A task whose outcome is uncertain is `awaiting_input` or `blocked`,
never `done` (MUST).

**AK-TSK-16.** Locks MUST be explicit, keyed and time-bounded: one writer per task, one
writer per bot memory scope, one action executor per connector account. A stale lock is
recovered by lease expiry and recorded, not by deleting state (MUST).

**AK-TSK-17.** Handoffs between bots MUST be tasks (delegation with a parent link, or a
reassignment), with acceptance criteria, checkpoint and usage attribution. A chat message
is not a handoff (MUST).

**AK-TSK-18.** Cloud/child agents (temporary workers, sandbox runs, delegated bots) MUST
be tracked as child units of work with their own usage records and parent linkage, never
as hidden cost (MUST).

---

## 9. Portable skills and procedures

Design detail, per-route support levels and the v1 catalogue: `docs/07-integrations.md` §4 and `docs/15-skills-v1.md`.

**AK-SKL-01.** Akira MUST adopt one canonical skill package: a directory containing
`SKILL.md` with YAML frontmatter (`name`, `description`, version, allowed tools) and an
instructions body, plus optional `references/`, `scripts/` and `assets/` (MUST). This is
the format three inspected ecosystems already read: Claude Code scans skill roots,
Codex lists skills over its app-server, Grok reports them via `grok inspect --json`
(source-cited in `docs/02-akeru-baseline.md`).

**AK-SKL-02.** Akira MUST publish a human-facing `SKILLS.md` index generated from the
registry (names, purpose, version, per-route support, dependencies). Execution MUST NOT
depend on a file literally named `SKILLS.md`: no inspected candidate discovers that name
(MUST). The HUMAN request for "SKILLS.md support" is met by the canonical package plus
the generated index, and this substitution must be stated in the UI.

**AK-SKL-03.** Each skill MUST declare: metadata, triggers/invocation, instructions,
supporting resources, tool and connector needs, validation command, version and
provenance (authored, vendored, imported), and a license (MUST).

**AK-SKL-04.** The registry MUST materialise skills per route through adapters with four
operations: discover, register/project, can-execute, execute-and-verify (MUST). A route's
support level MUST be one of: `native-verified`, `native-unverified`,
`projected-unverified`, `prompt-injected`, `unsupported`. Verification is orthogonal to
the mechanism: every per-route entry carries a `verified` flag backed by an evidence
record, including for `prompt-injected`; an entry without an evidence record is
unverified whatever its mechanism (MUST; `docs/05-interfaces.md` §3).

**AK-SKL-05.** `native-verified` requires an end-to-end execution on that route,
including access to at least one supporting resource file, recorded with route, model,
date and evidence (MUST). A visible skill name or a copied file is not verification.

**AK-SKL-06.** Custom API routes without native skills MUST use prompt injection of the
skill instructions plus Akira's tool runtime, labelled `prompt-injected`; they MUST NOT
claim native skill selection (MUST). The empty catalogs in Akeru's Custom API, Kimi and
OpenCode Go drivers (V) are the baseline this requirement fixes.

**AK-SKL-07.** Codex skill discovery and `$name` invocation MUST be verified
end-to-end, not inferred from the app-server listing or the composer text (MUST). The
handoff specifically identifies Codex wiring as uncertain; the spec resolves it by test,
not assumption.

**AK-SKL-08.** Grok discovery MUST run through `grok inspect --json` and MUST handle the
missing-CLI case explicitly (empty catalog with reason, not a cached empty success)
(MUST). Claude scanning MUST cover user and project roots with documented precedence,
and the built-in no-CLI runtime path must be tested, since the skill dispatch in
`ClaudeDriver.ts`/`ClaudeSkills.ts` is used by the composer and may not be the path the
Mastra-orchestrated Claude transport takes (V, sources cited).

**AK-SKL-09.** Switching route mid-task MUST re-run the skill compatibility check and
MUST surface skills that will be prompt-injected or unavailable, before dispatch (MUST).

**AK-SKL-10.** Procedures MUST reference skills by id and minimum version; a procedure
whose skill is unavailable on the chosen route is not dispatchable (MUST).

**AK-SKL-11.** Skill and procedure changes are versioned and audited; a bot cannot
silently upgrade its own procedure or widen its own tool grant (MUST). Observer proposals
to change skills/procedures follow §11 and need approval.

**AK-SKL-12.** Skill bundles and their support matrix MUST survive export/restore, with
the per-route verification results retained and invalidated when the route, model or CLI
version changes (MUST).

**AK-SKL-13.** Akira v1 MUST ship the enumerated skill catalogue in
`docs/15-skills-v1.md`: ten mandatory skills and four connector-conditional skills, each
with purpose, triggers, dependencies, expected route support and a validation fixture
(MUST). A skill without a passing fixture is `deferred`, never "experimental" or
silently available. `SKILLS.md` is generated from this catalogue and lists status and
support per route (MUST).

**AK-SKL-14.** A connector-conditional skill MUST NOT be listed as available before its
connector reaches workflow-verified status; if the connector slips, the skill slips to
the next release. Browser automation MUST NOT be substituted for the missing connector
capability in a skill's advertised support (MUST NOT).

---

## 10. Collaboration, deliberate communication and silence

Design detail: `docs/08-collaboration-and-accountability.md` §2–§4.

**AK-COL-01.** Rooms MUST have a topic, members with roles (owner, contributor,
observer), an addressed-message rule, a board of durable items, and a decision log
(MUST). Akeru groups (boss + specialists, mentions) are the base; rooms add boards,
roles and explicit routing rules.

**AK-COL-02.** Message routing MUST be deterministic and explainable: a direct mention
addresses one bot; a room rule (round-robin, lead, or explicit assignment) decides who
answers when nobody is mentioned; the rule is visible in the room (MUST). The default
rule for a new room is `mention` (multiple mentions: first-listed wins unless the room is
configured last-wins; an unaddressed message goes to the lead or to no one, never
broadcast). Akeru's "boss answers every message, last mention wins" is retained as the
`lead-bot` rule configuration and applied to migrated Akeru groups.

**AK-COL-03.** Bots MUST be able to act quietly: work on a task, update a board item and
leave the conversation untouched (MUST).

**AK-COL-04.** Ending a turn without a visible message MUST be a first-class outcome
(`TurnOutcome = silent`) with a reason code, recorded in the audit trail, and never
rendered as a chat message (MUST). "Nothing to say" announcements are prohibited
(MUST NOT).

**AK-COL-05.** Silence is justified only when at least one holds: the message requires no
new work and adds no information; the point is already answered by a newer message or by
another bot; the bot is waiting on a dependency and has nothing actionable; the bot is
not addressed and has no evidence to add; the message is a duplicate within the dedupe
window; quiet hours or an explicit room rule applies (MUST). The policy is data, not
improvisation. The silence reason codes in `docs/08-collaboration-and-accountability.md`
§3.2 form a closed set that maps one-to-one onto these clauses (`no_evidence` is the
"not addressed" clause; `policy_hold` is the explicit-room-rule clause); a directly
addressed bot cannot be silent on a direct question.

**AK-COL-06.** A silent turn MUST still journal what the bot did or checked, any spend,
and why it stayed silent, visible to an operator and not to the room by default
(MUST). Silence never hides activity, errors or cost.

**AK-COL-07.** Akira MUST prevent ping-pong: no auto-follow-up turns between bots,
per-thread bot-message budget, mention-only bot-to-bot routing unless a task requires it,
dedupe window per topic, and a hard stop with an operator alert (MUST). Akeru already
ignores bot-authored inbound channel messages and starts no follow-up turn when
delegated work finishes; those behaviours are retained and generalised.

**AK-COL-08.** Challenging work MUST be structured: a claim, its evidence, the objection,
the proposed test or correction, and the requested decision (MUST). "I disagree" without
evidence is not a challenge.

**AK-COL-09.** Disagreement MUST be recorded, not smoothed away. A room decision records
dissent and the evidence behind it; manufactured consensus is a defect (MUST).

**AK-COL-10.** Corrections MUST create a new revision of the artifact or decision,
retaining the previous one and the reason (MUST). Akeru's reroute and revert patterns
(pre-checkpoint restore, message revert) are reused where applicable.

**AK-COL-11.** Handoffs MUST be task objects with owner, acceptance criteria, checkpoint
and next action; the receiving bot acknowledges or rejects with a reason (MUST).

**AK-COL-12.** Notifications MUST be deduplicated and meaningful: an operator sees
blockers, failures, approvals and unresolved external effects; routine progress is
batched. No notification for "nothing happened" (MUST).

**AK-COL-13.** Duplicate work MUST be detectable: a task claimed by two bots, or two bots
answering the same request, triggers a room-level resolution instead of two outputs
(MUST).

**AK-COL-14.** Communication style MUST follow the persona and the room norm (language,
length, formality), while substantive content requirements (evidence, uncertainty,
next action) are non-negotiable (MUST).

---

## 11. Task ratings, reputation and the observer

Design detail and dispute mechanics: `docs/08-collaboration-and-accountability.md` §5–§7.

### 11.1 Ratings

**AK-RAT-01.** The rated object MUST be a task outcome, not a bot's personality or
popularity. A rating record MUST carry: task id and revision, reviewer identity and
relationship (consumer, peer reviewer, observer, HUMAN), criteria scores, reasons,
linked artifacts/revisions, unresolved issues, difficulty context, timestamp and
provenance (MUST).

**AK-RAT-02.** Criteria MUST cover at least: issue-resolution completeness, output
quality/correctness, rework required, efficiency (time and cost relative to difficulty),
and clarity of handoff (MUST). Scores use a documented scale with anchors; free text is
required for low scores and for any score that contradicts the acceptance criteria.

**AK-RAT-03.** Self-rating MUST be impossible: a bot cannot rate its own task, and the
system MUST ignore any attempt (MUST NOT). A bot that consumed another bot's output may
rate it; a bot that merely observed may leave a review note that does not count as a
consumer rating.

**AK-RAT-04.** A task has at most one current rating per reviewer; a revised rating
supersedes the previous one with both retained (MUST). Aggregate reputation is derived
from ratings, never edited directly.

**AK-RAT-05.** A contested rating MUST be disputable: the rated bot or a HUMAN can open a
dispute with evidence; disputed ratings are excluded from aggregates until resolved, and
both positions remain visible (MUST). The resolver MUST be distinct from both the
rating's author and the disputant (or a HUMAN) and is recorded (MUST).

**AK-RAT-06.** Ratings without evidence (U6) (no artifact link, no acceptance-criteria
reference) MUST be flagged low-confidence and MUST NOT move reputation beyond a bounded
amount (MUST). The aggregation model is configurable; no weights are HUMAN-approved in
this draft (`docs/13-open-decisions.md` U6).

**AK-RAT-07.** Anti-gaming MUST include: mutual-praise detection (reciprocal high ratings
with no rework evidence), reviewer-independence weighting (consumer > peer > observer),
difficulty normalisation, and anomaly review by the observer (MUST). A bot cannot improve
its reputation by hiding hard work: tasks it declines or blocks are recorded.

**AK-RAT-08.** Reputation MUST be presented with sample size and confidence, broken down
by task class and route, and MUST NOT be a single opaque number (MUST).

### 11.2 Observer

**AK-OBS-01.** The observer MUST consume outcome evidence (ratings, rework, failed
attempts, cost, incidents, silence decisions), not chat volume, and MUST publish
proposals as durable records with a target (template, persona, procedure, skill, route
policy, communication policy), rationale, evidence links, expected benefit and estimated
cost (MUST).

**AK-OBS-02.** A proposal lifecycle: `draft → evaluated → awaiting_review → accepted |
rejected | superseded`, with an evaluation on held-out or shadow tasks before
`awaiting_review` (MUST). A proposal that cannot be evaluated is not ready.

**AK-OBS-03.** Activation MUST be explicit, reviewed by a HUMAN or a designated
bot-admin with the authority, versioned, and reversible to the previous revision
(MUST). The observer MUST NOT activate its own proposal (MUST NOT).

**AK-OBS-04.** The observer MUST NEVER silently change HUMAN-defined goals, persona
identity fields marked as HUMAN-owned, or permissions. It may propose; it may not edit
(MUST NOT). This is a hard boundary even when the proposal is obviously beneficial.

**AK-OBS-05.** Refinements MUST be evaluated on outcomes that matter: accepted-task rate,
rework, escalation rate, cost per accepted task, incident rate. A refinement that merely
raises peer ratings without improving outcomes MUST be rejected (MUST).

**AK-OBS-06.** Observer overhead MUST be visible in usage and cost, attributed to its own
category and the tasks it reviewed (MUST). The observer's own effectiveness is subject to
periodic review using the same standards.

**AK-OBS-07.** The observer MUST be able to propose "no change" with evidence, and that
outcome is a success. It MUST not manufacture proposals to look useful (MUST NOT).

**AK-OBS-08.** Observer proposals and their evaluations MUST be exported and restorable;
rejected proposals are retained with their reasons (MUST).

---

## 12. Tokens, cost and credit accountability

Design detail: `docs/09-accounting.md`. The organising rule: **one record, one owner;
roll-ups are queries, never duplicated records.**

**AK-ACC-01.** Every model turn, tool execution with cost, child agent, delegation,
routine run, review and observer activity MUST produce a usage record with a stable
idempotency key and a stated measurement basis (MUST). Akeru's
`akeru_bot_usage_entries` table (migration 056) with `UNIQUE (bot_id, source_key)` is the
base; Akira extends its dimensions.

**AK-ACC-02.** Dimensions MUST include: bot, task, attempt, thread/room, route
(harness/driver/provider/model/account instance), category (turn, tool, delegation,
routine, review, coordination, observer, media, other), and parent-child linkage (MUST).
Akeru's legacy categories (`delegated`, `reflector`, `extraction`, `recall`) map
deterministically onto this set at migration, keeping the original value
(`docs/09-accounting.md` §3). Each record has exactly one category.
Attribution to a room and to a parent task must not be inferred at display time from
mutable state; it is recorded at write time.

**AK-ACC-03.** Token dimensions MUST distinguish uncached input, cached input, cache
creation, output, and reasoning where the provider reports it (MUST). Reasoning is a
subset of output where reported; it MUST NOT be added again. Unavailable values are
`null` with a reason, never zero (MUST).

**AK-ACC-04.** Cost provenance MUST be one of: provider-reported charge, price-table
estimate at a versioned price list, subscription-equivalent estimate, or unknown (MUST).
API-equivalent estimates MUST NOT be presented as money spent on a subscription (MUST).
Currency and price-table version are part of the record. Summaries MUST keep separate
subtotals per currency and cost provenance (provider-reported, price-table estimate,
subscription-equivalent, with unknown coverage); a combined figure, if shown, is a
labelled *combined economic estimate, not spend* shown with its components (MUST).

**AK-ACC-05.** Exclusive usage belongs to the record's owner; inclusive roll-ups sum
exclusive descendants plus the owner's own turn usage, with explicit parent links. A
child's tokens MUST NOT be counted twice in a parent total (MUST). The worked example in
`docs/09-accounting.md` §4 and its unit split (§4a) are normative.

**AK-ACC-06.** Retries, failed attempts, cancelled work and fallback turns MUST be
recorded and visible; cost-per-accepted-task includes them (MUST). Hiding failed spend
is a defect.

**AK-ACC-07.** Coordination and review overhead (observer, peer review, triage, spec
writing, handoffs) MUST be a visible category, not absorbed silently into delivery:
overhead = `review` + `coordination` + `observer`; delivery is every other category
(MUST).

**AK-ACC-08.** Provider-reported plan meters and credit balances MUST be shown with
source and freshness; unknown stays unknown. Akira MUST NOT derive a credit balance from
its own ledger (MUST NOT).

**AK-ACC-09.** Delayed or corrected provider telemetry MUST be handled by appending a
correction record that supersedes the earlier record as the effective usage snapshot for
whichever token and cost fields have become known; queries select the effective revision
once per logical usage record and never sum tokens across revisions (MUST). Akeru's
cache-token correction path is the precedent.

**AK-ACC-10.** Cached tokens MUST be reported separately, and "savings" MUST be derived
from the price table, labelled as an estimate (MUST).

**AK-ACC-11.** Non-token costs (telephony minutes, WhatsApp conversation/template fees,
image/video renders, sandbox and hosting) MUST be recorded in the same ledger with their
own units and price basis, separate from token cost but included in task totals (MUST).

**AK-ACC-12.** Usage MUST be queryable by bot, task, room, route, account, day and
parent/child, with drill-down from a task to its records; exports include the ledger
(MUST).

**AK-ACC-13.** The UI MUST show exclusive and inclusive totals side by side for a task,
and MUST label measured, estimated, subscription and unavailable values distinctly
(MUST).

**AK-ACC-14.** A task's cost summary MUST separate delivery cost from review/
coordination/observer overhead and from failed attempts (MUST). Cost-per-accepted-task
is the complete attributable cost divided by the number of distinct accepted tasks;
rework adds cost, not accepted tasks. Coverage is `(reported + estimated + subscription)
/ (reported + estimated + subscription + unknown)` over cost-bearing records, `n/a` when
there are none.

**AK-ACC-15.** Usage records are append-only and audited; deletion is not a correction
mechanism (MUST; AKIRA-D2).

**AK-ACC-16.** The ledger MUST be usable as the evidence base for routing calibration
(cost per accepted task per route/task class) without a second accounting system
(MUST).

---

## 13. Specialist agents and real integrations

Detailed matrices, evidence and cost basis: `docs/07-integrations.md` §5–§6. The rule:
**a capability exists only when the operation set and the failure semantics are defined;
a vendor API or a connector name is not a capability.**

**AK-SPC-01.** Akira MUST define specialist capability contracts independent of any
vendor: `telephony` (PSTN), `messaging` (WhatsApp Business messaging), `whatsapp-admin`
(profile, numbers, templates, verification), `image-generation`, `video-production`
(MUST). Each contract lists operations, inputs/outputs, asynchrony, idempotency,
delivery/acknowledgement semantics, limits, cost units and required consent/approval.

**AK-SPC-02.** PSTN calling MUST be distinguished from in-app voice (A5, U13). The PSTN adapter
MUST support: place call with a script/goal, DTMF, status callbacks, transcript/recording
per policy, voicemail detection, hangup and cost per minute, with an explicit consent
and recording policy (MUST). Akeru's in-client voice (ChatGPT/OpenAI realtime or
transcribe/reply/speak) is retained as a separate capability and MUST NOT be presented
as telephony (MUST).

**AK-SPC-03.** WhatsApp messaging MUST support text, media, templates (scope U5), inbound webhooks
and delivery states, with an honest `unknown` state when the provider may have accepted a
send (MUST). Akeru's Cloud API channel, direct messages only, one bot per account and a
public HTTPS origin are the base; Akira generalises the adapter but keeps the constraints
visible (`docs/07-integrations.md` §6).

**AK-SPC-04.** WhatsApp Business administration MUST be a separate capability, not
implied by messaging: profile read/update, business profile fields, phone number
registration/verification, message template create/list/update/delete, quality/limit
status, and account-level settings where the provider API supports it (MUST). Each
operation carries its own permission and cost basis; unsupported operations are stated
as such (MUST NOT be claimed).

**AK-SPC-05.** Image generation MUST be provider-agnostic: text-to-image, reference/edit
where supported, size/aspect controls, seed/provenance metadata, storage as an artifact,
cost per image, moderation and asset licensing (MUST). Akeru's ChatGPT/Grok subscription
tools are one provider; a local model (the operator's existing SDXL pipeline) and an API
provider are alternatives (MAY).

**AK-SPC-06.** Short movies MUST be a complete workflow (A6), not a single "make video" call:
brief → script → storyboard/shot list → per-shot generation → audio/voice → assemble →
review → approved deliverable, with every step an artifact and every paid render gated
by an explicit approval policy (MUST). Job submission, polling, cancellation, retry and
partial-failure recovery are required.

**AK-SPC-07.** Every specialist integration MUST have: credential custody, webhook/
callback endpoint with signature verification where offered, replay/idempotency handling,
rate-limit and cost guards, delivery state, failure classification, and per-task cost
attribution (MUST).

**AK-SPC-08.** No specialist action that contacts a real person or spends real money may
run in verification without a HUMAN-authorized test account or explicit approval
(MUST; AKIRA-D3). Stubs and synthetic fixtures are the default verification path.

**AK-SPC-09.** Provider choice (telephony, WhatsApp BSP vs direct, image, video) MUST be
recorded as an integration decision with current primary-source evidence, pricing basis
and date, and MUST be replaceable behind the contract (MUST). No vendor is recommended
in this draft without that evidence; candidates are named, not selected.

**AK-SPC-10.** Specialist bots MUST be ordinary bots with templates, skills and tool
grants; a specialist is not a separate runtime or a second orchestrator (MUST). For
example, "Natalia" may hold `telephony` grants without becoming a telephony service.

**AK-SPC-11.** Asynchronous jobs MUST be durable: submitted, running, succeeded, failed,
cancelled and unknown states are stored; a restart resumes polling; an unknown submission
is reconciled before a duplicate job is created (MUST).

**AK-SPC-12.** Every specialist scenario in `docs/10-tests-and-acceptance.md` MUST pass
against stubs before a live provider is enabled for the team (MUST).

---

## 14. Connectors and extensibility

Detailed inventory and per-service matrix: `docs/07-integrations.md` §6–§7.

**AK-CON-01.** Akira MUST publish a service/action inventory for the integrations the team
actually needs, with read and write actions listed separately. It MUST NOT claim
connector parity from a connector count or a directory listing (MUST NOT).

**AK-CON-02.** For each integration the inventory MUST state: concrete API/MCP/connector,
authentication and token custody, scopes, host dependencies (local vs hosted), onboarding
steps, read/write coverage, gaps, implementation effort range, ongoing cost basis, and
evidence date (MUST).

**AK-CON-03.** Tool discovery, authentication and successful workflow execution MUST be
three separate statuses. An installed plugin, a visible tool or a completed OAuth flow is
not evidence of a working workflow (MUST).

**AK-CON-04.** The base substrate is: custom MCP servers (supported by Akeru), a
bring-your-own Composio account (supported, with verification limits), and first-party
connectors built by Akira where an MCP or broker is unsuitable (MUST). The bundled Akeru
plugin catalog is currently not installable (all 54 entries are `verification-pending` or
`approval-pending`; V), so it MUST be presented as a preview, not as available capability
(MUST).

**AK-CON-05.** Hosted connector credentials do not transfer. An OAuth token held by a
hosted vendor is not available to a local runtime; moving the client does not move the
token backend (debate finding F1, retained). Import MUST list connector re-authentication
as an explicit migration step (MUST).

**AK-CON-06.** Held tokens MUST be protected: per-connector custody, least-privilege
scopes, per-bot access grants, encryption at rest where the store supports it, rotation
and revocation, and no token in logs/exports (MUST).

**AK-CON-07.** Connector actions MUST flow through the Action Executor and ledger
(§8.3), with idempotency where the API supports it and reconciliation where it does not
(MUST).

**AK-CON-08.** Per-bot access control MUST be default-deny for mutating scopes: a bot
gets a connector action only through its template/tool grant, and widening requires an
explicit reviewed change (MUST).

**AK-CON-09.** Connector health MUST be a real check (a read operation with the saved
credential), with last success, last failure, repair action and staleness (MUST).

**AK-CON-10.** Browser automation MAY be used as a fallback for services with no
structured API, behind an explicit "unverified fallback" label and separate permission;
it MUST NOT be presented as connector parity and MUST NOT be the default for actions that
send, pay or delete (MUST).

**AK-CON-11.** Connector and plugin supply chain MUST be trusted explicitly: pinned
versions, provenance, review before install, sandboxed or least-privilege execution, and
the ability to disable one connector without touching others (MUST).

**AK-CON-12.** Extensibility MUST be documented as a contract (adapter interfaces,
manifest, capability declaration, approval classes) so a new connector or specialist is
data + a small adapter, not a fork of the orchestrator (MUST).

---

## 15. Autonomy, communication and approval boundaries

**AK-SEC-01.** Bots MUST resolve routine work inside the user's intent without asking:
reading, planning, drafting, running safe tools, retrying safe failures and updating
their own task state are routine (MUST). Asking for permission must be reserved for
consequential actions, missing information and genuine ambiguity (MUST).

**AK-SEC-02.** Consequential actions MUST require approval unless a recorded policy grants
them: sending external messages, publishing, paying, deleting, changing production,
changing accounts/permissions, exposing secrets, signing, refunding, and any call to a
real person (MUST). Akeru's protected-action list and approval semantics are the base
(`Auto review` allows routine actions and asks for these).

**AK-SEC-03.** Approval MUST be bound to the exact action and tool call, single-use by
default, and MUST NOT be silently broadened by a bot, a retry or a route change (MUST).
An approval that expires or is lost is re-requested, never assumed.

**AK-SEC-04.** Permissions MUST be least-privilege and scoped by user, bot and room:
workspace access, connector scopes, tool grants, memory scopes and model routes are
separate (MUST). A room cannot grant a bot access the bot's grant does not allow.

**AK-SEC-05.** Untrusted content MUST NOT become instructions: web pages, emails,
attachments, connector output, MCP tool descriptions and third-party skill files are
data. The agent instructions MUST state this and the tool runtime MUST mark provenance
(MUST). Prompt-injection tests are required (`docs/10-tests-and-acceptance.md`).

**AK-SEC-06.** Secrets MUST NOT enter prompts, memory, checkpoints, artifacts, exports or
logs. A secret detected in content is redacted and the incident recorded (MUST).

**AK-SEC-07.** Remote access MUST be authenticated, scoped and revocable: environment
pairing tokens, SSH/tailnet support, admin scopes for credential and assignment commands,
and no credential exposure to clients (MUST). Public exposure of the WhatsApp webhook is
the only intended inbound surface; everything else stays private by default.

**AK-SEC-08.** The system MUST record an audit trail for: credential changes, permission
changes, approvals, destructive actions, connector actions, route overrides, template/
persona activation, observer activation, and export and restore operations (actor,
scopes, bundle id, destination, checksum, result) (MUST). Audit records are append-only
and exportable.

**AK-SEC-09.** Autonomy MUST be bounded by spend and blast radius: per-task and per-bot
concurrency, per-connector rate limits, approval gates for expensive operations, and a
kill switch that pauses all dispatch without losing state (MUST). Defaults are proposed
and configurable; they are not HUMAN-approved budgets.

**AK-SEC-10.** A bot MUST stop and escalate on: conflicting instructions, an action it
cannot undo, an unresolved external effect, a capability mismatch, or a request outside
its grant. Stopping is a success mode, not a failure (MUST).

**AK-SEC-11.** Dependency and plugin trust: pinned versions, no auto-update of
third-party code into the runtime, provenance recorded, and a review gate for any plugin
that can write externally (MUST).

**AK-SEC-12.** Privacy: memory scopes (private bot, room, task), retention configuration,
export/delete-on-request semantics that respect AKIRA-D2, and no analytics payload that
contains user content (Akeru's fixed analytics schema is retained).

---

## 16. User experience

Flows and wireframes: `docs/06-ux.md`. UX requirements are normative in §4; this section
adds the quality bar.

**AK-UX-17.** The primary workspace MUST make the team legible in one screen: who is
working, on what, through which route, at what cost band, and what needs a human (MUST).

**AK-UX-18.** Progressive disclosure MUST be the default: compact indicators expand into
task, usage, rating and decision detail; no dashboard is required to operate (MUST).

**AK-UX-19.** Model/route switching MUST be one action from the bot panel, chat header or
task inspector, with consequences previewed (MUST).

**AK-UX-20.** The UI MUST never display invented precision: unknown usage, unverified
integration, stale quota and estimated cost are labelled as such at the point of display
(MUST).

**AK-UX-21.** Accessibility and responsiveness: keyboard operation for the main flows,
reduced-motion respect (Akeru already supports it), and a usable narrow layout (MUST).

**AK-UX-22.** The visual language follows the supplied Grokbot screenshot: roster and
rooms on the left, conversation/board in the centre, contextual inspector on the right,
quiet surfaces, dense but readable typography (MUST).

---

## 17. Deployment, migration, maintenance and recovery

Runbooks: `docs/12-operations.md`. Migration detail: `docs/11-backlog.md` §11 and
`docs/06-ux.md` §11.

**AK-OPS-01.** Akira MUST run as a single-writer server (AKIRA-D4) with a documented state
directory, SQLite database, attachments, memory files, logs, secrets and worktrees
(MUST). Akeru's layout (`<base>/userdata/state.sqlite`, `secrets/`, `logs/`,
`attachments/`, worktrees) is the base.

**AK-OPS-02.** Deployment MUST be reproducible: pinned Akeru revision, lockfile, exact
Node version, build artifact hash, and a documented install/upgrade/rollback procedure
(MUST).

**AK-OPS-03.** Upstream maintenance MUST be a patch series (AKIRA-D6) over a pinned revision, with
each patch owning a requirement, a test and a conflict note, and a rebase runbook (MUST).
A blind upstream merge is prohibited; every port is reviewed against Akira's identity,
state and provider architecture (upstream AGENTS guidance, adopted as policy).

**AK-OPS-04.** Backup MUST cover the complete restore set: database, attachments,
memory, artifacts, settings, skill/procedure/template registry, action and usage ledgers,
and configuration (MUST). Secrets are backed up only in an encrypted, separately handled
form, or re-entered after restore — never left in a plain bundle (MUST).

**AK-OPS-05.** A restore MUST be verified on a second environment, with a checklist that
proves: bots and personas, rooms, tasks and checkpoints, memory, skills, connector
registrations (with re-auth steps), usage history, and unresolved actions (MUST). A
backup that has not been restored is not a backup.

**AK-OPS-06.** Upgrades MUST snapshot state before migration, run forward migrations,
verify health, and support rollback to the previous server and database snapshot
(Akeru's service update already snapshots; retained and extended).

**AK-OPS-07.** Health and monitoring MUST cover: server liveness, database integrity,
queue/worker backlog, provider auth health, quota freshness, channel webhook health,
disk space, backup age, and unresolved external effects (MUST). Alerts are actionable and
deduplicated; no alert storm.

**AK-OPS-08.** Incident recovery MUST be documented for: provider outage, credit
exhaustion, credential revocation, database corruption, lost acknowledgement, duplicate
send, disk exhaustion, runaway spend, unauthorized action, and secret exposure (MUST).

**AK-OPS-09.** Service objectives MUST be proposed, not asserted (U4): availability target for
the server during working hours, RPO/RTO for state, and maximum tolerated time to notice
a failed channel. They are labelled proposals in `docs/12-operations.md` §2 and require
HUMAN approval.

**AK-OPS-10.** Capacity MUST be stated as a workload model with ranges: bot count, rooms,
concurrent tasks, turns/day, tokens/day, connector calls/day, media jobs/month, and the
corresponding single-node limits (MUST). The model states where it breaks.

**AK-OPS-11.** The retention policy MUST default to keep-everything for bots, chats,
tasks, artifacts, ratings and ledgers, with configurable archival (not deletion).
Permanent purge is an explicit, named, audited HUMAN operation (MUST; AKIRA-D2).

**AK-OPS-12.** A migration runbook MUST exist for the existing team and rooms, including
re-authentication, draft personas, routine recreation and shared-page handling. It MUST
state what cannot be imported rather than inventing it (MUST).

**AK-OPS-13.** Test and staging environments MUST be reproducible from the same artifacts
and MUST NOT point at production credentials. Synthetic fixtures are the default
(MUST; AKIRA-D3).

**AK-OPS-14.** Every release MUST ship: changelog, migration notes, updated compatibility
matrix, known limitations, and the Akeru revision it is based on (MUST).

**AK-OPS-15.** A restored or rolled-back server MUST start in recovery quarantine:
autonomous dispatch, routines, outbound channel delivery and external writes disabled;
the original environment stopped or fenced; the recovery point and the uncertain interval
recorded. Tasks and routines that could have acted in that interval are reconciled
against preserved post-snapshot evidence or external state before release; where a prior
effect cannot be established the task stays blocked for HUMAN reconciliation and is never
replayed (MUST; `docs/12-operations.md` §5.3). A restore drill keeps these disabled.

**AK-OPS-16.** Backups MUST be append-only: each run writes a new uniquely named
generation and uses no deletion flag; earlier generations and database snapshots are
preserved. Removing a backup generation is a separate operation requiring a HUMAN message
naming the items (MUST; AKIRA-D2; `docs/12-operations.md` §5.2).

**AK-OPS-17.** The server MUST NOT accept Akeru's upstream hard-delete command
(`bot.delete`) directly: the decider rejects it unless issued through the `purge.request`
guards (explicit ids, verified backup, `destructive` scope, audit record). Hiding the
UI path is not sufficient; enforcement is at the command authority (MUST; AKIRA-D2).

---

## 18. Acceptance

The normative acceptance suite is `docs/10-tests-and-acceptance.md`. This draft is
accepted only when all fifteen mandatory scenarios pass on a staging build, plus the
requirement-level suites, with evidence attached (scenarios 13–15 were added in v0.4):

1. Same named bot moves Codex → Claude → DeepSeek → Grok and back: identity, memory,
   goal, procedure, skill and task state preserved; provenance recorded.
2. Forced credit exhaustion mid-task: task pauses with the right failure class, no
   silent downgrade, resume on another adequate route from checkpoint.
3. Restart after a stub write was accepted but not acknowledged: no duplicate write, the
   unknown state is visible and reconciled.
4. Skill execution after switching: native or prompt-injected per route, resource access
   verified, support level shown.
5. One template instantiated twice: fully isolated memory, tasks, usage, credentials.
6. Justified silent turn: no chat message, audit record present, no duplicate reply.
7. Peer-disputed rating: dispute recorded, aggregate excludes it, correction preserves
   both versions.
8. Observer refinement: evaluated on held-out tasks, accepted or rejected on outcome
   evidence, overhead visible, goals/persona untouched.
9. Accounting without double counting: parent task, child delegation, retries, observer
   and tool costs each counted once, exclusive and inclusive views consistent.
10. Early triage of a complex integration: flagged before execution, discovery bounded,
    readiness scored, route and reason visible, re-triage on new evidence.
11. Full export and restore of the working team state on a second environment.
12. Deletion safety: archived bot still present after the retention window; no delete
    command dispatched; a direct `bot.delete` rejected without the purge guards; purge
    only with an explicit named HUMAN request.
13. Append-only backup: a later backup never removes earlier generations (T-13).
14. Restore into recovery quarantine: no replay of effects missing from an older
    snapshot (T-14).
15. Skill catalogue completeness and availability gate (T-15).

**AK-TST-01.** No requirement is "done" without a passing test that exercises the
behaviour on the real integration point or a faithful stub, with the evidence linked
(MUST).

---

## 19. Non-goals and explicit deferrals

- Hosted multi-tenant SaaS, billing, per-seat accounts and organization federation.
- A public plugin/skill marketplace.
- Guaranteed Grokbot connector parity; parity is expressed only against the defined
  service/action inventory.
- Redistribution of proprietary connectors or bypassing vendor terms.
- Every provider being interchangeable on every feature: unsupported combinations fail
  closed and are listed.
- Replacing the provider vendors' own clients for interactive coding.
- Native mobile feature parity in the first release; mobile is read/reply/approvals
  first.
- Full video editing/assembly quality; the first release does scripted generation,
  audio and reviewable assembly, not a timeline editor.
- Automatic permanent deletion of anything (AKIRA-D2).

---

## 20. Risks and residual production blockers

| ID | Risk | Impact | Mitigation / status |
|---|---|---|---|
| R1 | Akeru is a pre-1.0 fork of a fast-moving upstream (v0.2.1, 70 open issues, 2026-08 creation) | Rebase cost and regression risk | Pin revision, patch series, CI on both suites, quarterly rebase budget (`docs/11-backlog.md` §15) |
| R2 | Provider behaviour and vendor terms can change without notice | Subscription routes may become impermissible or unusable | Transport-permission field, API-key fallback, no permanent assumptions (AK-RTE-04) |
| R3 | External effects cannot always be exactly-once | Duplicate sends or lost writes | Ledger + reconciliation + unknown state, narrow exactly-once claims (AK-TSK-12) |
| R4 | WhatsApp/telephony onboarding depends on Meta/Twilio approval and a public HTTPS origin | Specialists may be blocked for weeks | Stub-first, onboarding checklist, outbound-only fallback (AK-SPC-03/04) |
| R5 | Skill execution differs per route and can silently degrade | Quality loss after switching | Support levels, E2E verification, re-check on switch (AK-SKL-04/05/09) |
| R6 | Observer and ratings can create perverse incentives | Distorted reputation, hidden hard work | Anti-gaming, evidence requirements, held-out evaluation (AK-RAT-07, AK-OBS-05) |
| R7 | Routing/triage thresholds have no HUMAN-approved values | Wrong cost/quality balance | Configurable, visible, calibration from ledger; defaults labelled proposed (AK-TRG-15) |
| R8 | Akeru's seven-day deletion and delete semantics conflict with AKIRA-D2 | Data loss | Retention disabled before real data, archive-first UI, synthetic tests (AKIRA-D2, ADR-08) |
| R9 | Single-node SQLite and one server process | Capacity and availability ceiling | Documented workload model and migration trigger (ADR-10, AK-OPS-10) |
| R10 | Unverified vendor pricing and subscription entitlement | Cost estimates wrong | Price table versioning, unknown labels, no fabricated totals (AK-ACC-04/08) |

**Residual blockers before production:** disable retention in a built artifact and prove
it; verify DeepSeek tool reliability end-to-end; verify skill execution on all four
routes; prove export/restore; and set the budget/spend policy (U4) plus the remaining
non-blocking choices (U4–U16). Host, subscription transport and distribution are settled
(AKIRA-D4–D6). None of these blocks specification review; all block a real-data launch.

---

## 21. Companion documents

| Document | Contents |
|---|---|
| `docs/01-product-scope.md` | Scope, personas, workflows, what Akira adds over Akeru, success measures |
| `docs/02-akeru-baseline.md` | Pinned-revision source inspection, capability inventory, reuse/extend/replace/build, licensing, gap matrix |
| `docs/03-architecture.md` | Components, boundaries, state ownership, ADR records, upstream mapping, rejected alternatives |
| `docs/04-data-model.md` | Canonical schemas, state machines, invariants, representative records |
| `docs/05-interfaces.md` | RPC/command contracts, adapter contracts, error taxonomy, idempotency |
| `docs/06-ux.md` | Flows and compact wireframes for every primary workflow |
| `docs/07-integrations.md` | Provider/route, skills, connector and specialist matrices with support levels |
| `docs/08-collaboration-and-accountability.md` | Rooms, publish gate, silence, challenge, ratings, observer, audit |
| `docs/09-accounting.md` | Usage/cost ledger, attribution, roll-ups, worked example, reconciliation |
| `docs/10-tests-and-acceptance.md` | Acceptance scenarios, fixtures, failure injection, traceability |
| `docs/11-backlog.md` | Phases, critical path, effort, exit criteria, vertical slice, deferrals |
| `docs/12-operations.md` | Security, deployment, backup/restore, migration, monitoring, incidents |
| `docs/13-open-decisions.md` | Decisions register: resolved HUMAN answers, remaining reversible defaults |
| `docs/14-evidence-log.md` | Source inspection log: files, symbols, commands, dates |
| `docs/15-skills-v1.md` | v1 skill catalogue, `SKILLS.md` contents, support policy, deferrals |

---

*End of specification. Version 0.4 — draft after review round 1. Nothing in this document has
been verified by execution; evidence labels state what was inspected and what was not.*
