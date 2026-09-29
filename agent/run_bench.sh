#!/bin/bash
# Wait for the search index, then score each model on the same benchmark sample.
# Usage: agent/run_bench.sh <limit> <model> [<model> ...]
cd "$(dirname "$0")/.."
limit=$1
shift
while [ ! -f data/index/meta.json ]; do sleep 60; done
for model in "$@"; do
    python3 -u agent/evaluate.py --limit "$limit" --model "$model"
done
