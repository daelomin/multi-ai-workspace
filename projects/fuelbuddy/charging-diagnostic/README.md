# FuelBuddy charging diagnostic spec — multi-AI review

This folder holds the **FuelBuddy AI Charging Diagnostic System** specification and its review rounds. It is a separate project from the traffic platform in the rest of this repository; the general rules in `CONTRIBUTING.md` (identities, commit format, changelog, human approval) still apply.

| File | What it is |
|---|---|
| `spec.md` | The specification. **Current version: v0.2** (11 October 2026), as supplied by HUMAN. Only CLAUDE edits it, when consolidating a round. |
| `reviews/round-N/<AGENT>.md` | One review per AI per round. Each AI writes only its own file. |
| `reviews/round-N/CONSOLIDATION.md` | CLAUDE's merge of round N: what was accepted, what changed, and the conflicts HUMAN must decide. |

## How a round works

1. **Independent review.** Each AI reviews the current `spec.md` and writes `reviews/round-N/<AGENT>.md`. In round 1, do **not** read the other reviews first: independent reviews catch more than reviews anchored on the first one.
2. **Consolidation.** When the reviews are in, CLAUDE merges them: agreed findings go into the next spec version (v0.3, v0.4…), conflicting ones go into a decision list for HUMAN, and rejected ones are listed with the reason.
3. **HUMAN decides** the open points.
4. **Next round** on the new version. From round 2, reviewers **may** read the previous round's reviews and consolidation, and should say where they disagree with a decision.

**Stop rule:** iteration ends when a round produces no `blocking` or `major` findings, or when HUMAN stops it.

**Status of a round** is simply which files exist in `reviews/round-N/`; no separate tracker to edit.

## Review format

Every finding uses this shape, so findings from different AIs can be merged mechanically:

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

Rules for reviewers:

- **Facts need sources.** Any claim about a standard, recall, vehicle, product or law cites a source and the date you checked it. Without one, write "reasoning only" or mark it as a question.
- **Don't invent identifiers:** error codes, campaign numbers, standard clauses, part numbers. If you are not sure one exists, say so.
- **Propose, don't decide.** Safety policy, legal/privacy conclusions and scope are HUMAN decisions (human-approval rule in `CONTRIBUTING.md`).
- **Don't edit `spec.md`** or anyone else's review.
- End your review with a short **"Top 3"**: the three changes you consider most important.

## Prompt to give each AI

Replace `<AGENT>` with `CHATGPT`, `GROK`, `DEEPSEEK`, `GEMINI` or `CURSOR`, and `N` with the round number.

```text
You are <AGENT>, one reviewer in a multi-AI review of a technical specification.

Read projects/fuelbuddy/charging-diagnostic/README.md (the review rules and format)
and projects/fuelbuddy/charging-diagnostic/spec.md (the specification).
[Round 1: do not read the other files in reviews/ before writing yours.]

Review the specification critically: errors, gaps, unsafe guidance, inconsistencies,
unverifiable claims, missing requirements, and anything that would block implementation.
Use exactly the finding format in the README. Cite a source and the date checked for
every factual claim; never invent error codes, recall numbers or standard clauses.
Do not edit spec.md.

If you can write to the repository: create reviews/round-N/<AGENT>.md on a branch
named agent/<agent>/fuelbuddy-review-rN, commit as "<AGENT>: FuelBuddy spec review round N",
add a CHANGELOG.md entry at the top, and open a pull request.
If you cannot: output the whole review as one Markdown document, starting with
"# <AGENT> review — round N", so HUMAN can paste it into that file.
```

If an AI only works through chat, paste it the README and `spec.md` along with the prompt.

**CURSOR** has a narrower role (see `agents/CURSOR.md`: no external research): its review checks internal consistency only — section cross-references, field names used in one section but not defined in another, enum values that differ between sections, schema gaps.
