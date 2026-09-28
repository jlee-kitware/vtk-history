#!/usr/bin/env python3
"""Mirror a Discourse forum's public topics into a git repository.

Each topic is stored as one JSON file with its metadata and all of its posts:

  <out>/topics/<id>.json

Requests are anonymous, so only public categories are mirrored. Topics are listed
from /latest.json (most recently active first). A sync fetches every topic active
since the previous sync and skips topics whose saved copy is already current.

Posts on discourse.vtk.org are licensed CC BY-NC-SA 3.0 (terms of service, section 3);
each file records that license.

Usage:
  python mirror/discourse_mirror.py sync --limit 5
  python mirror/discourse_mirror.py sync
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

LICENSE = "CC BY-NC-SA 3.0 (https://creativecommons.org/licenses/by-nc-sa/3.0/)"
POSTS_PER_REQUEST = 20
POST_FIELDS = ("id", "post_number", "username", "name", "created_at", "updated_at", "reply_to_post_number",
               "cooked", "accepted_answer", "staff", "post_type", "reads", "score")


class Discourse:
    def __init__(self, url, delay):
        self.url = url.rstrip("/")
        self.delay = delay
        self.requests = 0
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "kitware-history-mirror/0.3 (contact: jeff.lee@kitware.com)"

    def get(self, path, params=None):
        dropped = 0
        while True:
            time.sleep(self.delay)
            self.requests += 1
            try:
                r = self.session.get(self.url + path, params=params, timeout=120)
            except (requests.ConnectionError, requests.Timeout) as e:
                dropped += 1
                if dropped > 5:
                    raise
                print(f"  connection error on {path} ({type(e).__name__}); retrying in {60 * dropped}s", file=sys.stderr)
                time.sleep(60 * dropped)
                continue
            if r.status_code == 429 or r.status_code >= 500:
                wait = int(r.headers.get("Retry-After", 120))
                print(f"  HTTP {r.status_code} on {path}; waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if r.status_code in (403, 404, 410, 422):
                if r.status_code == 422:
                    print(f"  HTTP 422 on {path}; skipped", file=sys.stderr)
                return None
            r.raise_for_status()
            return r.json()

    def latest(self):
        page = 0
        while True:
            data = self.get("/latest.json", {"no_definitions": "true", "page": page})
            topics = (data or {}).get("topic_list", {}).get("topics", [])
            if not topics:
                return
            yield from topics
            page += 1

    def topic(self, topic_id):
        data = self.get(f"/t/{topic_id}.json")
        if not data:
            return None
        posts = data["post_stream"]["posts"]
        stream = data["post_stream"].get("stream", [])
        if len(posts) < len(stream):
            have = {p["id"] for p in posts}
            missing = [pid for pid in stream if pid not in have]
            for i in range(0, len(missing), POSTS_PER_REQUEST):
                extra = self.get(f"/t/{topic_id}/posts.json", {"post_ids[]": missing[i:i + POSTS_PER_REQUEST]})
                posts += (extra or {}).get("post_stream", {}).get("posts", [])
        posts.sort(key=lambda p: p["post_number"])
        return {
            "topic": {k: data.get(k) for k in ("id", "title", "slug", "category_id", "tags", "created_at",
                                               "last_posted_at", "bumped_at", "posts_count", "views",
                                               "closed", "archived", "accepted_answer")},
            "url": f"{self.url}/t/{data.get('slug')}/{topic_id}",
            "license": LICENSE,
            "posts": [{k: p.get(k) for k in POST_FIELDS} for p in posts],
        }


def write_json(path, record):
    path.write_text(json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["sync"])
    p.add_argument("--url", default="https://discourse.vtk.org")
    p.add_argument("--out", default="data/discourse-history")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    p.add_argument("--limit", type=int, default=0, help="stop after N topics (trial run)")
    p.add_argument("--no-commit", action="store_true")
    args = p.parse_args()

    d = Discourse(args.url, args.delay)
    out = Path(args.out)
    (out / "topics").mkdir(parents=True, exist_ok=True)
    if not (out / ".git").exists():
        git(out, "init", "-q", "-b", "main")
    state_file = out / "sync.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    since = state.get("bumped_after")
    started = datetime.now(timezone.utc).isoformat()

    categories = d.get("/categories.json", {"include_subcategories": "true"})
    if categories:
        write_json(out / "categories.json", categories.get("category_list", {}).get("categories", []))
    print(f"Syncing {args.url} into {out}/ ({'topics active since ' + since if since else 'all public topics'}), "
          f"{args.delay}s between requests")

    fetched = skipped = 0
    for t in d.latest():
        if since and t["bumped_at"] < since and not (t.get("pinned") or t.get("pinned_globally")):
            break
        path = out / "topics" / f"{t['id']}.json"
        if path.exists() and json.loads(path.read_text())["topic"].get("bumped_at") == t["bumped_at"]:
            skipped += 1
            continue
        record = d.topic(t["id"])
        if record:
            record["topic"]["bumped_at"] = t["bumped_at"]
            write_json(path, record)
            fetched += 1
        if fetched and fetched % 50 == 0:
            print(f"  {fetched} topics, {d.requests} requests (last {t['id']}, active {t['bumped_at']})")
        if args.limit and fetched >= args.limit:
            break
    print(f"topics: {fetched} written, {skipped} already current, {d.requests} requests")

    if args.limit:
        print("Trial run: sync point not saved.")
        return
    write_json(state_file, {"url": args.url, "bumped_after": started})
    if not args.no_commit:
        git(out, "add", "-A")
        if subprocess.run(["git", "-C", str(out), "diff", "--cached", "--quiet"]).returncode:
            git(out, "commit", "-q", "-m", f"Sync {args.url} through {started} ({fetched} topics)")
            print("Committed.")


if __name__ == "__main__":
    main()
