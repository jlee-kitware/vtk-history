#!/usr/bin/env python3
"""Can VTK's review history tell an author what reviewers will ask for on a change?

For each merge request after --cutoff where a reviewer applied one of the mined rules, the
rules are ranked using only comments from before the cutoff, and a case succeeds when an applied
rule is among the top k.

Rankings:
  file history   rules reviewers applied before on the same files (weight 4), the same directory
                 (2), and the same module (1), counting each earlier comment
  most common    the rules applied most often overall before the cutoff, the same for every MR
  added code     rules whose earlier comments are most similar in meaning to the lines the MR adds
                 (qwen3-embedding; each rule is the mean of its pre-cutoff comment embeddings)
  combined       added-code ranking fused with file history (reciprocal ranks)

Usage:
  python eval/review_concerns.py [--cutoff 2024-07-01] [--k 1 3 5 10]
"""

import argparse
import json
import sys

import numpy as np
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")
    groups = {}
    gpath = ROOT / "data/rule_groups.json"
    if gpath.exists():
        for g in json.loads(gpath.read_text())["groups"]:
            for rid in g:
                groups[rid] = g[0]
    rule_of = {}
    for r in rules:
        for m in r["members"]:
            rule_of[m] = groups.get(r["id"], r["id"])
    comments = []
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            if e["discussion_id"] not in rule_of:
                continue
            code = e.get("code") or {}
            comments.append({"id": e["discussion_id"], "rule": rule_of[e["discussion_id"]], "mr": e["mr"]["iid"],
                             "date": e["thread"][0]["created_at"][:10], "path": code.get("path"),
                             "module": code.get("module")})
    return comments


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cutoff", default="2024-07-01")
    p.add_argument("--k", type=int, nargs="+", default=[1, 3, 5, 10])
    args = p.parse_args()
    comments = load()
    before = [c for c in comments if c["date"] < args.cutoff]
    after = [c for c in comments if c["date"] >= args.cutoff]
    common = [r for r, _ in Counter(c["rule"] for c in before).most_common()]
    by_path, by_dir, by_module = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    for c in before:
        if c["path"]:
            by_path[c["path"]][c["rule"]] += 1
            by_dir[str(Path(c["path"]).parent)][c["rule"]] += 1
        if c["module"]:
            by_module[c["module"]][c["rule"]] += 1
    files = json.loads((ROOT / "data/eval/mr_files.json").read_text())
    added = json.loads((ROOT / "data/eval/mr_added.json").read_text())
    sys.path.insert(0, str(ROOT / "index"))
    from search import Index
    ix = Index(str(ROOT / "data/index"))
    cache = np.load(ROOT / "data/convention_embeddings.npy", allow_pickle=True).item()
    cvec = dict(zip(cache["ids"], cache["vectors"]))
    rule_vecs = defaultdict(list)
    for c in before:
        if c["id"] in cvec:
            rule_vecs[c["rule"]].append(np.asarray(cvec[c["id"]], dtype=np.float32))
    rule_ids = sorted(rule_vecs)
    dim = ix.vectors.shape[1]
    R = np.array([np.mean([x[:dim] / np.linalg.norm(x[:dim]) for x in rule_vecs[r]], axis=0) for r in rule_ids])
    R /= np.linalg.norm(R, axis=1, keepdims=True)
    mrs = defaultdict(set)
    for c in after:
        mrs[c["mr"]].add(c["rule"])
    hits = {"file history": Counter(), "most common": Counter(), "added code": Counter(), "combined": Counter()}
    tested = 0
    for mr, applied in mrs.items():
        changed = files.get(str(mr))
        if not changed:
            continue
        tested += 1
        score = Counter()
        for path, module in changed:
            score.update({r: 4 * n for r, n in by_path[path].items()})
            score.update({r: 2 * n for r, n in by_dir[str(Path(path).parent)].items()})
            if module:
                score.update(by_module[module])
        ranked = [r for r, _ in score.most_common()] + [r for r in common if r not in score]
        text = added.get(str(mr)) or ""
        if text.strip():
            v = ix.embed([text[:4000]], query=False)[0]
            v = v / np.linalg.norm(v)
            by_code = [rule_ids[i] for i in np.argsort(-(R @ v))]
        else:
            by_code = common
        fused = Counter()
        for lst in (ranked, by_code):
            for i, r in enumerate(lst):
                fused[r] += 1 / (60 + i)
        both = [r for r, _ in fused.most_common()]
        for k in args.k:
            hits["file history"][k] += bool(applied & set(ranked[:k]))
            hits["most common"][k] += bool(applied & set(common[:k]))
            hits["added code"][k] += bool(applied & set(by_code[:k]))
            hits["combined"][k] += bool(applied & set(both[:k]))
    print(f"{tested} merge requests after {args.cutoff} where a reviewer applied a mined rule; "
          f"{len({c['rule'] for c in before})} rules seen before the cutoff")
    for name, h in hits.items():
        print(f"  {name:13} " + "  ".join(f"top {k}: {h[k] / tested:5.1%}" for k in args.k))
    out = {name: {k: round(h[k] / tested, 3) for k in args.k} for name, h in hits.items()}
    (ROOT / "data/eval/review_concerns.json").write_text(json.dumps({"cutoff": args.cutoff, "mrs": tested, **out}, indent=1))


if __name__ == "__main__":
    main()
