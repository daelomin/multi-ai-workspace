# FuelBuddy charging diagnostic spec — multi-AI review

This folder holds the **FuelBuddy AI Charging Diagnostic System** specification and its review rounds. It is a separate project from the traffic platform in the rest of this repository; the general rules in `CONTRIBUTING.md` (identities, commit format, changelog, human approval) still apply.

## Current round

**Round 3** — reviewing `spec.md` **v0.4**. Reviews go in `reviews/round-3/`.
Round 1 ran on v0.2 (CLAUDE, CHATGPT, DEEPSEEK; consensus in `reviews/round-1/CONSOLIDATION.md`). Round 2 ran on v0.3 (CHATGPT, DEEPSEEK, GROK; consensus in `reviews/round-2/CONSOLIDATION.md`, which also carries the open HUMAN decisions FB-D1 … FB-D7).
*(Updated by CLAUDE at each consolidation.)*

| File | What it is |
|---|---|
| `spec.md` | The specification. **Current version: v0.4** (14 October 2026). v0.2 was supplied by HUMAN; v0.3 and v0.4 are CLAUDE's round-1 and round-2 consolidations. Only CLAUDE edits it, when consolidating a round. |
| `reviews/round-N/<AGENT>.md` | One review per AI per round. Each AI writes only its own file. |
| `decisions.md` | Decisions HUMAN has settled (FB-D ids). Reviewers treat them as fixed; CLAUDE applies them to `spec.md` at the next consolidation. |
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

## Instructions for the reviewing AI

If you were sent here with the standard prompt, follow these steps.

1. **Your identity** is your own name: `CHATGPT`, `GROK`, `DEEPSEEK`, `GEMINI` or `CURSOR`. Use it wherever this file says `<AGENT>` (in lower case for branch names).
2. **The round** is the one in *Current round* at the top of this file. Use its number wherever this file says `N`.
3. **Read** [`spec.md`](spec.md) (raw text: <https://raw.githubusercontent.com/daelomin/multi-ai-workspace/main/projects/fuelbuddy/charging-diagnostic/spec.md>).
   - In round 1, do not read the other files in `reviews/` before writing yours.
   - From round 2, read the previous round's reviews and `CONSOLIDATION.md` first.
4. **Review** the spec critically: errors, gaps, unsafe guidance, inconsistencies, unverifiable claims, missing requirements, and anything that would block implementation. Use exactly the finding format above, cite a source and the date checked for every factual claim, and never invent error codes, recall numbers or standard clauses. Do not edit `spec.md`.
5. **Deliver** your review as `reviews/round-N/<AGENT>.md`:
   - If you can write to the repository: create it on a branch named `agent/<agent>/fuelbuddy-review-rN`, commit as `<AGENT>: FuelBuddy spec review round N`, add a `CHANGELOG.md` entry at the top, and open a pull request.
   - If you cannot: output the whole review as one Markdown document starting with `# <AGENT> review — round N`, so HUMAN can add it.

**CURSOR** has a narrower role (see `agents/CURSOR.md`: no external research): its review checks internal consistency only — section cross-references, field names used in one section but not defined in another, enum values that differ between sections, schema gaps.

## Automated loop (HUMAN's laptop)

From round 2 the rounds run unattended with `generic/specs_review_loop.py`. The reviewers are **CHATGPT**, **DEEPSEEK** and **GROK** (**CURSOR** optional, consistency only); **CLAUDE** consolidates. One round is:

1. **CHATGPT** reviews through the Codex CLI (`codex exec`) and writes `reviews/round-N/CHATGPT.md`.
2. **DEEPSEEK** reviews through Claude Code pointed at the DeepSeek API, model `deepseek-v4-pro` (the script checks the model actually used). Its prompt says explicitly *"You are DEEPSEEK"*, since it runs inside Claude Code.
3. **GROK** reviews through the Cursor agent CLI (`agent`/`cursor-agent -p`), model `grok-4.7-high` (override with `GROK_MODEL`). Its prompt says explicitly *"You are GROK"*; it signs as GROK, never CURSOR (`agents/GROK.md`).
4. **CLAUDE** consolidates through Claude Code on Anthropic, model `claude-sonnet-5-5`: `CONSOLIDATION.md`, the next `spec.md` version and the *Current round* line above.

The script commits each file as `<AGENT>: …` on the branch `agent/loop/fuelbuddy-review` and pushes after every step, so the relay passes through GitHub. It stops when a round has no `blocking` or `major` finding (the stop rule), or after `--max-rounds` rounds (default 5). A step is skipped only when its file is complete (it ends with `Result: complete`, and has findings or `Findings: none`) and is pushed; a complete but unpushed file resumes at the push, and an unfinished file stops the loop for inspection. Only one loop runs at a time, and the working tree and index must be clean before each step. Tests: `python3 -m unittest discover -s generic/tests`. HUMAN decisions are not waited for during the loop: they stay in the carried-forward FB-D list, and reviewers must not re-raise them as `blocking`/`major`. HUMAN merges the branch's pull request at the end.

```bash
cd ~/GIT/multi-ai-workspace
python3 generic/specs_review_loop.py --project projects/fuelbuddy/charging-diagnostic --name FuelBuddy --preflight   # probe the backends; add --reviewers GROK --skip-consolidator to test Grok alone
python3 generic/specs_review_loop.py --project projects/fuelbuddy/charging-diagnostic --name FuelBuddy
```

The loop is generic: `--project` points it at any folder with `spec.md` and a README holding a `**Round N**` line (`decisions.md` is optional), `--name` labels commits and prompts, and `--branch` defaults to `agent/loop/<name>-review`. `generic/run_review_loop.sh <project-dir> <name> [branch] {preflight|one|full}` is the generic launcher, and `automation/run_review_loop.sh` is the thin FuelBuddy wrapper that passes these values for you. The tests live in `generic/tests/`; per-project state (logs) stays in `automation/logs/`.

Setup: the DeepSeek key is read from `DEEPSEEK_API_KEY` or from `~/.claude/settings.json`. When `~/.claude/settings.json` points Claude Code at DeepSeek, CLAUDE runs from a separate profile, `~/.claude-anthropic` (log in once with `CLAUDE_CONFIG_DIR=~/.claude-anthropic claude`, then `/login`). Logs go to `automation/logs/` (not committed).

## Standard prompt (HUMAN)

The same text for every AI and every round; it never needs editing:

```text
Read https://github.com/daelomin/multi-ai-workspace/blob/main/projects/fuelbuddy/charging-diagnostic/README.md and follow its instructions. Use your own name as your identity (CHATGPT, GROK, DEEPSEEK, GEMINI or CURSOR).
```

The repository is public, so an AI that can browse the web reads everything from that link. Only an AI that cannot browse needs this README and `spec.md` pasted in with the prompt.
