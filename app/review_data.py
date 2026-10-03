"""Merge requests, their diffs, reviewer and agent comments, and ratings for the Review view.

A revision is a (base, head) commit pair. The revisions offered for an MR are the ones
reviewers left line comments on (recorded in each comment's position), plus the final
revision. Reviewer comments are shown on the revision they were written against.

Ratings of agent comments go to ratings/ratings.jsonl, one line per rating, tracked in git.
The latest rating of a comment by a given person is the one that counts.
"""

import getpass
import glob
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
RATINGS = ROOT / "ratings" / "ratings.jsonl"
VERDICTS = ("valid", "wrong", "unsure")
SKIP_PATH = re.compile(r"^ThirdParty/|/Testing/Data/|/Baseline/|\.(png|jpg|sha512|md5|vtk|vtp|vtu|vti)$")


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else ""


def comment_key(iid, head, c):
    raw = f"{iid}|{head}|{c['path']}|{c['line']}|{c['comment']}"
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


class Reviews:
    def __init__(self, repo="/home/jlee/gitsync/vtk", mirror=ROOT / "data/vtk-history"):
        self.repo, self.mirror = repo, Path(mirror)

    def mr(self, iid):
        path = self.mirror / "merge_requests" / f"{iid}.json"
        return json.loads(path.read_text()) if path.exists() else None

    def ensure(self, *shas):
        missing = [s for s in shas if s and not git(self.repo, "cat-file", "-t", s).strip()]
        if missing:
            subprocess.run(["git", "-C", self.repo, "fetch", "-q", "upstream", *missing], capture_output=True)
        return all(git(self.repo, "cat-file", "-t", s).strip() for s in shas if s)

    def revisions(self, record):
        mr = record["merge_request"]
        seen = {}
        for d in record.get("discussions") or []:
            for n in d.get("notes", []):
                pos = n.get("position") or {}
                if n.get("type") == "DiffNote" and pos.get("base_sha") and pos.get("head_sha"):
                    key = (pos["base_sha"], pos["head_sha"])
                    first = seen.setdefault(key, {"base": key[0], "head": key[1], "date": n["created_at"][:10], "count": 0})
                    first["count"] += 1
                    first["date"] = min(first["date"], n["created_at"][:10])
        revs = sorted(seen.values(), key=lambda r: r["date"])
        for r in revs:
            r["label"] = f"Reviewed {r['date']}: {r['head'][:8]} ({r['count']} reviewer comments)"
        head = mr.get("sha")
        if head and head not in {r["head"] for r in revs}:
            target = f"{mr['merge_commit_sha']}^1" if mr.get("merge_commit_sha") else "upstream/master"
            self.ensure(head)
            base = git(self.repo, "merge-base", target, head).strip()
            if base:
                revs.append({"base": base, "head": head, "date": (mr.get("merged_at") or mr["updated_at"])[:10],
                             "count": 0, "label": f"Final revision: {head[:8]}"})
        return revs

    def diff(self, base, head):
        """Files changed between base and head, each a list of display rows."""
        if not self.ensure(base, head):
            return None
        files, cur, old_no, new_no = [], None, 0, 0
        for line in git(self.repo, "diff", "-U3", "--no-color", base, head).splitlines():
            if line.startswith("diff --git"):
                cur = None
            elif line.startswith("+++ "):
                path = line[6:] if line.startswith("+++ b/") else None
                if path and not SKIP_PATH.search(path):
                    cur = {"path": path, "rows": [], "added": 0, "removed": 0}
                    files.append(cur)
            elif cur is None or line.startswith(("--- ", "index ", "new file", "deleted file", "similarity", "rename")):
                continue
            elif line.startswith("@@"):
                m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)", line)
                old_no, new_no = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
                cur["rows"].append({"kind": "hunk", "old": "", "new": "", "text": line})
            elif line.startswith("+"):
                cur["rows"].append({"kind": "add", "old": "", "new": new_no, "text": line[1:]})
                cur["added"] += 1
                new_no += 1
            elif line.startswith("-"):
                cur["rows"].append({"kind": "del", "old": old_no, "new": "", "text": line[1:]})
                cur["removed"] += 1
                old_no += 1
            elif line.startswith(" "):
                cur["rows"].append({"kind": "ctx", "old": old_no, "new": new_no, "text": line[1:]})
                old_no += 1
                new_no += 1
        return files

    def reviewer_comments(self, record, head):
        out = []
        for d in record.get("discussions") or []:
            notes = d.get("notes", [])
            pos = (notes[0].get("position") or {}) if notes else {}
            if not notes or notes[0].get("type") != "DiffNote" or pos.get("head_sha") != head:
                continue
            out.append({"path": pos.get("new_path") or pos.get("old_path"), "line": pos.get("new_line"),
                        "old_line": pos.get("old_line"), "author": notes[0]["author"]["username"],
                        "date": notes[0]["created_at"][:10], "body": notes[0]["body"],
                        "replies": [{"author": n["author"]["username"], "body": n["body"]} for n in notes[1:]
                                    if not n.get("system")]})
        return out

    @property
    def benchmark_heads(self):
        if not hasattr(self, "_bench"):
            path = ROOT / "data/benchmark/benchmark.jsonl"
            self._bench = {json.loads(l)["mr"]["iid"]: json.loads(l)["head_sha"] for l in open(path)} if path.exists() else {}
        return self._bench

    def saved_runs(self, iid, head):
        """Agent reviews of this MR revision: benchmark runs and reviews started from the app."""
        runs = []
        if self.benchmark_heads.get(iid) == head:
            for f in sorted(glob.glob(str(ROOT / f"data/benchmark/runs*/*/{iid}.json"))):
                run = Path(f).parent
                runs.append((f"benchmark {run.parent.name}/{run.name}", f))
        for f in sorted(glob.glob(str(ROOT / f"data/reviews/{iid}-{head[:12]}-*.json"))):
            runs.append((f"app {Path(f).stem.split('-', 2)[2]}", f))
        out = []
        for label, f in runs:
            record = json.loads(Path(f).read_text())
            out.append({"label": label, "file": f, "model": record.get("model") or label.split("/")[-1],
                        "predictions": record["predictions"], "trace": record.get("trace") or [],
                        "findings": record.get("findings") or [],
                        "tool_findings": record.get("tool_findings") or []})
        return out

    def reviewed_mrs(self):
        """MRs reviewed by the tool agent, unrated first, with the number of its comments you have not rated.
        Older per-hunk benchmark runs stay viewable from the MR but are left out of the queue."""
        rated = {(r["mr"], r["head"], r["path"], r["line"], r["comment"]) for r in self.ratings().values()}
        comments, titles = {}, {}
        for f in glob.glob(str(ROOT / "data/benchmark/runs*/*-tool/*.json")) + glob.glob(str(ROOT / "data/reviews/*.json")):
            if f.endswith("report.json"):
                continue
            record = json.loads(Path(f).read_text())
            mr = record["mr"]
            iid = mr["iid"] if isinstance(mr, dict) else mr
            head = record.get("head") or self.benchmark_heads.get(iid)
            titles[iid] = mr["title"] if isinstance(mr, dict) else titles.get(iid, "")
            for p in record["predictions"]:
                comments.setdefault(iid, set()).add((iid, head, p["path"], p["line"], p["comment"]))
        rows = []
        for iid, cs in comments.items():
            if not titles.get(iid) and (rec := self.mr(iid)):
                titles[iid] = rec["merge_request"]["title"]
            left = len(cs - rated)
            rows.append({"title": f"!{iid} {titles.get(iid, '')[:60]} ({left} to rate)", "value": iid, "left": left})
        return sorted(rows, key=lambda r: (r["left"] == 0, -r["value"]))

    def run_agent(self, iid, base, head, title, until, model):
        """Review one revision with the tool reviewer and save the result beside earlier ones."""
        from tool_review import ToolReviewer
        reviewer = ToolReviewer(self.repo, model)
        predictions, hunks, drafted = reviewer.review(base, head, title, until, exclude_ref=f"!{iid}")
        from judge_comments import vet
        predictions, held_back = vet(title, head, predictions)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M")
        record = {"mr": iid, "base": base, "head": head, "model": model, "until": until, "hunks": hunks,
                  "drafted": drafted, "predictions": predictions, "held_back": held_back, "trace": reviewer.trace,
                  "findings": reviewer.findings, "tool_findings": getattr(reviewer, "tool_findings", []),
                  "at": stamp}
        out = ROOT / "data/reviews" / f"{iid}-{head[:12]}-{model.replace(':', '_')}-{stamp}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=1, ensure_ascii=False))
        return str(out)

    def rate(self, iid, head, comment, verdict, note, source, who=None):
        entry = {"key": comment_key(iid, head, comment), "mr": iid, "head": head, "path": comment["path"],
                 "line": comment["line"], "comment": comment["comment"], "severity": comment.get("severity"),
                 "source": source, "verdict": verdict, "note": note.strip(), "by": who or getpass.getuser(),
                 "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
        RATINGS.parent.mkdir(exist_ok=True)
        with open(RATINGS, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def ratings(self, who=None):
        """Latest verdict per comment by this person."""
        who = who or getpass.getuser()
        latest = {}
        if RATINGS.exists():
            for line in open(RATINGS):
                r = json.loads(line)
                if r["by"] == who:
                    latest[r["key"]] = r
        return latest

    def summary(self, who=None):
        counts = {v: 0 for v in VERDICTS}
        for r in self.ratings(who).values():
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        decided = counts["valid"] + counts["wrong"]
        share = f", {100 * counts['valid'] / decided:.0f}% valid" if decided else ""
        return f"{sum(counts.values())} rated: {counts['valid']} valid, {counts['wrong']} wrong, {counts['unsure']} unsure{share}"
