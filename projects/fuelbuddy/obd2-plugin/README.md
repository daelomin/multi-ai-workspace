# obd2-plugin spec — multi-AI review

Review rounds for `spec.md`. General rules: `CONTRIBUTING.md`; loop rules: `generic/REVIEW_LOOP_GUIDELINE.md`.

## Current round

**Round 2** — reviewing `spec.md` **v0.2**. Reviews go in `reviews/round-2/`.
*(Updated by CLAUDE at each consolidation.)*

| File | What it is |
|---|---|
| `spec.md` | The specification. Only CLAUDE edits it, when consolidating a round. |
| `reviews/round-N/<AGENT>.md` | One review per AI per round. Each AI writes only its own file. |
| `decisions.md` | Decisions HUMAN has settled (optional). Reviewers treat them as fixed. |
| `reviews/round-N/CONSOLIDATION.md` | CLAUDE's merge of round N. |

**Stop rule:** iteration ends when a round produces no `blocking` or `major` findings, or when HUMAN stops it.

## Review format

```markdown
### <AGENT>-<n> · <short title>

- **Section:** §x.y (or "general")
- **Type:** error | gap | risk | inconsistency | suggestion | question
- **Severity:** blocking | major | minor
- **Finding:** what is wrong or missing, in two or three sentences.
- **Proposed change:** the exact text or rule to add, change or delete.
- **Evidence:** source URL + date checked, or "reasoning only".
- **Confidence:** high | medium | low
```

Rules: facts need sources; don't invent identifiers; propose, don't decide (safety, legal and scope are HUMAN decisions);
don't edit `spec.md` or another review. End with a short **Top 3**. A review ends with `Result: complete`, and has
findings or `Findings: none`.
