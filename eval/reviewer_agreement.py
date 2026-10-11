"""How often do two VTK reviewers on the same MR comment on the same lines? The ceiling for any reviewer imitation.

For every MR with line comments from at least two reviewers (authors excluded), each reviewer's comments are checked
against the other reviewers' comments: same file, within WINDOW lines. "Same revision" restricts the pair to comments
made on the same pushed version, where line numbers are comparable without mapping.
"""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WINDOW = 5


def main():
    by_mr = defaultdict(list)
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            c = e.get("code") or {}
            if e.get("kind") != "line" or c.get("side") != "new" or e["reviewer"] == e["mr"]["author"]:
                continue
            by_mr[e["mr"]["iid"]].append({"who": e["reviewer"], "path": c["path"], "line": c["line"],
                                          "head": c.get("head_sha"), "acted": bool(e.get("acted_on")),
                                          "date": e["thread"][0]["created_at"]})
    for same_rev in (False, True):
        mrs = pairs = comments = near = near_acted = acted = 0
        per_mr = []
        for iid, cs in by_mr.items():
            who = {c["who"] for c in cs}
            if len(who) < 2:
                continue
            mrs += 1
            hit_mr = 0
            for c in cs:
                others = [o for o in cs if o["who"] != c["who"] and (not same_rev or o["head"] == c["head"])]
                if same_rev and not others:
                    continue
                comments += 1
                hit = any(o["path"] == c["path"] and abs(o["line"] - c["line"]) <= WINDOW for o in others)
                near += hit
                hit_mr += hit
                acted += c["acted"]
                near_acted += hit and c["acted"]
            per_mr.append(hit_mr)
        label = "same revision" if same_rev else "any revision"
        print(f"{label:14} MRs with 2+ reviewers {mrs}, comments {comments}: another reviewer commented within "
              f"{WINDOW} lines for {near} ({near / comments:.1%}); among comments the author acted on "
              f"{near_acted}/{acted} ({near_acted / max(acted, 1):.1%})")
    first = defaultdict(int)
    for iid, cs in by_mr.items():
        if len({c["who"] for c in cs}) >= 2:
            first[len(cs)] += 1
    reviewers = [len({c["who"] for c in cs}) for cs in by_mr.values()]
    print(f"MRs with line comments {len(by_mr)}; with 2+ reviewers {sum(r >= 2 for r in reviewers)}")


if __name__ == "__main__":
    main()
