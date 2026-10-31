#!/usr/bin/env python3
"""Apply reviewed area labels to VTK issues on GitLab.

Only suggestions a maintainer marked right, or corrected, on the Labels page are applied
(data/labels/label_decisions.json). Each issue gets its area label plus MARKER, so later corrections can be
counted from GitLab's label history; issues that gained an area label since the review are skipped. Every
write is logged to data/labels/applied.jsonl.

Writing needs VTK_LABEL_WRITE=1 and a GITLAB_TOKEN with the api scope; without both, apply only prints the plan.
apply labels every accepted issue in one run; --issue applies to the issues named (one-shot), --limit caps a run.

Usage:
  python triage/apply_labels.py plan
  VTK_LABEL_WRITE=1 python triage/apply_labels.py apply [--issue N ...] [--limit N]
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISIONS = ROOT / "data/labels/label_decisions.json"
APPLIED = ROOT / "data/labels/applied.jsonl"
MIRROR = ROOT / "data/vtk-history/issues"
API = "https://gitlab.kitware.com/api/v4"
PROJECT = urllib.parse.quote("vtk/vtk", safe="")
MARKER = "triage:auto-labeled"
NO_FIT = "no label fits"
APPLY = ("right", "relabel")


def load_decisions(path=DECISIONS):
    return json.loads(path.read_text()) if path.exists() else {}


def applied_issues():
    if not APPLIED.exists():
        return set()
    return {json.loads(line)["issue"] for line in APPLIED.read_text().splitlines() if line.strip()}


def plan(decisions=None):
    """(issues to label, issues skipped with the reason), from the review decisions and the mirror."""
    decisions = load_decisions() if decisions is None else decisions
    done = applied_issues()
    rows, skipped = [], []
    for key, d in sorted(decisions.items(), key=lambda kv: int(kv[0])):
        if d["verdict"] not in APPLY or not d.get("label") or d["label"] == NO_FIT:
            continue
        iid = int(key)
        path = MIRROR / f"{iid}.json"
        issue = json.loads(path.read_text())["issue"] if path.exists() else {}
        areas = [l for l in issue.get("labels") or [] if l.startswith("area:")]
        if iid in done:
            skipped.append({"issue": iid, "reason": "applied already"})
        elif areas:
            skipped.append({"issue": iid, "reason": "now has " + ", ".join(areas)})
        else:
            rows.append({"issue": iid, "add": [d["label"], MARKER], "title": issue.get("title", ""),
                         "state": issue.get("state", ""), "by": d.get("by", "")})
    return rows, skipped


def token():
    sys.path.insert(0, str(ROOT))
    import config
    return os.environ.get("GITLAB_TOKEN") or getattr(config, "GITLAB_TOKEN", None)


def request(method, url, tok):
    req = urllib.request.Request(url, method=method, headers={"PRIVATE-TOKEN": tok})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def write_blocker(tok=None):
    """Why writing is not allowed, or "" when it is. The switch is checked first, so the usual answer needs no network."""
    if os.environ.get("VTK_LABEL_WRITE") != "1":
        return "VTK_LABEL_WRITE=1 is not set"
    tok = tok or token()
    if not tok:
        return "no GITLAB_TOKEN"
    try:
        scopes = request("GET", f"{API}/personal_access_tokens/self", tok).get("scopes", [])
    except OSError as e:
        return f"could not check the token: {e}"
    return "" if "api" in scopes else f"the token's scopes are {', '.join(scopes)}; writing needs api"


def apply(rows, tok):
    for r in rows:
        query = urllib.parse.urlencode({"add_labels": ",".join(r["add"])})
        result = request("PUT", f"{API}/projects/{PROJECT}/issues/{r['issue']}?{query}", tok)
        with APPLIED.open("a") as f:
            f.write(json.dumps({"issue": r["issue"], "added": r["add"], "labels_after": result.get("labels"),
                                "reviewed_by": r["by"],
                                "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}) + "\n")
        yield r, result.get("labels")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", choices=["plan", "apply"])
    p.add_argument("--issue", type=int, action="append", help="only this issue (repeatable)")
    p.add_argument("--limit", type=int, help="apply to at most this many issues")
    args = p.parse_args()
    rows, skipped = plan()
    if args.issue:
        missing = set(args.issue) - {r["issue"] for r in rows}
        rows = [r for r in rows if r["issue"] in args.issue]
        for iid in sorted(missing):
            print(f"#{iid} is not ready to apply: accept its suggestion on the Labels page first")
    rows = rows[:args.limit] if args.limit else rows
    for r in rows:
        print(f"#{r['issue']:<6} + {', '.join(r['add']):<40} {r['state']:<7} {r['title'][:70]}")
    for s in skipped:
        print(f"#{s['issue']:<6} skipped: {s['reason']}")
    print(f"{len(rows)} issues to label, {len(skipped)} skipped")
    if args.command == "plan":
        return
    tok = token()
    blocker = write_blocker(tok)
    if blocker:
        sys.exit(f"Not applied: {blocker}.")
    for r, labels in apply(rows, tok):
        print(f"#{r['issue']} labels now: {', '.join(labels or [])}")


if __name__ == "__main__":
    main()
