#!/usr/bin/env python3
"""Rule follow-through adjusted for who commented and how.

Stage 1, a comment model fit on every line comment (rule or not):
  logit q_c = b0 + reviewer_c + w . z_c
  z_c: GitLab suggestion block, a question, log length, severity label (nit / minor / major),
       the reviewer is the MR author, inline code in the comment
  Reviewer effects are ridge-penalized, so reviewers with few comments sit near the average.
Stage 2, a rule effect on top of that offset:
  logit p_c = logit q_c + u_r,   u_r ~ Normal(0, tau^2)
u_r is the rule's own pull: positive when authors act on it more often than on comparable
comments from the same reviewers. Each u_r is a MAP estimate with a Laplace 90% interval and
P(u_r > 0). tau is chosen by rolling validation.

Only facts known when the comment is written enter the model (no replies, resolution, or MR outcome).

Usage:
  python rules/adjusted.py validate
  python rules/adjusted.py fit
"""

import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import norm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "rules"))
import estimate  # noqa: E402

REVIEWER_RIDGE = 20.0
USE_AUTHORS = False
COMMENT_FEATURES = ["suggestion block", "question", "log length", "minor", "major", "self review", "inline code"]
TAUS = [0.25, 0.5, 0.75, 1.0, 1.5]
TAU = 0.75


def load_comments():
    labels = {}
    with open(ROOT / "data/review_labels.jsonl") as f:
        for line in f:
            lab = json.loads(line)
            labels[lab.get("discussion_id")] = lab.get("severity")
    rows = []
    with open(ROOT / "data/review_examples.jsonl") as f:
        for line in f:
            e = json.loads(line)
            if e["kind"] != "line" or e.get("acted_on") is None:
                continue
            body = e["thread"][0]["body"]
            sev = labels.get(e["discussion_id"])
            rows.append({"id": e["discussion_id"], "date": e["thread"][0]["created_at"][:10],
                         "reviewer": e["reviewer"], "author": e["mr"].get("author"), "y": float(bool(e["acted_on"])),
                         "z": [float("```suggestion" in body), float("?" in body), math.log1p(len(body)),
                               float(sev == "minor"), float(sev == "major"),
                               float(e["reviewer"] == e["mr"].get("author")), float(bool(re.search(r"`[^`]+`", body)))]})
    return rows


class CommentModel:
    def fit(self, rows):
        self.reviewers = {r: i for i, r in enumerate(sorted({c["reviewer"] for c in rows}))}
        if USE_AUTHORS:
            n = len(self.reviewers)
            self.reviewers.update({"author:" + a: n + i for i, a in enumerate(sorted({c["author"] for c in rows}))})
        Z = np.array([c["z"] for c in rows])
        self.mu, self.sd = Z.mean(0), np.where(Z.std(0) > 0, Z.std(0), 1)
        X = self._design(rows)
        y = np.array([c["y"] for c in rows])
        nz, nr = len(COMMENT_FEATURES), len(self.reviewers)

        def loss(w):
            eta = X @ w
            ll = y * eta - np.logaddexp(0, eta)
            pen = REVIEWER_RIDGE * (w[1 + nz:] ** 2).sum() / 2 + 0.5 * (w[1:1 + nz] ** 2).sum() / 2
            grad = -(X.T @ (y - expit(eta)))
            grad[1 + nz:] += REVIEWER_RIDGE * w[1 + nz:]
            grad[1:1 + nz] += 0.5 * w[1:1 + nz]
            return -ll.sum() + pen, grad

        w0 = np.zeros(1 + nz + nr)
        w0[0] = math.log(y.mean() / (1 - y.mean()))
        self.w = minimize(loss, w0, jac=True, method="L-BFGS-B").x
        return self

    def _design(self, rows):
        nz = len(COMMENT_FEATURES)
        Z = (np.array([c["z"] for c in rows]) - self.mu) / self.sd
        pairs = [(i, self.reviewers.get(c["reviewer"])) for i, c in enumerate(rows)]
        if USE_AUTHORS:
            pairs += [(i, self.reviewers.get("author:" + str(c["author"]))) for i, c in enumerate(rows)]
        pairs = [(i, j) for i, j in pairs if j is not None]
        R = sparse.csr_matrix((np.ones(len(pairs)), ([i for i, _ in pairs], [j for _, j in pairs])),
                              shape=(len(rows), len(self.reviewers)))
        return sparse.hstack([sparse.csr_matrix(np.ones((len(rows), 1))), sparse.csr_matrix(Z), R]).tocsr()

    def offset(self, rows):
        return self._design(rows) @ self.w


def rule_effect(y, off, tau):
    """MAP of u for logit p = off + u with u ~ N(0, tau^2); returns (u, sd)."""
    u = 0.0
    for _ in range(30):
        p = expit(off + u)
        g = (y - p).sum() - u / tau ** 2
        h = -(p * (1 - p)).sum() - 1 / tau ** 2
        step = g / h
        u -= step
        if abs(step) < 1e-8:
            break
    p = expit(off + u)
    return u, 1 / math.sqrt((p * (1 - p)).sum() + 1 / tau ** 2)


def rule_members(rules, line_ids):
    return {r["id"]: [m for m in r["members"] if m in line_ids] for r in rules}


def validate(taus=TAUS):
    rules, examples, extra, rule_key = estimate.load()
    comments = load_comments()
    by_id = {c["id"]: c for c in comments}
    members = rule_members(rules, by_id)
    cutoffs = ["2022-07-01", "2023-01-01", "2023-07-01", "2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01"]
    out = {"rule only (current)": [], "comment model only": []}
    out.update({f"comment model + rule, tau {t}": [] for t in taus})
    ys, groups, bands, expected = [], [], [], []
    for i, cut in enumerate(cutoffs):
        end = cutoffs[i + 1] if i + 1 < len(cutoffs) else "2099-01-01"
        train = [c for c in comments if c["date"] < cut]
        cm = CommentModel().fit(train)
        model, rows, X, k, n = estimate.fit_all(rules, examples, extra, rule_key, cut)
        a, b = model.posterior(X, k, n)
        prior_mean = {r["id"]: a[j] / (a[j] + b[j]) for j, (r, *_rest) in enumerate(rows)}
        for r in rules:
            early = [by_id[m] for m in members[r["id"]] if by_id[m]["date"] < cut]
            later = [by_id[m] for m in members[r["id"]] if cut <= by_id[m]["date"] < end]
            if not later:
                continue
            y_e = np.array([c["y"] for c in early])
            off_e = cm.offset(early) if early else np.array([])
            off_l = cm.offset(later)
            ys += [c["y"] for c in later]
            groups += [f"{r['id']}@{cut}"] * len(later)
            out["rule only (current)"] += [prior_mean.get(r["id"], np.mean([c["y"] for c in train]))] * len(later)
            out["comment model only"] += list(expit(off_l))
            for t in taus:
                u, sd = rule_effect(y_e, off_e, t) if early else (0.0, t)
                out[f"comment model + rule, tau {t}"] += list(expit(off_l + u))
                if t == TAU:
                    bands += [estimate.level(float(norm.sf(0, u, sd)))] * len(later)
                    expected += list(expit(off_l))
    print(f"{len(ys)} later rule comments across {len(cutoffs)} windows\n")
    print(f"{'predictor':34} {'Brier':>7} {'log loss':>9}")
    for name, p in out.items():
        brier, ll = estimate.scores(ys, p)
        print(f"{name:34} {brier:7.4f} {ll:9.4f}")
    a, b = np.array(out["rule only (current)"]), np.array(out[f"comment model + rule, tau {TAU}"])
    y = np.array(ys)
    g = np.array(groups)
    keys = np.unique(g)
    idx = {k: np.where(g == k)[0] for k in keys}
    rng = np.random.default_rng(5)
    diffs = []
    for _ in range(2000):
        s = np.concatenate([idx[k] for k in rng.choice(keys, len(keys))])
        diffs.append(np.mean((b[s] - y[s]) ** 2) - np.mean((a[s] - y[s]) ** 2))
    print(f"\nBrier change, comment model + rule vs rule only: {np.mean((b - y) ** 2) - np.mean((a - y) ** 2):+.4f} "
          f"(95% {np.percentile(diffs, 2.5):+.4f} to {np.percentile(diffs, 97.5):+.4f}, resampling rule-windows)")
    print("Levels from P(rule effect > 0), judged on later comments:")
    ex = np.array(expected)
    for lv in ("high", "medium", "low"):
        sel = np.array([x == lv for x in bands])
        if sel.sum():
            print(f"  {lv:7} {sel.sum():4} comments, acted on {y[sel].mean():.1%}, expected from reviewer and phrasing "
                  f"{ex[sel].mean():.1%}")
    print("Reliability (comment model + rule):")
    for lo, hi in [(0, .5), (.5, .6), (.6, .7), (.7, .8), (.8, .9), (.9, 1.01)]:
        sel = (b >= lo) & (b < hi)
        if sel.sum():
            print(f"  {lo:.1f}-{min(hi, 1):.1f}: {sel.sum():4} comments, predicted {b[sel].mean():.1%}, observed {y[sel].mean():.1%}")
    return ys, out


def fit(tau=TAU):
    rules, examples, extra, rule_key = estimate.load()
    comments = load_comments()
    by_id = {c["id"]: c for c in comments}
    members = rule_members(rules, by_id)
    cm = CommentModel().fit(comments)
    base = np.mean([c["y"] for c in comments])
    nz = len(COMMENT_FEATURES)
    weights = {f: round(float(w), 3) for f, w in zip(COMMENT_FEATURES, cm.w[1:1 + nz])}
    out = {}
    for r in rules:
        cs = [by_id[m] for m in members[r["id"]]]
        if not cs:
            continue
        y = np.array([c["y"] for c in cs])
        off = cm.offset(cs)
        u, sd = rule_effect(y, off, tau)
        typical = float(expit(off).mean())
        rate = lambda v: float(expit(off + v).mean())
        out[rule_key(r)] = {"effect": round(u, 3), "sd": round(sd, 3), "p_above": round(float(norm.sf(0, u, sd)), 3),
                            "expected": round(typical, 3), "adjusted": round(rate(u), 3),
                            "lo": round(rate(u - 1.645 * sd), 3), "hi": round(rate(u + 1.645 * sd), 3),
                            "k": int(y.sum()), "n": len(y)}
    return {"baseline": round(float(base), 3), "tau": tau, "comment_weights": weights, "rules": out}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if mode == "validate":
        validate()
    elif mode == "authors":
        global USE_AUTHORS
        USE_AUTHORS = True
        validate([TAU])
    else:
        res = fit()
        print("comment model weights (log-odds per standard deviation):", res["comment_weights"])
        lv = [v["p_above"] for v in res["rules"].values()]
        print(f"rules {len(lv)}; P(effect > 0) >= 0.8: {sum(p >= 0.8 for p in lv)}, <= 0.3: {sum(p <= 0.3 for p in lv)}")


if __name__ == "__main__":
    main()
