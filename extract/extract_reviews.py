#!/usr/bin/env python3
"""Turn mirrored merge request discussions into review examples.

Each output line is one review thread:

  kind       "line" (attached to code, with the code recovered from git),
             "legacy" (old line comment whose position GitLab no longer has),
             "general" (review discussion on the MR as a whole), or
             "approval" (a short standalone approval such as "+2" or "LGTM")
  mr         iid, title, url, state, merged_at, author, target_branch
  thread     the human comments in order (author, created_at, body)
  reviewer   author of the first comment
  resolved   GitLab's resolved flag, when the thread was resolvable
  code       for "line": path, line, side, the diff hunk the reviewer saw,
             and surrounding source at that revision
  acted_on   for "line": true if the author changed lines within 3 of the commented
             line between the revision the reviewer saw and the MR's final revision.
             A heuristic: a reply made elsewhere in the code reads as false.

Revisions missing from the local clone (force-pushed MR revisions) are fetched from
the upstream remote by hash, in batches.

Usage:
  python extract/extract_reviews.py --mirror data/vtk-history --repo /home/jlee/gitsync/vtk
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

BOTS = {"kwrobot", "buildbot", "vtk-ci", "ghost", "gitlab-bot"}
ROBOT_LINE = re.compile(r"^\s*(Do|Fast-forward|Backport|Topic-rename|Cc|Acked-by|Tested-by|Reviewed-by|Rejected-by|Bypass-token)\s*:", re.I)
MENTIONS_ONLY = re.compile(r"^(\s*@[\w.\-]+[,:]?)+\s*$")
APPROVAL = re.compile(r"^\s*(\+[12]\b|lgtm\b|looks good|thanks?\b|thank you|:\+1:|👍)", re.I)
CONTEXT_BEFORE, CONTEXT_AFTER, ACTED_WINDOW = 12, 6, 3
FETCH_BATCH = 200


class Repo:
    def __init__(self, path, remote):
        self.path, self.remote = str(path), remote
        self._present = {}

    def run(self, *args, check=False):
        r = subprocess.run(["git", "-C", self.path, *args], capture_output=True, text=True, errors="replace")
        if check and r.returncode:
            raise RuntimeError(r.stderr.strip())
        return r

    def check_present(self, shas):
        todo = [s for s in shas if s not in self._present]
        if not todo:
            return
        r = subprocess.run(["git", "-C", self.path, "cat-file", "--batch-check"],
                           input="".join(f"{s}^{{commit}}\n" for s in todo),
                           capture_output=True, text=True)
        for sha, line in zip(todo, r.stdout.splitlines()):
            self._present[sha] = not line.endswith("missing")

    def ensure(self, shas):
        shas = sorted(set(s for s in shas if s))
        self.check_present(shas)
        missing = [s for s in shas if not self._present[s]]
        if missing:
            print(f"Fetching {len(missing)} revisions missing from the local clone", file=sys.stderr)
        for i in range(0, len(missing), FETCH_BATCH):
            batch = missing[i:i + FETCH_BATCH]
            if self.run("fetch", "-q", self.remote, *batch).returncode:
                for s in batch:
                    self.run("fetch", "-q", self.remote, s)
            for s in batch:
                self._present.pop(s, None)
            self.check_present(batch)
        still = [s for s in missing if not self._present[s]]
        if still:
            print(f"{len(still)} revisions could not be fetched", file=sys.stderr)

    def present(self, sha):
        return bool(sha) and self._present.get(sha, False)

    def file_lines(self, sha, path):
        r = self.run("show", f"{sha}:{path}")
        return r.stdout.splitlines() if r.returncode == 0 else None

    def diff(self, a, b, path, context=3):
        r = self.run("diff", f"-U{context}", a, b, "--", path)
        return r.stdout if r.returncode == 0 else None


HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def hunks(diff_text):
    out, cur = [], None
    for line in (diff_text or "").splitlines():
        m = HUNK.match(line)
        if m:
            cur = {"old_start": int(m[1]), "old_len": int(m[2] or 1),
                   "new_start": int(m[3]), "new_len": int(m[4] or 1), "lines": [line]}
            out.append(cur)
        elif cur is not None:
            cur["lines"].append(line)
    return out


def overlaps(start, length, lo, hi):
    end = start + max(length, 1) - 1
    return start <= hi and end >= lo


def human_notes(discussion):
    notes = []
    for n in discussion["notes"]:
        if n.get("system") or n["author"]["username"] in BOTS:
            continue
        body = "\n".join(l for l in n["body"].splitlines() if not ROBOT_LINE.match(l)).strip()
        if body and not MENTIONS_ONLY.match(body):
            notes.append({"author": n["author"]["username"], "created_at": n["created_at"], "body": body})
    return notes


def resolved(discussion):
    flags = [n.get("resolved") for n in discussion["notes"] if n.get("resolvable")]
    return all(flags) if flags else None


def mr_summary(mr):
    return {k: mr.get(k) for k in ("iid", "title", "web_url", "state", "merged_at", "target_branch", "sha", "labels")} | {
        "author": (mr.get("author") or {}).get("username")}


def line_code(repo, pos, final_sha):
    base, head = pos.get("base_sha"), pos.get("head_sha")
    new_path, old_path = pos.get("new_path"), pos.get("old_path")
    if pos.get("new_line"):
        side, line, path, sha = "new", pos["new_line"], new_path, head
    elif pos.get("old_line"):
        side, line, path, sha = "old", pos["old_line"], old_path, base
    else:
        return None, None
    if not (repo.present(base) and repo.present(head)):
        return {"path": path, "line": line, "side": side, "unavailable": True}, None

    source = repo.file_lines(sha, path) or []
    lo = max(1, line - CONTEXT_BEFORE)
    hi = min(len(source), line + CONTEXT_AFTER)
    context = [f"{i:6d}{'>' if i == line else ' '} {source[i - 1]}" for i in range(lo, hi + 1)]

    hunk = None
    for h in hunks(repo.diff(base, head, new_path if side == "new" else old_path)):
        start, length = (h["new_start"], h["new_len"]) if side == "new" else (h["old_start"], h["old_len"])
        if overlaps(start, length, line, line):
            hunk = "\n".join(h["lines"])
            break

    code = {"path": path, "line": line, "side": side, "base_sha": base, "head_sha": head,
            "hunk": hunk, "context": "\n".join(context)}

    acted = None
    if side == "new" and repo.present(final_sha):
        if final_sha == head:
            acted = False
        else:
            later = hunks(repo.diff(head, final_sha, new_path, context=0))
            if later is not None:
                acted = any(overlaps(h["old_start"], h["old_len"], line - ACTED_WINDOW, line + ACTED_WINDOW)
                            for h in later)
    return code, acted


def needed_shas(record):
    shas = {record["merge_request"].get("sha")}
    for d in record["discussions"]:
        pos = d["notes"][0].get("position") if d["notes"] else None
        if pos:
            shas.update((pos.get("base_sha"), pos.get("head_sha")))
    return shas


def examples(record, repo):
    mr = record["merge_request"]
    summary = mr_summary(mr)
    for d in record["discussions"]:
        notes = human_notes(d)
        if not notes:
            continue
        first = next(n for n in d["notes"] if not n.get("system"))
        kind_raw, pos = first.get("type"), first.get("position")
        ex = {"mr": summary, "discussion_id": d["id"], "reviewer": notes[0]["author"],
              "thread": notes, "resolved": resolved(d)}
        if kind_raw == "DiffNote" and pos:
            code, acted = line_code(repo, pos, mr.get("sha"))
            if code is None:
                continue
            ex.update(kind="line", code=code, acted_on=acted)
        elif kind_raw in ("DiffNote", "LegacyDiffNote"):
            ex.update(kind="legacy")
        else:
            if notes[0]["author"] == summary["author"] and len(notes) == 1:
                continue
            short_approval = len(notes) == 1 and len(notes[0]["body"]) < 80 and APPROVAL.match(notes[0]["body"])
            ex.update(kind="approval" if short_approval else "general")
        yield ex


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default="data/vtk-history")
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--remote", default="upstream")
    p.add_argument("--out", default="data/review_examples.jsonl")
    p.add_argument("--no-fetch", action="store_true", help="use only revisions already in the local clone")
    args = p.parse_args()

    repo = Repo(args.repo, args.remote)
    files = sorted(Path(args.mirror, "merge_requests").glob("*.json"), key=lambda f: int(f.stem))
    records = [json.loads(f.read_text()) for f in files]

    shas = set().union(*(needed_shas(r) for r in records)) if records else set()
    if args.no_fetch:
        repo.check_present(sorted(s for s in shas if s))
    else:
        repo.ensure(shas)

    counts = {"line": 0, "legacy": 0, "general": 0, "approval": 0, "unavailable": 0, "acted_on": 0}
    with open(args.out, "w") as out:
        for r in records:
            for ex in examples(r, repo):
                counts[ex["kind"]] += 1
                if ex.get("code", {}).get("unavailable"):
                    counts["unavailable"] += 1
                if ex.get("acted_on"):
                    counts["acted_on"] += 1
                out.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"{len(records)} merge requests -> {args.out}")
    print(", ".join(f"{k}: {v}" for k, v in counts.items()))


if __name__ == "__main__":
    main()
