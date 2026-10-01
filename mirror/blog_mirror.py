#!/usr/bin/env python3
"""Mirror Kitware blog posts that mention VTK, through the site's public WordPress API.

Each post is stored as one JSON file with its title, dates, link, categories, tags, and HTML content:

  <out>/posts/<id>.json

A sync lists posts matching --search (default VTK) modified since the previous sync, 100 per request,
one request per second. Posts are Kitware's public content (copyright Kitware, Inc.), mirrored for search.

Usage:
  python mirror/blog_mirror.py sync
  python mirror/blog_mirror.py sync --full
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
API = "https://www.kitware.com/wp-json/wp/v2"
FIELDS = "id,date_gmt,modified_gmt,link,title,excerpt,content,categories,tags,author"


def get(session, path, params, delay):
    for attempt in range(5):
        time.sleep(delay)
        try:
            r = session.get(API + path, params=params, timeout=120)
        except (requests.ConnectionError, requests.Timeout) as e:
            print(f"  connection error ({type(e).__name__}); retrying", file=sys.stderr)
            time.sleep(30 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(int(r.headers.get("Retry-After", 60)))
            continue
        r.raise_for_status()
        return r
    raise RuntimeError(f"gave up on {path}")


def sync(out, search, full, delay):
    out.mkdir(parents=True, exist_ok=True)
    (out / "posts").mkdir(exist_ok=True)
    state_path = out / "sync.json"
    state = json.loads(state_path.read_text()) if state_path.exists() and not full else {}
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    session = requests.Session()
    session.headers["User-Agent"] = "kitware-history-mirror/0.3 (contact: jeff.lee@kitware.com)"
    tags = {t["id"]: t["name"] for t in get(session, "/tags", {"per_page": 100, "search": search, "_fields": "id,name"},
                                             delay).json()}
    params = {"search": search, "per_page": 100, "orderby": "modified", "order": "desc", "_fields": FIELDS}
    if state.get("modified_after"):
        params["modified_after"] = state["modified_after"]
    page, written = 1, 0
    while True:
        r = get(session, "/posts", dict(params, page=page), delay)
        posts = r.json()
        for p in posts:
            record = {"id": p["id"], "title": p["title"]["rendered"], "link": p["link"], "date": p["date_gmt"],
                      "modified": p["modified_gmt"], "categories": p["categories"], "tags": p["tags"],
                      "excerpt": p["excerpt"]["rendered"], "content": p["content"]["rendered"],
                      "license": "Copyright Kitware, Inc.; public blog post mirrored for search"}
            (out / "posts" / f"{p['id']}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))
            written += 1
        total_pages = int(r.headers.get("X-WP-TotalPages", 1))
        print(f"  page {page}/{total_pages}: {len(posts)} posts", flush=True)
        if page >= total_pages:
            break
        page += 1
    state.update(modified_after=started, search=search, vtk_tags=tags)
    state_path.write_text(json.dumps(state, indent=1))
    print(f"{written} posts written; {len(list((out / 'posts').glob('*.json')))} in the mirror")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["sync"])
    ap.add_argument("--out", default=str(ROOT / "data/blog-history"))
    ap.add_argument("--search", default="VTK")
    ap.add_argument("--full", action="store_true", help="ignore the previous sync point")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()
    sync(Path(args.out), args.search, args.full, args.delay)


if __name__ == "__main__":
    main()
