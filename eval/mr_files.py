#!/usr/bin/env python3
"""Changed files (with their VTK module) for each merge request, from the first revision reviewers
commented on. Writes data/eval/mr_files.json: {iid: [[path, module], ...]}.

Usage: python eval/mr_files.py [--since 2024-07-01]
"""

import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "/home/jlee/gitsync/vtk"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--since", default="2024-07-01")
    args = p.parse_args()
    first, module_of = {}, {}
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            code = e.get("code") or {}
            if code.get("path") and code.get("module"):
                module_of[str(Path(code["path"]).parent)] = code["module"]
            if e["kind"] != "line" or not code.get("base_sha"):
                continue
            date = e["thread"][0]["created_at"][:10]
            iid = e["mr"]["iid"]
            if date >= args.since and (iid not in first or date < first[iid][0]):
                first[iid] = (date, code["base_sha"], code["head_sha"])

    def module(path):
        d = Path(path).parent
        while str(d) not in ("", "."):
            if str(d) in module_of:
                return module_of[str(d)]
            d = d.parent
        return None
    out, added = {}, {}
    for iid, (_d, base, head) in first.items():
        r = subprocess.run(["git", "-C", REPO, "diff", "--name-only", base, head], capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            out[str(iid)] = [[p, module(p)] for p in r.stdout.split()]
            d = subprocess.run(["git", "-C", REPO, "diff", "-U0", base, head, "--", "*.cxx", "*.h", "*.txx", "*.hxx",
                                "*.cmake", "CMakeLists.txt", "*.py"], capture_output=True, text=True, errors="replace")
            lines = [ln[1:] for ln in d.stdout.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
            added[str(iid)] = "\n".join(lines)[:6000]
    (ROOT / "data/eval/mr_added.json").write_text(json.dumps(added))
    (ROOT / "data/eval").mkdir(exist_ok=True)
    (ROOT / "data/eval/mr_files.json").write_text(json.dumps(out))
    print(f"{len(out)} merge requests with changed files since {args.since}")


if __name__ == "__main__":
    main()
