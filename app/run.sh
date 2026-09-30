#!/bin/bash
# Start (or restart) the review history app detached on port 8080; open http://localhost:8080
cd "$(dirname "$0")/.."
for pid in $(ps -eo pid,args | awk '/[a]pp\/main.py/ {print $1}'); do kill "$pid"; done
mkdir -p data/logs
setsid nohup python3 -u app/main.py --server --port "${1:-8080}" --host 0.0.0.0 > data/logs/app.log 2>&1 < /dev/null &
disown
sleep 8
tail -n 4 data/logs/app.log
