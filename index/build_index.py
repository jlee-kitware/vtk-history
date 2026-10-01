#!/usr/bin/env python3
"""Build the search index over VTK review threads, MRs, issues, Discourse posts, and Kitware blog posts.

Each searchable unit becomes one row in data/index/docs.sqlite, with an FTS5 full-text
index for exact identifiers, and one embedding row in data/index/vectors.npy for
meaning-based search. Units:

  thread   one review discussion (line, general, or legacy), with its file, module, class
  mr       one merge request's title and description
  issue    one issue's title, description, and discussion
  post     one Discourse post, with its topic title
  doc      one section of a VTK design document, guide, file format spec, or README (index/docs.py)
  note     one release note as its author wrote it, linked to the MR that added it
  class    the Doxygen description of one VTK class
  blog     one section of a Kitware blog post that mentions VTK (mirror/blog_mirror.py)

Embeddings come from qwen3-embedding, truncated to --dim dimensions (the model is trained
so that leading dimensions stand alone) and stored as float16. The embedding cache is
saved as it goes, so an interrupted build resumes. MR embeddings are reused from the theme
discovery cache when present.

Usage:
  python index/build_index.py              # rows, full text, and embeddings
  python index/build_index.py --no-embed   # rows and full text only
"""

import argparse
import glob
import html
import json
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import docs  # noqa: E402

HOST = "http://192.168.50.23:11435"
EMBED_CHARS = 2000
BATCH = 32
SKIP_KINDS = {"approval"}


BLOG_CHARS = 3000


def about_vtk(title, body):
    return "VTK" in title or len(re.findall(r"\bVTK\b", body)) >= 2


def blog_units(blog):
    """Posts about VTK (named in the title or at least twice in the text), each split at its headings into
    sections of up to BLOG_CHARS, small sections merged."""
    for f in sorted(glob.glob(f"{blog}/posts/*.json")):
        b = json.load(open(f))
        title = html.unescape(b["title"])
        if not about_vtk(title, strip_html(b["content"])):
            continue
        parts = re.split(r"(?i)<h[2-4][^>]*>(.*?)</h[2-4]>", b["content"])
        sections = [("", parts[0])] + [(strip_html(parts[i]), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]
        chunks, heading, text = [], "", ""
        for head, body in sections:
            body = strip_html(body)
            if text and len(text) + len(body) > BLOG_CHARS:
                chunks.append((heading, text))
                heading, text = head, ""
            heading = heading or head
            text = f"{text}\n\n{head}\n{body}".strip() if head else f"{text}\n\n{body}".strip()
        if text:
            chunks.append((heading, text))
        for n, (head, text) in enumerate(chunks):
            if len(text) < 80:
                continue
            full = f"{title}" + (f": {head}" if head else "") + f"\n\n{text}"
            yield {"id": f"blog:{b['id']}/{n}", "kind": "blog", "ref": "blog", "url": b["link"],
                   "date": b["date"][:10], "author": "Kitware blog", "path": None, "module": None, "class": None,
                   "title": title + (f": {head}" if head else ""), "text": full, "embed_text": full[:EMBED_CHARS]}


def post(path, payload, timeout=600):
    for attempt in range(5):
        try:
            req = urllib.request.Request(HOST + path, json.dumps(payload).encode(), {"Content-Type": "application/json"})
            return json.load(urllib.request.urlopen(req, timeout=timeout))
        except OSError as e:
            print(f"  {path} failed ({e}); retrying", file=sys.stderr)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError(f"{path} failed after retries")


def strip_html(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s or "")).split())


def threads(examples):
    for line in open(examples):
        ex = json.loads(line)
        if ex["kind"] in SKIP_KINDS:
            continue
        mr, code = ex["mr"], ex.get("code") or {}
        comments = "\n".join(f"{n['author']}: {n['body']}" for n in ex["thread"])
        where = f"File: {code['path']} ({code.get('class') or code.get('module') or ''})\n" if code.get("path") else ""
        context = f"Code:\n{code['context']}\n" if code.get("context") else ""
        text = f"MR !{mr['iid']}: {mr['title']}\n{where}{comments}"
        yield {
            "id": f"thread:{ex['discussion_id']}", "kind": "thread", "ref": f"!{mr['iid']}", "url": mr.get("web_url"),
            "date": ex["thread"][0]["created_at"][:10], "author": ex["reviewer"], "path": code.get("path"),
            "module": code.get("module"), "class": code.get("class"), "title": mr["title"],
            "text": text, "embed_text": (text + "\n" + context)[:EMBED_CHARS],
        }


def mrs(mirror):
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        mr = json.load(open(f))["merge_request"]
        desc = mr.get("description") or ""
        yield {
            "id": f"mr:{mr['iid']}", "kind": "mr", "ref": f"!{mr['iid']}", "url": mr.get("web_url"),
            "date": mr["created_at"][:10], "author": mr["author"]["username"], "path": None, "module": None,
            "class": None, "title": mr["title"], "text": f"{mr['title']}\n\n{desc}",
            "embed_text": f"{mr['title']}\n\n{desc[:1500]}", "cache_key": f"mr:{mr['iid']}",
        }


def issues(mirror):
    for f in glob.glob(f"{mirror}/issues/*.json"):
        record = json.load(open(f))
        issue = record["issue"]
        notes = [n for d in record.get("discussions") or [] for n in d.get("notes", []) if not n.get("system")]
        body = "\n".join(f"{n['author']['username']}: {n['body']}" for n in notes)
        text = f"Issue #{issue['iid']}: {issue['title']}\n\n{issue.get('description') or ''}\n{body}"
        yield {
            "id": f"issue:{issue['iid']}", "kind": "issue", "ref": f"#{issue['iid']}", "url": issue.get("web_url"),
            "date": issue["created_at"][:10], "author": issue["author"]["username"], "path": None, "module": None,
            "class": None, "title": issue["title"], "text": text, "embed_text": text[:EMBED_CHARS],
        }


def posts(discourse):
    for f in glob.glob(f"{discourse}/topics/*.json"):
        t = json.load(open(f))
        topic = t["topic"]
        for p in t["posts"]:
            body = strip_html(p["cooked"])
            if len(body) < 40:
                continue
            text = f"{topic['title']}\n\n{p['username']}: {body}"
            yield {
                "id": f"post:{topic['id']}/{p['post_number']}", "kind": "post", "ref": f"topic {topic['id']}",
                "url": f"{t['url']}/{p['post_number']}", "date": p["created_at"][:10], "author": p["username"],
                "path": None, "module": None, "class": None, "title": topic["title"], "text": text,
                "embed_text": text[:EMBED_CHARS],
            }


def merge_commits(mirror):
    by_sha = {}
    for f in glob.glob(f"{mirror}/merge_requests/*.json"):
        mr = json.load(open(f))["merge_request"]
        for key in ("merge_commit_sha", "squash_commit_sha"):
            if mr.get(key):
                by_sha[mr[key]] = mr["iid"]
    return by_sha


def write_rows(rows, path):
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE docs (rowid INTEGER PRIMARY KEY, id TEXT UNIQUE, kind TEXT, ref TEXT, url TEXT, date TEXT,
                           author TEXT, path TEXT, module TEXT, class TEXT, title TEXT, text TEXT);
        CREATE INDEX docs_kind_date ON docs(kind, date);
        CREATE VIRTUAL TABLE docs_fts USING fts5(title, text, path, class, content='docs', content_rowid='rowid',
                                                 tokenize="unicode61 tokenchars '_'");
    """)
    con.executemany(
        "INSERT INTO docs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        [(i + 1, r["id"], r["kind"], r["ref"], r["url"], r["date"], r["author"], r["path"], r["module"], r["class"],
          r["title"], r["text"]) for i, r in enumerate(rows)])
    con.execute("INSERT INTO docs_fts(docs_fts) VALUES ('rebuild')")
    con.commit()
    con.close()


def load_cache(path):
    if not path.exists():
        return {}
    data = np.load(path, allow_pickle=True).item()
    return dict(zip(data["ids"], data["vectors"]))


def save_cache(path, cache):
    np.save(path, {"ids": list(cache), "vectors": list(cache.values())})


def reduce(vectors, dim):
    v = np.asarray(vectors, dtype=np.float32)[:, :dim]
    return (v / np.linalg.norm(v, axis=1, keepdims=True)).astype(np.float16)


def embed_rows(rows, model, dim, cache_path, theme_cache):
    cache = load_cache(cache_path)
    reused = 0
    if theme_cache.exists():
        themes = load_cache(theme_cache)
        for r in rows:
            k = r.get("cache_key")
            if k and r["id"] not in cache and k in themes:
                cache[r["id"]] = reduce([themes[k]], dim)[0]
                reused += 1
    todo = [r for r in rows if r["id"] not in cache]
    print(f"embedding {len(todo)} units ({len(rows) - len(todo) - reused} cached, {reused} reused from themes)", flush=True)
    start = time.time()
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        vecs = post("/api/embed", {"model": model, "input": [r["embed_text"] for r in batch], "truncate": True})["embeddings"]
        cache.update(zip((r["id"] for r in batch), reduce(vecs, dim)))
        done = i + len(batch)
        if (i // BATCH) % 200 == 0 or done == len(todo):
            save_cache(cache_path, cache)
            rate = done / max(1e-9, time.time() - start)
            print(f"  {done}/{len(todo)} ({batch[0]['kind']}), {rate:.1f}/s, {(len(todo) - done) / rate / 60:.0f} min left",
                  flush=True)
    save_cache(cache_path, cache)
    return np.stack([cache.get(r["id"], np.zeros(dim, np.float16)) for r in rows])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--examples", default="data/review_examples.jsonl")
    p.add_argument("--mirror", default="data/vtk-history")
    p.add_argument("--discourse", default="data/discourse-history")
    p.add_argument("--blog", default="data/blog-history")
    p.add_argument("--embed-model", default="qwen3-embedding:latest")
    p.add_argument("--dim", type=int, default=1024)
    p.add_argument("--theme-cache", default="data/trends/doc_embeddings.npy")
    p.add_argument("--out", default="data/index")
    p.add_argument("--no-embed", action="store_true")
    p.add_argument("--no-docs", action="store_true", help="leave out VTK documentation, release notes, and class docs")
    p.add_argument("--vtk-repo", default="/home/jlee/gitsync/vtk")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(threads(args.examples)) + list(issues(args.mirror)) + list(posts(args.discourse)) + list(mrs(args.mirror))
    rows += list(blog_units(args.blog))
    if not args.no_docs:
        mr_by_sha = merge_commits(args.mirror)
        ref = next(r for r in ("upstream/master", "origin/master", "master")
                   if subprocess.run(["git", "-C", args.vtk_repo, "rev-parse", "--verify", "-q", r],
                                     capture_output=True).returncode == 0)
        rows += list(docs.doc_units(args.vtk_repo, ref, mr_by_sha))
        rows += list(docs.note_units(args.vtk_repo, ref, mr_by_sha))
        rows += list(docs.class_units(args.vtk_repo, ref, mr_by_sha))
        for r in rows:
            if r["kind"] == "note" and r.get("mr"):
                r["url"] = f"https://gitlab.kitware.com/vtk/vtk/-/merge_requests/{r['mr']}"
    counts = {k: sum(1 for r in rows if r["kind"] == k) for k in ("thread", "issue", "post", "mr", "doc", "note", "class", "blog")}
    print(f"{len(rows)} units: {counts}", flush=True)
    write_rows(rows, out / "docs.sqlite")
    print(f"wrote {out / 'docs.sqlite'}", flush=True)
    if args.no_embed:
        return
    vectors = embed_rows(rows, args.embed_model, args.dim, out / "embed_cache.npy", Path(args.theme_cache))
    np.save(out / "vectors.npy", vectors)
    json.dump({"model": args.embed_model, "dim": args.dim, "count": len(rows)}, open(out / "meta.json", "w"))
    print(f"wrote {out / 'vectors.npy'} {vectors.shape}", flush=True)


if __name__ == "__main__":
    main()
