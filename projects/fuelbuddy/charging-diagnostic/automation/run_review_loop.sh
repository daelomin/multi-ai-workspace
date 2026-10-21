#!/usr/bin/env bash
# FuelBuddy wrapper: ./run_review_loop.sh {preflight|one|full}  (see generic/run_review_loop.sh)
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)/generic/run_review_loop.sh" \
  projects/fuelbuddy/charging-diagnostic FuelBuddy agent/loop/fuelbuddy-review "${1:-preflight}"
