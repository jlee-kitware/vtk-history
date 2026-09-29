#!/bin/bash
# Build the search index detached, logging to data/logs/index.log.
cd "$(dirname "$0")/.."
mkdir -p data/logs
setsid nohup python3 -u index/build_index.py "$@" > data/logs/index.log 2>&1 < /dev/null &
disown
sleep 50
cat data/logs/index.log
