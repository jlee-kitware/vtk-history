#!/usr/bin/env python3
"""Match each mined review rule against the rules VTK's documentation states (--source doc) or its tools
check (--source tool: clang-tidy checks on and off, clang-format settings, the GitLab robot's commit checks).

For every mined rule, the --candidates nearest documented rules by embedding are judged by a model as
  same         the guide states this rule (possibly more or less broadly)
  contradicts  following one breaks the other
  related      same subject, different requirement
  unrelated
The judge is checked on rules/doc_match_gold.json before the run (one miss allowed).

Writes data/doc_match.json (or data/tool_match.json): for each mined rule key, the rule it restates or
contradicts (for tools, the enabled check that enforces it and any disabled clang-tidy check that could),
and the source rules no mined rule restates.

Usage:
  python rules/doc_match.py
  python rules/doc_match.py --source tool
"""

import argparse
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
SOURCES = {"doc": ("the VTK developer guide", "Guide text"),
           "tool": ("a check VTK's tools run (clang-tidy, clang-format, or the GitLab commit checks)", "Configured by")}
PROMPT = """Compare a rule mined from VTK code review comments with {what}.

Mined rule: {mined}
Other rule: {doc}
{quote_label}: "{quote}"

Reply with JSON only: {{"verdict": "...", "why": "..."}}
  verdict  "same" if the other rule states or enforces this rule, even if one is broader or narrower;
           "contradicts" if following one would break the other;
           "related" if they concern the same subject but require different things;
           "unrelated" otherwise
  why      one short sentence"""


def embed(texts, model="qwen3-embedding:latest"):
    body = json.dumps({"model": model, "input": texts}).encode()
    req = urllib.request.Request(f"{HOST}/api/embed", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        v = np.array(json.loads(r.read())["embeddings"], dtype=np.float32)
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def judge(model, mined, doc, quote, source="doc"):
    what, label = SOURCES[source]
    reply = ask(model, PROMPT.format(what=what, quote_label=label, mined=mined, doc=doc, quote=quote))
    verdict = reply.get("verdict") if reply.get("verdict") in VERDICTS else "unrelated"
    return verdict, reply.get("why", "")


def check_gold(model):
    gold = json.loads((ROOT / "rules/doc_match_gold.json").read_text())
    misses = [g for g in gold if judge(model, g["mined"], g["doc"], g["doc"])[0] != g["verdict"]]
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
    args = ap.parse_args()
    check_gold(args.model)
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
    out = {"matches": matches, "automatable": automatable,
           "doc_only": [d["id"] for d in docs if d["id"] not in restated and d["enabled"]]}
    (ROOT / f"data/{args.source}_match.json").write_text(json.dumps(out, indent=1))
    same = sum(m["verdict"] == "same" for m in matches.values())
    print(f"{same} mined rules restate a {args.source} rule, {len(matches) - same} contradict one; "
          f"{len(automatable)} match a clang-tidy check that is off; "
          f"{len(out['doc_only'])} of {sum(d['enabled'] for d in docs)} {args.source} rules have no mined counterpart")


if __name__ == "__main__":
    main()
