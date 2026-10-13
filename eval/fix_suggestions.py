"""Can a model write the fix a VTK reviewer asked for? The history supplies the answer key.

Each pair is a line comment the author acted on: the file as the reviewer saw it, the comment, and the change the
author made near that line before the MR merged. The model gets the code window and the comment and returns the
revised window; it is scored against the author's change.

  build   pick pairs (no model): data/eval/fix_pairs.jsonl
  pool    earlier comment-and-fix pairs to draw examples from: data/eval/fix_history.jsonl
  run     ask a model for each fix: data/eval/fix_runs/<label>.jsonl   (--history adds similar past fixes)
  score   compare with the author's change, and ask the local judge whether the fix addresses the comment
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import difflib
import json
import random
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agent"))
REPO = config.VTK_REPO
PAIRS = ROOT / "data/eval/fix_pairs.jsonl"
RUNS = ROOT / "data/eval/fix_runs"
CONTEXT = 30
NEAR = 3
SOURCE = re.compile(r"\.(cxx|h|txx|hxx|py|cmake)$|CMakeLists\.txt$")
SUGGESTION = re.compile(r"```suggestion")


def git(*args):
    r = subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def local_hunks(head, final, path, line):
    """Hunks of head..final in path that touch lines within NEAR of line (head numbering)."""
    out = git("diff", "-U0", "--no-color", head, final, "--", path)
    if out is None:
        return None
    hunks = []
    for m in re.finditer(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*\n((?:[-+ \\].*\n?)*)", out, re.M):
        start, count = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
        lo, hi = (start, start + count - 1) if count else (start + 1, start)
        if lo - NEAR <= line <= hi + NEAR or (count == 0 and abs(start - line) <= NEAR):
            body = [l for l in m.group(5).splitlines() if l[:1] in "+-"]
            hunks.append({"start": start, "count": count,
                          "removed": [l[1:] for l in body if l[0] == "-"],
                          "added": [l[1:] for l in body if l[0] == "+"]})
    return hunks


def apply(lines, hunks):
    """Apply -U0 hunks (head numbering, 1-based) to the head file's lines."""
    out, pos = [], 1
    for h in sorted(hunks, key=lambda h: h["start"]):
        first = h["start"] if h["count"] else h["start"] + 1
        out += lines[pos - 1:first - 1]
        out += h["added"]
        pos = first + h["count"]
    return out + lines[pos - 1:]


def build(args):
    pairs = select(args.since, "9999", args.n, args.max_changed, args.seed, set())
    write(PAIRS, pairs)
    print(f"{len(pairs)} pairs from {len(pairs)} MRs since {args.since}; median lines changed "
          f"{sorted(p['changed'] for p in pairs)[len(pairs) // 2]}")


def pool(args):
    test_mrs = {p["mr"] for p in load_pairs()}
    pairs = select("2015-01-01", "9999", args.n, args.max_changed, args.seed, test_mrs, per_mr=3)
    write(ROOT / "data/eval/fix_history.jsonl", pairs)
    print(f"{len(pairs)} earlier comment-and-fix pairs, none from the test MRs")


def write(path, pairs):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")


def select(since, until, n, max_changed, seed, skip_mrs, per_mr=1):
    rng = random.Random(seed)
    candidates = defaultdict(list)
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            c = e.get("code") or {}
            body = e["thread"][0]["body"].strip()
            if (e.get("kind") != "line" or not e.get("acted_on") or c.get("side") != "new"
                    or not since <= e["thread"][0]["created_at"][:10] < until or e["mr"]["iid"] in skip_mrs
                    or not SOURCE.search(c.get("path", ""))
                    or SUGGESTION.search(body) or not 15 <= len(body) <= 700
                    or e["thread"][0]["author"] == e["mr"]["author"]):
                continue
            candidates[e["mr"]["iid"]].append(e)
    mrs = list(candidates)
    rng.shuffle(mrs)
    pairs = []
    for iid in mrs:
        taken = 0
        for e in rng.sample(candidates[iid], len(candidates[iid])):
            c = e["code"]
            text = git("show", f"{c['head_sha']}:{c['path']}")
            hunks = local_hunks(c["head_sha"], e["mr"]["sha"], c["path"], c["line"]) if text is not None else None
            if not hunks:
                continue
            changed = sum(len(h["removed"]) + len(h["added"]) for h in hunks)
            if not 1 <= changed <= max_changed:
                continue
            lines = text.split("\n")
            lo, hi = max(1, c["line"] - CONTEXT), min(len(lines), c["line"] + CONTEXT)
            if any(h["start"] < lo or h["start"] + max(h["count"], 1) - 1 > hi for h in hunks):
                continue
            after = apply(lines, hunks)
            delta = sum(len(h["added"]) - h["count"] for h in hunks)
            pairs.append({"id": e["discussion_id"], "mr": iid, "title": e["mr"]["title"], "path": c["path"],
                          "line": c["line"], "date": e["thread"][0]["created_at"][:10], "reviewer": e["reviewer"],
                          "comment": e["thread"][0]["body"].strip(), "head": c["head_sha"], "lo": lo,
                          "before": lines[lo - 1:hi], "after": after[lo - 1:hi + delta], "changed": changed})
            taken += 1
            if taken >= per_mr:
                break
        if len(pairs) >= n:
            break
    return pairs


def load_pairs():
    return [json.loads(l) for l in open(PAIRS)]


SYSTEM = ("You are a VTK developer addressing a code review comment. You get a window of a file with line numbers "
          "and the reviewer's comment on the marked line. Change the window to address the comment the way an "
          "experienced VTK maintainer would, changing nothing else. Reply in JSON: "
          '{"lines": ["<every line of the revised window, in order, without line numbers>"]}')


def numbered(p):
    return "\n".join(f"{p['lo'] + i:6}{'>' if p['lo'] + i == p['line'] else ' '} {t}"
                     for i, t in enumerate(p["before"]))


def prompt(p, examples=""):
    return (f"Merge request: {p['title']}\nFile: {p['path']}\n\n{examples}"
            f"Window (lines {p['lo']}-{p['lo'] + len(p['before']) - 1}; the comment is on the line marked >):\n"
            f"{numbered(p)}\n\nReviewer comment on line {p['line']}:\n{p['comment']}\n")


DEFINITION = re.compile(r"^(?:[A-Za-z_][\w:<>,*&\s]*?\s)?([A-Za-z_][\w]*(?:::[~\w]+)+|[A-Za-z_]\w*)\s*\([^;]*$")


def enclosing_function(p):
    """The C++ function definition the commented line sits in, found by scanning up for a definition at column 0."""
    text = git("show", f"{p['head']}:{p['path']}") or ""
    lines = text.split("\n")
    for i in range(min(p["line"], len(lines)) - 1, -1, -1):
        line = lines[i]
        if line[:1].isalpha() and not line.startswith(("return", "if", "for", "while", "else", "#")):
            m = DEFINITION.match(line)
            if m:
                return m.group(1)
    return None


def code_examples(p, _pool=None, k=3):
    """The latest earlier commits that changed the same function (else the same file), from other MRs, with
    their message and the part of their diff in that function or file."""
    import sqlite3
    con = sqlite3.connect(ROOT / "data/index/commits.sqlite")
    func = enclosing_function(p)
    found, why = [], ""
    if func:
        found = con.execute("SELECT sha, landed, subject, mr FROM commits WHERE landed < ? AND (mr IS NULL OR mr != ?) "
                            "AND json_array_length(files) <= 30 AND files LIKE ? AND functions LIKE ? ORDER BY landed DESC LIMIT ?",
                            [p["date"], p["mr"], f'%"{p["path"]}"%', f'%"{func}"%', k]).fetchall()
        why = f"function {func}"
    if not found:
        found = con.execute("SELECT sha, landed, subject, mr FROM commits WHERE landed < ? AND (mr IS NULL OR mr != ?) "
                            "AND json_array_length(files) <= 30 AND files LIKE ? ORDER BY landed DESC LIMIT ?",
                            [p["date"], p["mr"], f'%"{p["path"]}"%', k]).fetchall()
        why = f"file {p['path']}"
    if not found:
        return ""
    text = f"Earlier commits that changed this code ({why}), most recent first:\n\n"
    short = func.split("::")[-1] if func else None
    for sha, date, subject, mr in found:
        diff = git("show", "--format=", "-U2", "--no-color", sha, "--", p["path"]) or ""
        hunks = re.split(r"(?m)^(?=@@)", diff)
        keep = [h for h in hunks[1:] if short and short in h.split("\n", 1)[0] + h] or hunks[1:2]
        body = "\n".join("\n".join(keep).splitlines()[:40])
        text += f"{date} {subject}{f' (!{mr})' if mr else ''}\n{body}\n\n"
    return text


def random_examples(p, pool, k=3):
    """Earlier comment-and-fix pairs chosen at random: a control for what similar examples add."""
    rng = random.Random(p["id"])
    earlier = [e for e in pool.values() if e["date"] < p["date"] and e["mr"] != p["mr"]]
    return examples_text(rng.sample(earlier, min(k, len(earlier))))


def past_examples(p, pool, k=3):
    """Earlier comments that ask for the same kind of change (qwen3-embedding of the comment text), with the change
    the author made. Only comments made before this one, from other MRs."""
    import numpy as np
    sys.path.insert(0, str(ROOT / "index"))
    from search import Index
    if not hasattr(past_examples, "vecs"):
        idx = past_examples.idx = Index()
        past_examples.pool = list(pool.values())
        cache = ROOT / "data/eval/fix_history_emb.npy"
        if cache.exists():
            vecs = np.load(cache)
        else:
            texts = [e["comment"] for e in past_examples.pool]
            vecs = np.vstack([idx.embed(texts[i:i + 64], query=False) for i in range(0, len(texts), 64)])
            np.save(cache, vecs)
        past_examples.vecs = vecs
    pool_list = past_examples.pool
    sims = past_examples.vecs @ past_examples.idx.embed([p["comment"]])[0]
    same_dir = str(Path(p["path"]).parent)
    order = sorted(range(len(pool_list)),
                   key=lambda i: -(sims[i] + (0.03 if str(Path(pool_list[i]["path"]).parent) == same_dir else 0)))
    out = []
    for i in order:
        e = pool_list[i]
        if e["date"] < p["date"] and e["mr"] != p["mr"]:
            out.append(e)
        if len(out) >= k:
            break
    return examples_text(out)


def examples_text(out):
    if not out:
        return ""
    text = "Earlier VTK review comments like this one, and the change the author made:\n\n"
    for e in out:
        diff = "\n".join(l for l in difflib.unified_diff(e["before"], e["after"], lineterm="", n=1)
                         if not l.startswith(("---", "+++")))
        text += f"Comment: {e['comment']}\nChange in {e['path']}:\n{diff}\n\n"
    return text


def run(args):
    import llm
    pairs = load_pairs()
    history = {}
    if args.history and not args.code_history:
        history = {e["id"]: e for e in (json.loads(l) for l in open(ROOT / "data/eval/fix_history.jsonl"))}
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{args.label}.jsonl"
    done = {json.loads(l)["id"] for l in open(out)} if out.exists() else set()
    for n, p in enumerate(pairs, 1):
        if p["id"] in done:
            continue
        pick = code_examples if args.code_history else random_examples if args.random_examples else past_examples
        user = prompt(p, pick(p, history) if (args.history or args.code_history) else "")
        msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
        if llm.is_openai(args.model):
            content = llm.chat(args.model, msgs, json_mode=True, label=f"fix-{args.label}")["content"]
        else:
            from review import HOST
            import urllib.request
            payload = {"model": args.model, "stream": False, "format": "json", "messages": msgs,
                       "options": {"temperature": 0, "num_ctx": 16384, "num_predict": 4096}}
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            content = json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"]
        try:
            lines = json.loads(content)["lines"]
        except (json.JSONDecodeError, KeyError, TypeError):
            lines = None
        with open(out, "a") as f:
            f.write(json.dumps({"id": p["id"], "lines": lines}, ensure_ascii=False) + "\n")
        print(f"[{n}/{len(pairs)}] !{p['mr']} {p['path'].split('/')[-1]}:{p['line']} "
              f"{'ok' if lines is not None else 'no answer'}", flush=True)


def norm(t):
    return " ".join(t.split())


def edits(before, after):
    """The change as a set of (kind, content) items, whitespace-insensitive."""
    sm = difflib.SequenceMatcher(a=[norm(x) for x in before], b=[norm(x) for x in after], autojunk=False)
    items = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            items += [("-", i, norm(before[i])) for i in range(i1, i2)]
            items += [("+", norm(after[j])) for j in range(j1, j2)]
    return items


def f1(pred, gold):
    from collections import Counter
    p, g = Counter(pred), Counter(gold)
    hit = sum((p & g).values())
    if not p and not g:
        return 1.0
    return 2 * hit / (sum(p.values()) + sum(g.values())) if hit else 0.0


JUDGE = ("You compare two fixes for a VTK code review comment. You see the original code, the comment, the change "
         "the author actually made, and a proposed change. Reply in JSON: "
         '{"verdict": "same" | "different_but_valid" | "partial" | "wrong" | "no_change", "why": "<one sentence>"}. '
         '"same": does what the author did (formatting aside). "different_but_valid": addresses the comment '
         "correctly another way. \"partial\": addresses part of it. \"wrong\": does not address it or breaks the "
         "code. \"no_change\": leaves the code as it was.")


def judge(p, lines):
    import urllib.request
    from review import HOST
    diff = lambda b, a: "\n".join(l for l in difflib.unified_diff(b, a, lineterm="", n=2)
                                  if not l.startswith(("---", "+++"))) or "(no change)"
    user = (f"File: {p['path']}\nOriginal (numbered):\n{numbered(p)}\n\nReviewer comment on line {p['line']}:\n"
            f"{p['comment']}\n\nAuthor's change:\n{diff(p['before'], p['after'])}\n\n"
            f"Proposed change:\n{diff(p['before'], lines)}\n")
    payload = {"model": "gpt-oss:120b", "stream": False, "format": "json", "think": "medium",
               "messages": [{"role": "system", "content": JUDGE}, {"role": "user", "content": user}],
               "options": {"temperature": 0, "num_ctx": 16384}}
    req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    try:
        return json.loads(json.load(urllib.request.urlopen(req, timeout=900))["message"]["content"])
    except Exception as e:  # keep scoring if one verdict fails
        return {"verdict": "error", "why": str(e)[:100]}


def score(args):
    pairs = {p["id"]: p for p in load_pairs()}
    for label in args.labels:
        path = RUNS / f"{label}.jsonl"
        rows = [json.loads(l) for l in open(path)]
        cache = RUNS / f"{label}.scored.jsonl"
        scored = {json.loads(l)["id"]: json.loads(l) for l in open(cache)} if cache.exists() else {}
        for r in rows:
            if r["id"] in scored:
                continue
            p = pairs[r["id"]]
            lines = r["lines"] if isinstance(r["lines"], list) else p["before"]
            lines = [str(x) for x in lines]
            gold, pred = edits(p["before"], p["after"]), edits(p["before"], lines)
            s = {"id": r["id"], "f1": round(f1(pred, gold), 3),
                 "exact": [norm(x) for x in lines] == [norm(x) for x in p["after"]],
                 "changed": bool(pred), **judge(p, lines)}
            scored[r["id"]] = s
            with open(cache, "a") as f:
                f.write(json.dumps(s) + "\n")
        vals = list(scored.values())
        n = len(vals)
        from collections import Counter
        verdicts = Counter(v.get("verdict") for v in vals)
        ok = verdicts["same"] + verdicts["different_but_valid"]
        print(f"{label:28} n={n}  exact {sum(v['exact'] for v in vals)}  mean edit F1 {sum(v['f1'] for v in vals) / n:.2f}"
              f"  addresses the comment {ok}/{n} ({ok / n:.0%})  " + "  ".join(f"{k} {c}" for k, c in verdicts.most_common()))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--n", type=int, default=50)
    b.add_argument("--since", default="2023-01-01")
    b.add_argument("--max-changed", type=int, default=20)
    b.add_argument("--seed", type=int, default=7)
    o = sub.add_parser("pool")
    o.add_argument("--n", type=int, default=3000)
    o.add_argument("--max-changed", type=int, default=20)
    o.add_argument("--seed", type=int, default=7)
    r = sub.add_parser("run")
    r.add_argument("--model", default="gpt-5.4-mini")
    r.add_argument("--label")
    r.add_argument("--history", action="store_true")
    r.add_argument("--random-examples", action="store_true", help="with --history: random earlier pairs instead")
    r.add_argument("--code-history", action="store_true", help="earlier commits to the same function or file")
    s = sub.add_parser("score")
    s.add_argument("labels", nargs="+")
    args = p.parse_args()
    if args.cmd == "run":
        args.label = args.label or (args.model + ("-code" if args.code_history else "-random" if args.random_examples
                                                  else "-history" if args.history else "")).replace(":", "_")
    {"build": build, "pool": pool, "run": run, "score": score}[args.cmd](args)


if __name__ == "__main__":
    main()
