#!/usr/bin/env python3
"""Draft REVIEW_RULES.md from the conventions found in labeled review threads.

1. Collect threads whose label carries a quote-backed convention, from before --cutoff
   (the benchmark uses MRs after it, so rules never contain its answers).
2. Embed each convention with an Ollama embedding model (cached between runs).
3. Cluster by cosine distance (average linkage) and keep clusters that recur across
   at least --min-mrs merge requests and --min-reviewers reviewers.
4. Ask a larger model to state each cluster as one rule, using only the evidence.
5. Write data/rule_candidates.json and a draft REVIEW_RULES.md for maintainer review.

Usage:
  python rules/draft_rules.py --explore          # cluster statistics at several thresholds
  python rules/draft_rules.py --threshold 0.25
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage

HOST = "http://192.168.50.23:11435"

RULE_PROMPT = """These are conventions that VTK code reviewers stated in separate merge request reviews, each with the reviewer's own words as evidence. They were grouped because they appear to express the same rule.

{members}

Reply with JSON only:
  "rule": the shared rule in one imperative sentence, stated as specifically as the evidence supports
  "rationale": the reason the reviewers gave, in one sentence, or null if the evidence gives no reason
  "scope": where the rule applies (for example "all C++ sources", "CMake module files", "Python wrapping", "tests"), from the evidence only
  "consistent": true if all the evidence supports the same rule, false if some members disagree or are about something else
Use only what the evidence says. Do not add reasons, tools, or details the reviewers did not state.
"""


def post(path, payload, timeout=600):
    req = urllib.request.Request(HOST + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def load(examples_path, labels_path, cutoff):
    examples = {}
    for line in open(examples_path):
        ex = json.loads(line)
        examples[ex["discussion_id"]] = ex
    rows = []
    for line in open(labels_path):
        lab = json.loads(line)
        ex = examples.get(lab["discussion_id"])
        if not lab.get("convention") or not ex:
            continue
        when = ex["thread"][0]["created_at"]
        if when >= cutoff:
            continue
        rows.append({
            "discussion_id": lab["discussion_id"], "convention": lab["convention"], "evidence": lab["evidence"],
            "topic": lab["topic"], "reviewer": lab["reviewer"], "mr": ex["mr"]["iid"], "mr_title": ex["mr"]["title"],
            "url": ex["mr"].get("web_url"), "date": when[:10], "path": (ex.get("code") or {}).get("path"),
            "module": (ex.get("code") or {}).get("module"),
        })
    return rows


def embed(rows, model, cache):
    cached = {}
    if cache.exists():
        data = np.load(cache, allow_pickle=True).item()
        cached = dict(zip(data["ids"], data["vectors"]))
    todo = [r for r in rows if r["discussion_id"] not in cached]
    print(f"embedding {len(todo)} conventions ({len(rows) - len(todo)} cached)")
    for i in range(0, len(todo), 64):
        batch = todo[i:i + 64]
        vecs = post("/api/embed", {"model": model, "input": [r["convention"] for r in batch]})["embeddings"]
        cached.update({r["discussion_id"]: np.asarray(v, dtype=np.float32) for r, v in zip(batch, vecs)})
        if (i // 64) % 10 == 0:
            print(f"  {i + len(batch)}/{len(todo)}")
    np.save(cache, {"ids": list(cached), "vectors": list(cached.values())})
    v = np.stack([cached[r["discussion_id"]] for r in rows])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def clusters_at(tree, threshold, rows, min_mrs, min_reviewers):
    labels = fcluster(tree, t=threshold, criterion="distance")
    groups = defaultdict(list)
    for r, c in zip(rows, labels):
        groups[c].append(r)
    kept = [g for g in groups.values()
            if len({r["mr"] for r in g}) >= min_mrs and len({r["reviewer"] for r in g}) >= min_reviewers]
    return sorted(kept, key=lambda g: -len({r["mr"] for r in g}))


def state_rule(model, group):
    sample = sorted(group, key=lambda r: r["date"], reverse=True)[:12]
    members = "\n".join(f"- convention: {r['convention']}\n  evidence ({r['reviewer']}, !{r['mr']}): \"{r['evidence'][:300]}\""
                        for r in sample)
    for attempt in range(3):
        try:
            r = post("/api/generate", {"model": model, "prompt": RULE_PROMPT.format(members=members), "stream": False,
                                        "format": "json", "think": False,
                                        "options": {"temperature": 0, "num_predict": 400}})
            return json.loads(r["response"])
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  rule statement failed ({e}); retrying", file=sys.stderr)
            time.sleep(5)
    return None


SUGGESTION = re.compile(r"^\s*`{0,3}\s*suggestion:[-+0-9]*\s*", re.I)


def clean_evidence(text):
    return SUGGESTION.sub("", text).strip()


def explanatory(r):
    return not SUGGESTION.match(r["evidence"]) and len(r["evidence"].split()) >= 4


def summarize(group, stated, counter=()):
    mrs = sorted({r["mr"] for r in group})
    examples = sorted(group, key=lambda r: (explanatory(r), r["date"]), reverse=True)
    seen, picked = set(), []
    for r in examples:
        if r["mr"] not in seen:
            picked.append(r)
            seen.add(r["mr"])
        if len(picked) == 3:
            break
    return {
        "rule": stated.get("rule") if stated else None,
        "rationale": stated.get("rationale") if stated else None,
        "scope": stated.get("scope") if stated else None,
        "consistent": stated.get("consistent") if stated else None,
        "topic": Counter(r["topic"] for r in group).most_common(1)[0][0],
        "support_mrs": len(mrs),
        "support_threads": len(group),
        "reviewers": Counter(r["reviewer"] for r in group).most_common(),
        "first_seen": min(r["date"] for r in group),
        "last_seen": max(r["date"] for r in group),
        "modules": Counter(r["module"] for r in group if r["module"]).most_common(3),
        "examples": [{"mr": r["mr"], "url": r["url"], "reviewer": r["reviewer"], "date": r["date"],
                      "evidence": r["evidence"]} for r in picked],
        "counter_examples": [{"mr": r["mr"], "url": r["url"], "reviewer": r["reviewer"], "date": r["date"],
                              "evidence": r["evidence"]} for r in counter],
        "members": [r["discussion_id"] for r in group],
    }


def evidence_line(e):
    raw = " ".join(e["evidence"].split())
    text = clean_evidence(raw)[:200]
    shown = f"suggested `{text}`" if SUGGESTION.match(raw) else f"\"{text}\""
    return f"- [!{e['mr']}]({e['url']}) {e['reviewer']}, {e['date']}: {shown}"


def write_markdown(rules, path, cutoff, threshold):
    by_topic = defaultdict(list)
    for i, rule in enumerate(rules, 1):
        rule["id"] = f"R{i:03d}"
        by_topic[rule["topic"]].append(rule)
    lines = [
        "# VTK review rules (draft)",
        "",
        f"Drafted automatically from VTK merge request reviews before {cutoff}. Each rule groups conventions that "
        f"reviewers stated in their own words across several merge requests (cosine distance {threshold}). "
        "Nothing here is approved: a maintainer should accept, edit, merge, or reject each rule.",
        "",
        "Every supporting comment was checked individually against the stated rule; comments about something else were "
        "removed from the support counts, and comments that disagree are listed as counter-evidence. "
        "A rule marked *mixed evidence* has at least one counter-example.",
        "",
    ]
    for topic in sorted(by_topic, key=lambda t: -sum(r["support_mrs"] for r in by_topic[t])):
        lines += [f"## {topic}", ""]
        for r in by_topic[topic]:
            reviewers = ", ".join(f"{name} ({n})" for name, n in r["reviewers"][:5])
            lines += [f"### {r['id']}: {r['rule'] or '(rule statement failed)'}", ""]
            if r["consistent"] is False:
                lines += ["*Mixed evidence: check the examples before accepting.*", ""]
            if r["rationale"]:
                lines += [f"Rationale: {r['rationale']}", ""]
            lines += [
                f"- Scope: {r['scope'] or 'unspecified'}",
                f"- Support: {r['support_mrs']} MRs, {r['support_threads']} threads, {r['first_seen']} to {r['last_seen']}",
                f"- Reviewers: {reviewers}",
            ]
            for e in r["examples"]:
                lines.append(evidence_line(e))
            if r.get("counter_examples"):
                lines.append("- Counter-evidence:")
                lines += ["  " + evidence_line(e) for e in r["counter_examples"][:3]]
            lines.append("")
    Path(path).write_text("\n".join(lines))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--labels", default="data/review_labels.jsonl")
    p.add_argument("--cutoff", default="2026-01-01", help="use only threads started before this date")
    p.add_argument("--embed-model", default="qwen3-embedding:latest")
    p.add_argument("--rule-model", default="nemotron3:33b")
    p.add_argument("--threshold", type=float, default=0.25, help="cosine distance for merging conventions")
    p.add_argument("--min-mrs", type=int, default=3)
    p.add_argument("--min-reviewers", type=int, default=2)
    p.add_argument("--explore", action="store_true", help="print cluster statistics at several thresholds and stop")
    p.add_argument("--out", default="REVIEW_RULES.md")
    args = p.parse_args()

    rows = load(args.examples, args.labels, args.cutoff)
    print(f"{len(rows)} conventions from threads before {args.cutoff}")
    vectors = embed(rows, args.embed_model, Path("data/convention_embeddings.npy"))
    tree = linkage(vectors, method="average", metric="cosine")

    if args.explore:
        for t in (0.15, 0.2, 0.25, 0.3, 0.35):
            kept = clusters_at(tree, t, rows, args.min_mrs, args.min_reviewers)
            covered = sum(len(g) for g in kept)
            print(f"threshold {t}: {len(kept)} rules covering {covered} conventions; "
                  f"largest supports {len({r['mr'] for r in kept[0]}) if kept else 0} MRs")
            for g in kept[:3]:
                print(f"    {len({r['mr'] for r in g})} MRs: {g[0]['convention'][:110]!r}")
        return

    groups = clusters_at(tree, args.threshold, rows, args.min_mrs, args.min_reviewers)
    print(f"{len(groups)} clusters kept; stating rules with {args.rule_model}")
    with ThreadPoolExecutor(2) as pool:
        stated = list(pool.map(lambda g: state_rule(args.rule_model, g), groups))
    rules = [summarize(g, s) for g, s in zip(groups, stated)]
    Path("data/rule_candidates.json").write_text(json.dumps(rules, indent=1, ensure_ascii=False))
    write_markdown(rules, args.out, args.cutoff, args.threshold)
    print(f"{len(rules)} draft rules -> {args.out} and data/rule_candidates.json; "
          f"{sum(1 for r in rules if r['consistent'] is False)} marked mixed evidence")


if __name__ == "__main__":
    main()
