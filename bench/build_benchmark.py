#!/usr/bin/env python3
"""Build the time-split review benchmark.

For each merge request merged into the target branch on or after --cutoff, take the
first revision reviewers commented on (its base and head commits) as the agent's
input, and the line-level comments that reviewers other than the author left on that
revision as the answer key. Rules and retrieval use only history before --cutoff.

Output, one MR per line:
  mr         iid, title, url, author, merged_at
  base_sha, head_sha, diff_stat      the revision under review
  answers    reviewer, path, line, side, first comment, topic, severity, acted_on

Usage:
  python bench/build_benchmark.py --count 200
"""

import argparse
import json
import random
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


def diff_stat(repo, base, head):
    r = subprocess.run(["git", "-C", repo, "diff", "--numstat", base, head], capture_output=True, text=True)
    if r.returncode:
        return None
    files = [line.split("\t") for line in r.stdout.splitlines() if line.strip()]
    added = sum(int(a) for a, _, _ in files if a.isdigit())
    removed = sum(int(d) for _, d, _ in files if d.isdigit())
    return {"files": len(files), "added": added, "removed": removed}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--labels", default="data/review_labels.jsonl")
    p.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    p.add_argument("--cutoff", default="2026-01-01")
    p.add_argument("--target-branch", default="master")
    p.add_argument("--min-answers", type=int, default=2)
    p.add_argument("--max-files", type=int, default=40)
    p.add_argument("--count", type=int, default=200)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--out", default="data/benchmark/benchmark.jsonl")
    args = p.parse_args()

    labels = {}
    for line in open(args.labels):
        lab = json.loads(line)
        labels[lab["discussion_id"]] = lab

    by_mr = defaultdict(list)
    for line in open(args.examples):
        ex = json.loads(line)
        mr = ex["mr"]
        code = ex.get("code") or {}
        if (ex["kind"] != "line" or code.get("unavailable") or mr.get("state") != "merged"
                or (mr.get("merged_at") or "") < args.cutoff or mr.get("target_branch") != args.target_branch):
            continue
        by_mr[mr["iid"]].append(ex)

    reasons = Counter()
    candidates = []
    for iid, threads in by_mr.items():
        mr = threads[0]["mr"]
        reviewed = [t for t in threads if t["reviewer"] != mr.get("author")]
        if not reviewed:
            reasons["only author comments"] += 1
            continue
        first = min(reviewed, key=lambda t: t["thread"][0]["created_at"])
        base, head = first["code"]["base_sha"], first["code"]["head_sha"]
        answers = [t for t in reviewed if t["code"]["head_sha"] == head]
        if len(answers) < args.min_answers:
            reasons[f"fewer than {args.min_answers} comments on first revision"] += 1
            continue
        stat = diff_stat(args.repo, base, head)
        if not stat:
            reasons["revision diff unavailable"] += 1
            continue
        if stat["files"] > args.max_files:
            reasons[f"more than {args.max_files} files"] += 1
            continue
        candidates.append({
            "mr": {k: mr.get(k) for k in ("iid", "title", "web_url", "author", "merged_at")},
            "base_sha": base, "head_sha": head, "diff_stat": stat,
            "answers": [{
                "discussion_id": t["discussion_id"], "reviewer": t["reviewer"], "path": t["code"]["path"],
                "line": t["code"]["line"], "side": t["code"]["side"], "module": t["code"].get("module"),
                "comment": t["thread"][0]["body"], "created_at": t["thread"][0]["created_at"],
                "topic": labels.get(t["discussion_id"], {}).get("topic"),
                "severity": labels.get(t["discussion_id"], {}).get("severity"),
                "acted_on": t.get("acted_on"),
            } for t in sorted(answers, key=lambda t: t["thread"][0]["created_at"])],
        })

    random.Random(args.seed).shuffle(candidates)
    chosen = sorted(candidates[:args.count], key=lambda c: c["mr"]["merged_at"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as f:
        for c in chosen:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    answers = [a for c in chosen for a in c["answers"]]
    print(f"{len(by_mr)} MRs merged into {args.target_branch} since {args.cutoff} with line comments; "
          f"{len(candidates)} qualify; {len(chosen)} chosen -> {args.out}")
    print("excluded:", dict(reasons))
    print(f"answer key: {len(answers)} comments, median {sorted(len(c['answers']) for c in chosen)[len(chosen) // 2]} per MR, "
          f"{sum(1 for a in answers if a['acted_on'])} acted on")
    print("answer topics:", Counter(a["topic"] for a in answers).most_common())
    print("reviewers:", Counter(a["reviewer"] for a in answers).most_common(8))
    print("diff files, median:", sorted(c["diff_stat"]["files"] for c in chosen)[len(chosen) // 2])


if __name__ == "__main__":
    main()
