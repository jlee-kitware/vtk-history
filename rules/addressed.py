#!/usr/bin/env python3
"""Label whether the author's later changes addressed a line comment, by reading the diff.

The acted_on flag says only that lines within 3 of the comment changed before merge. Here
gpt-oss:120b reads the comment, the code the reviewer saw, and every later change to that file
before merge, and says whether the changes did what the comment asked. It does not see the
thread's replies.

check builds a reply-based check set from MR authors' first replies: "done", "fixed",
"updated" mark addressed; "prefer to keep", "separate MR", "intentional", "I disagree" mark
not addressed. It scores both acted_on and the model's label against it.

Usage:
  python rules/addressed.py check [--n 60]
  python rules/addressed.py label          (every line comment that supports a rule)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = config.VTK_REPO
HOST = config.OLLAMA_HOST
MODEL = "gpt-oss:120b"
OUT = ROOT / "data/addressed_labels.jsonl"
VERSION = 2
MAX_DIFF = 6000

POS = re.compile(r"^\s*(done|fixed|good catch|updated|addressed|changed|thanks?[,!. ]+(done|fixed|updated|changed))\b", re.I)
NEG = re.compile(r"(prefer to keep|i'?d (rather|prefer) (keep|not)|keep it as is|leave it as is|out of scope|"
                 r"(in|for) a (follow[- ]?up|separate|later|different) (mr|merge request)|"
                 r"this is (intended|intentional)|on purpose|i disagree)", re.I)

SYSTEM = "You check whether code review comments were addressed. Reply with JSON only."
PROMPT = """A reviewer commented on line {line} of {path} in a VTK merge request titled "{title}".

Reviewer's comment:
"{comment}"

Code the reviewer saw (line {line} marked with >):
{context}

All changes the author made to {path} after this comment, up to the merged version:
{diff}

Did those later changes resolve the concern the comment raised? Count it as addressed when the problem
went away, including by a different fix than the one suggested (removing the code, a cast instead of a
new format, another API). For a comment with several requests, judge its main concern. For a question,
count it as addressed only if the code changed in response. Changes elsewhere in the file that do not
touch the concern do not count.
Reply {{"addressed": "yes" | "no" | "unclear", "why": "<one sentence>"}}"""


def git(*args):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else ""


def final_sha(iid, cache={}):
    if iid not in cache:
        f = ROOT / "data/vtk-history/merge_requests" / f"{iid}.json"
        cache[iid] = json.loads(f.read_text())["merge_request"].get("sha") if f.exists() else None
    return cache[iid]


def later_diff(head, final, path, line):
    diff = git("diff", "-U4", head, final, "--", path)
    if not diff.strip():
        return "(no changes to this file after the comment)"
    hunks = re.split(r"(?m)^(?=@@ )", diff)
    near = [h for h in hunks[1:] if (m := re.match(r"@@ -(\d+)(?:,(\d+))?", h))
            and int(m.group(1)) - 40 <= line <= int(m.group(1)) + int(m.group(2) or 1) + 40]
    text = "".join(near) or "".join(hunks[1:])
    note = "" if near else "(no change within 40 lines of the comment; the whole diff of the file follows)\n"
    return note + (text[:MAX_DIFF] + "\n... (truncated)" if len(text) > MAX_DIFF else text)


def ask(user):
    payload = {"model": MODEL, "stream": False, "think": "medium",
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
               "options": {"temperature": 0, "num_predict": 3000, "num_ctx": 16384}}
    for _ in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            text = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
            m = re.search(r"\{.*\}", text, re.S)
            out = json.loads(m.group(0)) if m else {}
            if out.get("addressed") in ("yes", "no", "unclear"):
                return out
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  call failed ({e}); retrying", file=sys.stderr)
            time.sleep(10)
    return {"addressed": "unclear", "why": "no verdict"}


def cached():
    out = {}
    if OUT.exists():
        for line in OUT.open():
            r = json.loads(line)
            if r.get("v") == VERSION:
                out[r["id"]] = r
    return out


def label(e, done):
    if e["discussion_id"] in done:
        return done[e["discussion_id"]]
    code = e["code"]
    final = final_sha(e["mr"]["iid"])
    if not final or not git("cat-file", "-t", final).strip():
        rec = {"id": e["discussion_id"], "addressed": None, "why": "final revision unavailable"}
    elif final == code["head_sha"]:
        rec = {"id": e["discussion_id"], "addressed": "no", "why": "no revision after the comment"}
    else:
        user = PROMPT.format(line=code["line"], path=code["path"], title=e["mr"]["title"],
                             comment=e["thread"][0]["body"][:1500], context=code.get("context") or "",
                             diff=later_diff(code["head_sha"], final, code["path"], int(code["line"])))
        rec = {"id": e["discussion_id"], **ask(user)}
    rec["v"] = VERSION
    with OUT.open("a") as f:
        f.write(json.dumps(rec) + "\n")
    done[e["discussion_id"]] = rec
    return rec


def line_examples(ids=None):
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            if e["kind"] == "line" and e.get("acted_on") is not None and e.get("code", {}).get("side") == "new" \
                    and (ids is None or e["discussion_id"] in ids):
                yield e


def check(n):
    pos, neg = [], []
    for e in line_examples():
        final = final_sha(e["mr"]["iid"])
        if not final or final == e["code"]["head_sha"]:
            continue
        reps = [t["body"] for t in e["thread"][1:] if t["author"] == e["mr"].get("author")]
        if not reps:
            continue
        p, q = bool(POS.search(reps[0])), bool(NEG.search(reps[0]))
        if p and not q:
            pos.append(e)
        elif q and not p:
            neg.append(e)
    rng = random.Random(4)
    sample = [(e, True) for e in rng.sample(pos, min(n, len(pos)))] + [(e, False) for e in rng.sample(neg, min(n, len(neg)))]
    print(f"check set: {len(pos)} 'done/fixed' replies and {len(neg)} refusals available; using "
          f"{sum(t for _, t in sample)} and {sum(not t for _, t in sample)}", flush=True)
    done = cached()
    rows = []
    for i, (e, truth) in enumerate(sample, 1):
        rec = label(e, done)
        rows.append((truth, bool(e["acted_on"]), rec["addressed"]))
        if i % 10 == 0:
            print(f"  {i}/{len(sample)}", flush=True)
    for name, idx in (("acted_on (lines changed nearby)", 1), ("model label", 2)):
        for truth in (True, False):
            sub = [r for r in rows if r[0] == truth]
            if idx == 1:
                right = sum(r[1] == truth for r in sub)
                print(f"{name:32} on {'addressed' if truth else 'refused':9}: {right}/{len(sub)} ({right / len(sub):.0%})")
            else:
                right = sum(r[2] == ("yes" if truth else "no") for r in sub)
                unclear = sum(r[2] not in ("yes", "no") for r in sub)
                print(f"{name:32} on {'addressed' if truth else 'refused':9}: {right}/{len(sub)} ({right / len(sub):.0%}), "
                      f"{unclear} unclear")


def label_rules():
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    ids = {m for r in rules for m in r["members"]}
    todo = list(line_examples(ids))
    done = cached()
    print(f"{len(todo)} rule line comments; {sum(e['discussion_id'] in done for e in todo)} already labeled", flush=True)
    for i, e in enumerate(todo, 1):
        label(e, done)
        if i % 25 == 0:
            print(f"  {i}/{len(todo)}", flush=True)
    counts = {}
    for e in todo:
        v = done[e["discussion_id"]]["addressed"]
        counts[v] = counts.get(v, 0) + 1
    print("labels:", counts)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["check", "label"])
    p.add_argument("--n", type=int, default=60)
    args = p.parse_args()
    check(args.n) if args.mode == "check" else label_rules()


if __name__ == "__main__":
    main()
