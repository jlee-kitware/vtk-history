#!/bin/bash
# Before/after benchmark on the same MRs.
#   before  rules drafted before the 2026 redraft, no confidence levels, no tool checks
#   after   current rules with confidence levels, documented rules, tool checks
# Usage: agent/bench_compare.sh <limit> [out dir]   (limit 0 = all MRs; cached reviews are reused)
cd "$(dirname "$0")/.."
limit=$1
out=${2:-data/benchmark/runs-v5}
python3 -u agent/evaluate.py --agent tool --limit "$limit" --out "$out" --label before \
    --rules data/rules_verified.before-2026.json --plain-rules --no-tool-checks
python3 -u agent/evaluate.py --agent tool --limit "$limit" --out "$out" --label after --doc-rules
python3 agent/compare_runs.py "$out/before" "$out/after"
