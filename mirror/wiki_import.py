#!/usr/bin/env python3
"""Import the VTK pages of the retired KitwarePublic wiki (vtk.org/Wiki) from a MediaWiki XML export.

The wiki was shared by VTK, ParaView, ITK, CMake and other Kitware projects and is no longer
served; its content is under a Creative Commons license. Kept: main-namespace pages, not redirects, whose title starts with "VTK", plus any page
that VTK's GitLab, Discourse or blog history links to (vtk.org/Wiki/<title>). Each page is stored
with its current text (wikitext, plain text, and plain text by section), first and last edit dates, revision count, and
editors, in data/wiki-history/pages/<id>.json; redirects go to data/wiki-history/redirects.json. The export itself stays outside the repository.

Usage:
  python mirror/wiki_import.py /path/to/wiki_dump.xml
"""

import argparse
import glob
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote

import mwparserfromhell

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.mediawiki.org/xml/export-0.11/}"
LINK = re.compile(r"vtk\.org/Wiki/([^\s\"'<>)\]|#?]+)", re.I)
ARCHIVE = "https://web.archive.org/web/2025/https://vtk.org/Wiki/"


def norm(title):
    t = unquote(title).replace("_", " ").strip()
    return t[:1].upper() + t[1:]


def linked_titles():
    """Wiki page titles linked from the mirrored GitLab, Discourse and blog history."""
    found = set()
    for pattern in ("data/vtk-history/issues/*.json", "data/vtk-history/merge_requests/*.json",
                    "data/discourse-history/topics/*.json", "data/blog-history/posts/*.json"):
        for f in glob.glob(str(ROOT / pattern)):
            found.update(norm(t) for t in LINK.findall(Path(f).read_text(errors="replace")))
    return found


def plain(wikitext):
    code = mwparserfromhell.parse(wikitext)
    for tag in code.filter_tags(recursive=True):
        if str(tag.tag).lower() in ("source", "syntaxhighlight", "pre", "code"):
            try:
                code.replace(tag, f"\n{tag.contents}\n")
            except ValueError:
                pass
    text = code.strip_code(normalize=True, collapse=True)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


HEADING = re.compile(r"^(={2,4})\s*(.+?)\s*\1\s*$", re.M)


def sections(wikitext):
    """[(heading, plain text)], splitting at level 2 to 4 headings."""
    parts = HEADING.split(wikitext)
    out = [("", plain(parts[0]))]
    for i in range(1, len(parts) - 2, 3):
        out.append((plain(parts[i + 1]), plain(parts[i + 2])))
    return [(h, t) for h, t in out if t]


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dump")
    p.add_argument("--out", default=str(ROOT / "data/wiki-history"))
    args = p.parse_args()

    wanted = linked_titles()
    out = Path(args.out) / "pages"
    out.mkdir(parents=True, exist_ok=True)
    kept = linked = 0
    redirects = {}
    for _, el in ET.iterparse(args.dump, events=("end",)):
        if el.tag != NS + "page":
            continue
        title = el.findtext(NS + "title")
        if el.findtext(NS + "ns") == "0" and el.find(NS + "redirect") is not None:
            redirects[norm(title)] = norm(el.find(NS + "redirect").get("title"))
        if el.findtext(NS + "ns") == "0" and el.find(NS + "redirect") is None:
            is_vtk = re.match(r"VTK\b", title, re.I) is not None
            if is_vtk or norm(title) in wanted:
                revs = el.findall(NS + "revision")
                wikitext = revs[-1].findtext(NS + "text") or ""
                editors = sorted({r.findtext(f"{NS}contributor/{NS}username") or "" for r in revs} - {""})
                page = {"id": int(el.findtext(NS + "id")), "title": title,
                        "url": ARCHIVE + title.replace(" ", "_"),
                        "created": revs[0].findtext(NS + "timestamp"), "updated": revs[-1].findtext(NS + "timestamp"),
                        "revisions": len(revs), "editors": editors, "linked_from_history": norm(title) in wanted,
                        "text": plain(wikitext), "sections": sections(wikitext), "wikitext": wikitext}
                (out / f"{page['id']}.json").write_text(json.dumps(page, indent=1, ensure_ascii=False))
                kept += 1
                linked += page["linked_from_history"]
        el.clear()
    (Path(args.out) / "redirects.json").write_text(json.dumps(redirects, indent=0, sort_keys=True))
    (Path(args.out) / "import.json").write_text(json.dumps(
        {"source": "KitwarePublic MediaWiki XML export", "license": "Creative Commons (variant to confirm)",
         "pages": kept, "linked_from_history": linked,
         "titles_linked_from_history": len(wanted)}, indent=1))
    print(f"kept {kept} pages ({linked} linked from the history; {len(wanted)} distinct titles linked)")


if __name__ == "__main__":
    main()
