#!/usr/bin/env python3
"""Rescore saved benchmark predictions with a given judge, without rerunning the reviewer.

Usage:
  python agent/rescore.py data/benchmark/runs-v1/nemotron3_33b
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate import check_judge, score  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("run")
    p.add_argument("--benchmark", default="data/benchmark/benchmark.jsonl")
    p.add_argument("--judge", default="nemotron-3.5-lightning:latest")
    p.add_argument("--window", type=int, default=5)
    args = p.parse_args()

    check_judge(args.judge)
    bench = {json.loads(line)["mr"]["iid"]: json.loads(line) for line in open(args.benchmark)}
    t = dict.fromkeys(("mrs", "answers", "located", "matched", "predictions", "p_located", "p_matched"), 0)
    for f in sorted(Path(args.run).glob("*.json")):
        if f.name == "report.json":
            continue
        record = json.loads(f.read_text())
        s = score(bench[record["mr"]["iid"]], record["predictions"], args.judge, args.window)
        t["mrs"] += 1
        t["answers"] += len(s["answers"])
        t["located"] += sum(a["located"] for a in s["answers"])
        t["matched"] += sum(a["matched"] for a in s["answers"])
        t["predictions"] += len(s["predictions"])
        t["p_located"] += sum(x["located"] for x in s["predictions"])
        t["p_matched"] += sum(x["matched"] for x in s["predictions"])
    r = lambda a, b: round(a / b, 3) if b else None
    print(json.dumps({"run": args.run, "judge": args.judge, "mrs": t["mrs"],
                      "recall_location": r(t["located"], t["answers"]), "recall_content": r(t["matched"], t["answers"]),
                      "precision_location": r(t["p_located"], t["predictions"]),
                      "precision_content": r(t["p_matched"], t["predictions"]),
                      "comments_per_mr": r(t["predictions"], t["mrs"]), "matched": t["matched"],
                      "answers": t["answers"]}, indent=1))


if __name__ == "__main__":
    main()
