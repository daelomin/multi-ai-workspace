# 05 — Interface and API contracts

**Status:** draft v0.4 · **Normative:** `spec.md` §6–§9 · **Schema detail:** `docs/04-data-model.md`

Akira extends Akeru's typed WebSocket RPC and orchestration command set. It does not add
an HTTP API for internal operations, and it does not let adapters call each other. The
contracts below are the implementation contract; field names are normative, transport
framing follows Akeru's existing RPC layer.

---

## 1. Command/query groups (client ↔ server)

All commands are idempotent by `commandId`; a duplicate `commandId` returns the original
receipt and dispatches nothing. All queries are projections and never mutate.

### 1.1 Identity and library

| Command | Purpose | Key guards |
|---|---|---|
| `template.create` / `template.publish` / `template.deprecate` | author the library | published versions immutable; content hash computed server-side |
| `persona.create-revision` | new persona revision from document or patch | schema validation; secrets scan; author recorded |
| `persona.activate` | point an instance/template at a revision | actor authorized on the target; diff recorded |
| `bot.instantiate` | create instance from template (+ overrides) | credentials checked; isolation invariants; name uniqueness in room |
| `bot.upgrade` | move instance to a newer template/persona | diff preview token required; working state untouched |
| `bot.clone` | clone as new instance, or derive template | no memory/task/credential copy |
| `goal.create` / `goal.propose-change` | goals | bot proposals cannot activate |
| `procedure.publish` / `routine.bind` | procedures and schedules | approval required before enable |

### 1.2 Tasks and routing

| Command | Purpose | Key guards |
|---|---|---|
| `task.create` | register intent + acceptance criteria | acceptance criteria non-empty for non-trivial tasks |
| `task.triage` | attach TriageRecord revision | readiness + estimate present; records policy version |
| `task.select-route` | choose RouteDecision | floor check; readiness rule; explicit override reason |
| `task.start` | dispatch attempt | one active attempt; compatibility check |
| `task.pause` / `task.resume` / `task.cancel` | lifecycle | reason; children handled |
| `task.review` | accept / request rework / reject | criteria evidence |
| `task.reopen` | reopen terminal task | authorized actor; new revision |
| `route.preview` | show options and consequences before switching | does not dispatch |
| `route.override` | per-bot/room/task/attempt override | scope + reason; visible in task |
| `checkpoint.create` | explicit checkpoint | task revision matches |
| `checkpoint.resume` | resume from checkpoint on a route | compatibility check; lost-state list |

### 1.3 Collaboration

| Command | Purpose | Key guards |
|---|---|---|
| `room.create` / `room.update` | topic, members, routing rule | membership + role validation |
| `room.post` | addressee, message, links | publish gate; dedupe; loop limits |
| `board.add` / `board.move` | durable items | item refs valid |
| `decision.record` | decision with evidence, alternatives, dissent | required fields |
| `handoff.create` | task handoff | acceptance criteria; assignee grant |
| `turn.complete-silent` | end a turn with `silent` outcome | reason code from closed set; audit record |

### 1.4 Accountability

| Command | Purpose | Key guards |
|---|---|---|
| `rating.submit` | rate a task outcome | reviewer ≠ rated bot; evidence required for extremes |
| `rating.dispute` | contest a rating | evidence; aggregate exclusion |
| `rating.resolve` | resolve a dispute | resolver distinct from rating author and disputant (or HUMAN); resolver recorded; both versions retained |
| `observer.propose` | publish a proposal | target + evidence + expected benefit |
| `observer.evaluate` | attach evaluation results | held-out/shadow evidence; cost recorded |
| `observer.activate` | apply an accepted proposal | approver ≠ observer; version bump; rollback point |
| `audit.query` | inspect decision/action trail | scope-limited |

### 1.5 Operations

| Command | Purpose | Key guards |
|---|---|---|
| `usage.query` | bot/task/room/route/account roll-ups | exclusive vs inclusive explicit |
| `export.create` | full-team bundle | async; includes allowed scopes; no plaintext secrets; audited (actor, scopes, bundle id, destination, checksum, result) |
| `export.verify` | validate a bundle | schema + checksum + restore dry-run |
| `restore.apply` | restore into an environment | empty/dedicated target only; project mapping; starts in recovery quarantine (AK-OPS-15); audited (actor, bundle id, target, checksum, result) |
| `retention.set` | archive policy (never auto-delete) | no destructive option |
| `purge.request` | permanent removal of named items | explicit ids; backup first; `destructive` scope; audit |
| `bot.delete` (upstream, guarded) | Akeru's hard-delete decider command | **not callable directly in Akira**: the decider rejects it unless it is issued through `purge.request` guards (explicit ids, verified backup, `destructive` scope, audit record). It is never reachable from a timer, retention sweep or UI path |
| `health.report` | server/provider/connector/backup status | read-only |

---

## 2. Provider adapter contract

The existing Akeru driver/adapter split is preserved. Akira adds a capability descriptor
and explicit attempt-level metadata; it does not add a new agent loop.

```ts
interface ProviderAdapter {
  readonly driverKind: DriverKind;              // codex|claudeAgent|grok|kimi|opencode|opencodeGo|customOpenai|…
  readonly instanceId: string;
  probe(): Promise<ProviderCapabilities>;       // auth + models + limits; cached with TTL
  startTurn(input: StartTurnInput): Promise<TurnHandle>;
  cancelTurn(handle: TurnHandle, reason: string): Promise<void>;
  // no resumeTurn across providers; resume is a new turn from a checkpoint
  usage(handle): AsyncIterable<UsageUpdate>;    // provider-reported or unavailable
  events(handle): AsyncIterable<ProviderRuntimeEvent>; // normalized by ingestion
}

interface StartTurnInput {
  threadId: string; attemptId: string; taskId?: string;
  route: RouteSnapshot;                          // model, options, instance, account
  messages: CanonicalMessage[];                  // from projection + memory assembly
  memory: MemoryAssembly;                        // persona, USER/MEMORY/GROUP, task scope
  tools: ToolDescriptor[];                       // grants only
  skills: SkillProjection[];                     // materialized/injected per support level
  approvalPolicy: ApprovalPolicy;
  budget: { maxTurns?: number; maxTokens?: number; deadline?: ISO };
}
```

**Contract rules.**

1. The adapter never chooses a route, retries a turn, or writes task state.
2. `probe()` reports authentication class, available models, plan meters if exposed, and
   capability flags; unknown is a value, not an error.
3. Tool calls are mapped to `ToolDescriptor` ids; an unmapped tool call fails the attempt
   with `failed_tool_contract`, never with a silent no-op.
4. The adapter must emit a terminal event for every turn (completed, failed with class,
   cancelled, interrupted) or the ingestion watchdog marks the attempt interrupted.
5. The adapter must not log prompts, completions or secrets by default; diagnostic
   logging is opt-in and redacted.

### 2.1 Capability descriptor

```ts
ProviderCapabilities {
  authClass: "subscription-oauth" | "api-key" | "local" | "none";
  transportPermission: "verified" | "assumed-for-personal-use" | "forbidden" | "unknown";
  models: { id; contextWindow; maxOutput; input: ("text"|"image"|"file")[];
            output: ("text"|"json"|"image")[]; reasoning?: {kind; levels[]};
            tools: { supported: boolean; parallel: boolean; dialect: string };
            skills: "native" | "prompt-injected" | "none"; streaming: boolean;
            usageReporting: "per-turn" | "aggregate" | "none" }[];
  limits?: { window; used; resetsAt; source: "provider-reported" };
  knownGaps: string[];                            // e.g. "custom base URL rejected"
  evidence: { checkedAt: ISO; method: "probe" | "docs"; source?: string };
}
```

---

## 3. Skill adapter contract

```ts
interface SkillAdapter {
  discover(): Promise<DiscoveredSkill[]>;         // route-native or empty with reason
  project(skill: SkillPackage): Promise<ProjectionResult>;  // copy/inject + verify resources
  canExecute(skill: SkillPackage): Promise<SupportLevel>;
  verify(skill: SkillPackage, fixture: SkillFixture): Promise<VerificationResult>;
}
```

**Rules.** `project` must report the exact path or injection mechanism; `verify` must run
the skill's validation fixture and confirm resource access; a support level without a
matching `verify` evidence record is downgraded to `*-unverified`. Projection is
idempotent and content-hashed, so re-projecting does not duplicate or mutate.

**Verification is orthogonal to mechanism.** Each per-route support entry is a
`SkillSupportEntry` (`docs/04` §2): the mechanism (native, projected, prompt-injected,
unsupported) and a `verified` flag; its `evidence` record (route, model, date, evidence)
is required when `verified` is true and absent otherwise. The
flag applies to every mechanism, including `prompt-injected`: a prompt-injected route
with no evidence record is rendered "prompt-injected (unverified)" and counts as
unverified for the floor and for `SKILLS.md`. The downgrade rule is total: no evidence
record → unverified, whatever the mechanism. `native-verified` remains the only level
that satisfies a `native-verified` floor.

---

## 4. Task/attempt interfaces

The Task Supervisor does not call adapters. It dispatches commands:

```
attempt.requested (internal)
  → task.start command → decider verifies guards → attempt.started event
  → ProviderCommandReactor resolves route and starts the turn
  → runtime events → ingestion → attempt.outcome event (completed/failed/cancelled)
  → task.review or task.ready (policy) with checkpoint after
```

**Recovery interface.** `task.recover(taskId)` is a query that returns: last checkpoint,
attempts, unresolved actions, dependencies, and the compatibility report for a candidate
route. The UI renders it; the supervisor uses it to plan the next command.

---

## 5. Connector / specialist contract

```ts
interface ConnectorAdapter {
  readonly connectorId: string; readonly version: string;
  capabilities(): ConnectorCapabilities;   // operations, read/write, scopes, limits, async
  authorize(): Promise<AuthResult>;         // OAuth/API key; never returns tokens to clients
  health(): Promise<HealthResult>;          // a real read with the saved credential
  execute(op: Operation, input: unknown, ctx: ActionContext): Promise<ActionResult>;
  reconcile(action: ActionRecord): Promise<ReconcileResult>;  // for unknown outcomes
}

interface ActionResult {
  state: "confirmed" | "failed" | "unknown";
  externalId?: string; evidence?: Link; cost?: UsageRecord; retrySafe: boolean;
}
```

**Rules.** `retrySafe` is a property of the operation semantics, not of the error. A
connector that cannot prove non-acceptance returns `unknown`; the executor never retries
`unknown` automatically. Specialist adapters implement the same interface with
`capability` names (`telephony`, `messaging`, `whatsapp-admin`, `image-generation`,
`video-production`).

---

## 6. Error taxonomy

| Class | Examples | Retry | Fallback (default) | User action |
|---|---|---|---|---|
| `quota_exhausted` | plan limit, credit balance zero | no | no | wait / switch account / switch route |
| `rate_limited` | 429, concurrency cap | yes with backoff | infrastructure-only | wait |
| `auth_missing` | not signed in, key absent | no | no | connect account |
| `auth_expired` | revoked refresh token, 401 | no | no (unless another verified account) | reconnect |
| `entitlement` | plan does not include model/feature | no | no | choose another model/plan |
| `capability_gap` | no tool calling, context too small, no skills | no | **no** | re-triage/escalate |
| `tool_contract` | unsupported tool schema, invalid call | once after repair | no | adapter fix or reroute |
| `context_overflow` | prompt exceeds window | with compaction | no | reduce scope/split task |
| `network` | DNS, TLS, timeout before acceptance | yes | infrastructure-only | retry |
| `safety_block` | approval rejected, policy block | no | no | human decision |
| `unknown` | unclassified | no | no | inspect, escalate |

The taxonomy is closed and shared by attempts, UI and routing. A provider-specific error
is mapped into one class; unmapped errors become `unknown` with the raw code retained.
Each class maps to exactly one attempt outcome (`docs/04` §4.2 mapping table). The
**Retry** and **Fallback** columns apply only when no external action of the attempt is
`dispatched` or `unknown`; otherwise the outcome is `interrupted`/`failed_unknown`, there
is no retry or fallback, and the task waits for reconciliation (AK-RTE-12, AK-TSK-11).

---

## 7. Versioning and compatibility

- **Contract version** is part of every schema (`schemaVersion`), following Akeru's
  Effect Schema pattern. Decoders accept known older shapes; unknown newer fields are
  preserved at the edge and ignored by old clients, never rejected wholesale.
- **Route keys** are stable strings (`codex/gpt-5.1-codex`, `claude/sonnet-4.7`,
  `deepseek/deepseek-chat`, `grok/grok-4.7`), versioned by the model id they embed. A
  renamed model is a new route key; old attempts keep their key.
- **Capability descriptors** and **support levels** carry `checkedAt` and are invalidated
  on model, CLI, adapter or host change.
- **RPC compatibility:** additive commands/fields are minor; removing or changing
  semantics is major and requires a migration note and a client version gate.
- **Export format** is versioned and forward-only: a bundle declares `akiraArchiveVersion`
  and the schema versions it contains; restore refuses a newer major version rather than
  guessing.

---

## 8. Security interface rules

### 8.1 Roles and scopes

| Role | May | May not |
|---|---|---|
| Operator (HUMAN) | read all, approve consequential actions, configure policy, manage accounts, request purge with the `destructive` scope | bypass AKIRA-D2; approve its own purge without naming items |
| Bot-admin (HUMAN or delegated) | author templates/personas/procedures, approve observer activation and template upgrades, grant connectors | change HUMAN goals; purge data |
| Member (HUMAN) | read rooms, create tasks, rate outcomes, join decisions | change policy, grants or templates |
| Bot | act inside its task and grants, write its own memory, use granted connectors/tools | administer templates, approve its own proposals, self-rate, change goals |
| Observer bot | read outcomes/ratings/ledgers, propose refinements | activate proposals, edit personas/goals, write external systems |
| Connector identity | execute only the operations the executor sends | initiate work, read other connectors' secrets |

Scopes are enforced server-side; UI gating is presentation only (Akeru's rule, retained).

### 8.2 Command rules

- Every credential-related command requires the `access:write`/admin scope server-side.
- Adapters receive short-lived access tokens or the key for their instance only; they
  never read the secret store directly.
- The Action Executor is the only writer to external systems; tools return intents, not
  side effects, when they target a connector.
- All inbound webhooks are verified (signature/secret), idempotent by external message id,
  and rate-limited; an unverifiable webhook is rejected and logged without payload.

---

## 9. Extension points

| Point | Contract | Who may add |
|---|---|---|
| Provider driver | `ProviderAdapter` + driver config schema | Akira maintainers; community later |
| Skill adapter | `SkillAdapter` | per route, small |
| Connector | `ConnectorAdapter` + manifest | maintainers, with review |
| Specialist capability | `ConnectorAdapter` with a capability name | maintainers |
| Observer strategy | proposal generator + evaluator interface | maintainers; strategies are versioned |
| Routing policy | declarative policy document (floors, cost weights, fallback) | operators, reviewed |
| Template | data only | bot-admin |

Each extension declares its approval classes and its cost units so the orchestrator does
not need code changes to account for it.
