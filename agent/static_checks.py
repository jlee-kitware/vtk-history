#!/usr/bin/env python3
"""Deterministic checks on a merge request's added lines, run against the head commit.

Each check reports a candidate problem with the file and new-file line it concerns:

  undefined   a method declared in a header with no definition anywhere in the tree
  unused      a new data member, or a new method of internal code (Private/ paths, *Internals
              classes), referenced nowhere else; public API is left alone since users call it
  unreleased  a GL/EGL handle or heap object stored in a member with no matching release
  unset       a CMake variable read in added lines that nothing in the tree sets
  raw-new     a local raw pointer from vtkX::New(), where VTK reviewers ask for vtkNew or vtkSmartPointer
  stdout      std::cout, std::cerr, or printf in library code, where VTK uses its logging macros
  deprecated  a use of an API that VTK deprecated or removed before the review date

Candidates are facts about the tree, not verdicts: the reviewer model confirms each one
before commenting (a method may be defined by a macro, a member used through a template).
"""

import re
import subprocess
from pathlib import Path

HEADER = re.compile(r"\.(h|hxx|txx)$")
SOURCE = re.compile(r"\.(cxx|cpp|cc|txx|h|hxx)$")
CMAKE = re.compile(r"(CMakeLists\.txt|\.cmake)$")
METHOD_DECL = re.compile(r"^\s*(?:virtual\s+|static\s+|inline\s+|explicit\s+|VTK_\w+\s+)*[\w:<>,*&\s]+?[\s*&](~?[A-Z]\w*)\s*"
                         r"\([^;{]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:=\s*0\s*)?;\s*(?://.*)?$")
MEMBER_DECL = re.compile(r"^\s*(?:mutable\s+|static\s+)?[\w:<>,*&\s]+?[\s*&]([A-Z]\w*)\s*(?:=\s*[^;]+|\{[^;]*\})?\s*;\s*(?://.*)?$")
FUNC_DEF = re.compile(r"^(?:[\w:<>,*&\s]+?\s)?(?:(\w+)::)?(~?[A-Za-z_]\w*)\s*\([^;]*\)?\s*(?:const)?\s*(?:\{.*)?$")
CREATE = [
    (re.compile(r"glGen(Framebuffers|Textures|Renderbuffers|Buffers|VertexArrays)\s*\(\s*\w+\s*,\s*&?\s*([\w>.\-\[\]]+)"),
     lambda kind, var: rf"glDelete{kind}\s*\([^;]*{re.escape(var)}"),
    (re.compile(r"([\w>.\-]+)\s*=\s*eglCreate(Context)\s*\("), lambda var, kind: rf"eglDestroy{kind}\s*\([^;]*{re.escape(var)}"),
    (re.compile(r"([\w>.\-]+)\s*=\s*eglCreate\w*(Surface)\s*\("), lambda var, kind: rf"eglDestroy{kind}\s*\([^;]*{re.escape(var)}"),
    (re.compile(r"(this->\w+|\b[A-Z]\w+)\s*=\s*new\s+[\w:<>]+"), lambda var, _k: rf"delete(\[\])?\s+{re.escape(var)}\b"),
]
CMAKE_READ = re.compile(r"\$\{(\w+)\}|\bif\s*\(\s*(?:NOT\s+)?(\w+)\s*\)")
CMAKE_BUILTIN = re.compile(r"^(CMAKE_|PROJECT_|VTK_MODULE_|_|ARG_|WIN32$|APPLE$|UNIX$|MSVC|ANDROID$|EMSCRIPTEN$)")


CODE = ("*.cxx", "*.cpp", "*.h", "*.txx", "*.hxx", "*.mm")
RAW_NEW = re.compile(r"^\s*(?:const\s+)?(vtk\w+)\s*\*\s*(\w+)\s*=\s*(vtk\w+)::New\s*\(\s*\)\s*;")
STDOUT = re.compile(r"\bstd::(cout|cerr)\b|(?<![\w.:])printf\s*\(|fprintf\s*\(\s*stderr")
NOT_LIBRARY = re.compile(r"(^|/)(Testing|Examples|Utilities|ThirdParty|Wrapping)/|\.py$")
IDENT_TOKEN = re.compile(r"\b[A-Za-z_]\w{3,}\b")


def still_current(repo, head, rec, cache={}):
    """True when the tree at head still declares the symbol without a deprecation mark: in the class
    header, or for a name the class does not declare itself, in any header (an inherited method)."""
    key = (head, rec["class"], rec["symbol"])
    if key not in cache:
        whole = rec["class"] == rec["symbol"]
        pattern = rf"class\s+(VTK\w*_EXPORT\s+)?{rec['class']}\b" if whole else rf"\b{rec['symbol']}\s*\("
        current, found = declared(repo, head, pattern, f"*/{rec['class']}.h")
        if not found and not whole:
            current, _ = declared(repo, head, pattern, "*.h")
        cache[key] = current
    return cache[key]


def declared(repo, head, pattern, pathspec):
    """(declared without a deprecation mark, declared at all) for a pattern in headers at head."""
    r = subprocess.run(["git", "-C", repo, "grep", "-n", "-B1", "-E", "-e", pattern, head, "--", pathspec],
                       capture_output=True, text=True, errors="replace", timeout=120)
    marked = lambda x: "VTK_DEPRECATED" in x or "VTK_LEGACY" in x
    found, prev = False, ""
    for line in r.stdout.splitlines():
        if line == "--":
            prev = ""
            continue
        body = re.sub(r"^[0-9a-f]{40}:[^:]*?[:-]\d+[:-]", "", line)
        if re.search(pattern, body) and not body.lstrip().startswith(("//", "*")):
            found = True
            if not marked(body) and not (marked(prev) and not prev.rstrip().endswith(";")):
                return True, True
        prev = body
    return False, found


def deprecated_uses(path, number, text, deprecated, until, repo=None, head=None):
    if not deprecated or "VTK_DEPRECATED" in text or "VTK_LEGACY" in text or text.lstrip().startswith("//"):
        return []
    out = []
    tokens = set(IDENT_TOKEN.findall(text))
    for name in tokens & deprecated.keys():
        for rec in deprecated[name]:
            when = rec["deprecated"]["date"]
            if not when or (until and when >= until):
                continue
            whole_class = rec["class"] == rec["symbol"]
            if whole_class or rec["class"] in tokens or rec["class"] == Path(path).stem:
                if repo and still_current(repo, head, rec):
                    continue
                state = f"deprecated in VTK {rec['version']}" if rec.get("version") else "deprecated"
                if rec.get("removed") and (not until or rec["removed"]["date"] < until):
                    state += f" and {rec['outcome']}"
                why = f" ({rec['reason']})" if rec.get("reason") else ""
                out.append({"kind": "deprecated", "path": path, "line": number,
                            "fact": f"{rec['class']}{'' if whole_class else '::' + rec['symbol']} is {state}{why}"})
                break
    return out


def grep(repo, head, pattern, *paths, word=False):
    args = ["git", "-C", repo, "grep", "-n", "-I", "-E"] + (["-w"] if word else []) + ["-e", pattern, head, "--", *paths]
    r = subprocess.run(args, capture_output=True, text=True, errors="replace", timeout=120)
    return [line.split(":", 1)[1] for line in r.stdout.splitlines() if ":" in line]


def added_lines(hunks):
    """(path, line number, text) for every added line."""
    for path, _hunk, added, numbers in hunks:
        for number, text in zip(numbers, added.splitlines()):
            yield path, number, text


def check(repo, head, hunks, limit=12, deprecated=None, until=None):
    findings = []
    lines = list(added_lines(hunks))
    returned = {(path, m.group(1)) for path, _n, text in lines if (m := re.match(r"\s*return\s+(\w+)\s*;", text))}
    for path, number, text in lines:
        cls = Path(path).stem
        if SOURCE.search(path) and (m := RAW_NEW.match(text)) and "Take" not in text and (path, m.group(2)) not in returned:
            findings.append({"kind": "raw-new", "path": path, "line": number,
                             "fact": f"{m.group(2)} holds a raw pointer from {m.group(3)}::New(); "
                                     f"vtkNew<{m.group(3)}> or vtkSmartPointer would release it"})
        if SOURCE.search(path) and not NOT_LIBRARY.search(path) and STDOUT.search(text.split("//")[0]):
            findings.append({"kind": "stdout", "path": path, "line": number,
                             "fact": "library code writes to stdout/stderr directly instead of using vtkLog "
                                     "or vtkWarningMacro/vtkErrorMacro"})
        if SOURCE.search(path):
            findings += deprecated_uses(path, number, text, deprecated, until, repo, head)
        if HEADER.search(path) and (m := METHOD_DECL.match(text)) and "=" not in text.split("(")[0]:
            name = m.group(1)
            if name in (cls, f"~{cls}", "New") or re.search(r"=\s*(default|delete|0)\b", text):
                continue
            prop = re.sub(r"^(Set|Get)", "", name)
            defined = grep(repo, head, rf"\b{cls}::{name}\s*\(", *CODE) or grep(
                repo, head, rf"\b{name}\s*\([^;]*\)\s*(const\s*)?(override\s*)?\{{", path) or grep(
                repo, head, rf"vtk\w*Macro\s*\(\s*({cls}\s*,\s*)?{prop}\b", *CODE)
            if not defined:
                findings.append({"kind": "undefined", "path": path, "line": number,
                                 "fact": f"{cls}::{name} is declared here but no definition was found in the tree"})
                continue
        internal = "Private/" in path or "Internal" in cls
        if SOURCE.search(path) and "override" not in text:
            member = MEMBER_DECL.match(text) if HEADER.search(path) else None
            method = METHOD_DECL.match(text) if HEADER.search(path) and internal else None
            name = (member or method).group(1) if (member or method) else None
            if not name and internal and not HEADER.search(path) and (d := FUNC_DEF.match(text)) and d.group(1):
                name = d.group(2)
            if name and len(name) > 3 and not name.startswith("~") and name != cls:
                decl = re.compile(rf":\d+:\s*(?!return\b)(?:[\w:<>,*&]+\s+)+[*&]?(?:\w+::)?{re.escape(name)}\s*[(;={{]")
                refs = [u for u in grep(repo, head, name, *CODE, "*.py", word=True) if not decl.search(u)]
                if not refs:
                    findings.append({"kind": "unused", "path": path, "line": number,
                                     "fact": f"{name} is declared or defined but never referenced anywhere in the tree"})
        for pattern, release in CREATE:
            if (m := pattern.search(text)):
                a, b = m.group(1), m.group(2) if m.lastindex and m.lastindex > 1 else ""
                kind, var = (a, b) if pattern.pattern.startswith("glGen") else (b, a)
                member = var.replace("this->", "").replace("&", "").strip()
                if not re.match(r"^[A-Z]\w*$", member):
                    continue
                if not grep(repo, head, release(kind, member), *CODE):
                    findings.append({"kind": "unreleased", "path": path, "line": number,
                                     "fact": f"{member} is created here but nothing in the tree releases it"})
        if CMAKE.search(path):
            for m in CMAKE_READ.finditer(text):
                var = m.group(1) or m.group(2)
                if not var or CMAKE_BUILTIN.match(var) or var.islower():
                    continue
                setters = grep(repo, head, rf"(set|option|cmake_dependent_option|find_\w+|mark_as_advanced)\s*\(\s*{var}\b",
                               "*.cmake", "*CMakeLists.txt", "*.cmake.in")
                if not setters:
                    findings.append({"kind": "unset", "path": path, "line": number,
                                     "fact": f"CMake variable {var} is read here but nothing in the tree sets it"})
    seen, unique = set(), []
    for f in findings:
        if (f["kind"], f["fact"]) not in seen:
            seen.add((f["kind"], f["fact"]))
            unique.append(f)
    return unique[:limit]


def render(findings):
    return "\n".join(f"- [{f['kind']}] {f['path']}:{f['line']}: {f['fact']}" for f in findings) or "(none)"
