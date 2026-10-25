# 10 — Tests, acceptance scenarios and traceability

**Status:** draft v0.3 · **Normative:** `spec.md` §18 and every requirement it references.
**Nothing in this document has been executed.** It defines what must pass, with which
fixtures and evidence, before a requirement is called done.

---

## 1. Test strategy

| Layer | What it proves | Tools / pattern | Gate |
|---|---|---|---|
| Contract tests | Schemas, commands, events, projections, export versioning | Akeru's Effect Schema tests + Akira fixtures | every PR |
| Decider/invariant tests | Illegal transitions rejected; invariants (§`docs/04` §8) hold | property/table tests on the decider | every PR |
| Adapter contract tests | Provider/skill/connector adapters honour interfaces and error taxonomy | shared adapter suite, fakes per vendor | every adapter change |
| Integration tests | Orchestrator + adapters + SQLite + files + fake provider | in-process harness, no network | every PR |
| End-to-end (stub) | Full flows with stub providers/connectors/webhooks | scripted stubs + fixture homes | every PR for critical paths |
| End-to-end (live, opt-in) | Real provider/tool/skill execution | test accounts only; explicit approval | release candidate |
| Fault injection | Crash, duplicate, timeout, 5xx, revoked token, disk full | chaos harness on staging | release candidate |
| Evals | Task-level outcome quality and routing calibration | golden tasks + ratings | phase exit |
| Restore/migration | Backup → new host → working team | scripted runbook | release candidate |
| Security | Injection, SSRF, secret leakage, scope escape | adversarial fixtures | release candidate |

**Rules.** No test may use real customer data, real phone numbers, real WhatsApp
recipients or paid media jobs without explicit approval (AKIRA-D3). Tests that need a
provider use a scripted fake that reproduces the dialect, including streaming and error
shapes. Live tests are labelled and run only on test accounts.

---

## 2. Mandatory acceptance scenarios

Each scenario is a release blocker. Evidence is attached to the task/PR.

### T-01 — Same bot across Codex → Claude → DeepSeek → Grok and back

**Steps.** Create `Natalia` from the research template. Seed three private memory facts,
one goal, one procedure, one skill bundle (`sheet-ops`), and a task with two completed
steps. Run a turn on Codex (stub/live). Switch route to Claude, then DeepSeek, then Grok,
then back to Codex, one turn each.

**Pass.** Same `botId` throughout; persona revision unchanged; all three facts recalled;
goal and procedure versions identical; skill support level reported per route; task
checkpoint advances; each attempt records route, provider-reported model (or `unknown`),
and usage. No new bot is created. Transcript continuity is visible.

**Fail signals.** Any identity field resets; memory loss; skill silently missing;
attempt without route provenance; a duplicate bot.

### T-02 — Forced credit exhaustion mid-task

**Steps.** Start a task on a route whose account is scripted to return `quota_exhausted`
after the first tool call. Observe the pause; answer "switch route" to an adequate
alternate; resume.

**Pass.** Attempt ends `failed_quota`; task status `paused`/`blocked` with a quota reason
and options; no silent model downgrade; checkpoint exists; resume on the alternate route
reconstructs plan/artifacts; a new attempt is recorded; cost of the failed attempt is
visible.

**Fail signals.** Automatic fallback to a cheaper model; task marked failed instead of
paused; lost artifacts; resume re-executes a completed external action.

### T-03 — Restart after a stub write was accepted but not acknowledged

**Steps.** Stub connector accepts `mail.send` then drops the response. Akira records
`unknown`. Kill the server. Restart. Run reconciliation with the stub reporting the
message exists.

**Pass.** Exactly one message exists in the stub. The action becomes `confirmed` with the
external id. No automatic retry occurred before reconciliation. Dependent work stayed
blocked. The UI showed `unknown` before resolution. Audit records the reconciliation.

**Fail signals.** Duplicate message; retry while unknown; task marked done; silent
resolution with no evidence.

### T-04 — Skill execution after switching

**Steps.** Install a skill with a reference file. Execute on Claude, Codex, Grok, then
DeepSeek (prompt-injected). On each route, ask the skill to read its reference file and
produce a verifiable output.

**Pass.** Native routes show the skill as discovered and invoke it end-to-end (tool
trace); the reference file is read. DeepSeek route shows `prompt-injected` and still
produces the correct output using the injected instructions plus the tool runtime. After
switching, the support level shown matches the recorded evidence.

**Fail signals.** Skill visible but not dispatched; resource unavailable; support level
claims native without execution evidence.

### T-05 — One template, two isolated instances

**Steps.** Instantiate the same template twice (`Natalia-A`, `Natalia-B`). Give A a memory
fact and a task; give B a conflicting fact. Run both.

**Pass.** Distinct bot ids, memory directories, task lists and usage rows. A's fact never
appears in B. Credentials are shared only by reference, never copied into the instance
record. Deleting/archiving A does not affect B (and never deletes B's data).

**Fail signals.** Shared memory path; copied secret; usage attributed to the wrong bot.

### T-06 — Justified silent turn

**Steps.** Post a message in a room that is already answered by a newer message; address
no bot; give the bot a duplicate of an existing answer. Also post a question that requires
work.

**Pass.** The bot ends with `silent` + an allowed reason; no chat message; audit record
shows what it checked and spend; the question turn produces a real answer. No "nothing to
say" message. A second duplicate within the window is suppressed.

**Fail signals.** Empty/placeholder message; missing audit; silence on a direct question;
repeated notifications.

### T-07 — Peer-disputed rating and correction

**Steps.** Natalia rates Rajiv's task 3/5 for efficiency with a reason. Rajiv disputes with
evidence that scope changed after the estimate. Resolve; then a second reviewer rates 5/5
with an artifact.

**Pass.** Both rating revisions retained; disputed rating excluded from aggregates while
open; dispute resolution records actor, evidence, outcome; reputation view shows sample
size and excludes the disputed value; no self-rating possible.

**Fail signals.** Rating overwritten; dispute resolved by the disputant; aggregate moves
while disputed.

### T-08 — Observer refinement evaluated for benefit and cost

**Steps.** Seed 10 historical tasks with ratings and rework evidence. Observer proposes a
procedure change. It runs a shadow evaluation on 6 held-out tasks. Approve; activate;
rollback.

**Pass.** Proposal record with target, evidence, expected benefit and cost; evaluation
results with sample size; approval by a non-observer; activation creates a new version
and rollback point; observer usage recorded in `observer` category; goals and persona
identity untouched.

**Fail signals.** Auto-activation; proposal without evaluation; persona/goal edited;
cost hidden.

### T-09 — Accounting without double counting

**Steps.** Execute the worked example (`docs/09` §4): parent task, failed attempt, rework,
child delegation, review, observer, triage. Query task exclusive, task inclusive, child,
room, bot, route, team.

**Pass.** Numbers equal the worked example within rounding; each record counted once
exclusively; inclusive parent includes child exactly once; team total equals sum of
exclusive records; reasoning tokens not added to output; coverage reports unknown.

**Fail signals.** Any total off by the child or overhead; duplicate settlement; hidden
failed cost.

### T-10 — Early triage of a complex integration

**Steps.** Submit the WhatsApp template/sender integration task. Observe triage before
execution: complexity flags, estimate range, readiness scoring, proposed routes.
Run bounded discovery; re-triage with new evidence; choose a route.

**Pass.** Triage record exists before dispatch; readiness `not-ready` disables the
cheap-build path until gaps are assigned; discovery stays within budget; re-triage creates
a new revision; route rationale visible; actual cost compared with the estimate after
completion.

**Fail signals.** Dispatch before triage; invented precision; no re-triage after new
evidence; estimate never compared with actual.

### T-11 — Full export and restore of the working team

**Steps.** Export without secrets. Restore on a clean second environment. Map projects.
Re-authenticate one connector. Start a task.

**Pass.** Bots, personas, rooms, tasks, checkpoints, memory, skills, procedures and usage
history present; unresolved actions restored as unresolved (not lost or auto-confirmed);
connector shows "needs re-auth"; no secret in the bundle; checksum/schema verified;
restored team can run a turn on a stub route. Export/restore report states what was
excluded and why.

**Fail signals.** Missing memory/routines/skills/usage; plaintext credential; restored
actions silently confirmed; partial import presented as success.

### T-12 — Deletion safety

**Steps.** Archive a bot with a synthetic clock advanced beyond seven days; run the
startup sweep and the hourly sweep. Then request a purge of a named synthetic bot.

**Pass.** The archived bot still exists after the window; no `bot.delete` command was
dispatched by a timer; all chats, memory and usage remain readable. The explicit purge
requires named ids, a `destructive` scope, writes a backup first and is audited. Docker
images are never touched by the application.

**Fail signals.** Any automatic deletion; purge without backup/audit; cascade that removes
chats or usage.

---

## 3. Fault injection matrix

| ID | Fault | Injection point | Expected attempt outcome | Expected recovery |
|---|---|---|---|---|
| F-01 | 401/expired token | provider adapter probe | `auth_expired` | block, ask reconnect, no fallback by default |
| F-02 | 429 with Retry-After | adapter | `rate_limited` | backoff, then infrastructure fallback if configured |
| F-03 | 5xx mid-stream | adapter stream | `network`/`unknown` | never duplicate tool side effects; resume from checkpoint |
| F-04 | Quota zero | adapter/probe | `quota_exhausted` | pause + options |
| F-05 | Tool schema mismatch | adapter tool mapping | `tool_contract` | repair or reroute, one retry |
| F-06 | Context overflow | provider | `context_overflow` | compaction, scope split |
| F-07 | Provider silent 90 s | runtime ingestion | watchdog activity (not a failure) | operator decides; task not auto-failed |
| F-08 | Crash between action dispatch and ack | executor + process kill | `unknown` | reconciliation, no blind retry |
| F-09 | Duplicate webhook | channel/WhatsApp stub | idempotent ignore | no double task, no double reply |
| F-10 | Lost chat result after completion | restart before delivery | pending → delivered once | ack in same persisted step (Akeru pattern) |
| F-11 | Disk full during checkpoint | filesystem | attempt fails `unknown` | operator alert; no corrupt checkpoint committed |
| F-12 | Skill resource missing | skill adapter | `failed_capability` | explicit unsupported, not silent |
| F-13 | Observer evaluation provider down | observer | `failed_network` | proposal stays `draft`; no activation |
| F-14 | Concurrent task start | supervisor | invariant rejection | one active attempt |
| F-15 | Clock skew / retention sweep | synthetic clock | no deletion | timer test proves absence |

---

## 4. Evals and fixtures

| Fixture | Purpose |
|---|---|
| `evals/fixtures/task.json` | valid task with triage, acceptance criteria, attempts |
| `evals/fixtures/checkpoint.json` | portable checkpoint incl. lost-state list |
| `evals/fixtures/route-decision.json` | floor pass/fail and rationale |
| `evals/fixtures/rating.json` | rating with evidence and dispute link |
| `evals/fixtures/observer-proposal.json` | proposal with evaluation and approvals |
| `evals/fixtures/usage-record.json` | turn record with cache/reasoning and provenance |
| `evals/fixtures/action-record.json` | unknown-outcome action with reconciliation |
| `evals/fixtures/skill-package.json` | canonical skill with support matrix |

Golden tasks for evals (synthetic, no customer data): a small coding task, a data
extraction task, a research brief with citations, a review/challenge task, a triage
task, a silent-turn task. Each has acceptance criteria and a reference outcome. Evals
measure accepted outcome, rework and cost per route — not prose quality.

---

## 5. Traceability matrix

Requirement groups map to suites; individual IDs are listed where behaviour differs.
Every row is a release gate.

| Requirements | Primary tests | Fault tests | Phase |
|---|---|---|---|
| AK-GOV-01..09 | decider/invariant tests, single-authority audit | F-08, F-14 | 1 |
| AK-IDE-01..14 | T-01, T-05, template/instantiation contract tests | F-12 | 2 |
| AK-UX-01..05 | declaration E2E, isolation test | — | 2 |
| AK-RTE-01..16 | T-01, T-02, adapter contract, route provenance | F-01..F-05 | 3 |
| AK-TRG-01..16 | T-02, T-10, eval calibration | F-04, F-06 | 4 |
| AK-TSK-01..18 | T-03, T-11, state-machine property tests | F-08, F-10, F-11, F-14 | 3 |
| AK-SKL-01..12 | T-04, per-route skill E2E | F-12 | 5 |
| AK-COL-01..14 | room routing, T-06, anti-loop tests | F-09 | 6 |
| AK-COL-03..07 (silence) | T-06, silence-policy table tests | F-07 | 6 |
| AK-RAT-01..08 | T-07, aggregation invariants | — | 6 |
| AK-OBS-01..08 | T-08, evaluation harness | F-13 | 7 |
| AK-ACC-01..16 | T-09, ledger invariants, coverage tests | F-10 | 4 |
| AK-SPC-01..12 | stub specialist E2E; live opt-in | F-08, F-09 | 8 |
| AK-CON-01..12 | connector contract + health tests | F-08, F-09 | 8 |
| AK-UX-06..22 | UI flow fixtures, accessibility checks | — | 9 |
| AK-SEC-01..12 | security suite (injection, SSRF, scope, secrets) | F-01, F-11 | 9 |
| AK-OPS-01..14 | T-11, restore drill, upgrade/rollback drill, alert test | F-11 | 10 |
| AK-MIG (in AK-IDE-13/14, AK-OPS-12) | T-11 + migration rehearsal | — | 9 |
| AK-TST-01 | this document is the gate | — | all |

---

## 6. Security test suite

| ID | Test | Pass |
|---|---|---|
| S-01 | Prompt injection in a web page/email/attachment | content treated as data; no tool escalation; event recorded |
| S-02 | Malicious MCP tool description | not executed; approval requested; provenance shown |
| S-03 | SSRF via fetch/WebFetch to loopback/private/CGNAT | rejected per hop (Akeru's resolver behaviour retained) |
| S-04 | Secret in memory/artifact/export | redacted, incident recorded, export refused if unresolved |
| S-05 | Cross-bot/room scope escape | command rejected server-side |
| S-06 | Webhook signature/replay | rejected or idempotent |
| S-07 | Sandbox token lifetime | no refresh token in sandbox; access token expires |
| S-08 | Privilege escalation via approval reuse | single-use, bound to call id |
| S-09 | Log/analytics leakage | no prompt content, no ids beyond the allowed schema |
| S-10 | Destructive command without scope/naming | rejected + audited |

---

## 7. Release gates

A release candidate is blocked unless:

1. All T-01..T-12 pass with evidence on staging.
2. Requirement-level suites for the release's scope pass.
3. Restore drill passed within the proposed RTO.
4. Security suite passed; no open high severity.
5. Fault matrix F-01..F-15 passed for the implemented paths.
6. Migration rehearsal passed for a synthetic team of 10 bots/4 rooms.
7. Changelog, compatibility matrix, known limitations and upstream revision recorded.
8. AKIRA-D2 checks: no timer-based deletion; purge requires explicit naming.

A live provider or connector failure during a live test is recorded and triaged, not
papered over. A test that needs a sleep to pass is a wrong test (Akeru's rule, adopted).

---

## 8. What is not tested (and why)

- Real customer communications, real phone numbers, paid media: not authorized by
  AKIRA-D3; tested with stubs and separately authorized test accounts.
- Hosted connector parity: no inventory from HUMAN; tested only for the defined service
  list.
- All provider models: route matrix is exhaustive for the supported drivers; individual
  models are verified on adoption, with `unknown` until then.
- Long-term (months) drift: monitored via reconciliation and rebase runs, not a test.
