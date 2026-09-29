#!/bin/bash
# Usage: trends/run_terms.sh <name> [discover_terms.py options]
cd "$(dirname "$0")/.."
name=${1:-terms}
shift
mkdir -p data/logs
log=data/logs/trends-$name.log
setsid nohup python3 -u trends/discover_terms.py "$@" > "$log" 2>&1 < /dev/null &
disown
sleep 45
head -c 1500 "$log"
