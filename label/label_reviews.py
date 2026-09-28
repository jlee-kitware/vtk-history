#!/usr/bin/env python3
"""Label review threads with a local model served by Ollama.

For each thread in review_examples.jsonl (approvals skipped), asks the model for:

  topic        one of TOPICS
  convention   a general rule the thread itself states, in one sentence, or null.
               Kept only when the model's quoted evidence appears in the thread.
  evidence     the thread's own words stating the convention
  severity     nit, minor, or major
  summary      what the reviewer asked for, in one line

Labels are appended to the output file as they finish, so an interrupted run resumes
where it stopped.

Usage:
  python label/label_reviews.py --examples data/review_examples.jsonl --out data/review_labels.jsonl
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

TOPICS = [
    "style", "naming", "api-usage", "memory-ownership", "threading-smp", "python-wrapping",
    "testing", "build-cmake", "docs-release-notes", "design-architecture", "correctness",
    "performance", "compiler-warnings", "deprecation-abi", "process-ci", "other",
]
SEVERITIES = ["nit", "minor", "major"]

PROMPT = """You are labeling code review comments from the VTK project (C++ with Python wrapping, built with CMake).

Reply with JSON only, with these keys:
  "topic": one of {topics}
  "convention": a general VTK rule or practice that the thread itself states or directly asks for, in one sentence; null if the thread does not state one. Use only what the reviewers wrote. Do not supply reasons, rules, or tools they did not mention. Most short comments have no convention.
  "evidence": the exact words from the review thread that state the convention, copied verbatim; null when convention is null
  "severity": one of {severities} ("nit" for cosmetic, "major" for bugs, API breaks, or design problems)
  "summary": what the reviewer asked for, in one line, using only what the thread says

{location}{code}Review thread:
{thread}
"""

MAX_CODE_CHARS, MAX_NOTE_CHARS, MAX_NOTES = 2500, 1200, 4


def prompt_for(ex):
    code = ex.get("code") or {}
    location = f"Merge request: !{ex['mr']['iid']} {ex['mr']['title']}\n"
    if code.get("path"):
        location += f"File: {code['path']} line {code.get('line')}\n"
    if code.get("module"):
        location += f"Module: {code['module']}\n"
    if code.get("class"):
        location += f"Class: {code['class']} (derives from {' > '.join(code.get('ancestors') or []) or 'nothing'})\n"
    source = code.get("hunk") or code.get("context") or ""
    code_block = f"Code the reviewer saw:\n{source[:MAX_CODE_CHARS]}\n\n" if source else "\n"
    notes = ex["thread"][:MAX_NOTES]
    thread = "\n".join(f"[{n['author']}{' (MR author)' if n['author'] == ex['mr'].get('author') else ''}] "
                       f"{n['body'][:MAX_NOTE_CHARS]}" for n in notes)
    thread = thread or "(empty)"
    return PROMPT.format(topics=TOPICS, severities=SEVERITIES, location=location, code=code_block, thread=thread)


def squash(text):
    return re.sub(r"\W+", " ", text).strip().lower()


def normalize(raw, thread_text):
    label = json.loads(raw)
    topic = label.get("topic") if label.get("topic") in TOPICS else "other"
    severity = label.get("severity") if label.get("severity") in SEVERITIES else "minor"
    convention, evidence = label.get("convention"), label.get("evidence")
    if not isinstance(convention, str) or convention.strip().lower() in ("", "null", "none"):
        convention = None
    if not isinstance(evidence, str) or len(squash(evidence)) < 4 or squash(evidence) not in squash(thread_text):
        convention = evidence = None
    return {"topic": topic, "convention": convention, "evidence": evidence if convention else None,
            "severity": severity, "summary": str(label.get("summary") or "").strip()}


def label_one(url, model, ex, retries=3):
    body = json.dumps({"model": model, "prompt": prompt_for(ex), "stream": False, "format": "json",
                       "think": False, "options": {"temperature": 0, "num_predict": 300}}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, body, {"Content-Type": "application/json"})
            r = json.load(urllib.request.urlopen(req, timeout=300))
            return normalize(r["response"], "\n".join(n["body"] for n in ex["thread"]))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as e:
            if attempt == retries - 1:
                print(f"  failed {ex['discussion_id']}: {e}", file=sys.stderr)
                return None
            time.sleep(5 * (attempt + 1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--out", default="data/review_labels.jsonl")
    p.add_argument("--host", default="http://192.168.50.23:11435")
    p.add_argument("--model", default="nemotron-3.5-lightning:latest")
    p.add_argument("--parallel", type=int, default=2, help="requests in flight; match OLLAMA_NUM_PARALLEL")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    out = Path(args.out)
    done = set()
    if out.exists():
        done = {json.loads(l)["discussion_id"] for l in out.open() if l.strip()}

    todo = []
    for line in open(args.examples):
        ex = json.loads(line)
        if ex["kind"] != "approval" and ex["discussion_id"] not in done:
            todo.append(ex)
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(done)} already labeled, {len(todo)} to label with {args.model} ({args.parallel} in flight)")

    url = args.host.rstrip("/") + "/api/generate"
    start, n, failed = time.time(), 0, 0
    with out.open("a") as f, ThreadPoolExecutor(args.parallel) as pool:
        futures = {pool.submit(label_one, url, args.model, ex): ex for ex in todo}
        for fut in as_completed(futures):
            ex, label = futures[fut], fut.result()
            if label is None:
                failed += 1
                continue
            f.write(json.dumps({"discussion_id": ex["discussion_id"], "mr_iid": ex["mr"]["iid"],
                                "kind": ex["kind"], "reviewer": ex["reviewer"], "model": args.model,
                                **label}, ensure_ascii=False) + "\n")
            f.flush()
            n += 1
            if n % 100 == 0:
                rate = n / (time.time() - start)
                print(f"  {n}/{len(todo)} labeled, {rate:.2f}/s, about {(len(todo) - n) / rate / 60:.0f} min left")
    print(f"labeled {n}, failed {failed}, {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
