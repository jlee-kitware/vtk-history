#!/usr/bin/env python3
"""Proposed area labels for VTK's module groups (Common, Filters, IO, Rendering, ...).

VTK's existing area labels cover some module groups (area:rendering, area:io, area:interaction) and
none of others, so a merge request that only changes Common/DataModel gets no label. This proposes
one label per top-level group, reusing the existing label where one matches, with the module
(Common/DataModel, Filters/AMR) as the sub-area.

  merge request   the modules of the files it changes, counted by file
  issue           the modules of the files changed by merge requests that link it; otherwise the
                  modules of the VTK classes it names (ontology/entities.json), leaving out classes
                  named in more than 2% of issues (vtkRenderer, vtkActor and other example boilerplate)

Evaluated on issues that have both: how often the group from the classes an issue names matches
the group its linked merge requests changed most.

Writes data/labels/module_eval.json and data/labels/MODULE_LABELS.md.

Usage:
  python triage/module_labels.py
"""

import argparse
import glob
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLASS = re.compile(r"\bvtk[A-Z][A-Za-z0-9]+")
COMMENT = re.compile(r"<!--.*?-->", re.S)
ISSUE = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?#|gitlab\.kitware\.com/vtk/vtk/-?/?issues/)(\d{2,6})\b")
GROUP_LABEL = {
    "Rendering": "area:rendering", "IO": "area:io", "Interaction": "area:interaction", "Web": "area:web",
    "Serialization": "area:serialization", "GUISupport": "area:qt", "Accelerators": "area:vtkm",
    "CMake": "area:build", ".gitlab": "area:build", "Documentation": "area:doc", "ThirdParty": "area:third-party",
    "Common": "area:common", "Filters": "area:filters", "Imaging": "area:imaging", "Parallel": "area:parallel",
    "Charts": "area:charts", "Views": "area:views", "Infovis": "area:infovis", "Geovis": "area:geovis",
    "Domains": "area:domains", "Wrapping": "area:wrapping",
}
NEW_LABELS = {l for g, l in GROUP_LABEL.items() if g in
              ("Common", "Filters", "Imaging", "Parallel", "Charts", "Views", "Infovis", "Geovis", "Domains", "Wrapping")}
BOILERPLATE = 0.02


class Modules:
    def __init__(self, entities=ROOT / "ontology/entities.json"):
        e = json.loads(Path(entities).read_text())
        self.dirs = e["directories"]
        self.class_dir = {c: str(Path(v["header"]).parent) for c, v in e["classes"].items() if v.get("header")}

    def module_dir(self, path):
        p = Path(path)
        for parent in [p.parent, *p.parent.parents]:
            if str(parent) in self.dirs:
                return str(parent)
        return None

    @staticmethod
    def group(path):
        top = Path(path).parts[0] if Path(path).parts else ""
        return top if top in GROUP_LABEL else None

    def from_paths(self, paths):
        """[(label, module or top directory, files)] most files first."""
        counts = Counter()
        for path in paths:
            if path.startswith("Documentation/release/"):
                continue
            g = self.group(path)
            if g:
                counts[(GROUP_LABEL[g], self.module_dir(path) or g)] += 1
        return [(l, m, n) for (l, m), n in counts.most_common()]

    def from_classes(self, classes):
        counts = Counter()
        for c in classes:
            d = self.class_dir.get(c)
            if d and self.group(d):
                counts[(GROUP_LABEL[self.group(d)], d)] += 1
        return [(l, m, n) for (l, m), n in counts.most_common()]


def by_label(rows):
    totals = Counter()
    for label, _module, n in rows:
        totals[label] += n
    return totals


def mr_files(commits_db=ROOT / "data/index/commits.sqlite"):
    out = defaultdict(list)
    for mr, files in sqlite3.connect(commits_db).execute("SELECT mr, files FROM commits WHERE mr IS NOT NULL"):
        out[mr] += json.loads(files or "[]")
    return out


def load(mirror):
    issues, links = {}, defaultdict(set)
    for f in glob.glob(f"{mirror}/issues/*.json"):
        i = json.load(open(f))["issue"]
        text = f"{i['title']}\n{COMMENT.sub('', i.get('description') or '')}"
        issues[i["iid"]] = {"classes": set(CLASS.findall(text)), "state": i["state"],
                            "areas": {l for l in i.get("labels") or [] if l.startswith("area:")}}
    mrs = {}
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        m = json.load(open(f))["merge_request"]
        mrs[m["iid"]] = {"state": m["state"], "areas": {l for l in m.get("labels") or [] if l.startswith("area:")}}
        for n in ISSUE.findall(f"{m['title']}\n{m.get('description') or ''}"):
            links[int(n)].add(m["iid"])
    return issues, mrs, links


def boilerplate(issues):
    df = Counter(c for v in issues.values() for c in v["classes"])
    return {c for c, n in df.items() if n > BOILERPLATE * len(issues)}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default=str(ROOT / "data/vtk-history"))
    p.add_argument("--out", default=str(ROOT / "data/labels"))
    args = p.parse_args()

    mod = Modules()
    issues, mrs, links = load(args.mirror)
    files = mr_files()
    common = boilerplate(issues)

    agree = total = 0
    examples = []
    issue_labels, mr_labels = {}, {}
    for m in mrs:
        if files.get(m):
            rows = by_label(mod.from_paths(files[m]))
            if rows:
                mr_labels[m] = rows.most_common(1)[0][0]
    for i, v in issues.items():
        named = v["classes"] - common
        from_classes = by_label(mod.from_classes(named))
        linked = [p for m in links.get(i, ()) for p in files.get(m, [])]
        from_files = by_label(mod.from_paths(linked))
        if from_files:
            issue_labels[i] = from_files.most_common(1)[0][0]
        elif from_classes:
            issue_labels[i] = from_classes.most_common(1)[0][0]
        if from_files and from_classes:
            total += 1
            hit = from_classes.most_common(1)[0][0] == from_files.most_common(1)[0][0]
            agree += hit
            if not hit and len(examples) < 10:
                examples.append((i, from_classes.most_common(1)[0][0], from_files.most_common(1)[0][0]))

    def coverage(labels, items):
        c = Counter(labels.values())
        return [{"label": l, "count": n, "new": l in NEW_LABELS} for l, n in c.most_common()]

    def gained(labels, items):
        return sum(1 for k, l in labels.items() if not items[k]["areas"])

    report = {
        "boilerplate_classes": len(common),
        "issues_naming_classes": sum(bool(v["classes"] - common) for v in issues.values()),
        "class_vs_mr": {"issues": total, "agree": agree, "share": round(agree / total, 3) if total else None,
                        "disagreements": examples},
        "issues": {"total": len(issues), "with_group_label": len(issue_labels),
                   "unlabeled_now_gaining": gained(issue_labels, issues), "by_label": coverage(issue_labels, issues)},
        "mrs": {"total": len(mrs), "with_group_label": len(mr_labels),
                "unlabeled_now_gaining": gained(mr_labels, mrs), "by_label": coverage(mr_labels, mrs)},
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(out / "module_eval.json", "w"), indent=1)

    cv = report["class_vs_mr"]
    lines = ["# Module group labels", "",
             f"Classes named by issues agree with the group their linked merge requests changed most for "
             f"{cv['agree']} of {cv['issues']} issues ({cv['share']:.0%}). {len(common)} classes named in more than "
             f"{BOILERPLATE:.0%} of issues are left out as example boilerplate.", "",
             f"Merge requests: {len(mr_labels)} of {len(mrs)} get a group label from their files; "
             f"{report['mrs']['unlabeled_now_gaining']} of them have no area label today.",
             f"Issues: {len(issue_labels)} of {len(issues)} get one (from linked merge requests or named classes); "
             f"{report['issues']['unlabeled_now_gaining']} have no area label today.", "",
             "| Label | MRs | Issues | New label |", "| --- | --- | --- | --- |"]
    mc = {r["label"]: r["count"] for r in report["mrs"]["by_label"]}
    ic = {r["label"]: r["count"] for r in report["issues"]["by_label"]}
    for l in sorted(set(mc) | set(ic), key=lambda l: -(mc.get(l, 0) + ic.get(l, 0))):
        lines.append(f"| {l} | {mc.get(l, 0)} | {ic.get(l, 0)} | {'yes' if l in NEW_LABELS else ''} |")
    (out / "MODULE_LABELS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("disagreements (issue, from classes, from linked MR):", examples)


if __name__ == "__main__":
    main()
