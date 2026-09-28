#!/usr/bin/env python3
"""Mirror a GitLab project's merge request and issue history into a git repository.

Each merge request and issue is stored as one JSON file:

  <out>/merge_requests/<iid>.json
  <out>/issues/<iid>.json

A sync asks GitLab which items changed since the last sync, refetches each changed
item's full history, and overwrites its file. The output directory is a git
repository, so each sync is a commit and the repository can be published as-is.

Use a token from an account with no project or group memberships. Such an account
sees only what an anonymous visitor sees, so confidential issues and internal
notes cannot leak into the mirror. The script refuses to run with a token that has
membership access to the project.

Usage:
  export GITLAB_TOKEN=...          # read_api scope, from a no-membership account
  python mirror/gitlab_mirror.py count
  python mirror/gitlab_mirror.py sync --out data/vtk-history --limit 200
  python mirror/gitlab_mirror.py sync --out data/vtk-history
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
        self.session = requests.Session()
        self.session.headers.update({
            "PRIVATE-TOKEN": token,
            "User-Agent": "kitware-history-mirror/0.2",
        })

    def get(self, path, params=None):
        while True:
            time.sleep(self.delay)
            r = self.session.get(self.api + path, params=params, timeout=120)
            if r.status_code == 429 or r.status_code >= 500:
                wait = int(r.headers.get("Retry-After", 60))
                print(f"  HTTP {r.status_code} on {path}; waiting {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r

    def get_json(self, path, params=None, default=None):
        try:
            return self.get(path, params).json()
        except requests.HTTPError as e:
            if default is not None and e.response.status_code in (403, 404):
                return default
            raise

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


def public_discussions(discussions):
    kept = []
    for d in discussions:
        notes = [n for n in d.get("notes", []) if not n.get("internal") and not n.get("confidential")]
        if notes:
            kept.append({**d, "notes": notes})
    return kept


def write_record(path, record):
    path.write_text(json.dumps(record, indent=1, sort_keys=True, ensure_ascii=False) + "\n")


def fetch_merge_request(gl, pid, mr, all_versions):
    base = f"/projects/{pid}/merge_requests/{mr['iid']}"
    versions = list(gl.paged(base + "/versions"))
    wanted = versions if all_versions else ([versions[-1], versions[0]] if len(versions) > 1 else versions)
    return {
        "merge_request": mr,
        "discussions": public_discussions(gl.paged(base + "/discussions")),
        "versions": versions,
        "version_diffs": {str(v["id"]): gl.get_json(f"{base}/versions/{v['id']}", default={}) for v in wanted},
        "commits": list(gl.paged(base + "/commits")),
        "closes_issues": list(gl.paged(base + "/closes_issues")),
        "approvals": gl.get_json(base + "/approvals", default={}),
    }


def fetch_issue(gl, pid, issue):
    base = f"/projects/{pid}/issues/{issue['iid']}"
    return {
        "issue": issue,
        "discussions": public_discussions(gl.paged(base + "/discussions")),
        "related_merge_requests": list(gl.paged(base + "/related_merge_requests")),
    }


def sync_kind(gl, pid, out, kind, since, limit, fetch):
    folder = out / kind
    folder.mkdir(exist_ok=True)
    params = {"state": "all", "order_by": "updated_at", "sort": "asc"}
    if since:
        params["updated_after"] = since
    if kind == "issues":
        params["confidential"] = "false"
    n = 0
    for item in gl.paged(f"/projects/{pid}/{kind}", params):
        write_record(folder / f"{item['iid']}.json", fetch(item))
        n += 1
        if n % 25 == 0:
            print(f"  {n} {kind} (last {item['iid']}, updated {item['updated_at']})")
        if limit and n >= limit:
            break
    print(f"{kind}: {n} written")
    return n


def count(gl, pid):
    print("Merge requests (all):   ", gl.total(f"/projects/{pid}/merge_requests", {"state": "all"}))
    print("Merge requests (merged):", gl.total(f"/projects/{pid}/merge_requests", {"state": "merged"}))
    print("Issues (visible):       ", gl.total(f"/projects/{pid}/issues", {"state": "all"}))

    sample = gl.get_json(f"/projects/{pid}/merge_requests",
                         {"state": "merged", "order_by": "updated_at", "per_page": 50})
    human_notes = [
        sum(1 for n in gl.paged(f"/projects/{pid}/merge_requests/{mr['iid']}/notes") if not n.get("system"))
        for mr in sample
    ]
    if human_notes:
        reviewed = sum(1 for n in human_notes if n >= 3)
        print(f"Sample of {len(human_notes)} recent merged MRs: "
              f"{sum(human_notes) / len(human_notes):.1f} human comments on average, "
              f"{reviewed} with 3 or more")


def check_no_membership(project):
    perms = project.get("permissions") or {}
    if perms.get("project_access") or perms.get("group_access"):
        sys.exit("This token's account is a member of the project and can see private content.\n"
                 "Create a token from an account with no memberships, so the mirror holds only public data.")


def git(out, *args):
    subprocess.run(["git", "-C", str(out), *args], check=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["count", "sync"])
    p.add_argument("--url", default="https://gitlab.kitware.com")
    p.add_argument("--project", default="vtk/vtk")
    p.add_argument("--out", default="data/vtk-history")
    p.add_argument("--delay", type=float, default=0.5, help="seconds between requests")
    p.add_argument("--limit", type=int, default=0, help="stop after N merge requests and N issues (trial run)")
    p.add_argument("--since", help="ISO timestamp; overrides the saved sync point")
    p.add_argument("--all-versions", action="store_true", help="fetch diffs for every MR revision")
    p.add_argument("--no-commit", action="store_true", help="write files without committing")
    args = p.parse_args()

    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        sys.exit("Set GITLAB_TOKEN to a read_api token from an account with no project memberships.")

    gl = GitLab(args.url, token, args.delay)
    pid = quote(args.project, safe="")
    project = gl.get_json(f"/projects/{pid}")
    print(f"Project: {project['path_with_namespace']} (id {project['id']})")
    check_no_membership(project)

    if args.mode == "count":
        count(gl, pid)
        return

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if not (out / ".git").exists():
        git(out, "init", "-q")

    state_file = out / "sync.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    since = args.since or state.get("updated_after")
    started = datetime.now(timezone.utc).isoformat()
    print(f"Syncing into {out}/ ({'changes since ' + since if since else 'full history'})")

    changed = sync_kind(gl, pid, out, "merge_requests", since, args.limit,
                        lambda mr: fetch_merge_request(gl, pid, mr, args.all_versions))
    changed += sync_kind(gl, pid, out, "issues", since, args.limit,
                         lambda issue: fetch_issue(gl, pid, issue))

    if args.limit:
        print("Trial run: sync point not saved.")
        return
    write_record(state_file, {"project": project["path_with_namespace"], "updated_after": started})

    if not args.no_commit:
        git(out, "add", "-A")
        if subprocess.run(["git", "-C", str(out), "diff", "--cached", "--quiet"]).returncode:
            git(out, "commit", "-q", "-m", f"Sync {project['path_with_namespace']} through {started} ({changed} items)")
            print("Committed.")
        else:
            print("No changes.")


if __name__ == "__main__":
    main()
