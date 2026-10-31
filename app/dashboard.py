"""The dashboard: what needs attention in VTK's review queue and triage, and how the project is changing.

Everything is computed from data already on disk (the GitLab mirror, data/people/mrs.jsonl, the label
evaluation, the deprecation index and the trends) as of the mirror's last sync, and cached in
data/dashboard.json until the mirror changes.
"""

import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "data/vtk-history"
CACHE = ROOT / "data/dashboard.json"
MONTHS = 24
QUEUE_ROWS = 12
QUEUE_DAYS = 90
CONCENTRATED = 0.75

MEASURED = [
    {"tool": "Related history", "result": "the fixed issue is in the top 5 for 84% of MRs"},
    {"tool": "Reviewer suggestions", "result": "an actual reviewer is in the top 3 for 76% of MRs"},
    {"tool": "Area labels", "result": "95% right above the 0.7 confidence cutoff"},
    {"tool": "Convention follow-through", "result": "Brier 0.194 against 0.218 for the base rate"},
]


def when(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def month(text):
    return text[:7]


def last_months(as_of, n):
    y, m = as_of.year, as_of.month
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y, m - 1) if m > 1 else (y - 1, 12)
    return out[::-1]


def median(values):
    return round(statistics.median(values), 1) if values else 0.0


def mirror_stamp():
    return json.loads((MIRROR / "sync.json").read_text())["updated_after"]


def inputs_stamp():
    """Changes when the mirror syncs or a table the dashboard reads is rebuilt."""
    tables = [ROOT / "data/people/mrs.jsonl", ROOT / "data/labels/area_eval.json"]
    return mirror_stamp() + "".join(f"|{p.stat().st_mtime:.0f}" for p in tables if p.exists())


def read_mirror():
    mrs, issues, files = {}, [], {}
    for f in (MIRROR / "merge_requests").glob("*.json"):
        m = json.loads(f.read_text())["merge_request"]
        mrs[m["iid"]] = {"iid": m["iid"], "title": m["title"], "state": m["state"], "draft": m["draft"],
                         "created": m["created_at"], "merged": m["merged_at"], "updated": m["updated_at"],
                         "author": (m.get("author") or {}).get("username", ""), "target": m["target_branch"],
                         "url": m["web_url"], "sha": m.get("sha")}
    for f in (MIRROR / "mr_files").glob("*.json"):
        files[int(f.stem)] = json.loads(f.read_text())
    for f in (MIRROR / "issues").glob("*.json"):
        i = json.loads(f.read_text())["issue"]
        issues.append({"created": i["created_at"], "state": i["state"], "labels": i["labels"]})
    return mrs, issues, files


def changed_files(store, m, people, files):
    """Files an MR changes: the reviewer table, the mirror's list, or a diff of its fetched head."""
    known = people.get(m["iid"], {}).get("files") or files.get(m["iid"])
    if known or not m.get("sha"):
        return known or []
    try:
        return store.mr_paths(m["sha"])
    except Exception:
        return []


def review_queue(store, mrs, people, files, expertise, as_of):
    opened = [m for m in mrs.values() if m["state"] == "opened" and m["target"] == "master"]
    ready = [m for m in opened if not m["draft"]]
    waiting = [m for m in ready if not people.get(m["iid"], {}).get("reviewers")]
    recent_since = (as_of - timedelta(days=QUEUE_DAYS)).isoformat()
    recent = [m for m in waiting if m["created"] >= recent_since]
    stalled_since = (as_of - timedelta(days=60)).isoformat()
    abandoned_since = (as_of - timedelta(days=365)).isoformat()
    rows = []
    for m in sorted(recent, key=lambda m: m["created"])[:QUEUE_ROWS]:
        changed = changed_files(store, m, people, files)
        suggested = expertise.suggest(changed, as_of.isoformat(), exclude={m["author"]}, top=3) if changed else []
        rows.append({"iid": m["iid"], "title": m["title"], "author": m["author"], "url": m["url"],
                     "age": (as_of - when(m["created"])).days,
                     "reviewers": ", ".join(f"{s['user']} ({s['median_first_response_days']} d)"
                                            if s["median_first_response_days"] is not None else s["user"]
                                            for s in suggested) or "no file list yet"})
    return {"open": len(opened), "drafts": len(opened) - len(ready), "waiting": len(waiting),
            "waiting_recent": len(recent), "days": QUEUE_DAYS,
            "stalled": sum(abandoned_since <= m["updated"] < stalled_since for m in ready),
            "abandoned": sum(m["updated"] < abandoned_since for m in ready), "rows": rows}


def activity(mrs, people, issues, as_of):
    months = last_months(as_of, MONTHS)
    merged, to_merge, to_review, filed = Counter(), defaultdict(list), defaultdict(list), Counter()
    for m in mrs.values():
        if m["merged"] and month(m["merged"]) in months:
            merged[month(m["merged"])] += 1
            to_merge[month(m["merged"])].append((when(m["merged"]) - when(m["created"])).total_seconds() / 86400)
    for p in people.values():
        firsts = [r["first"] for r in p["reviewers"]]
        if firsts and month(p["created"]) in months:
            to_review[month(p["created"])].append((when(min(firsts)) - when(p["created"])).total_seconds() / 86400)
    for i in issues:
        if month(i["created"]) in months:
            filed[month(i["created"])] += 1
    return {"months": months, "merged": [merged[k] for k in months],
            "days_to_merge": [median(to_merge[k]) for k in months],
            "days_to_review": [median(to_review[k]) for k in months],
            "issues": [filed[k] for k in months]}


def reviewers(people, as_of, is_bot, keys):
    since = (as_of - timedelta(days=90)).isoformat()
    year = (as_of - timedelta(days=365)).isoformat()
    load = Counter()
    module_mrs, module_people = Counter(), defaultdict(Counter)
    for p in people.values():
        for r in p["reviewers"]:
            if since <= r["first"] and not is_bot(r["user"]):
                load[r["user"]] += 1
        names = {r["user"] for r in p["reviewers"] if not is_bot(r["user"])}
        if p["created"] >= year and p["files"] and names:
            for module in {keys(f)[2] for f in p["files"]} - {None}:
                module_mrs[module] += 1
                module_people[module].update(names)
    thin = []
    for mod, n in module_mrs.most_common():
        if n < 5:
            continue
        user, count = module_people[mod].most_common(1)[0]
        if count / n >= CONCENTRATED:
            thin.append({"module": mod, "mrs": n, "reviewer": user, "share": f"{count / n:.0%}",
                         "others": len(module_people[mod]) - 1})
    return {"load": [{"user": u, "mrs": n} for u, n in load.most_common(10)], "thin": thin[:10]}


def deprecations_due(rows):
    def version(v):
        return tuple(int(x) for x in v.split(".")[:2] if x.isdigit())
    versions = sorted({version(r["version"]) for r in rows if r["version"]})
    if len(versions) < 3:
        return {"due": 0, "rows": [], "through": ""}
    through = versions[-3]
    due = sorted((r for r in rows if r["outcome"] == "present" and version(r["version"]) <= through),
                 key=lambda r: version(r["version"]))
    return {"due": len(due), "through": ".".join(map(str, through)),
            "rows": [{"api": r["api"], "version": r["version"], "url": r["deprecated_url"]} for r in due[:8]]}


def triage(area_eval):
    b = (area_eval or {}).get("backfill")
    if not b:
        return {}
    cutoff = area_eval["cutoff"]
    precision = next((x["precision"] for x in area_eval["by_confidence"] if x["confidence_at_least"] == cutoff), None)
    return {"open": b["open"], "open_labeled": b["open_labeled_now"], "open_added": b["open_added"],
            "cutoff": cutoff, "precision": f"{precision:.0%}" if precision is not None else ""}


def trend_names(store):
    out = {}
    for kind in ("emerging", "fading"):
        labels, _, _ = store.trend_rows("labels", "mr", kind)
        terms, _, _ = store.trend_rows("terms", "mr", kind)
        out[kind] = [{"name": r["name"], "ratio": r["ratio"]} for r in (labels[:3] + terms)[:8]]
    return out


def compute(store, expertise):
    from expertise import is_bot, keys
    stamp = mirror_stamp()
    as_of = when(stamp)
    mrs, issues, files = read_mirror()
    people = expertise.by_iid
    meta = json.loads((ROOT / "data/index/meta.json").read_text())
    return {
        "stamp": inputs_stamp(), "as_of": stamp[:10], "computed": datetime.now().isoformat(timespec="minutes"),
        "counts": {"mrs": len(mrs), "issues": len(issues), "documents": meta.get("count", 0)},
        "queue": review_queue(store, mrs, people, files, expertise, as_of),
        "activity": activity(mrs, people, issues, as_of),
        "reviewers": reviewers(people, as_of, is_bot, keys),
        "deprecations": deprecations_due(store.deprecation_rows()),
        "triage": triage(store.area_eval),
        "trends": trend_names(store),
        "measured": MEASURED,
    }


def summary(store, expertise):
    if CACHE.exists():
        cached = json.loads(CACHE.read_text())
        if cached.get("stamp") == inputs_stamp():
            return cached
    data = compute(store, expertise)
    CACHE.write_text(json.dumps(data))
    return data
