#!/usr/bin/env python3
"""Mirror a GitLab project's merge request and issue discussions into a git repository.

Each merge request and issue is stored as one JSON file holding the item and all of
its public discussion threads, including line-level review comments with their
diff positions:

  <out>/merge_requests/<iid>.json
  <out>/issues/<iid>.json

Code does not come from the API. Fetch every merge request's head into a local clone
with --repo, and reconstruct diffs from the base_sha/head_sha recorded on each review
comment. Links between issues and merge requests are parsed from the text later.
That leaves one API call per item (more only for very long threads).

A sync asks GitLab which items changed since the last sync and refetches their full
discussions. An interrupted sync resumes where it stopped. The output directory is a
git repository with one commit per completed sync.

The token must come from an account with no project or group memberships, so it sees
only public content. The script refuses a token that can see private content.

Usage:
  export GITLAB_TOKEN=...
  python mirror/gitlab_mirror.py count
  python mirror/gitlab_mirror.py sync --limit 200
  python mirror/gitlab_mirror.py sync --repo $VTK_REPO
  python mirror/gitlab_mirror.py files            # changed files of MRs with no commits on master
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


class GitLab:
    def __init__(self, url, token, delay):
        self.api = url.rstrip("/") + "/api/v4"
        self.delay = delay
        self.requests = 0
        self.session = requests.Session()
        self.session.headers.update({
            "PRIVATE-TOKEN": token,
            "User-Agent": "kitware-history-mirror/0.3 (contact: jeff.lee@kitware.com)",
        })

    def get(self, path, params=None):
        dropped = 0
        while True:
            time.sleep(self.delay)
            self.requests += 1
            try:
                r = self.session.get(self.api + path, params=params, timeout=120)
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
            r.raise_for_status()
            return r

    def paged(self, path, params=None):
        params = dict(params or {}, per_page=100, page=1)
        while True:
            r = self.get(path, params)
            yield from r.json()
            next_page = r.headers.get("X-Next-Page")
            if not next_page:
                return
            params["page"] = int(next_page)

    def total(self, path, params=None):
        r = self.get(path, dict(params or {}, per_page=1))
        return r.headers.get("X-Total") or "more than 10,000 (GitLab omits exact totals above that)"


def mr_files(gl, pid, out, commits_db):
    """Changed file paths of merge requests that have no commits on master (closed, open, or merged into
    another branch), one JSON list per MR in <out>/mr_files/. GitLab removes the branch refs of closed
    MRs, so the API is the only source for most of them."""
    import sqlite3
    on_master = {m for (m,) in sqlite3.connect(commits_db).execute(
        "SELECT DISTINCT mr FROM commits WHERE mr IS NOT NULL")} if commits_db.exists() else set()
    target = out / "mr_files"
    target.mkdir(exist_ok=True)
    todo = sorted(int(p.stem) for p in (out / "merge_requests").glob("*.json")
                  if int(p.stem) not in on_master and not (target / p.name).exists())
    print(f"{len(todo)} merge requests without commits on master")
    for n, iid in enumerate(todo, 1):
        try:
            paths = sorted({d["new_path"] for d in gl.paged(f"/projects/{pid}/merge_requests/{iid}/diffs")}
                           )
        except requests.HTTPError as e:
            if e.response is None or e.response.status_code != 404:
                raise
            paths = []
        (target / f"{iid}.json").write_text(json.dumps(paths))
        if n % 100 == 0:
            print(f"  {n}/{len(todo)} ({gl.requests} requests)", flush=True)


def public_discussions(discussions):
    kept = []
    for d in discussions:
        notes = [n for n in d.get("notes", []) if not n.get("internal") and not n.get("confidential")]
        if notes:
            kept.append({**d, "notes": notes})
    return kept


def write_json(path, record):
    path.write_text(json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def fetch(gl, pid, kind, item):
    discussions = public_discussions(gl.paged(f"/projects/{pid}/{kind}/{item['iid']}/discussions"))
    key = "merge_request" if kind == "merge_requests" else "issue"
    return {key: item, "discussions": discussions}


def sync_kind(gl, pid, out, kind, since, limit, state, state_file):
    folder = out / kind
    folder.mkdir(exist_ok=True)
    resume = state.setdefault("resume", {}).get(kind)
    params = {"state": "all", "order_by": "updated_at", "sort": "asc"}
    if resume or since:
        params["updated_after"] = resume or since
    if kind == "issues":
        params["confidential"] = "false"
    print(f"{kind}: {'resuming from ' + resume if resume else 'starting'}")

    n = 0
    for item in gl.paged(f"/projects/{pid}/{kind}", params):
        write_json(folder / f"{item['iid']}.json", fetch(gl, pid, kind, item))
        n += 1
        if n % 25 == 0:
            if not limit:
                state["resume"][kind] = item["updated_at"]
                write_json(state_file, state)
            print(f"  {n} {kind}, {gl.requests} requests (last {item['iid']}, updated {item['updated_at']})")
        if limit and n >= limit:
            break
    print(f"{kind}: {n} written")
    return n


def count(gl, pid):
    print("Merge requests (all):   ", gl.total(f"/projects/{pid}/merge_requests", {"state": "all"}))
    print("Merge requests (merged):", gl.total(f"/projects/{pid}/merge_requests", {"state": "merged"}))
    print("Issues (public):        ", gl.total(f"/projects/{pid}/issues", {"state": "all", "confidential": "false"}))

    sample = gl.get(f"/projects/{pid}/merge_requests",
                    {"state": "merged", "order_by": "updated_at", "per_page": 50}).json()
    comments, line_comments = [], []
    for mr in sample:
        notes = [n for d in gl.paged(f"/projects/{pid}/merge_requests/{mr['iid']}/discussions")
                 for n in d["notes"] if not n.get("system")]
        comments.append(len(notes))
        line_comments.append(sum(1 for n in notes if n.get("type") == "DiffNote"))
    print(f"Sample of {len(sample)} recent merged MRs: "
          f"{sum(comments) / len(sample):.1f} human comments per MR, "
          f"{sum(line_comments) / len(sample):.1f} line-level review comments per MR, "
          f"{sum(1 for c in comments if c >= 3)} MRs with 3 or more comments")


def check_no_membership(project):
    perms = project.get("permissions") or {}
    if perms.get("project_access") or perms.get("group_access"):
        sys.exit("This token's account is a member of the project and can see private content.\n"
                 "Create a token from an account with no memberships, so the mirror holds only public data.")


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True)


def fetch_mr_refs(repo, remote):
    print(f"Fetching merge request heads into {repo} (refs/remotes/{remote}/mr/*)")
    git(repo, "fetch", "--quiet", remote, f"+refs/merge-requests/*/head:refs/remotes/{remote}/mr/*")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["count", "sync", "files"])
    p.add_argument("--url", default="https://gitlab.kitware.com")
    p.add_argument("--project", default="vtk/vtk")
    p.add_argument("--commits", default="data/index/commits.sqlite", help="commit index, for the files mode")
    p.add_argument("--out", default="data/vtk-history")
    p.add_argument("--repo", help="local clone to fetch merge request heads into")
    p.add_argument("--remote", default="upstream", help="remote in --repo that points at the upstream project")
    p.add_argument("--delay", type=float, default=1.0, help="seconds between requests")
    p.add_argument("--limit", type=int, default=0, help="stop after N merge requests and N issues (trial run)")
    p.add_argument("--since", help="ISO timestamp; overrides the saved sync point")
    p.add_argument("--no-commit", action="store_true", help="write files without committing")
    args = p.parse_args()

    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        sys.exit("Set GITLAB_TOKEN to a read_api token from an account with no project memberships.\n"
                 "GitLab does not serve discussions to anonymous requests.")

    gl = GitLab(args.url, token, args.delay)
    pid = quote(args.project, safe="")
    project = gl.get(f"/projects/{pid}").json()
    print(f"Project: {project['path_with_namespace']} (id {project['id']})")
    check_no_membership(project)

    if args.mode == "count":
        count(gl, pid)
        print(f"{gl.requests} requests")
        return
    if args.mode == "files":
        mr_files(gl, pid, Path(args.out), Path(args.commits))
        print(f"{gl.requests} requests")
        return

    if args.repo:
        fetch_mr_refs(args.repo, args.remote)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not (out / ".git").exists():
        git(out, "init", "-q", "-b", "main")

    state_file = out / "sync.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    state["project"] = project["path_with_namespace"]
    since = args.since or state.get("updated_after")
    started = datetime.now(timezone.utc).isoformat()
    print(f"Syncing into {out}/ ({'changes since ' + since if since else 'full history'}), "
          f"{args.delay}s between requests")

    changed = sum(sync_kind(gl, pid, out, kind, since, args.limit, state, state_file)
                  for kind in ("merge_requests", "issues"))
    print(f"{gl.requests} requests")

    if args.limit:
        print("Trial run: sync point not saved.")
        return
    state["updated_after"] = started
    state.pop("resume", None)
    write_json(state_file, state)

    if not args.no_commit:
        git(out, "add", "-A")
        if subprocess.run(["git", "-C", str(out), "diff", "--cached", "--quiet"]).returncode:
            git(out, "commit", "-q", "-m", f"Sync {project['path_with_namespace']} through {started} ({changed} items)")
            print("Committed.")
        else:
            print("No changes.")


if __name__ == "__main__":
    main()
