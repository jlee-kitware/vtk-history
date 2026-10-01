#!/usr/bin/env python3
"""Match each mined review rule against the rules VTK's documentation states (--source doc) or its tools
check (--source tool: clang-tidy checks on and off, clang-format settings, the GitLab robot's commit checks).

For every mined rule, the --candidates nearest documented rules by embedding are judged by a model as
  same         the guide states this rule (possibly more or less broadly)
  contradicts  following one breaks the other
  related      same subject, different requirement
  unrelated
The judge is checked on rules/<source>_match_gold.json before the run (one miss allowed).

Writes data/doc_match.json (or data/tool_match.json): for each mined rule key, the rule it restates or
contradicts (for tools, the enabled check that enforces it and any disabled clang-tidy check that could),
and the source rules no mined rule restates.

Usage:
  python rules/doc_match.py
  python rules/doc_match.py --source tool
"""

import argparse
import hashlib
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
sys.path.insert(0, str(ROOT / "rules"))
from data import rule_key  # noqa: E402
from doc_rules import HOST, ask  # noqa: E402

VERDICTS = ["same", "contradicts", "related", "unrelated"]
SOURCES = {"doc": ("a rule from the VTK developer guide", "Developer guide", "Guide text", "the guide states this rule"),
           "tool": ("a check that VTK's tools run automatically", "Tool check", "Configured by",
                    "the tool check enforces this rule")}
PROMPT = """Compare a rule mined from VTK code review comments with {what}.

Mined rule: {mined}
{rule_label}: {doc}
{quote_label}: "{quote}"

Reply with JSON only: {{"verdict": "...", "why": "..."}}
  verdict  "same" if {same_when}, even if one is broader or narrower than the other;
           "contradicts" if following one would break the other;
           "related" if they concern the same subject but require different things;
           "unrelated" otherwise
  why      one short sentence"""


CONFIRM = """A rule mined from VTK code reviews was matched to a check VTK's tools run.

Mined rule: {mined}
Tool check: {check} ({tool}): {rule}

{question}
Reply with JSON only: {{"answer": "yes" or "no", "why": "one short sentence"}}"""
QUESTIONS = {
    "same": "Is finding code that breaks the mined rule the main purpose of this tool check, so that running the "
            "check would report that code? Answer no if the check targets a different or much narrower problem.",
    "contradicts": "Would code that follows the mined rule be reported or rewritten by this tool check? Answer no if "
                   "the check agrees with the mined rule or concerns something else.",
}


def safe_ask(model, prompt):
    """A request that keeps failing counts as no match rather than stopping the run."""
    try:
        return ask(model, prompt, max_tokens=200) or {}
    except Exception as e:
        print(f"  judge request failed, counted as no match: {e}", flush=True)
        return {}


def confirm(model, mined, tool, verdict):
    question = QUESTIONS["same" if verdict == "automatable" else verdict]
    reply = safe_ask(model, CONFIRM.format(mined=mined, check=tool.get("check", ""), tool=tool.get("tool", ""),
                                      rule=tool["rule"], question=question))
    return str(reply.get("answer", "")).lower().startswith("y"), reply.get("why", "")


def embed(texts, model="qwen3-embedding:latest"):
    body = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(f"{HOST}/api/embed", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        v = np.array(json.loads(r.read())["embeddings"], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def judge(model, mined, doc, quote, source="doc"):
    what, rule_label, quote_label, same_when = SOURCES[source]
    reply = safe_ask(model, PROMPT.format(what=what, rule_label=rule_label, quote_label=quote_label, same_when=same_when,
                                     mined=mined, doc=doc, quote=quote))
    verdict = reply.get("verdict") if reply.get("verdict") in VERDICTS else "unrelated"
    return verdict, reply.get("why", "")


def check_gold(model, source):
    gold = json.loads((ROOT / f"rules/{source}_match_gold.json").read_text())

    def final(g):
        verdict = judge(model, g["mined"], g["doc"], g.get("quote", g["doc"]), source)[0]
        if source == "tool" and verdict in ("same", "contradicts"):
            ok, _ = confirm(model, g["mined"], {"rule": g["doc"], "check": g.get("check", ""), "tool": g.get("tool", "")},
                            verdict)
            verdict = verdict if ok else "unrelated"
        return "unrelated" if verdict == "related" and g["verdict"] == "unrelated" else verdict

    misses = [g for g in gold if final(g) != g["verdict"]]
    for g in misses:
        print(f"gold miss: expected {g['verdict']}: {g['mined'][:60]} / {g['doc'][:60]}")
    if len(misses) > 1:
        sys.exit(f"judge missed {len(misses)} of {len(gold)} gold cases; not running")
    print(f"judge passed gold check ({len(gold) - len(misses)}/{len(gold)})", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    ap.add_argument("--candidates", type=int, default=4)
    ap.add_argument("--source", choices=list(SOURCES), default="doc")
    ap.add_argument("--force", action="store_true", help="match even if neither rule set changed")
    args = ap.parse_args()
    out_path = ROOT / f"data/{args.source}_match.json"
    inputs = hashlib.sha1((ROOT / "data/rules_verified.json").read_bytes()
                          + (ROOT / f"data/{args.source}_rules.json").read_bytes()).hexdigest()
    if not args.force and out_path.exists() and json.loads(out_path.read_text()).get("inputs") == inputs:
        print(f"rules unchanged since the last match; keeping {out_path}")
        return
    check_gold(args.model, args.source)
    mined = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    docs = json.loads((ROOT / f"data/{args.source}_rules.json").read_text())["rules"]
    for d in docs:
        d.setdefault("quote", d.get("evidence", ""))
        d.setdefault("enabled", True)
    mv = embed([f"{r['rule']} ({r.get('scope') or ''})" for r in mined])
    dv = embed([d["rule"] for d in docs])
    sims = mv @ dv.T
    jobs = [(i, int(j)) for i in range(len(mined)) for j in np.argsort(-sims[i])[:args.candidates]]
    print(f"judging {len(jobs)} pairs", flush=True)

    def run(job):
        i, j = job
        return i, j, *judge(args.model, mined[i]["rule"], docs[j]["rule"], docs[j]["quote"], args.source)

    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(run, jobs))
    if args.source == "tool":
        candidates = [r for r in results if r[2] in ("same", "contradicts")]
        print(f"confirming {len(candidates)} tool matches", flush=True)

        def check(r):
            i, j, verdict, why = r
            kind = "automatable" if verdict == "same" and not docs[j]["enabled"] else verdict
            ok, reason = confirm(args.model, mined[i]["rule"], docs[j], kind)
            return (i, j, verdict if ok else "unrelated", why if ok else reason)

        with ThreadPoolExecutor(2) as pool:
            confirmed = {(r[0], r[1]): r for r in pool.map(check, candidates)}
        results = [confirmed.get((r[0], r[1]), r) for r in results]
        print(f"{sum(r[2] in ('same', 'contradicts') for r in results)} confirmed", flush=True)
    matches, restated, automatable = {}, set(), {}
    for i, j, verdict, why in results:
        if verdict not in ("same", "contradicts"):
            continue
        key = rule_key(mined[i])
        if not docs[j]["enabled"]:
            if verdict == "same" and (key not in automatable or sims[i, j] > automatable[key]["similarity"]):
                automatable[key] = {"doc": docs[j]["id"], "why": why, "similarity": round(float(sims[i, j]), 3)}
            continue
        current = matches.get(key)
        if current is None or (verdict == "contradicts" and current["verdict"] == "same") \
                or (verdict == current["verdict"] and sims[i, j] > current["similarity"]):
            matches[key] = {"verdict": verdict, "why": why, "doc": docs[j]["id"], "similarity": round(float(sims[i, j]), 3)}
        if verdict == "same":
            restated.add(docs[j]["id"])
    out = {"inputs": inputs, "matches": matches, "automatable": automatable,
           "doc_only": [d["id"] for d in docs if d["id"] not in restated and d["enabled"]]}
    out_path.write_text(json.dumps(out, indent=1))
    same = sum(m["verdict"] == "same" for m in matches.values())
    print(f"{same} mined rules restate a {args.source} rule, {len(matches) - same} contradict one; "
          f"{len(automatable)} match a clang-tidy check that is off; "
          f"{len(out['doc_only'])} of {sum(d['enabled'] for d in docs)} {args.source} rules have no mined counterpart")


if __name__ == "__main__":
    main()
