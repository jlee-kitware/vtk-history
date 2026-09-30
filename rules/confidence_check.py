#!/usr/bin/env python3
"""Check rule confidence against the benchmark: how often does an agent comment that cites a rule match a
reviewer's comment (judge says same concern) or at least land where one was made (within 5 lines)?

Counts every scored benchmark run; a comment citing several rules counts once under its lowest level.

Usage:
  python rules/confidence_check.py
"""

import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from data import rule_key  # noqa: E402

RANK = {"high": 0, "medium": 1, "low": 2}


def main():
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    conf = json.loads((ROOT / "data/rules_confidence.json").read_text())["rules"]
    level = {f"R{i:03d}": conf[rule_key(r)]["level"] for i, r in enumerate(rules, 1)}
    stats = defaultdict(lambda: defaultdict(int))
    for f in sorted(glob.glob(str(ROOT / "data/benchmark/runs*/*/*.json"))):
        if f.endswith("report.json"):
            continue
        record = json.loads(Path(f).read_text())
        scores = (record.get("score") or {}).get("predictions")
        if not scores or len(scores) != len(record["predictions"]):
            continue
        run = Path(f).parent.parent.name + "/" + Path(f).parent.name
        for p, s in zip(record["predictions"], scores):
            cited = [level[x] for x in re.findall(r"R\d{3}", f"{p.get('basis', '')} {p.get('comment', '')}") if x in level]
            bucket = max(cited, key=RANK.get) if cited else "no rule cited"
            for key in (bucket, f"{bucket} [{'tool' if run.endswith('-tool') else 'per-hunk'}]"):
                stats[key]["comments"] += 1
                stats[key]["matched"] += bool(s.get("matched"))
                stats[key]["located"] += bool(s.get("located"))
    print(f"{'citing rules at level':34} {'comments':>8} {'matched':>8} {'rate':>6} {'located':>8} {'rate':>6}")
    for key in sorted(stats, key=lambda k: (k.split(" [")[0] not in RANK, k)):
        s = stats[key]
        print(f"{key:34} {s['comments']:8} {s['matched']:8} {s['matched'] / s['comments']:6.1%} "
              f"{s['located']:8} {s['located'] / s['comments']:6.1%}")


if __name__ == "__main__":
    main()
