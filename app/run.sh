#!/bin/bash
# Start (or restart) the app on port 8080 as a systemd user service, so it outlives the shell that started it.
# Needs lingering once: loginctl enable-linger $USER. Logs: data/logs/app.log. Stop: systemctl --user stop vtk-app
cd "$(dirname "$0")/.."
for pid in $(ps -eo pid,args | awk '/[a]pp\/main.py/ {print $1}'); do kill "$pid"; done
systemctl --user stop vtk-app 2>/dev/null
systemctl --user reset-failed vtk-app 2>/dev/null
mkdir -p data/logs
systemd-run --user --unit vtk-app --working-directory="$PWD" \
  -p StandardOutput=file:"$PWD/data/logs/app.log" -p StandardError=inherit \
  /usr/bin/python3 -u app/main.py --server --port "${1:-8080}" --host 0.0.0.0
sleep 8
systemctl --user is-active vtk-app
tail -n 4 data/logs/app.log
