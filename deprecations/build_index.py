#!/usr/bin/env python3
"""Index every API VTK deprecated: when, why, in which merge request, and when it was removed.

Walks master's first-parent history with each merge's full diff, so every event maps to
the merge commit GitLab recorded for its MR. An event is a header line that gains or
loses a VTK_DEPRECATED_IN_x_y_z(...) or VTK_LEGACY(...) marker.

A deprecated declaration whose marker later disappears is recorded as removed by that
merge, or as un-deprecated when the same declaration is still added back without a marker.

Writes data/deprecations/index.jsonl and data/deprecations/SUMMARY.md.

Usage:
  python deprecations/build_index.py
"""

import argparse
import glob
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

MARKER = re.compile(r"\bVTK_DEPRECATED_IN_(\d+)_(\d+)_(\d+)\b|\bVTK_LEGACY\b(?!_)")
STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')
TYPE_DECL = re.compile(r"\b(?:class|struct|using|enum)\s+(?:VTK\w*_EXPORT\s+)?([A-Za-z_]\w*)")
CALL = re.compile(r"(~?[A-Za-z_]\w*)\s*\(")
ACCESSOR = re.compile(r"vtk(?:Get|Set|Boolean)\w*Macro\s*\(\s*(\w+)")
NOT_SYMBOLS = {"virtual", "static", "inline", "const", "return", "if", "for", "while", "sizeof", "decltype", "operator"}


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace").stdout


def balanced(text, start):
    """Return the index just past the parenthesis group opening at text[start]."""
    depth, quoted, i = 0, False, start
    while i < len(text):
        c = text[i]
        if quoted:
            if c == "\\":
                i += 1
            elif c == '"':
                quoted = False
        elif c == '"':
            quoted = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def parse_marker(buf, m):
    """Version, reason, and the declaration a marker applies to."""
    version = ".".join(m.groups()) if m.group(1) else "legacy"
    rest = buf[m.end():].lstrip()
    if rest.startswith("("):
        end = balanced(rest, 0)
        inside, rest = rest[1:end - 1], rest[end:]
    else:
        inside = ""
    if version == "legacy":
        decl, reason = inside, None
    else:
        reason = " ".join(STRING.findall(inside)) or None
        decl = rest
    decl = re.split(r"[;{]", decl, 1)[0]
    return version, reason, " ".join(decl.split())


def symbol_of(decl):
    m = TYPE_DECL.search(decl) or ACCESSOR.search(decl)
    if m:
        return m.group(1)
    names = [c for c in CALL.findall(decl) if c not in NOT_SYMBOLS and not c.startswith("VTK_")]
    return names[0] if names else None


def events(side_lines, sign):
    """Markers on lines with the given sign; the buffer continues over following lines on that side."""
    for i, (s, text) in enumerate(side_lines):
        if s != sign or text.lstrip().startswith(("#", "//", "*", "/*")):
            continue
        m = MARKER.search(text)
        if not m:
            continue
        buf = text + "\n" + "\n".join(t for s2, t in side_lines[i + 1:i + 6] if s2 in (sign, " "))
        yield parse_marker(buf, MARKER.search(buf))


def walk(repo, ref):
    """Yield (sha, date, subject, file, side_lines) for every hunk touching a deprecation marker."""
    proc = subprocess.Popen(
        ["git", "-C", repo, "log", "--first-parent", "--diff-merges=first-parent", "-p", "--reverse",
         "-G", r"VTK_DEPRECATED_IN_|VTK_LEGACY\b", "--format=@@@%H %cI %s", ref, "--", "*.h", "*.txx", "*.hxx"],
        stdout=subprocess.PIPE, text=True, errors="replace")
    sha = date = subject = path = old_path = None
    hunk, in_header = [], False
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.startswith("@@@"):
            if hunk:
                yield sha, date, subject, path, hunk
            sha, date, subject = (line[3:].split(" ", 2) + [""])[:3]
            path, hunk = None, []
        elif line.startswith("diff --git "):
            if hunk:
                yield sha, date, subject, path, hunk
            path, hunk, in_header = None, [], True
        elif in_header and line.startswith("--- "):
            old_path = line[6:] if line.startswith("--- a/") else None
        elif in_header and line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else old_path
        elif line.startswith("@@"):
            if hunk:
                yield sha, date, subject, path, hunk
            hunk, in_header = [], False
        elif path and not in_header and line[:1] in (" ", "+", "-"):
            hunk.append((line[0], line[1:]))
    if hunk:
        yield sha, date, subject, path, hunk


def load_mrs(mirror):
    by_sha = {}
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        mr = json.load(open(f))["merge_request"]
        for key in ("merge_commit_sha", "squash_commit_sha"):
            if mr.get(key):
                by_sha[mr[key]] = {"mr": mr["iid"], "title": mr["title"]}
    return by_sha


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--ref", default=None, help="branch to walk (default: first of upstream/master, origin/master, master)")
    p.add_argument("--mirror", default="data/vtk-history")
    p.add_argument("--out", default="data/deprecations")
    args = p.parse_args()

    ref = args.ref or next(r for r in ("upstream/master", "origin/master", "master")
                           if git(args.repo, "rev-parse", "--verify", "-q", r).strip())
    mrs = load_mrs(args.mirror)
    print(f"walking {ref}; {len(mrs)} MR merge commits known", flush=True)

    live, records, commits = {}, [], set()
    pending = {}
    current = None

    def flush():
        added, removed = pending.get("+", {}), pending.get("-", {})
        sha, date, subject = current
        where = {"sha": sha, "date": date[:10], "subject": subject, **mrs.get(sha, {"mr": None, "title": None})}
        for key in removed.keys() - added.keys():
            rec = live.pop(key, None)
            if rec:
                rec["removed"] = where
                rec["outcome"] = "undeprecated" if key in pending.get("plain", set()) else "removed"
        for key in added.keys() - removed.keys():
            if key not in live:
                version, reason, decl, path = added[key]
                rec = {"class": key[0], "symbol": key[1], "version": version, "reason": reason, "declaration": decl,
                       "file": path, "deprecated": where, "removed": None, "outcome": "present"}
                live[key] = rec
                records.append(rec)
        pending.clear()

    for sha, date, subject, path, hunk in walk(args.repo, ref):
        if current and sha != current[0]:
            flush()
        current = (sha, date, subject)
        commits.add(sha)
        cls = Path(path).stem
        for sign in ("+", "-"):
            for version, reason, decl in events(hunk, sign):
                sym = symbol_of(decl)
                if sym:
                    pending.setdefault(sign, {})[(cls, sym)] = (version, reason, decl, path)
        plain = {(cls, s) for s_, t in hunk if s_ == "+" and not MARKER.search(t) for s in [symbol_of(t)] if s}
        pending.setdefault("plain", set()).update(plain)
    if current:
        flush()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "index.jsonl", "w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    write_summary(out / "SUMMARY.md", records, ref, len(commits))
    outcomes = Counter(r["outcome"] for r in records)
    print(f"{len(records)} deprecations from {len(commits)} commits: {dict(outcomes)}; "
          f"{sum(1 for r in records if r['deprecated']['mr'])} linked to an MR")


def days(a, b):
    from datetime import date
    return (date.fromisoformat(b) - date.fromisoformat(a)).days


def write_summary(path, records, ref, commits):
    lines = ["# VTK deprecations", "",
             f"{len(records)} deprecated APIs found in {commits} commits on `{ref}` that added or removed a "
             "`VTK_DEPRECATED_IN_*` or `VTK_LEGACY` marker in a header.", "",
             "| Version | Deprecated | Removed | Un-deprecated | Still deprecated | Median days to removal |",
             "| --- | --- | --- | --- | --- | --- |"]
    by_version = {}
    for r in records:
        by_version.setdefault(r["version"], []).append(r)
    order = sorted(by_version, key=lambda v: [int(x) for x in v.split(".")] if v != "legacy" else [0])
    for v in order:
        rs = by_version[v]
        gone = sorted(days(r["deprecated"]["date"], r["removed"]["date"]) for r in rs if r["outcome"] == "removed")
        counts = Counter(r["outcome"] for r in rs)
        lines.append(f"| {v} | {len(rs)} | {counts['removed']} | {counts['undeprecated']} | {counts['present']} | "
                     f"{gone[len(gone) // 2] if gone else '-'} |")
    lines += ["", "## Merge requests that deprecated the most APIs", "", "| MR | Date | APIs | Title |",
              "| --- | --- | --- | --- |"]
    by_mr = Counter((r["deprecated"]["mr"], r["deprecated"]["date"], r["deprecated"]["title"] or r["deprecated"]["subject"])
                    for r in records)
    for (mr, date, title), n in by_mr.most_common(25):
        lines.append(f"| {'!' + str(mr) if mr else '(direct commit)'} | {date} | {n} | {(title or '')[:70].replace('|', '/')} |")
    lines += ["", "## Modules with the most deprecations", "", "| Module directory | APIs | Still deprecated |",
              "| --- | --- | --- |"]
    by_dir = Counter("/".join(Path(r["file"]).parts[:2]) for r in records)
    still = Counter("/".join(Path(r["file"]).parts[:2]) for r in records if r["outcome"] == "present")
    for d, n in by_dir.most_common(20):
        lines.append(f"| {d} | {n} | {still[d]} |")
    Path(path).write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
