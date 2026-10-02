#!/usr/bin/env python3
"""Review a VTK change the way VTK maintainers have reviewed past changes.

For each changed hunk between a base and head commit, gather evidence and ask a model
whether a VTK reviewer would comment:

  precedent     past review threads most similar to the hunk, and past threads on the same file
  rules         the review rules most similar to the hunk, each with an id
  deprecations  deprecated or removed APIs that appear in the added lines

History is limited to dates before --until, so an evaluation never sees the answers.
Each hunk yields at most one or two draft comments tied to new-side lines. A final pass
drops near-duplicates and keeps about one comment per six hunks (at least two): the
ones the model judges a maintainer would actually post.

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

You will see one changed hunk from a merge request, with evidence from VTK's review history: similar past review threads, past threads on the same file, deprecated APIs in the new code, and the review rules most related to this hunk.

VTK reviewers comment on roughly one hunk in seven. Most hunks need no comment, so an empty list is the usual answer. Comment only when the added lines themselves show a specific problem: a bug, a misuse of a VTK API, a missing test or release note detail, or a clear break from a rule listed below. Do not apply a rule unless the added lines violate it. Do not restate what the code does, praise it, ask the author to "verify" or "ensure" something without saying what is wrong, or suggest changes to lines the hunk did not add.

Give at most one comment, or two if one of them is a bug. Write it the way a VTK maintainer would: short, direct, and naming what to change.

Reply with JSON only: {"comments": [{"line": <new-file line number of an added line>, "comment": "<what the reviewer would write>", "basis": "<rule id, past MR (e.g. !1234), deprecation, or 'code'>", "severity": "bug" | "convention" | "nit" | "question"}]}."""

SELECT = """These are candidate review comments on one VTK merge request, titled "{title}". A VTK maintainer reviewing it would post about {k} comments.

{candidates}

Keep at most {k}: the comments a VTK maintainer would actually post, preferring bugs, API misuse, and concrete requested changes. Drop generic style advice, speculation, requests to "verify" or "check", and duplicates.
Reply with JSON only: {{"keep": [<candidate numbers>]}}"""

USER = """Merge request: {title}
File: {path}

Hunk (new-file line numbers on the left; + added, - removed):
{hunk}

Similar past review threads:
{precedent}

Past review threads on this file:
{file_history}

Deprecated APIs used in the added lines:
{deprecations}

Review rules most related to this hunk:
{rules}"""
RULES_PER_HUNK = 6
DOC_RULES = 3


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


def rule_key(r):
    from hashlib import sha1
    return sha1("|".join(sorted(r["members"])).encode()).hexdigest()[:12]


def load_rules(path="data/rules_verified.json", confidence="data/rules_confidence.json", skip_automated=True,
               levels=True):
    """Mined rules numbered in file order, with confidence levels; rules a tool enforces are left to the tool."""
    rules = json.loads(Path(path).read_text())["rules"]
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")
    conf_path = Path(confidence)
    if (skip_automated or levels) and conf_path.exists():
        conf = json.loads(conf_path.read_text())["rules"]
        if skip_automated:
            rules = [r for r in rules if not conf.get(rule_key(r), {}).get("automated")]
        if levels:
            for r in rules:
                c = conf.get(rule_key(r))
                if c:
                    r["level"], r["reviewers"] = c["level"], c["reviewers"]
    return rules


def load_doc_rules(rules, path="data/doc_rules.json", matches="data/doc_match.json", dates="data/doc_rule_dates.json"):
    """Rules quoted from VTK's developer docs, dated, and linked to the mined rule they restate."""
    doc = json.loads(Path(path).read_text())["rules"]
    when = json.loads(Path(dates).read_text())["dates"]
    same = {}
    by_key = {rule_key(r): r["id"] for r in rules}
    for key, m in json.loads(Path(matches).read_text())["matches"].items():
        if m["verdict"] == "same" and key in by_key:
            same[m["doc"]] = by_key[key]
    return [{**d, "date": when.get(d["id"]), "same_as": same.get(d["id"])} for d in doc]


class Reviewer:
    def __init__(self, repo, model, rules_path="data/rules_verified.json", deprecations="data/deprecations/index.jsonl",
                 index="data/index", rules=None, doc_rules=None):
        self.repo, self.model = repo, model
        self.index = Index(index)
        self.rules = rules if rules is not None else load_rules(rules_path)
        self.doc_rules = doc_rules or []
        self.until = None
        self.system = SYSTEM
        self.rule_vectors = self.index.embed([f"{r['rule']} ({r.get('scope') or ''})" for r in self.rules], query=False)
        self.doc_vectors = (self.index.embed([d["rule"] for d in self.doc_rules], query=False)
                            if self.doc_rules else None)
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

    def _related_rules(self, text):
        query = self.index.embed([text])[0]
        top = [self.rules[i] for i in (self.rule_vectors @ query).argsort()[::-1][:RULES_PER_HUNK]]
        docs = [d for d in self.doc_rules if d["date"] and (not self.until or d["date"] < self.until)]
        documented = {d["same_as"]: d["file"] for d in docs if d["same_as"]}
        lines = []
        for r in top:
            tags = []
            if r.get("level"):
                tags.append(f"{r['level']} confidence, {r['reviewers']} reviewers")
            if r["id"] in documented:
                tags.append(f"also in {documented[r['id']]}")
            lines.append(f"{r['id']}{' [' + '; '.join(tags) + ']' if tags else ''}: {r['rule']}")
        if docs:
            shown = {r["id"] for r in top}
            index = {d["id"]: i for i, d in enumerate(self.doc_rules)}
            scores = self.doc_vectors @ query
            extra = sorted((d for d in docs if d["same_as"] not in shown), key=lambda d: -scores[index[d["id"]]])
            lines += [f"{d['id']} [documented, {d['strength']}, {d['file']}]: {d['rule']}" for d in extra[:DOC_RULES]]
        return "\n".join(lines)

    def review_hunk(self, title, path, hunk, added, numbers, until, exclude_ref):
        query = f"{path}\n{added[:1500]}"
        precedent = self.index.search(query, k=5, kind="thread", until=until)
        on_file = self.index.search(added[:800], k=4, kind="thread", path=path, until=until)
        user = USER.format(title=title, path=path, hunk=hunk, precedent=self._threads(precedent, exclude_ref),
                           file_history=self._threads(on_file, exclude_ref),
                           deprecations=self._deprecations(path, added, until), rules=self._related_rules(query))
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

    def select(self, title, candidates, k, verified=()):
        """Keep the comments a maintainer would post.

        Near-duplicates (same file, within 3 lines, mostly the same words) are merged. Comments on a
        line a static check flagged are kept outright; the model picks up to k of the rest.
        """
        words = lambda c: set(c["comment"].lower().split())
        same = lambda a, b: (a["path"] == b["path"] and abs(a["line"] - b["line"]) <= 3
                             and len(words(a) & words(b)) >= 0.5 * len(words(a) | words(b)))
        unique = []
        for c in candidates:
            if not any(same(u, c) for u in unique):
                unique.append(c)
        kept = list({(c["path"], c["line"]): c for c in reversed(unique) if (c["path"], c["line"]) in verified}.values())[::-1]
        unique = [c for c in unique if (c["path"], c["line"]) not in verified]
        if len(unique) <= k:
            return kept + unique
        listing = "\n".join(f"{i}. {c['path']}:{c['line']} [{c['severity']}] {c['comment'][:400]}"
                            for i, c in enumerate(unique))
        out = chat(self.model, "You select code review comments. Reply with JSON only.",
                   SELECT.format(title=title, k=k, candidates=listing), num_ctx=32768)
        keep = [i for i in out.get("keep") or [] if isinstance(i, int) and 0 <= i < len(unique)]
        if not keep:
            order = {"bug": 0, "question": 1, "convention": 2, "nit": 3}
            keep = sorted(range(len(unique)), key=lambda i: order.get(unique[i]["severity"], 4))
        return kept + [unique[i] for i in dict.fromkeys(keep)][:k]

    def review(self, base, head, title, until, exclude_ref=None, max_hunks=60, parallel=2, per_hunks=6):
        from concurrent.futures import ThreadPoolExecutor
        self.until = until
        todo = list(hunks(self.repo, base, head))[:max_hunks]
        with ThreadPoolExecutor(parallel) as pool:
            results = pool.map(lambda h: self.review_hunk(title, *h, until, exclude_ref), todo)
        candidates = [c for cs in results for c in cs]
        k = max(2, -(-len(todo) // per_hunks))
        return self.select(title, candidates, k), len(todo), len(candidates)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--until", required=True, help="use only history before this date (YYYY-MM-DD)")
    p.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    args = p.parse_args()
    comments, n, drafted = Reviewer(args.repo, args.model).review(args.base, args.head, args.title, args.until)
    print(f"{len(comments)} comments kept of {drafted} drafted on {n} hunks")
    for c in comments:
        print(f"{c['path']}:{c['line']} [{c['severity']}, {c['basis']}]\n    {c['comment']}\n")


if __name__ == "__main__":
    main()
