#!/usr/bin/env python3
"""Flag review rules that mention an API VTK has since deprecated or removed.

A rule is flagged when its statement, rationale, or example evidence names a deprecated
symbol shaped like code (an internal capital or an underscore), and either the owning
class is named too, one merge request deprecated that name in two or more classes (a
project-wide change such as GetVoidPointer), or at most 3 current headers declare it
(so common methods like PrintSelf or RequestData need their class).

Writes data/deprecations/RULE_CONFLICTS.md.

Usage:
  python deprecations/check_rules.py
"""

import argparse
import functools
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

IDENT = re.compile(r"~?[A-Za-z_]\w{3,}")
CODE_SHAPED = re.compile(r"[a-z][A-Z]|_")


@functools.lru_cache(maxsize=None)
def headers_declaring(repo, symbol):
    """Headers at HEAD that mention the symbol followed by an opening parenthesis."""
    r = subprocess.run(["git", "-C", repo, "grep", "-l", "-E", rf"\b{symbol}\s*\(", "--", "*.h"],
                       capture_output=True, text=True)
    return len(r.stdout.splitlines())


def load_index(path):
    by_symbol = defaultdict(list)
    for line in open(path):
        rec = json.loads(line)
        by_symbol[rec["symbol"]].append(rec)
    return by_symbol


def conflicts(rule, by_symbol, repo):
    """Deprecation records for the APIs a rule names, oldest first, one per class, symbol, and version."""
    text = " ".join([rule.get("rule") or "", rule.get("rationale") or ""] + [e["evidence"] for e in rule["examples"]])
    idents = set(IDENT.findall(text))
    hits = []
    for sym in idents & by_symbol.keys():
        if not CODE_SHAPED.search(sym):
            continue
        recs = by_symbol[sym]
        named = [rec for rec in recs if rec["class"] in idents]
        policy = max(Counter(rec["deprecated"]["sha"] for rec in recs).values()) >= 2
        if named or policy or headers_declaring(repo, sym) <= 3:
            hits += named or recs
    seen, unique = set(), []
    for rec in sorted(hits, key=lambda x: x["deprecated"]["date"]):
        key = (rec["class"], rec["symbol"], rec["version"])
        if key not in seen:
            seen.add(key)
            unique.append(rec)
    return unique


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rules", default="data/rules_verified.json")
    p.add_argument("--index", default="data/deprecations/index.jsonl")
    p.add_argument("--out", default="data/deprecations/RULE_CONFLICTS.md")
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    args = p.parse_args()

    by_symbol = load_index(args.index)
    rules = json.loads(Path(args.rules).read_text())["rules"]
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")

    lines = ["# Rules that mention deprecated APIs", "",
             "Each entry is a draft review rule that names an API VTK later deprecated or removed. "
             "A rule whose last supporting comment predates the deprecation may recommend what VTK now discourages.", ""]
    flagged = 0
    for r in rules:
        hits = conflicts(r, by_symbol, args.repo)
        if not hits:
            continue
        flagged += 1
        lines += [f"## {r['id']}: {r['rule']}", "",
                  f"Rule evidence: {r['first_seen']} to {r['last_seen']}, {r['support_mrs']} MRs.", ""]
        for rec in hits:
            dep = rec["deprecated"]
            when = f"deprecated in {rec['version']} on {dep['date']}" + (f" by !{dep['mr']}" if dep["mr"] else "")
            if rec["removed"]:
                rem = rec["removed"]
                when += f"; {rec['outcome']} on {rem['date']}" + (f" by !{rem['mr']}" if rem["mr"] else "")
            after = " (after this rule's last evidence)" if dep["date"] > r["last_seen"] else ""
            reason = f": \"{rec['reason']}\"" if rec["reason"] else ""
            lines.append(f"- `{rec['class']}::{rec['symbol']}` {when}{after}{reason}")
        lines.append("")
    lines.insert(3, f"{flagged} of {len(rules)} rules flagged.\n")
    Path(args.out).write_text("\n".join(lines))
    print(f"{flagged} of {len(rules)} rules mention deprecated APIs -> {args.out}")


if __name__ == "__main__":
    main()
