# Round 4 consolidation — Akira specification

**Consolidator:** CHATGPT · **Input:** `spec.md` v0.6 · **Output:** `spec.md` v0.7 (2026-10-25)
**Reviews:** CHATGPT 3 minor, DEEPSEEK 7 minor, GROK 7 minor — **17 findings**, no blocking or major.
**Previous consolidation:** `reviews/round-3/CONSOLIDATION.md` (v0.6).

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol (Codex banner) | **unverified** — banner metadata, not provider telemetry |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified** — provider reported no served model |

CHATGPT has banner-only served-model metadata and GROK reports no served model; both
are unverified. DEEPSEEK is verified by provider telemetry. Findings were checked
against local contracts; acceptance relies on that evidence, not model identity.

## Outcome

All 17 findings are accepted and merged, grouped into 16 changes below. **The review
converged at round 4 on spec v0.7. This is the last round:** no further review is launched
or requested. Convergence closes specification review. At HUMAN’s request, v0.7 is the final
specification and implementation baseline. Implementation is pending, and the
production evidence/release gates remain in force.

`loop.json` governed scope: spec, decisions, docs, evals and the declared assets path.
`assets/` remains absent as previously recorded. No unrelated project or historical
MASTER/TODO queue was used or changed. Activity is recorded only in the project CHANGELOG.

### Settled HUMAN decisions applied

`decisions.md` contains only AKIRA-D1–D6, all already implemented in the v0.6 text and
retained in v0.7. No matching “Pending HUMAN decision” passage remains to replace.

| Settled ID | Application retained in spec and companions |
|---|---|
| AKIRA-D1 | Akeru base, Akira name, specification/plan scope: §2.1, §2.4, pinned base header; docs/02–03 |
| AKIRA-D2 | No deletion without a HUMAN message naming items; archive-first, disabled retention and guarded purge: §2.1, AK-OPS-11/16/17; docs/12 |
| AKIRA-D3 | Specification only; no deployment, paid work or real customer contact authorized: §2.1, AK-SPC-08, AK-OPS-13; docs/10 |
| AKIRA-D4 | Linux x86_64, single node, SQLite, systemd user service, always available enough for routines/webhooks: §2.1, A1, AK-OPS-01; docs/12 §3 |
| AKIRA-D5 | Operator's personal subscription use permitted, API fallback, credentials protected, route-specific prohibition: §2.1, A2, AK-RTE-04/05; permission snapshots now explicit in docs/04–05 and examples |
| AKIRA-D6 | Private internal deployment, no publication/redistribution, preserved notices: §2.1, A8, AK-OPS-03; docs/02–03 |

U1–U3 remain historically resolved by AKIRA-D4–D6 and are excluded from the open list.
No new HUMAN answer, budget, vendor choice or policy approval was inferred.

## 1. Accepted and merged

Paths abbreviated `docs/04`, etc. refer to the numbered companion documents.

| ID | Evidence and reason | Change and location |
|---|---|---|
| M1 | Ledger enum omitted the infrastructure units already required by AK-ACC-11/docs/09. | Add sandbox-hour and host-month to UsageRecord.units; concrete synthetic rate/record cases in T-09. Docs/04 §5, docs/09 §10, docs/10 T-09. |
| M2 | A single category money cell cannot hold USD and EUR or separate provenance. | Shared CostSubtotal/UsageCoverage/CostBreakdown shapes; byCategory has per-currency/per-provenance subtotals plus coverage; rounding residuals labelled. Docs/04 §5, docs/09 §8, T-09. |
| M3 | Unknown fixture's second-read/24h wording suggested evidence-free retry. | Follow-up time is escalation only; repeated not-found and elapsed time keep unknown. Evidence/HUMAN reconciliation must establish prior effect. Action fixture, docs/04 §4.4, T-03. |
| M4 | Logical intent identity and provider-call dedupe had incompatible key/unique-index semantics. | Define logicalActionKey, optional providerIdempotencyKey, linkedActionId, credential reference and ActionContext. One unresolved logical action; scoped call-key registry maps provider key to logical key/hash, not a unique key on all state events. Linked retries keep intent/hash; provider reuse follows documented validity. AK-TSK-10/13; docs/04 §4.4/§6, docs/05 §5/§7, action fixture, T-03. |
| M5 | Backup takeover/auth wording and undefined always-adequate contradicted quota/default fallback edges. | Define none, infrastructure-only and explicit quota-only extension always-adequate; quota pauses by default, auth blocks for operator repair. Backup accounts use the same policy; never rewrite the failed attempt. All floor/permission/availability/approval/action/quarantine guards remain. AK-RTE-09/12/13, AK-TSK-01; docs/04 §4.1–4.2, docs/05 §6, docs/01 §3.3, docs/11 P3, docs/12 §7.2, T-02/F-04. No policy is enabled by this consolidation. |
| M6 | Failed-attempt separation had no defined filter and risked double addition to delivery. | Required query-only failedAttempts CostBreakdown selects effective delivery records on failed_* or interrupted attempts; remains inside delivery. Cancelled usage, rework, failed overhead and unclassified attribution are explicit. Embedded Task.cost may omit query fields. AK-ACC-14; docs/04 §5, docs/09 §4/§8, docs/06 inspector, fixture notes, T-09. |
| M7 | PersonaPatch was referenced but undefined. | Define field paths, set/remove, value, pinned base hash, layer/actor/revision/time; template → instance → HUMAN order, revision order within layer, ambiguity/type/hash rejection and field provenance. Explicit rebase on upgrade; no authority expansion. Docs/04 §2, docs/05 §1.1, T-05. |
| M8 | Usage uniqueness differed between owner kinds and export/merge; owner changes could duplicate charges. | Globally namespaced immutable source identity independent of owner; logical key + revision uniqueness, supersedes chain and duplicate receipt guards; stable legacy bot/source mapping; merge preserves chains and rejects conflicting successors. AK-ACC-01/09; docs/04 §5–§7, docs/03 concurrency, docs/09 §7/§12, usage fixture, T-09. |
| M9 | Budget pointer named U6, SLOs had no register owner, and §1.7 was not a heading. | Budget reference → U4; extend existing U4 question to include proposed service targets without approving values. Repair references to §1 item 7 in spec/docs/09/docs/13. Also align companion vendor-choice references to existing U7, not export item U8. Docs/01, docs/03, docs/07, docs/13; AK-TRG-10/AK-OPS-09. |
| M10 | A liveness notification and terminal-event recovery were conflated. | Preserve upstream-style 90s notification for a live session. Distinct lost-session/stream-without-terminal-event branch records interrupted, checkpoint and blocked/awaiting_input; no silence-only terminal deadline invented. Docs/05 §2 rule 4; F-07 explicitly asserts both branches; T-03/T-14. |
| M11 | CapabilityFloor/SupportLevel and ordering were undefined; probe omitted projected. | Define allowed-mechanism + requireVerified predicate per required skill and closed derived label. Native/projected are distinct; verified projection satisfies projected floor, not native. Probe accepts projected. AK-SKL-04; docs/04 §2–§3/§4, docs/05 §2.1/§3, route fixture, T-10. |
| M12 | Silence table allowed direct questions under codes other than no_evidence. | Apply existing direct-question prohibition to every code and legacy alias; quiet-hours/policy-hold cannot override it. Response remains within grants. AK-COL-05, docs/08 §3.2, docs/05 §1.3, T-06. |
| M13 | Permission was on capability descriptor but absent from dispatch records/candidates. | Add transportPermission to RouteSnapshot and candidates; selection/start/resume reject forbidden/unknown independently of meetsFloor; revalidate at dispatch and preserve attempt snapshot. AK-RTE-02/04; docs/04 §3–§4, docs/05 §1.2, route/task/usage examples and fixture notes, T-02/T-10. Subscription examples use HUMAN-accepted assumption, API permission stays unknown rather than inventing verification. |
| M14 | Effective usage states did not specify reservation replacement/release exclusion. | Settlement supersedes reservation under same logical key; latest revision once; released contributes no tokens/cost/coverage; reserved/unavailable retain known values and unknown coverage. AK-ACC-09; docs/04 §5, docs/09 §7/§12, T-09. |
| M15 | Failed-only route produces CPAT division by zero. | Zero accepted roots → n/a, with cost/sample size still visible; no zero/infinity value for calibration. AK-ACC-14/16, docs/09 §9, T-09. |
| M16 | task.start/checkpoint.resume and F-02 omitted the full unresolved-action guard. | Explicit dispatched/unknown/dead-attempt intent guard on commands, infrastructure transition and F-02; decider invariant remains authoritative. Docs/04 §4.1–4.2, docs/05 §1.2, T-02/T-03/F-02. |

No requirement IDs were added or removed. Draft-shape compatibility/migration handling is
in docs/05 §7; the examples retain draft schemaVersion 1.0, without claiming deployed
schema compatibility. Production contracts must be versioned/gated before adoption.

## 2. Decisions for HUMAN (single carried-forward open list)

These are existing **Akira project register IDs** in docs/13, not new AKIRA-D settlements.
HUMAN is not answering during automated review; no answer was awaited or chosen. Defaults
remain reversible proposals, not approvals. The review has ended with these still open.

| ID | Question | Default in v0.7 |
|---|---|---|
| U4 | Budgets, spend caps, concurrency caps, approval thresholds; service targets (availability, RPO/RTO, failed-channel notice time) | no HUMAN-set values; configurable labelled proposals, SLO proposals in docs/12 §2 |
| U5 | WhatsApp Business administration scope | messaging now; admin profile/numbers/templates |
| U6 | Rating aggregation model | configurable derived view; no fixed HUMAN weights |
| U7 | Telephony / WhatsApp / image / video vendors | contracts and candidates only; no selection |
| U8 | Existing team exports available | drafts marked needs-human-review; no invented content |
| U9 | Observer activation/template-upgrade approver | HUMAN or explicitly designated bot-admin |
| U10 | Log and backup retention windows | proposals only; no automatic deletion; AKIRA-D2 applies |
| U11 | Desktop/mobile in first release | web first |
| U12 | Multi-team/hosted tenancy | single environment |
| U13 | Scope of phone calls | outbound first; recording needs policy |
| U14 | Task run limit before HUMAN checkpoint | optional deadlines; defaults proposed |
| U15 | Akeru analytics | off |
| U16 | Cross-auth-class cost ranking | off; operator chooses across classes |

AKIRA-D1–D6 are settled and excluded. U4's clarification registers already-labelled SLO
proposals under the existing ID; it supplies no HUMAN target and creates no new decision.
Historical round lists are preserved; this is the current carried-forward list.

## 3. Rejected or deferred (with reasons)

**No finding rejected or left unfixed at specification level.** Alternative suggestions
were resolved as follows:

- DEEPSEEK-7: accept its explicit alternative of distinguishing liveness notification
  from interruption, preserving the inspected baseline that 90s silence never interrupts.
  Terminal interruption needs observed session/stream loss, not an invented timeout.
- DEEPSEEK-1: use a separate provider-call-key registry with references from linked
  actions/events rather than a unique provider key on every append-only event. This
  allows the permitted reused-key retry without a false uniqueness collision.
- DEEPSEEK-3: use a required query sub-line, not another stored Task.cost ledger total;
  the existing task fixture may omit these query-only fields by contract.
- GROK-4: define the existing explicit quota policy exception instead of removing the
  enum; it stays disabled by default. No automatic auth/capability/safety fallback is
  introduced and no U4 approval rule is selected.
- Executable schema decoders, policy/adapter implementations and acceptance suites remain
  implementation work (P0/P1 onward). T-09 contains concrete synthetic infrastructure
  record cases; no live infrastructure charge or vendor-rate verification was performed.
- Existing planned skill fixtures and the absent assets directory remain as previously
  documented; no asset or runtime behavior is invented to close this review.

## 4. Traceability of every finding

| Finding | Severity | Disposition |
|---|---|---|
| CHATGPT-1 | minor | accepted → M1 |
| CHATGPT-2 | minor | accepted → M2 |
| CHATGPT-3 | minor | accepted → M3 |
| DEEPSEEK-1 | minor | accepted → M4 |
| DEEPSEEK-2 | minor | accepted → M5 |
| DEEPSEEK-3 | minor | accepted → M6 |
| DEEPSEEK-4 | minor | accepted → M7 |
| DEEPSEEK-5 | minor | accepted → M8 |
| DEEPSEEK-6 | minor | accepted → M9 |
| DEEPSEEK-7 | minor | accepted → M10; notification/interruption distinction, §3 |
| GROK-1 | minor | accepted → M11 |
| GROK-2 | minor | accepted → M12 |
| GROK-3 | minor | accepted → M13 |
| GROK-4 | minor | accepted → M5 |
| GROK-5 | minor | accepted → M14 (+ M8 revision identity) |
| GROK-6 | minor | accepted → M15 |
| GROK-7 | minor | accepted → M16 |

All **17** findings accounted for: CHATGPT 3, DEEPSEEK 7, GROK 7.

## 5. Verification and limits

Static checks cover JSON parsing/schemaVersion on all eight fixtures, route permission
and skill-predicate shapes, task/route candidate identity, checkpoint/task revision
identity, usage key/source/revision consistency, action key/reconciliation shape,
requirement count/uniqueness and fault-table column structure. Arithmetic checks retain
the normative exclusive $3.12 / overhead $0.45 / delivery $2.67 / inclusive $3.50, the
failed-attempt $0.31 subset, exact 100 × USD 0.004 = USD 0.40, and the synthetic USD 10.50
infrastructure-unit example. Traceability is checked against all three review reports.
These are document/fixture consistency checks, not executed Akira acceptance tests or a
complete executable schema validator. The new positive/negative contract cases are
specified in docs/10 for implementation. No git command, deployment, authentication,
paid job, real customer contact, deletion or reviewer invocation was performed.
