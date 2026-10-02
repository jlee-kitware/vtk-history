#!/usr/bin/env python3
"""Compare two benchmark runs on the MRs both scored.

Prints recall and precision for each run, the per-MR difference with a 95% bootstrap
interval (MRs resampled), and how often each run used the rules.

Usage: python agent/compare_runs.py data/benchmark/runs-v5/before data/benchmark/runs-v5/after
"""

import json
import random
import re
import sys
from pathlib import Path

RULE_REF = re.compile(r"\b[RD]\d{3}\b")


def load(run):
    out = {}
    for f in Path(run).glob("*.json"):
        if f.stem.isdigit():
            rec = json.loads(f.read_text())
            if rec.get("score") is not None:
                out[f.stem] = rec
    return out


def stats(recs):
    a = sum(len(r["score"]["answers"]) for r in recs)
    am = sum(x["matched"] for r in recs for x in r["score"]["answers"])
    p = sum(len(r["score"]["predictions"]) for r in recs)
    pm = sum(x["matched"] for r in recs for x in r["score"]["predictions"])
    calls = sum(1 for r in recs for t in r.get("trace") or [] if t["tool"] == "rules")
    cited = sum(1 for r in recs for c in r["predictions"]
                if RULE_REF.search(f"{c.get('basis') or ''} {c['comment']}"))
    return {"answers": a, "matched": am, "recall": am / a if a else 0, "comments": p, "comments_matched": pm,
            "precision": pm / p if p else 0, "rules_calls_per_mr": calls / len(recs), "comments_citing_rules": cited}


def boot(pairs, metric, n=4000, seed=7):
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        sample = [rng.choice(pairs) for _ in pairs]
        diffs.append(metric([b for b, _ in sample], [a for _, a in sample]))
    diffs.sort()
    return diffs[int(0.025 * n)], diffs[int(0.975 * n)]


def main():
    before, after = load(sys.argv[1]), load(sys.argv[2])
    common = sorted(set(before) & set(after))
    pairs = [(before[k], after[k]) for k in common]
    sb, sa = stats([b for b, _ in pairs]), stats([a for _, a in pairs])
    print(f"{len(common)} MRs scored in both runs\n")
    print(f"{'':24}{'before':>10}{'after':>10}")
    for key in ["answers", "matched", "recall", "comments", "comments_matched", "precision",
                "rules_calls_per_mr", "comments_citing_rules"]:
        fmt = (lambda v: f"{v:10.3f}") if isinstance(sb[key], float) else (lambda v: f"{v:10d}")
        print(f"{key:24}{fmt(sb[key])}{fmt(sa[key])}")
    recall = lambda bs, as_: stats(as_)["recall"] - stats(bs)["recall"]
    precision = lambda bs, as_: stats(as_)["precision"] - stats(bs)["precision"]
    lo, hi = boot(pairs, recall)
    print(f"\nrecall change    {sa['recall'] - sb['recall']:+.3f}  (95% interval {lo:+.3f} to {hi:+.3f})")
    lo, hi = boot(pairs, precision)
    print(f"precision change {sa['precision'] - sb['precision']:+.3f}  (95% interval {lo:+.3f} to {hi:+.3f})")
    better = sum(1 for b, a in pairs if sum(x["matched"] for x in a["score"]["answers"])
                 > sum(x["matched"] for x in b["score"]["answers"]))
    worse = sum(1 for b, a in pairs if sum(x["matched"] for x in a["score"]["answers"])
                < sum(x["matched"] for x in b["score"]["answers"]))
    print(f"MRs with more reviewer comments found: after {better}, before {worse}")


if __name__ == "__main__":
    main()
