#!/usr/bin/env python3
"""Review a VTK change the way VTK maintainers have reviewed past changes.

For each changed hunk between a base and head commit, gather evidence and ask a model
whether a VTK reviewer would comment:

  precedent     past review threads most similar to the hunk, and past threads on the same file
  rules         the review rules (REVIEW_RULES.md), each with an id
  deprecations  deprecated or removed APIs that appear in the added lines

History is limited to dates before --until, so an evaluation never sees the answers.
The model returns zero or more comments, each tied to a new-side line and to the
evidence it relies on.

Usage:
  python agent/review.py --base <sha> --head <sha> --until 2025-12-17
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "index"))
from search import Index  # noqa: E402

HOST = "http://192.168.50.23:11435"
SKIP_PATH = re.compile(r"^ThirdParty/|/Testing/Data/|/Baseline/|\.(png|jpg|sha512|md5|vtk|vtp|vtu|vti)$")
IDENT = re.compile(r"\b[A-Za-z_]\w{3,}\b")
MAX_HUNK_LINES = 120

SYSTEM = """You review merge requests for VTK, the Visualization Toolkit, the way its maintainers do.

You will see one changed hunk from a merge request, with evidence from VTK's review history: similar past review threads, past threads on the same file, deprecated APIs in the new code, and the project's review rules below.

Comment only where an experienced VTK reviewer would. Most hunks need no comment. Do not restate what the code does, praise it, or raise generic style points the rules and precedent do not support. A good comment names a specific problem or VTK convention and says what to do instead.

Review rules:
{rules}

Reply with JSON only: {{"comments": [{{"line": <new-file line number from the hunk>, "comment": "<what the reviewer would write>", "basis": "<rule id, past MR (e.g. !1234), deprecation, or 'code'>", "severity": "bug" | "convention" | "nit" | "question"}}]}}. Use an empty list when nothing needs a comment."""

USER = """Merge request: {title}
File: {path}

Hunk (new-file line numbers on the left; + added, - removed):
{hunk}

Similar past review threads:
{precedent}

Past review threads on this file:
{file_history}

Deprecated APIs used in the added lines:
{deprecations}"""


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace").stdout


def hunks(repo, base, head):
    """Yield (path, numbered hunk text, added text, added line numbers) for each hunk of the diff."""
    diff = git(repo, "diff", "-U3", "--no-color", base, head)
    path, lines, new_no, added, numbers = None, [], 0, [], []

    def flush():
        if path and lines and added and not SKIP_PATH.search(path):
            return path, "\n".join(lines[:MAX_HUNK_LINES]), "\n".join(added), numbers
        return None

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if (h := flush()):
                yield h
            path, lines, added, numbers = None, [], [], []
        elif line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            if (h := flush()):
                yield h
            m = re.search(r"\+(\d+)", line)
            new_no, lines, added, numbers = int(m.group(1)) if m else 0, [], [], []
        elif path is None or line.startswith(("--- ", "index ", "new file", "deleted file", "similarity", "rename ")):
            continue
        elif line.startswith("+"):
            lines.append(f"{new_no:6} +{line[1:]}")
            added.append(line[1:])
            numbers.append(new_no)
            new_no += 1
        elif line.startswith("-"):
            lines.append(f"{'':6} -{line[1:]}")
        elif line.startswith(" "):
            lines.append(f"{new_no:6}  {line[1:]}")
            new_no += 1
    if (h := flush()):
        yield h


def chat(model, system, user, num_ctx=16384):
    payload = {"model": model, "stream": False, "format": "json", "think": False,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "options": {"temperature": 0, "num_predict": 800, "num_ctx": num_ctx}}
    for attempt in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            return json.loads(json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"])
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  model call failed ({e}); retrying", file=sys.stderr)
            time.sleep(10)
    return {"comments": []}


def load_rules(path="data/rules_verified.json"):
    rules = json.loads(Path(path).read_text())["rules"]
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")
    return rules


class Reviewer:
    def __init__(self, repo, model, rules_path="data/rules_verified.json", deprecations="data/deprecations/index.jsonl",
                 index="data/index", rules=None):
        self.repo, self.model = repo, model
        self.index = Index(index)
        self.rules = rules if rules is not None else load_rules(rules_path)
        self.system = SYSTEM.format(rules="\n".join(f"{r['id']}: {r['rule']}" for r in self.rules))
        self.deprecated = {}
        for line in open(deprecations):
            rec = json.loads(line)
            self.deprecated.setdefault(rec["symbol"], []).append(rec)

    def _threads(self, hits, exclude_ref):
        out = []
        for h in hits:
            if h["ref"] == exclude_ref:
                continue
            body = " ".join(h["text"].split())[:500]
            out.append(f"- {h['ref']} ({h['date']}, {h['author']}, {h['path'] or ''}): {body}")
        return "\n".join(out) or "(none)"

    def _deprecations(self, path, added, until):
        stem = Path(path).stem
        idents = set(IDENT.findall(added))
        notes = []
        for sym in sorted(idents & self.deprecated.keys()):
            if not re.search(r"[a-z][A-Z]|_", sym):
                continue
            recs = [r for r in self.deprecated[sym] if r["deprecated"]["date"] < until]
            specific = [r for r in recs if r["class"] in idents or r["class"] == stem]
            for r in specific or (recs if len({x["class"] for x in recs}) >= 2 else []):
                gone = r["removed"] and r["removed"]["date"] < until
                state = "removed" if gone and r["outcome"] == "removed" else f"deprecated in {r['version']}"
                mr = f" by !{r['deprecated']['mr']}" if r["deprecated"]["mr"] else ""
                notes.append(f"- {r['class']}::{sym} {state}{mr}: {r['reason'] or 'no reason given'}")
        return "\n".join(list(dict.fromkeys(notes))[:8]) or "(none)"

    def review_hunk(self, title, path, hunk, added, numbers, until, exclude_ref):
        precedent = self.index.search(f"{path}\n{added[:1500]}", k=5, kind="thread", until=until)
        on_file = self.index.search(added[:800], k=4, kind="thread", path=path, until=until)
        user = USER.format(title=title, path=path, hunk=hunk, precedent=self._threads(precedent, exclude_ref),
                           file_history=self._threads(on_file, exclude_ref),
                           deprecations=self._deprecations(path, added, until))
        out = chat(self.model, self.system, user).get("comments") or []
        comments = []
        for c in out if isinstance(out, list) else []:
            if not isinstance(c, dict) or not c.get("comment"):
                continue
            try:
                line = int(c.get("line"))
            except (TypeError, ValueError):
                line = numbers[0]
            if line not in numbers:
                line = min(numbers, key=lambda n: abs(n - line))
            comments.append({"path": path, "line": line, "comment": c["comment"], "basis": c.get("basis"),
                             "severity": c.get("severity"),
                             "evidence": [h["ref"] for h in precedent + on_file if h["ref"] != exclude_ref]})
        return comments

    def review(self, base, head, title, until, exclude_ref=None, max_hunks=60, parallel=2):
        from concurrent.futures import ThreadPoolExecutor
        todo = list(hunks(self.repo, base, head))[:max_hunks]
        with ThreadPoolExecutor(parallel) as pool:
            results = pool.map(lambda h: self.review_hunk(title, *h, until, exclude_ref), todo)
        return [c for cs in results for c in cs], len(todo)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--until", required=True, help="use only history before this date (YYYY-MM-DD)")
    p.add_argument("--model", default="nemotron-3.5-lightning:latest")
    args = p.parse_args()
    comments, n = Reviewer(args.repo, args.model).review(args.base, args.head, args.title, args.until)
    print(f"{len(comments)} comments on {n} hunks")
    for c in comments:
        print(f"{c['path']}:{c['line']} [{c['severity']}, {c['basis']}]\n    {c['comment']}\n")


if __name__ == "__main__":
    main()
