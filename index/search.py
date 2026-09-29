#!/usr/bin/env python3
"""Search the index built by index/build_index.py.

Combines two rankings by reciprocal rank fusion:
  keyword    SQLite FTS5 BM25 over title, text, file path, and class (exact identifiers)
  meaning    cosine similarity of qwen3-embedding vectors (paraphrases)

Filters: kind (thread, mr, issue, post), date range, module, class, path prefix, author.
The --until filter lets an evaluation see only history from before a given date.

Usage:
  python index/search.py "GetVoidPointer replacement"
  python index/search.py "ghost cells in parallel filters" --kind thread --until 2026-01-01
"""

import argparse
import json
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

import numpy as np

HOST = "http://192.168.50.23:11435"
INSTRUCT = ("Instruct: Given a question or code change about the VTK library, retrieve past code review discussions, "
            "merge requests, issues, and forum posts that are relevant\nQuery: ")
RRF_K = 60
TOKEN = re.compile(r"[A-Za-z0-9_]{2,}")


class Index:
    def __init__(self, path="data/index"):
        self.path = Path(path)
        self.con = sqlite3.connect(self.path / "docs.sqlite", check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        meta = self.path / "meta.json"
        self.meta = json.loads(meta.read_text()) if meta.exists() else None
        self.vectors = None
        if self.meta and (self.path / "vectors.npy").exists():
            self.vectors = np.load(self.path / "vectors.npy").astype(np.float32)
            cols = self.con.execute("SELECT kind, date, module, class, path, author FROM docs ORDER BY rowid").fetchall()
            self.cols = {name: np.array([c[i] or "" for c in cols]) for i, name in
                         enumerate(("kind", "date", "module", "class", "path", "author"))}

    def _where(self, f):
        clauses, params = [], []
        for col in ("kind", "module", "class", "author"):
            if f.get(col):
                clauses.append(f"d.{col} = ?")
                params.append(f[col])
        if f.get("since"):
            clauses.append("d.date >= ?")
            params.append(f["since"])
        if f.get("until"):
            clauses.append("d.date < ?")
            params.append(f["until"])
        if f.get("path"):
            clauses.append("d.path LIKE ?")
            params.append(f["path"] + "%")
        return (" AND " + " AND ".join(clauses)) if clauses else "", params

    def keyword(self, query, n, **f):
        terms = TOKEN.findall(query)
        if not terms:
            return []
        match = " OR ".join(f'"{t}"' for t in terms)
        where, params = self._where(f)
        rows = self.con.execute(
            f"SELECT d.rowid FROM docs_fts JOIN docs d ON d.rowid = docs_fts.rowid "
            f"WHERE docs_fts MATCH ?{where} ORDER BY bm25(docs_fts, 2.0, 1.0, 3.0, 3.0) LIMIT ?",
            [match, *params, n]).fetchall()
        return [r[0] for r in rows]

    def meaning(self, query, n, **f):
        if self.vectors is None:
            return []
        req = urllib.request.Request(HOST + "/api/embed", json.dumps(
            {"model": self.meta["model"], "input": [INSTRUCT + query], "truncate": True}).encode(),
            {"Content-Type": "application/json"})
        q = np.asarray(json.load(urllib.request.urlopen(req, timeout=120))["embeddings"][0], np.float32)[:self.meta["dim"]]
        scores = self.vectors @ (q / np.linalg.norm(q))
        mask = np.ones(len(scores), bool)
        for col in ("kind", "module", "class", "author"):
            if f.get(col):
                mask &= self.cols[col] == f[col]
        if f.get("since"):
            mask &= self.cols["date"] >= f["since"]
        if f.get("until"):
            mask &= self.cols["date"] < f["until"]
        if f.get("path"):
            mask &= np.char.startswith(self.cols["path"], f["path"])
        scores[~mask] = -np.inf
        top = np.argpartition(-scores, min(n, len(scores) - 1))[:n]
        return [int(i) + 1 for i in top[np.argsort(-scores[top])] if np.isfinite(scores[i])]

    def search(self, query, k=10, pool=50, **filters):
        fused = {}
        for ranking in (self.keyword(query, pool, **filters), self.meaning(query, pool, **filters)):
            for rank, rowid in enumerate(ranking):
                fused[rowid] = fused.get(rowid, 0.0) + 1.0 / (RRF_K + rank + 1)
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        rows = {r["rowid"]: r for r in self.con.execute(
            f"SELECT rowid, * FROM docs WHERE rowid IN ({','.join('?' * len(best))})", best)} if best else {}
        return [dict(rows[i], score=round(fused[i], 4)) for i in best]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query")
    p.add_argument("-k", type=int, default=10)
    p.add_argument("--kind", choices=["thread", "mr", "issue", "post"])
    p.add_argument("--since")
    p.add_argument("--until")
    p.add_argument("--module")
    p.add_argument("--class", dest="class_")
    p.add_argument("--path")
    p.add_argument("--author")
    p.add_argument("--index", default="data/index")
    args = p.parse_args()

    idx = Index(args.index)
    if idx.vectors is None:
        print("(embeddings not built yet: keyword search only)", file=sys.stderr)
    hits = idx.search(args.query, args.k, kind=args.kind, since=args.since, until=args.until, module=args.module,
                      **{"class": args.class_}, path=args.path, author=args.author)
    for h in hits:
        where = f" {h['path']}" if h["path"] else ""
        print(f"{h['score']:.4f} {h['kind']:6} {h['ref']:12} {h['date']} {h['author']}{where}\n"
              f"    {h['title'][:90]}\n    {' '.join(h['text'].split())[:220]}\n")


if __name__ == "__main__":
    main()
