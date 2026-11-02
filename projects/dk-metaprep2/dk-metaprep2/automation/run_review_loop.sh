#!/usr/bin/env bash
# Generated: the adjacent loop.json is authoritative. No project paths or branch names here.
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
common_dir="$(git -C "$project_dir" rev-parse --path-format=absolute --git-common-dir)"
toolkit_root="${REVIEW_TOOLKIT_ROOT:-$(dirname "$common_dir")}"
exec python3 "$toolkit_root/generic/loop_project.py" run --project "$project_dir" --mode "${1:-preflight}"
