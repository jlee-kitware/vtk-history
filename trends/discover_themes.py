#!/usr/bin/env python3
"""Group merge requests and Discourse topics by meaning and rank how each group changed over time.

1. Embed each document (title plus the start of its description or first post).
2. Group all documents with k-means on the embeddings, shared across both sources.
3. Score each group's share of documents per quarter, per source, with the emerging,
   fading, and past ratios from discover_terms.py.
4. After ranking, name each group from the titles nearest its center.

Writes data/trends/themes.json and data/trends/THEMES.md.

Usage:
  python trends/discover_themes.py
  python trends/discover_themes.py --k 120
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import glob
import json
import sys
import time
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.cluster.vq import kmeans2

sys.path.insert(0, str(Path(__file__).parent))
from discover_terms import all_quarters, analyze, quarter, strip_html  # noqa: E402

HOST = config.OLLAMA_HOST
MAX_CHARS = 1500
BATCH = 32
NAME_PROMPT = """These are titles of VTK merge requests and VTK forum topics that were grouped together because their content is similar.

{titles}

Reply with JSON only:
  "name": what they have in common, in at most 6 words
  "description": one sentence describing the group
Use only what the titles show."""


def post(path, payload, timeout=600):
    for attempt in range(5):
        try:
            req = urllib.request.Request(HOST + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=timeout))
        except OSError as e:
            print(f"  {path} failed ({e}); retrying", file=sys.stderr)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"{path} failed after retries")


def load_documents(mirror, discourse):
    docs = []
    for f in sorted(glob.glob(f"{mirror}/merge_requests/*.json")):
        mr = json.load(open(f))["merge_request"]
        docs.append({"source": "mr", "id": mr["iid"], "title": mr["title"], "q": quarter(mr["created_at"]),
                     "text": f"{mr['title']}\n\n{(mr.get('description') or '')[:MAX_CHARS]}"})
    for f in sorted(glob.glob(f"{discourse}/topics/*.json")):
        t = json.load(open(f))
        first = strip_html(t["posts"][0]["cooked"]) if t["posts"] else ""
        docs.append({"source": "discourse", "id": t["topic"]["id"], "title": t["topic"]["title"],
                     "q": quarter(t["topic"]["created_at"]), "text": f"{t['topic']['title']}\n\n{first[:MAX_CHARS]}"})
    return docs


def key(d):
    return f"{d['source']}:{d['id']}"


def embed(docs, model, cache):
    cached = {}
    if cache.exists():
        data = np.load(cache, allow_pickle=True).item()
        cached = dict(zip(data["ids"], data["vectors"]))
    todo = [d for d in docs if key(d) not in cached]
    print(f"embedding {len(todo)} documents ({len(docs) - len(todo)} cached)", flush=True)
    start = time.time()
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        vecs = post("/api/embed", {"model": model, "input": [d["text"] for d in batch], "truncate": True})["embeddings"]
        cached.update({key(d): np.asarray(v, dtype=np.float32) for d, v in zip(batch, vecs)})
        done = i + len(batch)
        if (i // BATCH) % 20 == 0 or done == len(todo):
            np.save(cache, {"ids": list(cached), "vectors": list(cached.values())})
            rate = done / max(1e-9, time.time() - start)
            print(f"  {done}/{len(todo)}, {rate:.1f}/s, {(len(todo) - done) / rate / 60:.0f} min left", flush=True)
    v = np.stack([cached[key(d)] for d in docs])
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def name_theme(model, titles):
    prompt = NAME_PROMPT.format(titles="\n".join(f"- {t}" for t in titles))
    for attempt in range(3):
        try:
            r = post("/api/generate", {"model": model, "prompt": prompt, "stream": False, "format": "json",
                                        "think": False, "options": {"temperature": 0, "num_predict": 120}})
            out = json.loads(r["response"])
            if out.get("name"):
                return out
        except (json.JSONDecodeError, KeyError):
            time.sleep(5)
    return {"name": None, "description": None}


def nearest(docs, vectors, members, center, k):
    order = sorted(members, key=lambda i: -float(vectors[i] @ center))
    return [docs[i] for i in order[:k]]


def theme_label(t):
    return f"{t['name'] or '(unnamed)'} (T{t['id']})"


def write_markdown(path, themes, report, last_quarter, top):
    lines = ["# Themes", "",
             f"{len(themes)} groups found by k-means on document embeddings, through {last_quarter}, with no keywords "
             "supplied. Groups were ranked before they were named; names come from the titles nearest each group's "
             "center. Ratio: emerging = last 2 years over the 4 before; fading = first 3 years of the source over "
             "the last 2; past = peak over the surrounding years.", ""]
    for source, name in (("mr", "Merge requests"), ("discourse", "Discourse topics")):
        scores = report["sources"][source]["scores"]
        lines += [f"# {name}", ""]
        for kind in ("emerging", "past", "fading"):
            ranked = sorted((s for s in scores.values() if s["kind"] == kind), key=lambda s: -s["score"])[:top]
            lines += [f"## {kind.capitalize()}", "", "| Theme | Ratio | Docs | First seen | Peak | Nearest titles |",
                      "| --- | --- | --- | --- | --- | --- |"]
            for s in ranked:
                t = themes[s["token"].split(":")[1]]
                titles = "; ".join(e["title"][:50].replace("|", "/") for e in t["examples"][source][:2])
                lines.append(f"| {theme_label(t)} | {s['ratio']} | {s['docs']} | {s['first_seen']} | {s['peak']} | {titles} |")
            lines.append("")
    lines += ["# All themes", "", "| Theme | Docs | MRs | Topics | MR trend | Discourse trend | Description |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for t in sorted(themes.values(), key=lambda t: -t["size"]):
        kinds = [report["sources"][s]["scores"].get(str(t["id"]), {}).get("kind", "-") for s in ("mr", "discourse")]
        lines.append(f"| {theme_label(t)} | {t['size']} | {t['sources'].get('mr', 0)} | {t['sources'].get('discourse', 0)} "
                     f"| {kinds[0]} | {kinds[1]} | {(t['description'] or '').replace('|', '/')} |")
    Path(path).write_text("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mirror", default="data/vtk-history")
    p.add_argument("--discourse", default="data/discourse-history")
    p.add_argument("--embed-model", default="qwen3-embedding:latest")
    p.add_argument("--name-model", default="qwen3-coder-next:q4_K_M")
    p.add_argument("--k", type=int, default=80)
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--last-quarter", default="2026Q2")
    p.add_argument("--top", type=int, default=25)
    p.add_argument("--out", default="data/trends")
    p.add_argument("--cache", default="data/trends/doc_embeddings.npy")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    docs = load_documents(args.mirror, args.discourse)
    print(f"{len(docs)} documents ({Counter(d['source'] for d in docs)})", flush=True)
    vectors = embed(docs, args.embed_model, Path(args.cache))

    centers, labels = kmeans2(vectors, args.k, minit="++", seed=args.seed, iter=50)
    centers = centers / np.linalg.norm(centers, axis=1, keepdims=True)
    members = {}
    for i, c in enumerate(labels):
        members.setdefault(int(c), []).append(i)
        docs[i]["tokens"] = {f"theme:{int(c)}"}
    print(f"{len(members)} non-empty groups; sizes {sorted(len(m) for m in members.values())}", flush=True)

    report = {"k": args.k, "seed": args.seed, "sources": {}}
    for source in ("mr", "discourse"):
        sdocs = [d for d in docs if d["source"] == source]
        quarters = all_quarters(sdocs)
        results, n = analyze(sdocs, quarters, args.last_quarter)
        report["sources"][source] = {"quarters": quarters[:len(n)], "documents_per_quarter": n,
                                     "scores": {r["token"].split(":")[1]: r for r in results}}

    ids = sorted(members)
    with ThreadPoolExecutor(2) as pool:
        names = list(pool.map(lambda c: name_theme(
            args.name_model, [d["title"] for d in nearest(docs, vectors, members[c], centers[c], 15)]), ids))
    themes = {}
    for c, nm in zip(ids, names):
        by_source = {s: [i for i in members[c] if docs[i]["source"] == s] for s in ("mr", "discourse")}
        themes[str(c)] = {
            "id": c, "name": nm.get("name"), "description": nm.get("description"), "size": len(members[c]),
            "sources": {s: len(m) for s, m in by_source.items()},
            "examples": {s: [{"id": d["id"], "q": d["q"], "title": d["title"]}
                             for d in nearest(docs, vectors, m, centers[c], 5)] for s, m in by_source.items()},
        }
    report["themes"] = themes
    json.dump(report, open(out / "themes.json", "w"), indent=1, ensure_ascii=False)
    json.dump({key(d): int(c) for d, c in zip(docs, labels)}, open(out / "theme_assignments.json", "w"))
    write_markdown(out / "THEMES.md", themes, report, args.last_quarter, args.top)

    for source in ("mr", "discourse"):
        scores = report["sources"][source]["scores"]
        for kind in ("emerging", "past", "fading"):
            ranked = sorted((s for s in scores.values() if s["kind"] == kind), key=lambda s: -s["score"])[:15]
            print(f"{source} {kind}: " + "; ".join(
                f"{theme_label(themes[s['token'].split(':')[1]])} {s['peak']}" for s in ranked), flush=True)


if __name__ == "__main__":
    main()
