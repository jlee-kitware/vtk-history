"""Documentation units from the VTK repository for the search index.

  doc    a section of a design document, guide, file format spec, or README at the current master,
         with the date and MR of the last change to the file
  note   a release note (Documentation/release/dev/*.md) as its author wrote it, recovered from the
         merge that added it, including notes since folded into a versioned release page
  class  the Doxygen description at the top of a header: what the class is for

Release notes and document changes link to MRs through the first-parent merge commits that
GitLab records as each MR's merge commit.
"""

import re
import subprocess
from pathlib import PurePosixPath

DOC_PATHS = re.compile(r"^(Documentation/(docs|dev)/.*\.(md|rst)|.*(^|/)README(\.md|\.txt)?|[^/]+\.md)$")
SKIP = re.compile(r"^(ThirdParty|Utilities/KWSys|Utilities/Doxygen|\.gitlab)/|/Testing/|/release/")
HEADING = re.compile(r"^(#{1,4})\s+(.+)$|^(.+)\n([=\-~^]{3,})$", re.M)
MAX_CHARS = 3000
CLASS_BLOCK = re.compile(r"/\*\*\s*\n(.*?)\*/", re.S)


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace").stdout


def sections(text):
    """Split a markdown or reStructuredText document at headings, keeping each heading with its body."""
    marks = [(m.start(), (m.group(2) or m.group(3) or "").strip()) for m in HEADING.finditer(text)]
    if not marks or marks[0][0] > 0:
        marks.insert(0, (0, ""))
    for (start, title), (end, _) in zip(marks, marks[1:] + [(len(text), "")]):
        body = text[start:end].strip()
        while body:
            yield title, body[:MAX_CHARS]
            body = body[MAX_CHARS:]


def last_change(repo, ref, path, mr_by_sha):
    out = git(repo, "log", "-1", "--first-parent", "--format=%H %cs", ref, "--", path).split()
    return (out[1], mr_by_sha.get(out[0])) if len(out) == 2 else ("", None)


def doc_units(repo, ref, mr_by_sha):
    for path in git(repo, "ls-tree", "-r", "--name-only", ref).splitlines():
        if not DOC_PATHS.match(path) or SKIP.search(path):
            continue
        text = git(repo, "show", f"{ref}:{path}")
        if len(text.strip()) < 80:
            continue
        date, mr = last_change(repo, ref, path, mr_by_sha)
        doc_title = next((t for t, _ in sections(text) if t), PurePosixPath(path).stem)
        for i, (title, body) in enumerate(sections(text)):
            yield {"id": f"doc:{path}#{i}", "kind": "doc", "ref": path, "date": date, "author": None,
                   "path": path, "module": None, "class": None,
                   "title": f"{doc_title}: {title}" if title and title != doc_title else doc_title,
                   "text": body, "url": f"https://gitlab.kitware.com/vtk/vtk/-/blob/master/{path}",
                   "mr": mr, "embed_text": f"{doc_title}\n{title}\n{body}"[:2000]}


def note_units(repo, ref, mr_by_sha):
    """Every release note as first added, with the MR whose merge added it."""
    log = git(repo, "log", "--first-parent", "--diff-merges=first-parent", "--diff-filter=A", "--name-only",
              "--format=@@@%H %cs", ref, "--", "Documentation/release/dev/*.md")
    sha = date = None
    for line in log.splitlines():
        if line.startswith("@@@"):
            sha, date = line[3:].split()
        elif line.endswith(".md") and not line.endswith("0-sample-topic.md"):
            text = git(repo, "show", f"{sha}:{line}")
            if len(text.strip()) < 40:
                continue
            mr = mr_by_sha.get(sha)
            title = next((t for t, _ in sections(text) if t), PurePosixPath(line).stem)
            yield {"id": f"note:{sha[:12]}:{line}", "kind": "note", "ref": f"!{mr}" if mr else sha[:12], "date": date,
                   "author": None, "path": line, "module": None, "class": None, "title": title,
                   "text": text[:MAX_CHARS], "url": None, "mr": mr, "embed_text": text[:2000]}


def class_units(repo, ref, mr_by_sha):
    """The first Doxygen block of each header that documents a vtk class."""
    for path in git(repo, "ls-tree", "-r", "--name-only", ref).splitlines():
        if not path.endswith(".h") or SKIP.search(path) or not PurePosixPath(path).stem.startswith("vtk"):
            continue
        text = git(repo, "show", f"{ref}:{path}")
        m = CLASS_BLOCK.search(text)
        if not m or "@class" not in m.group(1) and "@brief" not in m.group(1):
            continue
        body = "\n".join(line.strip().lstrip("*").rstrip() for line in m.group(1).splitlines()).strip()
        cls = PurePosixPath(path).stem
        date, _mr = last_change(repo, ref, path, mr_by_sha)
        yield {"id": f"class:{path}", "kind": "class", "ref": cls, "date": date, "author": None, "path": path,
               "module": None, "class": cls, "title": cls, "text": body[:MAX_CHARS],
               "url": f"https://gitlab.kitware.com/vtk/vtk/-/blob/master/{path}", "mr": None,
               "embed_text": f"{cls}\n{body}"[:2000]}
