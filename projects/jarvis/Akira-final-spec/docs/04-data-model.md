# 04 — Canonical data model, state machines and records

**Status:** draft v0.4 · **Normative:** `spec.md` §5–§12 · **Representative JSON:** `evals/fixtures/`.

---

## 1. Conventions

- **Identifiers** are ULIDs with a typed prefix (`bot_`, `tpl_`, `per_`, `task_`,
  `att_`, `chk_`, `act_`, `rat_`, `prp_`, `use_`, `room_`, `goal_`, `proc_`, `skl_`).
  Akeru already brands ids in `packages/contracts/src/baseSchemas.ts`; Akira adds
  prefixes for new aggregates.
- **Revisions** are monotonically increasing integers per aggregate, plus a
  **content hash** (`sha256:…`) for documents whose bytes matter (persona, procedure,
  skill package, template snapshot).
- **Timestamps** are ISO 8601 UTC with milliseconds, and every record names its actor
  (`human:<id>`, `bot:<id>`, `system`, `observer:<id>`, `connector:<id>`).
- **Enums** are closed and versioned. An unknown value received from a newer peer is
  preserved as `unknown` with the raw value, never coerced (§`docs/05-interfaces.md` §7).
- **Money** is stored as minor units plus currency; a USD estimate is a separate field
  with `estimate` provenance, never overwriting a provider-reported charge.
- **Tokens** are integers ≥ 0 or `null` with an `unavailable_reason`.
- **Append-only** records (events, attempts, actions, usage, ratings revisions, audit)
  are never updated in place; corrections are new records that supersede.

---

## 2. Identity: template, persona, instance

```ts
BotTemplate {
  id: tpl_…; name: string; role: string; description: string;
  version: integer;                    // immutable once published
  status: "draft" | "published" | "deprecated";
  persona: PersonaDocument;            // default identity
  goals: GoalSpec[];                   // proposed defaults, not active goals
  procedures: { procedureId: proc_…; version: integer }[];
  skills: { skillId: skl_…; version: string; required: boolean }[];
  toolGrants: ToolGrant[];             // capability ids + scopes
  routePolicy: RoutePolicy;
  memoryPolicy: MemoryPolicy;
  communicationPolicy: CommunicationPolicy;
  provenance: { author: actor; source: "akira-library" | "imported" | "derived"; license?: string };
  contentHash: "sha256:…"; createdAt; publishedAt?;
}

PersonaDocument {
  identity: { displayName: string; role: string; tagline?: string };
  outlook: string;                     // markdown, e.g. "skeptical, evidence-first"
  attitude: { tone: 0..100; formality: 0..100; directness: 0..100; humor: "none"|"dry"|"warm" };
  workingStyle: string[];              // how it plans, verifies, asks
  boundaries: string[];                // what it refuses or escalates
  escalationRules: string[];           // when to stop and ask
  communicationRules: string[];        // length, structure, silence norms
  language: { primary: string; allowed: string[] };
}

PersonaRevision {
  id: per_…; botTemplateId?: tpl_…; botId?: bot_…;
  revision: integer; contentHash: "sha256:…";
  document: PersonaDocument;
  composedFrom?: { templatePersonaHash?: string; overrides: PersonaPatch[] };
  status: "draft" | "active" | "superseded";
  authoredBy: actor; approvedBy?: actor; createdAt; activatedAt?;
}

BotInstance {                            // Akeru OrchestrationBot + additions
  id: bot_…; name: string; title: string; description?: string;
  avatar: BotAvatar;                     // Akeru shape/dither/image
  templateRef?: { templateId: tpl_…; version: integer };
  personaRevisionId: per_…;             // active revision (pointer)
  overrides: { persona?: PersonaPatch[]; goals?: GoalId[]; procedures?: ProcRef[];
               skills?: SkillEnablement[]; toolGrants?: ToolGrant[];
               routePolicy?: Partial<RoutePolicy>; memoryPolicy?: Partial<MemoryPolicy>;
               communicationPolicy?: Partial<CommunicationPolicy> };
  engine: BotEngine;                     // Akeru: {provider, model, options}
  runtimeMode: RuntimeMode;              // Akeru: approval mode
  routineBindings: { routineId: rt_…; procedureId: proc_…; version: integer }[];
  lifecycle: "draft" | "active" | "paused" | "archived";  // never auto-deleted
  archivedAt?: ISO; createdAt; updatedAt;
}
```

**Rules.** A template version is immutable after `published`; editing produces a new
version. An instance retains its pinned template version until an explicit upgrade.
Persona overrides are field-level patches with provenance, so the effective document is
recomputable. Credentials are **not** in these records: an instance references
`credentialRef`s resolved from the secret store (`docs/12-operations.md` §3).

### Goal

```ts
Goal {
  id: goal_…; statement: string; successCriteria: string[];
  scope: "bot" | "room" | "task" | "team"; ownerRef: bot_… | room_… | "human";
  parentGoalId?: goal_…; horizon: "task" | "week" | "quarter" | "ongoing";
  status: "proposed" | "active" | "achieved" | "abandoned" | "rejected";
  authority: "human" | "bot-proposed";   // bot-proposed never active without human approval
  evidence: Link[]; createdBy: actor; decidedBy?: actor; createdAt; updatedAt;
}
```

**Rule.** `authority: human` goals are immutable to bots; a bot changes status/statement
only through a proposal record that a HUMAN approves.

### Procedure

```ts
Procedure {
  id: proc_…; name: string; version: integer; contentHash;
  steps: { id: string; instruction: string; checkpoint: boolean;
           requiredSkills: SkillRef[]; requiredConnectors: ConnectorRef[];
           validation: string; optional?: boolean }[];
  preconditions: string[]; acceptanceChecklist: string[];
  owner: actor; provenance: "authored" | "imported" | "observer-proposed";
  status: "draft" | "approved" | "superseded";
  approvedBy?: actor; approvedAt?; supersedes?: proc_…;
}
```

A routine is `{ procedureId, version, botId, schedule, timezone, lifecycle }`, reusing
Akeru's daily/weekdays/weekly schema and its approval-before-schedule rule.

### Skill package

```ts
SkillPackage {
  id: skl_…; name: string; version: string; contentHash;
  frontmatter: { name; description; version; allowedTools?: string[]; license?: string };
  instructions: string;                 // body of SKILL.md
  resources: { path: string; sha256: string; bytes: integer }[];
  requires: { tools: string[]; connectors: ConnectorId[]; runtime: string[] };
  validation: { command?: string; fixture?: string; expected: string };
  provenance: "authored" | "vendored" | "imported"; sourceUrl?: string;
  support: { [routeKey: string]: "native-verified" | "native-unverified" |
             "projected-unverified" | "prompt-injected" | "unsupported" };
  supportEvidence: { routeKey: string; verifiedAt: ISO; model: string; evidence: Link }[];
}
```

### Room and board

```ts
Room {
  id: room_…; name: string; topic: string;
  members: { kind: "bot" | "human"; id; role: "owner" | "contributor" | "observer" }[];
  routingRule: { kind: "mention" | "lead-bot" | "round-robin" | "assigned"; leadBotId?: bot_… };
  communicationPolicy: CommunicationPolicy;
  board: BoardItemId[];                 // projection; items are separate records
  decisions: DecisionId[];
  createdAt; updatedAt;
}

BoardItem {
  id: item_…; roomId: room_…; kind: "task" | "result" | "decision" | "proposal" | "alert";
  title: string; ref: { taskId?; artifactId?; ratingId?; proposalId?; decisionId? };
  status: "open" | "in-progress" | "blocked" | "done"; ownerRef?: bot_…;
  createdAt; updatedAt;
}
```

---

## 3. Task model

```ts
Task {
  id: task_…; title: string; requester: actor;
  assignee: bot_…; roomId?: room_…; parentTaskId?: task_…; delegationId?: del_…;
  intent: string; acceptanceCriteria: AcceptanceCriterion[];
  status: TaskStatus;                   // §4.1
  priority: "low" | "normal" | "high" | "urgent";
  deadline?: ISO; dependencies: task_…[];
  triage: TriageRecord;                 // latest revision
  routeDecisionId?: rtd_…;              // currently selected route
  checkpointIds: chk_…[]; progress: { stepId: string; status: "pending"|"active"|"done"|"failed" }[];
  artifacts: art_…[]; reviewIds: rat_…[]; attemptIds: att_…[];
  cost: { exclusive: CostSummary; inclusive: CostSummary; overhead: CostSummary };
  createdAt; updatedAt; closedAt?;
}

AcceptanceCriterion { id: string; statement: string; validation: string; status: "open"|"met"|"failed"|"waived"; evidence?: Link[] }

TriageRecord {
  revision: integer; taskClass: string;
  complexity: { ambiguity: 0..5; integrations: 0..5; contextSize: 0..5;
                validationDifficulty: 0..5; expectedRework: 0..5; irreversibility: 0..5 };
  flags: ("large" | "ambiguous" | "integration-heavy" | "irreversible" | "novel")[];
  estimate: { effortHours: Range; cost: MoneyRange; confidence: 0..1; basis: string };
  readiness: ReadinessResult;           // §4.3
  proposedRoutes: RouteOption[];        // capability floor pass/fail + cost bands
  decision: { routeKey: string; reason: string; policyVersion: string };
  discovery?: { budget: { minutes: integer; tokens: integer; cost: Money }; stoppingRule: string; result?: string };
  createdAt; supersedes?: integer;
}

Attempt {
  id: att_…; taskId: task_…; number: integer; status: AttemptStatus;
  route: RouteSnapshot;                 // harness, driver, provider, model, account, options
  botId: bot_…; startedAt; endedAt?;
  outcome: { class: AttemptOutcomeClass; detail: string };   // §4.2
  checkpointBefore: chk_…; checkpointAfter?: chk_…;
  usage: { usageRecordIds: use_…[]; totalTokens: integer | null; cost: CostSummary };
  artifacts: art_…[]; providerReportedModel?: string; reroutedFrom?: string;
  approvalIds: appr_…[]; cancellation?: { by: actor; reason: string };
}

RouteDecision {
  id: rtd_…; taskId: task_…; attemptNumber?;
  taskClass: string; capabilityFloor: CapabilityFloor;
  schemaVersion: string;                // contract version (docs/05 §7)
  candidates: { routeKey: string;
                meetsFloor: boolean;     // capability only: tools, context, skill support >= requiredSkillSupport,
                                         // reliability. Never cleared by quota/auth/availability.
                available: "available"|"quota_exhausted"|"auth"|"rate_limited"|"unknown";
                availabilitySource?: string;   // e.g. provider meter, last error, timestamp
                estimatedCost: MoneyRange; costUnit: "provider-charge"|"price-table"|"subscription-equivalent";
                estimateBasis: string; support: "verified"|"assumed"|"unknown"; note?: string }[];
  chosen: { routeKey: string; reason: string; alternativesRejected: string[] };
  fallbackPolicy: "none" | "infrastructure-only" | "always-adequate";  // default infrastructure-only
  policyVersion: string; decidedBy: actor; createdAt;
}

TaskCheckpoint {
  id: chk_…; taskId: task_…; attemptId?: att_…; revision: integer;
  taskRevision: { title; acceptanceCriteria; triageRevision };
  plan: { stepId; statement; status }[];
  decisions: { decisionId; statement; evidence: Link[]; alternatives: string[] }[];
  openQuestions: { question; assignedTo: actor; blocking: boolean }[];
  artifacts: { artifactId; sha256; kind }[];
  memoryDelta: { scope: "bot"|"room"|"task"; entry: string; contentHash }[];
  skillVersions: { skillId; version }[]; procedureVersions: { procedureId; version }[];
  actionWatermark: { ledgerSeq: integer; unresolvedActionIds: act_…[] };
  nextIntent: string; lostOnResume: string[];  // e.g. "provider cache", "native tool buffer"
  workspaceCheckpointRef?: string;             // git ref when the task touched files
  createdBy: actor; createdAt;
}
```

---

## 4. State machines

### 4.1 Task

| From | Event | To | Guard |
|---|---|---|---|
| proposed | accept | triaged | acceptance criteria exist |
| triaged | route selected | ready | route meets floor; if readiness is `not-ready`, the route must not be specification-led/below-floor (an advanced route that meets the floor may proceed with the risks attached) |
| ready | attempt dispatched (`task.start`) | running | route meets floor **and** is available; compatibility check passed |
| running | needs input | awaiting_input | open question created |
| running | dependency/external block | blocked | blocker recorded with owner |
| running | pause (human or policy) | paused | reason |
| awaiting_input | question answered | ready | answer recorded; checkpoint refreshed; route check re-run |
| blocked | blocker resolved | ready | blocker reference closed; unresolved-action check passed; route check re-run |
| paused | explicit resume (`task.resume`) | ready | reason recorded; quota-paused tasks need an available adequate route or an operator choice; new checkpoint created |
| running | attempt ended `completed` | review | artifacts + acceptance evidence |
| running | attempt ended `failed_rate_limit`/`failed_network` (no dispatched external action) | ready | infrastructure fallback permitted by policy and the alternate route meets the floor; otherwise `blocked` |
| running | attempt ended `failed_quota` | paused | quota reason and recommended action; no fallback |
| running | attempt ended `failed_capability`/`failed_tool_contract`/`failed_context_overflow`/`failed_safety_block` | triaged | re-triage required; no automatic fallback |
| running | attempt ended `failed_auth` | blocked | repair action: reconnect or switch account |
| running | attempt ended `failed_unknown`/`interrupted` | blocked or awaiting_input | resumable checkpoint written; any `dispatched`/`unknown` action reconciled first |
| running | attempt ended `cancelled` | ready, paused or cancelled | as chosen by the canceller; reason recorded |
| review | accepted | done | all criteria met or waived with reason |
| review | rework requested | ready | new attempt planned, reason recorded |
| review | rejected | failed | reason; reopenable |
| any non-terminal | cancel | cancelled | reason; children cancelled |
| done/failed/cancelled | reopen | triaged | actor authorized; new revision |

**Invariants:** one active attempt; no `done` without acceptance evidence; no transition
from `blocked` to `running` without resolving the blocker reference; every transition is
an event with actor and timestamp.

### 4.2 Attempt outcomes

`completed` · `failed_capability` · `failed_tool_contract` · `failed_context_overflow` ·
`failed_auth` · `failed_quota` · `failed_rate_limit` · `failed_network` ·
`failed_safety_block` · `failed_unknown` · `cancelled` · `interrupted` (restart).

Mapping to route policy: only `failed_rate_limit` and `failed_network` are eligible for
automatic infrastructure fallback by default. `failed_quota` pauses and asks. Capability,
tool-contract and safety failures never fall back automatically; they re-triage.

**External-effect guard.** `failed_network` is reserved for failures with no dispatched
external action (DNS/TLS/timeout before acceptance, or a transport failure before any tool
request left). If the attempt dispatched any external action (ledger state `dispatched` or
`unknown`), the outcome is `interrupted` or `failed_unknown`, regardless of the transport
symptom (e.g. a 5xx mid-stream after a tool request was sent), and it is ineligible for
automatic fallback until the action is reconciled (§4.4).

**Availability is not adequacy.** A quota-exhausted, auth-blocked or rate-limited route is
recorded `meetsFloor: true` with `available` set accordingly; the task pauses (or falls
back only for infrastructure classes). It is never escalated or re-triaged because of
availability alone.

### 4.3 Readiness

```
ReadinessResult {
  outcome: "ready" | "ready-with-risks" | "not-ready";
  criteria: {                       // nine named criteria; every one is an EvidencedCriterion
    intendedOutcome, scopeAndExclusions, dependencies, interfaces,
    constraints, boundedSubtasks, acceptanceExamples, independentValidation,
    unknownsResolved: EvidencedCriterion
  };
  risks: { statement; mitigation; acceptedBy? }[];
}
EvidencedCriterion { outcome: "pass"|"fail"|"partial"; evidence: Link[]; note?: string }
```

A `pass` with an empty `evidence` list is invalid and fails T-10. AK-TRG-06's list is the
nine criteria above ("dependencies" and "interfaces" are separate criteria).

A `not-ready` result blocks only the *specification-led downgrade* path (cheap implementer
from the document). It does not block an advanced model from doing the work.

### 4.4 Action ledger

| State | Meaning | Allowed next |
|---|---|---|
| intent | action decided, not sent | dispatched, cancelled |
| dispatched | request possibly reached the provider | confirmed, failed, unknown |
| confirmed | provider acknowledged with an id | (terminal) |
| failed | provider rejected; no effect | intent (new action id) |
| unknown | acceptance not established | confirmed, failed (after reconciliation) |

**Rule:** `unknown → failed` requires evidence (read-back, error proving no acceptance),
never a timeout alone. A new action with the same logical intent reuses the idempotency
key only if the provider semantics permit it; otherwise it is a new key and the ledger
records the link.

### 4.5 Observer proposal

`draft → evaluated → awaiting_review → accepted | rejected | superseded`, and
`accepted → active → superseded` via an activation record. `rejected` retains the
evaluation and the reason. Activation is a separate command with an approver.

### 4.6 Rating

`submitted → (disputed → resolved) → superseded`. Each submission appends a revision;
the current rating is the latest non-superseded revision. A dispute record references
the rating revision and carries the disputant, evidence and resolution.

### 4.7 Bot lifecycle

`draft → active ⇄ paused → archived`. `archived` is terminal until `restore`.
`purge` (explicit, audited, backup-first) is the only destructive transition and requires
an actor with the `destructive` scope. There is no timer-based transition.

---

## 5. Accounting records

```ts
UsageRecord {
  id: use_…; idempotencyKey: string;      // unique per owner + source
  owner: { kind: "bot"|"task"|"room"|"observer"|"connector"; id };
  attribution: { botId?; taskId?; attemptId?; roomId?; threadId?; turnId?;
                 parentTaskId?; parentUsageId? };
  route: { harness; driver; provider; model; instanceId; accountLabel? };
  schemaVersion: string;
  category: "turn"|"tool"|"delegation"|"routine"|"review"|"coordination"|"observer"|"media"|"other";
                // overhead = review|coordination|observer; delivery = all others (docs/09 §3)
  measurement: "provider-reported"|"estimated"|"subscription-equivalent"|"unknown";
  tokens?: { uncachedInput: integer|null; cachedInput: integer|null;
             cacheCreation: integer|null; output: integer|null;
             reasoning?: integer|null; unavailableReason?: string };
  units?: { kind: "call"|"minute"|"message"|"image"|"video-second"|"job"; count: number };
  cost?: { amountMinor: integer; currency: string; provenance: CostProvenance;
           priceTableVersion?: string; providerChargeId?: string };
  state: "reserved"|"reported"|"corrected"|"released"|"unavailable";
  createdAt; settledAt?; supersedes?: use_…; notes?: string;
}
```

**Cost summary** (derived, never stored as truth):

```ts
CostSummary { schemaVersion: string;
              subtotals: { currency: string;
                           providerReported: Money | null;
                           priceTableEstimate: Money | null;
                           subscriptionEquivalent: Money | null }[];   // one row per currency; never merged
              combinedEstimate?: { amount: Money; currency: string; label: "combined economic estimate, not spend" };
              coverage: { reported: integer; estimated: integer; subscription: integer; unknown: integer };
              byCategory: Record<category, { amount: Money|null; provenance: CostProvenance|"mixed" }> }
```

The subtotals are authoritative; `combinedEstimate` is optional, labelled, and must be
shown with its subtotals. `coverage` counts cost-bearing records per bucket and the
buckets sum to the cost-bearing records. A correction record is a superseding effective
snapshot of all token and cost fields now known; queries take the effective revision once
per logical usage record (`docs/09-accounting.md` §7).

**Non-token costs** use the same table with `units`, so telephony minutes, template
messages, image renders and sandbox time are attributed without pretending to be tokens.

---

## 6. Storage mapping

| Record | Storage | Notes |
|---|---|---|
| BotTemplate, PersonaRevision, BotInstance, Goal, Procedure, SkillPackage, Room | events + projections, `projection_*` tables | new tables; content-addressed documents on disk for skill bundles/persona body if large |
| Task, Attempt, TriageRecord, RouteDecision, TaskCheckpoint | events + projections | checkpoints also written as JSON files for portability; hash recorded |
| ActionRecord | append-only table + projection for open actions | index on `(task_id, state)`, unique `(connector, idempotency_key)` |
| Rating, Dispute, ObserverProposal | events + projections | revisions append |
| UsageRecord | append-only table | extend `akeru_bot_usage_entries` or a new table keyed by `idempotencyKey`; see §7 |
| Artifact | files + metadata table | content hash, kind, producer, license, retention class |
| AuditRecord | append-only table | actor, action, target, before/after hash, request id |

### 7. Migration from Akeru tables

- `akeru_bot_usage_entries` gains nullable columns: `task_id`, `attempt_id`, `room_id`,
  `parent_entry_id`, `instance_id`, `account_label`, `measurement`, `currency`,
  `amount_minor`, `price_table_version`, `units_kind`, `units_count`, `supersedes_id`.
  Existing rows remain valid with nulls, preserving the `UNIQUE(bot_id, source_key)`
  semantics for old writers. Legacy `category` values are mapped by the deterministic
  table in `docs/09-accounting.md` §3 (delegated→delegation, reflector→observer,
  extraction/recall→other, unknown→other with the original value kept in `notes`); a
  migration test asserts each pre-migration row keeps one valid category and is counted
  once in exclusive totals.
- `bots` projection gains `template_ref`, `persona_revision_id`, `lifecycle`,
  `policy_json`; a backfill creates a default persona revision from name/description and
  the saved tone, marked `imported` (not `authored`).
- `groups` gain room fields (`topic`, `routing_rule`, `communication_policy`);
  membership roles map boss→lead/owner and specialist→contributor.
- A new `task` projection links `thread_id`/`turn_id`; legacy turns get no synthetic task
  (backfill would invent acceptance criteria — forbidden).

---

## 8. Invariants (must be enforced by the decider)

1. An attempt references a task and a route decision for the same task.
2. `checkpointBefore.createdAt ≤ attempt.startedAt`; `checkpointAfter` exists for every
   attempt that produced artifacts.
3. A task cannot be `done` while any acceptance criterion is `open` or `failed` (a
   waived criterion needs an actor and a reason).
4. An action in `unknown` blocks dependent actions until reconciled.
5. A usage record's parent chain is acyclic; a child has exactly one parent.
6. A rating's reviewer is not the rated bot; the rated task is `review`/`done`.
7. A proposal cannot be `accepted` without an `evaluated` result and an approver distinct
   from the observer. A rating dispute is resolved by an actor distinct from both the
   rating's author and the disputant (or a HUMAN); the resolver is recorded.
8. A persona revision cannot be `active` for two instances at once if it is instance-scoped;
   template-scoped revisions are shared read-only.
9. Archived bots cannot receive new tasks; restoring does not resume routines
   (Akeru behaviour, retained).
10. Template versions and persona revisions are immutable once referenced by an instance;
    edits create new records.

---

## 9. Representative records

Full JSON examples: `evals/fixtures/` (task, checkpoint, route-decision, rating,
observer-proposal, usage-record, action-record, skill-package). They are deliberately
small but complete; tests validate them against the schemas and use them as golden
fixtures for export/restore.

---

## 10. Open modelling questions

- Whether a task may have multiple assignees (assumption A9 says no; parallel work uses
  child tasks).
- Whether `TriageRecord` is an aggregate of the task or a separate reviewable record
  (current: attached to the task, immutable revisions).
- Whether room decisions need their own aggregate or can be board items with a
  `Decision` payload (current: separate `Decision` record referenced by board items).
- Exact retention classes for artifacts and logs (pending HUMAN; default keep).
