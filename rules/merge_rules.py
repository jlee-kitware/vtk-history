#!/usr/bin/env python3
"""Group mined rules that ask for the same thing, so their evidence is pooled.

Candidate pairs: rules whose member centroids are close (cosine >= --cutoff). A model confirms
each pair in both orders ("a comment applying one also applies the other"); when the two orders
disagree, gpt-oss:120b decides. Confirmed pairs are joined transitively. Each group's canonical rule is the one with the most MRs.

Writes data/rule_groups.json: {"groups": [[rule id, ...], ...], "pairs": [...]}.

Usage:
  python rules/merge_rules.py [--cutoff 0.85]
"""

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rules"))
import match_comments as M  # noqa: E402

PROMPT = """Two review rules mined from VTK merge request reviews:

A: "{a}"
B: "{b}"

Do they ask for the same thing, so that a comment applying one also applies the other? Rules on the same
topic that ask for different things (for example "use nullptr" and "initialize pointers") are not the same.
Reply {{"same": true}} or {{"same": false}}."""


def same(a, b, model=M.MODEL):
    payload = {"model": model, "stream": False, "format": "json", "think": False,
               "messages": [{"role": "user", "content": PROMPT.format(a=a, b=b)}],
               "options": {"temperature": 0, "num_predict": 30, "num_ctx": 2048}}
    for _ in range(3):
        try:
            req = urllib.request.Request(M.HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            return bool(json.loads(json.load(urllib.request.urlopen(req, timeout=300))["message"]["content"]).get("same"))
        except (json.JSONDecodeError, KeyError, OSError):
            time.sleep(5)
    return False


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cutoff", type=float, default=0.85)
    args = p.parse_args()
    rules, _key, vec, _labels, _examples = M.load()
    C = M.centroids(rules, vec)
    S = C @ C.T
    pairs = [(i, j) for i in range(len(rules)) for j in range(i + 1, len(rules)) if S[i, j] >= args.cutoff]
    print(f"{len(pairs)} candidate pairs at centroid similarity >= {args.cutoff}", flush=True)
    parent = list(range(len(rules)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    confirmed = []
    for n, (i, j) in enumerate(pairs, 1):
        ab, ba = same(rules[i]["rule"], rules[j]["rule"]), same(rules[j]["rule"], rules[i]["rule"])
        if ab != ba:
            ab = ba = same(rules[i]["rule"], rules[j]["rule"], "gpt-oss:120b")
        if ab and ba:
            confirmed.append((rules[i]["id"], rules[j]["id"], round(float(S[i, j]), 3)))
            parent[find(i)] = find(j)
        if n % 50 == 0:
            print(f"  {n}/{len(pairs)}; confirmed {len(confirmed)}", flush=True)
    groups = {}
    for i in range(len(rules)):
        groups.setdefault(find(i), []).append(i)
    multi = [sorted(g, key=lambda i: -rules[i]["support_mrs"]) for g in groups.values() if len(g) > 1]
    out = {"cutoff": args.cutoff, "groups": [[rules[i]["id"] for i in g] for g in multi],
           "pairs": confirmed}
    (ROOT / "data/rule_groups.json").write_text(json.dumps(out, indent=1))
    print(f"confirmed {len(confirmed)} pairs; {len(multi)} groups covering {sum(len(g) for g in multi)} rules")
    for g in multi[:25]:
        print("  " + " | ".join(f"{rules[i]['id']}: {rules[i]['rule'][:60]}" for i in g))


if __name__ == "__main__":
    main()
