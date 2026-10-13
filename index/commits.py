#!/usr/bin/env python3
"""Index of VTK's git history: one entry per non-merge commit on upstream master.

Each entry holds the message, author, date written, date landed on master (its merge's date), the files changed, the functions changed (the enclosing function git
names in each hunk header), line counts, and the merge request that brought the commit in (from the
"Merge-request: !N" line of its merge commit). Diffs stay in git and are read with `git show` when needed.

  build    parse the history into data/index/commits.sqlite (keyword search over message, files, functions)
  embed    qwen3-embedding vectors for each commit, resumable: data/index/commit_vectors.npy
  search   keyword and meaning search, filters by path, function and date

Usage:
  python index/commits.py build
  python index/commits.py embed
  python index/commits.py search "vtkOpenGLRenderWindow::Initialize context creation" --until 2025-01-01
"""

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "index"))
from search import HOST, INSTRUCT, RRF_K  # noqa: E402

REPO = "/home/jlee/gitsync/vtk"
BRANCH = "upstream/master"
DB = ROOT / "data/index/commits.sqlite"
VECTORS = ROOT / "data/index/commit_vectors.npy"
PROGRESS = ROOT / "data/index/commit_vectors.json"
MODEL, DIM = "qwen3-embedding:latest", 1024
SKIP = re.compile(r"^(ThirdParty|Utilities/(KWIML|KWSys|MetaIO|DICOMParser|octree)|.*Testing/Data|.*Baseline)/")
TRAILER = re.compile(r"^(Acked-by|Reviewed-by|Signed-off-by|Co-authored-by|Change-Id|Merge-request|Tested-by):",
                     re.I | re.M)
FUNC = re.compile(r"([A-Za-z_][\w:~<>]*)\s*\(")


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, errors="replace").stdout


def merge_requests():
    """(commit sha -> MR number, commit sha -> date it landed on master), from the first-parent history: a merge's
    commits land on the merge's date and take its Merge-request number; a direct commit lands on its own date."""
    mrs, landed = {}, {}
    log = git("log", "--first-parent", "--format=%H%x00%P%x00%cd%x00%b%x1e", "--date=short", BRANCH)
    merges = []
    for rec in log.split("\x1e"):
        parts = rec.strip("\n").split("\x00")
        if len(parts) < 4:
            continue
        sha, parents, date, body = parts
        ps = parents.split()
        landed[sha] = date
        if len(ps) == 2:
            m = re.search(r"^Merge-request: !(\d+)", body, re.M)
            merges.append((int(m.group(1)) if m else None, ps[0], ps[1], date))
    for n, (mr, first, second, date) in enumerate(merges, 1):
        for sha in git("rev-list", "--no-merges", f"{first}..{second}").split():
            landed.setdefault(sha, date)
            if mr:
                mrs.setdefault(sha, mr)
        if n % 4000 == 0:
            print(f"  {n}/{len(merges)} merges mapped", flush=True)
    return mrs, landed


def function_name(context):
    context = context.strip()
    m = FUNC.search(context)
    if m:
        return m.group(1).split("<")[0]
    m = re.match(r"(?:class|struct|namespace)\s+(\w+)", context)
    return m.group(0) if m else ""


def parse_log():
    cmd = ["git", "-C", REPO, "log", "--no-merges", "-U0", "--no-color", "--no-ext-diff", "--no-textconv",
           "--format=%x01%H%x00%an%x00%ad%x00%s%x00%b%x02", "--date=short", BRANCH]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    cur, header = None, None
    for raw in proc.stdout:
        line = raw.decode("utf-8", "replace")
        if header is not None:
            header += line
            if "\x02" in line:
                cur = start(header)
                header = None
            continue
        if line.startswith("\x01"):
            if cur:
                yield cur
            cur, header = None, line[1:]
            if "\x02" in header:
                cur, header = start(header), None
            continue
        if cur is None:
            continue
        if line.startswith("diff --git "):
            path = line.rstrip("\n").split(" b/", 1)[-1]
            cur["skip"] = bool(SKIP.match(path))
            if not cur["skip"]:
                cur["files"][path] += 0
        elif cur.get("skip"):
            continue
        elif line.startswith("@@"):
            parts = line.split("@@", 2)
            if len(parts) == 3:
                name = function_name(parts[2])
                if name:
                    cur["functions"][name] += 1
        elif line.startswith("+") and not line.startswith("+++"):
            cur["added"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            cur["removed"] += 1
    if cur:
        yield cur
    proc.wait()


def start(header):
    sha, author, date, subject, body = (header.split("\x02")[0].split("\x00") + [""] * 5)[:5]
    return {"sha": sha.strip(), "author": author, "date": date, "subject": subject,
            "body": TRAILER.sub("", body).strip()[:4000], "files": Counter(), "functions": Counter(),
            "added": 0, "removed": 0, "skip": False}


def build(args):
    t0 = time.time()
    print("mapping commits to merge requests", flush=True)
    mrs, landed = merge_requests()
    print(f"  {len(mrs)} commits linked to MRs ({time.time() - t0:.0f}s)", flush=True)
    DB.parent.mkdir(parents=True, exist_ok=True)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript("""
        CREATE TABLE commits (rowid INTEGER PRIMARY KEY, sha TEXT UNIQUE, date TEXT, landed TEXT, author TEXT, subject TEXT,
            body TEXT, files TEXT, functions TEXT, added INTEGER, removed INTEGER, mr INTEGER);
        CREATE VIRTUAL TABLE commits_fts USING fts5(subject, body, files, functions, content='commits',
            content_rowid='rowid', tokenize="unicode61 tokenchars '_:'");
        CREATE INDEX commits_date ON commits(date);
        CREATE INDEX commits_landed ON commits(landed);
        CREATE INDEX commits_mr ON commits(mr);
    """)
    rows = []
    for n, c in enumerate(parse_log(), 1):
        files = [p for p, _ in c["files"].most_common()]
        funcs = [f for f, _ in c["functions"].most_common(60)]
        rows.append((c["sha"], c["date"], landed.get(c["sha"], c["date"]), c["author"], c["subject"], c["body"], json.dumps(files),
                     json.dumps(funcs), c["added"], c["removed"], mrs.get(c["sha"])))
        if len(rows) >= 2000:
            con.executemany("INSERT OR IGNORE INTO commits (sha, date, landed, author, subject, body, files, "
                            "functions, added, removed, mr) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
            rows = []
            print(f"  {n} commits ({time.time() - t0:.0f}s)", flush=True)
    con.executemany("INSERT OR IGNORE INTO commits (sha, date, landed, author, subject, body, files, functions, "
                    "added, removed, mr) VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    con.execute("INSERT INTO commits_fts (rowid, subject, body, files, functions) "
                "SELECT rowid, subject, body, replace(files, '/', ' '), functions FROM commits")
    con.commit()
    total, linked = con.execute("SELECT count(*), count(mr) FROM commits").fetchone()
    print(f"{total} commits indexed, {linked} linked to an MR, in {time.time() - t0:.0f}s")


def document(row):
    files = json.loads(row["files"])
    funcs = json.loads(row["functions"])
    text = f"{row['subject']}\n{row['body'][:800]}"
    if funcs:
        text += "\nChanged: " + ", ".join(funcs[:15])
    if files:
        text += "\nFiles: " + ", ".join(files[:10])
    return text[:2500]


def embed_texts(texts, query=False):
    payload = {"model": MODEL, "input": [INSTRUCT + t if query else t for t in texts], "truncate": True}
    req = urllib.request.Request(HOST + "/api/embed", json.dumps(payload).encode(), {"Content-Type": "application/json"})
    v = np.asarray(json.load(urllib.request.urlopen(req, timeout=600))["embeddings"], np.float32)[:, :DIM]
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def embed(args):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT rowid, subject, body, files, functions FROM commits ORDER BY rowid").fetchall()
    n = len(rows)
    if VECTORS.exists() and PROGRESS.exists() and json.loads(PROGRESS.read_text())["count"] == n:
        vecs = np.load(VECTORS, mmap_mode="r+")
        done = json.loads(PROGRESS.read_text())["done"]
    else:
        vecs = np.lib.format.open_memmap(VECTORS, mode="w+", dtype=np.float16, shape=(n, DIM))
        done = 0
    t0 = time.time()
    while done < n:
        batch = rows[done:done + args.batch]
        vecs[done:done + len(batch)] = embed_texts([document(r) for r in batch]).astype(np.float16)
        done += len(batch)
        if done // args.batch % 20 == 0 or done >= n:
            vecs.flush()
            PROGRESS.write_text(json.dumps({"count": n, "done": done}))
            rate = (done - 0) / max(time.time() - t0, 1)
            print(f"  {done}/{n} embedded", flush=True)
    vecs.flush()
    PROGRESS.write_text(json.dumps({"count": n, "done": done}))


class Commits:
    def __init__(self):
        self.con = sqlite3.connect(DB, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        ready = PROGRESS.exists() and json.loads(PROGRESS.read_text())["done"] == json.loads(PROGRESS.read_text())["count"]
        self.vectors = np.load(VECTORS, mmap_mode="r") if ready else None

    def where(self, until=None, since=None, path=None, function=None):
        clauses, params = [], []
        if until:
            clauses.append("c.landed < ?")
            params.append(until)
        if since:
            clauses.append("c.landed >= ?")
            params.append(since)
        if path:
            clauses.append("c.files LIKE ?")
            params.append(f'%"{path}%')
        if function:
            clauses.append("c.functions LIKE ?")
            params.append(f'%{function}%')
        return (" AND ".join(clauses) or "1"), params

    def search(self, query, k=10, pool=100, **filters):
        cond, params = self.where(**filters)
        terms = " OR ".join(f'"{t}"' for t in re.findall(r"[A-Za-z0-9_:~]{3,}", query)[:20])
        keyword = []
        if terms:
            keyword = [r[0] for r in self.con.execute(
                f"SELECT c.rowid FROM commits_fts f JOIN commits c ON c.rowid = f.rowid WHERE commits_fts MATCH ? "
                f"AND {cond} ORDER BY bm25(commits_fts, 4, 1, 2, 3) LIMIT ?", [terms, *params, pool])]
        meaning = []
        if self.vectors is not None:
            allowed = None
            if filters and any(filters.values()):
                allowed = np.array([r[0] - 1 for r in self.con.execute(f"SELECT c.rowid FROM commits c WHERE {cond}",
                                                                       params)], dtype=np.int64)
            q = embed_texts([query], query=True)[0].astype(np.float32)
            if allowed is None:
                scores = self.vectors @ q.astype(np.float16)
                top = np.argsort(-scores.astype(np.float32))[:pool]
            elif len(allowed):
                scores = self.vectors[allowed].astype(np.float32) @ q
                top = allowed[np.argsort(-scores)[:pool]]
            else:
                top = []
            meaning = [int(i) + 1 for i in top]
        fused = Counter()
        for ranking in (keyword, meaning):
            for rank, rowid in enumerate(ranking):
                fused[rowid] += 1 / (RRF_K + rank)
        out = []
        for rowid, score in fused.most_common(k):
            r = self.con.execute("SELECT * FROM commits WHERE rowid = ?", [rowid]).fetchone()
            out.append({"sha": r["sha"], "date": r["date"], "author": r["author"], "subject": r["subject"],
                        "mr": r["mr"], "files": json.loads(r["files"])[:5], "functions": json.loads(r["functions"])[:8],
                        "score": round(score, 4)})
        return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("build")
    e = sub.add_parser("embed")
    e.add_argument("--batch", type=int, default=64)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("-k", type=int, default=10)
    s.add_argument("--until")
    s.add_argument("--since")
    s.add_argument("--path")
    s.add_argument("--function")
    args = p.parse_args()
    if args.cmd == "build":
        build(args)
    elif args.cmd == "embed":
        embed(args)
    else:
        for r in Commits().search(args.query, args.k, until=args.until, since=args.since, path=args.path,
                                  function=args.function):
            mr = f" !{r['mr']}" if r["mr"] else ""
            print(f"{r['date']} {r['sha'][:11]}{mr} {r['author']}: {r['subject']}\n    {', '.join(r['functions'][:5])}"
                  f" | {', '.join(r['files'][:3])}")


if __name__ == "__main__":
    main()
