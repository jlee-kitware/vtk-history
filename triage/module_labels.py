#!/usr/bin/env python3
"""Proposed area labels for VTK's module groups (Common, Filters, IO, Rendering, ...).

VTK's existing area labels cover some module groups (area:rendering, area:io, area:interaction) and
none of others, so a merge request that only changes Common/DataModel gets no label. This proposes
one label per top-level directory, reusing the existing label where one matches, with the module
(Common/DataModel, Filters/AMR) as the sub-area. Evidence, first that applies:

  merge request   the modules of the files it changes: from its commits on master, or for one that
                  was not merged there, from its branch (refs/mr/N, fetched from GitLab) against
                  master, or from the GitLab API (mirror/gitlab_mirror.py files) once the branch is gone. Files from an imported upstream tree (src/, include/ of a third-party
                  project) count as area:third-party; files at the top of the repository as area:build
  issue           the files changed by merge requests that link it; then the VTK classes it names,
                  including classes since removed (where their header lived), module library names
                  (vtkCommonCore) and Qt widgets (QVTK...), leaving out classes
                  named in more than 2% of issues (vtkRenderer, vtkActor and other example boilerplate)
  either          the most similar items by embedding that have a label from their files, used only
                  when the vote reaches the cutoff measured below

Measured on issues whose linked merge requests give a label: how often the named classes, and
separately the similar items, give the same label.

Writes data/labels/module_eval.json, data/labels/MODULE_LABELS.md, and caches
data/labels/removed_classes.json and data/labels/mr_branch_files.json.

Usage:
  python triage/module_labels.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import glob
import json
import re
import sqlite3
import subprocess
from collections import Counter, defaultdict

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/labels"
CLASS = re.compile(r"\b(?:vtk|QVTK)[A-Z][A-Za-z0-9]+")
COMMENT = re.compile(r"<!--.*?-->", re.S)
ISSUE = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?#|gitlab\.kitware\.com/vtk/vtk/-?/?issues/)(\d{2,6})\b")
GROUP_LABEL = {
    "Rendering": "area:rendering", "IO": "area:io", "Interaction": "area:interaction", "Web": "area:web",
    "Serialization": "area:serialization", "GUISupport": "area:qt", "Accelerators": "area:vtkm",
    "CMake": "area:build", ".gitlab": "area:build", ".github": "area:build", "Documentation": "area:doc",
    "Examples": "area:doc", "ThirdParty": "area:third-party", "Remote": "area:third-party",
    "Common": "area:common", "Filters": "area:filters", "Imaging": "area:imaging", "Parallel": "area:parallel",
    "Charts": "area:charts", "Views": "area:views", "Infovis": "area:infovis", "Geovis": "area:geovis",
    "Domains": "area:domains", "Wrapping": "area:wrapping",
}
NEW_LABELS = {GROUP_LABEL[g] for g in
              ("Common", "Filters", "Imaging", "Parallel", "Charts", "Views", "Infovis", "Geovis", "Domains", "Wrapping")}
BOILERPLATE = 0.02
K = 15


def git(*args):
    return subprocess.run(["git", "-C", config.VTK_REPO, *args], capture_output=True, text=True,
                          errors="replace").stdout


class Modules:
    def __init__(self, entities=ROOT / "ontology/entities.json"):
        e = json.loads(Path(entities).read_text())
        self.dirs = e["directories"]
        self.class_dir = {c: str(Path(v["header"]).parent) for c, v in e["classes"].items() if v.get("header")}
        for name, m in e["modules"].items():
            if name.startswith("VTK::") and m.get("directory"):
                self.class_dir.setdefault("vtk" + name[5:], m["directory"])
        self.top = set(git("ls-tree", "-d", "--name-only", "upstream/master").split()) | set(GROUP_LABEL)
        self.top_files = set(git("ls-tree", "--name-only", "upstream/master").split()) - self.top

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
        counts, foreign, toplevel = Counter(), 0, 0
        for path in paths:
            if path.startswith("Documentation/release/"):
                continue
            parts = Path(path).parts
            g = self.group(path)
            if g:
                counts[(GROUP_LABEL[g], self.module_dir(path) or g)] += 1
            elif len(parts) == 1 and parts[0] in self.top_files:
                toplevel += 1
            elif parts[0] not in self.top:
                foreign += 1
        if not counts and foreign:
            counts[("area:third-party", "imported upstream files")] = foreign
        elif not counts and toplevel:
            counts[("area:build", "top-level files")] = toplevel
        return [(l, m, n) for (l, m), n in counts.most_common()]

    def from_classes(self, classes):
        counts = Counter()
        for c in classes:
            d = self.class_dir.get(c) or ("GUISupport/Qt" if c.startswith("QVTK") else None)
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


def removed_classes(cache=OUT / "removed_classes.json"):
    """Classes whose header was deleted at some point, with the directory it lived in."""
    if cache.exists():
        return json.loads(cache.read_text())
    out = {}
    for line in git("log", "--diff-filter=D", "--name-only", "--format=", "upstream/master", "--", "*vtk*.h").splitlines():
        p = Path(line.strip())
        if p.name.startswith("vtk") and p.suffix == ".h" and len(p.parts) > 1:
            out.setdefault(p.stem, str(p.parent))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(out, indent=0, sort_keys=True))
    return out


def branch_files(mrs, files, cache=OUT / "mr_branch_files.json"):
    """Files changed by MRs with no commits on master, from refs/mr/N against its merge base with master."""
    done = json.loads(cache.read_text()) if cache.exists() else {}
    refs = set(git("for-each-ref", "--format=%(refname:lstrip=2)", "refs/mr").split())
    todo = [m for m in mrs if not files.get(m) and str(m) not in done and str(m) in refs]
    for n, m in enumerate(todo, 1):
        base = git("merge-base", "upstream/master", f"refs/mr/{m}").strip()
        done[str(m)] = git("diff", "--name-only", base, f"refs/mr/{m}").split() if base else []
        if n % 500 == 0:
            cache.write_text(json.dumps(done))
            print(f"  branch files: {n}/{len(todo)}", flush=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(done))
    return {int(k): v for k, v in done.items()}


class Labeler:
    def __init__(self, mirror=ROOT / "data/vtk-history", index=None, refresh=False):
        self.mod = Modules()
        self.issues, self.mrs, self.links = {}, {}, defaultdict(set)
        for f in glob.glob(f"{mirror}/issues/*.json"):
            i = json.load(open(f))["issue"]
            text = f"{i['title']}\n{COMMENT.sub('', i.get('description') or '')}"
            self.issues[i["iid"]] = {"classes": set(CLASS.findall(text)), "state": i["state"],
                                     "areas": {l for l in i.get("labels") or [] if l.startswith("area:")}}
        for f in glob.glob(f"{mirror}/merge_requests/*.json"):
            m = json.load(open(f))["merge_request"]
            self.mrs[m["iid"]] = {"state": m["state"], "areas": {l for l in m.get("labels") or []
                                                                 if l.startswith("area:")}}
            for n in ISSUE.findall(f"{m['title']}\n{m.get('description') or ''}"):
                self.links[int(n)].add(m["iid"])
        self.files = mr_files()
        branch = branch_files(self.mrs, self.files) if refresh else {
            int(k): v for k, v in json.loads((OUT / "mr_branch_files.json").read_text()).items()} \
            if (OUT / "mr_branch_files.json").exists() else {}
        for m, paths in branch.items():
            if paths:
                self.files.setdefault(m, paths)
        for p in Path(mirror, "mr_files").glob("*.json"):
            if not self.files.get(int(p.stem)):
                self.files[int(p.stem)] = json.loads(p.read_text())
        for c, d in removed_classes().items():
            self.mod.class_dir.setdefault(c, d)
        df = Counter(c for v in self.issues.values() for c in v["classes"])
        self.common = {c for c, n in df.items() if n > BOILERPLATE * len(self.issues)}
        self.index, self.cutoff = index, 0.6
        self._pool = None

    def direct(self, kind, iid, paths=None, classes=None):
        """(rows, source) from files or named classes, without the similarity fallback."""
        if kind == "mr":
            rows = self.mod.from_paths(paths if paths is not None else self.files.get(iid, []))
            return rows, "files it changes"
        linked = [p for m in self.links.get(iid, ()) for p in self.files.get(m, [])]
        rows = self.mod.from_paths(linked)
        if rows:
            return rows, "files changed by linked MRs"
        named = (classes if classes is not None else self.issues.get(iid, {}).get("classes", set())) - self.common
        return self.mod.from_classes(named), "VTK classes it names"

    def pool(self):
        if self._pool is None:
            rowid = {r[0]: r[1] for r in self.index.con.execute(
                "SELECT ref, rowid FROM docs WHERE kind IN ('issue', 'mr')")}
            refs, labels = [], []
            for m in self.mrs:
                t = by_label(self.direct("mr", m)[0])
                if t and f"!{m}" in rowid:
                    refs.append(f"!{m}")
                    labels.append(t.most_common(1)[0][0])
            for i in self.issues:
                rows = self.mod.from_paths([p for m in self.links.get(i, ()) for p in self.files.get(m, [])])
                if rows and f"#{i}" in rowid:
                    refs.append(f"#{i}")
                    labels.append(by_label(rows).most_common(1)[0][0])
            self._pool = (refs, labels, self.index.vectors[[rowid[r] - 1 for r in refs]], rowid)
        return self._pool

    def similar(self, ref, exclude=(), vector=None):
        """(label, confidence) from the K most similar items that have a label from files."""
        refs, labels, vecs, rowid = self.pool()
        if vector is None:
            if ref not in rowid:
                return None, 0.0
            vector = self.index.vectors[rowid[ref] - 1]
        sims = vecs @ vector
        votes = Counter()
        taken = 0
        for j in np.argsort(-sims):
            if refs[j] == ref or refs[j] in exclude:
                continue
            votes[labels[j]] += float(max(sims[j], 0)) ** 4
            taken += 1
            if taken == K:
                break
        if not votes:
            return None, 0.0
        label, v = votes.most_common(1)[0]
        return label, v / sum(votes.values())

    def label(self, kind, iid, paths=None, classes=None, vector=None):
        rows, source = self.direct(kind, iid, paths, classes)
        if rows or self.index is None:
            return rows, source, None
        ref = f"{'!' if kind == 'mr' else '#'}{iid}"
        exclude = {f"!{m}" for m in self.links.get(iid, ())} if kind == "issue" else set()
        label, conf = self.similar(ref, exclude, vector)
        if label and conf >= self.cutoff:
            return [(label, "similar issues and MRs", 0)], f"similar issues and MRs ({conf:.0%} of the vote)", conf
        return [], "no evidence", conf


def precision_by(results, bins=(0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.0)):
    return [{"confidence_at_least": lo, "items": len(h := [ok for c, ok in results if c >= lo]),
             "precision": round(sum(h) / len(h), 3) if h else None} for lo in bins]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--target", type=float, default=0.9)
    args = p.parse_args()
    sys.path.insert(0, str(ROOT / "index"))
    from search import Index
    lab = Labeler(index=Index(str(ROOT / "data/index")), refresh=True)

    agree, sim_results = [], []
    for i in lab.issues:
        rows = lab.mod.from_paths([p for m in lab.links.get(i, ()) for p in lab.files.get(m, [])])
        if not rows:
            continue
        truth = by_label(rows).most_common(1)[0][0]
        named = by_label(lab.mod.from_classes(lab.issues[i]["classes"] - lab.common))
        if named:
            agree.append(named.most_common(1)[0][0] == truth)
        label, conf = lab.similar(f"#{i}", {f"!{m}" for m in lab.links.get(i, ())})
        if label:
            sim_results.append((conf, label == truth))
    bins = precision_by(sim_results)
    ok = [b["confidence_at_least"] for b in bins if b["precision"] is not None and b["precision"] >= args.target]
    lab.cutoff = min(ok) if ok else 1.0

    result = {"mr": {}, "issue": {}}
    source_counts = {"mr": Counter(), "issue": Counter()}
    for kind, items in (("mr", lab.mrs), ("issue", lab.issues)):
        for iid in items:
            rows, source, _conf = lab.label(kind, iid)
            if rows:
                result[kind][iid] = by_label(rows).most_common(1)[0][0]
                source_counts[kind][source.split(" (")[0]] += 1
            else:
                source_counts[kind]["none"] += 1

    def summary(kind, items):
        c = Counter(result[kind].values())
        return {"total": len(items), "with_group_label": len(result[kind]),
                "unlabeled_now_gaining": sum(1 for k in result[kind] if not items[k]["areas"]),
                "open_without": sum(1 for k, v in items.items() if k not in result[kind] and v["state"] == "opened"),
                "sources": dict(source_counts[kind]),
                "by_label": [{"label": l, "count": n, "new": l in NEW_LABELS} for l, n in c.most_common()]}

    report = {
        "boilerplate_classes": len(lab.common), "cutoff": lab.cutoff,
        "class_vs_mr": {"issues": len(agree), "agree": sum(agree),
                        "share": round(sum(agree) / len(agree), 3) if agree else None},
        "similar_vs_mr": {"issues": len(sim_results), "by_confidence": bins},
        "mrs": summary("mr", lab.mrs), "issues": summary("issue", lab.issues),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(report, open(OUT / "module_eval.json", "w"), indent=1)

    cv = report["class_vs_mr"]
    lines = ["# Module group labels", "",
             f"Classes named by issues agree with the group their linked merge requests changed most for "
             f"{cv['agree']} of {cv['issues']} issues ({cv['share']:.0%}).",
             f"Similar items (excluding the issue's own linked merge requests) agree, by confidence:", "",
             "| Confidence at least | Issues | Same label |", "| --- | --- | --- |"]
    lines += [f"| {b['confidence_at_least']} | {b['items']} | {b['precision'] if b['precision'] is not None else ''} |"
              for b in bins]
    lines += ["", f"Similarity is used only at confidence {lab.cutoff} or more ({args.target:.0%} agreement).", ""]
    for kind, name in (("mrs", "Merge requests"), ("issues", "Issues")):
        s = report[kind]
        lines.append(f"{name}: {s['with_group_label']} of {s['total']} get a group label "
                     f"({s['unlabeled_now_gaining']} have no area label today); {s['open_without']} open ones "
                     f"remain without. Sources: {s['sources']}.")
    lines += ["", "| Label | MRs | Issues | New label |", "| --- | --- | --- | --- |"]
    mc = {r["label"]: r["count"] for r in report["mrs"]["by_label"]}
    ic = {r["label"]: r["count"] for r in report["issues"]["by_label"]}
    for l in sorted(set(mc) | set(ic), key=lambda l: -(mc.get(l, 0) + ic.get(l, 0))):
        lines.append(f"| {l} | {mc.get(l, 0)} | {ic.get(l, 0)} | {'yes' if l in NEW_LABELS else ''} |")
    (OUT / "MODULE_LABELS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
