#!/usr/bin/env python3
"""Search the index built by index/build_index.py.

Combines two rankings by reciprocal rank fusion:
  keyword    SQLite FTS5 BM25 over title, text, file path, and class (exact identifiers)
  meaning    cosine similarity of qwen3-embedding vectors (paraphrases)

Filters: kind (thread, mr, issue, post, blog, doc, note, class), date range, module, class, path prefix, author.
With no kind given, search_mixed adds the best few of each kind missing from the overall top results, so a
small source (blog posts, docs) is not crowded out by a large one (review threads).
The --until filter lets an evaluation see only history from before a given date.

Usage:
  python index/search.py "GetVoidPointer replacement"
  python index/search.py "ghost cells in parallel filters" --kind thread --until 2026-01-01
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import config  # noqa: E402
import argparse
import json
import re
import sqlite3
import sys
import threading
import urllib.request
from pathlib import Path

import numpy as np

HOST = config.OLLAMA_HOST
INSTRUCT = ("Instruct: Given a question or code change about the VTK library, retrieve past code review discussions, "
            "merge requests, issues, and forum posts that are relevant\nQuery: ")
RRF_K = 60
TOKEN = re.compile(r"[A-Za-z0-9_]{2,}")
CODE_SHAPED = re.compile(r"[a-z][A-Z]|_|^vtk")
COMMON = set("""the and for this that with from are was not but can will should would could has have had its into
if else return const int double float void auto true false nullptr this new delete static class struct public
private protected virtual override include define endif ifndef std size_t vtkIdType for while do break continue
""".split())


class Index:
    def __init__(self, path="data/index"):
        self.path = Path(path)
        self._local = threading.local()
        meta = self.path / "meta.json"
        self.meta = json.loads(meta.read_text()) if meta.exists() else None
        self.vectors = None
        if self.meta and (self.path / "vectors.npy").exists():
            self.vectors = np.load(self.path / "vectors.npy").astype(np.float32)
            cols = self.con.execute("SELECT kind, date, module, class, path, author FROM docs ORDER BY rowid").fetchall()
            self.cols = {name: np.array([c[i] or "" for c in cols]) for i, name in
                         enumerate(("kind", "date", "module", "class", "path", "author"))}

    @property
    def con(self):
        """One SQLite connection per thread; a shared connection corrupts concurrent cursors."""
        if not hasattr(self._local, "con"):
            self._local.con = sqlite3.connect(self.path / "docs.sqlite")
            self._local.con.row_factory = sqlite3.Row
        return self._local.con

    def embed(self, texts, query=True):
        payload = {"model": self.meta["model"], "input": [INSTRUCT + t if query else t for t in texts], "truncate": True}
        req = urllib.request.Request(HOST + "/api/embed", json.dumps(payload).encode(), {"Content-Type": "application/json"})
        v = np.asarray(json.load(urllib.request.urlopen(req, timeout=300))["embeddings"], np.float32)[:, :self.meta["dim"]]
        return v / np.linalg.norm(v, axis=1, keepdims=True)

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

    def keyword(self, query, n, max_terms=40, **f):
        seen = dict.fromkeys(t for t in TOKEN.findall(query) if t.lower() not in COMMON)
        terms = sorted(seen, key=lambda t: (not CODE_SHAPED.search(t), -len(t)))[:max_terms]
        if not terms:
            return []
        match = " OR ".join(f'"{t}"' for t in terms)
        where, params = self._where(f)
        rows = self.con.execute(
            "WITH hits AS MATERIALIZED (SELECT rowid, bm25(docs_fts, 2.0, 1.0, 3.0, 3.0) AS s FROM docs_fts "
            "WHERE docs_fts MATCH ? ORDER BY s LIMIT ?) "
            f"SELECT h.rowid FROM hits h JOIN docs d ON d.rowid = h.rowid WHERE 1=1{where} ORDER BY h.s LIMIT ?",
            [match, max(2000, 40 * n), *params, n]).fetchall()
        return [r[0] for r in rows]

    def meaning(self, query, n, query_vector=None, **f):
        if self.vectors is None:
            return []
        scores = self.vectors @ (self.embed([query])[0] if query_vector is None else query_vector)
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

    def fuse(self, query, pool, query_vector=None, **filters):
        fused = {}
        for ranking in (self.keyword(query, pool, **filters),
                        self.meaning(query, pool, query_vector=query_vector, **filters)):
            for rank, rowid in enumerate(ranking):
                fused[rowid] = fused.get(rowid, 0.0) + 1.0 / (RRF_K + rank + 1)
        return fused

    def rows(self, ids, scores, **extra):
        rows = {r["rowid"]: r for r in self.con.execute(
            f"SELECT rowid, * FROM docs WHERE rowid IN ({','.join('?' * len(ids))})", ids)} if ids else {}
        return [dict(rows[i], score=round(scores[i], 4), **extra) for i in ids]

    def search(self, query, k=10, pool=50, **filters):
        fused = self.fuse(query, pool, **filters)
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        return self.rows(best, fused)

    def search_mixed(self, query, k=25, per_kind=3, pool=50, **filters):
        """The overall best k, then the best per_kind of every kind absent from them (marked other_kind)."""
        if filters.get("kind"):
            return self.search(query, k, pool, **filters)
        qv = self.embed([query])[0] if self.vectors is not None else None
        fused = self.fuse(query, pool, query_vector=qv, **filters)
        best = sorted(fused, key=fused.get, reverse=True)[:k]
        out = self.rows(best, fused)
        shown = {r["kind"] for r in out}
        kinds = [r[0] for r in self.con.execute("SELECT DISTINCT kind FROM docs")]
        for kind in kinds:
            if kind in shown:
                continue
            per = self.fuse(query, pool, query_vector=qv, **dict(filters, kind=kind))
            top = sorted(per, key=per.get, reverse=True)[:per_kind]
            out += self.rows(top, per, other_kind=True)
        return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("query")
    p.add_argument("-k", type=int, default=10)
    p.add_argument("--kind", choices=["thread", "mr", "issue", "post", "blog", "doc", "note", "class"])
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
