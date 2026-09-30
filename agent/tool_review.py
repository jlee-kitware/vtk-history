#!/usr/bin/env python3
"""Review a whole VTK merge request with tools, the way a maintainer investigates one.

The model sees the full diff (or a file list, for very large changes) and can call tools
to look beyond it:

  read_diff        the diff of one file, with new-file line numbers
  read_file        lines of a file at the head commit
  grep             search the head commit (callers, definitions, where a variable is set)
  search_history   past review threads, MRs, issues, and forum posts before the review date
  file_history     recent commits that touched a file before this MR
  rules            the review rules most related to a topic
  deprecations     whether an API was deprecated or removed, and what replaces it
  add_comment      post a review comment on a new-side line
  finish           end the review

History tools see only dates before --until. After the loop, near-duplicate comments are
merged and, if there are more than about one per six hunks, the model keeps the best ones.

Usage:
  python agent/tool_review.py --base <sha> --head <sha> --until 2025-12-17 --title "..."
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import static_checks  # noqa: E402
from review import HOST, Reviewer, hunks  # noqa: E402

MAX_STEPS = 40
MIN_INVESTIGATION = 3
FULL_DIFF_CHARS = 40000
MAX_TOOL_CHARS = 6000

SYSTEM = """You are an experienced VTK maintainer reviewing a merge request. Review it the way VTK maintainers do: look for real problems and project conventions, and say what to change.

How to work:
1. Read the change. For a large change, read the diffs of the files that matter most.
2. Investigate before commenting. For each new function, method, member, option, or variable, grep for it: is it called, is it implemented, is what it allocates released, and is the variable set anywhere? Unused, unimplemented, leaked, or never-set code is among the most common things VTK reviewers catch. Use read_file to see surrounding code. Use search_history and rules to see how VTK reviewers treated similar code, and deprecations for APIs that look outdated.
3. Post a comment with add_comment only for a concrete, verified problem: a bug, a resource leak, dead or unimplemented code, a build or configuration error, API misuse, a missing test or release note detail, or a clear break from a VTK rule. Keep each comment short and direct, the way a maintainer writes, and name what to change. Never post a comment you have not checked against the code.
4. Call finish when done.

VTK reviewers post about one comment per six changed hunks. Do not comment on style unless a rule covers it, do not praise, and do not ask the author to "verify" or "ensure" something without saying what is wrong. Comment only on lines this merge request adds."""

REPEAT = ("(You already ran this exact call; its result is above. Do not repeat it. Post a comment for a problem you "
          "have verified, use a different tool or arguments, or call finish.)")
WRAP_UP = ("You have {left} steps left. Post each problem you have verified with add_comment now, then call finish. "
           "Do not read more code unless one check decides whether a comment is right.")

CHECKS_NOTE = ("These are text-search results, so confirm each with grep or read_file before commenting: a method can "
               "be defined by a macro, and a resource can be released through a helper. Each one you confirm is a "
               "problem VTK reviewers raise, so post it.")

TOO_EARLY = ("(Not yet: you have not investigated the change. Before finishing, check at least a few things: grep "
             "for the new functions, members, or options to see if they are used, implemented, and set; read the "
             "surrounding code; or search_history for how reviewers treated similar changes.)")

REPORT = """The investigation is over. Write your review now, using only what you found above.
List each concrete problem you verified in the code: a bug, a leak, dead or unimplemented code, something never set or never called, a build or configuration error, API misuse, or a clear break from a VTK rule. Include problems you already posted. Put each comment on the added line it concerns and write it the way a VTK maintainer would: short, direct, naming what to change.
Reply with JSON only: {"comments": [{"path": "<changed file>", "line": <new-file line>, "comment": "...", "severity": "bug" | "convention" | "nit" | "question", "basis": "<what you checked>"}]}. Use an empty list if you verified no problem."""

TOOLS = [
    {"type": "function", "function": {"name": "read_diff", "description": "Diff of one changed file, with new-file line numbers.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "read_file", "description": "Lines of a file at the head commit (up to 200 lines).",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "start": {"type": "integer"},
                                                     "end": {"type": "integer"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "grep", "description": "Search the head commit with a regular expression. Returns up to 40 matching lines as path:line:text.",
     "parameters": {"type": "object", "properties": {"pattern": {"type": "string"},
                                                     "path_glob": {"type": "string", "description": "optional, e.g. 'Rendering/**' or '*.cmake'"}},
                    "required": ["pattern"]}}},
    {"type": "function", "function": {"name": "search_history", "description": "Search past VTK review threads, MRs, issues, forum posts, design documents, release notes, and class documentation.",
     "parameters": {"type": "object", "properties": {"query": {"type": "string"},
                                                     "kind": {"type": "string", "enum": ["thread", "mr", "issue", "post", "doc", "note", "class"]}},
                    "required": ["query"]}}},
    {"type": "function", "function": {"name": "file_history", "description": "Recent commits that touched a file before this merge request.",
     "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    {"type": "function", "function": {"name": "rules", "description": "VTK review rules most related to a topic.",
     "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}}},
    {"type": "function", "function": {"name": "deprecations", "description": "Whether a VTK class or method was deprecated or removed, when, and what replaces it.",
     "parameters": {"type": "object", "properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}}},
    {"type": "function", "function": {"name": "add_comment", "description": "Post a review comment on a line this merge request adds.",
     "parameters": {"type": "object", "properties": {
         "path": {"type": "string"}, "line": {"type": "integer", "description": "new-file line number"},
         "comment": {"type": "string"}, "severity": {"type": "string", "enum": ["bug", "convention", "nit", "question"]},
         "basis": {"type": "string", "description": "what supports it: code you checked, a rule id, a past MR, or a deprecation"}},
         "required": ["path", "line", "comment", "severity"]}}},
    {"type": "function", "function": {"name": "finish", "description": "End the review.",
     "parameters": {"type": "object", "properties": {}}}},
]


def chat_tools(model, messages, num_ctx=65536):
    payload = {"model": model, "stream": False, "messages": messages, "tools": TOOLS,
               "options": {"temperature": 0.2, "num_predict": 2048, "num_ctx": num_ctx}}
    for attempt in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=1800))["message"]
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  model call failed ({e}); retrying", file=sys.stderr)
            time.sleep(15)
    return {"role": "assistant", "content": ""}


class ToolReviewer(Reviewer):
    def git(self, *args, timeout=60):
        r = subprocess.run(["git", "-C", self.repo, *args], capture_output=True, text=True, errors="replace",
                           timeout=timeout)
        return r.stdout if r.returncode == 0 else f"(git error: {r.stderr.strip()[:300]})"

    def _history(self, query, kind=None):
        hits = [h for h in self.index.search(query, k=8, kind=kind, until=self.until) if h["ref"] != self.exclude_ref]
        return "\n".join(f"- {h['kind']} {h['ref']} ({h['date']}, {h['author']}{', ' + h['path'] if h['path'] else ''}): "
                         f"{' '.join(h['text'].split())[:600]}" for h in hits[:6]) or "(nothing found)"

    def _deprecation_lookup(self, symbol):
        name = symbol.split("::")[-1]
        cls = symbol.split("::")[0] if "::" in symbol else None
        recs = [r for r in self.deprecated.get(name, []) if not cls or r["class"] == cls]
        recs += [r for recs_ in self.deprecated.values() for r in recs_ if r["class"] == name and r not in recs][:10]
        lines = []
        for r in recs:
            if r["deprecated"]["date"] >= self.until:
                continue
            state = f"deprecated in {r['version']} on {r['deprecated']['date']}"
            if r["deprecated"]["mr"]:
                state += f" by !{r['deprecated']['mr']}"
            if r["removed"] and r["removed"]["date"] < self.until:
                state += f"; {r['outcome']} on {r['removed']['date']}"
            lines.append(f"- {r['class']}::{r['symbol']}: {state}. Reason: {r['reason'] or 'none given'}")
        return "\n".join(lines[:12]) or f"(no deprecation recorded for {symbol} before {self.until})"

    def run_tool(self, name, args):
        if name == "read_diff":
            return self.diffs.get(args.get("path", ""), f"(not changed in this MR; changed files: {', '.join(self.diffs)})")
        if name == "read_file":
            text = self.git("show", f"{self.head}:{args.get('path', '')}")
            if text.startswith("(git error"):
                return text
            lines = text.splitlines()
            start = max(1, int(args.get("start") or 1))
            end = min(len(lines), int(args.get("end") or start + 199), start + 199)
            return "\n".join(f"{i:6}  {lines[i - 1]}" for i in range(start, end + 1)) or "(empty range)"
        if name == "grep":
            glob = args.get("path_glob")
            out = self.git("grep", "-n", "-I", "-E", "-e", args.get("pattern", ""), self.head, *(["--", glob] if glob else []))
            rows = [line.split(":", 1)[1][:220] for line in out.splitlines() if ":" in line]
            return "\n".join(rows[:40]) + (f"\n... {len(rows) - 40} more" if len(rows) > 40 else "") if rows else (
                out if out.startswith("(git error") else "(no matches)")
        if name == "search_history":
            return self._history(args.get("query", ""), args.get("kind"))
        if name == "file_history":
            return self.git("log", "--format=%h %ad %an: %s", "--date=short", "-n", "12", self.base, "--",
                            args.get("path", "")) or "(no earlier commits)"
        if name == "rules":
            return self._related_rules(args.get("topic", ""))
        if name == "deprecations":
            return self._deprecation_lookup(args.get("symbol", ""))
        if name == "add_comment":
            path = args.get("path", "")
            if path not in self.added:
                return f"(rejected: {path} is not changed by this MR)"
            try:
                line = int(args.get("line"))
            except (TypeError, ValueError):
                return "(rejected: line must be a new-file line number)"
            if line not in self.added[path]:
                line = min(self.added[path], key=lambda n: abs(n - line))
            self.comments.append({"path": path, "line": line, "comment": args.get("comment", ""),
                                  "severity": args.get("severity"), "basis": args.get("basis")})
            return f"recorded at {path}:{line}"
        return f"(There is no tool named {name}. The tools are: {', '.join(t['function']['name'] for t in TOOLS)}.)"

    def report(self, messages):
        """Ask for the verified findings as structured comments, with no further tool use."""
        payload = {"model": self.model, "stream": False, "format": "json",
                   "messages": messages + [{"role": "user", "content": REPORT}],
                   "options": {"temperature": 0, "num_predict": 3000, "num_ctx": 65536}}
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            out = json.loads(json.load(urllib.request.urlopen(req, timeout=1800))["message"]["content"])
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  report failed ({e})", file=sys.stderr)
            return
        for c in out.get("comments") or []:
            if isinstance(c, dict) and c.get("comment"):
                result = self.run_tool("add_comment", c)
                self.trace.append({"step": "report", "tool": "add_comment", "args": c, "result": result})

    def review(self, base, head, title, until, exclude_ref=None, per_hunks=6, **_):
        self.base, self.head, self.until, self.exclude_ref = base, head, until, exclude_ref
        self.comments, self.diffs, self.added, self.trace = [], {}, {}, []
        todo = list(hunks(self.repo, base, head))
        for path, text, _added, numbers in todo:
            self.diffs[path] = (self.diffs[path] + "\n...\n" if path in self.diffs else "") + text
            self.added.setdefault(path, set()).update(numbers)
        if not todo:
            return [], 0, 0
        listing = "\n".join(f"- {p} (+{len(self.added[p])} lines)" for p in self.diffs)
        full = "\n\n".join(f"=== {p}\n{d}" for p, d in self.diffs.items())
        body = full if len(full) <= FULL_DIFF_CHARS else "(The diff is large; use read_diff for the files you want.)"
        self.findings = static_checks.check(self.repo, head, todo)
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": f"Merge request: {title}\n\nChanged files:\n{listing}\n\n"
                                                f"Automatic checks of the head commit found:\n"
                                                f"{static_checks.render(self.findings)}\n{CHECKS_NOTE}\n\n{body}"}]
        nudges, seen, repeats, warned = 0, set(), 0, False
        for step in range(MAX_STEPS):
            if not warned and (repeats >= 2 or step >= MAX_STEPS - 8):
                warned = True
                messages.append({"role": "user", "content": WRAP_UP.format(left=MAX_STEPS - step)})
            msg = chat_tools(self.model, messages)
            messages.append({k: v for k, v in msg.items() if k in ("role", "content", "tool_calls", "thinking")})
            calls = msg.get("tool_calls") or []
            if not calls:
                if nudges >= 2:
                    break
                nudges += 1
                messages.append({"role": "user", "content": "Continue the review with the tools, or call finish."})
                continue
            done = False
            for call in calls:
                fn = call.get("function", {})
                name, args = fn.get("name"), fn.get("arguments") or {}
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                key = json.dumps([name, args], sort_keys=True)
                investigated = sum(1 for t in self.trace if t["tool"] not in ("finish", "add_comment"))
                if name == "finish" and investigated < MIN_INVESTIGATION:
                    result = TOO_EARLY
                elif name == "finish":
                    done = True
                    result = "review finished"
                elif key in seen and name != "add_comment":
                    repeats += 1
                    result = REPEAT
                else:
                    seen.add(key)
                    try:
                        result = self.run_tool(name, args)
                    except Exception as e:  # a bad tool argument should not end the review
                        result = f"(tool error: {e})"
                self.trace.append({"step": step, "tool": name, "args": args, "result": result[:300]})
                messages.append({"role": "tool", "tool_name": name, "content": result[:MAX_TOOL_CHARS]})
            if done or repeats >= 5:
                break
        self.report(messages)
        k = max(2, -(-len(todo) // per_hunks))
        verified = {(f["path"], f["line"]) for f in self.findings}
        return self.select(title, self.comments, k, verified), len(todo), len(self.comments)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--title", default="")
    p.add_argument("--until", required=True, help="use only history before this date (YYYY-MM-DD)")
    p.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    args = p.parse_args()
    reviewer = ToolReviewer(args.repo, args.model)
    comments, n, drafted = reviewer.review(args.base, args.head, args.title, args.until)
    for t in reviewer.trace:
        print(f"  [{t['step']}] {t['tool']}({json.dumps(t['args'])[:120]}) -> {t['result'][:100]!r}")
    print(f"{len(comments)} comments kept of {drafted} posted on {n} hunks")
    for c in comments:
        print(f"{c['path']}:{c['line']} [{c['severity']}, {c['basis']}]\n    {c['comment']}\n")


if __name__ == "__main__":
    main()
