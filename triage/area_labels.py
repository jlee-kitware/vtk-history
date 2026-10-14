#!/usr/bin/env python3
"""Suggest GitLab labels (area:rendering, lang:python, ...) for VTK issues that have none.

Evidence for an issue, each turned into a vote per area label:
  text    the most similar labeled issues and MRs by embedding (data/index/vectors.npy)
  files   directories changed by MRs whose description links the issue, scored by how
          often MRs touching each directory carry each label
  mr      area labels on the linked MRs themselves
Labels that name a technology (area:wasm, area:webgpu, area:qt, ...) are suggested from similar issues
or changed files only when the issue's own title or description names that technology. Their code
overlaps with general rendering code, so similar issues alone pulled them onto desktop issues.

  field   the issue template's Configuration lines ("Language and version: Python 3.12",
          "Graphics backend: WebGPU"), matched exactly; HTML comments are ignored, so the
          template's own examples never match

The closest match is suggested only when its confidence reaches a cutoff chosen so that,
on issues maintainers already labeled, suggestions at or above it were right at least
--target of the time in both evaluations below. Below the cutoff the issue is marked "no label fits", with the
best guess kept in its own column, since an issue there often belongs to an area that
has no label yet.

Evaluated two ways on the issues maintainers already labeled; a suggestion is correct
when it is one of the issue's own area labels:
  leave-one-out  each labeled issue is treated as unlabeled (the backfill case)
  time split     labels from before --split only, tested on issues labeled after it
                 (the case of a newly filed issue); issues whose label had fewer than MIN_ITEMS
                 examples before the split are left out, since no method could suggest a label
                 it has not seen (area:webgpu and area:VTKHDF were new then)

Also counts, per top-level source directory, how many MRs changed it and how many of those
carry any area label, which shows the code areas no label covers.

Writes data/labels/area_eval.json, data/labels/AREA_LABELS.md, and
data/labels/area_suggestions.csv (one row per unlabeled issue, highest confidence first).

A merge request gets the same text votes, plus votes from the directories it changes (its own
labels left out), and its changed paths count toward naming a technology.

Usage:
  python triage/area_labels.py                  # evaluate and write suggestions
  python triage/area_labels.py --issue 19512    # suggest for one issue
  python triage/area_labels.py --mrs            # leave-one-out on labeled merge requests
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
COMMENT = re.compile(r"<!--.*?-->", re.S)
FIELD = re.compile(r"^[\s*\-]*\**\s*(language[^:\n]*|graphics backend[^:\n]*):\**\s*(.*)$", re.I | re.M)
FIELD_LABELS = {
    "language": [(r"\bpython\b", "lang:python"), (r"\bjava\b(?!script)", "lang:java"),
                 (r"javascript|webassembly|\bwasm\b|emscripten", "area:wasm")],
    "graphics backend": [(r"webgpu|\bdawn\b", "area:webgpu"), (r"\banari\b", "area:anari"),
                         (r"ospray|optix|ray.?trac", "area:ray-tracing")],
}
GATED = {
    "area:wasm": r"wasm|webassembly|emscripten|browser|javascript|\bjs\b|vtk\.?js",
    "area:webgpu": r"webgpu|\bdawn\b|wgpu",
    "area:anari": r"anari",
    "area:vr": r"openvr|openxr|\bvr\b|\bxr\b|zspace|headset|\bhmd\b|\bcave\b|virtual reality",
    "area:qt": r"\bqt\b|qvtk|\bqml\b|qwidget|qt5|qt6",
    "area:ray-tracing": r"ospray|optix|ray.?trac|path.?trac",
    "area:VTKHDF": r"hdf",
    "area:serialization": r"seriali|serdes|marshal",
    "area:text": r"font|freetype|\btext|label|glyph",
}
NOT_AN_AREA = {"Documentation/release"}
MIN_ITEMS = 8
K = 15
BINS = (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.0)
NO_FIT = "no label fits"


def area(labels):
    return {l for l in labels or [] if l.startswith("area:")}


def field_labels(description):
    """Labels named exactly by the template's Configuration lines."""
    out = set()
    for name, value in FIELD.findall(COMMENT.sub("", description or "")):
        key = "language" if name.lower().startswith("language") else "graphics backend"
        for pattern, label in FIELD_LABELS[key]:
            if re.search(pattern, value, re.I):
                out.add(label)
    return out


def load_items(mirror):
    issues, mrs, links = {}, {}, defaultdict(set)
    for f in glob.glob(f"{mirror}/issues/*.json"):
        i = json.load(open(f))["issue"]
        issues[i["iid"]] = {"title": i["title"], "state": i["state"], "created": i["created_at"][:10],
                            "url": i["web_url"], "areas": area(i.get("labels")),
                            "text": f"{i['title']}\n{COMMENT.sub('', i.get('description') or '')}",
                            "fields": field_labels(i.get("description"))}
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        m = json.load(open(f))["merge_request"]
        mrs[m["iid"]] = {"areas": area(m.get("labels")), "created": m["created_at"][:10], "title": m["title"],
                         "state": m["state"], "url": m["web_url"],
                         "text": f"{m['title']}\n{COMMENT.sub('', m.get('description') or '')}"}
        for n in ISSUE.findall(f"{m['title']}\n{m.get('description') or ''}"):
            links[int(n)].add(m["iid"])
    return issues, mrs, links


def top_dirs(paths):
    return {"/".join(Path(p).parts[:2]) for p in paths if len(Path(p).parts) > 1} - NOT_AN_AREA


def mr_dirs(commits_db):
    out = defaultdict(set)
    con = sqlite3.connect(commits_db)
    for mr, files in con.execute("SELECT mr, files FROM commits WHERE mr IS NOT NULL"):
        for path in json.loads(files or "[]"):
            out[mr] |= top_dirs([path])
    return out


def normalize(votes):
    total = sum(votes.values())
    return {k: v / total for k, v in votes.items()} if total else {}


class Suggester:
    """Votes from labeled issues and MRs created before `before` (all of them when None)."""

    def __init__(self, index, issues, mrs, links, dirs, labels, before=None):
        self.index, self.labels = index, labels
        self.issues, self.mrs, self.links, self.dirs = issues, mrs, links, dirs
        ok = (lambda d: d < before) if before else (lambda d: True)
        self.rowid = {r["ref"]: r["rowid"] for r in index.con.execute(
            "SELECT rowid, ref FROM docs WHERE kind IN ('issue', 'mr')")}
        pool = [(f"#{i}", v["areas"]) for i, v in issues.items() if v["areas"] & labels and ok(v["created"])] + \
               [(f"!{m}", v["areas"]) for m, v in mrs.items() if v["areas"] & labels and ok(v["created"])]
        pool = [(ref, a & labels) for ref, a in pool if ref in self.rowid]
        self.pool_refs = [ref for ref, _ in pool]
        self.pool_areas = [a for _, a in pool]
        self.pool_vecs = index.vectors[[self.rowid[ref] - 1 for ref in self.pool_refs]]
        self.mr_areas = {m: v["areas"] & labels for m, v in mrs.items() if ok(v["created"])}
        self.dir_votes = defaultdict(Counter)
        for m, a in self.mr_areas.items():
            for d in dirs.get(m, ()):
                for l in a:
                    self.dir_votes[d][l] += 1

    def vector(self, iid, text=None):
        ref = f"#{iid}"
        if ref in self.rowid:
            return self.index.vectors[self.rowid[ref] - 1]
        return self.index.embed([text], query=False)[0] if text else None

    def evidence(self, iid, text=None, fields=None, gate=True):
        ref = f"#{iid}"
        out = {}
        own = text if text is not None else self.issues.get(iid, {}).get("text", "")
        allowed = (lambda l: l not in GATED or re.search(GATED[l], own, re.I)) if gate else (lambda l: True)
        vec = self.vector(iid, text)
        if vec is not None:
            sims = self.pool_vecs @ vec
            votes = Counter()
            for j in np.argsort(-sims)[:K + 1]:
                if self.pool_refs[j] != ref:
                    for l in self.pool_areas[j]:
                        if allowed(l):
                            votes[l] += float(max(sims[j], 0)) ** 4
            out["text"] = normalize(votes)
        linked = self.links.get(iid, set())
        files = Counter()
        for m in linked:
            for d in self.dirs.get(m, ()):
                files.update(normalize({l: n for l, n in self.dir_votes.get(d, {}).items() if allowed(l)}))
        if files:
            out["files"] = normalize(files)
        mr_labels = Counter(l for m in linked for l in self.mr_areas.get(m, set()))
        if mr_labels:
            out["mr"] = normalize(mr_labels)
        fields = self.issues.get(iid, {}).get("fields", set()) if fields is None else fields
        if {l for l in fields if l.startswith("area:")}:
            out["field"] = {l: 1.0 for l in fields if l.startswith("area:")}
        return out

    def mr_evidence(self, iid, gate=True, changed=None):
        """Votes for a merge request: similar labeled items other than itself, and its changed directories
        (from its commits on master, or `changed` for one that was not merged)."""
        ref, mine = f"!{iid}", self.mr_areas.get(iid, set())
        changed = self.dirs.get(iid, set()) if changed is None else changed
        own = f"{self.mrs.get(iid, {}).get('text', '')}\n{' '.join(sorted(changed))}"
        allowed = (lambda l: l not in GATED or re.search(GATED[l], own, re.I)) if gate else (lambda l: True)
        out = {}
        vec = self.vector_ref(ref)
        if vec is not None:
            sims = self.pool_vecs @ vec
            votes = Counter()
            for j in np.argsort(-sims)[:K + 1]:
                if self.pool_refs[j] != ref:
                    for l in self.pool_areas[j]:
                        if allowed(l):
                            votes[l] += float(max(sims[j], 0)) ** 4
            out["text"] = normalize(votes)
        files = Counter()
        for d in changed:
            counts = {l: n - (l in mine) for l, n in self.dir_votes.get(d, {}).items()}
            files.update(normalize({l: n for l, n in counts.items() if n > 0 and allowed(l)}))
        if files:
            out["files"] = normalize(files)
        return out

    def vector_ref(self, ref):
        return self.index.vectors[self.rowid[ref] - 1] if ref in self.rowid else None

    @staticmethod
    def combine(ev, use=("text", "files", "mr")):
        if "field" in ev and "field" in use:
            ranked = sorted(ev["field"].items())
            return ranked[0][0], 1.0, ranked
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


def cutoff_for(bins, target):
    """The lowest confidence whose suggestions at or above it reach the target precision."""
    ok = [b["confidence_at_least"] for b in bins if b["precision"] is not None and b["precision"] >= target]
    return min(ok) if ok else 1.0


def evaluate(s, issues, labeled, labels, gate=True):
    variants = {"text": ("text",), "files": ("files",), "mr": ("mr",), "combined": ("text", "files", "mr", "field")}
    scored = {name: [] for name in variants}
    per_label = defaultdict(lambda: {"true": 0, "suggested": 0, "correct": 0})
    for i in labeled:
        truth = issues[i]["areas"] & labels
        ev = s.evidence(i, gate=gate)
        for name, use in variants.items():
            top, conf, _ = s.combine(ev, use)
            if top:
                scored[name].append((conf, top in truth))
        top, _, _ = s.combine(ev, variants["combined"])
        for l in truth:
            per_label[l]["true"] += 1
        if top:
            per_label[top]["suggested"] += 1
            per_label[top]["correct"] += top in truth
    return scored, per_label


def setup(mirror):
    index = Index(str(ROOT / "data/index"))
    issues, mrs, links = load_items(mirror)
    counts = Counter(l for v in issues.values() for l in v["areas"]) + \
        Counter(l for v in mrs.values() for l in v["areas"])
    labels = {l for l, n in counts.items() if n >= MIN_ITEMS}
    return index, issues, mrs, links, mr_dirs(ROOT / "data/index/commits.sqlite"), labels


def evaluate_mrs(args):
    index, issues, mrs, links, dirs, labels = setup(args.mirror)
    s = Suggester(index, issues, mrs, links, dirs, labels)
    labeled = [m for m, v in mrs.items() if v["areas"] & labels]
    results = {name: [] for name in ("text", "files", "combined")}
    for m in labeled:
        truth = mrs[m]["areas"] & labels
        ev = s.mr_evidence(m)
        for name, use in (("text", ("text",)), ("files", ("files",)), ("combined", ("text", "files"))):
            top, conf, _ = Suggester.combine(ev, use)
            if top:
                results[name].append((conf, top in truth))
    majority = Counter(l for m in labeled for l in mrs[m]["areas"] & labels).most_common(1)[0]
    print(f"{len(labeled)} labeled MRs; always suggesting {majority[0]} is right for "
          f"{sum(majority[0] in mrs[m]['areas'] for m in labeled) / len(labeled):.0%}")
    for name, r in results.items():
        print(f"  {name}: {len(r)} MRs with evidence, top suggestion right {sum(ok for _, ok in r) / len(r):.0%}")
    for b in precision_table(results["combined"]):
        print(f"  confidence >= {b['confidence_at_least']}: {b['precision']} of {b['issues']}")


def one_issue(args):
    index, issues, mrs, links, dirs, labels = setup(args.mirror)
    s = Suggester(index, issues, mrs, links, dirs, labels)
    record = json.load(open(f"{args.mirror}/issues/{args.issue}.json"))["issue"]
    text = f"Issue #{record['iid']}: {record['title']}\n\n{record.get('description') or ''}"
    fields = field_labels(record.get("description"))
    top, conf, ranked = s.combine(s.evidence(args.issue, text, fields), ("text", "files", "mr", "field"))
    report = json.loads((Path(args.out) / "area_eval.json").read_text())
    cut = report["cutoff"]
    print(f"#{args.issue} {record['title']}\n  current labels: {', '.join(record.get('labels') or []) or 'none'}")
    print(f"  suggested: {top if conf >= cut else NO_FIT} (confidence {conf:.2f}, cutoff {cut})")
    print("  ranked: " + ", ".join(f"{l} {v / sum(x for _, x in ranked):.2f}" for l, v in ranked[:4]))
    lang = sorted(l for l in fields if l.startswith("lang:"))
    if lang:
        print(f"  from the template: {', '.join(lang)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default=str(ROOT / "data/vtk-history"))
    p.add_argument("--out", default=str(ROOT / "data/labels"))
    p.add_argument("--target", type=float, default=0.9, help="precision the cutoff must reach")
    p.add_argument("--split", default="2024-01-01", help="date for the time-split evaluation")
    p.add_argument("--issue", type=int, help="suggest labels for this issue and stop")
    p.add_argument("--mrs", action="store_true", help="evaluate suggestions on labeled merge requests and stop")
    args = p.parse_args()
    if args.issue:
        return one_issue(args)
    if args.mrs:
        return evaluate_mrs(args)

    index, issues, mrs, links, dirs, labels = setup(args.mirror)
    s = Suggester(index, issues, mrs, links, dirs, labels)
    labeled = [i for i, v in issues.items() if v["areas"] & labels]
    majority = Counter(l for i in labeled for l in issues[i]["areas"] & labels).most_common(1)[0][0]
    scored, per_label = evaluate(s, issues, labeled, labels)
    bins = precision_table(scored["combined"])
    early = Suggester(index, issues, mrs, links, dirs, labels, before=args.split)
    known = Counter(l for a in early.pool_areas for l in a)
    after_split = [i for i in labeled if issues[i]["created"] >= args.split]
    later = [i for i in after_split if all(known[l] >= MIN_ITEMS for l in issues[i]["areas"] & labels)]
    split_scored, _ = evaluate(early, issues, later, labels)
    split_bins = precision_table(split_scored["combined"])
    ungated = {"backfill": precision_table(evaluate(s, issues, labeled, labels, gate=False)[0]["combined"]),
               "new": precision_table(evaluate(early, issues, later, labels, gate=False)[0]["combined"])}
    cut = max(cutoff_for(bins, args.target), cutoff_for(split_bins, args.target))
    split_above = [ok for conf, ok in split_scored["combined"] if conf >= cut]

    report = {
        "labeled_issues": len(labeled), "labels": sorted(labels), "majority_label": majority,
        "majority_precision": round(sum(majority in issues[i]["areas"] for i in labeled) / len(labeled), 3),
        "target": args.target, "cutoff": cut,
        "variants": {name: {"issues_with_evidence": len(r),
                            "precision": round(sum(ok for _, ok in r) / len(r), 3) if r else None}
                     for name, r in scored.items()},
        "by_confidence": bins,
        "time_split": {"split": args.split, "issues": len(later), "left_out": len(after_split) - len(later),
                       "new_labels": sorted(l for l in labels if known[l] < MIN_ITEMS), "by_confidence": split_bins,
                       "at_cutoff": {"issues": len(split_above),
                                     "precision": round(sum(split_above) / len(split_above), 3) if split_above else None}},
        "by_label": {l: dict(v, precision=round(v["correct"] / v["suggested"], 3) if v["suggested"] else None,
                             recall=round(v["correct"] / v["true"], 3) if v["true"] else None)
                     for l, v in sorted(per_label.items(), key=lambda x: -x[1]["true"])},
        "without_gate": ungated,
        "issues_with_template_fields": sum(bool(v["fields"]) for v in issues.values()),
    }

    def expected(conf):
        return next(b["precision"] for b in bins if conf >= b["confidence_at_least"])

    rows = []
    for i, v in issues.items():
        if v["areas"]:
            continue
        ev = s.evidence(i)
        top, conf, ranked = s.combine(ev, ("text", "files", "mr", "field"))
        if not top:
            continue
        fits = conf >= cut
        rows.append({"issue": i, "state": v["state"], "created": v["created"],
                     "suggested": top if fits else NO_FIT, "best_guess": top, "confidence": round(conf, 2),
                     "expected_precision": expected(conf),
                     "runner_up": ranked[1][0] if len(ranked) > 1 else "",
                     "lang_from_template": " ".join(sorted(l for l in v["fields"] if l.startswith("lang:"))),
                     "evidence": "+".join(k for k in ("field", "text", "files", "mr") if top in ev.get(k, {})),
                     "linked_mrs": " ".join(f"!{m}" for m in sorted(links.get(i, ()))),
                     "title": v["title"], "url": v["url"]})
    rows.sort(key=lambda r: (-r["confidence"], r["state"] != "opened", r["issue"]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "area_suggestions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    tops, tops_labeled = Counter(), Counter()
    for m, ds in dirs.items():
        for t in {d.split("/")[0] for d in ds}:
            tops[t] += 1
            tops_labeled[t] += bool(mrs.get(m, {}).get("areas"))
    report["directories"] = {t: {"mrs": n, "with_area_label": tops_labeled[t]} for t, n in tops.most_common(15)}
    fit = [r for r in rows if r["suggested"] != NO_FIT]
    report["suggestions"] = {"unlabeled": len(rows), "suggested": len(fit), "no_fit": len(rows) - len(fit),
                             "open_suggested": sum(r["state"] == "opened" for r in fit),
                             "open_no_fit": sum(r["state"] == "opened" and r["suggested"] == NO_FIT for r in rows)}
    now = Counter(l for v in issues.values() for l in v["areas"])
    added = Counter(r["suggested"] for r in fit)
    is_open = {i for i, v in issues.items() if v["state"] == "opened"}
    report["backfill"] = {
        "issues": len(issues), "open": len(is_open),
        "labeled_now": sum(bool(v["areas"]) for v in issues.values()),
        "open_labeled_now": sum(bool(issues[i]["areas"]) for i in is_open),
        "added": len(fit), "open_added": sum(r["issue"] in is_open for r in fit),
        "expected_wrong": round(sum(1 - r["expected_precision"] for r in fit)),
        "by_label": [{"label": l, "now": now[l], "added": added[l], "after": now[l] + added[l]}
                     for l in sorted(set(now) | set(added), key=lambda l: -(now[l] + added[l]))],
    }
    json.dump(report, open(out / "area_eval.json", "w"), indent=1)

    pct = lambda x: f"{x:.0%}" if x is not None else ""
    lines = ["# Area label suggestions: evaluation", "",
             f"Tested on {len(labeled)} issues that already carry one of {len(labels)} area labels "
             f"(labels used on at least {MIN_ITEMS} issues or MRs). A suggestion is correct when it is one of the "
             f"issue's own area labels. Always suggesting {majority} is correct for "
             f"{report['majority_precision']:.0%}.", "",
             "## Leave-one-out (backfill)", "",
             "| Evidence | Issues with this evidence | Top suggestion correct |", "| --- | --- | --- |"]
    for name, v in report["variants"].items():
        lines.append(f"| {name} | {v['issues_with_evidence']} | {pct(v['precision'])} |")
    lines += ["", "| Confidence at least | Issues | Top suggestion correct |", "| --- | --- | --- |"]
    lines += [f"| {b['confidence_at_least']:.1f} | {b['issues']} | {pct(b['precision'])} |" for b in bins]
    lines += ["", f"Cutoff: confidence {cut}, the lowest level whose suggestions were right at least "
                  f"{args.target:.0%} of the time here and in the time split below. Below it the issue is marked "
                  f"\"{NO_FIT}\".", "",
              f"## Time split (new issues)", "",
              f"Labels from before {args.split} only, tested on the {len(later)} labeled issues created after it "
              f"whose labels already had {MIN_ITEMS} examples; {len(after_split) - len(later)} issues labeled "
              f"{', '.join(report['time_split']['new_labels'])} are left out.", "",
              "| Confidence at least | Issues | Top suggestion correct |", "| --- | --- | --- |"]
    lines += [f"| {b['confidence_at_least']:.1f} | {b['issues']} | {pct(b['precision'])} |" for b in split_bins]
    lines += ["", f"At the cutoff: {report['time_split']['at_cutoff']['issues']} issues, "
                  f"{pct(report['time_split']['at_cutoff']['precision'])} correct.", "",
              "## By label (leave-one-out, no cutoff)", "",
              "| Label | Labeled issues | Suggested | Precision | Recall |", "| --- | --- | --- | --- | --- |"]
    for l, v in report["by_label"].items():
        lines.append(f"| {l} | {v['true']} | {v['suggested']} | {pct(v['precision'])} | {pct(v['recall'])} |")
    lines += ["", "## Code areas without a label", "",
              "Merge requests that changed each top-level directory, and the share carrying any area label.", "",
              "| Directory | MRs | With an area label |", "| --- | --- | --- |"]
    lines += [f"| {t} | {n} | {tops_labeled[t] / n:.0%} |" for t, n in tops.most_common(15)]
    sg = report["suggestions"]
    lines += ["", "## Suggestions", "",
              f"{sg['unlabeled']} unlabeled issues: {sg['suggested']} get a suggested label ({sg['open_suggested']} "
              f"open) and {sg['no_fit']} are marked \"{NO_FIT}\" ({sg['open_no_fit']} open). "
              f"{report['issues_with_template_fields']} issues have template Configuration lines that name a "
              "language or graphics backend. Written to area_suggestions.csv.", ""]
    (out / "AREA_LABELS.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
