#!/bin/bash
# Score each model on the same benchmark sample. evaluate.py reviews every MR first,
# unloads the reviewer model, then scores with the judge, so two large models are
# never loaded at once.
# Usage: agent/run_bench.sh <limit> <hunk|tool> <model> [<model> ...]
cd "$(dirname "$0")/.."
limit=$1
agent=$2
shift 2
while [ ! -f data/index/meta.json ]; do sleep 60; done
for model in "$@"; do
    python3 -u agent/evaluate.py --limit "$limit" --agent "$agent" --model "$model"
done
