#!/usr/bin/env python3
"""Extract the rules VTK's documentation states, each with a verbatim quote.

Covers the developer guide and the documents that tell developers how to do things: advanced topics
(object factory, SMP, wrapping, ...), the CMake module system, design documents, and migration guides.
Reads them from the VTK clone at --ref, splits each file into sections at headings and
paragraph boundaries, and asks the model to list every rule a section states. A rule is kept only
when its quote appears in the section text (whitespace and markdown emphasis ignored).

Writes data/doc_rules.json.

Usage:
  python rules/doc_rules.py
"""

import argparse
import json
import re
import subprocess
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = "http://192.168.50.23:11435"
DOCS = "Documentation/docs"
GUIDE_FILES = ["developers_guide/coding_conventions.md", "developers_guide/git/deprecation.md",
               "developers_guide/git/develop.md", "developers_guide/testing.md"]
DIRS = ["advanced", "api/cmake", "design_documents"]
BLOB = "https://gitlab.kitware.com/vtk/vtk/-/blob/master/"
MAX_CHARS = 3000

PROMPT = """Below is a section of the VTK documentation ({file}, under "{heading}").

List every rule this section states for people writing or submitting VTK code: a requirement, a
prohibition, or a stated preference. Skip background, history, and descriptions of how tools work
unless they tell a developer what to do.

Reply with JSON only: {{"rules": [{{"rule": "...", "quote": "...", "strength": "..."}}]}}
  rule      the rule in one imperative sentence, using only what the section says
  quote     the exact words from the section that state it, copied verbatim (one sentence or list item)
  strength  "must" (required or prohibited) or "should" (preferred or discouraged)
Reply {{"rules": []}} if the section states none.

Section:
{text}"""


def normalize(text):
    return re.sub(r"\s+", " ", re.sub(r"[*_`>]", "", text)).strip().lower()


def sections(text):
    heading, buf, out = "", [], []

    def flush():
        body = "\n".join(buf).strip()
        if body:
            chunk = []
            for para in re.split(r"\n\s*\n", body):
                if chunk and sum(len(p) for p in chunk) + len(para) > MAX_CHARS:
                    out.append((heading, "\n\n".join(chunk)))
                    chunk = []
                chunk.append(para)
            if chunk:
                out.append((heading, "\n\n".join(chunk)))
        buf.clear()

    for line in text.splitlines():
        m = re.match(r"^#{1,4}\s+(.*)", line)
        if m:
            flush()
            heading = m.group(1).strip().rstrip("#").strip()
        else:
            buf.append(line)
    flush()
    return out


def ask(model, prompt, retries=3, max_tokens=2048):
    body = json.dumps({"model": model, "prompt": prompt, "stream": False, "format": "json",
                       "options": {"temperature": 0, "num_ctx": 8192, "num_predict": max_tokens}}).encode()
    for attempt in range(retries):
        try:
            req = urllib.request.Request(f"{HOST}/api/generate", body, {"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.loads(json.loads(r.read())["response"])
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(5)


def extract(model, file, heading, text):
    reply = ask(model, PROMPT.format(file=file, heading=heading or "top", text=text))
    kept, dropped = [], 0
    haystack = normalize(text)
    for r in reply.get("rules") or []:
        quote = (r.get("quote") or "").strip()
        if quote and r.get("rule") and normalize(quote) in haystack:
            kept.append({"rule": r["rule"].strip(), "quote": quote, "strength": r.get("strength", "should"),
                         "file": file, "section": heading, "url": BLOB + f"{DOCS}/{file}"})
        else:
            dropped += 1
    return kept, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default="/home/jlee/gitsync/vtk")
    ap.add_argument("--ref", default="upstream/master")
    ap.add_argument("--model", default="qwen3-coder-next:q4_K_M")
    ap.add_argument("--out", default=str(ROOT / "data/doc_rules.json"))
    ap.add_argument("--force", action="store_true", help="extract even if no document changed")
    args = ap.parse_args()
    commit = subprocess.check_output(["git", "-C", args.repo, "rev-parse", "--short", args.ref], text=True).strip()
    listed = subprocess.check_output(["git", "-C", args.repo, "ls-tree", "-r", "--name-only", args.ref,
                                      *[f"{DOCS}/{d}" for d in DIRS]], text=True).split()
    files = GUIDE_FILES + [p[len(DOCS) + 1:] for p in listed if p.endswith(".md")]
    sources = {f: subprocess.check_output(["git", "-C", args.repo, "rev-parse", f"{args.ref}:{DOCS}/{f}"], text=True).strip()
               for f in files}
    out_path = Path(args.out)
    if not args.force and out_path.exists() and json.loads(out_path.read_text()).get("sources") == sources:
        print(f"documents unchanged since the last extraction; keeping {out_path}")
        return
    jobs = []
    for file in files:
        text = subprocess.check_output(["git", "-C", args.repo, "show", f"{args.ref}:{DOCS}/{file}"], text=True)
        jobs += [(file, h, t) for h, t in sections(text)]
    print(f"{len(jobs)} sections from {len(files)} files at {commit}", flush=True)
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda j: extract(args.model, *j), jobs))
    rules, dropped, seen = [], 0, set()
    for kept, lost in results:
        dropped += lost
        for r in kept:
            if normalize(r["quote"]) not in seen:
                seen.add(normalize(r["quote"]))
                rules.append(r)
    for i, r in enumerate(rules, 1):
        r["id"] = f"D{i:03d}"
    out_path.write_text(json.dumps({"commit": commit, "sources": sources, "rules": rules}, indent=1, ensure_ascii=False))
    by_dir = {}
    for r in rules:
        top = r["file"].split("/")[0]
        by_dir[top] = by_dir.get(top, 0) + 1
    print(f"{len(rules)} documented rules {by_dir}; {dropped} dropped for quotes not in the text")


if __name__ == "__main__":
    main()
