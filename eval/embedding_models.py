#!/usr/bin/env python3
"""Build a search index variant whose issue and MR vectors come from another embedding model, so
eval/related_history.py can compare models on the same test.

Only issue and MR rows are embedded (the related-history test searches nothing else); other rows
get zero vectors. The variant shares docs.sqlite with the main index through a symlink.
Also times one query embedding per model, the cost the app pays per search.

Usage:
  python eval/embedding_models.py qwen3-embedding:0.6b      # writes data/index-qwen3-embedding_0.6b/
  python eval/related_history.py --index data/index-qwen3-embedding_0.6b
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import json
import sqlite3
import time
import urllib.request

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
EMBED_CHARS, MR_DESC = 2000, 1500
BATCH = 32


def post(path, payload, timeout=1200):
    req = urllib.request.Request(config.OLLAMA_HOST + path, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=timeout))


def embed(model, texts, dim):
    v = np.asarray(post("/api/embed", {"model": model, "input": texts, "truncate": True})["embeddings"],
                   np.float32)[:, :dim]
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embed_text(kind, text):
    if kind == "mr":
        title, _, desc = text.partition("\n\n")
        return f"{title}\n\n{desc[:MR_DESC]}"
    return text[:EMBED_CHARS]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("model")
    p.add_argument("--index", default=str(ROOT / "data/index"))
    args = p.parse_args()

    src = Path(args.index)
    meta = json.loads((src / "meta.json").read_text())
    out = ROOT / f"data/index-{args.model.replace(':', '_')}"
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "docs.sqlite").exists():
        (out / "docs.sqlite").symlink_to((src / "docs.sqlite").resolve())

    post("/api/pull", {"model": args.model, "stream": False}, timeout=3600)
    rows = sqlite3.connect(src / "docs.sqlite").execute(
        "SELECT rowid, kind, text FROM docs WHERE kind IN ('issue', 'mr') ORDER BY rowid").fetchall()
    vectors = np.zeros((meta["count"], meta["dim"]), np.float16)
    start = time.time()
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        vecs = embed(args.model, [embed_text(k, t or "") for _, k, t in batch], meta["dim"])
        vectors[[r - 1 for r, _, _ in batch]] = vecs.astype(np.float16)
        if (i // BATCH) % 100 == 0:
            print(f"  {i + len(batch)}/{len(rows)}, {(i + len(batch)) / (time.time() - start):.0f}/s", flush=True)
    np.save(out / "vectors.npy", vectors)
    (out / "meta.json").write_text(json.dumps({"model": args.model, "dim": meta["dim"], "count": meta["count"]}))

    query = rows[len(rows) // 2][2][:1600]
    embed(args.model, [query], meta["dim"])
    t = time.time()
    for _ in range(10):
        embed(args.model, [query], meta["dim"])
    print(f"{args.model}: {len(rows)} documents in {time.time() - start:.0f}s; "
          f"one query takes {(time.time() - t) / 10 * 1000:.0f} ms on the model server", flush=True)


if __name__ == "__main__":
    main()
