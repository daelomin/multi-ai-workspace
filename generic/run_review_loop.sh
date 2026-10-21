#!/usr/bin/env bash
# Generic spec review loop launcher (wraps generic/specs_review_loop.py).
# Usage: run_review_loop.sh <project-dir> <name> [branch] {preflight|one|full}
#   <project-dir>  folder with spec.md + README.md, e.g. projects/fuelbuddy/charging-diagnostic
#   <name>         commit/prompt label, e.g. FuelBuddy
#   [branch]       default agent/loop/<name lower-case>-review
#   preflight      probe all backends, no spec changes
#   one            one live round (CHATGPT,DEEPSEEK,GROK), max-rounds 1
#   full           up to 5 rounds
# Per-project wrappers (projects/<p>/.../automation/run_review_loop.sh) just call this with their values.
# LOOP_WORKTREE=<dir>  run in that git worktree (its own branch and files) instead of the main checkout, so several
#                      loops can run at once. The engine code always comes from the main checkout.
# The DeepSeek key is read from the environment, or prompted (hidden, never written to disk).
set -euo pipefail

REPO="${REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LOOP="$REPO/generic/specs_review_loop.py"
if [ "$#" -lt 3 ] || [ "$#" -gt 4 ]; then
  echo "usage: $0 <project-dir> <name> [branch] {preflight|one|full}" >&2; exit 2
fi
PROJECT="$1"; NAME="$2"; shift 2
if [ "$#" -eq 2 ]; then BRANCH="$1"; shift; else BRANCH="agent/loop/$(printf '%s' "$NAME" | tr '[:upper:]' '[:lower:]')-review"; fi
ROOT="${LOOP_WORKTREE:-$REPO}"
PROJECT_ARGS=(--project "$ROOT/$PROJECT" --name "$NAME" --branch "$BRANCH")

# FAST=1 -> Codex Fast service tier (about 2x speed, 2x price) and Grok 4.7 medium-fast.
# DeepSeek and the Anthropic consolidator have no fast variant, so they are unchanged.
if [ "${FAST:-0}" = "1" ]; then
  export GROK_MODEL="${GROK_MODEL:-grok-4.7-medium-fast}"
  export CODEX_SERVICE_TIER="${CODEX_SERVICE_TIER:-fast}"
fi

# --- configuration (override by exporting before running) ---
export GROK_MODEL="${GROK_MODEL:-grok-4.7-medium}"
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-flash}"
export DEEPSEEK_SMALL_MODEL="${DEEPSEEK_SMALL_MODEL:-deepseek-flash}"
# Effort level of every backend (low|medium|high|xhigh|max); Grok's is part of its model name above.
export DEEPSEEK_EFFORT="${DEEPSEEK_EFFORT:-medium}"
export CONSOLIDATOR_EFFORT="${CONSOLIDATOR_EFFORT:-medium}"
export CLAUDE_CONSOLIDATOR_MODEL="${CLAUDE_CONSOLIDATOR_MODEL:-claude-sonnet-5-5}"
export ANTHROPIC_CLAUDE_CONFIG_DIR="${ANTHROPIC_CLAUDE_CONFIG_DIR:-$HOME/.claude-anthropic}"
export CURSOR_AGENT_BIN="${CURSOR_AGENT_BIN:-$(command -v cursor-agent || command -v agent || echo cursor-agent)}"
export CODEX_EXTRA_ARGS="${CODEX_EXTRA_ARGS:--c sandbox_workspace_write.network_access=true -c 'model_reasoning_effort=\"medium\"'}"
export DEEPSEEK_ACCEPT_UNVERIFIED="${DEEPSEEK_ACCEPT_UNVERIFIED:-0}"   # decision D2: default refuse
export REVIEW_MAX_ROUNDS="${REVIEW_MAX_ROUNDS:-5}"
REVIEWERS="${REVIEWERS:-CHATGPT,DEEPSEEK,GROK}"

mode="${1:-preflight}"

# --- sanity checks ---
for bin in git python3 codex claude "$CURSOR_AGENT_BIN"; do
  command -v "$bin" >/dev/null 2>&1 || { echo "missing binary: $bin" >&2; exit 1; }
done
[ -f "$LOOP" ] || { echo "not found: $LOOP" >&2; exit 1; }
[ -d "$ANTHROPIC_CLAUDE_CONFIG_DIR" ] || { echo "Anthropic profile missing: $ANTHROPIC_CLAUDE_CONFIG_DIR (run: CLAUDE_CONFIG_DIR=$ANTHROPIC_CLAUDE_CONFIG_DIR claude, then /login)" >&2; exit 1; }

# The loop script must already support the reviewers asked for (roadmap Phase 3 adds GROK).
if [[ "$REVIEWERS" == *GROK* ]] && ! grep -q "run_cursor_agent" "$LOOP"; then
  echo "specs_review_loop.py has no GROK runner yet (roadmap Phase 3). Use REVIEWERS=CHATGPT,DEEPSEEK for a labelled diagnostic run only." >&2
  exit 1
fi


source ~/.credentials
# --- DeepSeek key: env first, else hidden prompt; never written anywhere ---
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  read -rsp "DeepSeek API key: " DEEPSEEK_API_KEY; echo
  export DEEPSEEK_API_KEY
fi

# --- one loop per checkout/worktree: the lock is per git-dir, so loops in different worktrees run in parallel ---
[ -d "$ROOT" ] || { echo "worktree not found: $ROOT" >&2; exit 1; }
cd "$ROOT"
exec 9>"$(git rev-parse --absolute-git-dir)/review-loop.lock"
if ! flock -n 9; then
  echo "another review loop (or preflight) is already using $ROOT; wait for it to finish. Two in one checkout would switch its branch and commit work to the wrong branch." >&2
  exit 1
fi
# fd 9 stays open in the engine below, so the lock is held until this script ends.

# --- git state: clean tree, on the loop branch ---
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean in $ROOT; commit or stash first" >&2; git status --short >&2; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || git checkout "$BRANCH"

case "$mode" in
  preflight)
    python3 "$LOOP" "${PROJECT_ARGS[@]}" --preflight ;;
  one)
    python3 "$LOOP" "${PROJECT_ARGS[@]}" --preflight
    python3 "$LOOP" "${PROJECT_ARGS[@]}" --reviewers "$REVIEWERS" --max-rounds 1 ;;
  full)
    python3 "$LOOP" "${PROJECT_ARGS[@]}" --preflight
    python3 "$LOOP" "${PROJECT_ARGS[@]}" --reviewers "$REVIEWERS" --max-rounds "$REVIEW_MAX_ROUNDS" ;;
  *)
    echo "usage: $0 <project-dir> <name> [branch] {preflight|one|full}" >&2; exit 2 ;;
esac
