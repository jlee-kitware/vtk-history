#!/usr/bin/env python3
"""Check each draft rule against every comment that supports it.

For each rule in data/rule_candidates.json, ask a model whether each member comment
supports the stated rule, contradicts it, or is about something else. Then:

  - unrelated comments are removed from the rule's support
  - contradicting comments are kept as counter-evidence and the rule is marked mixed
  - rules left with fewer than --min-mrs supporting MRs are dropped
  - rules that lost members are restated from the supporting comments only

Writes data/rules_verified.json and REVIEW_RULES.md.

Usage:
  python rules/verify_rules.py
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from draft_rules import load, post, state_rule, summarize, write_markdown  # noqa: E402

VERDICT_PROMPT = """You are checking whether a VTK code reviewer's comment is evidence for a draft review rule.

Rule: {rule}

Reviewer's comment: "{evidence}"

First decide what the comment asks for or says, in a few words. Then compare it with the rule:
- "supports": the comment asks for what the rule says, or complains that the rule was not followed. Agreement in a different wording still counts.
- "contradicts": the comment asks for the opposite of the rule, or argues against applying it.
- "unrelated": the comment is about a different subject.
Reply with JSON only: {{"comment_asks": "<a few words>", "verdict": "supports" | "contradicts" | "unrelated"}}
"""
MAX_MEMBERS = 40


def verdict(model, rule, member):
    prompt = VERDICT_PROMPT.format(rule=rule, evidence=" ".join(member["evidence"].split())[:600])
    for attempt in range(3):
        try:
            r = post("/api/generate", {"model": model, "prompt": prompt, "stream": False, "format": "json",
                                        "think": False, "options": {"temperature": 0, "num_predict": 80}})
            v = json.loads(r["response"]).get("verdict")
            if v in ("supports", "contradicts", "unrelated"):
                return v
        except (json.JSONDecodeError, KeyError, OSError):
            time.sleep(5)
    return "unrelated"


def check_gold(model, path):
    gold = json.loads(Path(path).read_text())
    missed = [g for g in gold if verdict(model, g["rule"], {"evidence": g["evidence"]}) != g["expected"]]
    print(f"known-answer check: {len(gold) - len(missed)}/{len(gold)} correct with {model}")
    return len(missed) <= len(gold) // 5


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gold", default="rules/verdict_gold.json", help="known-answer cases checked before the run")
    p.add_argument("--candidates", default="data/rule_candidates.json")
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--labels", default="data/review_labels.jsonl")
    p.add_argument("--cutoff", default="2026-01-01")
    p.add_argument("--check-model", default="qwen3-coder-next:q4_K_M")
    p.add_argument("--rule-model", default="qwen3-coder-next:q4_K_M")
    p.add_argument("--min-mrs", type=int, default=3)
    p.add_argument("--threshold", type=float, default=0.25, help="recorded in the markdown header")
    p.add_argument("--parallel", type=int, default=2)
    p.add_argument("--out", default="REVIEW_RULES.md")
    args = p.parse_args()

    if not check_gold(args.check_model, args.gold):
        sys.exit("The verdict model misses too many known-answer cases; fix the prompt or model before a full run.")
    candidates = json.loads(Path(args.candidates).read_text())
    rows = {r["discussion_id"]: r for r in load(args.examples, args.labels, args.cutoff)}

    jobs = [(i, rows[d]) for i, c in enumerate(candidates) if c["rule"]
            for d in c["members"][:MAX_MEMBERS] if d in rows]
    print(f"checking {len(jobs)} comments against {len(candidates)} rules with {args.check_model}")
    start = time.time()
    with ThreadPoolExecutor(args.parallel) as pool:
        verdicts = list(pool.map(lambda j: verdict(args.check_model, candidates[j[0]]["rule"], j[1]), jobs))
    print(f"  done in {time.time() - start:.0f}s")

    grouped = {}
    for (i, member), v in zip(jobs, verdicts):
        grouped.setdefault(i, {"supports": [], "contradicts": [], "unrelated": []})[v].append(member)

    kept, dropped, restate = [], [], []
    for i, c in enumerate(candidates):
        g = grouped.get(i)
        if not g or len({m["mr"] for m in g["supports"]}) < args.min_mrs:
            dropped.append(c)
            continue
        kept.append((c, g))
        if g["contradicts"] or g["unrelated"]:
            restate.append(len(kept) - 1)

    print(f"{len(kept)} rules kept, {len(dropped)} dropped for too little support; restating {len(restate)}")
    with ThreadPoolExecutor(args.parallel) as pool:
        restated = dict(zip(restate, pool.map(lambda k: state_rule(args.rule_model, kept[k][1]["supports"]), restate)))

    rules = []
    for k, (c, g) in enumerate(kept):
        stated = restated.get(k) or {key: c[key] for key in ("rule", "rationale", "scope", "consistent")}
        rule = summarize(g["supports"], stated, counter=g["contradicts"])
        rule["consistent"] = not g["contradicts"]
        rule["removed_unrelated"] = len(g["unrelated"])
        rules.append(rule)
    rules.sort(key=lambda r: -r["support_mrs"])

    write_markdown(rules, args.out, args.cutoff, args.threshold)
    Path("data/rules_verified.json").write_text(json.dumps(
        {"rules": rules, "dropped": [c["rule"] for c in dropped]}, indent=1, ensure_ascii=False))
    counts = {v: verdicts.count(v) for v in ("supports", "contradicts", "unrelated")}
    print(f"verdicts: {counts}")
    print(f"{len(rules)} rules -> {args.out}; {sum(1 for r in rules if not r['consistent'])} with counter-evidence; "
          f"{len(dropped)} dropped")


if __name__ == "__main__":
    main()
