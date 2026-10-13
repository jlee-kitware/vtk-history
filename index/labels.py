#!/usr/bin/env python3
"""GitLab labels on VTK issues and merge requests, stored in the search index.

Each row of data/index/docs.sqlite gets a labels column holding the GitLab labels of the issue
or merge request it belongs to, as ",area:rendering,triage:confirmed,". Review threads and
release notes take the labels of their MR. build_index.py calls apply(); run this file to add
the column to an index built before labels were stored.

Usage:
  python index/labels.py              # add or refresh the labels column
  python index/labels.py --counts     # labels in use, with issue and MR counts
"""

import argparse
import glob
import json
import sqlite3
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "data/vtk-history"


def labels_by_ref(mirror=MIRROR):
    """{'#123': [...], '!456': [...]} for every mirrored issue and MR that has labels."""
    out = {}
    for kind, key, mark in (("issues", "issue", "#"), ("merge_requests", "merge_request", "!")):
        for f in glob.glob(f"{mirror}/{kind}/*.json"):
            item = json.load(open(f))[key]
            if item.get("labels"):
                out[f"{mark}{item['iid']}"] = sorted(item["labels"])
    return out


def encode(labels):
    return f",{','.join(labels)}," if labels else ""


def apply(db, mirror=MIRROR):
    con = sqlite3.connect(db)
    cols = {r[1] for r in con.execute("PRAGMA table_info(docs)")}
    if "labels" not in cols:
        con.execute("ALTER TABLE docs ADD COLUMN labels TEXT DEFAULT ''")
    by_ref = labels_by_ref(mirror)
    con.execute("UPDATE docs SET labels = ''")
    con.executemany("UPDATE docs SET labels = ? WHERE ref = ? AND kind IN ('issue', 'mr', 'thread', 'note')",
                    [(encode(v), k) for k, v in by_ref.items()])
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM docs WHERE labels != ''").fetchone()[0]
    con.close()
    return n


def counts(mirror=MIRROR):
    """[(label, issues, mrs)] sorted by total use."""
    issues, mrs = Counter(), Counter()
    for ref, labels in labels_by_ref(mirror).items():
        (issues if ref.startswith("#") else mrs).update(labels)
    return sorted(((l, issues[l], mrs[l]) for l in set(issues) | set(mrs)), key=lambda x: -(x[1] + x[2]))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--index", default=str(ROOT / "data/index/docs.sqlite"))
    p.add_argument("--counts", action="store_true")
    args = p.parse_args()
    if args.counts:
        for label, i, m in counts():
            print(f"{i:5} issues {m:5} MRs  {label}")
        return
    print(f"labeled {apply(args.index)} index rows")


if __name__ == "__main__":
    main()
