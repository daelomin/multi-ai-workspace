# Round 2 consolidation — Akira specification

**Consolidator:** CLAUDE · **Input:** `spec.md` v0.4 · **Output:** `spec.md` v0.5 (2026-10-25)
**Reviews:** `CHATGPT.md` (4 findings), `DEEPSEEK.md` (6), `GROK.md` (9) — 19 findings.
**Previous consolidation:** `reviews/round-1/CONSOLIDATION.md` (38 findings, all accepted).

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified** — the provider reported no served model |

GROK is the unverified reviewer. Its findings are weighted as evidence only where a second
reviewer corroborates them or the cited text was read and confirmed. Findings with no
second reviewer are GROK-2 (startup dispatch under quarantine), GROK-4 (specification-led
predicate) and the cancel-edge/429-after-send parts of GROK-3; each was checked against the
cited text in `spec.md` v0.4 and `docs/04`/`docs/05`/`docs/12` before acceptance, and the
defects are present as described.

## Outcome

`decisions.md` holds only AKIRA-D1–D6, all applied in v0.3; there is no "Pending HUMAN
decision" passage, so nothing changed from `decisions.md` and no open item left the list.
Round 2 found major defects in the runbooks and guards added by round 1, not in its
direction: the backup generation is not a faithful restore set (3/3 reviewers), startup
reconciliation can dispatch during quarantine and the quarantine checklist is narrower than
AK-OPS-15 (2/3), a retry/fallback path or cancel edge can still follow an unresolved
external action (GROK), and the "specification-led" guard has no decision procedure
(GROK). All were accepted; no finding was rejected. No new requirement ID was added
(requirement count stays 209). Round 3 reviews v0.5.

## 1. Accepted and merged

| ID | Change | Where |
|---|---|---|
| N1 | Backup generation is complete and faithful: each tree copied under its own path (no trailing-slash merge); database snapshot named by the per-run timestamp inside the generation (`VACUUM INTO` needs a fresh target); checked steps for encrypted secrets, configuration, content-addressed registry, checkpoint refs + bundles; manifest with one checksummed entry per item; T-13 extended (same-name file in three trees, two runs same day, seven manifest items) | AK-OPS-16; `docs/12` §5.2; `docs/10` T-13 |
| N2 | Recovery quarantine covers every task/routine/delivery that could have acted whatever its snapshot status (paused, terminal, post-snapshot work); AK-TSK-14 startup reconciliation may only mark/block under quarantine; T-14 gains paused-then-resumed and post-snapshot cases | AK-OPS-15, AK-TSK-14; `docs/12` §5.3; `docs/10` T-14 |
| N3 | One error-class → attempt-outcome table; fault matrix and runbooks use outcome names; AK-TSK-14 records `interrupted`; retry/fallback columns apply only with no `dispatched`/`unknown` action (429 after send is `interrupted`/`failed_unknown`); cancel edge and `task.start` require reconciliation first; F-02 split, new F-17 (cancel with unknown action), contract test for outcome membership | AK-RTE-12, AK-TSK-01, AK-TSK-14; `docs/04` §4.1–4.2; `docs/05` §6; `docs/10` F-01..F-17 |
| N4 | "Specification-led" defined: `role` attribute on each route candidate, set by versioned route policy (proposed default: lowest-cost floor-meeting candidate is specification-led, others advanced); `not-ready` rejects only that role; below-floor rejected by the floor check alone; role added to fixtures and T-10 | AK-TRG-07, AK-TSK-01; `docs/04` §3, §4.1, §4.3; `docs/10` T-10; fixtures |
| N5 | CPAT numerator is the union of effective usage records of a root-task cohort (each record once), not a sum of inclusive totals; route attribution per attempt; denominator counts accepted root tasks of the cohort; T-09 gains same-class parent/child ($2 not $3) and multi-route cases | AK-ACC-14; `docs/09` §9; `docs/10` T-09 |
| N6 | Task has monotonic `revision` and `contentHash`; checkpoint `taskRevision` = `{taskId, revision, contentHash, triageRevision}`; resume surfaces mismatch before dispatch; stale-definition case in T-02 | AK-TSK-06, AK-TSK-14; `docs/04` §3; `docs/10` T-02; fixtures |
| N7 | `Money` defined once (`amountMinor` + currency; `MoneyRange` low/high minor); `CostSummary` uses `…Minor` fields and one currency; `byCategory` optional in embedded summaries; task, route-decision fixtures regenerated in minor units | `docs/04` §1, §5; fixtures |
| N8 | `SkillSupportEntry` = mechanism + `verified` + `evidence` (required only when verified); skill fixture aligned; unverified entries carry no fabricated timestamp | `docs/04` §2; `docs/05` §3; `evals/fixtures/skill-package.json` |
| N9 | Runbook §7.10 "Unauthorized action"; release gate 9 requires all ten AK-OPS-08 runbooks walked through | `docs/12` §7.10; `docs/10` §7 |
| N10 | One connector effort basis: `docs/07` §6.2 is the adapter-only subset; P8 per service = adapter days + 1–2 ew integration (placeholder), first three 5.6–10.4 ew; totals recomputed (specialists + first three ≈12–21 ew; full target ≈47–71 ew) | `docs/11` header, §10; `docs/07` §6.2 |

Fixture note: the planned executable fixture validator remains implementation work
(P0/P1), as deferred in round 1; `docs/10` §4 now names the shapes it must enforce.

## 2. Decisions for HUMAN (carried forward; not decided here)

HUMAN is not answering during the automated review; none of these blocks review. Defaults
stay in force. Round 2 added no new HUMAN decision; the list is unchanged from round 1.

| ID | Question | Default in v0.5 |
|---|---|---|
| U4 | Budgets, spend caps, concurrency caps, approval thresholds | none; proposals labelled |
| U5 | WhatsApp Business admin scope (template scope for AK-SPC-03) | messaging; admin = profile/numbers/templates |
| U6 | Rating aggregation model | configurable, no weights |
| U7 | Telephony / WhatsApp / image / video vendors | contracts only; candidates unnamed |
| U8 | Existing team exports available | drafts, `needs-human-review` |
| U9 | Who approves observer activation and template upgrades | HUMAN or explicit bot-admin |
| U10 | Log and backup retention windows (never deletes user data) | proposals only |
| U11 | Desktop/mobile in first release | web first |
| U12 | Multi-team/hosted tenancy | single environment |
| U13 | Scope of "phone calls" | outbound first; recording needs policy |
| U14 | Task run limit before human checkpoint | optional deadlines |
| U15 | Akeru analytics | off |
| U16 | Cross-auth-class cost ranking | off; operator chooses |

AKIRA-D1–D6 are settled and are not in this list. The route `role` default (N4) and the
P8 integration overhead (N10) are reversible proposals in configuration/planning, not HUMAN
decisions.

## 3. Rejected or deferred

None rejected. Deferred detail (not rejected):

- Executable fixture/schema validator (CHATGPT-4, DEEPSEEK-4, GROK-7/8): shapes are fixed
  and the validator requirement stated in `docs/10` §4; the tool is implementation work.
- The 1–2 ew per-service integration overhead (DEEPSEEK-6) is a placeholder; it is
  re-estimated at P8 start rather than decomposed further without measured velocity.
- The declared `assets/` directory still does not exist; no requirement depends on it.

## 4. Traceability of every finding

| Finding | Disposition |
|---|---|
| CHATGPT-1, DEEPSEEK-1, GROK-1 | accepted → N1 |
| CHATGPT-3 | accepted → N2 |
| GROK-2 | accepted → N2 |
| DEEPSEEK-2 | accepted → N3 |
| GROK-3 | accepted → N3 |
| GROK-4 | accepted → N4 |
| CHATGPT-2, GROK-5 | accepted → N5 |
| DEEPSEEK-3, GROK-6 | accepted → N6 |
| DEEPSEEK-4, GROK-7 | accepted → N7 |
| CHATGPT-4 | accepted → N7 (byCategory) and N8 (support entry) |
| GROK-8 | accepted → N8 |
| DEEPSEEK-5, GROK-9 | accepted → N9 |
| DEEPSEEK-6 | accepted → N10 |

All 19 findings are accounted for (CHATGPT 4, DEEPSEEK 6, GROK 9).
