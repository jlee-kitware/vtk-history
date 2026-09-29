#!/bin/bash
# Usage: trends/run_themes.sh <name> [discover_themes.py options]
cd "$(dirname "$0")/.."
name=${1:-themes}
shift
mkdir -p data/logs
log=data/logs/trends-$name.log
setsid nohup python3 -u trends/discover_themes.py "$@" > "$log" 2>&1 < /dev/null &
disown
sleep 60
cat "$log"
