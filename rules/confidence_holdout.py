#!/usr/bin/env python3
"""Does confidence predict what authors do later? Score each rule from its comments before a cutoff, then
measure follow-through on its line comments after the cutoff, grouped by the earlier level.

Usage:
  python rules/confidence_holdout.py [--cutoff 2024-07-01]
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rules"))
from confidence import MIN_LINES, score  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cutoff", default="2024-07-01")
    args = ap.parse_args()
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    examples, meta = {}, {}
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            examples[e["discussion_id"]] = (e["kind"], bool(e.get("acted_on")))
            meta[e["discussion_id"]] = (e["thread"][0]["created_at"][:10], e["reviewer"])
    flags = [a for k, a in examples.values() if k == "line"]
    baseline = sum(flags) / len(flags)

    groups = defaultdict(lambda: {"rules": 0, "later": 0, "acted": 0})
    for r in rules:
        before = [m for m in r["members"] if meta[m][0] < args.cutoff]
        after = [m for m in r["members"] if meta[m][0] >= args.cutoff and examples[m][0] == "line"]
        if not before or not after:
            continue
        early = dict(r, members=before, reviewers=[[x, 1] for x in {meta[m][1] for m in before}],
                     support_threads=len(before), last_seen=max(meta[m][0] for m in before),
                     counter_examples=[c for c in r.get("counter_examples") or [] if c["date"] < args.cutoff])
        level = score(early, examples, baseline, False)["level"]
        g = groups[level]
        g["rules"] += 1
        g["later"] += len(after)
        g["acted"] += sum(examples[m][1] for m in after)
    print(f"cutoff {args.cutoff}; all line comments acted on: {baseline:.1%}; "
          f"levels need {MIN_LINES}+ earlier line comments to use follow-through")
    print(f"{'level before cutoff':20} {'rules':>6} {'later line comments':>20} {'acted on':>9}")
    for level in ("high", "medium", "low"):
        g = groups[level]
        if g["later"]:
            print(f"{level:20} {g['rules']:6} {g['later']:20} {g['acted'] / g['later']:9.1%}")


if __name__ == "__main__":
    main()
