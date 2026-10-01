"""A Discourse topic as one conversation, with what it links to and what links back to it."""

import html
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ROOT / "data/discourse-history/topics"
MIRROR = ROOT / "data/vtk-history"
BLOG = ROOT / "data/blog-history/posts"
BLOG_LINK = re.compile(r"(https?://(?:www\.)?kitware\.com/[\w-]+/?)")
_blog_titles = None


def blog_titles():
    global _blog_titles
    if _blog_titles is None:
        _blog_titles = {}
        for f in BLOG.glob("*.json"):
            b = json.loads(f.read_text())
            _blog_titles[b["link"].rstrip("/")] = html.unescape(b["title"])
    return _blog_titles


def gitlab_title(kind, num):
    path = MIRROR / kind / f"{num}.json"
    if not path.exists():
        return ""
    rec = json.loads(path.read_text())
    return (rec.get("merge_request") or rec.get("issue") or rec).get("title", "")
INDEX = ROOT / "data/index/docs.sqlite"
GITLAB = re.compile(r"gitlab\.kitware\.com/vtk/vtk/(?:-/)?(merge_requests|issues)/(\d+)")
FORUM = re.compile(r"discourse\.vtk\.org/t/(?:[^/\s\"'<>]+/)?(\d+)")
KIND_LABEL = {"mr": "merge request", "thread": "review thread", "issue": "issue", "blog": "blog post",
              "note": "release note", "doc": "documentation"}


def readable(cooked):
    """Discourse HTML as plain text that keeps paragraphs, list items, and code blocks."""
    text = re.sub(r"(?is)<pre[^>]*>(.*?)</pre>", lambda m: "\n" + m.group(1) + "\n", cooked)
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|h\d|blockquote)>", "\n\n", text)
    text = re.sub(r"(?i)<li[^>]*>", "\n- ", text)
    text = re.sub(r"(?is)<aside.*?</aside>", "", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def topic(tid):
    path = TOPICS / f"{int(tid)}.json"
    if not path.exists():
        return None
    t = json.loads(path.read_text())
    meta = t["topic"]
    posts, outgoing = [], {}
    for p in t["posts"]:
        if p.get("post_type", 1) != 1:
            continue
        for kind, num in GITLAB.findall(p["cooked"]):
            label = ("!" if kind == "merge_requests" else "#") + num
            if label not in outgoing:
                outgoing[label] = {"label": label, "kind": "merge request" if kind == "merge_requests" else "issue",
                                   "url": f"https://gitlab.kitware.com/vtk/vtk/-/{kind}/{num}",
                                   "title": gitlab_title(kind, num)}
        for url in BLOG_LINK.findall(p["cooked"]):
            title = blog_titles().get(url.rstrip("/"))
            if title:
                outgoing[url] = {"label": title[:70], "kind": "blog post", "url": url, "title": ""}
        for other in FORUM.findall(p["cooked"]):
            if int(other) != int(tid):
                outgoing[f"topic {other}"] = {"label": f"topic {other}", "kind": "forum topic",
                                              "url": f"https://discourse.vtk.org/t/{other}", "title": "", "topic": int(other)}
        posts.append({"n": p["post_number"], "author": p.get("name") or p["username"], "user": p["username"],
                      "date": p["created_at"][:10], "accepted": bool(p.get("accepted_answer")),
                      "staff": bool(p.get("staff")), "reply_to": p.get("reply_to_post_number"),
                      "text": readable(p["cooked"])})
    return {"id": meta["id"], "title": html.unescape(meta["title"]), "url": t.get("url") or f"https://discourse.vtk.org/t/{tid}",
            "created": (meta.get("created_at") or "")[:10], "posts": posts,
            "outgoing": sorted(outgoing.values(), key=lambda x: x["label"]), "incoming": incoming(int(tid))}


def incoming(tid):
    """Items in the search index (MRs, review threads, issues, blog posts, docs) whose text cites this topic."""
    if not INDEX.exists():
        return []
    con = sqlite3.connect(f"file:{INDEX}?mode=ro", uri=True)
    rows = con.execute("SELECT kind, ref, url, date, title, text FROM docs WHERE kind != 'post' AND text LIKE ?",
                       (f"%discourse.vtk.org/t/%{tid}%",)).fetchall()
    out, seen = [], set()
    for kind, ref, url, date, title, text in rows:
        if tid not in {int(x) for x in FORUM.findall(text)} or (kind, ref) in seen:
            continue
        seen.add((kind, ref))
        if ref and ref.startswith("!"):
            url = f"https://gitlab.kitware.com/vtk/vtk/-/merge_requests/{ref[1:]}"
        elif ref and ref.startswith("#"):
            url = f"https://gitlab.kitware.com/vtk/vtk/-/issues/{ref[1:]}"
        out.append({"label": ref if ref and ref != "blog" else (title or "")[:60], "kind": KIND_LABEL.get(kind, kind),
                    "url": url, "title": title or "", "date": date or ""})
    return sorted(out, key=lambda x: x["date"])
