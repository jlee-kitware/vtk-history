#!/usr/bin/env python3
"""Estimate each rule's follow-through rate with an uncertainty interval.

The quantity is p, the chance an author changes the code when a reviewer applies the rule in a
line comment. Each rule has k acted-on comments out of n.

Model (empirical-Bayes beta-binomial, fit by maximum marginal likelihood across rules):
  p_r  ~ Beta(kappa m, kappa (1 - m))
  k_r  ~ Binomial(n_r, p_r)
The posterior for a rule is Beta(kappa m + k_r, kappa (1 - m) + n_r - k_r): a rule with few
comments stays near the average, and one with many is ruled by its own record.

The model can also set the prior mean from the rule's other evidence, m_r = logistic(x_r . w), with
x_r holding reviewers and MRs, objections, consistency, developer guide and tool agreement, and a
deprecated API ("factors" mode). None of those had a weight distinguishable from zero, and predictions
were better without them, so the estimate uses the track record alone; the other evidence is
reported beside it as verification.

validate fits on comments before each cutoff and predicts the next six months, pooling the
predictions, and compares Brier score and log loss with the points-based levels, the rule's raw
rate, and a constant.

Outcome: by default a comment counts as acted on when lines within 3 of it changed before merge.
With RULE_OUTCOME=addressed, rule comments use data/addressed_labels.jsonl instead (a model read
the later diff and judged whether it resolved the comment; rules/addressed.py), comments it could
not judge are left out, and the average is taken over rule comments.

By default each rule's evidence includes the members of rules grouped with it as duplicates
(data/rule_groups.json). RULE_POOL=matches also adds the comments rules/match_comments.py attached to
any rule in the group (data/rule_matches.json); RULE_POOL=none uses the rule's own members only.
Validation scores only the original members' later comments. Adding matches doubled the median
comments per rule but made later predictions slightly worse (Brier 0.1968 vs 0.1941 adjusted), so
they are off by default.

Usage:
  python rules/estimate.py validate
  python rules/estimate.py factors    (fit with the evidence factors and print their weights)
  python rules/estimate.py fit        (used by rules/confidence.py)
"""

import json
import math
import os
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.special import betaln, expit
from scipy.stats import beta as beta_dist

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["log reviewers", "log MRs", "objection share", "newer objection", "inconsistent",
            "guide agrees", "guide contradicts", "tool agrees", "tool contradicts", "deprecated API"]
RIDGE = 1.0
HALF_LIFE_YEARS = None
HIGH, LOW = 0.8, 0.3


def level(p_above):
    return "high" if p_above >= HIGH else "low" if p_above <= LOW else "medium"


def age_weight(date, ref, half_life):
    if not half_life or not ref:
        return 1.0
    years = (np.datetime64(ref) - np.datetime64(date)).astype(int) / 365.25
    return 0.5 ** (max(0.0, years) / half_life)


def features(rule, doc=None, tool=None, deprecated=False):
    counter = rule.get("counter_examples") or []
    share = len(counter) / (len(counter) + max(1, rule["support_threads"]))
    return np.array([
        math.log1p(len(rule["reviewers"])), math.log1p(rule["support_mrs"]), share,
        float(any(c["date"] > rule["last_seen"] for c in counter)), float(not rule.get("consistent", True)),
        float(bool(doc) and doc["verdict"] == "same"), float(bool(doc) and doc["verdict"] == "contradicts"),
        float(bool(tool) and tool["verdict"] == "same"), float(bool(tool) and tool["verdict"] == "contradicts"),
        float(deprecated)])


class Model:
    def __init__(self, w=None, log_kappa=None, mean=None, scale=None):
        self.w, self.log_kappa, self.mean, self.scale = w, log_kappa, mean, scale

    def design(self, X):
        Z = (X - self.mean) / self.scale
        return np.hstack([np.ones((len(Z), 1)), Z])

    def fit(self, X, k, n):
        self.mean = X.mean(axis=0)
        self.scale = np.where(X.std(axis=0) > 0, X.std(axis=0), 1.0)
        D = self.design(X)

        def nll(theta):
            w, kappa = theta[:-1], math.exp(theta[-1])
            m = np.clip(expit(D @ w), 1e-4, 1 - 1e-4)
            a, b = kappa * m, kappa * (1 - m)
            ll = betaln(a + k, b + n - k) - betaln(a, b)
            return -ll.sum() + RIDGE * (w[1:] ** 2).sum() / 2

        rate = k.sum() / n.sum()
        start = np.r_[math.log(rate / (1 - rate)), np.zeros(D.shape[1] - 1), math.log(10.0)]
        out = minimize(nll, start, method="L-BFGS-B", bounds=[(None, None)] * D.shape[1] + [(math.log(0.5), math.log(500))])
        self.w, self.log_kappa = out.x[:-1], out.x[-1]
        return self

    def prior(self, X):
        kappa = math.exp(self.log_kappa)
        m = expit(self.design(X) @ self.w)
        return kappa * m, kappa * (1 - m)

    def posterior(self, X, k, n):
        a, b = self.prior(X)
        return a + k, b + n - k


def load():
    sys.path.insert(0, str(ROOT / "app"))
    sys.path.insert(0, str(ROOT / "deprecations"))
    sys.path.insert(0, str(ROOT / "rules"))
    from check_rules import conflicts, load_index
    from confidence import load_doc_matches, load_tool_matches
    from data import rule_key
    rules = json.loads((ROOT / "data/rules_verified.json").read_text())["rules"]
    examples = {}
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            examples[e["discussion_id"]] = {"kind": e["kind"], "acted": bool(e.get("acted_on")), "mr": e["mr"]["iid"],
                                            "date": e["thread"][0]["created_at"][:10], "reviewer": e["reviewer"]}
    if os.environ.get("RULE_POOL", "groups") != "none":
        pool(rules, rule_key, with_matches=os.environ.get("RULE_POOL") == "matches")
    if os.environ.get("RULE_OUTCOME") == "addressed":
        apply_addressed(rules, examples)
    docs = load_doc_matches()
    tools, _ = load_tool_matches()
    by_symbol = load_index(ROOT / "data/deprecations/index.jsonl")
    extra = {rule_key(r): (docs.get(rule_key(r)), tools.get(rule_key(r)),
                           bool(conflicts(r, by_symbol, "/home/jlee/gitsync/vtk"))) for r in rules}
    return rules, examples, extra, rule_key


def pool(rules, rule_key, with_matches=False):
    """Set rule["pool"]: its members plus grouped duplicates' members and matched comments."""
    for i, r in enumerate(rules, 1):
        r.setdefault("id", f"R{i:03d}")
    byid = {r["id"]: r for r in rules}
    group = {r["id"]: {r["id"]} for r in rules}
    gpath, mpath = ROOT / "data/rule_groups.json", ROOT / "data/rule_matches.json"
    if gpath.exists():
        for g in json.loads(gpath.read_text())["groups"]:
            for rid in g:
                group[rid] = set(g)
    matches = json.loads(mpath.read_text())["matches"] if with_matches and mpath.exists() else {}
    for r in rules:
        ids = set()
        for rid in group[r["id"]]:
            ids.update(byid[rid]["members"])
            ids.update(matches.get(rule_key(byid[rid]), []))
        r["pool"] = sorted(ids)


def addressed_labels():
    out = {}
    path = ROOT / "data/addressed_labels.jsonl"
    if path.exists():
        for line in path.open():
            r = json.loads(line)
            if r.get("v") == 2:
                out[r["id"]] = r["addressed"]
    return out


def apply_addressed(rules, examples):
    """Rule comments take the diff-reading label; other line comments leave the average."""
    labels = addressed_labels()
    members = {m for r in rules for m in r["members"]}
    for m, e in examples.items():
        if e["kind"] != "line":
            continue
        if m in members and labels.get(m) in ("yes", "no"):
            e["acted"] = labels[m] == "yes"
        else:
            e["kind"] = "line-unlabeled" if m in members else "line-other"


def view(rule, examples, cutoff=None):
    """The rule as it looked before a cutoff, and its line comments (acted flags) before it."""
    members = [m for m in rule.get("pool", rule["members"]) if m in examples
               and (cutoff is None or examples[m]["date"] < cutoff)]
    if not members:
        return None, []
    reviewers = {examples[m]["reviewer"] for m in members}
    early = dict(rule, members=members, reviewers=[[r, 1] for r in reviewers],
                 support_threads=len(members), support_mrs=len({examples[m]["mr"] for m in members}),
                 last_seen=max(examples[m]["date"] for m in members),
                 counter_examples=[c for c in rule.get("counter_examples") or [] if cutoff is None or c["date"] < cutoff])
    lines = [(examples[m]["acted"], examples[m]["date"]) for m in members if examples[m]["kind"] == "line"]
    return early, lines


def fit_all(rules, examples, extra, rule_key, cutoff=None, half_life=HALF_LIFE_YEARS, ref=None, factors=False):
    ref = cutoff or ref
    rows = []
    for r in rules:
        early, lines = view(r, examples, cutoff)
        if early is None:
            continue
        doc, tool, dep = extra[rule_key(r)]
        wts = [age_weight(d, ref, half_life) for _a, d in lines]
        x = features(early, doc, tool, dep) if factors else np.zeros(1)
        rows.append((r, x, sum(w * a for w, (a, _d) in zip(wts, lines)), sum(wts)))
    X = np.array([x for _, x, _, _ in rows])
    k = np.array([a for _, _, a, _ in rows], dtype=float)
    n = np.array([b for _, _, _, b in rows], dtype=float)
    used = n > 0
    model = Model().fit(X[used], k[used], n[used])
    return model, rows, X, k, n


def scores(y, p):
    p = np.clip(np.asarray(p), 1e-6, 1 - 1e-6)
    y = np.asarray(y, dtype=float)
    return float(np.mean((p - y) ** 2)), float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def validate(half_life=HALF_LIFE_YEARS, quiet=False):
    sys.path.insert(0, str(ROOT / "rules"))
    from confidence import score
    rules, examples, extra, rule_key = load()
    cutoffs = ["2022-07-01", "2023-01-01", "2023-07-01", "2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01"]
    preds = {"constant": [], "points level": [], "raw rate": [], "estimate": []}
    ys, ests, bands, old_bands = [], [], [], []
    for i, cut in enumerate(cutoffs):
        end = cutoffs[i + 1] if i + 1 < len(cutoffs) else "2099-01-01"
        before = [e["acted"] for e in examples.values() if e["kind"] == "line" and e["date"] < cut]
        base = sum(before) / len(before)
        model, rows, X, k, n = fit_all(rules, examples, extra, rule_key, cut, half_life)
        a, b = model.posterior(X, k, n)
        level_rates, level_of, raw_n = {}, {}, {}
        for j, (r, _x, kk, nn) in enumerate(rows):
            early, _ = view(r, examples, cut)
            doc, tool, dep = extra[rule_key(r)]
            flags = {m: (examples[m]["kind"], examples[m]["acted"]) for m in early["members"]}
            raw_n[j] = sum(1 for m in early["members"] if examples[m]["kind"] == "line")
            level_of[j] = score(early, flags, base, dep, doc, tool)["level"]
            s = level_rates.setdefault(level_of[j], [0, 0])
            s[0] += kk
            s[1] += nn
        for j, (r, _x, kk, nn) in enumerate(rows):
            later = [examples[m]["acted"] for m in r["members"] if m in examples
                     and examples[m]["kind"] == "line" and cut <= examples[m]["date"] < end]
            for y in later:
                ys.append(y)
                lr = level_rates[level_of[j]]
                preds["constant"].append(base)
                preds["points level"].append(lr[0] / lr[1] if lr[1] else base)
                preds["raw rate"].append(kk / nn if raw_n[j] >= 3 else base)
                old_bands.append(level_of[j])
                preds["estimate"].append(a[j] / (a[j] + b[j]))
                bands.append(level(beta_dist.sf(base, a[j], b[j])))
                ests.append((a[j], b[j], r["id"], cut))
    if quiet:
        return scores(ys, preds["estimate"])
    print(f"{len(ys)} later line comments across {len(cutoffs)} six-month windows; acted on {np.mean(ys):.1%}\n")
    print(f"{'predictor':14} {'Brier':>7} {'log loss':>9}")
    for name, p in preds.items():
        brier, ll = scores(ys, p)
        print(f"{name:14} {brier:7.4f} {ll:9.4f}")
    print("\nLevels judged on later comments:   from the estimate      from the points")
    for lv in ("high", "medium", "low"):
        new = [y for y, b in zip(ys, bands) if b == lv]
        old = [y for y, b in zip(ys, old_bands) if b == lv]
        print(f"  {lv:7} {len(new):4} comments, acted on {np.mean(new):5.1%}    "
              f"{len(old):4} comments, acted on {np.mean(old):5.1%}")
    print("\nReliability of the estimate (predicted vs observed on later comments)")
    p = np.array(preds["estimate"])
    y = np.array(ys, dtype=float)
    for lo, hi in [(0, .55), (.55, .62), (.62, .68), (.68, .75), (.75, 1.01)]:
        sel = (p >= lo) & (p < hi)
        if sel.sum():
            print(f"  {lo:.2f}-{min(hi, 1):.2f}: {sel.sum():4} comments, predicted {p[sel].mean():.1%}, observed {y[sel].mean():.1%}")
    from scipy.stats import betabinom
    groups = {}
    for (a, b, rid, cut), yy in zip(ests, ys):
        groups.setdefault((rid, cut), [a, b, 0, 0])
        groups[(rid, cut)][2] += yy
        groups[(rid, cut)][3] += 1
    cover = [betabinom.ppf(0.05, nn, a, b) <= kk <= betabinom.ppf(0.95, nn, a, b)
             for a, b, kk, nn in groups.values() if nn >= 3]
    print(f"\nRule-windows with 3+ later comments whose acted-on count falls inside the 90% predictive "
          f"interval: {sum(cover)}/{len(cover)} ({np.mean(cover):.0%})")


def fit(boot=300, half_life=HALF_LIFE_YEARS, factors=False):
    """Fit on all data; return per-rule estimates (and, with factors, their weights with bootstrap intervals)."""
    rules, examples, extra, rule_key = load()
    today = max(e["date"] for e in examples.values())
    model, rows, X, k, n = fit_all(rules, examples, extra, rule_key, None, half_life, today, factors)
    base = np.mean([e["acted"] for e in examples.values() if e["kind"] == "line"])
    a, b = model.posterior(X, k, n)
    pa, pb = model.prior(X)
    rng = np.random.default_rng(7)
    used = np.where(n > 0)[0]
    ws = []
    for _ in range(boot if factors else 0):
        s = rng.choice(used, len(used))
        ws.append(Model().fit(X[s], k[s], n[s]).w[1:])
    ws = np.array(ws)
    weights = {f: {"weight": round(float(w), 3), "lo": round(float(np.percentile(ws[:, i], 5)), 3),
                   "hi": round(float(np.percentile(ws[:, i], 95)), 3)}
               for i, (f, w) in enumerate(zip(FEATURES, model.w[1:]))} if factors else {}
    out = {}
    for j, (r, _x, kk, nn) in enumerate(rows):
        out[rule_key(r)] = {"mean": round(float(a[j] / (a[j] + b[j])), 3),
                            "lo": round(float(beta_dist.ppf(0.05, a[j], b[j])), 3),
                            "hi": round(float(beta_dist.ppf(0.95, a[j], b[j])), 3),
                            "p_above": round(float(beta_dist.sf(base, a[j], b[j])), 3),
                            "level": level(float(beta_dist.sf(base, a[j], b[j]))),
                            "prior": round(float(pa[j] / (pa[j] + pb[j])), 3), "k": int(kk), "n": int(nn)}
    return {"baseline": round(float(base), 3), "kappa": round(math.exp(model.log_kappa), 2),
            "weights": weights, "rules": out}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if mode == "validate":
        validate()
    elif mode == "half-life":
        for hl in [None, 8, 4, 2, 1]:
            brier, ll = validate(hl, quiet=True)
            print(f"half-life {hl or 'none':>4}: Brier {brier:.4f}  log loss {ll:.4f}")
    elif mode == "factors":
        res = fit(factors=True)
        print(f"baseline {res['baseline']:.1%}, prior strength kappa {res['kappa']} (about that many comments)")
        print("factor weights on the log-odds scale, per standard deviation, with 90% bootstrap intervals:")
        for f, w in res["weights"].items():
            print(f"  {f:18} {w['weight']:+.2f}  ({w['lo']:+.2f} to {w['hi']:+.2f})")
    else:
        res = fit()
        lv = [v["level"] for v in res["rules"].values()]
        print(f"baseline {res['baseline']:.1%}, prior worth {res['kappa']} comments; "
              f"levels: high {lv.count('high')}, medium {lv.count('medium')}, low {lv.count('low')}")


if __name__ == "__main__":
    main()
