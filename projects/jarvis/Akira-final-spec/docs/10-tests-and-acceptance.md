# 10 — Tests, acceptance scenarios and traceability

**Status:** draft v0.6 · **Normative:** `spec.md` §18 and every requirement it references.
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
after the first read-only tool call (no external write; an unresolved write instead
uses the external-effect guard and T-03). Observe the pause; answer "switch route" to an adequate
alternate; resume.

**Pass.** Attempt ends `failed_quota`; the exhausted route is recorded
`meetsFloor: true, available: quota_exhausted` (not as a floor failure) and the task
pauses rather than escalating; task status `paused`/`blocked` with a quota reason
and options; `task.resume` moves `paused → ready` and a new attempt starts; no silent model downgrade; checkpoint exists; resume on the alternate route
reconstructs plan/artifacts; a new attempt is recorded; cost of the failed attempt is
visible. Stale-definition case: change an acceptance criterion's statement (same id)
after a checkpoint; resume surfaces a `Task.revision`/`contentHash` mismatch against
`TaskCheckpoint.taskRevision` before dispatch and does not guess.

**Fail signals.** Automatic fallback to a cheaper model; task marked failed instead of
paused; lost artifacts; resume re-executes a completed external action; resume against a
changed task definition with no mismatch reported.

### T-03 — Restart after a stub write was accepted but not acknowledged

**Steps.** Stub connector accepts `mail.send` then drops the response. Akira records
`unknown`. Kill the server. Restart. Run reconciliation with the stub reporting the
message exists. **Write-ahead variants (F-18):** block the durable `dispatched`
append and assert the connector is never invoked; kill before that append completes.
Separately kill after durable append but before the call, and after stub acceptance but
before result persistence. Seed a legacy/fault-injected dead-attempt `intent` whose call
was started without the append: recovery must reconcile it rather than resend. This last
case models the old ordering defect; it is forbidden in the corrected executor.

**Pass.** Exactly one message exists in the stub. The action becomes `confirmed` with the
external id. No automatic retry occurred before reconciliation. Dependent work stayed
blocked. The UI showed `unknown` before resolution. Audit records the reconciliation. In
the write-ahead variant the connector is never invoked before a durable `dispatched`
record exists; the surviving `intent` of a dead attempt is reconciled (read-back), not
resent, and the task cannot start a new attempt until it is resolved; when the executor
proves the call never started, the action is cancelled with that proof recorded.

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
evidence that scope changed after the estimate. Natalia (the rating's author) attempts to
resolve the dispute and is rejected; a third party or HUMAN resolves; then a second
reviewer rates 5/5 with an artifact.

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
exclusive records; reasoning tokens not added to output; coverage reports unknown. The
unit split of `docs/09` §4a is preserved (provider-reported $0.82 / price-table $0.46 /
subscription-equivalent $1.84 exclusive) and no total is shown without it; every record
has exactly one category; delivery $2.67 + overhead $0.45 = exclusive $3.12; exclusive +
child = inclusive $3.50; the coverage buckets sum to the cost-bearing records; CPAT counts
a multi-attempt accepted task once in the denominator; a same-class parent/child pair
(parent $1 + child $1) yields a numerator of $2, not $3; a task that switched routes
contributes each attempt's cost to that attempt's route and counts once in the delivering
route's denominator; an accepted child under an accepted root adds nothing to the
denominator; inclusive T-142 equals exclusive (every category) + child, $3.50; 100 records
of USD 0.004 total USD 0.40 (summed as exact fixed point, rounded once), never 0 or 1.00; a
late cache-token correction
supersedes the effective snapshot without double counting tokens (including an
unavailable-to-reported settlement); a pre-migration usage row keeps one valid category
and counts once.

**Fail signals.** Any total off by the child or overhead; duplicate settlement; hidden
failed cost.

### T-10 — Early triage of a complex integration

**Steps.** Submit the WhatsApp template/sender integration task. Observe triage before
execution: complexity flags, estimate range, readiness scoring, proposed routes.
Run bounded discovery; re-triage with new evidence; choose a route.

**Pass.** Triage record exists before dispatch; every `pass` readiness criterion carries
an evidence link (a `pass` without one fails the test); readiness `not-ready` disables
the cheap-build path until gaps are assigned: the guard rejects candidates with `role:
specification-led` (docs/04 §4.3) while a floor-meeting `advanced` candidate may proceed
with the risks attached, and a below-floor candidate is rejected by the floor check for
every readiness outcome (the route-decision fixture carries both roles); candidates in two
auth classes are not ranked against each other by the role default, and two overlapping
cost ranges leave all otherwise eligible candidates `advanced` by default; each candidate's `skillSupport` is the
input of the skill floor and a `meetsFloor: true` candidate below the required support
fails validation; discovery stays within budget; re-triage creates
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

Server-level check: a **direct `bot.delete` command** sent by a client is rejected unless
it carries explicit ids, a verified backup, the `destructive` scope and an audit record
(i.e. it is the `purge.request` path). A UI-less client with the command's scope cannot
bypass the safeguards.

**Fail signals.** Any automatic deletion; purge without backup/audit; cascade that removes
chats or usage; a direct `bot.delete` accepted without the purge guards.

### T-13 — Backup never removes earlier generations

**Steps.** On synthetic state: run the backup (`docs/12` §5.2); remove a source file
(simulating a named purge or a missing mount); run the backup again.

**Pass.** The second run writes a new generation directory; the removed file is still
present in the first generation; no deletion flag was used; manifests and checksums verify
for both generations; removal of any generation requires a HUMAN-named operation. Within a
generation: a file with the same relative name in `attachments/`, `artifacts/` and
`memory/` (different contents) yields three distinct paths and hashes and all three restore
to their own trees; two runs on the same day produce two database snapshots; the manifest
has one entry per item for all seven items of `docs/12` §5.1 (checksum, or `absent` with
the reason; secrets present only encrypted). On a fresh generation with at least one
workspace holding `refs/t3/checkpoints`, `checkpoint-refs/` exists and holds that
workspace's ref list and bundle; with no workspaces the item is listed `absent: no active
workspaces`; removing a whole source tree yields an `absent` entry, not a silent skip; a
failed ref-list or bundle command stops completion and no complete manifest is written;
empty trees have a checksummed inventory, and missing required trees are marked absent
and incomplete. Faults are simulated with fixture snapshots, not by deleting real files.

**Fail signals.** Reused destination directory; `--delete*` flags; an earlier copy missing;
trees merged into one directory; a database snapshot overwritten or failing because the
name already existed; a missing item with no manifest entry.

### T-14 — Restore into recovery quarantine does not replay effects

**Steps.** Snapshot while one task is `ready` and another is `paused`; then let the live
stub system send a non-idempotent message for each (the paused task is resumed first) and
confirm them, and create a new task and channel delivery that exist only after the
snapshot; restore the snapshot on a second environment (original fenced); start with
queued work present (startup reconciliation runs).

**Pass.** The restored server starts with dispatch, routines, outbound delivery and
external writes disabled; the recovery point and uncertain interval are recorded; the
affected tasks (the `ready` one, the paused-then-resumed one, and the post-snapshot work)
are reconciled against preserved post-snapshot evidence or stay `blocked` for a HUMAN; no
second message is sent; startup reconciliation only marks or blocks and dispatches
nothing; release from quarantine is recorded per task.

**Fail signals.** Task dispatched on startup (including by the AK-TSK-14 queued-work
pass); a task released because its snapshot status was not in a listed set; second
message; both environments writing;
quarantine released without reconciliation.

**Safety controls (AK-SEC-09, AK-OPS-15).** `quarantine.release` without stored
reconciliation evidence is rejected; with it, one item is released and audited.
`dispatch.pause` blocks starting turns and external writes without cancelling work or
losing state, and `dispatch.resume` restores dispatch; both require the HUMAN Operator role and are audited. Test global, bot and connector
pause scopes, a write from an already-running attempt, pause persistence across restart,
unauthorized commands, and that resume/release cannot clear each other's independent
barriers. Release tests cover task, routine and channel delivery individually.

### T-15 — Skill catalogue completeness and availability gate

**Steps.** Run each mandatory skill's fixture (`docs/15` §2) on its required route
matrix; separately, register a conditional skill with no workflow-verified connector and a
skill whose fixture is made to fail.

**Pass.** Mandatory skills with passing fixtures are listed with per-route support and
verification; the conditional skill and the failed-fixture skill are `deferred` and absent
from `SKILLS.md` availability and the registry's available set.

**Fail signals.** A conditional skill advertised before connector verification; a failed
fixture advertised; browser automation substituted for the connector.

---

## 3. Fault injection matrix

Result kinds: `attempt outcome` (member of `AttemptOutcomeClass`, `docs/04` §4.2),
`action state` (§4.4), `delivery state`, `watchdog`, `invariant`, `retention`,
`quarantine`. The membership contract test applies only to `attempt outcome` results; each
other kind is asserted against its own component. A row may name both an attempt outcome
and another result; each is then asserted separately.

| ID | Fault | Injection point | Result kind | Expected result | Expected recovery |
|---|---|---|---|---|---|
| F-01 | 401/expired token | provider adapter probe | attempt outcome | `failed_auth` (class `auth_expired`) | block, ask reconnect, no fallback by default |
| F-02 | 429 with Retry-After | adapter | attempt outcome | `failed_rate_limit` if no action is `dispatched`/`unknown`; otherwise `interrupted` (stream severed) or `failed_unknown` (terminal 429, acceptance not established) | backoff, then infrastructure fallback if configured and no unresolved action; with an unresolved action: no retry or fallback until reconciled (both sub-cases tested) |
| F-03 | 5xx mid-stream | adapter stream | attempt outcome | `failed_network` before any external action; `interrupted` when stream ends without terminal event after send; `failed_unknown` for terminal error with acceptance unestablished | no duplicate effects; external-effect cases wait for reconciliation; all branches tested |
| F-04 | Quota zero | adapter/probe | attempt outcome | `failed_quota` | pause + options |
| F-05 | Tool schema mismatch | adapter tool mapping | attempt outcome | `failed_tool_contract` | repair or reroute, one retry |
| F-06 | Context overflow | provider | attempt outcome | `failed_context_overflow` | compaction, scope split |
| F-07 | Provider silent 90 s | runtime ingestion | watchdog | operator inbox activity, no terminal failure | operator decides; not auto-failed |
| F-08 | Crash between dispatch and ack | executor + process kill | attempt outcome; action state | attempt `interrupted`; action `dispatched` or `unknown`, then `confirmed` only with evidence | reconciliation, no blind retry |
| F-09 | Duplicate webhook | channel/WhatsApp stub | delivery state | idempotent ignore | no double task/reply |
| F-10 | Lost chat result after completion | restart before delivery | delivery state | pending → delivered once | ack in same persisted step |
| F-11 | Disk full during checkpoint | filesystem | attempt outcome | `failed_unknown` | operator alert; no corrupt checkpoint committed |
| F-12 | Skill resource missing | skill adapter | attempt outcome | `failed_capability` | explicit unsupported |
| F-13 | Observer evaluation provider down | observer | attempt outcome | `failed_network` (no external action) | proposal stays `draft` |
| F-14 | Concurrent task start | supervisor | invariant | rejected second start | one active attempt |
| F-15 | Clock skew / retention sweep | synthetic clock | retention | no deletion | timer test proves absence |
| F-16 | Restore older than a confirmed non-idempotent write | restore drill | quarantine | affected work blocked pending reconciliation | no second write; T-14 |
| F-17 | Cancel while action unknown | canceller | attempt outcome; action state | `cancelled`; action remains `unknown` | no ready/start until reconciliation; blocked/paused |
| F-18 | Crash around write-ahead boundary | executor durable append / stub | invariant; attempt outcome; action state | no call before durable `dispatched`; attempt `interrupted`; dead-attempt `intent` blocks until reconciled or proven never sent | T-03 variants: pre-append, post-append/pre-call, accepted/pre-result, legacy bad ordering; no resend |

Enum membership applies to each explicitly named attempt outcome only; component states
and assertions are checked separately. Test every named branch, including the
external-effect override in docs/04 §4.2 (no terminal event → `interrupted`; terminal error
with unestablished acceptance → `failed_unknown`).

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
| `evals/fixtures/skill-package.json` | canonical skill with support matrix (format example; its validation fixture is planned) |

All fixtures carry `schemaVersion` (`docs/05` §7). Fixtures are validated against the
published shapes (`docs/04`: summary/proposal `Money` as `amountMinor` + currency,
usage `ExactMoney` as coefficient + scale + currency, `SkillSupportEntry`, checkpoint
`taskRevision`, `RouteSnapshot`, and candidates including `authClass`, options, provenance,
per-required-skill `skillSupport`, `role` and role basis; `docs/08` ObserverProposal money
and cost delta) as well as JSON syntax; the executable
validator is implementation work (P0/P1) and must reject a shape mismatch. Fixtures are
validated for semantic
invariants as well as JSON syntax: no route with `meetsFloor: true` below the required
skill support; availability separate from capability; unit-split cost summaries whose
subtotals sum to the combined estimate; readiness `pass` criteria with evidence;
overhead equal to review + coordination + observer.

Golden tasks for evals (synthetic, no customer data): a small coding task, a data
extraction task, a research brief with citations, a review/challenge task, a triage
task, a silent-turn task. Each has acceptance criteria and a reference outcome. Evals
measure accepted outcome, rework and cost per route — not prose quality.

---

## 5. Traceability matrix

Requirement groups map to suites; individual IDs are listed where behaviour differs.
Every row is a release gate. The Phase column uses the backlog numbering `P0`–`P10` of
`docs/11-backlog.md`.

| Requirements | Primary tests | Fault tests | Phase |
|---|---|---|---|
| AK-GOV-01..09 | decider/invariant tests, single-authority audit | F-08, F-14 | P0–P2 |
| AK-IDE-01..14 | T-01, T-05, template/instantiation contract tests | F-12 | P1 |
| AK-UX-01..05 | declaration E2E, isolation test | — | P1 |
| AK-RTE-01..16 | T-01, T-02, adapter contract, route provenance | F-01..F-05, F-03 external-effect guard | P3 |
| AK-TRG-01..16 | T-02, T-10, eval calibration, availability-vs-floor test (T-02) | F-04, F-06 | P3 |
| AK-TSK-01..18 | T-03, T-11, T-14, state-machine property tests (incl. resume/recovery transitions) | F-08, F-10, F-11, F-14, F-16, F-18 | P2 |
| AK-SKL-01..12 | T-04, per-route skill E2E | F-12 | P4 |
| AK-SKL-13..14 | T-04 plus catalogue tests (T-15): each mandatory skill's `docs/15` fixture passes on its required route matrix; negative tests: a skill whose fixture failed, or a conditional skill whose connector is not workflow-verified, is not advertised in `SKILLS.md` or the registry | F-12 | P4 (conditional skills: P8) |
| AK-COL-01..14 | room routing, T-06, anti-loop tests | F-09 | P6 |
| AK-COL-03..07 (silence) | T-06, silence-policy table tests (every code maps to an AK-COL-05 clause; a direct question cannot be silent) | F-07 | P6 |
| AK-RAT-01..08 | T-07, aggregation invariants | — | P6 |
| AK-OBS-01..08 | T-08, evaluation harness | F-13 | P6 |
| AK-ACC-01..16 | T-09, ledger invariants, coverage tests, legacy-category migration test | F-10 | P5 (estimate/price-table slice: P2) |
| AK-SPC-01..12 | stub specialist E2E; live opt-in | F-08, F-09 | P7 |
| AK-CON-01..12 | connector contract + health tests | F-08, F-09 | P8 |
| AK-UX-06..22 | UI flow fixtures, accessibility checks | — | P9 |
| AK-SEC-01..12 | security suite (injection, SSRF, scope, secrets, S-11 export/restore audit) | F-01, F-11 | P10 |
| AK-OPS-01..17 | T-11, T-12, T-13, T-14, restore drill, upgrade/rollback drill, alert test, runbook walk-through (release gate 9) | F-11, F-16 | P10 (P0 for the deletion items) |
| AK-MIG (in AK-IDE-13/14, AK-OPS-12) | T-11 + migration rehearsal | — | P9 |
| AK-TST-01 | this document is the gate | — | all |

Planned fixture directories under `evals/fixtures/skill-*/` are created with their skill
in P4; until then they are planned, not present.

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
| S-10 | Destructive command without scope/naming (including a direct upstream `bot.delete`) | rejected + audited |
| S-11 | Export and restore | each produces an audit record (actor, scopes/bundle id, destination, checksum, result); an export's destination and included scopes are visible |

---

## 7. Release gates

A release candidate is blocked unless:

1. All T-01..T-15 pass with evidence on staging.
2. Requirement-level suites for the release's scope pass.
3. Restore drill passed within the proposed RTO.
4. Security suite passed; no open high severity.
5. Fault matrix F-01..F-18 passed for the implemented paths.
6. Migration rehearsal passed for a synthetic team of 10 bots/4 rooms.
7. Changelog, compatibility matrix, known limitations and upstream revision recorded.
8. AKIRA-D2 checks: no timer-based deletion; purge requires explicit naming.
9. The ten AK-OPS-08 incident runbooks exist in `docs/12` §7 (including §7.10,
   unauthorized action) and each has been walked through once on synthetic state.

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
