#!/usr/bin/env python3
"""Score each verified rule's confidence from the review record.

The level comes from rules/adjusted.py: the rule's effect on follow-through (how often authors
change the code when a reviewer applies it) beyond what the reviewer and the comment's form predict,
with a 90% interval. high: at least an 80% chance the effect is positive; low: 30% or less, or the
rule contradicts a configured tool or names a deprecated API. rules/estimate.py's unadjusted rate
(empirical-Bayes beta-binomial) is kept beside it.

The factors below are reported beside the estimate as verification. Their points are kept for
comparison but no longer set the level: fit as predictors, none had a weight distinguishable
from zero (python rules/estimate.py factors).

Factors:
  breadth        distinct reviewers who asked for it
  follow-through share of its line comments the author acted on (changed lines within 3 of the comment
                 in a later commit), compared with the rate for all line comments; needs 3 or more
  objections     counter-examples as a share of support, and whether any is newer than the latest support
  consistency    whether verification found the supporting comments agree
  deprecations   a rule naming an API VTK has deprecated or removed is low regardless of the rest
  developer guide a rule the guide states gains two points; one it contradicts loses two and is flagged
                 (often the mined rule is stated too broadly rather than wrong)
  tools          a rule a tool VTK runs enforces (clang-tidy check on, clang-format setting, commit check) gains two
                 points and is marked automated, so the agent leaves it to the tool; one that contradicts an enabled
                 tool loses three; a clang-tidy check that is off but would enforce it is noted
                 (from data/tool_match.json, made by rules/tool_rules.py and rules/doc_match.py --source tool)
                 (from data/doc_match.json, made by rules/doc_rules.py and rules/doc_match.py)

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


def score(rule, examples, baseline, conflicted, doc=None, tool=None, automatable=None):
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
    points["documented"] = 0 if not doc else 2 if doc["verdict"] == "same" else -2
    points["tools"] = 0 if not tool else 2 if tool["verdict"] == "same" else -3
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
    if doc:
        parts.append(("stated in " if doc["verdict"] == "same" else "contradicts ") + f"the developer guide ({doc['file']})")
    if tool:
        parts.append(("enforced by " if tool["verdict"] == "same" else "contradicts ") + f"{tool['tool']} ({tool['check']})")
    if automatable:
        parts.append(f"clang-tidy check {automatable['check']} could enforce it (off in VTK)")
    return {"level": level, "score": total, "points": points, "reason": ", ".join(parts),
            "follow": None if follow is None else round(follow, 3), "line_comments": len(lines), "acted": acted,
            "reviewers": reviewers, "objections": len(counter), "objection_share": round(share, 3),
            "newer_objection": newer, "consistent": rule.get("consistent", True), "deprecated_api": conflicted,
            "doc": doc, "tool": tool, "automatable": automatable,
            "automated": bool(tool and tool["verdict"] == "same")}


def load_doc_matches():
    match_path, rules_path = ROOT / "data/doc_match.json", ROOT / "data/doc_rules.json"
    if not match_path.exists() or not rules_path.exists():
        return {}
    docs = {d["id"]: d for d in json.loads(rules_path.read_text())["rules"]}
    return {key: dict(m, **{k: docs[m["doc"]][k] for k in ("rule", "quote", "file", "section", "url")})
            for key, m in json.loads(match_path.read_text())["matches"].items()}


def load_tool_matches():
    match_path, rules_path = ROOT / "data/tool_match.json", ROOT / "data/tool_rules.json"
    if not match_path.exists() or not rules_path.exists():
        return {}, {}
    tools = {t["id"]: t for t in json.loads(rules_path.read_text())["rules"]}
    data = json.loads(match_path.read_text())
    pick = lambda m: dict(m, **{k: tools[m["doc"]].get(k) for k in ("tool", "check", "rule", "evidence", "url")})
    return ({key: pick(m) for key, m in data["matches"].items()},
            {key: pick(m) for key, m in (data.get("automatable") or {}).items()})


def main():
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    examples = load_examples()
    line_flags = [a for k, a in examples.values() if k == "line"]
    baseline = sum(line_flags) / len(line_flags)
    by_symbol = load_index(ROOT / "data/deprecations/index.jsonl")
    docs = load_doc_matches()
    tools, automatable = load_tool_matches()
    out = {}
    for r in rules:
        key = rule_key(r)
        out[key] = score(r, examples, baseline, bool(conflicts(r, by_symbol, "/home/jlee/gitsync/vtk")), docs.get(key),
                         tools.get(key), automatable.get(key))
    sys.path.insert(0, str(ROOT / "rules"))
    import adjusted
    import estimate
    est = estimate.fit()
    adj = adjusted.fit()
    for key, c in out.items():
        e = est["rules"].get(key)
        if not e:
            continue
        c["estimate"] = e
        a = adj["rules"].get(key)
        c["adjusted"] = a
        c["points_level"] = c["level"]
        overrides = []
        if (c.get("tool") or {}).get("verdict") == "contradicts":
            overrides.append("contradicts a configured tool")
        if c["deprecated_api"]:
            overrides.append("names a deprecated or removed API")
        c["level"] = "low" if overrides else estimate.level(a["p_above"]) if a else "medium"
        c["score"] = a["p_above"] if a else 0.5
        if a:
            head = (f"authors acted on {a['k']} of {a['n']} line comments; adjusted for reviewer and phrasing, "
                    f"{a['adjusted']:.0%} against {a['expected']:.0%} for comparable comments "
                    f"(90% range {a['lo']:.0%} to {a['hi']:.0%}), {a['p_above']:.0%} chance the rule itself helps")
        else:
            head = (f"no line comments to measure; estimate is the {e['mean']:.0%} typical for rules "
                    f"(90% range {e['lo']:.0%} to {e['hi']:.0%})")
        rest = [part for part in c["reason"].split(", ")
                if not part.startswith(("authors changed the code", "follow-through not measurable"))]
        c["reason"] = head + "".join(f"; {o}" for o in overrides) + "; " + ", ".join(rest)
    (ROOT / "data/rules_confidence.json").write_text(json.dumps(
        {"baseline_follow": round(baseline, 3), "line_comments": len(line_flags), "prior_comments": est["kappa"],
         "rules": out}, indent=1))
    levels = {lv: sum(v["level"] == lv for v in out.values()) for lv in ("high", "medium", "low")}
    levels["automated"] = sum(v["automated"] for v in out.values())
    levels["could be automated"] = sum(bool(v["automatable"]) for v in out.values())
    print(f"baseline follow-through {baseline:.1%} over {len(line_flags)} line comments; {levels}")


if __name__ == "__main__":
    main()
