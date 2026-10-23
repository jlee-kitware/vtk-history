#!/usr/bin/env python3
"""Which pages of the retired VTK wiki are still needed, and which are out of date.

Only the examples moved when vtk.org/Wiki was taken offline. For every imported VTK wiki page
(mirror/wiki_import.py) this measures:

  links      issues, MRs, review comments, forum posts and blog posts that link to the page
             (following wiki redirects), in total and since --recent
  questions  forum topics started since --recent whose first post is close in meaning to a
             section of the page (embedding similarity of at least --match; data/index vectors)
  outdated   VTK classes the page names that VTK has since removed, against the classes in
             today's source tree (ontology/entities.json) and removed headers (git history)
  covered    the closest section of VTK's current documentation (Documentation/ and READMEs in
             the repository, the index's doc rows), as a hint that the content already exists

Pages are ranked by recent links plus recent questions. Writes data/wiki-history/pages_ranked.json
and data/wiki-history/WIKI_PAGES.md.

Usage:
  python triage/wiki_pages.py [--recent 2023-01-01] [--match 0.7]
"""

import argparse
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "index"))
sys.path.insert(0, str(ROOT / "mirror"))
sys.path.insert(0, str(ROOT / "triage"))
from search import Index  # noqa: E402
from wiki_import import LINK, norm  # noqa: E402

CLASS = re.compile(r"\bvtk[A-Z][A-Za-z0-9]+")
WIKI = ROOT / "data/wiki-history"
NOT_CLASSES = {"vtkIdType", "vtkCommon", "vtkParse", "vtkType"}


def resolve(title, redirects):
    for _ in range(4):
        if title not in redirects:
            break
        title = redirects[title]
    return title


def history_links():
    """[(title, date, kind, ref)] for every vtk.org/Wiki link in the mirrored history."""
    out = []

    def add(text, date, kind, ref):
        for t in LINK.findall(text or ""):
            out.append((norm(t), (date or "")[:10], kind, ref))

    for kind, key, mark in (("issues", "issue", "#"), ("merge_requests", "merge_request", "!")):
        for f in glob.glob(str(ROOT / f"data/vtk-history/{kind}/*.json")):
            rec = json.load(open(f))
            item = rec[key]
            ref = f"{mark}{item['iid']}"
            add(item.get("description"), item["created_at"], kind, ref)
            for d in rec.get("discussions") or []:
                for n in d.get("notes", []):
                    add(n.get("body"), n.get("created_at"), kind, ref)
    for f in glob.glob(str(ROOT / "data/discourse-history/topics/*.json")):
        t = json.load(open(f))
        for p in t["posts"]:
            add(p.get("cooked"), p.get("created_at"), "forum", f"topic {t['topic']['id']}")
    for f in glob.glob(str(ROOT / "data/blog-history/posts/*.json")):
        b = json.load(open(f))
        add(b.get("content"), b.get("date"), "blog", b.get("link"))
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--recent", default="2023-01-01")
    p.add_argument("--match", type=float, default=0.7)
    p.add_argument("--explore", action="store_true", help="print similarity distributions and stop")
    args = p.parse_args()

    pages = {json.load(open(f))["title"]: json.load(open(f)) for f in glob.glob(str(WIKI / "pages/*.json"))}
    by_norm = {norm(t): t for t in pages}
    redirects = json.loads((WIKI / "redirects.json").read_text())

    links, unresolved = defaultdict(list), Counter()
    for title, date, kind, ref in history_links():
        target = resolve(title, redirects)
        if target in by_norm:
            links[by_norm[target]].append((date, kind, ref))
        else:
            unresolved[target.split("/")[0] + ("/" + target.split("/")[1] if "/" in target else "")] += 1

    import module_labels as ML
    current = set(json.loads((ROOT / "ontology/entities.json").read_text())["classes"])
    removed = set(ML.removed_classes()) - current - NOT_CLASSES

    ix = Index(str(ROOT / "data/index"))
    rows = ix.con.execute("SELECT rowid, id, kind, date, title FROM docs WHERE kind IN ('wiki', 'post', 'doc')").fetchall()
    wiki_rows = [r for r in rows if r[2] == "wiki"]
    wiki_page = [r[4].partition(": ")[0] for r in wiki_rows]
    wv = ix.vectors[[r[0] - 1 for r in wiki_rows]]
    topics = [r for r in rows if r[2] == "post" and r[1].endswith("/1") and r[3] >= args.recent]
    tv = ix.vectors[[r[0] - 1 for r in topics]]
    docs = [r for r in rows if r[2] == "doc"]
    dv = ix.vectors[[r[0] - 1 for r in docs]]

    sims = tv @ wv.T
    best = sims.max(axis=1)
    if args.explore:
        print("recent topics:", len(topics), "best-match percentiles 50/75/90/95/99:",
              np.percentile(best, [50, 75, 90, 95, 99]).round(3))
        for lo in (0.6, 0.65, 0.7, 0.75):
            print(f"  >= {lo}: {(best >= lo).sum()} topics")
        order = np.argsort(-best)
        for i in list(order[:6]) + list(order[int(len(order) * 0.05):int(len(order) * 0.05) + 6]):
            print(f"  {best[i]:.3f} {topics[i][4][:60]!r} -> {wiki_page[int(sims[i].argmax())]}")
        return

    questions = defaultdict(list)
    for i in np.where(best >= args.match)[0]:
        questions[wiki_page[int(sims[i].argmax())]].append(topics[i][1].split(":")[1].split("/")[0])
    doc_sim = wv @ dv.T
    doc_best = defaultdict(lambda: (0.0, ""))
    for j, page in enumerate(wiki_page):
        k = int(doc_sim[j].argmax())
        if doc_sim[j, k] > doc_best[page][0]:
            doc_best[page] = (float(doc_sim[j, k]), docs[k][4])

    ranked = []
    for title, page in pages.items():
        named = set(CLASS.findall(page["text"]))
        gone = sorted(named & removed)
        ls = links.get(title, [])
        recent = [l for l in ls if l[0] >= args.recent]
        ranked.append({
            "title": title, "url": page["url"], "updated": page["updated"][:10], "revisions": page["revisions"],
            "links": len(ls), "links_recent": len(recent), "last_linked": max((l[0] for l in ls), default=""),
            "questions_recent": len(questions.get(title, [])), "question_topics": questions.get(title, [])[:5],
            "classes_named": len(named), "classes_removed": gone,
            "docs_closest": round(doc_best[title][0], 3), "docs_closest_title": doc_best[title][1],
        })
    for r in ranked:
        r["score"] = r["links_recent"] + r["questions_recent"]
    ranked.sort(key=lambda r: (-r["score"], -r["links"], -r["revisions"]))
    WIKI.mkdir(exist_ok=True)
    json.dump({"recent": args.recent, "match": args.match, "pages": ranked,
               "links_to_pages_not_kept": unresolved.most_common(20)},
              open(WIKI / "pages_ranked.json", "w"), indent=1)

    used = [r for r in ranked if r["score"]]
    lines = ["# VTK wiki pages still in use", "",
             f"{len(pages)} imported pages. Since {args.recent}: {sum(r['links_recent'] for r in ranked)} links from "
             f"the history, and {sum(r['questions_recent'] for r in ranked)} of {len(topics)} new forum topics close "
             f"to a wiki section (similarity at least {args.match}). {len(used)} pages have either.", "",
             "| Page | Last edited | Links since | Last linked | Close forum topics | Removed classes named | "
             "Closest current doc (similarity) |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in used[:40]:
        gone = ", ".join(r["classes_removed"][:3]) + (" ..." if len(r["classes_removed"]) > 3 else "")
        lines.append(f"| [{r['title']}]({r['url']}) | {r['updated']} | {r['links_recent']} | {r['last_linked']} | "
                     f"{r['questions_recent']} | {gone} | {r['docs_closest_title'][:40]} ({r['docs_closest']}) |")
    lines += ["", "Links to wiki pages that were not imported (mostly examples that moved to vtk-examples):", "",
              ", ".join(f"{t} ({n})" for t, n in unresolved.most_common(10)), ""]
    (WIKI / "WIKI_PAGES.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
