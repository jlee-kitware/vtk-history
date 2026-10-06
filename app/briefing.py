"""What VTK's history says about a merge request, gathered in one place.

Sections, each with how well it held up when measured on past merge requests (eval/):
  reviewers    who reviewed and wrote these files recently (people/expertise.py)
  related      earlier issues, merge requests, and forum threads matching the title and description
  conventions  rules reviewers applied before on these files, with their follow-through estimate
  deprecated   deprecated or removed APIs used in the added lines
  file history recent commits on the most-changed files
"""

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
sys.path.insert(0, str(ROOT / "people"))
import static_checks  # noqa: E402
from expertise import reason  # noqa: E402
from review import hunks  # noqa: E402

ISSUE = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?#|gitlab\.kitware\.com/vtk/vtk/-?/?issues/)(\d{2,6})\b")
MR = re.compile(r"(?:(?<![\w/&])(?:vtk/vtk)?!|gitlab\.kitware\.com/vtk/vtk/-?/?merge_requests/)(\d{2,6})\b")
URL = re.compile(r"https?://\S+")

MEASURED = {
    "reviewers": "On past MRs, an actual reviewer was in this top 3 for 76% of 1,656 MRs (67% for the three most active reviewers).",
    "related": "On 300 past MRs that link an issue, this search found it in the top 5 for 84% (73% from the title "
               "alone) among about 3,700 issues; for a linked earlier MR, 51% among about 9,900.",
    "conventions": "Reference: what reviewers asked for on these files before. Which one a reviewer raises next "
                   "could not be predicted from history (at most 20% in the top 10), so read these as a checklist.",
    "deprecated": "Checked against VTK's deprecation records, confirmed in the headers at this revision.",
    "files": "Recent commits on the files this MR changes most.",
}


class Briefing:
    def __init__(self, reviews, expertise, index):
        self.reviews, self.expertise, self.index = reviews, expertise, index
        self._rules = None
        self._deprecated = None

    def rules(self):
        """(rule by id, rule ids applied per file path with comment dates)"""
        if self._rules is None:
            rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
            conf = json.loads((ROOT / "data/rules_confidence.json").read_text())["rules"]
            sys.path.insert(0, str(ROOT / "app"))
            from data import rule_key
            by_id, owner = {}, {}
            for i, r in enumerate(rules, 1):
                rid = r.get("id") or f"R{i:03d}"
                c = conf.get(rule_key(r), {})
                by_id[rid] = {"id": rid, "rule": r["rule"], "level": c.get("level", "medium"),
                              "estimate": (c.get("adjusted") or {}).get("adjusted"),
                              "automated": c.get("automated", False)}
                for m in r["members"]:
                    owner[m] = rid
            per_path = defaultdict(list)
            with open(ROOT / "data/review_examples.jsonl") as f:
                for line in f:
                    e = json.loads(line)
                    rid = owner.get(e["discussion_id"])
                    path = (e.get("code") or {}).get("path")
                    if rid and path:
                        per_path[path].append((rid, e["thread"][0]["created_at"][:10], e["mr"]["iid"]))
            self._rules = (by_id, per_path)
        return self._rules

    def deprecated(self):
        if self._deprecated is None:
            self._deprecated = {}
            for line in open(ROOT / "data/deprecations/index.jsonl"):
                rec = json.loads(line)
                self._deprecated.setdefault(rec["symbol"], []).append(rec)
        return self._deprecated

    def build(self, record, rev, files):
        mr = record["merge_request"]
        author = mr["author"]["username"]
        is_open = mr["state"] == "opened"
        opened = mr["created_at"][:10]
        at = datetime.now().isoformat()[:19] if is_open else mr["created_at"][:19]
        until = None if is_open else opened
        paths = [f["path"] for f in files]
        desc = mr.get("description") or ""
        linked = {f"#{n}" for n in ISSUE.findall(desc)} | {f"!{n}" for n in MR.findall(desc)}
        query = f"{mr['title']}\n{' '.join(MR.sub(' ', ISSUE.sub(' ', URL.sub(' ', desc))).split())[:1500]}"
        return {
            "reviewers": self.reviewer_section(record, paths, at, author),
            "related": self.related_section(query, until, f"!{mr['iid']}", linked),
            "conventions": self.convention_section(paths, opened if not is_open else "9999"),
            "deprecated": self.deprecated_section(rev, until),
            "files": self.file_section(files, rev),
            "measured": MEASURED,
        }

    def reviewer_section(self, record, paths, at, author):
        actual = {n["author"]["username"] for d in record.get("discussions") or [] for n in d["notes"]}
        picks = self.expertise.suggest(paths, at, exclude={author}, top=5)
        return [{"user": s["user"], "reason": reason(s), "reviewed": s["user"] in actual} for s in picks]

    def related_section(self, query, until, self_ref, linked):
        out = []
        for kind, label, k in (("issue", "Issue", 5), ("mr", "Merge request", 5), ("post", "Forum", 3)):
            seen = set()
            for h in self.index.search(query, k=k * 3, kind=kind, **({"until": until} if until else {})):
                ref = h["ref"]
                if ref == self_ref or ref in seen:
                    continue
                seen.add(ref)
                out.append({"key": f"{kind}{ref}", "kind": label, "ref": ref, "title": h.get("title") or "",
                            "date": h["date"], "url": h.get("url") or "", "linked": ref in linked,
                            "topic": h.get("topic") or ""})
                if len(seen) >= k:
                    break
        return out

    def convention_section(self, paths, before):
        by_id, per_path = self.rules()
        hits, where = Counter(), defaultdict(set)
        dirs = {str(Path(p).parent) for p in paths}
        for path, items in per_path.items():
            same_file = path in paths
            if not same_file and str(Path(path).parent) not in dirs:
                continue
            for rid, date, iid in items:
                if date < before:
                    hits[rid] += 3 if same_file else 1
                    where[rid].add(f"!{iid}")
        out = []
        for rid, _ in hits.most_common(8):
            r = by_id[rid]
            est = f"authors follow it about {r['estimate']:.0%} of the time" if r["estimate"] else ""
            out.append({"key": rid, "id": rid, "rule": r["rule"], "level": r["level"],
                        "detail": f"raised in {len(where[rid])} earlier MR{'s' if len(where[rid]) != 1 else ''} on "
                                  f"these files or directories" + (f"; {est}" if est else "")
                                  + ("; a tool enforces it" if r["automated"] else "")})
        return out

    def deprecated_section(self, rev, until):
        repo = self.reviews.repo
        todo = list(hunks(repo, rev["base"], rev["head"]))
        found = []
        for path, number, text in static_checks.added_lines(todo):
            if static_checks.SOURCE.search(path):
                found += static_checks.deprecated_uses(path, number, text, self.deprecated(), until, repo, rev["head"])
        seen, out = set(), []
        for f in found:
            if f["fact"] not in seen:
                seen.add(f["fact"])
                out.append({"key": f"{f['path']}:{f['line']}", "where": f"{f['path'].split('/')[-1]}:{f['line']}",
                            "fact": f["fact"]})
        return out[:10]

    def file_section(self, files, rev):
        top = sorted(files, key=lambda f: -(f.get("added", 0) + f.get("removed", 0)))[:4]
        out = []
        for f in top:
            r = subprocess.run(["git", "-C", self.reviews.repo, "log", "-n", "3", "--format=%h|%ad|%an|%s",
                                "--date=short", rev["base"], "--", f["path"]], capture_output=True, text=True)
            commits = [dict(zip(("sha", "date", "who", "subject"), line.split("|", 3)))
                       for line in r.stdout.splitlines() if line.count("|") >= 3]
            out.append({"key": f["path"], "path": f["path"], "commits": commits})
        return out
