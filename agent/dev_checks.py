#!/usr/bin/env python3
"""Run the checks a VTK developer runs on a change, in a configured build tree.

For a revision (base, head), with the worktree checked out at head and the tree reconfigured:

  cmake       configure with --warn-uninitialized; errors, and warnings in changed CMake files
  compile     each changed C++ source, and the source paired with each changed header, with
              -fsyntax-only -Wall -Wextra; errors anywhere in the changed files, warnings on added lines
  clang-tidy  VTK's own .clang-tidy on the changed sources; diagnostics on added lines
  ruff        changed Python files; findings on added lines

Only the files the change touches are compiled, so a check takes about a minute plus the configure.
A lock keeps two reviews from using the tree at once.

Usage:
  python agent/dev_checks.py --base <sha> --head <sha>
"""

import argparse
import fcntl
import json
import os
import re
import shlex
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

WORKTREE = Path(os.environ.get("VTK_REVIEW_WORKTREE", "/home/jlee/gitsync/vtk-review-wt"))
BUILD = Path(os.environ.get("VTK_REVIEW_BUILD", "/home/jlee/gitsync/vtk-review-build"))
BIN = Path.home() / ".local/bin"
CXX = re.compile(r"\.(cxx|cpp|cc|c|mm)$")
HEADER = re.compile(r"\.(h|hxx|txx)$")
CMAKE = re.compile(r"(CMakeLists\.txt|\.cmake)$")
CONFIGURE = ["-G", "Ninja", "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
             "-DCMAKE_DISABLE_PRECOMPILE_HEADERS=ON", "-DVTK_BUILD_TESTING=ON", "-DVTK_WRAP_PYTHON=OFF",
             "-DVTK_GROUP_ENABLE_Rendering=YES", "-DVTK_GROUP_ENABLE_StandAlone=YES",
             "-DCMAKE_C_COMPILER=clang", "-DCMAKE_CXX_COMPILER=clang++"]
MAX_TIDY = 8


def run(cmd, cwd=None, timeout=600):
    env = dict(os.environ, PATH=f"{BIN}:{os.environ.get('PATH', '')}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace", timeout=timeout, env=env)


def checkout(repo, head):
    if not WORKTREE.exists():
        run(["git", "-C", repo, "worktree", "add", "--detach", str(WORKTREE), head])
    r = run(["git", "-C", str(WORKTREE), "checkout", "--quiet", "--detach", "--force", head])
    if r.returncode:
        raise RuntimeError(f"checkout failed: {r.stderr.strip()[:300]}")


def configure():
    """Fresh configure (old revisions may not accept a newer cache); returns cmake's stderr."""
    BUILD.mkdir(parents=True, exist_ok=True)
    for stale in (BUILD / "CMakeCache.txt",):
        stale.unlink(missing_ok=True)
    r = run(["cmake", "--warn-uninitialized", *CONFIGURE, "-S", str(WORKTREE), "-B", str(BUILD)], timeout=900)
    return r.returncode, r.stderr


def cmake_findings(stderr, rc, changed):
    out = []
    for block in re.split(r"\n(?=CMake (?:Warning|Error|Deprecation))", stderr):
        m = re.match(r"CMake (Warning|Error|Deprecation Warning)[^\n]*? at ([^:\n]+):(\d+)", block)
        if not m:
            continue
        path = os.path.relpath(m.group(2), WORKTREE) if m.group(2).startswith("/") else m.group(2)
        text = " ".join(line.strip() for line in block.splitlines()[1:] if line.strip())[:300]
        if m.group(1) == "Error" or path in changed:
            out.append({"tool": "cmake", "path": path, "line": int(m.group(3)),
                        "message": f"{m.group(1).lower()}: {text}"})
    if rc and not any(f["message"].startswith("error") for f in out):
        out.append({"tool": "cmake", "path": None, "line": None, "message": "configure failed: " + stderr[-300:]})
    return out


def compile_db():
    path = BUILD / "compile_commands.json"
    return {Path(e["file"]).resolve(): e for e in json.loads(path.read_text())} if path.exists() else {}


def syntax_command(entry):
    args, out, skip = shlex.split(entry["command"]), [], False
    for a in args:
        if skip:
            skip = False
            continue
        if a in ("-o", "-MF", "-MT", "-MQ"):
            skip = True
            continue
        if a in ("-c", "-MD", "-MMD"):
            continue
        out.append(a)
    return out + ["-fsyntax-only", "-Wall", "-Wextra", "-fno-color-diagnostics"]


DIAG = re.compile(r"^(/[^:]+):(\d+):(\d+): (warning|error): (.*)$")


def diagnostics(text):
    for line in text.splitlines():
        if (m := DIAG.match(line)):
            yield os.path.relpath(m.group(1), WORKTREE), int(m.group(2)), m.group(4), m.group(5)


def sources_for(changed, db):
    """Changed C++ sources, plus the same-named source for each changed header."""
    picks = {}
    for path in changed:
        full = (WORKTREE / path).resolve()
        if CXX.search(path) and full in db:
            picks[path] = db[full]
        elif HEADER.search(path):
            for ext in (".cxx", ".cpp"):
                cand = full.with_suffix(ext)
                if cand in db:
                    picks[path] = db[cand]
                    break
    return picks


def compile_findings(picks, changed, added):
    def one(entry):
        return run(syntax_command(entry), cwd=entry["directory"], timeout=300).stderr
    out = []
    with ThreadPoolExecutor(6) as pool:
        for text in pool.map(one, list({id(e): e for e in picks.values()}.values())):
            for path, line, kind, msg in diagnostics(text):
                if path not in changed:
                    continue
                if kind == "error" or line in added.get(path, ()):
                    out.append({"tool": "compiler", "path": path, "line": line, "message": f"{kind}: {msg}"})
    return out


def tidy_findings(picks, changed, added):
    headers = [re.escape(p) for p in changed if HEADER.search(p)]
    flt = f"--header-filter=({'|'.join(headers)})$" if headers else "--header-filter=^$"
    files = sorted({e["file"] for e in picks.values()})[:MAX_TIDY]

    def one(f):
        return run(["clang-tidy", "-p", str(BUILD), "--quiet", flt, f], cwd=str(WORKTREE), timeout=600).stdout
    out = []
    with ThreadPoolExecutor(4) as pool:
        for text in pool.map(one, files):
            for path, line, kind, msg in diagnostics(text):
                if path in changed and line in added.get(path, ()):
                    out.append({"tool": "clang-tidy", "path": path, "line": line, "message": f"{kind}: {msg}"})
    return out


def ruff_findings(changed, added):
    files = [p for p in changed if p.endswith(".py") and (WORKTREE / p).exists()]
    if not files:
        return []
    r = run(["ruff", "check", "--no-cache", "--output-format=json", "--isolated", *files], cwd=str(WORKTREE))
    out = []
    for item in json.loads(r.stdout or "[]"):
        path = os.path.relpath(item["filename"], WORKTREE)
        line = item["location"]["row"]
        if line in added.get(path, ()):
            out.append({"tool": "ruff", "path": path, "line": line, "message": f"{item['code']}: {item['message']}"})
    return out


def check(repo, base, head, hunks):
    """Findings for the lines a revision adds. hunks: review.hunks(repo, base, head) as a list."""
    added = {}
    for path, _text, _added, numbers in hunks:
        added.setdefault(path, set()).update(numbers)
    changed = set(added)
    lock = open(BUILD.parent / ".vtk-review-build.lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    try:
        start = time.time()
        checkout(repo, head)
        rc, stderr = configure()
        findings = cmake_findings(stderr, rc, changed)
        db = compile_db() if rc == 0 else {}
        picks = sources_for(changed, db)
        findings += compile_findings(picks, changed, added)
        findings += tidy_findings(picks, changed, added)
        findings += ruff_findings(changed, added)
        seen, unique = set(), []
        for f in findings:
            key = (f["tool"], f["path"], f["line"], f["message"])
            if key not in seen:
                seen.add(key)
                unique.append(f)
        check.last = {"seconds": round(time.time() - start), "compiled": len(picks), "configure_rc": rc}
        return unique
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def render(findings, limit=25):
    lines = [f"- [{f['tool']}] {f['path'] or ''}{':' + str(f['line']) if f['line'] else ''}: {f['message']}"
             for f in findings[:limit]]
    if len(findings) > limit:
        lines.append(f"- ... {len(findings) - limit} more")
    return "\n".join(lines) or "(none)"


def main():
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from review import hunks
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--base", required=True)
    p.add_argument("--head", required=True)
    args = p.parse_args()
    found = check(args.repo, args.base, args.head, list(hunks(args.repo, args.base, args.head)))
    print(check.last)
    print(render(found, limit=100))


if __name__ == "__main__":
    main()
