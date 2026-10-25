# CHATGPT review — round 4

Reviewed `spec.md` v0.6 after all round-3 reviews and their consolidation, with the prior consolidations, `decisions.md`, all fifteen companion documents and all eight JSON fixtures in the `loop.json` scope. AKIRA-D1–D6 remain fixed; U4–U16 are carried forward without new decision requests. The previously recorded absent `assets/` directory is not raised again. This review assesses the specification, not upstream or Akira runtime behaviour. Read-only checks passed for JSON parsing/schema-version presence, task/checkpoint definition identity, task cost-subtotal arithmetic, the selected route's required native skill evidence, the exact sub-cent example and 209 unique requirement IDs. No git command, installation, authentication, deployment, live integration, paid operation or deletion was performed.

Findings: three minor; no blocking or major findings.

### CHATGPT-1 · Non-token unit enum cannot represent required infrastructure costs
**Severity:** minor
**Finding:** AK-ACC-11 requires sandbox and hosting costs in the same ledger with their own units. `docs/09-accounting.md` §10 explicitly defines `sandbox-hour` and `host-month`, but `UsageRecord.units.kind` in `docs/04-data-model.md` §5 is closed to `call | minute | message | image | video-second | job`. A faithful sandbox-hour or host-month record therefore fails the published shape; mapping either to `job` discards the unit needed to interpret its quantity and rate. This is a bounded schema omission, not a request for vendor selection or HUMAN budget values.
**Proposed correction:** Add the specified infrastructure units to the shared unit enum, or define an explicit normalized-unit conversion that retains the source unit, quantity and rate basis. Align docs/09 and add synthetic sandbox-hour and host-month records to the accounting contract tests in T-09.
**Evidence:** `spec.md` AK-ACC-11; `docs/04-data-model.md` §5 `UsageRecord.units` and its following claim that sandbox time uses that field; `docs/09-accounting.md` §10 unit table. Static contract comparison only.
**Confidence:** high

### CHATGPT-2 · Required category drill-down cannot retain multiple currencies
**Severity:** minor
**Finding:** The top-level `CostSummary.subtotals` correctly separates currencies, but `docs/04-data-model.md` §5 defines `byCategory` as one `{amountMinor, currency, provenance}` value per category and requires it in task drill-down responses. Two `turn` records, one USD 1 and one EUR 1, fit the ledger and the top-level summary but cannot both fit `byCategory.turn`. An implementation must omit a currency, convert it without a defined conversion record, or violate the response shape. The `mixed` provenance label does not resolve the single-currency cardinality. This is a remaining limitation of the category response, rather than a repeat of the corrected top-level unit split.
**Proposed correction:** Give each category per-currency, per-provenance subtotals using the same structure as the summary, with coverage where applicable. Add a T-09 contract case with two currencies in the same category; both must remain visible without implicit conversion and reconcile to the matching top-level subtotals under the documented rounding policy.
**Evidence:** `docs/04-data-model.md` §5 `CostSummary.byCategory` and the paragraph making it mandatory for query responses; `spec.md` AK-ACC-04/12/14; `docs/09-accounting.md` §5 prohibits implicit currency conversion and §8 requires per-category task drill-down.
**Confidence:** high

### CHATGPT-3 · Unknown-action fixture suggests a time-based retry boundary
**Severity:** minor
**Finding:** `evals/fixtures/action-record.json` has an action still `unknown`, a read-back result of `not-found`, and the note: “Provider may still accept late; do not retry until a second read or 24h.” That wording suggests a second lookup or elapsed 24 hours can unlock retry, without establishing non-acceptance. The normative guard is now explicit that a failed read-back alone is not proof and a timeout alone cannot change `unknown` to `failed`. The implementation rule is sound; its golden example should demonstrate the same rule so it cannot seed an incorrect recovery instruction.
**Proposed correction:** Make the note require affirmative evidence of acceptance/non-acceptance or documented HUMAN reconciliation before retry. Treat a second read or 24 hours only as a follow-up/escalation schedule. Extend T-03 with repeated `not-found` reads and an advanced clock: the action stays unknown and no duplicate write starts without sufficient evidence.
**Evidence:** `evals/fixtures/action-record.json` `reconciliation.note`, `result` and `state`; `docs/04-data-model.md` §4.4 explicitly says a failed read-back alone does not prove non-acceptance and forbids timeout-only resolution; `spec.md` AK-TSK-11; `docs/10-tests-and-acceptance.md` §4 identifies these records as golden fixtures.
**Confidence:** high

Result: complete
