#!/bin/bash
# Run gitlab_mirror.py detached, logging to data/logs/<timestamp>-<mode>.log.
# Usage: mirror/run_bg.sh count | mirror/run_bg.sh sync --limit 200
cd "$(dirname "$0")/.."
eval "$(grep '^export GITLAB_TOKEN=' ~/.bashrc | tail -1)"
mkdir -p data/logs
log="data/logs/$(date +%Y%m%d-%H%M%S)-$1.log"
setsid nohup python3 -u mirror/gitlab_mirror.py "$@" > "$log" 2>&1 < /dev/null &
echo "log $log"
