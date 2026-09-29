#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p data/logs
log=data/logs/trends-themes.log
setsid nohup python3 -u trends/discover_themes.py "$@" > "$log" 2>&1 < /dev/null &
disown
sleep 60
cat "$log"
