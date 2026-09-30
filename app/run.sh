#!/bin/bash
# Start (or restart) the review history app detached on port 8080; open http://localhost:8080
# Needs trame v4 with trame-mui; PY defaults to the venv made by: python3 -m venv --system-site-packages ~/venvs/trame4
# && ~/venvs/trame4/bin/pip install "trame>=4" trame-mui
cd "$(dirname "$0")/.."
PY=${PY:-$HOME/venvs/trame4/bin/python}
for pid in $(ps -eo pid,args | awk '/[a]pp\/main.py/ {print $1}'); do kill "$pid"; done
mkdir -p data/logs
setsid nohup "$PY" -u app/main.py --server --port "${1:-8080}" --host 0.0.0.0 > data/logs/app.log 2>&1 < /dev/null &
disown
sleep 8
tail -n 4 data/logs/app.log
