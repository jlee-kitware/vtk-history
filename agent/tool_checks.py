#!/usr/bin/env python3
"""Run the checks VTK's tools and GitLab robot apply, on one MR revision, before the robot does.

  clang-format  lines this revision adds that clang-format 18 (VTK's pinned version, with the .clang-format
                at the revision) would rewrite
  codespell     misspellings on added lines, with VTK's .codespellrc
  whitespace    trailing whitespace or tab indentation on added lines of C/C++ sources
  commits       subjects over 78 characters, WIP/fixup/squash commits, author names without a space
  release note  no file added under Documentation/release/dev
  third party   edits inside ThirdParty/<name>/vtk<name>, which is imported from upstream

Findings are facts from the tools, reported apart from the agent's review comments.

Usage:
  python agent/tool_checks.py <base> <head> [--repo $VTK_REPO]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import difflib
import re
import subprocess
import tempfile
from pathlib import Path

CXX = (".c", ".h", ".cpp", ".cxx", ".hxx", ".txx", ".mm")
CLANG_FORMAT = "clang-format"
CODESPELL = str(Path.home() / ".local/bin/codespell")


def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=check).stdout


def added_lines(repo, base, head):
    """{path: {line number at head: text}} for lines the revision adds."""
    out, path, line = {}, None, 0
    for row in git(repo, "diff", "-U0", "--no-color", base, head).splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
            if path:
                out.setdefault(path, {})
        elif row.startswith("@@") and path:
            line = int(re.match(r"@@ -\S+ \+(\d+)", row).group(1))
        elif row.startswith("+") and path:
            out[path][line] = row[1:]
            line += 1
    return {p: lines for p, lines in out.items() if lines}


def spans(numbers):
    numbers, out = sorted(numbers), []
    for n in numbers:
        if out and n == out[-1][1] + 1:
            out[-1][1] = n
        else:
            out.append([n, n])
    return out


def clang_format(repo, head, added, tmp):
    style = tmp / ".clang-format"
    style.write_text(git(repo, "show", f"{head}:.clang-format"))
    findings = []
    for path, lines in added.items():
        if not path.endswith(CXX) or path.startswith("ThirdParty/"):
            continue
        source = git(repo, "show", f"{head}:{path}")
        formatted = subprocess.run([CLANG_FORMAT, f"--style=file:{style}", f"--assume-filename={path}"],
                                   input=source, capture_output=True, text=True).stdout
        changed = set()
        matcher = difflib.SequenceMatcher(None, source.splitlines(), formatted.splitlines(), autojunk=False)
        for tag, i1, i2, _, _ in matcher.get_opcodes():
            if tag != "equal":
                changed.update(range(i1 + 1, max(i2, i1 + 1) + 1))
        for start, end in spans(changed & set(lines)):
            where = f"line {start}" if start == end else f"lines {start}-{end}"
            findings.append({"tool": "clang-format", "path": path, "line": start,
                             "message": f"clang-format would reformat {where}; comment `Do: reformat` on the MR "
                                        "or run Utilities/Scripts/clang-format.bash"})
    return findings


def codespell(repo, head, added, tmp):
    config = tmp / ".codespellrc"
    config.write_text(git(repo, "show", f"{head}:.codespellrc", check=False))
    findings = []
    for path, lines in added.items():
        if path.startswith(("ThirdParty/", "Utilities/")) or path.endswith((".png", ".jpg", ".vtp", ".sha512")):
            continue
        body = tmp / "added.txt"
        body.write_text("\n".join(lines.values()) + "\n")
        numbers = list(lines)
        out = subprocess.run([CODESPELL, "--config", str(config), str(body)], capture_output=True, text=True).stdout
        for row in out.splitlines():
            m = re.match(r".*?:(\d+): (.*)", row)
            if m:
                findings.append({"tool": "codespell", "path": path, "line": numbers[int(m.group(1)) - 1],
                                 "message": f"spelling: {m.group(2)}"})
    return findings


def whitespace(added):
    findings = []
    for path, lines in added.items():
        if not path.endswith(CXX) or path.startswith("ThirdParty/"):
            continue
        bad = [n for n, text in lines.items() if text != text.rstrip() or re.match(r"^ *\t", text)]
        for start, end in spans(bad):
            findings.append({"tool": "whitespace", "path": path, "line": start,
                             "message": "trailing whitespace or tab indentation"
                                        + (f" on lines {start}-{end}" if end > start else "")})
    return findings


def commits(repo, base, head):
    findings = []
    for row in git(repo, "log", "--format=%h%x00%s%x00%an", f"{base}..{head}").splitlines():
        sha, subject, author = row.split("\x00")
        if len(subject) > 78:
            findings.append({"tool": "commit", "path": None, "line": None,
                             "message": f"commit {sha}: subject is {len(subject)} characters; the limit is 78"})
        if re.match(r"(WIP|fixup!|squash!|amend!)", subject, re.I):
            findings.append({"tool": "commit", "path": None, "line": None,
                             "message": f"commit {sha} is a WIP or fixup commit; squash it before merging"})
        if " " not in author.strip():
            findings.append({"tool": "commit", "path": None, "line": None,
                             "message": f"commit {sha}: author name '{author}' has no space; use your full name"})
    return findings


def project(repo, base, head):
    changed = git(repo, "diff", "--name-status", base, head).splitlines()
    findings = []
    paths = [row.split("\t")[-1] for row in changed]
    if not any(p.startswith("Documentation/release/dev/") for p in paths):
        findings.append({"tool": "release note", "path": None, "line": None,
                         "message": "no release note: add a file under Documentation/release/dev/ for user-visible changes"})
    for p in paths:
        m = re.match(r"ThirdParty/([^/]+)/vtk([^/]+)/", p)
        if m and m.group(1).lower() == m.group(2).lower():
            findings.append({"tool": "third party", "path": p, "line": None,
                             "message": f"{p} is imported from upstream {m.group(1)}; change it upstream and "
                                        "reimport with ThirdParty/" + m.group(1) + "/update.sh"})
    return findings


def check(repo, base, head):
    added = added_lines(repo, base, head)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        found = (clang_format(repo, head, added, tmp) + codespell(repo, head, added, tmp) + whitespace(added)
                 + commits(repo, base, head) + project(repo, base, head))
    unique = {(f["tool"], f["path"], f["line"], f["message"]): f for f in found}
    return list(unique.values())


def render(findings):
    if not findings:
        return "(none)"
    return "\n".join(f"- [{f['tool']}] " + (f"{f['path']}:{f['line']} " if f["line"] else f"{f['path']} " if f["path"] else "")
                     + f["message"] for f in findings)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--repo", default=config.VTK_REPO)
    args = ap.parse_args()
    for f in check(args.repo, args.base, args.head):
        where = f"{f['path']}:{f['line']}" if f["line"] else (f["path"] or "")
        print(f"[{f['tool']}] {where} {f['message']}")


if __name__ == "__main__":
    main()
