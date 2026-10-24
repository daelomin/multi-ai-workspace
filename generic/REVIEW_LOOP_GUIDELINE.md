# Starting a spec review loop — guideline

**Prefer the guided version:** run `generic/loop_wizard.py` and open the URL it prints; the assistant asks what you want and runs each step for you.

Follow this when you (any agent) set up a new multi-AI review loop for a spec. The loop engine is `generic/specs_review_loop.py`; the launcher is `generic/run_review_loop.sh`. Do not copy or fork either into a project folder.

## 1. Folder structure

One folder per spec, under `projects/<project>/<spec-name>/`:

```
projects/<project>/<spec-name>/
├── spec.md              # the specification (single writer: CLAUDE, at consolidation)
├── README.md            # round state + review rules (required, see §2)
├── decisions.md         # HUMAN-settled decisions, optional but recommended
├── reviews/
│   └── round-N/
│       ├── <AGENT>.md          # one file per reviewer, written only by that agent
│       └── CONSOLIDATION.md    # CLAUDE's merge of the round
└── automation/
    ├── .gitignore       # contains `logs/`
    ├── logs/            # created by the loop, never committed
    └── run_review_loop.sh   # optional thin wrapper (see §5)
```

Everything else (launcher, engine, tests) stays in `generic/`. Nothing goes at the repo root (`CONTRIBUTING.md`).

## 2. Required content

- **`spec.md`** — first 500 characters contain `version X.Y` (e.g. `Version 0.2`); the loop reads it for prompts and commit messages.
- **`README.md`** — must contain a line `**Round N**` under a "Current round" heading (N = the round to run next; the loop refuses to start without it). It also holds the review format, rules for reviewers and the stop rule. Copy the FuelBuddy README as the template (`projects/fuelbuddy/charging-diagnostic/README.md`) and replace names and links.
- **`decisions.md`** (optional) — HUMAN decisions with ids (`<PREFIX>-D1`, …). If the file exists, the loop adds the rule "decisions are fixed, do not re-raise them as blocking/major" to the prompts.
- Review findings use the shape defined in the README (`### <AGENT>-<n> · title`, `**Severity:** blocking|major|minor`, …). A review file is complete only if it ends with `Result: complete` and has findings or `Findings: none`.

## 3. Roles and ownership

| Who | Writes |
|---|---|
| CHATGPT, DEEPSEEK, GROK (CURSOR optional) | only their own `reviews/round-N/<AGENT>.md` |
| CLAUDE | `spec.md`, `reviews/round-N/CONSOLIDATION.md`, README "Current round" |
| HUMAN | `decisions.md` (agents may record it only when HUMAN decided), merges the PR |

Reviewers never edit `spec.md` or another agent's review. Round 1 reviews are independent (do not read the others first).

## 4. Before you start

1. Read `MASTER.md`, `TODO.md`, recent `CHANGELOG.md` (per `CONTRIBUTING.md`).
2. Create the folder from §1 on a clean tree; commit as `<YOUR NAME>: …` and append a `CHANGELOG.md` entry.
3. Pick `<name>` (label used in commits/prompts, e.g. `FuelBuddy`) and the branch. Default branch is `agent/loop/<name lower-case>-review`; never run on `main`.
4. Run the preflight and fix every failing backend before a live round:

```bash
generic/run_review_loop.sh projects/<project>/<spec-name> <Name> preflight
```

## 5. Running

```bash
generic/run_review_loop.sh projects/<project>/<spec-name> <Name> [branch] one    # a single live round
generic/run_review_loop.sh projects/<project>/<spec-name> <Name> [branch] full   # up to 5 rounds
```

Optionally add `automation/run_review_loop.sh` as a 3-line wrapper that execs the generic launcher with your values (see FuelBuddy's). The working tree must be clean; the DeepSeek key comes from the environment or a hidden prompt, never from a file in the repo.

The loop commits and pushes after every step as `<AGENT>: …`, skips steps whose file already exists, and stops when a round has no `blocking`/`major` finding or after `--max-rounds`. Only one loop runs per project (lock in `automation/logs/.loop.lock`).

## 6. Rules while it runs

- Do not hand-edit files in `reviews/round-N/` of a running loop; stop it first.
- HUMAN decisions are never waited for: carry open ones forward in the CONSOLIDATION and let the next round proceed.
- Never delete reviews, logs or branches to "retry"; ask HUMAN first (`CONTRIBUTING.md`, global no-delete rule).
- If the engine needs a change, change `generic/specs_review_loop.py` and its tests (`python3 -m unittest discover -s generic/tests`), not a project copy.
- When the stop rule is met, CLAUDE writes the final CONSOLIDATION, README says `converged`, and HUMAN merges the PR.

## 7. Checklist

- [ ] Folder under `projects/<project>/<spec-name>/` with `spec.md` (version line) and `README.md` (`**Round N**`)
- [ ] `automation/.gitignore` contains `logs/`
- [ ] `decisions.md` created if HUMAN has already decided anything
- [ ] Clean tree, correct branch, CHANGELOG entry
- [ ] Preflight passes for every reviewer in use
- [ ] Generic tests pass

## 8. Monitor and chaining

Register every loop in `generic/loops.json` (copy `loops.example.json`): `id`, `project`, `name`, optional `branch`, `reviewers`, `after` (id of the loop that must be complete first) and `autostart` (default `false`).

```bash
generic/loop_monitor.py status        # table + refresh outputs, never launches
generic/loop_monitor.py tick          # also launches the next due loop
generic/loop_monitor.py watch 30      # tick every 30 s (optional unit: generic/loop-monitor.service)
generic/loop_monitor.py retry <id>    # clear a failed launch
```

- **Colours** (`generic/.monitor/index.html`, open as a file): green running, blue complete, red failed, grey pending.
- **Jarvis** (http://127.0.0.1:8777/): graph `review-loop-<id>`, one node per round and reviewer; round N+1 appears when the README advances after the consolidation of round N, and depends on `rN-CLAUDE`. Jarvis draws running blue and complete green, and an idle half-done loop orange.
- **Chaining:** a loop with `after` and `autostart: true` is launched when its predecessor is complete, nothing else runs, and the git tree is clean (loops share one checkout). A failed loop is never relaunched automatically.

## 9. Several loops at once (git worktrees)

Every new loop gets its own **git worktree**: its own folder and branch, in `~/GIT/multi-ai-workspace.loops/<loop-id>/` (override with `LOOP_WORKTREES_DIR`). Loops in different worktrees run in parallel; the engine code always runs from the main checkout, only the loop's files and git operations are in the worktree.

- **Create:** the assistant's "Create a new loop" makes the worktree and branch from your current branch, writes `spec.md` and `README.md` there and commits that folder. It records `branch` and `worktree` in `generic/loops.json`.
- **Existing loops:** a loop registered before this has no `worktree` and uses the main checkout (only one at a time). The assistant offers "Give this loop its own worktree"; the branch must not be checked out in the main checkout.
- **Your spec goes in the worktree:** edit `<worktree>/projects/<project>/<spec>/spec.md` and commit it there (the assistant's git step does it for the selected loop). The launcher refuses to run on a dirty worktree.
- **Replies go to the right branch:** the engine commits and pushes inside its own worktree, so each review lands on that loop's branch. Git refuses the same branch in two worktrees, and the launcher lock is per worktree.
- **Limit:** at most 3 loops at once (`LOOP_MAX_PARALLEL`); they share your OpenAI, DeepSeek, Cursor and Anthropic accounts and run up the bill in parallel.
- **Merging branches:** `.gitattributes` sets `CHANGELOG.md merge=union`, so parallel loops that each add a changelog entry merge without conflicts.
- **Cleanup:** worktrees are never removed automatically. When a loop is merged: `git worktree remove <path>` (HUMAN decision).

## 10. Cost per step

Every step records its cost in `automation/logs/r{n}-{step}.timing.json` (`cost_usd`, `cost_basis`), shown on the Jarvis nodes, the chips and as a round total on the cards:

| Step | Cost | Basis |
|---|---|---|
| DEEPSEEK | token counts x DeepSeek list prices (peak / off-peak, Beijing time), converted at `CNY_USD` (default 0.14, an assumption: set today's rate) | the only per-token API key |
| CHATGPT | Codex's estimate from its session file | subscription-equivalent (ChatGPT login) |
| CLAUDE | Claude Code's `total_cost_usd` | subscription-equivalent (claude.ai login) |
| GROK | not reported by Cursor, flagged as missing in the round total | Cursor plan |

Claude Code's own cost figure for DeepSeek runs is not used: it prices the tokens with another table. DeepSeek prices live in `DEEPSEEK_PRICES` (override with `DEEPSEEK_PRICES_JSON`); they were read on 2026-10-21 and may change.

## 11. Choose a workflow template before starting

The wizard offers two templates, stored in `generic/templates/`:

| Template | Input and output | Stop rule |
|---|---|---|
| `spec-review` | Review an implementation spec; Claude merges accepted corrections and bumps its version. | No blocking/major findings (existing behavior). |
| `option-debate` | Compare proposed options; every reviewer proposes, challenges every peer, then responds; Claude moderates and recommends one choice with arguments. | Always stop after the debate for HUMAN's choice, regardless of severity counts. |

Existing projects without `workflow.json` keep `spec-review`. For an option debate, add `workflow.json` with `{"template": "option-debate", "phase": "options"}` and use the corresponding `readme.md` template. Never edit or bump the input proposal in this phase. Prompts for independent proposals, peer challenges, responses and consolidation are separately editable Markdown templates. Every pass uses distinct files and logs; resume preserves completed passes. The monitor shows all debate passes and an `awaiting_choice` state, which does not unlock chained implementation loops.

This option-debate rule overrides §6's instruction to proceed without HUMAN decisions: choosing the primary implementation is an explicit gate. No full specifications before the choice. After HUMAN explicitly selects, record it in project `decisions.md`, switch workflow to `{"template": "spec-review", "phase": "specification", "human_choice": "<actual HUMAN choice and decision reference>"}`, remove the README waiting marker and advance to the next round. Then write/review the full specification of that selected option. AI recommendations never count as HUMAN selection.

Use new rounds to change an existing loop's purpose; preserve earlier reviews and logs. Do not reuse spec-review outputs as completed option-debate passes.
