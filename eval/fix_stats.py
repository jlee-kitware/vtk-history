"""Paired comparison of fix-suggestion runs on the same review comments: exact sign test and a bootstrap interval."""

import json
import random
import sys
from math import comb
from pathlib import Path

RUNS = Path(__file__).resolve().parents[1] / "data/eval/fix_runs"
GOOD = ("same", "different_but_valid")


def load(label):
    return {json.loads(l)["id"]: json.loads(l) for l in open(RUNS / f"{label}.scored.jsonl")}


def sign_test(wins, losses):
    n = wins + losses
    k = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n) if n else 1.0


def compare(a_label, b_label, measure, ids):
    a, b = load(a_label), load(b_label)
    xa = [measure(a[i]) for i in ids]
    xb = [measure(b[i]) for i in ids]
    wins = sum(y and not x for x, y in zip(xa, xb))
    losses = sum(x and not y for x, y in zip(xa, xb))
    rng = random.Random(1)
    diffs = []
    for _ in range(10000):
        sample = [rng.randrange(len(ids)) for _ in ids]
        diffs.append(sum(xb[j] - xa[j] for j in sample) / len(ids))
    diffs.sort()
    lo, hi = diffs[249], diffs[9749]
    print(f"  {b_label} vs {a_label}: {sum(xb)}/{len(ids)} vs {sum(xa)}/{len(ids)}  "
          f"(+{wins} / -{losses})  difference {100 * (sum(xb) - sum(xa)) / len(ids):+.0f} points, "
          f"95% interval {100 * lo:+.0f} to {100 * hi:+.0f}, sign test p = {sign_test(wins, losses):.3f}")


def main():
    labels = sys.argv[1:] or ["gpt-5.4-mini", "gpt-5.4-mini-random", "gpt-5.4-mini-history"]
    ids = sorted(set.intersection(*(set(load(l)) for l in labels)))
    print(f"{len(ids)} review comments scored in every run")
    for name, measure in (("addresses the comment (judge: same or different but valid)", lambda s: s.get("verdict") in GOOD),
                          ("the author's own fix (judge: same)", lambda s: s.get("verdict") == "same"),
                          ("exact match with the author's change", lambda s: bool(s.get("exact")))):
        print(name)
        base, rand, hist = labels
        compare(base, hist, measure, ids)
        compare(rand, hist, measure, ids)
        compare(base, rand, measure, ids)


if __name__ == "__main__":
    main()
