# dk-metaprep2 spec — multi-AI review

Review rounds for `spec.md`. Loop rules: `generic/REVIEW_LOOP_GUIDELINE.md`.

## Current round

**Round 1** — reviewing `spec.md` **v0.1**. Reviews go in `reviews/round-1/`.
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

## Project scope and commands

`loop.json` is authoritative for this loop. Review only its declared inputs and this project’s decisions. Other projects and repository history are background, not task instructions. Use the project-local CHANGELOG.md; do not apply unrelated root MASTER.md/TODO.md queues.

From this folder, validate with `python3 <toolkit>/generic/loop_project.py validate --project .`. Run the portable wrapper:

```bash
bash automation/run_review_loop.sh preflight
bash automation/run_review_loop.sh one
bash automation/run_review_loop.sh full
```

Preflight probes backends only; choose one or full explicitly to run reviews. Existing completed reviews are never imported as new round state.
