#!/usr/bin/env python3
"""Find terms and code areas whose use surged or faded, with no keywords supplied.

Documents are merge requests (title, description, and the directories their merge
commit changed) and Discourse topics (title and first post). Each document is reduced
to a set of tokens:

  words and identifiers    from the text, lowercased unless they look like code
  dir:<a>/<b>              the top two directory levels of each changed file

For every token, the share of documents containing it is computed per quarter. Each
token is scored three ways and assigned to whichever ratio is largest (at least 2.5):

  emerging   share in the last 2 years over share in the 4 years before
  fading     share in the first 3 years of the record over share in the last 2 years
  past       peak (4-quarter smoothed) over the surrounding years, for peaks that ended

Tokens are ranked by log(ratio) times log(number of documents).

Writes data/trends/terms.json and data/trends/TERMS.md.

Usage:
  python trends/discover_terms.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import glob
import html
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from wordfreq import zipf_frequency

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before being below between both
but by can could did do does doing down during each few for from further had has have having he her here hers him his
how i if in into is it its itself just let me more most my no nor not now of off on once only or other our ours out over
own same she should so some such than that the their them then there these they this those through to too under until
up very was we were what when where which while who whom why will with would you your yours yes ok thanks thank please
http https www com org html md png jpg gif
""".split())
WORD = re.compile(r"[A-Za-z][A-Za-z0-9_+#.-]*[A-Za-z0-9+#]|[A-Za-z]{2}")
CODE_LIKE = re.compile(r"[a-z][A-Z]|[A-Z]{2}|_|\d")
MIN_DOCS = 15
SMOOTH = 4
RECENT, EARLIER, START = 8, 16, 12
MIN_RATIO = 2.5
COMMON_ZIPF = 3.5


def is_common(token):
    return token.islower() and not CODE_LIKE.search(token) and zipf_frequency(token, "en") >= COMMON_ZIPF


def quarter(ts):
    return f"{ts[:4]}Q{(int(ts[5:7]) - 1) // 3 + 1}"


URL = re.compile(r"https?://\S+|\S+@\S+")
MENTION = re.compile(r"@[\w.-]+")


def tokens(text):
    out = set()
    for w in WORD.findall(MENTION.sub(" ", URL.sub(" ", text or ""))):
        w = w.strip(".-")
        if len(w) < 3:
            continue
        key = w if CODE_LIKE.search(w) else w.lower()
        if key.lower() not in STOPWORDS:
            out.add(key)
    return out


def changed_dirs(repo, sha):
    r = subprocess.run(["git", "-C", repo, "diff", "--name-only", f"{sha}^1", sha], capture_output=True, text=True)
    if r.returncode:
        return set()
    return {"dir:" + "/".join(Path(p).parts[:2]) for p in r.stdout.splitlines() if len(Path(p).parts) > 1}


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or ""))


def people_names(record, people):
    for user in [record["merge_request"]["author"]] + [n["author"] for d in record.get("discussions") or []
                                                        for n in d.get("notes", [])]:
        if re.search(r"bot|ghost|project|release|robot", f"{user['username']} {user['name']}", re.I):
            continue
        people.add(user["username"].lower())


def load_documents(mirror, discourse, repo):
    docs, people = [], set()
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        record = json.load(open(f))
        people_names(record, people)
        mr = record["merge_request"]
        toks = tokens(mr["title"]) | tokens((mr.get("description") or "")[:3000])
        if mr.get("merge_commit_sha"):
            toks |= changed_dirs(repo, mr["merge_commit_sha"])
        docs.append({"source": "mr", "id": mr["iid"], "title": mr["title"], "q": quarter(mr["created_at"]),
                     "tokens": toks})
    for f in glob.glob(f"{discourse}/topics/*.json"):
        t = json.load(open(f))
        first = strip_html(t["posts"][0]["cooked"]) if t["posts"] else ""
        docs.append({"source": "discourse", "id": t["topic"]["id"], "title": t["topic"]["title"],
                     "q": quarter(t["topic"]["created_at"]), "tokens": tokens(t["topic"]["title"]) | tokens(first[:3000])})
    people -= {"vtk", "paraview", "kitware", "robot", "bot"}
    removed = Counter(t for d in docs for t in d["tokens"] if t.lower() in people)
    print(f"removed {len(removed)} person-name tokens; most frequent: "
          + ", ".join(f"{t} ({n})" for t, n in removed.most_common(60)))
    for d in docs:
        d["tokens"] = {t for t in d["tokens"] if t.lower() not in people}
    return docs


def all_quarters(docs):
    qs = sorted({d["q"] for d in docs})
    first, last = qs[0], qs[-1]
    out, (y, q) = [], (int(first[:4]), int(first[5]))
    while f"{y}Q{q}" <= last:
        out.append(f"{y}Q{q}")
        y, q = (y + 1, 1) if q == 4 else (y, q + 1)
    return out


def analyze(docs, quarters, last_complete):
    qi = {q: i for i, q in enumerate(quarters)}
    n = [0] * len(quarters)
    df = defaultdict(lambda: [0] * len(quarters))
    for d in docs:
        i = qi[d["q"]]
        n[i] += 1
        for t in d["tokens"]:
            df[t][i] += 1
    end = qi[last_complete] + 1
    eps = 0.5 / max(1, sum(n[:end]) / end)

    def mean_share(counts, lo, hi):
        lo, hi = max(0, lo), min(end, hi)
        docs = sum(n[lo:hi])
        return sum(counts[lo:hi]) / docs if docs else 0.0

    results = []
    for tok, counts in df.items():
        total = sum(counts[:end])
        if total < MIN_DOCS:
            continue
        share = [counts[i] / n[i] if n[i] else 0.0 for i in range(end)]
        smooth = [sum(share[max(0, i - SMOOTH + 1):i + 1]) / min(SMOOTH, i + 1) for i in range(end)]
        peak = max(range(end), key=lambda i: smooth[i])
        recent = mean_share(counts, end - RECENT, end)
        earlier = mean_share(counts, end - RECENT - EARLIER, end - RECENT)
        start = mean_share(counts, 0, START)
        around = max(mean_share(counts, peak - 12, peak - SMOOTH), mean_share(counts, peak + SMOOTH, peak + 12))
        ratios = {
            "emerging": (recent + eps) / (earlier + eps),
            "fading": (start + eps) / (recent + eps),
            "past": (smooth[peak] + eps) / (around + eps) if RECENT <= peak < end - RECENT else 0.0,
        }
        kind = max(ratios, key=ratios.get)
        ratio = ratios[kind]
        if ratio < MIN_RATIO:
            kind, ratio = "steady", 1.0
        first = next(i for i in range(end) if counts[i])
        results.append({"token": tok, "kind": kind, "score": round(math.log(ratio) * math.log(total), 3),
                        "ratio": round(ratio, 2), "docs": total, "first_seen": quarters[first],
                        "peak": quarters[peak], "share_recent": round(recent, 4), "share_peak": round(smooth[peak], 4),
                        "series": counts[:end]})
    return results, n[:end]


def examples(docs, token, k=5):
    hits = sorted((d for d in docs if token in d["tokens"]), key=lambda d: d["q"])
    step = max(1, len(hits) // k)
    return [{"source": d["source"], "id": d["id"], "q": d["q"], "title": d["title"]} for d in hits[::step][:k]]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default="data/vtk-history")
    p.add_argument("--discourse", default="data/discourse-history")
    p.add_argument("--repo", default=config.VTK_REPO)
    p.add_argument("--last-quarter", default="2026Q2", help="last complete quarter included in the analysis")
    p.add_argument("--top", type=int, default=40)
    p.add_argument("--out", default="data/trends")
    args = p.parse_args()

    all_docs = load_documents(args.mirror, args.discourse, args.repo)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report = {}
    lines = ["# Term and code-area trends", "",
             f"Discovered through {args.last_quarter} with no keywords supplied. Each source is analyzed separately, "
             "since Discourse starts later than GitLab. Ratio: emerging = last 2 years over the 4 before; "
             "fading = first 3 years of the source over the last 2; past = peak over the surrounding years.", ""]
    for source, name in (("mr", "Merge requests"), ("discourse", "Discourse topics")):
        docs = [d for d in all_docs if d["source"] == source]
        quarters = all_quarters(docs)
        results, n = analyze(docs, quarters, args.last_quarter)
        print(f"\n{name}: {len(docs)} documents, {quarters[0]} to {args.last_quarter}, "
              f"{len(results)} tokens in at least {MIN_DOCS} documents")
        ranked = {}
        for common, suffix, top in ((False, "", args.top), (True, " (common English words)", 15)):
            for kind in ("emerging", "past", "fading"):
                ranked[kind + suffix] = sorted((r for r in results if r["kind"] == kind and is_common(r["token"]) == common),
                                               key=lambda r: -r["score"])[:top]
        for rs in ranked.values():
            for r in rs:
                r["examples"] = examples(docs, r["token"])
        report[source] = {"quarters": quarters[:len(n)], "documents_per_quarter": n, "ranked": ranked}

        lines += [f"# {name} ({len(docs)} documents from {quarters[0]})", ""]
        for kind, rs in ranked.items():
            lines += [f"## {kind.capitalize()}", "", "| Token | Ratio | Docs | First seen | Peak | Example |",
                      "| --- | --- | --- | --- | --- | --- |"]
            for r in rs:
                ex = r["examples"][len(r["examples"]) // 2]
                ref = f"!{ex['id']}" if ex["source"] == "mr" else f"topic {ex['id']}"
                lines.append(f"| `{r['token']}` | {r['ratio']} | {r['docs']} | {r['first_seen']} | {r['peak']} | "
                             f"{ref}: {ex['title'][:60].replace('|', '/')} |")
            lines.append("")
            print(f"  {kind}: " + ", ".join(f"{r['token']} ({r['peak']})" for r in rs[:25]))

    json.dump(report, open(out / "terms.json", "w"), indent=1)
    (out / "TERMS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
