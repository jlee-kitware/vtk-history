#!/usr/bin/env python3
"""Trends in the area and language labels maintainers put on VTK issues and merge requests.

Documents are the issues and MRs that carry at least one area: or lang: label (labels came
into use with the move to GitLab in 2015). Each label's share of those documents is
computed per quarter and scored the same way as discover_terms.py (emerging, past, fading),
and every label is also listed under "all", most used first.

Writes data/trends/labels.json.

Usage:
  python trends/label_trends.py
"""

import argparse
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import discover_terms as terms  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ("area:", "lang:")


def load(mirror):
    docs = []
    for kind, key, source in (("issues", "issue", "issue"), ("merge_requests", "merge_request", "mr")):
        for f in glob.glob(f"{mirror}/{kind}/*.json"):
            item = json.load(open(f))[key]
            labels = {l for l in item.get("labels") or [] if l.startswith(PREFIXES)}
            if labels:
                docs.append({"source": source, "id": item["iid"], "title": item["title"],
                             "q": terms.quarter(item["created_at"]), "tokens": labels})
    return docs


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default=str(ROOT / "data/vtk-history"))
    p.add_argument("--last-quarter", default="2026Q2")
    p.add_argument("--min-docs", type=int, default=8)
    p.add_argument("--out", default=str(ROOT / "data/trends/labels.json"))
    args = p.parse_args()

    terms.MIN_DOCS = args.min_docs
    report = {}
    for source in ("mr", "issue"):
        docs = [d for d in load(args.mirror) if d["source"] == source]
        quarters = terms.all_quarters(docs)
        results, n = terms.analyze(docs, quarters, args.last_quarter)
        ranked = {kind: sorted((r for r in results if r["kind"] == kind), key=lambda r: -r["score"])
                  for kind in ("emerging", "past", "fading")}
        ranked["all"] = sorted(results, key=lambda r: -r["docs"])
        for r in results:
            r["examples"] = terms.examples(docs, r["token"])
        report[source] = {"quarters": quarters[:len(n)], "documents_per_quarter": n, "ranked": ranked}
        print(f"{source}: {len(docs)} labeled documents from {quarters[0]}; "
              + ", ".join(f"{r['token']} {r['kind']} {r['ratio']}" for r in ranked["all"][:12]))
    json.dump(report, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
