#!/usr/bin/env python3
"""Suggest GitLab area labels (area:rendering, area:build, ...) for VTK issues that have none.

Evidence for an issue, each turned into a vote per label:
  text    the most similar labeled issues and MRs by embedding (data/index/vectors.npy)
  files   directories changed by MRs whose description links the issue, scored by how
          often MRs touching each directory carry each label
  mr      area labels on the linked MRs themselves

Evaluated by leave-one-out on the issues maintainers already labeled: each labeled issue
is treated as unlabeled, and the top suggestion counts as correct when it is one of the
issue's own area labels. Precision is reported per label and per confidence level, so a
reviewer can choose a threshold before applying anything.

Also counts, per top-level source directory, how many MRs changed it and how many of those carry
any area label, which shows the code areas no label covers.

Writes data/labels/area_eval.json, data/labels/AREA_LABELS.md, and
data/labels/area_suggestions.csv (one row per unlabeled issue, highest confidence first).

Usage:
  python triage/area_labels.py
"""

import argparse
import csv
import glob
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "index"))
from search import Index  # noqa: E402

ISSUE = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?#|gitlab\.kitware\.com/vtk/vtk/-?/?issues/)(\d{2,6})\b")
MIN_ITEMS = 8
K = 15
BINS = (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.0)


def area(labels):
    return {l for l in labels or [] if l.startswith("area:")}


def load_items(mirror):
    issues, mrs, links = {}, {}, defaultdict(set)
    for f in glob.glob(f"{mirror}/issues/*.json"):
        i = json.load(open(f))["issue"]
        issues[i["iid"]] = {"title": i["title"], "state": i["state"], "created": i["created_at"][:10],
                            "url": i["web_url"], "areas": area(i.get("labels"))}
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        m = json.load(open(f))["merge_request"]
        mrs[m["iid"]] = area(m.get("labels"))
        for n in ISSUE.findall(f"{m['title']}\n{m.get('description') or ''}"):
            links[int(n)].add(m["iid"])
    return issues, mrs, links


def mr_dirs(commits_db):
    out = defaultdict(set)
    con = sqlite3.connect(commits_db)
    for mr, files in con.execute("SELECT mr, files FROM commits WHERE mr IS NOT NULL"):
        for path in json.loads(files or "[]"):
            parts = Path(path).parts
            if len(parts) > 1:
                out[mr].add("/".join(parts[:2]))
    return out


def normalize(votes):
    total = sum(votes.values())
    return {k: v / total for k, v in votes.items()} if total else {}


class Suggester:
    def __init__(self, index, issues, mrs, links, dirs, labels):
        self.labels = labels
        self.issues, self.mrs, self.links, self.dirs = issues, mrs, links, dirs
        rowid = {r["ref"]: r["rowid"] for r in index.con.execute(
            "SELECT rowid, ref FROM docs WHERE kind IN ('issue', 'mr')")}
        pool = [(f"#{i}", v["areas"]) for i, v in issues.items() if v["areas"] & labels] + \
               [(f"!{m}", a) for m, a in mrs.items() if a & labels]
        pool = [(ref, a & labels) for ref, a in pool if ref in rowid]
        self.pool_refs = [ref for ref, _ in pool]
        self.pool_areas = [a for _, a in pool]
        self.pool_vecs = index.vectors[[rowid[ref] - 1 for ref in self.pool_refs]]
        self.vec = {ref: index.vectors[rowid[ref] - 1] for ref in (f"#{i}" for i in issues) if ref in rowid}
        self.dir_votes = defaultdict(Counter)
        for m, a in mrs.items():
            for d in dirs.get(m, ()):
                for l in a & labels:
                    self.dir_votes[d][l] += 1

    def evidence(self, iid):
        ref = f"#{iid}"
        out = {}
        if ref in self.vec:
            sims = self.pool_vecs @ self.vec[ref]
            votes = Counter()
            for j in np.argsort(-sims)[:K + 1]:
                if self.pool_refs[j] != ref:
                    for l in self.pool_areas[j]:
                        votes[l] += float(max(sims[j], 0)) ** 4
            out["text"] = normalize(votes)
        linked = self.links.get(iid, set())
        files = Counter()
        for m in linked:
            for d in self.dirs.get(m, ()):
                files.update(normalize(self.dir_votes.get(d, {})))
        if files:
            out["files"] = normalize(files)
        mr_labels = Counter(l for m in linked for l in self.mrs.get(m, set()) & self.labels)
        if mr_labels:
            out["mr"] = normalize(mr_labels)
        return out

    @staticmethod
    def combine(ev, use=("text", "files", "mr")):
        votes = Counter()
        for name in use:
            votes.update(ev.get(name, {}))
        ranked = votes.most_common()
        if not ranked:
            return None, 0.0, []
        total = sum(v for _, v in ranked)
        return ranked[0][0], ranked[0][1] / total, ranked


def precision_table(results):
    rows = []
    for lo in BINS:
        hits = [ok for conf, ok in results if conf >= lo]
        rows.append({"confidence_at_least": lo, "issues": len(hits),
                     "precision": round(sum(hits) / len(hits), 3) if hits else None})
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default=str(ROOT / "data/vtk-history"))
    p.add_argument("--out", default=str(ROOT / "data/labels"))
    args = p.parse_args()

    index = Index(str(ROOT / "data/index"))
    issues, mrs, links = load_items(args.mirror)
    counts = Counter(l for v in issues.values() for l in v["areas"]) + Counter(l for a in mrs.values() for l in a)
    labels = {l for l, n in counts.items() if n >= MIN_ITEMS}
    dirs = mr_dirs(ROOT / "data/index/commits.sqlite")
    s = Suggester(index, issues, mrs, links, dirs, labels)

    labeled = [i for i, v in issues.items() if v["areas"] & labels]
    majority = Counter(l for i in labeled for l in issues[i]["areas"] & labels).most_common(1)[0][0]
    variants = {"text": ("text",), "files": ("files",), "mr": ("mr",), "combined": ("text", "files", "mr")}
    scored = {name: [] for name in variants}
    per_label = defaultdict(lambda: {"true": 0, "suggested": 0, "correct": 0})
    for i in labeled:
        truth = issues[i]["areas"] & labels
        ev = s.evidence(i)
        for name, use in variants.items():
            top, conf, _ = s.combine(ev, use)
            if top:
                scored[name].append((conf, top in truth))
        top, _, _ = s.combine(ev)
        for l in truth:
            per_label[l]["true"] += 1
        if top:
            per_label[top]["suggested"] += 1
            per_label[top]["correct"] += top in truth

    combined = scored["combined"]
    report = {
        "labeled_issues": len(labeled), "labels": sorted(labels), "majority_label": majority,
        "majority_precision": round(sum(majority in issues[i]["areas"] for i in labeled) / len(labeled), 3),
        "variants": {name: {"issues_with_evidence": len(r),
                            "precision": round(sum(ok for _, ok in r) / len(r), 3) if r else None}
                     for name, r in scored.items()},
        "by_confidence": precision_table(combined),
        "by_label": {l: dict(v, precision=round(v["correct"] / v["suggested"], 3) if v["suggested"] else None,
                             recall=round(v["correct"] / v["true"], 3) if v["true"] else None)
                     for l, v in sorted(per_label.items(), key=lambda x: -x[1]["true"])},
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(out / "area_eval.json", "w"), indent=1)

    bins = report["by_confidence"]

    def expected(conf):
        return next(b["precision"] for b in bins if conf >= b["confidence_at_least"])

    rows = []
    for i, v in issues.items():
        if v["areas"]:
            continue
        ev = s.evidence(i)
        top, conf, ranked = s.combine(ev)
        if not top:
            continue
        rows.append({"issue": i, "state": v["state"], "created": v["created"], "suggested": top,
                     "confidence": round(conf, 2), "expected_precision": expected(conf),
                     "runner_up": ranked[1][0] if len(ranked) > 1 else "",
                     "evidence": "+".join(k for k in ("text", "files", "mr") if top in ev.get(k, {})),
                     "linked_mrs": " ".join(f"!{m}" for m in sorted(links.get(i, ()))),
                     "title": v["title"], "url": v["url"]})
    rows.sort(key=lambda r: (-r["confidence"], r["state"] != "opened", r["issue"]))
    with open(out / "area_suggestions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    lines = ["# Area label suggestions: evaluation", "",
             f"Leave-one-out on {len(labeled)} issues that already carry one of {len(labels)} area labels "
             f"(labels used on at least {MIN_ITEMS} issues or MRs). A suggestion is correct when it is one of the "
             f"issue's own area labels. Always suggesting {majority} is correct for "
             f"{report['majority_precision']:.0%}.", "",
             "| Evidence | Issues with this evidence | Top suggestion correct |", "| --- | --- | --- |"]
    for name, v in report["variants"].items():
        lines.append(f"| {name} | {v['issues_with_evidence']} | "
                     + (f"{v['precision']:.0%} |" if v["precision"] is not None else "|"))
    lines += ["", "| Confidence at least | Issues | Top suggestion correct |", "| --- | --- | --- |"]
    for b in bins:
        lines.append(f"| {b['confidence_at_least']:.1f} | {b['issues']} | "
                     + (f"{b['precision']:.0%} |" if b["precision"] is not None else "|"))
    lines += ["", "| Label | Labeled issues | Suggested | Precision | Recall |", "| --- | --- | --- | --- | --- |"]
    for l, v in report["by_label"].items():
        prec = f"{v['precision']:.0%}" if v["precision"] is not None else ""
        rec = f"{v['recall']:.0%}" if v["recall"] is not None else ""
        lines.append(f"| {l} | {v['true']} | {v['suggested']} | {prec} | {rec} |")
    tops, tops_labeled = Counter(), Counter()
    for m, ds in dirs.items():
        for t in {d.split("/")[0] for d in ds}:
            tops[t] += 1
            tops_labeled[t] += bool(mrs.get(m))
    report["directories"] = {t: {"mrs": n, "with_area_label": tops_labeled[t]} for t, n in tops.most_common(15)}
    json.dump(report, open(out / "area_eval.json", "w"), indent=1)
    lines += ["", "Coverage by code area: merge requests that changed each top-level directory, and the share "
                  "carrying any area label.", "", "| Directory | MRs | With an area label |", "| --- | --- | --- |"]
    for t, n in tops.most_common(15):
        lines.append(f"| {t} | {n} | {tops_labeled[t] / n:.0%} |")
    opened = sum(r["state"] == "opened" for r in rows)
    lines += ["", f"Suggestions written for {len(rows)} unlabeled issues ({opened} open) to area_suggestions.csv.", ""]
    (out / "AREA_LABELS.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
