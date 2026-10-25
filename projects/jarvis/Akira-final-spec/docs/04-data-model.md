# 04 — Canonical data model, state machines and records

**Status:** Final specification v0.7 · **Normative:** `spec.md` §5–§12 · **Representative JSON:** `evals/fixtures/`.

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
- **Summary/proposal Money** has one shape: `Money { amountMinor: integer; currency: string }`
  (minor units, e.g. cents). `MoneyRange { lowMinor: integer; highMinor: integer;
  currency: string }`. Inside a structure that already carries a `currency` (a
  `CostSummary` subtotal row), fields are named `…Minor` and share that currency. Decimals
  are a display format only, never stored. A USD estimate is a separate field with
  `estimate` provenance, never overwriting a provider-reported charge.
- **ExactMoney** is the per-record and price-calculation shape:
  `{ coefficient: string; scale: integer; currency: string }`, meaning the signed base-10
  integer coefficient × 10^(-scale) major currency units. `scale >= 0`; the coefficient
  is a canonical integer string (no leading zeros except `0`), handled with arbitrary
  precision, never binary floating point. USD 0.004 is `{coefficient: "4000", scale: 6,
  currency: "USD"}`. Products retain all source digits; scale may exceed six when needed.
  A reported USD 1.84 remains exactly 1.84; extra trailing zeros imply no new measurement
  precision. Keep the reported amount/scale and price-table inputs as provenance.
  Aggregate effective records exactly, aligning scales, then round half to even to the
  currency's minor units once per subtotal/display boundary, never per record.
  The price table declares the currency minor-unit exponent. `Money`/`…Minor` summaries
  and proposal estimates are boundary values, never inputs for re-summing usage records.
  Thus 100 × USD 0.004 = USD 0.40. Combined display estimates sum displayed provenance
  subtotals; any category/display rounding residual is labelled, never written as usage.
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

PersonaPatch {
  path: string;                        // RFC 6901 pointer to a PersonaDocument field
  op: "set" | "remove"; value?: unknown; // value required for set, absent for remove
  basePersonaHash: string;             // pinned base document before overrides
  provenance: "template" | "instance" | "human";
  authoredBy: actor; revision: integer; createdAt: ISO;
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
recomputable. Start from the pinned template/base document, apply template-layer
patches, then instance patches, then explicit HUMAN patches, in increasing revision
order within each layer. Revisions are unique per
layer in a composition; duplicate revisions or mismatched base hashes reject, never
sort by timestamp. `set` replaces a field or adds an optional field; `remove` removes
only optional fields. Arrays are replaced whole; array-index/root patches, unknown
paths, invalid types and removal of required fields reject. HUMAN provenance requires
a HUMAN actor; other provenance cannot change HUMAN-owned fields. Retain every patch
and each field's winning provenance, validate and hash the effective document. A template
upgrade requires explicit rebase/diff against the new base hash, never silent replay.
Credentials are **not** in these records: an instance references
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
  support: { [routeKey: string]: SkillSupportEntry };
}

SkillSupportEntry {
  mechanism: "native" | "projected" | "prompt-injected" | "unsupported";
  verified: boolean;                    // orthogonal to mechanism, incl. prompt-injected
  evidence?: { verifiedAt: ISO; model: string; evidence: Link };  // required iff verified
  note?: string;                        // e.g. "no injection test run yet"
}
```

`SupportLevel = "native-verified" | "native-unverified" | "projected-verified" |
"projected-unverified" | "prompt-injected" | "unsupported"`.

The support level (`native-verified`, `native-unverified`, `projected-verified`,
`projected-unverified`, `prompt-injected`, `unsupported`; AK-SKL-04) is derived from
`mechanism` and `verified`; a `prompt-injected` entry keeps that level whether or not
`verified` is set and renders "(unverified)" when it is not. Only `native-verified`
satisfies a native floor.
`unsupported` always has `verified: false`.
`evidence` is required when `verified` is true and absent otherwise: an unverified entry
never carries a fabricated verification timestamp.

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
  revision: integer;                    // monotonic; +1 on any change to the fields hashed below
  contentHash: string;                  // sha256 over the task definition: title, intent,
                                        // assignee, acceptanceCriteria (statement + validation),
                                        // dependencies, priority, deadline
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
  route: RouteSnapshot;                 // harness, driver, provider, model, account, authClass, options
  botId: bot_…; startedAt; endedAt?;
  outcome: { class: AttemptOutcomeClass; detail: string };   // §4.2
  checkpointBefore: chk_…; checkpointAfter?: chk_…;
  usage: { usageRecordIds: use_…[]; totalTokens: integer | null; cost: CostSummary };
  artifacts: art_…[]; providerReportedModel?: string; reroutedFrom?: string;
  approvalIds: appr_…[]; cancellation?: { by: actor; reason: string };
}

RouteSnapshot {
  harness: string; driver: string; provider: string; model: string;
  instanceId: string; accountLabel?: string;
  authClass: "subscription-oauth"|"api-key"|"local"|"none";
  options: object; provenance: "verified"|"assumed";
  transportPermission: "verified"|"assumed-for-personal-use"|"forbidden"|"unknown";
}
CapabilityFloor {
  requiredTools: string[]; minimumContext: integer; requiredReliability: string;
  requiredSkills: skl_…[];
  requiredSkillSupport: { allowedMechanisms: ("native"|"projected"|"prompt-injected")[];
                          requireVerified: boolean };
}
RouteOption = RouteDecision.candidates[number];  // same shape in TriageRecord.proposedRoutes

RouteDecision {
  id: rtd_…; taskId: task_…; attemptNumber?;
  roleBasis: string;                    // policy/default/explicit override, with reason
  taskClass: string; capabilityFloor: CapabilityFloor;       // includes requiredSkills: skl_…[]
  schemaVersion: string;                // contract version (docs/05 §7)
  candidates: { routeKey: string;
                authClass: "subscription-oauth"|"api-key"|"local"|"none";   // docs/05 §2.1
                options: object; provenance: "verified"|"assumed";
                transportPermission: "verified"|"assumed-for-personal-use"|"forbidden"|"unknown";
                meetsFloor: boolean;     // capability only: tools, context, skill predicate below,
                                         // reliability. Never cleared by quota/auth/availability.
                skillSupport: { skillId: skl_…; mechanism; verified: boolean; evidence? }[];
                                         // the SkillSupportEntry (§2) per required skill: the input
                                         // of the skill part of the floor check
                available: "available"|"quota_exhausted"|"auth"|"rate_limited"|"unknown";
                availabilitySource?: string;   // e.g. provider meter, last error, timestamp
                estimatedCost: MoneyRange; costUnit: "provider-charge"|"price-table"|"subscription-equivalent";
                estimateBasis: string; note?: string;
                role: "specification-led" | "advanced" }[];   // see §4.1 and §4.3
  chosen: { routeKey: string; reason: string; alternativesRejected: string[] };
  fallbackPolicy: "none" | "infrastructure-only" | "always-adequate";  // default infrastructure-only
  policyVersion: string; decidedBy: actor; createdAt;
}

TaskCheckpoint {
  id: chk_…; taskId: task_…; attemptId?: att_…; revision: integer;
  taskRevision: { taskId: task_…; revision: integer; contentHash: string; triageRevision: integer };
                                        // resume/reconcile compare revision + contentHash with the
                                        // live Task and surface any mismatch before dispatch
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

**Skill-floor predicate.** Every required skill needs an entry with a mechanism in
`allowedMechanisms`, and valid current verification evidence when `requireVerified` is
true. `unsupported` never passes; labels have no total ordering. A native floor is
`{allowedMechanisms:["native"], requireVerified:true}`; a verified projected floor uses
`["projected"]`; T3 native-or-projected uses `["native","projected"]` and verification.
Projected-verified passes the projected floor and fails the native floor. Tools, context
and reliability remain separate checks. Permission is separate from `meetsFloor`:
`forbidden`/`unknown` reject selection/dispatch even when capable. Copy permission from
the descriptor to candidates and RouteSnapshot; revalidate at start/resume and preserve
the attempt's snapshot.

### 4.1 Task

| From | Event | To | Guard |
|---|---|---|---|
| proposed | accept | triaged | acceptance criteria exist |
| triaged | route selected | ready | permission allowed; route meets floor (the floor check alone rejects below-floor routes, for every readiness outcome); if readiness is `not-ready`, the chosen candidate's `role` must not be `specification-led` (an `advanced` route that meets the floor may proceed with the risks attached) |
| ready | attempt dispatched (`task.start`) | running | route meets floor **and** is available; permission allowed; compatibility and unresolved-action checks passed |
| running | needs input | awaiting_input | open question created |
| running | dependency/external block | blocked | blocker recorded with owner |
| running | pause (human or policy) | paused | reason |
| awaiting_input | question answered | ready | answer recorded; checkpoint refreshed; route check re-run |
| blocked | blocker resolved | ready | blocker reference closed; unresolved-action check passed; route check re-run |
| paused | explicit resume (`task.resume`) | ready | reason recorded; quota-paused tasks need an available adequate route or an operator choice; new checkpoint created |
| running | attempt ended `completed` | review | artifacts + acceptance evidence |
| running | attempt ended `failed_rate_limit`/`failed_network` (no `dispatched`, `unknown` or unresolved dead-attempt `intent` action) | ready | infrastructure fallback permitted by policy and the alternate route meets the floor; otherwise `blocked` |
| running | attempt ended `failed_quota` | paused by default; ready only under explicit `always-adequate` | quota reason/options; recorded policy basis, adequate available permitted alternate and all unresolved-action guards required |
| running | attempt ended `failed_capability`/`failed_tool_contract`/`failed_context_overflow`/`failed_safety_block` | triaged | re-triage required; no automatic fallback |
| running | attempt ended `failed_auth` | blocked | repair action: reconnect or switch account |
| running | attempt ended `failed_unknown`/`interrupted` | blocked or awaiting_input | resumable checkpoint written; any `dispatched`/`unknown` action reconciled first |
| running | attempt ended `cancelled` | ready, paused or cancelled | as chosen by the canceller; reason recorded; to `ready`, any `dispatched`/`unknown` action is reconciled first, otherwise the task goes to `blocked` or `paused` |
| review | accepted | done | all criteria met or waived with reason |
| review | rework requested | ready | new attempt planned, reason recorded |
| review | rejected | failed | reason; reopenable |
| any non-terminal | cancel | cancelled | reason; children cancelled |
| done/failed/cancelled | reopen | triaged | actor authorized; new revision |

A new attempt (`task.start`) on a task with any `dispatched`, `unknown`, or unresolved
`intent` action whose attempt is no longer live is
rejected until that action is reconciled, whatever edge led to `ready`.

**Invariants:** one active attempt; no `done` without acceptance evidence; no transition
from `blocked` to `running` without resolving the blocker reference; every transition is
an event with actor and timestamp.

### 4.2 Attempt outcomes

`completed` · `failed_capability` · `failed_tool_contract` · `failed_context_overflow` ·
`failed_auth` · `failed_quota` · `failed_rate_limit` · `failed_network` ·
`failed_safety_block` · `failed_unknown` · `cancelled` · `interrupted` (restart).

Mapping to route policy: only `failed_rate_limit` and `failed_network` are eligible for
automatic infrastructure fallback by default, and only when no external action is
`dispatched`, `unknown` or unresolved dead-attempt `intent` (a 429 or timeout after a send is `interrupted`/`failed_unknown`). `failed_quota` pauses and asks unless the explicit quota policy below applies. Capability,
tool-contract and safety failures never fall back automatically; they re-triage.

**Fallback policy procedure.** `none`: no automatic fallback. `infrastructure-only`
(default): only failed_rate_limit/failed_network, with backoff as applicable.
`always-adequate`: those classes plus failed_quota, the explicit quota exception, not
permission for every failure. Auth/entitlement block for operator repair;
capability/tool-contract/context/safety re-triage; unknown/interrupted wait for recovery;
completed/cancelled never trigger fallback. Every policy preserves floor, readiness,
permission, availability, compatibility, approvals, pause/quarantine and unresolved-action
guards (`dispatched`, `unknown`, dead-attempt `intent`). No eligible alternate means
quota stays paused with options. Account takeover follows the same procedure, never an
adapter retry. Each fallback records policyVersion/basis, a visible RouteDecision and a
new attempt; the old outcome is retained.

**Error class → attempt outcome.** The error taxonomy (`docs/05` §6) and the outcome set
are two closed vocabularies related by this single mapping; fault-matrix expectations and
runbooks use the **outcome** names.

| Error class (`docs/05` §6) | Attempt outcome |
|---|---|
| `quota_exhausted` | `failed_quota` |
| `rate_limited` | `failed_rate_limit` |
| `auth_missing`, `auth_expired` | `failed_auth` |
| `entitlement` | `failed_auth` (repair: choose another model/plan; detail names the entitlement) |
| `capability_gap` | `failed_capability` |
| `tool_contract` | `failed_tool_contract` |
| `context_overflow` | `failed_context_overflow` |
| `network` | `failed_network` |
| `safety_block` | `failed_safety_block` |
| `unknown` | `failed_unknown` |
| any class, when an action was `dispatched`/`unknown`/`intent`-with-dead-attempt | `interrupted` when the session or attempt ended without a provider terminal event (severed stream, restart, kill); `failed_unknown` when the provider returned a terminal error but acceptance of the action is not established (external-effect guard below) |

A restart that finds a running attempt with no live session records `interrupted`
(AK-TSK-14), never a bare "failed". A contract test asserts that every fault-matrix row
whose result kind is `attempt outcome` is a member of the closed set above; rows of other
result kinds (action state, delivery state, watchdog, invariant, retention, quarantine) are
asserted against their own component, not against this set (`docs/10` §3).

**External-effect guard.** `failed_network` is reserved for failures with no dispatched
external action (DNS/TLS/timeout before acceptance, or a transport failure before any tool
request left). If the attempt dispatched any external action (ledger state `dispatched` or
`unknown`, or `intent` with a dead attempt), the outcome is `interrupted` if there is no provider terminal event, or `failed_unknown`
if a terminal error leaves acceptance unestablished, regardless of the transport
symptom (e.g. a 5xx mid-stream after a tool request was sent), and it is ineligible for
automatic fallback until the action is reconciled (§4.4).

**Availability is not adequacy.** A quota-exhausted, auth-blocked or rate-limited route is
recorded `meetsFloor: true` with `available` set accordingly; the task pauses (or falls
back only for infrastructure classes by default, or explicit quota policy). It is never escalated or re-triaged because of
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

**Route role (decision procedure).** Every candidate carries `role: "specification-led" |
"advanced"`, evaluated by the `triaged → ready` guard. The role is a route-policy
attribute (data, versioned with the policy, recorded on the candidate at decision time).
Proposed default, not HUMAN-approved: when more than one candidate meets the floor, the
uniquely cheapest one *within a comparable group of at least two floor-meeting
candidates with the same auth class, cost unit and currency* is `specification-led` and
every other floor-meeting candidate is `advanced`; a sole floor-meeting candidate in a group is `advanced`. The cheapest candidate must
have `highMinor < lowMinor` of every peer to be uniquely cheapest. Candidates in different auth classes or cost units are not ranked against each
other unless the policy enables the labelled routing comparison unit (U16, default off), in
which case the operator or policy sets the role. Two `MoneyRange`s are ordered only when
they do not overlap (`highMinor` of one < `lowMinor` of the other); overlapping ranges are
unordered; absent a uniquely cheapest candidate all candidates stay `advanced` by default, and the route policy or
operator may set the role per route key. `not-ready` rejects candidates
whose role is `specification-led`; a below-floor candidate is rejected by the floor check
alone, whatever the readiness outcome (its `role` comes from the route policy and is
irrelevant to the guard). `ready` and `ready-with-risks` accept either role.

### 4.4 Action ledger

| State | Meaning | Allowed next |
|---|---|---|
| intent | action decided, connector not yet invoked under the write-ahead contract | dispatched, cancelled; unknown during dead-attempt recovery if never-sent proof is unavailable |
| dispatched | durably recorded **before** the connector call; request possibly reached the provider | confirmed, failed, unknown |
| confirmed | provider acknowledged with an id | (terminal) |
| failed | provider rejected; no effect | intent (new action id) |
| unknown | acceptance not established | confirmed, failed (after reconciliation) |

**Write-ahead rule (AK-TSK-10).** The executor persists `intent`, then durably appends
`dispatched`, and only then invokes the connector. `intent → cancelled` is allowed only
before that append. An `intent` action whose attempt is no longer live (crash, kill,
restart) is treated as possibly sent: startup recovery verifies it by reconciliation and
never resends it, unless the executor can prove the connector call was never started. It
blocks new attempts and dependent actions exactly as `dispatched`/`unknown` do. Recovery
appends `unknown` before reconciling a possibly sent dead-attempt `intent`; proof the call
never started permits `cancelled` instead. A read-back confirmation then follows the
normal `unknown → confirmed` evidence path; no recovery transition invokes the connector
write. A failed read-back alone does not prove non-acceptance.

```ts
ActionRecord {
  schemaVersion: string; id: act_…; taskId: task_…; attemptId: att_…;
  connector: string; credentialRef: string; operation: string; requestHash: string; target: string;
  logicalActionKey: string;             // stable task + intent across retries
  providerIdempotencyKey?: string | null; // only if provider supports it
  linkedActionId?: act_… | null;        // predecessor on a new retry action
  state: "intent"|"dispatched"|"confirmed"|"failed"|"unknown"|"cancelled";
  externalId?: string | null; reconciliation?: object;
  blockedDependents: string[]; createdBy: actor; createdAt; updatedAt;
}
```

State events append under an action id; ActionRecord is their current projection.
Allow only one unresolved action per `(taskId, logicalActionKey)`. A confirmed logical
intent cannot dispatch again; changed business intent needs a new logical key. After
evidence-backed failure (or proven-never-sent cancellation), an authorized retry gets a
new action id, `linkedActionId`, the same logical key and request hash. Changed payload
requires new intent/approval. Provider-key scope is `(connector, credentialRef,
providerIdempotencyKey)` (reference only, never secret). A durable call-key registry maps
that tuple to logical key + hash; multiple events/linked retries may reference it, so it
is not a unique index on every append-only row. Reuse requires documented provider
semantics/validity and the same hash; colliding logical keys/hashes reject. If reuse is
forbidden, a linked retry gets a fresh provider key but the same logical key. Unsupported
providers omit/null the provider key; no dedupe guarantee is invented. No key authorizes
retry while an action is unresolved.

**Rule:** `unknown → failed` requires evidence (read-back, error proving no acceptance),
never a timeout alone. Linked retries follow the separate logical/provider-key rules above;
repeated not-found reads or elapsed time alone never authorize retry.

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
  id: use_…; idempotencyKey: string;      // globally namespaced logical usage identity
  source: { namespace: string; key: string }; // immutable source, independent of owner
  revision: integer;                    // starts at 1; unique per logical usage key
  owner: { kind: "bot"|"task"|"room"|"observer"|"connector"; id };
  attribution: { botId?; taskId?; attemptId?; roomId?; threadId?; turnId?;
                 parentTaskId?; parentUsageId? };
  route: RouteSnapshot;                 // includes authClass, options and provenance
  schemaVersion: string;
  category: "turn"|"tool"|"delegation"|"routine"|"review"|"coordination"|"observer"|"media"|"other";
                // overhead = review|coordination|observer; delivery = all others (docs/09 §3)
  measurement: "provider-reported"|"estimated"|"subscription-equivalent"|"unknown";
  tokens?: { uncachedInput: integer|null; cachedInput: integer|null;
             cacheCreation: integer|null; output: integer|null;
             reasoning?: integer|null; unavailableReason?: string };
  units?: { kind: "call"|"minute"|"message"|"image"|"video-second"|"job"|"sandbox-hour"|"host-month"; count: number };
  cost?: ExactMoney & { provenance: CostProvenance;   // §1 exact fixed point
           priceTableVersion?: string; providerChargeId?: string };
  state: "reserved"|"reported"|"corrected"|"released"|"unavailable";
  createdAt; settledAt?; supersedes?: use_…; notes?: string;
}
```

**Cost summary** (derived, never stored as truth):

```ts
CostSubtotal { currency: string; providerReportedMinor: integer|null;
               priceTableEstimateMinor: integer|null; subscriptionEquivalentMinor: integer|null }
UsageCoverage { reported: integer; estimated: integer; subscription: integer; unknown: integer }
CostBreakdown { subtotals: CostSubtotal[]; coverage: UsageCoverage }
CostSummary { schemaVersion: string;
              subtotals: CostSubtotal[]; // one row per currency; never merged
              combinedEstimate?: Money & { label: "combined economic estimate, not spend" };
              coverage: UsageCoverage;
              byCategory?: Partial<Record<category, CostBreakdown>>;
              failedAttempts?: CostBreakdown } // required in task drill-down only
```

`byCategory` is present in the cost-summary query response (task drill-down) and may be
omitted in summaries embedded in projections such as `Task.cost`; when present it is
consistent per currency/provenance, with display rounding residuals labelled (§1).
`failedAttempts` is the required query-only delivery sub-line in docs/09 §8; embedded
Task.cost summaries may omit it, as they may omit byCategory.

The subtotals are authoritative; `combinedEstimate` is optional, labelled, and must be
shown with its subtotals. `coverage` counts cost-bearing records per bucket and the
buckets sum to the cost-bearing records. A correction record is a superseding effective
snapshot of all token and cost fields now known; queries take the effective revision once
per logical usage record (`docs/09-accounting.md` §7).

**Usage identity/effective revisions.** `idempotencyKey` is the canonical JSON encoding
of `[source.namespace, source.key]`, without an owner dimension. Namespace is a persisted
globally unique source-origin id shared by copies/exports of that source; independent
origins get distinct ids. The key names one billable event/reservation, not settlement
delivery. Its mapping survives migration/export for every owner kind; ownership or
attribution correction preserves it. Initial revision is 1; settlement/correction/release
increments revision and `supersedes` the previous record id with a full snapshot under
the same key. Enforce unique `(idempotencyKey, revision)` and one successor per record;
duplicate receipts return the existing revision and conflicting successors reject for
reconciliation. Select the latest non-superseded revision once: reported/corrected count;
reserved/unavailable count under their measurement and unknown labels; released counts
neither tokens, cost nor coverage. Unknown money stays null, never zero. Superseded
revisions are audit-only.

**Non-token costs** use the same table with `units`, so telephony minutes, template
messages, image renders and sandbox time are attributed without pretending to be tokens.

---

## 6. Storage mapping

| Record | Storage | Notes |
|---|---|---|
| BotTemplate, PersonaRevision, BotInstance, Goal, Procedure, SkillPackage, Room | events + projections, `projection_*` tables | new tables; content-addressed documents on disk for skill bundles/persona body if large |
| Task, Attempt, TriageRecord, RouteDecision, TaskCheckpoint | events + projections | checkpoints also written as JSON files for portability; hash recorded |
| ActionRecord | append-only table + projection for open actions | index on `(task_id, state)`; logical-action guard and provider call-key registry per §4.4, not event-row provider-key uniqueness |
| Rating, Dispute, ObserverProposal | events + projections | revisions append |
| UsageRecord | append-only table | extend `akeru_bot_usage_entries` or a new table unique on `(idempotencyKey, revision)` plus chain guards (§5); see §7 |
| Artifact | files + metadata table | content hash, kind, producer, license, retention class |
| AuditRecord | append-only table | actor, action, target, before/after hash, request id |

### 7. Migration from Akeru tables

- `akeru_bot_usage_entries` gains nullable columns: `task_id`, `attempt_id`, `room_id`,
  `parent_entry_id`, `instance_id`, `account_label`, `measurement`, `currency`,
  `cost_coefficient`, `cost_scale`, `price_table_version`, `units_kind`, `units_count`, `supersedes_id`.
  Existing rows remain valid with nulls, preserving the `UNIQUE(bot_id, source_key)`
  semantics for old writers. Backfill a persisted origin namespace and canonical JSON
  source key from `(bot_id, source_key)`; old-writer inserts resolve through this map to
  the same logical key, never a parallel charge. New sources use their stable event key
  for all owner kinds. Add source/idempotency_key/revision and chain constraints (§5)
  while retaining legacy uniqueness. Legacy `category` values are mapped by the deterministic
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
4. An action in `dispatched`, `unknown`, or unresolved dead-attempt `intent` blocks
   dependent actions and new task attempts until reconciled (or proven never sent).
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
