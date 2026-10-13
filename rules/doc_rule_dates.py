#!/usr/bin/env python3
"""Date each documented rule by when its quoted text reached the docs.

The date is the newest commit among the lines the quote spans (git blame), so it is never
earlier than the text itself. A quote that can't be located gets its file's newest commit date.
The benchmark uses these dates to hide doc rules written after an MR was reviewed.

Usage: python rules/doc_rule_dates.py [--repo $VTK_REPO]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DOCS = "Documentation/docs/"
STRIP = re.compile(r"[`*_\[\]()#>|]")


def norm(text):
    return " ".join(STRIP.sub(" ", text.lower()).split())


def blame(repo, commit, path):
    out = subprocess.run(["git", "-C", repo, "blame", "--line-porcelain", commit, "--", path],
                         capture_output=True, text=True, errors="replace").stdout
    lines, when = [], None
    for row in out.splitlines():
        if row.startswith("committer-time "):
            when = int(row.split()[1])
        elif row.startswith("\t"):
            lines.append((row[1:], when))
    return lines


def locate(lines, quote):
    """Indexes of the lines a quote spans, or None."""
    text, starts = "", []
    for i, (line, _) in enumerate(lines):
        starts.append((len(text), i))
        text += norm(line) + " "
    words = norm(quote).split()
    tries = [" ".join(words)] + [" ".join(words[j:j + 6]) for j in range(0, max(1, len(words) - 5), 3)]
    for t in tries:
        at = text.find(t) if len(t) > 15 else -1
        if at >= 0:
            first = max(i for s, i in starts if s <= at)
            last = max(i for s, i in starts if s <= at + len(t) - 1)
            return range(first, last + 1)
    return None


def day(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", default=config.VTK_REPO)
    p.add_argument("--rules", default="data/doc_rules.json")
    p.add_argument("--out", default="data/doc_rule_dates.json")
    args = p.parse_args()
    doc = json.loads(Path(args.rules).read_text())
    cache, dates, unplaced = {}, {}, 0
    for r in doc["rules"]:
        path = DOCS + r["file"]
        if path not in cache:
            cache[path] = blame(args.repo, doc["commit"], path)
        lines = cache[path]
        if not lines:
            dates[r["id"]] = None
            unplaced += 1
            continue
        span = locate(lines, r["quote"])
        if span is None:
            unplaced += 1
            dates[r["id"]] = day(max(w for _, w in lines))
        else:
            dates[r["id"]] = day(max(lines[i][1] for i in span))
    Path(args.out).write_text(json.dumps({"commit": doc["commit"], "dates": dates}, indent=1))
    years = {}
    for d in dates.values():
        years[d[:4] if d else "unknown"] = years.get(d[:4] if d else "unknown", 0) + 1
    print(f"{len(dates)} rules dated; {unplaced} by file date (quote not located)")
    print("by year:", dict(sorted(years.items())))


if __name__ == "__main__":
    main()
