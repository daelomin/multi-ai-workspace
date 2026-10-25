# 09 — Token, cost and credit accounting

**Status:** draft v0.4 · **Normative:** `spec.md` §12 · **Schema:** `docs/04-data-model.md` §5.

The accounting system exists to answer three questions without lying:

1. What did this task cost, including the parts that failed?
2. Which bot, model, account and room consumed it?
3. What is measured, what is estimated, and what is unknown?

---

## 1. Principles

1. **One record, one owner.** Every usage record has exactly one owner. A parent's
   inclusive total is a query over children, never a second stored number.
2. **Append-only.** Corrections are new records (`supersedes`), not edits. Deletion is
   not an accounting operation (AKIRA-D2).
3. **Measurement before arithmetic.** A record says how it was measured before it carries
   a cost. Tokens with no price are still tokens; money with no source is not a fact.
4. **Unknown is a value.** `null` + reason, displayed as `Unavailable`, never zero.
5. **Every execution path pays its tax.** A turn that skips the ledger is a defect, even
   if the answer was good.
6. **No cross-unit equivalence.** API dollars, subscription-equivalent dollars, plan
   percentages and credits are different units. They may be shown side by side, never
   summed into one "spend" number. Every summary keeps separate subtotals per currency and
   cost provenance (§4a). Where a single figure is useful it is a *combined economic
   estimate*, labelled as such, never called spend, and always shown with its components.
7. **Routing compares like with like.** Cost-based route ranking (AK-TRG-10) runs within
   one `auth_class` by default. Ranking across classes uses one named *routing comparison
   unit* — the API-equivalent price-table estimate — only when the routing policy enables
   it (proposed default: off, so a cross-class choice is made by the operator). The
   comparison unit is displayed as "routing comparison, not spend".

---

## 2. What is recorded

| Source | Category | Measurement | Notes |
|---|---|---|---|
| Model turn (attempt) | `turn` | provider-reported or estimated | input/cache/output/reasoning where exposed |
| Tool execution | `tool` | usually zero-token lifecycle | tool's own bill (if any) recorded as units/cost |
| Delegation to another bot | `delegation` | child's records | parent link; child owns its turn records |
| Temporary worker / subagent | `tool` or `turn` with parent | same as turn | must not be hidden inside the parent's numbers |
| Routine run | `routine` | turn records + a run record | run outcome and provider failure recorded |
| Peer review / challenge | `review` | turn | reviewer's own route/account |
| Triage, discovery, spec writing, handoff | `coordination` | turn | planning overhead; not delivery |
| Observer | `observer` | turn | includes evaluation runs |
| Media generation | `media` | provider-reported units | image count / video seconds / render job |
| Telephony | `media`/`tool` | provider-reported minutes | per-call, with number and destination class |
| Messaging | `media`/`tool` | provider-reported conversations/templates | WhatsApp/Meta or BSP |
| Hosting / sandbox | `other` | configured rate | separate from inference; optional import |
| Manual correction | `*` | stated | always with reason and actor |

---

## 3. Dimensions and attribution

```
owner        bot | task | room | observer | connector
attribution  botId, taskId, attemptId, roomId, threadId, turnId,
             parentTaskId, parentUsageId
route        harness, driver, provider, model, instanceId, accountLabel
category     turn | tool | delegation | routine | review | coordination | observer
             | media | other
measurement  provider-reported | estimated | subscription-equivalent | unknown
```

**Category classes.** *Overhead* = `review` + `coordination` + `observer`. *Delivery* =
every other category (`turn`, `tool`, `delegation`, `routine`, `media`, `other`). Every
record belongs to exactly one category, so delivery + overhead = exclusive total.

**Legacy category map (migration, `docs/04-data-model.md` §7).** Akeru values map
deterministically: `turn`→`turn`, `tool`→`tool`, `routine`→`routine`,
`delegated`→`delegation`, `observer`→`observer`, `reflector`→`observer`,
`extraction`→`other`, `recall`→`other`, any unrecognised value→`other` (original value
kept in `notes`). The original string is retained so the map can be revised without data
loss. A pre-migration row keeps one valid category and counts once in exclusive totals.

**Attribution rules.**

- A turn is attributed to the bot and task it serves, even if a different account served
  it (account is a route dimension, not the owner).
- A delegated child's tokens are owned by the child task; the parent links to the child
  record. The parent does not copy the child's tokens.
- A temporary worker's usage is owned by the parent turn's attempt but carries
  `parentUsageId` and a `worker` marker so it can be subtracted when a view wants
  "exclusive of workers".
- Reviewer and observer turns are attributed to the reviewed task through
  `parentTaskId` but owned by the reviewer/observer category, so delivery cost and
  overhead can be separated.
- Room usage is the query over tasks/messages linked to the room; there is no separate
  "room meter" record to drift.

---

## 4. Worked example (normative)

Task **T-142** "Fuel Atlas page v2", parent, accepted.

| Record | Owner | Category | Measurement | Input | Output | Cost |
|---|---|---|---|---|---|---|
| use-1 attempt #1 (codex, failed quota) | task T-142 | turn | estimated | 12,000 | 1,000 | $0.31 |
| use-2 attempt #2 (claude) | task T-142 | turn | provider-reported tokens + price table | 41,000 (30,000 uncached, 11,000 cached) | 6,100 (1,200 reasoning) | $1.84 |
| use-3 attempt #3 rework (claude) | task T-142 | turn | provider-reported | 9,000 | 800 | $0.52 |
| use-4 tool: sheet.append | task T-142 | tool | zero-token lifecycle | — | — | $0.00 |
| use-5 tool: mail.send | task T-142 | tool | zero-token lifecycle | — | — | $0.00 |
| use-6 child T-143 (Stefano) | task T-143 | turn | estimated | 14,000 | 1,500 | $0.38 |
| use-7 peer review (Sarah) | task T-142 | review | provider-reported | 3,000 | 300 | $0.09 |
| use-8 observer p-12 evaluation | task T-142 | observer | provider-reported | 6,000 | 700 | $0.21 |
| use-9 triage turn (cheap route) | task T-142 | coordination | estimated | 4,000 | 400 | $0.15 |

Cost provenance per record: use-1 and use-9 price-table estimate; use-2
subscription-equivalent (Claude Max); use-3, use-7 and use-8 provider-reported; use-6
price-table estimate; use-4 and use-5 carry no cost.

**Queries.** The amounts below are the *combined economic estimate*; the unit split
follows in §4a. They are never spend.

- **Attempts only (delivery turns):** $0.31+$1.84+$0.52 = **$2.67**.
- **Exclusive T-142** (records owned by T-142, any category): 0.31+1.84+0.52+0.00+0.00
  +0.09+0.21+0.15 = **$3.12**; tokens 12,000+41,000+9,000+3,000+6,000+4,000 = 75,000 in,
  1,000+6,100+800+300+700+400 = 9,300 out.
- **Delivery-only T-142** (every category except review/coordination/observer):
  $0.31+$1.84+$0.52 = **$2.67**.
- **Overhead T-142** (review + coordination + observer): $0.09+$0.15+$0.21 = **$0.45**.
- **Delivery + overhead = exclusive:** 2.67 + 0.45 = 3.12.
- **Child T-143 exclusive:** **$0.38**, 14,000 in / 1,500 out.
- **Inclusive T-142** = exclusive T-142 + inclusive children = 3.12 + 0.38 = **$3.50**;
  tokens 89,000 in / 10,800 out.

### 4a. Unit split of the worked example (normative)

| Scope | Provider-reported charge | Price-table estimate | Subscription-equivalent | Combined economic estimate |
|---|---|---|---|---|
| Exclusive T-142 | $0.82 (use-3, 7, 8) | $0.46 (use-1, 9) | $1.84 (use-2) | $3.12 |
| Child T-143 | — | $0.38 (use-6) | — | $0.38 |
| Inclusive T-142 | $0.82 | $0.84 | $1.84 | $3.50 |
| Overhead T-142 | $0.30 (use-7, 8) | $0.15 (use-9) | — | $0.45 |

Coverage counts cost-bearing records per bucket (`reported`, `estimated`,
`subscription`, `unknown`): exclusive 3 / 2 / 1 / 0; inclusive 3 / 3 / 1 / 0; overhead
2 / 1 / 0 / 0. Zero-cost tool lifecycle records are not cost-bearing and are not counted.
The buckets sum to the cost-bearing records; a subscription record is neither "reported"
nor lost.
- **Failed-attempt cost:** $0.31 (attempt #1) — visible, included in delivery cost, not
  hidden in a separate "waste" bucket that nobody reconciles.
- **Cost per accepted task** (this task): $3.50. If T-142 had been rejected, the $3.12
  (or $3.50 with child) would still count in the denominator's numerator for the class.

The UX sketch (`docs/06-ux.md` §3) shows attempts-only $2.67, inclusive $3.50 and
overhead $0.45 (review + coordination + observer); both views are queries over these
records.
Any UI text must be generated from records, not from a hand-written sample.

**Double-counting checks (must be automated):**

1. Sum of all exclusive amounts for the team = sum of all records' costs (each record is
   counted once as exclusive).
2. Inclusive T-142 includes child T-143 exactly once; a team roll-up counts T-143 in its
   own row and does not add it again to the team total.
3. Reasoning tokens (1,200) are not added to output (6,100 include them).
4. Cached input (11,000) is not added to uncached input (30,000) as if it were extra
   input; both sum to the 41,000 total input.
5. A provider correction (e.g. cache tokens reported later) supersedes use-2's effective
   snapshot once (§7), without appending tokens twice.
6. Every record belongs to exactly one category; delivery + overhead = exclusive, and
   exclusive + child = inclusive.
7. The per-provenance subtotals sum to the combined estimate, and no summary presents the
   combined estimate without them.

---

## 5. Cost provenance

| Provenance | Meaning | Display |
|---|---|---|
| `provider-reported` | provider returned a charge or billable amount | actual charge (currency) |
| `price-table estimate` | tokens × versioned price list | estimated API-equivalent, not billed |
| `subscription-equivalent` | tokens × list price for a subscription route | "plan usage equivalent", never "spent" |
| `unknown` | no price and/or no tokens | `Unavailable` with reason |

Rules:

- A provider-reported charge always wins over an estimate for the same record; the
  estimate is retained as `supersedes` context, not displayed as a second charge.
- Price tables are versioned files with source URL and date. A model with no price entry
  is `unpriced`, counted in tokens, excluded from cost.
- Subscription routes never claim a dollar charge. They may show a plan meter if the
  provider reports one (percentage or token pool), with reset time and freshness.
- Currency conversion is explicit (rate + date), never implicit.

---

## 6. Credit and quota meters

| Source | What can be known | What cannot |
|---|---|---|
| Provider API usage endpoint | plan window, percentage, reset time (varies) | exact remaining credit for prepaid balances if not exposed |
| Provider error on request | exhausted / rate-limited / auth | exact balance |
| Akira ledger | tokens and estimated cost it produced | vendor's remaining credit |
| Prepaid balance API (where available) | balance in vendor units | conversion to other plans/accounts |

Akira displays meters with `source`, `checkedAt`, `stale` flag. It never infers "you have
$X left" from token counts. When a provider reports nothing, the UI says `Unavailable` and
the routing policy treats the route as availability-unknown, not as free.

---

## 7. Reconciliation

| Situation | Handling |
|---|---|
| Provider usage arrives after the turn | append a `correction` record that supersedes the estimate; do not edit |
| Provider reports cache tokens later | a correction is a superseding *effective usage snapshot*: it carries every token and cost field that is now known (e.g. the cached/uncached split of an input total, or tokens that were `null`). Queries select the effective revision once per logical usage record; superseded revisions stay for audit. Tokens are never summed across revisions |
| Duplicate settlement (retry/receipt) | idempotency key prevents a second record; if it slips through, a reconciliation job marks one as duplicate (audited) |
| Provider reports a charge with no token breakdown | record the charge as `provider-reported`, tokens null |
| Turn failed before usage was reported | record `unavailable` with the failure class; cost may be zero or unknown, never invented |
| Child work unknown (no usage) | parent inclusive shows a `+` floor marker |

A daily reconciliation job compares: ledger totals vs provider-reported totals where
available; unresolved `unknown` records older than a threshold; missing settlements for
attempts that ended. Discrepancies create an operator alert, not a silent fix.

---

## 8. Views and drill-down

| View | Shows | Must not |
|---|---|---|
| Task | exclusive, inclusive, overhead, failed attempts, per-category, per-attempt | hide child cost or failed spend |
| Bot | own turns, tasks it executed, reviews it gave/received, reputation context | conflate reviews given with work done |
| Room | merged tasks and messages cost | double count a task mentioned twice |
| Route | cost per accepted task, latency, failure rate | compare subscription-equivalent to API dollars as if equal (rank within an auth class, or use the labelled routing comparison unit, §1.7) |
| Account | provider-reported meter, last refresh, staleness | infer a balance |
| Observer | its own cost and evaluations | omit cost from the proposals it makes |
| Team/day | total exclusive, coverage %, unknown count | present an incomplete total as complete |

Coverage is a first-class number: `coverage = (reported + estimated + subscription) /
(reported + estimated + subscription + unknown)` over cost-bearing records, with the
unknown reasons listed. With zero cost-bearing records coverage is `n/a`, not 100% or 0%.
Example: 3 reported, 2 estimated, 1 subscription, 0 unknown → 6/6; adding 2 unknown →
6/8 = 75%.

---

## 9. Cost-per-accepted-task

```
CPAT(route, taskClass) =
  ( Σ inclusive attributable cost of all tasks of the class, any category,
    including failed attempts, rework, child work and overhead )
  ÷ number of distinct accepted tasks of the class
```

The numerator is each task's inclusive total, so overhead records are counted once (they
are already inside the exclusive total; do not add them again). Reported per cost
provenance (§4a); the combined estimate is labelled as such.

- Rejected/abandoned tasks stay in the numerator (their cost was real) and out of the
  denominator.
- Rework attempts add cost to the numerator only. An accepted task counts once in the
  denominator however many attempts it took (one accepted task with three attempts: three
  attempts of cost, denominator 1).
- Human time is not monetised by the system unless a HUMAN supplies a rate; it is shown
  as hours, not invented dollars.
- The metric is per route and task class, with sample size; a route with 3 samples is
  labelled low-confidence and cannot justify a permanent policy without review.

This metric is the input to routing calibration (`spec.md` §7) and
to the observer's evaluation.

---

## 10. Non-token costs

| Unit | Example | Basis |
|---|---|---|
| minute | PSTN call | provider rate, rounded per provider |
| message / conversation | WhatsApp | provider category (service/marketing/utility), template fees |
| image | image generation | provider per-image rate |
| video-second / job | video render | provider per-second or per-job rate |
| sandbox-hour | E2B/Daytona/Vercel/Upstash | provider rate |
| host-month | server/backup storage | HUMAN-supplied or estimated, labelled |

All use the same ledger; task totals add them with unit awareness. No "tokens per dollar"
conversion is invented for them.

---

## 11. Privacy and retention

- Usage records contain ids, counts, prices and model names, not prompt content.
- A record may reference a task/thread; deleting a task must not orphan its cost
  (AKIRA-D2: nothing is deleted). Archiving keeps the link.
- Exports include the ledger with the same ids; restore must preserve parent links or
  refuse the import (a broken parent chain is worse than a failed restore).

---

## 12. Failure modes the accounting must survive

1. A turn completes but the provider never reports usage → `unavailable`, attempt still
   counted, UI shows a floor.
2. The process crashes between provider completion and settlement → reservation
   reconciled on startup (Akeru's reservation lifecycle is the base).
3. Two servers (dev + prod) write to different databases → no cross-database sum; the
   export/merge path must dedupe by `idempotencyKey`.
4. A model is renamed mid-price-table → route key retains model id; price table version
   records which rate applied.
5. A route is removed → historical records keep their route snapshot; routing cannot use
   it for new work.
