# Round 1 consolidation — Akira specification

**Consolidator:** CLAUDE · **Input:** `spec.md` v0.3 · **Output:** `spec.md` v0.4 (2026-10-25)
**Reviews:** `CHATGPT.md` (8 findings), `DEEPSEEK.md` (16), `GROK.md` (14) — 38 findings.
**Previous consolidation:** none (round 1; no round-0 consolidation exists in this loop).

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified** — the provider reported no served model |

GROK's findings are weighted as evidence only where independently confirmed by a second
reviewer or by reading the cited text; every GROK finding below was either corroborated
or checked against the cited document section.

## Outcome

Every HUMAN decision in `decisions.md` (AKIRA-D1–D6) was already applied in v0.3;
there was no remaining "Pending HUMAN decision" passage, so nothing changed from
`decisions.md`. Round 1 produced consensus **major** findings, all accepted: backup
pruning (3/3 reviewers), server-callable hard delete (2/3), snapshot-restore replay (2/3),
quota recorded as a capability failure (2/3), mixed-unit cost totals (2/3), plus single-
reviewer majors on mid-stream retry and task resume transitions. No finding was rejected.
Round 2 reviews v0.4.

## 1. Accepted and merged

| ID | Change | Where |
|---|---|---|
| M1 | Backup is append-only: fresh generation per run, no deletion flags, removal only by HUMAN-named operation; new test T-13 | AK-OPS-16; `docs/12` §5.2; `docs/10` T-13 |
| M2 | Direct `bot.delete` rejected unless it carries purge guards; server-level test | AK-OPS-17; `docs/05` §1.5; `docs/02` B-33; `docs/10` T-12, S-10; `docs/11` P0 |
| M3 | Recovery quarantine for restore/rollback (dispatch, routines, outbound off; fence original; reconcile interval; HUMAN block when unprovable); tests T-14, F-16 | AK-OPS-15; `docs/12` §3.4, §5.3; `docs/10` |
| M4 | Availability separated from capability (`meetsFloor` vs `available`); below-skill-floor route is `meetsFloor: false`; fixtures and wireframes corrected | AK-RTE-13; `docs/04` §3, §4.2; fixtures; `docs/06` §4, §8 |
| M5 | Cost summaries keep per-currency, per-provenance subtotals; combined figure labelled "not spend"; routing ranks within auth class (cross-class via labelled comparison unit, default off, register item U16) | AK-ACC-04/05, AK-TRG-10; `docs/09` §1.6–1.7, §4a; `docs/04` §5; fixtures; `docs/06` §7 |
| M6 | `coordination` category added; overhead = review + coordination + observer; delivery + overhead = exclusive ($2.67 + $0.45 = $3.12); legacy category map | AK-ACC-02/07/14; `docs/09` §2–4; `docs/04` §5, §7 |
| M7 | Failure after a dispatched external action is `interrupted`/`failed_unknown`, never `failed_network`; F-03 revised | AK-RTE-12; `docs/04` §4.2; `docs/10` F-03 |
| M8 | Task state table gains resume and attempt-outcome edges; `not-ready` blocks only specification-led/below-floor routes; "assessment override" removed | AK-TSK-01; `docs/04` §4.1; T-02, T-10 |
| M9 | Coverage formula parenthesised with a `subscription` bucket and zero case; CPAT denominator counts distinct accepted tasks; no double-counted overhead | AK-ACC-14; `docs/09` §8–9; `docs/04` §5 |
| M10 | Late telemetry is a superseding effective snapshot of all known token/cost fields | AK-ACC-09; `docs/09` §7 |
| M11 | Traceability: AK-SKL-13/14 rows + T-15; phase column uses backlog P0–P10; requirement count 209; footer version; AK-OPS-01..17 | `docs/10` §5; spec §0, footer |
| M12 | Fixtures: `schemaVersion` everywhere; route-decision, task (unit split, overhead, evidenced readiness) and skill-package corrected; semantic-invariant validation required | `evals/fixtures/*`; `docs/10` §4 |
| M13 | Verification is orthogonal to skill mechanism (`verified` flag + evidence, including `prompt-injected`) | AK-SKL-04; `docs/05` §3; skill fixture |
| M14 | Readiness: nine named criteria each with evidence link; S2 aligned | AK-TRG-06; `docs/04` §4.3; `docs/15` S2; task fixture |
| M15 | Silence code set identical to AK-COL-05; direct question cannot be silent | AK-COL-05; `docs/08` §3.2 |
| M16 | Dispute resolver distinct from rating author and disputant | AK-RAT-05; `docs/08` §5.4; `docs/04` inv. 7; `docs/05` §1.4; T-07 |
| M17 | Export and restore audited | AK-SEC-08; `docs/05` §1.5; S-11 |
| M18 | Vertical slice uses connector-free S8 `data-extract`; S11 stays conditional; S11–S14 get triggers and route support; fixture paths marked planned | `docs/15` §3, §5; `docs/11` §13 |
| M19 | P3 cost-estimate prerequisite delivered with P2 | `docs/11` §5 |
| M20 | Rework removed from the 1–5 anchor table; averaged only over numeric criteria | `docs/08` §5.2 |
| M21 | Maintenance effort re-summed (≈4.75–7.75 ew/quarter, placeholder) | `docs/11` §15 |
| M22 | Default room rule is `mention`; `lead-bot` carries Akeru's behaviour; AK-SPC-03 cites U5; secret-leak cross-reference → §7.6 | AK-COL-02, AK-SPC-03; `docs/08` §2.3; `docs/12` §4 |

## 2. Decisions for HUMAN (carried forward; not decided here)

HUMAN is not answering during the automated review; none of these blocks review. Defaults
stay in force.

| ID | Question | Default in v0.4 |
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
| U16 | Cross-auth-class cost ranking (new in v0.4) | off; operator chooses |

AKIRA-D1–D6 are settled and are not in this list.

## 3. Rejected or deferred

None rejected. Deferred detail (not rejected):

- CHATGPT-7 "validate semantic invariants" — specified as a requirement on fixtures
  (`docs/10` §4); an executable validator belongs to implementation (P0/P1).
- Planned skill fixture directories (`evals/fixtures/skill-*/`) are created with each
  skill in P4, not in this specification; they are labelled planned.
- The declared `assets/` directory does not exist; no requirement depends on it.

## 4. Traceability of every finding

| Finding | Disposition |
|---|---|
| CHATGPT-1, DEEPSEEK-1, GROK-1 | accepted → M1 |
| DEEPSEEK-2, GROK-2 | accepted → M2 |
| CHATGPT-2, GROK-3 | accepted → M3 |
| DEEPSEEK-3, GROK-6 | accepted → M4 (and M13 for skill floor) |
| CHATGPT-3, DEEPSEEK-5, GROK-7 | accepted → M5 |
| DEEPSEEK-4 | accepted → M6 |
| GROK-8, DEEPSEEK-16 | accepted → M6 (legacy map) |
| GROK-4 | accepted → M7 |
| CHATGPT-6, GROK-5 | accepted → M8 |
| CHATGPT-4, DEEPSEEK-7, DEEPSEEK-8, GROK-9 | accepted → M9 (+ M6 for overhead definition) |
| CHATGPT-5 | accepted → M10 |
| CHATGPT-8, DEEPSEEK-6, DEEPSEEK-14, GROK-10 | accepted → M11, M19 |
| CHATGPT-7 | accepted → M12 (executable validation deferred, §3) |
| DEEPSEEK-9 | accepted → M13 |
| DEEPSEEK-10, GROK-11 | accepted → M14 |
| DEEPSEEK-11 | accepted → M15 |
| DEEPSEEK-12 | accepted → M16 |
| DEEPSEEK-13 | accepted → M17 |
| DEEPSEEK-15 | accepted → M18 |
| GROK-12 | accepted → M20 |
| GROK-13 | accepted → M21 |
| GROK-14 | accepted → M22 |

All 38 findings are accounted for.
