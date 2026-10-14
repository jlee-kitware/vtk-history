#!/usr/bin/env python3
"""Does searching VTK's history find the earlier work a new merge request is connected to?

Test cases come from merge request descriptions that link an earlier issue ("closes #18170",
an issues/ URL) or an earlier merge request ("see !9803"). The links are removed, the rest of the
title and description becomes the query, and the index is searched as of the day the MR was
opened. A case succeeds when the linked item is among the top k distinct results of its kind.

Compared: keyword search (BM25), meaning search (embeddings), the two fused (what the app uses),
and chance (k divided by the number of items of that kind that existed then).

Usage:
  python eval/related_history.py [--n 300] [--k 1 5 10] [--index data/index-<model>]
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "index"))
from search import Index  # noqa: E402

ISSUE = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?#|gitlab\.kitware\.com/vtk/vtk/-?/?issues/)(\d{2,6})\b")
MR = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?!|gitlab\.kitware\.com/vtk/vtk/-?/?merge_requests/)(\d{2,6})\b")
URL = re.compile(r"https?://\S+")


def cases(ix):
    known = {}
    for ref, date in ix.con.execute("SELECT ref, MIN(date) FROM docs WHERE kind IN ('mr', 'issue') GROUP BY ref"):
        known[ref] = date
    out = []
    for f in sorted((ROOT / "data/vtk-history/merge_requests").glob("*.json")):
        m = json.loads(f.read_text())["merge_request"]
        desc, opened = m.get("description") or "", (m.get("created_at") or "")[:10]
        if not desc or not opened:
            continue
        targets = [("issue", f"#{n}") for n in ISSUE.findall(desc)] + [("mr", f"!{n}") for n in MR.findall(desc)]
        targets = [(k, r) for k, r in targets if r in known and known[r] < opened and r != f"!{m['iid']}"]
        if not targets:
            continue
        query = MR.sub(" ", ISSUE.sub(" ", URL.sub(" ", desc)))
        query = f"{m['title']}\n{' '.join(query.split())[:1500]}"
        kind, ref = targets[0]
        out.append({"mr": m["iid"], "opened": opened, "kind": kind, "target": ref, "query": query})
    return out


def ranked_refs(ix, rowids, self_ref):
    refs, seen = [], set()
    rows = {r["rowid"]: r["ref"] for r in ix.con.execute(
        f"SELECT rowid, ref FROM docs WHERE rowid IN ({','.join('?' * len(rowids))})", rowids)} if rowids else {}
    for i in rowids:
        ref = rows.get(i)
        if ref and ref != self_ref and ref not in seen:
            seen.add(ref)
            refs.append(ref)
    return refs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=300, help="cases per kind")
    p.add_argument("--k", type=int, nargs="+", default=[1, 5, 10])
    p.add_argument("--title-only", action="store_true", help="query with the MR title alone")
    p.add_argument("--index", default=str(ROOT / "data/index"),
                   help="index to search, for comparing embedding models (eval/embedding_models.py)")
    args = p.parse_args()
    ix = Index(args.index)
    print(f"embedding model: {ix.meta['model']}", flush=True)
    allc = cases(ix)
    if args.title_only:
        allc = [dict(c, query=c["query"].split("\n")[0]) for c in allc]
    rng = random.Random(6)
    sample = []
    for kind in ("issue", "mr"):
        pool = [c for c in allc if c["kind"] == kind]
        sample += rng.sample(pool, min(args.n, len(pool)))
        print(f"{kind}: {len(pool)} merge requests link an earlier {kind}; testing {min(args.n, len(pool))}", flush=True)
    kmax = max(args.k)
    results = []
    for n, c in enumerate(sample, 1):
        f = {"kind": c["kind"], "until": c["opened"]}
        qv = ix.embed([c["query"]])[0]
        self_ref = f"!{c['mr']}"
        fused = ix.fuse(c["query"], 200, query_vector=qv, **f)
        methods = {
            "keyword": ranked_refs(ix, ix.keyword(c["query"], 200, **f), self_ref),
            "meaning": ranked_refs(ix, ix.meaning(c["query"], 200, query_vector=qv, **f), self_ref),
            "fused": ranked_refs(ix, sorted(fused, key=fused.get, reverse=True), self_ref),
        }
        total = ix.con.execute("SELECT COUNT(DISTINCT ref) FROM docs WHERE kind = ? AND date < ?",
                               (c["kind"], c["opened"])).fetchone()[0]
        rec = {"mr": c["mr"], "kind": c["kind"], "target": c["target"], "candidates": total}
        for name, refs in methods.items():
            rec[name] = refs.index(c["target"]) + 1 if c["target"] in refs[:kmax] else None
        results.append(rec)
        if n % 50 == 0:
            print(f"  {n}/{len(sample)}", flush=True)
    (ROOT / "data/eval").mkdir(exist_ok=True)
    tag = ("_title" if args.title_only else "") + ("" if Path(args.index).name == "index" else "_" + Path(args.index).name)
    (ROOT / f"data/eval/related_history{tag}.json").write_text(json.dumps(results, indent=1))
    for kind in ("issue", "mr"):
        rs = [r for r in results if r["kind"] == kind]
        if not rs:
            continue
        mid = sorted(r["candidates"] for r in rs)[len(rs) // 2]
        print(f"\nlinked earlier {kind} ({len(rs)} merge requests; median {mid} candidates)")
        for name in ("keyword", "meaning", "fused"):
            print(f"  {name:8} " + "  ".join(
                f"top {k}: {sum(1 for r in rs if r[name] and r[name] <= k) / len(rs):5.1%}" for k in args.k))
        print("  chance   " + "  ".join(
            f"top {k}: {sum(min(1, k / r['candidates']) for r in rs) / len(rs):5.1%}" for k in args.k))


if __name__ == "__main__":
    main()
