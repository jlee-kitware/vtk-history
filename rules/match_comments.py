#!/usr/bin/env python3
"""Find more comments that apply each rule, so its follow-through rests on more evidence.

Drafting clustered the conventions reviewers stated (data/review_labels.jsonl) and kept clusters that
recurred across enough MRs and reviewers; the rest were left out of every rule. This attaches those
conventions to the rule they state:

  1. candidates   each unattached convention's nearest rule by cosine similarity to the rule's
                  centroid (the mean of its members' convention embeddings), above a cutoff set
                  from how close members sit to their own rule (leave-one-out)
  2. choice       a model reads the reviewer's words and the four nearest rules and picks the one
                  the comment applies, or none; checked first on known members with their own rule
                  among the options (should pick it) and with it removed (should pick none, or a
                  rule that merge_rules.py groups with it)

Writes data/rule_matches.json: {rule key: [discussion ids]} for confirmed matches.

Usage:
  python rules/match_comments.py explore
  python rules/match_comments.py check [--n 60]
  python rules/match_comments.py match
"""

import argparse
import json
import os
import random
import re
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
HOST = "http://192.168.50.23:11435"
MODEL = os.environ.get("MATCH_MODEL", "qwen3-coder-next:q4_K_M")
OUT = ROOT / "data/rule_matches.json"
CACHE = ROOT / "data/rule_match_cache.jsonl"

SYSTEM = "You decide whether a code review comment applies a given review rule. Reply with JSON only."
PROMPT = """VTK review rule:
"{rule}"

A reviewer's comment on a VTK merge request:
"{comment}"

The convention this comment states, in short: "{convention}"

Does the comment ask for what the rule says, in this instance? Answer yes only if acting on the comment
means following this rule. A comment on a related topic that asks for something different is no.
Reply {{"applies": true}} or {{"applies": false}}."""


def load():
    sys.path.insert(0, str(ROOT / "app"))
    from data import rule_key
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")
    cache = np.load(ROOT / "data/convention_embeddings.npy", allow_pickle=True).item()
    vec = {i: np.asarray(v, dtype=np.float32) for i, v in zip(cache["ids"], cache["vectors"])}
    vec = {i: v / np.linalg.norm(v) for i, v in vec.items()}
    labels, examples = {}, {}
    for line in open(ROOT / "data/review_labels.jsonl"):
        x = json.loads(line)
        if x.get("convention"):
            labels[x["discussion_id"]] = x
    for line in open(ROOT / "data/review_examples.jsonl"):
        e = json.loads(line)
        if e["discussion_id"] in labels:
            examples[e["discussion_id"]] = e
    return rules, rule_key, vec, labels, examples


def centroids(rules, vec, leave_out=None):
    out = []
    for r in rules:
        ms = [vec[m] for m in r["members"] if m in vec and m != leave_out]
        c = np.mean(ms, axis=0) if ms else np.zeros(next(iter(vec.values())).shape)
        out.append(c / (np.linalg.norm(c) or 1))
    return np.array(out)


def explore():
    rules, _key, vec, labels, examples = load()
    C = centroids(rules, vec)
    own, other = [], []
    for j, r in enumerate(rules):
        ms = [m for m in r["members"] if m in vec]
        for m in ms:
            if len(ms) < 2:
                continue
            c = (C[j] * len(ms) - vec[m])
            c = c / np.linalg.norm(c)
            sims = C @ vec[m]
            sims[j] = -1
            own.append(float(c @ vec[m]))
            other.append(float(sims.max()))
    members = {m for r in rules for m in r["members"]}
    free = [i for i in vec if i not in members and examples.get(i, {}).get("kind") == "line"]
    best = np.array([float((C @ vec[i]).max()) for i in free])
    print(f"members: similarity to own rule (left out) median {np.median(own):.3f}, 10th pct {np.percentile(own, 10):.3f}; "
          f"to nearest other rule median {np.median(other):.3f}, 90th pct {np.percentile(other, 90):.3f}")
    print(f"unattached line conventions: {len(free)}")
    for t in (0.55, 0.6, 0.65, 0.7, 0.75, 0.8):
        recall = np.mean(np.array(own) >= t)
        print(f"  cutoff {t:.2f}: {int((best >= t).sum()):5} candidates; members kept at this cutoff {recall:.0%}")


CHOICE = """A reviewer's comment on a VTK merge request:
"{comment}"

The convention it states, in short: "{convention}"

VTK review rules:
{options}

Which rule does the comment apply, meaning that acting on the comment is following that rule? A rule on
a related topic that asks for something different does not count. If none fits, answer 0.
Reply {{"rule": <number>}}."""


def choose(rules, e, lab):
    options = "\n".join(f"{n}. {r['rule']}" for n, r in enumerate(rules, 1))
    reasoning = "gpt-oss" in MODEL
    payload = {"model": MODEL, "stream": False, "think": "medium" if reasoning else False,
               **({} if reasoning else {"format": "json"}),
               "messages": [{"role": "user", "content": CHOICE.format(comment=e["thread"][0]["body"][:1200],
                                                                     convention=lab["convention"], options=options)}],
               "options": {"temperature": 0, "num_predict": 2000 if reasoning else 30, "num_ctx": 4096}}
    for _ in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            text = json.load(urllib.request.urlopen(req, timeout=600))["message"]["content"]
            n = int(json.loads(re.search(r"\{.*\}", text, re.S).group(0)).get("rule", 0))
            return rules[n - 1] if 1 <= n <= len(rules) else None
        except (json.JSONDecodeError, KeyError, OSError, ValueError, TypeError):
            time.sleep(5)
    return None


def groups_of(rules):
    path = ROOT / "data/rule_groups.json"
    out = {r["id"]: {r["id"]} for r in rules}
    if path.exists():
        for g in json.loads(path.read_text())["groups"]:
            for rid in g:
                out[rid] = set(g)
    return out


def check_choice(n, k=4):
    rules, _key, vec, labels, examples = load()
    C = centroids(rules, vec)
    group = groups_of(rules)
    rng = random.Random(8)
    pairs = [(j, m) for j, r in enumerate(rules) for m in r["members"] if m in vec and m in examples]
    sample = rng.sample(pairs, n)
    with_own = without_own_none = without_own_group = 0
    for j, m in sample:
        order = list(np.argsort(-(C @ vec[m])))
        opts = [rules[i] for i in ([j] + [i for i in order if i != j][:k - 1])]
        rng.shuffle(opts)
        pick = choose(opts, examples[m], labels[m])
        with_own += bool(pick) and pick["id"] in group[rules[j]["id"]]
        opts = [rules[i] for i in [i for i in order if i != j][:k]]
        pick = choose(opts, examples[m], labels[m])
        without_own_none += pick is None
        without_own_group += bool(pick) and pick["id"] in group[rules[j]["id"]]
    print(f"own rule among {k} options: picked it {with_own}/{n}")
    print(f"own rule removed: picked none {without_own_none}/{n}, picked a grouped duplicate {without_own_group}/{n}, "
          f"picked a different rule {n - without_own_none - without_own_group}/{n}")


def ask(rule, e, lab):
    payload = {"model": MODEL, "stream": False, "format": "json", "think": False,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": PROMPT.format(rule=rule, comment=e["thread"][0]["body"][:1200],
                                                                      convention=lab["convention"])}],
               "options": {"temperature": 0, "num_predict": 50, "num_ctx": 4096}}
    for _ in range(3):
        try:
            req = urllib.request.Request(HOST + "/api/chat", json.dumps(payload).encode(),
                                         {"Content-Type": "application/json"})
            out = json.loads(json.load(urllib.request.urlopen(req, timeout=300))["message"]["content"])
            return bool(out.get("applies"))
        except (json.JSONDecodeError, KeyError, OSError) as err:
            print(f"  call failed ({err}); retrying", file=sys.stderr)
            time.sleep(5)
    return None


class Judge:
    def __init__(self):
        self.done = {}
        if CACHE.exists():
            for line in CACHE.open():
                x = json.loads(line)
                self.done[(x["rule"], x["id"])] = x["applies"]

    def __call__(self, r, e, lab):
        key = (r["id"], e["discussion_id"])
        if key not in self.done:
            self.done[key] = ask(r["rule"], e, lab)
            with CACHE.open("a") as f:
                f.write(json.dumps({"rule": r["id"], "id": e["discussion_id"], "applies": self.done[key]}) + "\n")
        return self.done[key]


def check(n):
    rules, _key, vec, labels, examples = load()
    C = centroids(rules, vec)
    rng = random.Random(8)
    pairs = [(j, m) for j, r in enumerate(rules) for m in r["members"] if m in vec and m in examples]
    sample = rng.sample(pairs, n)
    judge = Judge()
    yes_own = yes_next = 0
    for j, m in sample:
        sims = C @ vec[m]
        sims[j] = -1
        k = int(sims.argmax())
        yes_own += bool(judge(rules[j], examples[m], labels[m]))
        yes_next += bool(judge(rules[k], examples[m], labels[m]))
    print(f"known members judged to apply their own rule: {yes_own}/{n}; their next-closest rule: {yes_next}/{n}")


def match(cutoff, k=4):
    """Attach each unattached line convention to the rule a model picks among its k nearest, or none."""
    rules, rule_key, vec, labels, examples = load()
    C = centroids(rules, vec)
    members = {m for r in rules for m in r["members"]}
    free = [i for i in vec if i not in members and examples.get(i, {}).get("kind") == "line"]
    picks = {}
    if CACHE.exists():
        for line in CACHE.open():
            x = json.loads(line)
            if x.get("mode") == "choice" and x.get("model") == MODEL:
                picks[x["id"]] = x["rule"]
    cands = [i for i in free if float((C @ vec[i]).max()) >= cutoff]
    print(f"{len(cands)} candidates at cutoff {cutoff}; {sum(i in picks for i in cands)} already decided", flush=True)
    byid = {r["id"]: r for r in rules}
    for n, i in enumerate(cands, 1):
        if i not in picks:
            order = list(np.argsort(-(C @ vec[i])))[:k]
            pick = choose([rules[j] for j in order], examples[i], labels[i])
            picks[i] = pick["id"] if pick else None
            with CACHE.open("a") as f:
                f.write(json.dumps({"mode": "choice", "model": MODEL, "id": i, "rule": picks[i]}) + "\n")
        if n % 50 == 0:
            print(f"  {n}/{len(cands)}; matched {sum(1 for c in cands[:n] if picks.get(c))}", flush=True)
    out = {}
    for i in cands:
        if picks.get(i):
            out.setdefault(rule_key(byid[picks[i]]), []).append(i)
    OUT.write_text(json.dumps({"cutoff": cutoff, "model": MODEL, "matches": out}, indent=1))
    total = sum(len(v) for v in out.values())
    print(f"matched {total} of {len(cands)}; rules gaining comments: {len(out)}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["explore", "check", "check-choice", "match"])
    p.add_argument("--n", type=int, default=60)
    p.add_argument("--cutoff", type=float, default=0.65)
    args = p.parse_args()
    {"explore": explore, "check": lambda: check(args.n), "check-choice": lambda: check_choice(args.n),
     "match": lambda: match(args.cutoff)}[args.mode]()


if __name__ == "__main__":
    main()
