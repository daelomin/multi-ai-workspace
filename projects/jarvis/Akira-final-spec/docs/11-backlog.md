# 11 — Phased implementation backlog

**Status:** Final specification v0.7 · **Normative scope:** `spec.md` (complete target) · **Estimates:** ranges, ±50%, no historical velocity data.

The plan specifies the complete target and defers features explicitly. It does not
silently drop anything: deferred items are listed in §8 with the trigger that would pull
them forward.

**Effort unit:** engineer-weeks (ew) for one experienced engineer familiar with
TypeScript/Effect and agent runtimes. Ranges reflect unknown Akeru adaptation cost, not
optimism.

**Totals (planning, ±50%, no measured velocity).** Core to beta — P0–P6, P9, P10 —
**35–50 ew**. Specialists (P7, 6–10 ew) plus the first three connectors (P8, 5.6–10.4 ew,
§10): **≈12–21 ew**. Full target: **≈47–71 ew**. The vertical slice (§13) is 6–9 ew of that core.

---

## 1. Critical path

```
P0 baseline/spike
   └─► P1 identity/template core ─┬─► P2 task+checkpoint+ledger ─► P3 routing/triage ─► P5 accounting
                                  │                                     │
                                  ├─► P4 skills portability ────────────┤
                                  │                                     ▼
                                  └─────────────────────────────► P6 rooms/silence/ratings/observer
                                                                      │
                                          P7 specialists / P8 connectors (parallel, after P2/P3)
                                                                      ▼
                                                            P9 UX + migration ─► P10 hardening
```

P7 and P8 can start once P2/P3 interfaces are stable; they do not block P6. P9 runs
continuously from P1 (thin slices) and converges in P9.

---

## 2. Phase 0 — Baseline, deletion safety and continuity spike

**Effort:** 2–3 ew · **Depends on:** access to this host and test accounts.

**Work.**

1. Build the pinned Akeru revision on Linux; record exact Node/pnpm/vp versions and
   artifact hash.
2. Disable `ARCHIVED_BOT_RETENTION_DAYS`/sweep in a patch; write a synthetic-clock test
   proving no delete command is dispatched; remove/guard the hard-delete UI path **and**
   make the decider reject a direct `bot.delete` unless it carries the `purge.request`
   guards (explicit ids, verified backup, `destructive` scope, audit); add the server-level
   test (T-12).
3. Prove the primary goal manually: one bot, memory fact, procedure, goal placeholder,
   `SKILL.md`, a partly completed task across Codex/Claude/DeepSeek/Grok and back; record
   exactly what survives and what does not.
4. Measure the real patch surface for identity, task, usage and skills; compare against
   `docs/02` estimates. Record in `docs/14-evidence-log.md`.
5. Decide whether the "second authority" trigger fired (see §7).

**Deliverables.** `upstream.yaml` + patch series skeleton; spike report; retention test;
capability matrix updated with measured facts.

**Exit criteria.** A named bot completes a turn on all four routes with history,
memory and a skill attempt recorded; no automatic deletion is possible; build is
reproducible from a script; the spike report lists every deviation from this spec.

**Risk.** DeepSeek tool reliability, skill dispatch on the Mastra Claude path, and the
Windows/macOS-only features may invalidate assumptions; all three are bounded tests.

---

## 3. Phase 1 — Identity, persona and library core

**Effort:** 4–6 ew · **Depends on:** P0.

**Work.**

1. New aggregates: `BotTemplate`, `PersonaRevision`, `BotInstance` fields, `Goal`,
   `Procedure`, `Room` (minimal), with commands/events/projections and invariants.
2. Replace instruction generation with persona rendering; snapshot tests per route.
3. Instantiation/upgrade/clone commands; isolation test (T-05).
4. Library of 10 specialist templates (data + review), with provenance.
5. Migration backfill: legacy bots → default persona revision marked `imported`.
6. Minimal declaration UI (template pick, identity, policy, dependencies, first task).

**Exit criteria.** T-05 passes; a bot created from a template in under three minutes gets
a first accepted task on a stub route; persona is identical across two routes (snapshot);
no legacy bot is left without a persona revision; archived bots are never deleted.

---

## 4. Phase 2 — Task, attempt, checkpoint and action ledger

**Effort:** 6–8 ew · **Depends on:** P1.

**Work.**

1. `Task`, `Attempt`, `TaskCheckpoint`, `RouteDecision` aggregates and state machines.
2. Task Supervisor reactor dispatching only commands; single-active-attempt invariant.
3. Checkpoint writer/reader; link to Akeru's git-ref checkpoints; resume path with
   compatibility report.
4. Action Executor + ledger; unknown-state semantics; reconciliation jobs.
5. Task inspector UI; recovery flow; task creation from chat/delegation.
6. Restart reconciliation (attempts, actions, queue) with typed outcomes.

**Exit criteria.** T-02 and T-03 pass; a task survives a hard kill and resumes on a
different stub route; no external action is retried while unknown; the worked-example
task can be replayed end-to-end.

**Risk.** This is the highest-complexity phase; the temptation to add a side store is the
main architectural risk (ADR-01).

---

## 5. Phase 3 — Routing, triage and readiness

**Effort:** 4–6 ew · **Depends on:** P2 (interfaces) and a P2 prerequisite: the
versioned price table and estimate-basis records (a small slice of P5 delivered with P2
so cost bands exist before route selection; P5 later adds the full ledger extension,
queries and views).

**Work.**

1. Capability profiles per route/model with evidence records; probes.
2. Task classes, capability floors, route candidates and selection policy (config).
3. Triage: complexity drivers, estimate ranges, discovery budget, readiness rubric,
   re-triage.
4. Fallback policy and failure taxonomy mapping; quota pause path.
5. Route rationale UI; switch consequences; provenance on attempts.

**Exit criteria.** T-10 passes; a quota failure pauses by default; explicit quota fallback preserves all guards (docs/04 §4.2); a below-
floor route cannot be selected by policy or UI; every attempt has route provenance;
estimates are compared with actuals and stored.

---

## 6. Phase 4 — Skills portability

**Effort:** 3–4 ew · **Depends on:** P1/P2.

**Work.**

1. Skill registry (package, hash, provenance, validation) + `SKILLS.md` generation.
2. Adapters: Claude projection, Codex projection, Grok CLI probe, prompt-injection for
   Custom API/Kimi/OpenCode Go.
3. Support-level verification harness (fixture skill with resource file) per route.
4. Re-check on route switch; UI support badges.

**Exit criteria.** T-04 passes on all four routes (native or injected, correctly
labelled); the ten v1-mandatory skills in `docs/15-skills-v1.md` each pass their fixture
on the required routes; the four connector-conditional skills are `deferred` until their
connector is workflow-verified; no route claims a skill it cannot execute; support matrix
exported/restored.

---

## 7. Phase 5 — Accounting

**Effort:** 3–4 ew · **Depends on:** P2.

**Work.**

1. Ledger extension (columns, corrections, units, provenance); idempotency keys.
2. Write paths: turns, tools, delegation, workers, routines, review, observer, media.
3. Queries: exclusive/inclusive, task/bot/room/route/account, coverage.
4. Cost views with provenance labels; drill-down; price table versioning.
5. Reconciliation + coverage alerts.

**Exit criteria.** T-09 passes exactly; no double counting under delegation/retry/worker;
coverage and unknown are displayed; exports preserve parent links.

---

## 8. Phase 6 — Rooms, silence, ratings and observer

**Effort:** 5–7 ew · **Depends on:** P2/P3.

**Work.**

1. Room aggregate, roles, routing rules, board items, decisions; merged timeline.
2. Publish gate + `TurnOutcome`; silence reason codes; anti-loop budgets/dedupe.
3. Rating aggregate, disputes, reputation views, anti-gaming checks.
4. Observer service: inputs, proposal lifecycle, shadow evaluation harness, approval,
   activation/rollback, cost attribution.
5. Challenge protocol record and decision log.
6. Notification policy and digests.

**Exit criteria.** T-06, T-07, T-08 pass; no bot can self-rate; no auto-activation;
silence never hides activity; observer cost visible.

---

## 9. Phase 7 — Specialist capabilities

**Effort:** 6–10 ew for contracts + stubs + first adapters; live onboarding extra.
**Depends on:** P2 (Action Executor), P5 (cost units).

**Work.**

1. Capability contracts: telephony, messaging, whatsapp-admin, image, video.
2. PSTN adapter (candidate Twilio) with call state, callbacks, DTMF, recordings,
   consent policy; stub-first.
3. WhatsApp messaging extension (media, templates) on the existing channel; delivery
   states incl. unknown.
4. WhatsApp administration adapter (profile, numbers, templates, quality) where the API
   supports it; explicit unsupported list.
5. Image provider-agnostic tool; local model option.
6. Video workflow: stages, async jobs, render approval, partial-failure recovery.
7. Cost attribution per unit; specialist acceptance scenarios.

**Exit criteria.** All specialist scenarios pass against stubs; live path only with
authorized test accounts; no unscoped send/pay action; unknown outcomes reconcile.

**Risk.** Vendor onboarding (Meta/Twilio) can dominate; start onboarding early, in
parallel, with no production commitment.

---

## 10. Phase 8 — Connectors

**Effort:** ≈1.4–4 ew per service; **Depends on:** P2, P7 interface.

**Basis (one basis with `docs/07` §6.2).** Per service = the adapter-only person-days in
`docs/07` §6.2 (2–10 d, i.e. 0.4–2 ew at 5 d/ew) **plus** 1–2 ew of integration work the
adapter estimate excludes: auth custody, per-bot grants, health check, action-ledger
integration, docs and workflow-verification tests (planning placeholder, ±50%, re-estimate
at P8 start). First three connectors: adapters 13–22 d (2.6–4.4 ew) + 3 × 1–2 ew =
**5.6–10.4 ew**.

**Work.** Per service: adapter + manifest, auth custody, health check, action ledger
integration, per-bot grants, tests, docs. Priority order (by team value): Gmail,
Calendar, Drive/Sheets, Slack, Notion, GitHub, then others.

**Exit criteria.** Each connector: discovery/auth/workflow statuses separate; health check
real; unknown outcomes reconcile; scopes minimal; export excludes tokens.

---

## 11. Phase 9 — UX convergence and migration

**Effort:** 5–7 ew · **Depends on:** P1–P6.

**Work.** Workspace shell, declaration wizard, task/route/usage/rating/observer panels,
board, recovery, migration wizard, accessibility. Migration of the ten bots and four
rooms as drafts; shared-page handling; Weekly bot scorecard procedure draft; HUMAN review
checklist.

**Exit criteria.** T-11 passes; migration rehearsal completes; a HUMAN can operate the
team without editing files; the ten bots exist with personas marked reviewed or
explicitly waived.

---

## 12. Phase 10 — Hardening and operations

**Effort:** 3–5 ew · **Depends on:** all.

**Work.** Backup/restore automation + drill, upgrade/rollback, monitoring/alerts, incident
runbooks, capacity test, security suite, release packaging, docs, training.

**Exit criteria.** Release gates (`docs/10` §7) pass; restore drill within RTO; alerts
tested by fault injection; rollback tested; known limitations published.

---

## 13. Smallest useful vertical slice

**Goal:** prove the thesis end-to-end before building breadth.

**Scope (6–9 ew):** P0 + minimal P1 (template + persona + instance + one library
template) + minimal P2 (task, one attempt, checkpoint, action ledger) + minimal P3
(capability floor + route switch) + minimal P5 (turn usage + task roll-up) + one native
skill route + minimal P6 (silent outcome + one rating) + one stub connector.

**Demo script.**

1. Declare `Natalia` from the research template in under three minutes.
2. Run a small task on the cheapest adequate route; show triage, route reason, checkpoint.
3. Force quota exhaustion; switch to another adequate route; resume from checkpoint;
   show the same bot id, memory and artifacts.
4. Run the skill on both routes; show native vs prompt-injected support levels.
5. End a duplicate turn silently; show audit, no message.
6. Have a peer rate the task; show the disputed-rating path.
7. Execute a stub connector write that loses its acknowledgement; restart; reconcile;
   show one effect only.
8. Show task exclusive/inclusive usage and cost, with the failed attempt visible.
9. Export and restore the team on a second directory; start a turn.

**Why this slice.** It exercises the primary goal, the safety property, the accounting
truth and the collaboration model on a small surface. It also produces the calibration
data (cost, latency, failure rates) needed before committing to P7/P8 breadth.

**What it deliberately omits.** Multiple specialists, live connectors, video, mobile,
observer evaluation at scale, full library. Those follow only after the slice's evidence
supports them.

---

## 14. Explicit deferrals

| Deferred | Why | Trigger to pull forward |
|---|---|---|
| Mobile feature parity | Server contract is shared; mobile can read/reply/approve first | Team asks for field use; approvals on the go become a bottleneck |
| Desktop packaging beyond upstream | Electron shell exists; web covers the workflow | Offline/desktop-only requirement |
| Hosted multi-tenant | Security/compliance and tenancy cost | External customers or >1 team |
| Public plugin marketplace | Trust, review, distribution | Community contribution demand |
| Full video editing timeline | Complexity; scripted renders cover the need | Marketing needs frame-level editing |
| Live PSTN barge-in / realtime duplex | Streaming media service | Call quality becomes a product requirement |
| Postgres/multi-process | Single-node is sufficient (A3) | ADR-10 triggers |
| Automated template authoring by observer | Risk of persona drift | Observer proposals prove reliable for ≥3 months with review |
| Federated rooms across environments | No requirement yet | Multi-site team |
| Automatic cost-based route flapping | Needs calibration and stability | Ledger has ≥200 accepted tasks per class |

---

## 15. Maintenance budget (steady state)

| Activity | Cadence | Effort |
|---|---|---|
| Upstream rebase (pinned → newer) | quarterly or on security fix | 1–2 ew + regression run |
| Patch conflict review | per rebase | included |
| Provider/model updates (deprecations, new models) | monthly check | 0.5–1 ew/month |
| Connector auth/API drift | quarterly per connector | 0.5 ew each |
| Backup/restore drill | quarterly | 0.5 ew |
| Security review | per release | 0.5–1 ew |
| Price-table update | monthly or on vendor change | 0.25 ew |

Summing the rows for one quarter (one rebase, three monthly provider checks, three
price-table updates, one connector, one drill, one release security review) gives
**≈4.75–7.75 ew/quarter**, plus 0.5 ew per additional connector. This sum is a planning
placeholder, not a measured figure (the earlier 2–4 ew figure did not match the table).
It must be replaced with actuals after two quarters.

---

## 16. Backlog risks and decision points

| Point | Decision | When |
|---|---|---|
| DP-1 | Does the spike show adapter-level extension is enough, or does a second authority appear? | end of P0 |
| DP-2 | Is the persona/instructions replacement clean across all routes? | end of P1 |
| DP-3 | Do task/checkpoint semantics hold under restart and provider switch? | end of P2 |
| DP-4 | Is routing calibration possible with available data? | mid P3 |
| DP-5 | Are specialist vendors onboardable in the required window? | start of P7 onboarding |
| DP-6 | Does the vertical slice meet the acceptance bar? | end of slice |
| DP-7 | Is the upstream patch burden sustainable? | after first rebase |
| DP-8 | Is the single-node capacity model holding? | end of P10 |

If DP-1 or DP-7 fails, the fallback is a bounded re-evaluation of the thin-composition
option — not a silent architecture change. It would be recorded as a HUMAN decision,
with the measured patch burden and the retained/replaceable behaviours.
