# Round 3 consolidation — Akira specification

**Consolidator:** CHATGPT · **Started by:** CLAUDE · **Input:** `spec.md` v0.5
**Output:** `spec.md` v0.6 (2026-10-25)
**Reviews:** `CHATGPT.md` (3 minor), `DEEPSEEK.md` (1 major, 8 minor),
`GROK.md` (1 major, 8 minor) — **21 findings: 2 major, 19 minor, no blocking**.
**Previous consolidation:** `reviews/round-2/CONSOLIDATION.md` (19 findings).

## Reviewer provenance

| Reviewer | Requested | Served | Status |
|---|---|---|---|
| CHATGPT | gpt-6.1-sol | gpt-6.1-sol | verified |
| DEEPSEEK | deepseek-flash | deepseek-flash | verified |
| GROK | grok-4.7-medium | not reported | **unverified** — provider reported no served model |

GROK is the only unverified reviewer. Every finding was checked against its cited
requirements/contracts; corroborating review IDs are recorded below. The extra
error-to-outcome ambiguity in GROK-5 was independently confirmed in docs/04 §4.2 and
docs/05 §6. Model provenance does not substitute for evidence.

## Outcome and recovery handoff

CLAUDE exhausted its weekly credits midway through this consolidation, leaving partial
edits already marked v0.6. HUMAN explicitly handed completion to CHATGPT. Those edits were
read and assessed in place, retained where sound and completed consistently; **this is the
same v0.6 consolidation, not v0.7**. The stale v0.5 footer and README were corrected.
No git command was run; no reviewer report, decisions, manifest, agent or runtime code was
modified. Existing artifacts and historical activity remain preserved.

All 21 findings are accepted, grouped into 11 changes below. The two major findings
(DEEPSEEK-1 and GROK-1) independently identify the same unsafe write-before-ledger crash
window. They remain two major review findings even though one correction addresses both.
**Review convergence is not claimed. Round 4 reviews v0.6 in `reviews/round-4/`.** No
reviewer or subsequent round was run as part of this consolidation.

`decisions.md` contains only **AKIRA-D1–D6**. All six are already applied: Akeru/Akira
base/name (§2.1), preservation/archive-only rule (§2.1, §17), specification-only authority
(§2.1, AK-SPC-08), Linux single-node systemd user service (A1, §17, docs/12), personal-use
subscription permission with per-route prohibition handling (A2, AK-RTE-04), and private
internal distribution (A8, §17). No matching “Pending HUMAN decision” passage remains.
U1–U3 are resolved by AKIRA-D4–D6 and are excluded from the open list. There is no new
HUMAN answer to apply or infer; U4–U16 stay open under their existing Akira register IDs.

## 1. Accepted and merged

| ID | Evidence and reason for acceptance | Change and location |
|---|---|---|
| P1 | AK-TSK-10/14 previously allowed a call before durable `dispatched`, while recovery inspected only dispatched/unknown records; a crash could conceal a completed effect in `intent`. | Require durable `intent → dispatched` before connector invocation. Dead-attempt `intent` blocks dependent work/new attempts unless reconciled or proven never sent. AK-TSK-10/14; docs/04 §4.1, §4.2, §4.4, §8; docs/05 §5; T-03/F-18 and traceability/release gate in docs/10. |
| P2 | AK-SEC-09 and AK-OPS-15 required controls for which docs/05 had no commands. | Add `dispatch.pause/resume` and per-item `quarantine.release`: HUMAN Operator authorization, named scope/item, durable guards, evidence, reason and audit. Resume cannot clear quarantine; release cannot clear a pause. Pauses gate writes from running attempts too. Docs/05 §1.5, AK-SEC-09, docs/12 §5.3/§7.7, T-14 safety-control tests. |
| P3 | Route records omitted auth class/options/provenance despite AK-RTE-02; the lowest-cost role default could compare incompatible costs and gave no overlap rule. | Define shared RouteSnapshot and RouteOption; candidates/usage/start input carry authClass, options, provenance. Default compares same auth class, cost unit and currency; unique cheapest requires its upper bound below all peers' lower bounds, otherwise advanced. Cross-class comparison remains U16/off; explicit role policy has a recorded basis. AK-RTE-02, AK-TRG-07; docs/04 §3/§4.3/§5, docs/05 §2, docs/09 §3; route/task/usage fixtures; T-10. |
| P4 | Generic `support: assumed` could not establish a per-skill native-verified floor; the Codex example contradicted the package support record. | Replace generic support with per-required-skill SkillSupportEntry input; capabilityFloor names requiredSkills. Preserve unverified Codex support and set meetsFloor false independently of its exhausted quota. No verification evidence is invented. Align task triage candidates with route-decision and skill-package examples; docs/04 §3, docs/10 §4/T-10. |
| P5 | “Owner's own turn usage” omitted overhead in the normative $3.50 example; CPAT's accepted-task wording could count an accepted child again. | Inclusive = owner's exclusive records in every category + exclusive descendants once. CPAT denominator = accepted roots only, including route attribution rules; child acceptance adds no denominator. AK-ACC-05/14, docs/09 §9, T-09. Worked arithmetic stays exclusive $3.12, overhead $0.45, child $0.38, inclusive $3.50. |
| P6 | Per-turn integer cents can turn 100 × $0.004 into $0 or $1 rather than $0.40. | ExactMoney uses arbitrary-precision base-10 coefficient string + scale + currency; token-price products retain source digits. Sum effective records exactly, round half to even once at subtotal/display boundary. Summary/proposal Money remains minor-unit boundary data; never re-sum summaries as ledger truth. AK-ACC-04; docs/04 §1/§5/§7, docs/09 §5, usage fixture, T-09. |
| P7 | Observer expected cost and cost delta were decimal scalars with no currency despite the shared Money contract. | Retain CLAUDE's conversion to Money: expected cost USD 120 minor units; cost delta USD 34. Type both in docs/08 §6.2 and include ObserverProposal money in docs/10 §4 validation requirements. |
| P8 | The closed level set had no representation for a verified projected mechanism. | Add projected-verified and derive labels from mechanism + verified; native-verified alone satisfies a native floor. Prompt injection keeps its mechanism label plus explicit verification status/evidence. Unsupported cannot be verified. AK-SKL-04, docs/04 §2, docs/05 §3, docs/15 §4. |
| P9 | Eight codes could not map one-to-one onto six silence clauses. | Seven canonical codes, every code maps to one clause and every clause has a code; quiet_hours/policy_hold share the final clause. Preserve historical not_addressed as a decode alias of no_evidence with the same direct-address guard; no artifact deletion. AK-COL-05, docs/08 §3.2; policy-table test in docs/10. |
| P10 | Fresh checkpoint export wrote under an uncreated directory; per-file hashes could not represent empty/absent items; AK-OPS-04 omitted workspace restoration scope. | Align the seven-item list, including encrypted/re-entered secrets and workspace repositories/refs/bundles. Create checkpoint destination first, check list/bundle/verification failures, distinguish no-workspace/no-ref cases. Structured seven-entry manifest includes tree inventories, checksums or absent reasons; required missing sources are incomplete. AK-OPS-04/16; docs/12 §5.1–5.2; T-13. |
| P11 | Fault table mixed enum outcomes with watchdog, action, delivery and quarantine assertions; the unconditional “exactly one” mapping contradicted the external-effect override. | Every fault row has result kind(s); enum checks apply only to actual attempt outcomes. Deterministic override: no provider terminal event → interrupted; terminal error with unestablished action acceptance → failed_unknown. Docs/04 §4.2, docs/05 §6, docs/10 §3; all 18 rows have six columns. |

### Assessment of partial edits

CLAUDE's write-ahead ordering, safety commands, route metadata/skill entries, accounting
formula corrections, observer Money, projected-verified and silence mapping were retained
and completed. CHATGPT repaired the partly converted fault table and finished the backup
procedure/manifest contract. The earlier crash-test wording tried to accept a send while
blocking the very append now required before the call; T-03/F-18 now separately test
pre-append, post-append/pre-call, accepted/pre-result and legacy bad-order recovery.

CLAUDE's fixed six-decimal `amountMicro` proposal was refined into variable-scale exact
fixed point: six places handle the review example but cannot represent every possible
price-table product. The new shape retains all source digits without inventing provider
precision. Its earlier synthetic Codex verification entry was replaced by the package's
existing unverified state, with the floor result corrected; task triage copies were
updated too. The fixture's one specification-led candidate is below floor and explicitly
policy-assigned, not selected by cross-class cost ranking; both overlapping subscription
candidates remain advanced. Roles never waive the floor.

No new requirement IDs were needed: the specification still has 209 requirements.

## 2. Decisions for HUMAN (single carried-forward open list)

These are the existing **Akira project register IDs** from docs/13, not new AKIRA-D
settlements. HUMAN is not answering during automated review. No item is decided here or
blocks the next review. Defaults are reversible proposals, not approvals.

| ID | Question | Default in v0.6 |
|---|---|---|
| U4 | Budgets, spend caps, concurrency caps, approval thresholds | no HUMAN-set values; proposals labelled/configurable |
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

AKIRA-D1–D6 are settled, excluded from this list, and not reopened. U1–U3 remain
historically resolved in docs/13. No new HUMAN decision was introduced in round 3.

## 3. Rejected or deferred (with reasons)

**No finding rejected.** Implementation remains deferred, not its specification:

- The executable schema/fixture validator remains P0/P1 work, as in rounds 1–2. This
  completion uses read-only draft-contract checks, not a claim that production decoders
  exist. New fields, invariants and negative tests are specified in docs/10 §4.
- Backup encryption, structured-manifest generation and packaging are P10 work. Docs/12
  §5.2 explicitly labels its checked procedure as an outline, not a runnable complete
  backup program. No backup or git export was executed.
- The reviewers' “send before dispatched” crash is forbidden by the accepted ordering;
  retain it as a legacy/fault-injected recovery case rather than an allowed normal path.
- No new prompt-injected-verified display enum is needed: verification is already
  orthogonal and explicitly displayed (P8). A verified projection has its own new label.
- `assets/` remains absent, as previously recorded; no requirement depends on a new asset.
  Planned skill fixtures remain planned rather than being invented or executed here.

## 4. Traceability of every finding

| Finding | Severity | Disposition and evidence-based correction |
|---|---|---|
| CHATGPT-1 | minor | accepted → P10; docs/12 §5.2 lacked checkpoint mkdir/checked exports |
| CHATGPT-2 | minor | accepted → P11; docs/10 §3 heterogeneous result column |
| CHATGPT-3 | minor | accepted → P6; docs/04 §1 cents lost sub-cent products |
| DEEPSEEK-1 | major | accepted → P1; AK-TSK-10/14 write-ahead/recovery gap |
| DEEPSEEK-2 | minor | accepted → P2; docs/05 §1.5 omitted required controls |
| DEEPSEEK-3 | minor | accepted → P3; route shape and docs/04 §4.3 ranking guard |
| DEEPSEEK-4 | minor | accepted → P4; candidate support not a skill-floor input |
| DEEPSEEK-5 | minor | accepted → P5; AK-ACC-05/14 versus docs/09 §4/§9 |
| DEEPSEEK-6 | minor | accepted → P7; docs/08 and observer fixture decimal money |
| DEEPSEEK-7 | minor | accepted → P8; AK-SKL-04 missing projected-verified |
| DEEPSEEK-8 | minor | accepted → P9; AK-COL-05/docs/08 cardinality mismatch |
| DEEPSEEK-9 | minor | accepted → P10; AK-OPS-04/16 versus seven-item restore set and per-file manifest |
| GROK-1 | major | accepted → P1; corroborates DEEPSEEK-1, same durable-append window |
| GROK-2 | minor | accepted → P3; mixed auth classes/overlap without recordable guard |
| GROK-3 | minor | accepted → P4; no per-skill floor evidence input |
| GROK-4 | minor | accepted → P10; confirms missing checkpoint destination |
| GROK-5 | minor | accepted → P11; result kinds plus unconditional mapping contradiction |
| GROK-6 | minor | accepted → P5; inclusive formula drops all non-turn categories |
| GROK-7 | minor | accepted → P6; repeated sub-cent synthetic arithmetic |
| GROK-8 | minor | accepted → P9; eight-code/six-clause false bijection |
| GROK-9 | minor | accepted → P8; verified projected state unrepresentable |

All **21** findings are accounted for: CHATGPT 3, DEEPSEEK 9, GROK 9.

## 5. Verification and limits

CHATGPT read README, spec, decisions, loop.json, the prior consolidations, all three
completed round-3 reviews, all 15 companion documents and all eight JSON fixtures. Static
checks passed for JSON parsing/schema-version presence, required draft-shape fields,
route auth/options/provenance, required-skill evidence and floors, task/route/package
consistency, task/checkpoint revision identity, nine evidenced readiness criteria,
observer Money, exact usage cost, per-provenance totals and worked-example arithmetic.
Precision checks include 100 × USD 0.004 = USD 0.40, sub-micro products and half-even ties.
All 18 fault rows have six columns, and all 209 unique requirement IDs retain test-suite
coverage. These are document/fixture checks, not an executed Akira acceptance suite or a
full implementation schema validator. No provider, connector, backup, deployment,
reviewer invocation, deletion or git operation was performed.

**Completion attribution:** CHATGPT completed CLAUDE's interrupted round-3 consolidation.
