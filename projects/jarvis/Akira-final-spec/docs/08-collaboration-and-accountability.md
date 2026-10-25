# 08 — Collaboration, silence, ratings, observer and inspectable records

**Status:** draft v0.6 · **Normative:** `spec.md` §10, §11, §15 · **Schema:** `docs/04-data-model.md`.

---

## 1. Why this is one document

Collaboration quality, deliberate silence, peer challenge, task ratings and the observer
are the same feedback system. A bot that talks too much looks responsive; a bot that
stays silent can hide failure; ratings can reward chatter; an observer can optimise for
ratings instead of outcomes. Akira specifies them together so incentives cannot be
gamed in isolation.

The rule that ties them: **visibility of work is not the same as visibility of
messages.** Activity, decisions and cost are always inspectable; speech is optional.

---

## 2. Rooms and boards

### 2.1 Structures

| Concept | Definition | Storage |
|---|---|---|
| Room | Topic + members + roles + routing rule + communication policy | Room aggregate |
| Board | Durable items (task, result, decision, proposal, alert) with links | BoardItem records |
| Decision | A recorded choice with evidence, alternatives and dissent | Decision aggregate |
| Handoff | A task transferred with acceptance criteria and checkpoint | Task with parent/reassign link |
| Room timeline | Merged view of messages, board events and task updates | Projection (not a second transcript) |

Akeru's groups (boss + specialists, mention routing) are the base. Akira adds topic,
roles, a routing rule that is visible, a board and decisions. The room timeline is
derived; the truth is the task/message/decision records.

### 2.2 Roles

| Role | May | May not |
|---|---|---|
| Owner (human or bot) | change room policy, close decisions, assign work | silently change another room's policy |
| Contributor | post, claim tasks, review | change policy or membership |
| Observer | read, rate, propose | post in the room's name, activate proposals |
| HUMAN operator | everything in the environment | bypass AKIRA-D2 (deletion) |

### 2.3 Routing rules

- `mention` (**the default rule for new rooms**): a message with `@bot` goes to that bot;
  multiple mentions → the first-listed wins, unless the room is configured last-wins.
- `lead-bot`: the room's lead answers every message; other bots may be pulled in by the
  lead. This is Akeru's "boss answers, last mention wins" behaviour; it is applied to
  migrated Akeru groups by configuration, not as the universal default.
- `round-robin`: balanced assignment across eligible bots.
- `assigned`: only the assigned bot answers; others may comment on board items.

The rule is displayed in the room header and can be changed only by an owner. An
unaddressed message in a `mention` room is handled by the lead/owner bot or not at all;
it is never broadcast to every bot (Akeru's "boss answers every message" becomes the
`lead-bot` configuration, not the universal default).

---

## 3. The publish gate and deliberate silence

### 3.1 Turn outcome

Every turn ends with exactly one outcome:

```ts
TurnOutcome =
  | { kind: "speak"; message: MessageDraft; links?: Link[] }
  | { kind: "act"; action: ActionRef; note?: string }          // board/artifact update, no chat message
  | { kind: "ask"; question: Question; blocking: boolean }
  | { kind: "escalate"; reason: string; to: "human" | "bot" | "room" }
  | { kind: "silent"; reason: SilenceReason; evidence?: Link[] }
  | { kind: "failed"; error: AttemptError }
```

`silent` is terminal and legitimate. The gate records the outcome, the reason code and
any evidence (what was checked), then emits nothing to the room.

### 3.2 Silence reason codes (closed set)

| Code | Meaning | Allowed when |
|---|---|---|
| `no_new_work` | message needs no action and adds no information | always |
| `already_answered` | a newer message or another bot answered the same point | answer is verifiably equivalent or better |
| `duplicate` | same content/topic within the dedupe window | dedupe key matches |
| `waiting_dependency` | bot is blocked and has nothing actionable | blocker recorded on a task |
| `quiet_hours` | room policy (the "quiet hours" half of the last AK-COL-05 clause) | policy in force |
| `policy_hold` | room rule says only lead/assigned bots speak (the "explicit room rule" clause of AK-COL-05) | rule matches |
| `no_evidence` | bot is **not addressed** and would have to speculate (the "not addressed and no evidence to add" clause of AK-COL-05) | guard: rejected if the bot was directly addressed (mention, assignment or direct question); it says so internally, not in chat |

The seven codes map onto the six AK-COL-05 clauses: every code belongs to exactly one
clause and every clause has at least one code. Five clauses have one code each
(`no_new_work`, `already_answered`, `waiting_dependency`, `no_evidence`, `duplicate`); the
last clause (quiet hours or an explicit room rule) has two (`quiet_hours`,
`policy_hold`), so the mapping is code → clause, not one-to-one. (v0.5's separate
`not_addressed` duplicated `no_evidence`: retain it in historical records and decode it
as a legacy alias of `no_evidence`, with the same direct-address guard; new records emit
only the seven canonical codes.) A policy-table test enforces the
mapping and that a direct question cannot be answered with silence.

A reason not in this set is a schema error, not a free-text excuse. Every silent turn
still writes an audit record (what it read, what it checked, what it spent).

### 3.3 Anti-ping-pong and anti-noise

| Mechanism | Rule |
|---|---|
| No auto-follow-up | A bot never starts a new turn because another bot posted (Akeru already avoids follow-ups on delegation; generalised) |
| Mention-only bot-to-bot | A bot messaging another bot requires a task/handoff, not a chat mention, unless the room enables direct bot dialogue |
| Budget | Max N bot messages per topic per window (proposed default 6; not HUMAN-approved); exceeding pauses the thread and alerts an operator |
| Dedupe | Hash of normalized content + topic within a window (proposed 10 min); duplicate suppressed with a reason |
| Consecutive speakers | A bot cannot post twice in a row without new evidence (a link, a result, a question answer) |
| "Nothing to say" | Prohibited in all forms; the publish gate returns `silent` instead |

### 3.4 Challenge protocol

A challenge is a structured record, not a tone:

```ts
Challenge {
  id; roomId; targetTaskId; targetRevision;
  challenger: botId | humanId;
  claim: string;                 // what the work asserts
  evidence: Link[];              // what contradicts or weakens it
  objection: string;             // the specific problem
  proposedTest?: string;         // how to settle it
  requestedDecision: "rework" | "clarify" | "accept-with-risk" | "reject";
  severity: "minor" | "major" | "blocking";
  status: "open" | "accepted" | "rejected" | "withdrawn";
  response?: { by; statement; evidence?: Link[]; outcome; };
}
```

Rules: steelman first (state the target's strongest version); evidence is required for
`major`/`blocking`; the target responds with concede/rebut/unresolved and evidence;
dissent is recorded in the decision even when overruled. A challenge that cannot name a
test or an evidence gap is a preference, and is recorded as such.

### 3.5 Handoffs

A handoff is a child task or reassignment with: goal, acceptance criteria, checkpoint
reference, deadline (optional), and the receiving bot's acknowledgement (accept/reject
with reason). A chat message pointing at work is not a handoff and does not transfer
ownership.

---

## 4. Accountability records

### 4.1 What "transparent" means (and does not)

Required, inspectable:

- the task's intent, acceptance criteria and scope;
- the route decision and its reasons, including rejected alternatives;
- the evidence used (links, artifacts, tool results);
- assumptions and uncertainties, stated as such;
- actions taken and their external results;
- corrections and their reasons;
- cost and who paid it (account);
- the final outcome against criteria.

Not required, and not fabricated:

- private chain-of-thought or hidden reasoning traces;
- a narrative that pretends certainty it did not have;
- provider-internal token-level explanations.

If a bot's conclusion cannot be explained from evidence, the record says so. A decision
record without evidence is itself a finding.

### 4.2 Decision record

```ts
Decision {
  id; roomId?; taskId?; statement; context;
  options: { option; pros; cons; rejectedBecause? }[];
  evidence: Link[]; assumptions: string[]; uncertainties: string[];
  decidedBy: actor; authority: "human" | "bot" | "policy";
  dissent: { by; position; evidence? }[];
  supersedes?: DecisionId; status: "active" | "superseded" | "reversed";
  createdAt;
}
```

A decision is not a chat message with a conclusion; it is a durable record linked from
the board. Reversals keep the prior record and state why.

### 4.3 Audit trail vs room visibility

| Event | Room visible | Operator audit | Notes |
|---|---|---|---|
| Silent turn | no | yes (reason, checks, spend) | Silence never hides activity |
| Route fallback | compact notice | yes (full reason) | Not silent |
| Failed attempt | task chip | yes (error class) | Not hidden |
| Observer proposal | board item | yes (cost) | Reviewable |
| Credential change | no | yes | Sensitive |
| Purge request | notice after completion | yes (ids, backup) | AKIRA-D2 |

---

## 5. Task ratings

### 5.1 Record

```ts
Rating {
  id; taskId; taskRevision; reviewer: actor; relationship: "consumer"|"peer"|"observer"|"human";
  criteria: {
    resolution: 1..5; quality: 1..5; rework: "none"|"minor"|"major";
    efficiency: 1..5; handoff: 1..5;
  };
  reasons: string;                    // required if any criterion ≤2 or ≥5
  evidence: Link[];                  // artifact/revision/acceptance links
  unresolvedIssues: string[];
  difficulty: { taskClass; complexityScore? };  // context, not an excuse
  createdAt; revision: integer; supersedes?: RatingId;
  dispute?: DisputeId;
}
```

### 5.2 Scale anchors

| Criterion | 1 | 3 | 5 |
|---|---|---|---|
| Resolution | did not address the issue | partially, workaround needed | fully, no workaround |
| Quality | wrong/unsafe/unusable | usable with fixes | correct, clear, ready |
| Efficiency | far over estimate/effort | near estimate | better than expected |
| Handoff | no context, hard to continue | adequate | excellent, resumable |

**Rework is not on the 1–5 scale.** It is the three-value enum `none | minor | major`
(§5.1), reported as a count per bot/task class. Reputation formulas average only the
numeric criteria (resolution, quality, efficiency, handoff); where a formula needs a
number for rework it uses a single documented one-way mapping (`none`=0, `minor`=1,
`major`=2 rework events) and never mixes the enum into the mean.

### 5.3 Aggregation options (no HUMAN-approved weights)

The specification requires a derived reputation view but does not fix a formula. Options
to evaluate during the vertical slice:

1. **Evidence-weighted mean**: mean of criteria, weighted by evidence quality, reviewer
   independence, and recency; disputes excluded.
2. **Median + confidence**: robust to outliers; confidence from sample size.
3. **Task-class normalised**: compare within difficulty, not across (a hard task done
   adequately is not worse than an easy task done perfectly).

Whatever is chosen: reputation is shown as a distribution with sample size, never a
single number; self-ratings are impossible; mutual-praise clusters are flagged; a bot's
declined/blocked tasks are visible (hiding hard work is not neutral).

### 5.4 Disputes and corrections

- A dispute names the criterion, the claim, and evidence.
- Disputed ratings are excluded from aggregates until resolved; both versions remain
  visible.
- Resolution requires a resolver distinct from **both** the rating's author and the
  disputant (or a HUMAN); the resolver and the outcome are recorded with reasons. The
  rating's author cannot resolve a dispute about their own rating.
- A pattern of upheld disputes against one reviewer downgrades that reviewer's weight.

### 5.5 Anti-gaming checklist

| Tactic | Detection | Response |
|---|---|---|
| Mutual praise | reciprocal 5s with no artifacts | flag, reduce weight, observer review |
| Rating only easy tasks | task-class distribution | show coverage, not just average |
| Hiding difficult work | declines/blocks vs ratings | record declines; reputation includes them |
| Chatter as productivity | messages per accepted task | not a rating criterion; observer ignores volume |
| Cheap but unusable output | rework vs cost | cost-per-accepted-task penalises it |
| Self-rating via delegation loop | reviewer == rated or proxy | identity check on reviewer chain |

---

## 6. Observer

### 6.1 Inputs

Task outcomes and ratings, rework evidence, failed attempts and failure classes, route
decisions vs outcomes, cost per accepted task, silence decisions, incidents and disputes.
It does **not** use message count or sentiment as a proxy for value.

### 6.2 Proposal

```ts
ObserverProposal {
  id; target: { kind: "template"|"persona"|"procedure"|"skill"|"route-policy"|"communication-policy"; id; version };
  diagnosis: string; evidence: Link[]; change: string; diff?: string;
  expectedBenefit: { metric; direction; rationale }[];
  expectedCost: { tokens; money: Money | MoneyRange; risk }[];      // docs/04 §1
  // evaluation.results.costDeltaPerTask is a Money (signed amountMinor; may be negative)
  evaluation: { method: "shadow"|"held-out"|"ab"; sampleSize; results; accepted: boolean };
  status: "draft"|"evaluated"|"awaiting_review"|"accepted"|"rejected"|"superseded"|"active";
  proposedBy: "observer"; approvedBy?: actor; activatedAt?; rollbackTo?: version;
  createdAt;
}
```

### 6.3 Lifecycle rules

1. The observer may only propose; it cannot edit templates, personas, goals, procedures,
   skills or permissions.
2. Evaluation happens before review: a shadow or held-out run with a stated metric and
   sample size; "it felt better" is not evaluation.
3. Approval is by a HUMAN or a designated bot-admin, never the observer.
4. Activation creates a new version, a rollback pointer, and an audit record.
5. Rejection is retained with reasons; repeated rejected proposals are a cost signal.
6. The observer's own usage is attributed and reviewed like anyone else's.

### 6.4 Hard boundaries

- HUMAN-defined goals, persona identity fields marked human-owned, and permission grants
  are not proposable for automatic activation; the observer may flag them for human edit.
- The observer may not rate tasks it influenced (conflict of interest); it may provide
  evidence to a human reviewer.
- The observer may not suppress an incident or a dispute.

### 6.5 Success and failure criteria

Success: accepted refinements measurably improve held-out outcomes at acceptable cost.
Failure: proposals that raise ratings without outcome improvement, or cost more than the
improvement is worth. Both are recorded; the observer is not exempt from rating.

---

## 7. Notification policy

| Event | Channel | Timing |
|---|---|---|
| Task blocked on HUMAN | room + operator inbox | immediate |
| Approval needed | addressed message | immediate |
| External effect unknown | operator inbox + task | immediate |
| Failed attempt (recoverable) | task chip only | batch |
| Observer proposal awaiting review | operator inbox | daily digest unless blocking |
| Usage threshold (if configured) | operator inbox | once per threshold per period |
| Backup failure | operator inbox | immediate |

No notification for silence, routine progress or "still working". A notification has an
owner, an action and a dedupe key; repeats update the existing item.

---

## 8. Open questions

- Whether a room can have multiple leads (current: one lead rule, contributors may be
  assigned).
- Whether peer (non-consumer) ratings should count toward reputation at reduced weight
  (current: relationship recorded, aggregation configurable — U6).
- Whether the observer may propose changes to another bot's template without that bot's
  admin's consent (current: yes, as a proposal; no, for activation).
- Retention of rejected proposals and disputes (current: keep; AKIRA-D2).
