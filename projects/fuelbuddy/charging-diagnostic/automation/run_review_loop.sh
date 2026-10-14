#!/usr/bin/env bash
# FuelBuddy charging-diagnostic review loop launcher.
# Usage:
#   ./run_review_loop.sh preflight      # probe all backends, no spec changes
#   ./run_review_loop.sh one            # one live round (CHATGPT,DEEPSEEK,GROK), max-rounds 1
#   ./run_review_loop.sh full           # up to 5 rounds
# The DeepSeek key is read from the environment, or prompted (hidden, never written to disk).
set -euo pipefail

REPO="${REPO:-$HOME/GIT/multi-ai-workspace}"
LOOP="$REPO/projects/fuelbuddy/charging-diagnostic/automation/review_loop.py"
BRANCH="agent/loop/fuelbuddy-review"

# FAST=1 -> Codex Fast service tier (about 2x speed, 2x price) and Grok 4.7 high-fast.
# DeepSeek and the Anthropic consolidator have no fast variant, so they are unchanged.
if [ "${FAST:-0}" = "1" ]; then
  export GROK_MODEL="${GROK_MODEL:-grok-4.7-high-fast}"
  export CODEX_SERVICE_TIER="${CODEX_SERVICE_TIER:-fast}"
fi

# --- configuration (override by exporting before running) ---
export GROK_MODEL="${GROK_MODEL:-grok-4.7-high}"
export DEEPSEEK_MODEL="${DEEPSEEK_MODEL:-deepseek-v4-pro}"
export DEEPSEEK_SMALL_MODEL="${DEEPSEEK_SMALL_MODEL:-deepseek-flash}"
export CLAUDE_CONSOLIDATOR_MODEL="${CLAUDE_CONSOLIDATOR_MODEL:-claude-sonnet-5-5}"
export ANTHROPIC_CLAUDE_CONFIG_DIR="${ANTHROPIC_CLAUDE_CONFIG_DIR:-$HOME/.claude-anthropic}"
export CURSOR_AGENT_BIN="${CURSOR_AGENT_BIN:-$(command -v cursor-agent || command -v agent || echo cursor-agent)}"
export CODEX_EXTRA_ARGS="${CODEX_EXTRA_ARGS:--c sandbox_workspace_write.network_access=true}"
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
  echo "review_loop.py has no GROK runner yet (roadmap Phase 3). Use REVIEWERS=CHATGPT,DEEPSEEK for a labelled diagnostic run only." >&2
  exit 1
fi


source ~/.credentials
# --- DeepSeek key: env first, else hidden prompt; never written anywhere ---
if [ -z "${DEEPSEEK_API_KEY:-}" ]; then
  read -rsp "DeepSeek API key: " DEEPSEEK_API_KEY; echo
  export DEEPSEEK_API_KEY
fi

# --- git state: clean tree, on the loop branch ---
cd "$REPO"
[ -z "$(git status --porcelain)" ] || { echo "working tree not clean; commit or stash first" >&2; git status --short >&2; exit 1; }
[ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] || git checkout "$BRANCH"

case "$mode" in
  preflight)
    python3 "$LOOP" --preflight ;;
  one)
    python3 "$LOOP" --preflight
    python3 "$LOOP" --reviewers "$REVIEWERS" --max-rounds 1 ;;
  full)
    python3 "$LOOP" --preflight
    python3 "$LOOP" --reviewers "$REVIEWERS" --max-rounds "$REVIEW_MAX_ROUNDS" ;;
  *)
    echo "usage: $0 {preflight|one|full}" >&2; exit 2 ;;
esac
