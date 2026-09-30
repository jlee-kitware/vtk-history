#!/usr/bin/env python3
"""Suggest reviewers for a VTK merge request from who reviewed and wrote the code it touches.

For every mirrored MR we record its author, the people who commented on it (the MR author, bots and
system notes excluded) with the time of their first comment, and the files it changed (from its merge
commit on master, or from its diff notes for MRs that are not merged). A candidate's score for a new MR
sums, over earlier MRs, how closely each earlier MR's files match the new MR's files (same file 1, same
directory 0.5, same module 0.1), halved every six months of age: reviewing counts fully, authoring at 0.6.
Only people who commented on some MR in the 180 days before are suggested.

Usage:
  python people/expertise.py build                  # data/people/mrs.jsonl from the mirror and the VTK clone
  python people/expertise.py suggest 13389 [--top 5]
  python people/expertise.py backtest [--since 2025-01-01]
  python people/expertise.py quality                # are higher-ranked reviewers' comments acted on more?
"""

import argparse
import glob
import json
import os
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "data/vtk-history/merge_requests"
TABLE = ROOT / "data/people/mrs.jsonl"
REPO = "/home/jlee/gitsync/vtk"
BOTS = {"kwrobot", "ghost", "vtk-bot", "kitware-robot"}
LEVELS = ((0, 1.0), (1, 0.5), (2, float(os.environ.get("EXP_MODULE", 0.1))))
AUTHOR_WEIGHT = float(os.environ.get("EXP_AUTHOR", 0.6))
HALF_LIFE_DAYS = int(os.environ.get("EXP_HALF_LIFE", 180))
SPECIALIST = float(os.environ.get("EXP_SPECIALIST", 0))
ACTIVE_DAYS = 180


def is_bot(user):
    return user in BOTS or "bot" in user.lower() or user.startswith("project_") or user.startswith("group_")


def when(stamp):
    return datetime.fromisoformat(stamp[:19])


def keys(path):
    """The file itself, its directory, and its module (first two path parts)."""
    parts = path.split("/")
    return [path, "/".join(parts[:-1]), "/".join(parts[:2]) if len(parts) > 2 else None]


def merge_files():
    out = subprocess.run(["git", "-C", REPO, "log", "--first-parent", "--diff-merges=first-parent", "--name-only",
                          "--format=@%H", "upstream/master"], capture_output=True, text=True, check=True).stdout
    files, sha = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            sha = line[1:]
            files[sha] = []
        elif line and sha:
            files[sha].append(line)
    return files


def build():
    by_sha = merge_files()
    rows = []
    for f in glob.glob(str(MIRROR / "*.json")):
        rec = json.load(open(f))
        mr = rec["merge_request"]
        author = mr["author"]["username"]
        first, paths = {}, set()
        for d in rec.get("discussions") or []:
            for n in d["notes"]:
                if n.get("system"):
                    continue
                user = n["author"]["username"]
                pos = n.get("position") or {}
                if pos.get("new_path"):
                    paths.add(pos["new_path"])
                if user == author or is_bot(user):
                    continue
                first[user] = min(first.get(user, n["created_at"]), n["created_at"])
        sha = mr.get("merge_commit_sha") or mr.get("squash_commit_sha")
        files = by_sha.get(sha) or sorted(paths)
        rows.append({"iid": mr["iid"], "created": mr["created_at"][:19], "state": mr["state"], "author": author,
                     "title": mr["title"], "files": files, "from_merge": sha in by_sha,
                     "reviewers": [{"user": u, "first": t[:19]} for u, t in sorted(first.items(), key=lambda x: x[1])]})
    TABLE.parent.mkdir(parents=True, exist_ok=True)
    with open(TABLE, "w") as out:
        for r in sorted(rows, key=lambda r: r["created"]):
            out.write(json.dumps(r) + "\n")
    print(f"{len(rows)} MRs, {sum(r['from_merge'] for r in rows)} with files from their merge commit")


class Expertise:
    def __init__(self):
        self.mrs = [json.loads(line) for line in open(TABLE)]
        self.by_iid = {m["iid"]: m for m in self.mrs}
        self.index = [defaultdict(list) for _ in LEVELS]
        for m in self.mrs:
            for level, _ in LEVELS:
                for key in {keys(p)[level] for p in m["files"]} - {None}:
                    self.index[level][key].append(m["iid"])

    def overlap(self, files):
        """For each earlier MR touching the same files, directories, or modules: mean best closeness over our files."""
        best = defaultdict(lambda: [0.0] * len(files))
        for i, path in enumerate(files):
            for (level, weight), key in zip(LEVELS, keys(path)):
                for iid in self.index[level].get(key, ()) if key else ():
                    if best[iid][i] < weight:
                        best[iid][i] = weight
        return {iid: sum(v) / len(files) for iid, v in best.items()}

    def scores(self, files, at):
        at_dt = when(at)
        score = defaultdict(float)
        for iid, closeness in self.overlap(files).items():
            m = self.by_iid[iid]
            if m["created"] >= at:
                continue
            decay = 0.5 ** ((at_dt - when(m["created"])).days / HALF_LIFE_DAYS)
            for r in m["reviewers"]:
                if r["first"] < at:
                    score[r["user"]] += closeness * decay
            score[m["author"]] += AUTHOR_WEIGHT * closeness * decay
        return score

    def suggest(self, files, at, exclude=(), top=5):
        at_dt = when(at)
        active_since = (at_dt - timedelta(days=ACTIVE_DAYS)).isoformat()
        active, responses = set(), defaultdict(list)
        for m in self.mrs:
            if m["created"] >= at:
                break
            for r in m["reviewers"]:
                if active_since <= r["first"] < at:
                    active.add(r["user"])
                    responses[r["user"]].append((when(r["first"]) - when(m["created"])).total_seconds() / 86400)
        score, detail = defaultdict(float), defaultdict(lambda: {"reviewed": [], "authored": []})
        for iid, closeness in self.overlap(files).items():
            m = self.by_iid[iid]
            if m["created"] >= at:
                continue
            decay = 0.5 ** ((at_dt - when(m["created"])).days / HALF_LIFE_DAYS)
            for r in m["reviewers"]:
                if r["first"] < at:
                    score[r["user"]] += closeness * decay
                    detail[r["user"]]["reviewed"].append((closeness, m))
            score[m["author"]] += AUTHOR_WEIGHT * closeness * decay
            detail[m["author"]]["authored"].append((closeness, m))
        if SPECIALIST:
            volume = defaultdict(int)
            for gaps_user, gaps in responses.items():
                volume[gaps_user] = len(gaps)
            score = {u: v / (1 + volume[u]) ** SPECIALIST for u, v in score.items()}
        ranked = [u for u in sorted(score, key=score.get, reverse=True)
                  if u in active and u not in exclude and not is_bot(u)][:top]
        out = []
        for u in ranked:
            rev, auth = detail[u]["reviewed"], detail[u]["authored"]
            recent = max((m for _, m in rev + auth), key=lambda m: m["created"])
            gaps = responses[u]
            near = lambda items: sum(any(c >= 0.5 for c in [closeness]) for closeness, _ in items)
            out.append({"user": u, "score": round(score[u], 2), "reviewed": near(rev),
                        "reviewed_module": len(rev), "authored": near(auth),
                        "reviewed_same_files": sum(c == 1.0 for c, _ in rev),
                        "latest": {"iid": recent["iid"], "date": recent["created"][:10]},
                        "median_first_response_days": round(statistics.median(gaps), 1) if gaps else None})
        return out

    def most_active(self, at, exclude=(), top=5):
        since = (when(at) - timedelta(days=ACTIVE_DAYS)).isoformat()
        count = defaultdict(int)
        for m in self.mrs:
            for r in m["reviewers"]:
                if since <= r["first"] < at:
                    count[r["user"]] += 1
        return [u for u in sorted(count, key=count.get, reverse=True) if u not in exclude and not is_bot(u)][:top]


def reason(s):
    parts = []
    if s["reviewed"]:
        parts.append(f"reviewed {s['reviewed']} MR{'s' if s['reviewed'] != 1 else ''} on these files or directories"
                     + (f" ({s['reviewed_same_files']} on the same files)" if s["reviewed_same_files"] else ""))
    if s["reviewed_module"] > s["reviewed"]:
        parts.append(f"{s['reviewed_module']} in these modules")
    if s["authored"]:
        parts.append(f"wrote {s['authored']} MR{'s' if s['authored'] != 1 else ''} on these files or directories")
    parts.append(f"latest !{s['latest']['iid']} on {s['latest']['date']}")
    if s["median_first_response_days"] is not None:
        parts.append(f"first reply after a median {s['median_first_response_days']} days")
    return ", ".join(parts)


def backtest(since):
    ex = Expertise()
    tests = [m for m in ex.mrs if m["created"] >= since and m["reviewers"] and m["files"]]
    hits = {"expertise": [0, 0, 0], "most active": [0, 0, 0]}
    for m in tests:
        actual = {r["user"] for r in m["reviewers"]}
        first = m["reviewers"][0]["user"]
        picks = {"expertise": [s["user"] for s in ex.suggest(m["files"], m["created"], exclude={m["author"]}, top=3)],
                 "most active": ex.most_active(m["created"], exclude={m["author"]}, top=3)}
        for name, p in picks.items():
            hits[name][0] += bool(p and p[0] in actual)
            hits[name][1] += bool(set(p) & actual)
            hits[name][2] += first in p
    n = len(tests)
    print(f"{n} MRs since {since} with at least one reviewer; each ranking uses only data from before the MR")
    print(f"{'method':14} {'top pick reviewed':>18} {'any of top 3 reviewed':>22} {'first reviewer in top 3':>24}")
    for name, (h1, h3, hf) in hits.items():
        print(f"{name:14} {h1 / n:18.1%} {h3 / n:22.1%} {hf / n:24.1%}")


def quality():
    ex = Expertise()
    severity = {}
    with open(ROOT / "data/review_labels.jsonl") as f:
        for line in f:
            lab = json.loads(line)
            severity[lab["discussion_id"]] = lab.get("severity")
    acted, major = defaultdict(list), defaultdict(list)
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            key = (e["mr"]["iid"], e["reviewer"])
            if e["kind"] == "line":
                acted[key].append(bool(e.get("acted_on")))
            if e["discussion_id"] in severity:
                major[key].append(severity[e["discussion_id"]] == "major")
    by_mr = defaultdict(dict)
    for (iid, user) in set(acted) | set(major):
        by_mr[iid][user] = (acted.get((iid, user), []), major.get((iid, user), []))
    buckets = defaultdict(lambda: [0, 0, 0, 0])
    for iid, users in by_mr.items():
        m = ex.by_iid.get(iid)
        if not m or not m["files"]:
            continue
        score = ex.scores(m["files"], m["created"])
        order = [u for u in sorted(score, key=score.get, reverse=True) if u != m["author"] and not is_bot(u)]
        rank = {u: i + 1 for i, u in enumerate(order)}
        for user, (flags, majors) in users.items():
            r = rank.get(user)
            bucket = "1" if r == 1 else "2-3" if r and r <= 3 else "4-10" if r and r <= 10 else "below 10 or none"
            b = buckets[bucket]
            b[0] += sum(flags)
            b[1] += len(flags)
            b[2] += sum(majors)
            b[3] += len(majors)
    print("by the reviewer's expertise rank for that MR (computed from earlier MRs)")
    for name in ("1", "2-3", "4-10", "below 10 or none"):
        a, n, mj, labeled = buckets[name]
        if n:
            print(f"  rank {name:17} {n:6} line comments {a / n:6.1%} acted on;"
                  f" {labeled:6} labeled threads {mj / labeled:6.1%} major")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["build", "suggest", "backtest", "quality"])
    ap.add_argument("iid", nargs="?", type=int)
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--since", default="2025-01-01")
    args = ap.parse_args()
    if args.command == "build":
        build()
    elif args.command == "backtest":
        backtest(args.since)
    elif args.command == "quality":
        quality()
    else:
        ex = Expertise()
        m = ex.by_iid.get(args.iid)
        if not m:
            sys.exit(f"!{args.iid} is not in the mirror")
        print(f"!{m['iid']} {m['title']} by {m['author']}, {len(m['files'])} files")
        for s in ex.suggest(m["files"], m["created"], exclude={m["author"]}, top=args.top):
            print(f"  {s['user']:22} {s['score']:6.2f}  {reason(s)}")
        print("actual reviewers:", ", ".join(r["user"] for r in m["reviewers"]) or "none")


if __name__ == "__main__":
    main()
