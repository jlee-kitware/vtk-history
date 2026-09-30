#!/usr/bin/env python3
"""Score each verified rule's confidence from the review record.

Factors:
  breadth        distinct reviewers who asked for it
  follow-through share of its line comments the author acted on (changed lines within 3 of the comment
                 in a later commit), compared with the rate for all line comments; needs 3 or more
  objections     counter-examples as a share of support, and whether any is newer than the latest support
  consistency    whether verification found the supporting comments agree
  deprecations   a rule naming an API VTK has deprecated or removed is low regardless of the rest

Writes data/rules_confidence.json keyed by rule key.

Usage:
  python rules/confidence.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "deprecations"))
from check_rules import conflicts, load_index  # noqa: E402
from data import rule_key  # noqa: E402

MIN_LINES = 3
MIN_PENALTY = 5


def load_examples():
    out = {}
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            out[e["discussion_id"]] = (e["kind"], bool(e.get("acted_on")))
    return out


def score(rule, examples, baseline, conflicted):
    lines = [examples[m] for m in rule["members"] if m in examples and examples[m][0] == "line"]
    acted = sum(a for _, a in lines)
    follow = acted / len(lines) if len(lines) >= MIN_LINES else None
    reviewers = len(rule["reviewers"])
    counter = rule.get("counter_examples") or []
    share = len(counter) / (len(counter) + rule["support_threads"])
    newer = any(c["date"] > rule["last_seen"] for c in counter)

    points = {"breadth": 2 if reviewers >= 5 else 1 if reviewers >= 3 else 0}
    if follow is None:
        points["follow"] = 1
    else:
        lift = follow - baseline
        points["follow"] = 2 if lift >= 0.1 else 1 if lift >= -0.1 else -1 if len(lines) >= MIN_PENALTY else 0
    points["objections"] = -2 if share >= 0.25 and len(counter) >= 2 else -1 if share >= 0.1 else 0
    points["newer_objection"] = -1 if newer else 0
    points["consistency"] = 0 if rule.get("consistent", True) else -1
    total = sum(points.values())
    level = "low" if conflicted or total <= 0 else "high" if total >= 3 else "medium"

    parts = [f"{rule['support_mrs']} MRs", f"{reviewers} reviewers"]
    parts.append(f"authors changed the code {follow:.0%} of the time ({acted} of {len(lines)})" if follow is not None
                 else "follow-through not measurable (general comments)")
    parts.append(f"{len(counter)} objection{'s' if len(counter) != 1 else ''}" if counter else "no objections")
    if newer:
        parts.append("an objection is newer than the latest support")
    if not rule.get("consistent", True):
        parts.append("some supporting comments differ")
    if conflicted:
        parts.append("names a deprecated or removed API")
    return {"level": level, "score": total, "points": points, "reason": ", ".join(parts),
            "follow": None if follow is None else round(follow, 3), "line_comments": len(lines), "acted": acted,
            "reviewers": reviewers, "objections": len(counter), "objection_share": round(share, 3),
            "newer_objection": newer, "consistent": rule.get("consistent", True), "deprecated_api": conflicted}


def main():
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    examples = load_examples()
    line_flags = [a for k, a in examples.values() if k == "line"]
    baseline = sum(line_flags) / len(line_flags)
    by_symbol = load_index(ROOT / "data/deprecations/index.jsonl")
    out = {}
    for r in rules:
        out[rule_key(r)] = score(r, examples, baseline, bool(conflicts(r, by_symbol, "/home/jlee/gitsync/vtk")))
    (ROOT / "data/rules_confidence.json").write_text(json.dumps(
        {"baseline_follow": round(baseline, 3), "line_comments": len(line_flags), "rules": out}, indent=1))
    levels = {lv: sum(v["level"] == lv for v in out.values()) for lv in ("high", "medium", "low")}
    print(f"baseline follow-through {baseline:.1%} over {len(line_flags)} line comments; {levels}")


if __name__ == "__main__":
    main()
