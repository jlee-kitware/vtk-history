#!/bin/bash
# Bring every derived dataset up to date with the mirrors and the VTK repository.
# Waits for any running benchmark, since labeling and embedding share the Spark with it.
# Usage: ./refresh.sh            (run detached: setsid nohup ./refresh.sh > data/logs/refresh.log 2>&1 &)
cd "$(dirname "$0")"
set -e
step() { echo "== $1 $(date '+%F %T')"; }

while pgrep -f "[r]un_bench.sh" > /dev/null || pgrep -f "python3 -u agent/evaluate.py" > /dev/null || pgrep -f "[g]itlab_mirror.py sync" > /dev/null \
      || pgrep -f "[d]iscourse_mirror.py sync" > /dev/null; do
    sleep 120
done

step "fetch vtk"
git -C /home/jlee/gitsync/vtk fetch -q upstream master
step "extract review threads"
python3 -u extract/extract_reviews.py
step "label new threads"
python3 -u label/label_reviews.py
step "deprecation index"
python3 -u deprecations/build_index.py
python3 -u deprecations/check_rules.py
python3 -u rules/confidence.py
step "term trends"
python3 -u trends/discover_terms.py --out data/trends/terms-v2
step "search index"
python3 -u index/build_index.py
step "themes"
python3 -u trends/discover_themes.py --k 250 --out data/trends/k250
step "done"
