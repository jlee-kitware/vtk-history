#!/usr/bin/env python3
"""Score review comments on their own merit, without needing a reviewer to have raised them.

Two signals for each comment on a benchmark MR:
  changed   the author changed lines within 3 of the comment between the revision under
            review and the MR's final revision (the same test as a reviewer comment's
            acted_on). Compared with random added lines from the same MRs, since authors
            revise code for many reasons.
  judge     a second model reads the code around the line, plus grep results for the
            identifiers the comment names, and says whether the claim is correct and
            whether a VTK maintainer would want it posted.

calibrate checks the judge on real reviewer comments that authors acted on (should pass)
and the same comments moved to a random added line of another MR (should fail).

Usage:
  python agent/judge_comments.py calibrate [--n 40]
  python agent/judge_comments.py score data/benchmark/runs-v5/before data/benchmark/runs-v5/after ...
"""

import argparse
import hashlib
import json
import random
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from review import HOST, hunks  # noqa: E402

REPO = "/home/jlee/gitsync/vtk"
MR_DIR = Path("data/vtk-history/merge_requests")
CACHE = Path("data/benchmark/judge_cache.jsonl")
WINDOW = 3
CONTEXT = 25

SYSTEM = "You are a senior VTK maintainer checking review comments. Reply with JSON only."
PROMPT = """Merge request: {title}
File: {path}

Code at the revision under review (line {line} is marked with >):
{context}

Search of the same revision for identifiers the comment names:
{grep}

Review comment on line {line}:
"{comment}"

Judge the comment against the code shown.
1. correct: is what the comment claims true of this code? "yes", "no", or "unsure" if the code shown cannot settle it.
2. worth_posting: would a VTK maintainer want this comment on the merge request, because it points at a real problem or asks for a change they would agree with? Answer false for false claims, generic advice, style preferences VTK does not enforce, or comments that do not fit the marked line.
Reply {{"correct": "yes" | "no" | "unsure", "worth_posting": true | false, "why": "<one sentence>"}}"""


def git(*args):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, errors="replace")
    return r.stdout if r.returncode == 0 else ""


def final_sha(iid, cache={}):
    if iid not in cache:
        f = MR_DIR / f"{iid}.json"
        cache[iid] = json.loads(f.read_text())["merge_request"].get("sha") if f.exists() else None
    return cache[iid]


def changed_later(iid, head, path, line):
    final = final_sha(iid)
    if final == head:
        return False
    if not final or not git("cat-file", "-t", final).strip():
        return None
    for h in re.finditer(r"^@@ -(\d+)(?:,(\d+))? ", git("diff", "-U0", head, final, "--", path), re.M):
        start, length = int(h.group(1)), int(h.group(2) if h.group(2) is not None else 1)
        lo, hi = (start, start + length - 1) if length else (start, start)
        if lo <= line + WINDOW and hi >= line - WINDOW:
            return True
    return False


def context(head, path, line):
    lines = git("show", f"{head}:{path}").splitlines()
    lo, hi = max(1, line - CONTEXT), min(len(lines), line + CONTEXT)
    return "\n".join(f"{i:6}{'>' if i == line else ' '} {lines[i - 1]}" for i in range(lo, hi + 1))


IDENT = re.compile(r"`([^`]{3,60})`|\b([A-Za-z_]\w*[A-Z_]\w*)\b")


def grep_evidence(head, comment, limit=4):
    names = []
    for m in IDENT.finditer(comment):
        name = re.sub(r"[^\w:]", "", (m.group(1) or m.group(2) or "").split("(")[0]).split("::")[-1]
        if len(name) >= 4 and name not in names:
            names.append(name)
    out = []
    for name in names[:limit]:
        rows = git("grep", "-n", "-I", "-w", "-e", name, head).splitlines()
        rows = [r.split(":", 1)[1][:200] for r in rows if ":" in r]
        out.append(f"{name}: {len(rows)} matches" + "".join(f"\n  {r}" for r in rows[:6]))
    return "\n".join(out) or "(no identifiers named)"


def ask(model, user):
    payload = {"model": model, "stream": False, "think": "medium",
               "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}],
               "options": {"temperature": 0, "num_predict": 3000, "num_ctx": 16384}}
    for _ in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            text = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
            m = re.search(r"\{.*\}", text, re.S)
            out = json.loads(m.group(0)) if m else {}
            if "worth_posting" in out:
                return out
        except (json.JSONDecodeError, KeyError, OSError) as e:
            print(f"  judge call failed ({e}); retrying", file=sys.stderr)
            time.sleep(10)
    return {"correct": "unsure", "worth_posting": None, "why": "no verdict"}


class Judge:
    def __init__(self, model):
        self.model = model
        self.cache = {}
        if CACHE.exists():
            for line in CACHE.open():
                rec = json.loads(line)
                self.cache[rec["key"]] = rec["verdict"]

    def __call__(self, title, head, path, line, comment):
        key = hashlib.sha1(json.dumps([self.model, head, path, line, comment]).encode()).hexdigest()
        if key not in self.cache:
            user = PROMPT.format(title=title, path=path, line=line, context=context(head, path, line),
                                 grep=grep_evidence(head, comment), comment=comment[:1500])
            self.cache[key] = ask(self.model, user)
            with CACHE.open("a") as f:
                f.write(json.dumps({"key": key, "verdict": self.cache[key]}) + "\n")
        return self.cache[key]


def vet(title, head, comments, model="gpt-oss:120b"):
    """Split comments into (kept, held_back) by the judge's verdict, attaching it to each.

    Comments the judge calls wrong land on lines authors later change less often than random
    lines do; comments it accepts are changed about twice as often.
    """
    judge = Judge(model)
    kept, held = [], []
    for c in comments:
        v = judge(title, head, c["path"], c["line"], c["comment"])
        c = {**c, "check": v}
        (held if v.get("correct") == "no" or v.get("worth_posting") is False else kept).append(c)
    return kept, held


def load_bench():
    return {str(b["mr"]["iid"]): b for b in map(json.loads, open("data/benchmark/benchmark.jsonl"))}


def added_lines(b):
    return [(p, n) for p, _t, _a, nums in hunks(REPO, b["base_sha"], b["head_sha"]) for n in nums]


def calibrate(args):
    bench = load_bench()
    rng = random.Random(5)
    pool = [(iid, a) for iid, b in bench.items() for a in b["answers"]
            if a["acted_on"] and a["side"] == "new" and a["severity"] in ("minor", "major")]
    pos = rng.sample(pool, min(args.n, len(pool)))
    judge = Judge(args.model)
    rows = []
    for iid, a in pos:
        b = bench[iid]
        rows.append(("real", judge(b["mr"]["title"], b["head_sha"], a["path"], int(a["line"]), a["comment"])))
        other = rng.choice([k for k in bench if k != iid])
        lines = added_lines(bench[other])
        if lines:
            p, n = rng.choice(lines)
            ob = bench[other]
            rows.append(("moved", judge(ob["mr"]["title"], ob["head_sha"], p, n, a["comment"])))
        print(f"  {len(rows)} verdicts", flush=True)
    for kind in ("real", "moved"):
        vs = [v for k, v in rows if k == kind]
        worth = sum(v.get("worth_posting") is True for v in vs)
        correct = sum(v.get("correct") == "yes" for v in vs)
        print(f"{kind:6} {len(vs)}: worth posting {worth} ({worth / len(vs):.0%}), correct {correct} ({correct / len(vs):.0%})")


def score(args):
    bench = load_bench()
    judge = Judge(args.model)
    rng = random.Random(9)
    baseline, base_rows = {}, []
    for run in args.runs:
        recs = {f.stem: json.loads(f.read_text()) for f in Path(run).glob("*.json") if f.stem.isdigit()}
        rows = []
        for iid, rec in sorted(recs.items()):
            b = bench[iid]
            answers = [(a["path"], int(a["line"])) for a in b["answers"]]
            if iid not in baseline:
                lines = added_lines(b)
                baseline[iid] = rng.sample(lines, min(5, len(lines)))
                for p, n in baseline[iid]:
                    near = any(p == ap and abs(n - al) <= WINDOW for ap, al in answers)
                    base_rows.append({"changed": changed_later(int(iid), b["head_sha"], p, n), "near_reviewer": near})
            for c in rec["predictions"]:
                near = any(c["path"] == ap and abs(c["line"] - al) <= WINDOW for ap, al in answers)
                v = judge(b["mr"]["title"], b["head_sha"], c["path"], c["line"], c["comment"])
                rows.append({"mr": iid, "path": c["path"], "line": c["line"], "comment": c["comment"],
                             "severity": c.get("severity"), "near_reviewer": near,
                             "changed": changed_later(int(iid), b["head_sha"], c["path"], c["line"]), **v})
                print(f"  {Path(run).name} !{iid}: {v.get('correct')} / {v.get('worth_posting')}", flush=True)
        (Path(run) / "merit.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False))
        report(Path(run).name, rows, len(recs))
    report("random lines", base_rows, None)


def report(name, rows, mrs):
    n = len(rows)
    pct = lambda k, sub=rows: f"{sum(r.get(k) is True for r in sub)}/{len(sub)}" if sub else "0/0"
    far = [r for r in rows if not r["near_reviewer"]]
    known = [r for r in rows if r["changed"] is not None]
    line = f"{name:14} comments {n:3}  changed later {pct('changed', known)}  (away from reviewer comments {pct('changed', [r for r in far if r['changed'] is not None])})"
    if "worth_posting" in (rows[0] if rows else {}):
        good = sum(r.get("worth_posting") is True and r.get("correct") == "yes" for r in rows)
        wrong = sum(r.get("correct") == "no" for r in rows)
        line += f"  judged correct and worth posting {good}/{n}  wrong {wrong}/{n}"
        if mrs:
            line += f"  good comments per MR {good / mrs:.2f}"
    print(line, flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["calibrate", "score"])
    p.add_argument("runs", nargs="*")
    p.add_argument("--model", default="gpt-oss:120b")
    p.add_argument("--n", type=int, default=40)
    args = p.parse_args()
    calibrate(args) if args.mode == "calibrate" else score(args)


if __name__ == "__main__":
    main()
