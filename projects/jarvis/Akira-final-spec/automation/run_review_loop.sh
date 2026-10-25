#!/usr/bin/env bash
# Thin wrapper for the Akira specification review loop.
#   ./run_review_loop.sh preflight   # probe backends, no spec changes
#   ./run_review_loop.sh one         # one live round
#   ./run_review_loop.sh full        # up to REVIEW_MAX_ROUNDS
# Runs from the worktree root; requires a clean tree on the loop branch.
set -euo pipefail
exec "$(git -C "$(dirname "$0")/../../.." rev-parse --show-toplevel)/generic/run_review_loop.sh" \
  projects/jarvis/JarvisBot/akira Akira agent/loop/akira-review "${1:-preflight}"
