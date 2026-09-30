#!/usr/bin/env python3
"""Score the reviewer on the time-split benchmark.

For each benchmark MR, the reviewer sees the first revision reviewers commented on and
only history from before the first review comment. Rules whose support includes any
benchmark MR lose those threads, and rules left with fewer than 3 supporting MRs are
withheld, so no rule carries an answer.

Each real reviewer comment (answer) and each predicted comment is matched at two levels:
  location   same file, within --window lines
  content    a judge model says the two comments raise the same concern

Reported: recall (answers found), precision (predictions that match an answer), and
comments per MR. Predictions are cached per MR, so an interrupted run resumes.

Usage:
  python agent/evaluate.py --limit 20
  python agent/evaluate.py --limit 20 --model gpt-oss:120b
"""

import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review import Reviewer, load_rules, chat  # noqa: E402

JUDGE_SYSTEM = "You compare code review comments. Reply with JSON only."
JUDGE_USER = """Two review comments on the same place in a VTK merge request.

Reviewer's comment:
"{answer}"

Predicted comment:
"{prediction}"

Do they raise the same specific concern, so that making the change one asks for would also resolve the other? Comments about different problems are not the same concern, even when they are on the same lines or both mention the same code. A predicted comment that argues against what the reviewer asked is not the same concern. A predicted comment that asks for the same change in different words, or asks for part of it, is the same concern.
Reply {{"same": true}} or {{"same": false}}."""
GOLD = Path(__file__).resolve().parent / "judge_gold.json"


def safe_rules(rules_path, examples_path, benchmark_iids, min_mrs=3):
    mr_of = {}
    for line in open(examples_path):
        ex = json.loads(line)
        mr_of[ex["discussion_id"]] = ex["mr"]["iid"]
    kept = []
    for r in load_rules(rules_path):
        mrs = {mr_of.get(m) for m in r["members"]} - {None}
        if len(mrs - benchmark_iids) >= min_mrs:
            kept.append(r)
    return kept


def same_concern(judge, answer, prediction):
    out = chat(judge, JUDGE_SYSTEM, JUDGE_USER.format(answer=answer[:1200], prediction=prediction[:1200]), num_ctx=4096)
    return bool(out.get("same"))


def check_judge(judge, max_misses=1):
    gold = json.loads(GOLD.read_text())
    misses = [g for g in gold if same_concern(judge, g["answer"], g["prediction"]) != g["same"]]
    print(f"judge {judge}: {len(gold) - len(misses)}/{len(gold)} known cases correct", flush=True)
    for g in misses:
        print(f"  missed ({g['source']}, expected {g['same']}): {g['prediction'][:100]}", flush=True)
    if len(misses) > max_misses:
        sys.exit("judge is not reliable enough; scores would be misleading")


def score(mr, predictions, judge, window):
    answers = mr["answers"]
    near = lambda a, p: a["path"] == p["path"] and abs(int(a["line"]) - int(p["line"])) <= window
    result = {"answers": [], "predictions": [{"located": False, "matched": False} for _ in predictions]}
    for a in answers:
        cands = [i for i, p in enumerate(predictions) if near(a, p)]
        matched = [i for i in cands if same_concern(judge, a["comment"], predictions[i]["comment"])]
        for i in cands:
            result["predictions"][i]["located"] = True
        for i in matched:
            result["predictions"][i]["matched"] = True
        result["answers"].append({"located": bool(cands), "matched": bool(matched), "acted_on": a["acted_on"],
                                  "severity": a["severity"], "topic": a["topic"]})
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--benchmark", default="data/benchmark/benchmark.jsonl")
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--rules", default="data/rules_verified.json")
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    p.add_argument("--judge", default="qwen3-coder-next:q4_K_M")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--window", type=int, default=5)
    p.add_argument("--out", default="data/benchmark/runs")
    args = p.parse_args()

    bench = [json.loads(line) for line in open(args.benchmark)]
    iids = {b["mr"]["iid"] for b in bench}
    if args.limit:
        bench = random.Random(args.seed).sample(bench, args.limit)
    rules = safe_rules(args.rules, args.examples, iids)
    print(f"{len(bench)} MRs; {len(rules)} rules usable without benchmark evidence", flush=True)
    check_judge(args.judge)

    out = Path(args.out) / args.model.replace(":", "_").replace("/", "_")
    out.mkdir(parents=True, exist_ok=True)
    reviewer = Reviewer(args.repo, args.model, rules=rules)
    totals = defaultdict(Counter)
    for n, mr in enumerate(bench, 1):
        iid = mr["mr"]["iid"]
        cache = out / f"{iid}.json"
        if cache.exists():
            record = json.loads(cache.read_text())
        else:
            until = min(a["created_at"] for a in mr["answers"])[:10]
            start = time.time()
            predictions, hunks, drafted = reviewer.review(mr["base_sha"], mr["head_sha"], mr["mr"]["title"], until,
                                                          exclude_ref=f"!{iid}")
            record = {"mr": mr["mr"], "until": until, "hunks": hunks, "drafted": drafted,
                      "seconds": round(time.time() - start), "predictions": predictions}
            record["score"] = score(mr, predictions, args.judge, args.window)
            cache.write_text(json.dumps(record, indent=1, ensure_ascii=False))
        s = record["score"]
        t = totals["all"]
        t["mrs"] += 1
        t["answers"] += len(s["answers"])
        t["answers_located"] += sum(a["located"] for a in s["answers"])
        t["answers_matched"] += sum(a["matched"] for a in s["answers"])
        t["acted"] += sum(bool(a["acted_on"]) for a in s["answers"])
        t["acted_matched"] += sum(a["matched"] and bool(a["acted_on"]) for a in s["answers"])
        t["predictions"] += len(s["predictions"])
        t["predictions_located"] += sum(x["located"] for x in s["predictions"])
        t["predictions_matched"] += sum(x["matched"] for x in s["predictions"])
        t["seconds"] += record["seconds"]
        for a in s["answers"]:
            totals["topic_answers"][a["topic"]] += 1
            totals["topic_matched"][a["topic"]] += a["matched"]
        print(f"[{n}/{len(bench)}] !{iid}: {len(record['predictions'])} comments on {record['hunks']} hunks in "
              f"{record['seconds']}s; answers matched {sum(a['matched'] for a in s['answers'])}/{len(s['answers'])}",
              flush=True)

    t = totals["all"]
    ratio = lambda a, b: round(a / b, 3) if b else None
    report = {
        "model": args.model, "judge": args.judge, "mrs": t["mrs"], "rules": len(rules),
        "recall_location": ratio(t["answers_located"], t["answers"]),
        "recall_content": ratio(t["answers_matched"], t["answers"]),
        "recall_content_acted_on": ratio(t["acted_matched"], t["acted"]),
        "precision_location": ratio(t["predictions_located"], t["predictions"]),
        "precision_content": ratio(t["predictions_matched"], t["predictions"]),
        "comments_per_mr": ratio(t["predictions"], t["mrs"]), "answers_per_mr": ratio(t["answers"], t["mrs"]),
        "minutes_per_mr": ratio(t["seconds"] / 60, t["mrs"]),
        "recall_by_topic": {k: f"{totals['topic_matched'][k]}/{v}" for k, v in totals["topic_answers"].most_common()},
    }
    (out / "report.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
