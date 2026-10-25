# 03 — Architecture and decision records

**Status:** Final specification v0.7 · **Normative:** `spec.md` §3, §5–§8 · **Base revision:** Akeru `524eb68a` · **Evidence labels** per `spec.md` §0.

---

## 1. Architectural goal

Akira must add product concepts without adding a second brain. Akeru already has one
event-sourced orchestrator, one provider controller and one conversation record. Akira's
architecture extends those and makes the boundaries explicit, so that provider
independence, task durability, routing, ratings and accounting are properties of the
same state machine rather than four side systems.

```
                            ┌──────────────────────────────────────────────┐
   web / desktop / mobile   │  Clients (Akeru web + shared client runtime) │
                            └───────────────────┬──────────────────────────┘
                                                │ typed RPC / WebSocket
                            ┌───────────────────▼──────────────────────────┐
                            │  Orchestration Engine (single writer)         │
                            │  commands → decider → events → projector      │
                            │  aggregates: Bot, Room, Thread, Turn,         │
                            │  Task, Goal, Procedure, Rating, Proposal,     │
                            │  Action, Usage, RouteDecision, Artifact       │
                            └───┬───────────────┬───────────────┬──────────┘
                                │               │               │
                    reactors (side effects)  read models    audit/export
                                │               │
        ┌───────────────────────┼───────────────┼───────────────────────────┐
        │                       │               │                           │
┌───────▼────────┐   ┌──────────▼─────────┐  ┌──▼───────────────┐  ┌────────▼─────────┐
│ Task Supervisor│   │ ProviderCommand    │  │ Action Executor  │  │ Observer Service │
│ (dispatch/     │   │ Reactor +          │  │ (connectors,     │  │ (proposals,      │
│  resume/retry  │   │ AgentController    │  │  specialists,    │  │  held-out eval)  │
│  via commands) │   │ (one turn at a time│  │  ledger + recon) │  │                  │
└───────┬────────┘   │  per thread)       │  └──┬───────────────┘  └────────┬─────────┘
        │            └──────────┬─────────┘     │                           │
        │                       │               │                           │
        │            ┌──────────▼─────────┐  ┌──▼───────────┐   ┌───────────▼────────┐
        │            │ Provider adapters  │  │ Integrations │   │ Usage projection   │
        │            │ Codex/Claude/Grok/ │  │ MCP/Composio/│   │ (exclusive +       │
        │            │ DeepSeek/Kimi/...  │  │ first-party/ │   │  inclusive)        │
        │            └──────────┬─────────┘  │ PSTN/WhatsApp│   └───────────┬────────┘
        │                       │            └──────────────┘               │
        │            ┌──────────▼─────────┐                                 │
        └───────────►│ State: SQLite      │◄────────────────────────────────┘
                     │ events+projections │
                     │ files: memory,     │
                     │ artifacts, secrets │
                     │ git: checkpoints   │
                     └────────────────────┘
```

---

## 2. Component boundaries

| Component | Owns | Must not own | Failure mode it must survive |
|---|---|---|---|
| Orchestration Engine | Command validation, event append, projection, invariants | Provider I/O, tool execution, network calls | Restart mid-command; duplicate command delivery (idempotent command ids) |
| Task Supervisor (reactor) | Deciding when to dispatch, retry, pause, resume — **by dispatching commands** | Direct adapter calls; its own state store beyond a cursor | Crash after dispatch before receipt; recovery re-reads projections |
| ProviderCommandReactor + AgentController | Starting exactly one provider turn per thread; mapping runtime events; cancelling | Task policy, cost policy, routing decisions | Provider dies mid-turn; late events; model reroute |
| Provider adapters | Protocol translation, capability probes, usage extraction | Retry policy, task state, secrets beyond their instance | Auth expiry; malformed stream; unsupported tool dialect |
| Route Planner | Producing RouteDecision records (adequacy, cost, reason) | Dispatch; silent fallback | Stale capability data; unknown route |
| Action Executor | Executing external actions, ledger transitions, reconciliation | Deciding *whether* an action is wanted | Timeout after acceptance; duplicate webhook; partial failure |
| Connector/Specialist adapters | Vendor protocol, auth, limits, mapping to capability contract | Task/rating logic; approvals | Rate limit, revoked token, unknown delivery |
| Usage Ledger | Append-only usage records, corrections, idempotency | Roll-up storage (queries only) | Duplicate settlement; delayed provider usage |
| Observer Service | Proposals, evaluations, evidence | Activating proposals; editing goals/personas | Model outage; bad proposal; evaluation bias |
| Skill/Procedure Registry | Canonical packages, versions, per-route support matrix | Per-provider copies as truth | Missing resource; CLI absent; route switch |
| Publish Gate | TurnOutcome decision (speak/act/ask/silent) and message emission | Task execution | Duplicate/empty messages; loop |
| Export/Restore | Complete bundle, versioned, verified | Secrets in plaintext | Partial export; version skew |

---

## 3. Decision records

Each record is a **proposal baseline** for implementation, not a HUMAN decision. Status:
`adopted-for-spec` (default), `pending-human` (needs an answer), `assumption` (reversible
default, see `spec.md` §3.3).

### ADR-01 — Extend Akeru's orchestration; do not add a second orchestrator

**Status:** adopted-for-spec.

**Context.** Akeru's decider/projector/reactors already own dispatch, persistence and
provider lifecycle. Routing, tasks, ratings and accounting all need to observe and
influence dispatch.

**Decision.** New concepts are new aggregates/commands/events inside the existing engine.
The Task Supervisor is a reactor that only dispatches commands. No adapter or service
starts a provider turn or retries one directly.

**Alternatives rejected.**

- *Per-provider orchestrators with a shared database.* Two retry authorities; duplicate
  side effects; impossible to reason about attempt state.
- *External workflow engine (Temporal, Restate) as authority.* Adds a second source of
  truth and an operational dependency before the single-node limits are reached; revisit
  only if ADR-10's triggers fire.
- *Task state as chat messages.* Unqueryable, unversionable, and lost when a message is
  edited/reverted.

**Consequences.** Every new feature must be expressible as commands/events + projections;
this is slower than a side database and is the point.

---

### ADR-02 — Persona is a versioned document; the tone slider becomes a field

**Status:** adopted-for-spec.

**Context.** Akeru generates instructions from name, date and a 0–100 tone value
(`AkeruAgentInstructions.ts`, V). The named team needs outlook, attitude, procedures and
boundaries; those cannot be reconstructed from a number.

**Decision.** `PersonaRevision` is an immutable, content-addressed document (structured
fields + Markdown body). Every provider receives the same composed instructions. The tone
value remains as `personality.tone` inside the document, not as the identity itself.

**Alternatives rejected.** *Free-text system prompt on the bot record* (unversioned,
unmergeable, leaks into exports without structure); *per-provider prompts* (drift between
routes, exactly the failure the primary goal forbids).

**Consequences.** Akeru's instruction builder becomes a renderer of the persona document.
Provider adapters still add their own harness rules (tools, approvals), but identity text
is composed once.

---

### ADR-03 — Task is a first-class aggregate; chat remains the conversation

**Status:** adopted-for-spec.

**Context.** Akeru's turn is a unit of chat work; delegation is a child thread; a
"request" has no acceptance criteria or attempts. Rating, routing and cost need a durable
object.

**Decision.** `Task` is an aggregate with acceptance criteria, route decision, attempts,
checkpoints, artifacts, review and cost. A task binds to one or more threads/turns; a
turn may exist without a task (trivial chat).

**Alternatives rejected.** *Task = thread* (loses multiple attempts and review);
*task in a separate service* (second authority); *task only in the UI* (unexportable).

**Consequences.** Chat UX must create tasks deliberately, not every message; the triage
threshold decides. Delegation creates a child task with a parent link.

---

### ADR-04 — Continuation is a portable checkpoint; provider state is disposable

**Status:** adopted-for-spec.

**Context.** Akeru checkpoints workspace files to git refs per turn and keeps provider
sessions in a directory. Provider-native sessions cannot move between vendors and may not
survive a restart.

**Decision.** The portable unit is a `TaskCheckpoint`: plan and step status, decisions
with evidence, artifacts + hashes, memory deltas, skill/procedure versions, action
watermark, next intent, open questions. A new route resumes from it plus the canonical
transcript. No requirement depends on provider-private state.

**Alternatives rejected.** *Port provider transcripts and replay tool calls* (dialects
differ; replay can re-execute side effects); *require the same provider to resume*
(defeats the primary goal); *store chain-of-thought* (not available, not appropriate, and
an injection/leak risk).

**Consequences.** Resume costs some context re-establishment; checkpoints must be written
before every external effect; "what was lost" is displayed to the operator.

---

### ADR-05 — One canonical skill package, per-route projections with honest support levels

**Status:** adopted-for-spec.

**Context.** Four inspected discovery mechanisms differ; three drivers declare an empty
catalog (V). A file copied into a root does not prove execution.

**Decision.** Canonical `SKILL.md` package in an Akira registry. Adapters project it into
route-specific roots or prompt-inject it. Support levels are recorded and verified by
execution. `SKILLS.md` is a generated index, never the execution contract.

**Alternatives rejected.** *A single universal skills directory* (no inspected runtime
reads it); *per-route copies as source of truth* (drift, no provenance); *skills as MCP
tools only* (loses the model-directed instruction format that the ecosystems share).

**Consequences.** Some routes will be `prompt-injected`; that is a first-class, visible
quality difference and feeds routing.

---

### ADR-06 — Extend the usage ledger; never derive cost from chat volume

**Status:** adopted-for-spec.

**Context.** Akeru has an append-only ledger with reservations and idempotency (V) but
lacks task/attempt/room/account/parent dimensions and cost provenance.

**Decision.** Extend the ledger additively; add a correction record type; roll-ups are
queries over exclusive records linked by parent ids. Non-token costs use the same table
with units.

**Alternatives rejected.** *Recompute usage from provider logs* (provider-specific,
incomplete, delayed); *a spreadsheet/BI copy* (drifts, double counts); *invoice-based
accounting only* (subscriptions have no per-turn invoice).

**Consequences.** Every execution path must call the ledger; a missing call is a defect,
not a display gap.

---

### ADR-07 — Ratings and observer proposals are orchestration aggregates

**Status:** adopted-for-spec.

**Context.** HUMAN requires task ratings and an observer. Akeru's Observer/Reflector are
memory-curation stages (V), not effectiveness review.

**Decision.** `Rating` and `ObserverProposal` are events/projections with explicit
lifecycle and evidence links. The observer never edits goals/personas; activation is a
separate reviewed command.

**Alternatives rejected.** *Ratings in chat text* (unaggregatable, gameable);
*observer with write access to templates* (violates the no-silent-change requirement);
*LLM-as-judge only* (no consumer evidence, ignores rework).

**Consequences.** Reputation is derived; disputes are first-class; observer cost is
accounted.

---

### ADR-08 — Archive-first lifecycle; no automatic deletion

**Status:** adopted-for-spec (implements AKIRA-D2).

**Context.** Akeru deletes archived bots after seven days by a startup + hourly sweep
(V). The standing HUMAN rule forbids deletion without an explicit named request.

**Decision.** Remove the retention sweep from the Akira build; archived bots and their
data persist. UI "delete" archives. A separate `akira purge` operation takes explicit
ids, requires confirmation, writes a backup first, and is audited. Docker images and
backups are never touched by Akira.

**Alternatives rejected.** *Set retention to a large number* (still an automatic deletion
timer); *keep upstream behaviour and warn* (violates the rule); *delete only when the
operator clicks* (still needs the naming/audit discipline — covered by purge).

**Consequences.** State grows; archival and storage reporting replace deletion as the
capacity strategy.

---

### ADR-09 — Specialist integrations behind capability contracts; vendor chosen later

**Status:** adopted-for-spec; vendor selection pending (`docs/13-open-decisions.md` U7).

**Context.** HUMAN needs PSTN calls, WhatsApp Business management, images and movies.
Akeru has WhatsApp DM, subscription images and in-client voice only (V/D).

**Decision.** Define `telephony`, `messaging`, `whatsapp-admin`, `image-generation`,
`video-production` contracts. Implement adapters (candidate: Twilio Voice; Meta WhatsApp
Cloud API direct or via a BSP; image providers; video providers). Each adapter declares
operations, async model, idempotency, costs, limits, and consent policy.

**Alternatives rejected.** *Treat WhatsApp messaging as administration* (different
permission surface and onboarding); *treat in-client voice as telephony* (no PSTN);
*single-vendor mega-adapter* (blocks alternatives, hides capability gaps).

**Consequences.** Provider choice is a configuration decision with dated evidence; the
contracts stay stable.

---

### ADR-10 — Single-node SQLite now; explicit triggers for Postgres/multi-process

**Status:** adopted-for-spec.

**Context.** Akeru is SQLite + one server process (V). Akira's workload assumptions are
10–30 bots, 2–10 humans, 4–20 rooms (A3).

**Decision.** Stay single-writer SQLite for v1, with WAL, backups and a documented
capacity model. Define triggers to migrate: sustained write contention, >50 concurrent
active tasks, multi-host need, >100k events/day, or restore time above the RTO.

**Alternatives rejected.** *Postgres from day one* (operational cost before need;
Akeru compatibility work); *multi-process sharding* (state authority complexity).

**Consequences.** Availability is bounded by one host; accepted and documented
(`docs/12-operations.md` §2).

---

### ADR-11 — Upstream is a pinned base plus a reviewed patch series

**Status:** adopted-for-spec.

**Context.** Akeru is pre-1.0 and moves fast (V). A blind merge would overwrite identity,
retention and accounting changes.

**Decision.** Maintain `upstream.yaml` with the base SHA, patch list (each mapped to
requirements/tests), and conflict notes. Rebase quarterly or on security fixes; run both
the upstream suite and Akira's suite; never auto-merge upstream into `main` without
review.

**Alternatives rejected.** *Hard fork with no upstream* (loses fixes); *follow upstream
head* (unstable); *fork the fork* (duplicate maintenance).

**Consequences.** A standing maintenance budget and a documented conflict log.

---

### ADR-12 — One connector substrate, many providers, no parity claims

**Status:** adopted-for-spec.

**Context.** Akeru's catalog has 54 entries, none installable (V); custom MCP and own
Composio work; hosted connectors do not move.

**Decision.** Connectors are: custom MCP servers, bring-your-own Composio, and
first-party adapters where needed. Every action goes through the Action Executor and the
ledger. Per-bot grants are default-deny for writes. Browser automation is a labelled
fallback.

**Alternatives rejected.** *Claim parity from a directory* (dishonest and untestable);
*implement every vendor natively first* (too slow); *depend on hosted connector tokens*
(they do not transfer).

**Consequences.** The inventory (`docs/07-integrations.md` §7) is the contract; adding a
connector is a scheduled, costed item.

---

### ADR-13 — Rooms and boards are projections over existing threads

**Status:** adopted-for-spec.

**Context.** Akeru groups are membership + boss + mentions; conversation is per bot.

**Decision.** A Room is a projection entity with membership, roles, routing rule, board
items and decisions. It references bot threads rather than owning a second transcript.

**Alternatives rejected.** *A separate room chat store* (duplicate truth);
*reuse groups unchanged* (no board, no roles, no routing rules).

**Consequences.** Room-level views are queries over tasks/threads/items; a room's
"conversation" is a merged timeline with provenance.

---

## 4. Upstream mapping and change surface

| Upstream area | Akira change | Type | Conflict risk | Test |
|---|---|---|---|---|
| `packages/contracts/orchestration/*` | new aggregates/commands/events; bot fields | additive | medium (central schema) | contract tests |
| `decider/bots.ts`, `decider/threadTurns.ts` | persona fields, task linkage, attempt creation | modify | medium-high | decider invariants |
| `provider/AkeruAgentInstructions.ts` | render persona revision | replace | high (every turn) | per-route prompt snapshot |
| `provider/Drivers/*`, `provider/Layers/*` | capability probes, skill adapters, usage metadata | extend | high (vendor protocols) | per-route E2E |
| `usage/*`, migrations | new columns, corrections | additive | medium | accounting invariants |
| `orchestration/Services/ProviderCommandReactor.ts` | dispatch on task attempt + route decision | modify | high (single dispatch point) | restart/duplicate tests |
| `archivedBotRetention.ts`, `roster.ts` | remove sweep; archive-first | modify | low code / high consequence | synthetic retention test |
| `portability` | full-team bundle | replace | medium | export/restore test |
| `apps/web` | room/board/task inspector, declaration flow | extend | medium (UI churn) | UI fixtures |
| `docs/*` | Akira docs (separate tree) | additive | none | — |

---

## 5. Rejected alternatives (global)

1. **Build a new agent platform (O4).** The debate found no evidence it reaches a usable
   product sooner; it discards working provider, memory, delegation and usage mechanics.
   Akira reuses, and defines the fallback trigger if Akeru's patch burden proves
   unmaintainable (`docs/11-backlog.md` §7).
2. **Second orchestrator beside Akeru.** Rejected by ADR-01; would create two retry
   authorities and two task truths.
3. **Provider-native task stores.** Would tie task progress to a provider, defeating the
   primary goal.
4. **Auto-downgrade on quota.** Explicitly forbidden (AK-RTE-13): it silently lowers
   quality.
5. **Automatic observer edits.** Forbidden (AK-OBS-04).
6. **Hosted multi-tenant now.** Premature; increases secret-handling and tenancy risk
   before the single-team product is proven.
7. **Chat-only task tracking.** Rejected: cannot rate, resume, cost or export.
8. **One universal prompt for all providers.** Rejected: identity drift and tool-dialect
   mismatch; the persona is composed once but the harness contract stays per-adapter.

---

## 6. Concurrency model

| Scope | Rule |
|---|---|
| Task | One active attempt (A9); new attempt requires cancel/reason |
| Thread | One provider turn at a time (Akeru); new turn while running is queued/rejected per upstream rule |
| Bot | Configurable max concurrent tasks (default proposed: 2; not HUMAN-approved) |
| Room | Max active bot-to-bot exchanges per topic window; publish gate enforces |
| Connector account | Serialized per account; rate-limit token bucket |
| Memory scope | One writer per file scope, cross-process lock (Akeru) |
| Ledger | Append-only, global source namespace/key identity and revision chain (docs/04 §5); corrections append |

Lock acquisition is keyed and leased; stale locks expire and are logged, never deleted
by hand.

---

## 7. What would invalidate this architecture

- Akeru requiring a rewrite to support per-task routing without touching its controller
  (would re-open the "thin wrapper" comparison).
- Sustained load beyond ADR-10 triggers (would force a Postgres/multi-process design).
- Vendor terms forbidding subscription transports (would remove routes, not the
  architecture).
- A requirement for real-time voice-to-voice PSTN with barge-in (would add a streaming
  media service and change the concurrency model).
- A decision to publish Akira publicly (license/trademark review and distribution
  hardening).
